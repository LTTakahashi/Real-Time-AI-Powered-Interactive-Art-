import cv2
import numpy as np
import base64
import json
import time
import asyncio
import logging
import uvicorn
from pathlib import Path
from typing import Dict, Optional
from PIL import Image
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from hand_tracking import HandTracker
from gesture_recognition import GestureRecognizer
from canvas import GestureCanvas
from style_transfer import StableDiffusionStyleTransfer, STYLE_PRESETS
from threading_manager import ThreadingManager, GenerationQueue, GenerationRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GestureCanvasServer")

app = FastAPI(title="GestureCanvas API")

# Configure paths
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
FRONTEND_PUBLIC = BASE_DIR / "frontend" / "public"

# CORS (only for development - disabled for same-origin in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State
class ServerState:
    def __init__(self):
        self.tracker = HandTracker()
        self.recognizer = GestureRecognizer()
        # Use frontend canvas size (640x480) for coordinate consistency
        self.canvas = GestureCanvas(internal_size=(640, 480), display_size=(640, 480))
        self.style_transfer = StableDiffusionStyleTransfer()
        
        # Use ThreadingManager for generation queue/thread
        self.threading_manager = ThreadingManager()
        self.generation_queue = self.threading_manager.generation_queue
        
        # Start generation thread
        self.threading_manager.start_generation_thread(self.style_transfer)
        logger.info("Generation thread started via ThreadingManager")
        
        # State tracking
        self.drawing = False
        self.last_gesture = "NONE"
        self.clear_hold_start = None

state = ServerState()

# Models
class StyleRequest(BaseModel):
    style: str
    image: str  # Base64 encoded image

# WebSocket for Real-Time Tracking
@app.websocket("/ws/tracking")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Client connected to tracking WebSocket")
    
    try:
        while True:
            # Receive frame (base64)
            data = await websocket.receive_text()
            
            # Decode frame
            try:
                # Expecting "data:image/jpeg;base64,..."
                if "," in data:
                    header, encoded = data.split(",", 1)
                else:
                    encoded = data
                
                image_data = base64.b64decode(encoded)
                np_arr = np.frombuffer(image_data, np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                
                if frame is None:
                    continue
                    
                # Process frame
                # 1. Track Hand
                hands_data = state.tracker.process_frame(frame)
                
                # 2. Recognize Gesture
                gesture = "NONE"
                index_tip = None
                landmarks_list = []
                
                if hands_data:
                    # Use first hand
                    hand = hands_data[0]
                    landmarks_list = hand['landmarks']
                    gesture = state.recognizer.detect_gesture(landmarks_list)
                    
                    # Get index tip for drawing (landmark 8)
                    # landmarks are already in pixels {'x': int, 'y': int, 'z': float}
                    idx_pt = landmarks_list[8]
                    index_tip = (idx_pt['x'], idx_pt['y'])
                
                # 3. Update Canvas Logic (Backend State)
                response = {
                    "gesture": gesture,
                    "landmarks": landmarks_list,
                    "cursor": index_tip,
                    "action": None,
                    "points": None
                }
                
                # Canvas Interaction Logic
                if index_tip:
                    x, y = index_tip
                    # Map to canvas
                    canvas_x, canvas_y = state.canvas.gesture_to_canvas_coords(x, y, (frame.shape[1], frame.shape[0]))
                    
                    if gesture == "POINTING":
                        if not state.drawing:
                            state.canvas.start_stroke(canvas_x, canvas_y)
                            state.drawing = True
                            response["action"] = "start_stroke"
                            response["points"] = (canvas_x, canvas_y)
                        else:
                            state.canvas.add_point(canvas_x, canvas_y)
                            response["action"] = "draw"
                            response["points"] = (canvas_x, canvas_y)
                        state.clear_hold_start = None
                    
                    elif gesture != "POINTING" and state.drawing:
                        state.canvas.end_stroke()
                        state.drawing = False
                        response["action"] = "end_stroke"
                    
                    # Undo (PINCH)
                    if gesture == "PINCH" and state.last_gesture != "PINCH":
                        state.canvas.undo()
                        state.clear_hold_start = None
                        response["action"] = "undo"
                    
                    # Clear (OPEN_PALM held)
                    if gesture == "OPEN_PALM":
                        if state.clear_hold_start is None:
                            state.clear_hold_start = time.time()
                        elif time.time() - state.clear_hold_start > 1.0:
                            state.canvas.clear()
                            state.clear_hold_start = None
                            response["action"] = "clear"
                    else:
                        state.clear_hold_start = None
                
                state.last_gesture = gesture
                
                # Send response
                await websocket.send_json(response)
                
            except Exception as e:
                logger.error(f"Error processing frame: {e}")
                await websocket.send_json({"error": str(e)})
                
    except WebSocketDisconnect:
        logger.info("Client disconnected")

# REST Endpoints
@app.post("/generate")
async def generate_image(request: StyleRequest):
    if request.style not in STYLE_PRESETS:
        raise HTTPException(status_code=400, detail="Invalid style")
    
    # Ensure model is loaded
    if not state.style_transfer.is_loaded:
        logger.info("Loading SDXL model...")
        state.style_transfer.load_model()
    
    # Decode canvas image from request (Frontend sends current canvas state)
    # OR use backend canvas state? 
    # Using backend state is safer as it matches the drawing logic
    # BUT frontend might have higher res? No, backend is 1024x1024.
    # Let's use backend canvas for consistency.
    
    canvas_img = state.canvas.get_canvas()
    
    # Create request
    req_id = f"req_{int(time.time()*1000)}"
    gen_req = GenerationRequest(
        request_id=req_id,
        canvas_image=canvas_img,
        style=request.style,
        timestamp=time.time()
    )
    
    success = state.generation_queue.add_request(gen_req)
    if not success:
        raise HTTPException(status_code=503, detail="Queue full")
    
    return {"request_id": req_id, "status": "queued", "position": state.generation_queue.get_queue_size()}

@app.get("/status/{request_id}")
async def get_status(request_id: str):
    # Check result queue
    # This is tricky because GenerationQueue puts results in a queue that we need to poll
    # We need a way to store results.
    # Let's modify ServerState to hold results.
    pass 
    # We need to poll the result_queue from the generation thread.
    # Since this is async, we can't block.
    # We should have a background task that moves results from queue to a dict.

# Background result poller
async def result_poller():
    while True:
        try:
            if not state.threading_manager.result_queue.empty():
                result = state.threading_manager.result_queue.get_nowait()
                # Store result with timestamp for TTL cleanup
                results_store[result.request_id] = (result, time.time())
                logger.info(f"Result stored: {result.request_id}, success={result.success}")
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Poller error: {e}")
            await asyncio.sleep(1)

# Cleanup old results (TTL = 5 minutes)
async def cleanup_old_results():
    while True:
        try:
            now = time.time()
            to_delete = [
                rid for rid, (res, ts) in results_store.items() 
                if now - ts > 300  # 5 minute TTL
            ]
            for rid in to_delete:
                del results_store[rid]
                logger.info(f"Cleaned up result {rid}")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
        await asyncio.sleep(60)  # Run every minute

results_store = {}

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(result_poller())
    asyncio.create_task(cleanup_old_results())

@app.get("/result/{request_id}")
async def get_result(request_id: str):
    if request_id in results_store:
        result, _timestamp = results_store[request_id]  # Unpack tuple
        if result.success:
            # Convert PIL Image to numpy array (RGB -> BGR)
            if isinstance(result.styled_image, Image.Image):
                img_np = np.array(result.styled_image)
                img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            else:
                img_bgr = result.styled_image

            # Encode image
            _, buffer = cv2.imencode('.jpg', img_bgr)
            img_str = base64.b64encode(buffer).decode('utf-8')
            return {"status": "complete", "image": img_str, "time": result.metadata.get('generation_time')}
        else:
            return {"status": "failed", "error": result.error}
    
    # Check if still in queue
    pos = state.generation_queue.get_queue_position(request_id)
    if pos >= 0:
        logger.debug(f"Request {request_id} still in queue at position {pos}")
        return {"status": "queued", "position": pos}
    
    logger.warning(f"Request {request_id} not found in results_store or queue")
    return {"status": "not_found"}

# Health Check Endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for loading screen"""
    return {"status": "ok", "model_loaded": state.style_transfer is not None}

# Static File Serving (Production)
if FRONTEND_DIST.exists():
    # Mount assets directory
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")
    
    # Serve demo.mp4 from public
    if FRONTEND_PUBLIC.exists():
        @app.get("/demo.mp4")
        async def serve_demo():
            demo_path = FRONTEND_PUBLIC / "demo.mp4"
            if demo_path.exists():
                return FileResponse(demo_path, media_type="video/mp4")
            raise HTTPException(status_code=404, detail="Demo video not found")
    
    # Root route - serve index.html
    @app.get("/")
    async def serve_root():
        index_path = FRONTEND_DIST / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="Frontend not built. Run 'npm run build' in frontend/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
