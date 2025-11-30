"""
GestureCanvas - Main Gradio Application
Complete UI with webcam streaming, gesture feedback, canvas drawing, and style transfer.
"""

import gradio as gr
import cv2
import numpy as np
from PIL import Image
import time
import base64
from io import BytesIO
import threading

from hand_tracking import HandTracker
from gesture_recognition import GestureRecognizer
from canvas import GestureCanvas
from style_transfer import StableDiffusionStyleTransfer, STYLE_PRESETS
from threading_manager import ThreadingManager, GenerationRequest
from config import GESTURE_THRESHOLDS

# Global state
app_state = {
    'tracker': None,
    'recognizer': None,
    'canvas': None,
    'style_transfer': None,
    'threading_manager': None,
    'initialized': False,
    'drawing': False,
    'last_gesture': "NONE",
    'clear_hold_start': None,
    'show_tutorial': True,
    'generation_in_progress': False,
    'latest_styled_image': None
}

# Configuration
GESTURE_COLORS = {
    'POINTING': (0, 255, 0),  # Green - Draw
    'FIST': (255, 0, 0),      # Blue - Stop
    'OPEN_PALM': (0, 255, 255),  # Yellow - Clear
    'PINCH': (255, 0, 255),   # Magenta - Undo/Style
    'NONE': (255, 255, 255)   # White - No gesture
}

def encode_image_to_base64(image: np.ndarray) -> str:
    """Encode image to base64 for HTML display."""
    _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return base64.b64encode(buffer).decode('utf-8')


def initialize_system(camera_index=0):
    """Initialize all system components."""
    if app_state['initialized']:
        return "System already initialized"
    
    try:
        # Initialize components
        app_state['tracker'] = HandTracker()
        app_state['recognizer'] = GestureRecognizer()
        app_state['canvas'] = GestureCanvas(internal_size=(1024, 1024), display_size=(640, 480))
        app_state['style_transfer'] = StableDiffusionStyleTransfer()
        app_state['threading_manager'] = ThreadingManager()
        
        # Start threads
        app_state['threading_manager'].start_hand_tracking_thread(
            app_state['tracker'],
            app_state['recognizer'],
            camera_index=camera_index
        )
        
        app_state['initialized'] = True
        return "✅ System initialized successfully! Start gesturing to draw."
    
    except Exception as e:
        return f"❌ Initialization failed: {str(e)}"


def process_frame_with_overlay():
    """Get latest frame with gesture overlays."""
    if not app_state['initialized']:
        # Return placeholder
        placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(placeholder, "Click 'Initialize System' to start", (50, 240),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        return placeholder
    
    # Get latest frame
    frame = app_state['threading_manager'].frame_buffer.get_latest()
    if frame is None:
        return np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Get gesture state
    gesture_state = app_state['threading_manager'].gesture_state.get()
    
    # Draw hand landmarks
    if gesture_state.hand_detected and gesture_state.hand_landmarks:
        color = GESTURE_COLORS.get(gesture_state.gesture, (255, 255, 255))
        
        for lm in gesture_state.hand_landmarks:
            cv2.circle(frame, (lm['x'], lm['y']), 4, color, -1)
            cv2.circle(frame, (lm['x'], lm['y']), 6, (0, 0, 0), 1)
        
        # Draw cursor at index fingertip
        if gesture_state.index_tip_pos:
            x, y = gesture_state.index_tip_pos
            cv2.circle(frame, (x, y), 12, color, 2)
            cv2.line(frame, (x-8, y), (x+8, y), color, 2)
            cv2.line(frame, (x, y-8), (x, y+8), color, 2)
    
    # Gesture feedback border
    gesture = gesture_state.gesture
    if gesture != "NONE":
        color = GESTURE_COLORS[gesture]
        cv2.rectangle(frame, (0, 0), (frame.shape[1]-1, frame.shape[0]-1), color, 5)
    
    # Gesture label
    cv2.putText(frame, f"{gesture}", (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, GESTURE_COLORS[gesture], 2)
    
    # Tutorial overlay
    if app_state['show_tutorial']:
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 60), (630, 200), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        cv2.putText(frame, "GESTURES:", (20, 85),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, "POINTING (Green) - Draw on canvas", (20, 115),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(frame, "FIST (Blue) - Stop drawing", (20, 140),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        cv2.putText(frame, "OPEN PALM (Yellow) - Clear (hold 1s)", (20, 165),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        cv2.putText(frame, "PINCH (Magenta) - Undo or Apply Style", (20, 190),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
    
    return frame


def update_canvas():
    """Update canvas based on gestures."""
    if not app_state['initialized'] or app_state['canvas'] is None:
        return np.full((480, 640, 3), 255, dtype=np.uint8)
    
    gesture_state = app_state['threading_manager'].gesture_state.get()
    h, w = 480, 640
    
    # Handle drawing
    if gesture_state.hand_detected and gesture_state.index_tip_pos:
        gesture = gesture_state.gesture
        x, y = gesture_state.index_tip_pos
        
        # Transform to canvas coordinates
        canvas_x, canvas_y = app_state['canvas'].gesture_to_canvas_coords(x, y, (w, h))
        
        if gesture == "POINTING":
            if not app_state['drawing']:
                app_state['canvas'].start_stroke(canvas_x, canvas_y)
                app_state['drawing'] = True
            else:
                app_state['canvas'].add_point(canvas_x, canvas_y)
            app_state['clear_hold_start'] = None
        
        elif gesture != "POINTING" and app_state['drawing']:
            app_state['canvas'].end_stroke()
            app_state['drawing'] = False
        
        # Handle undo (PINCH)
        if gesture == "PINCH" and app_state['last_gesture'] != "PINCH":
            app_state['canvas'].undo()
            app_state['clear_hold_start'] = None
        
        # Handle clear (OPEN_PALM held)
        if gesture == "OPEN_PALM":
            if app_state['clear_hold_start'] is None:
                app_state['clear_hold_start'] = time.time()
            elif time.time() - app_state['clear_hold_start'] > 1.0:
                app_state['canvas'].clear()
                app_state['clear_hold_start'] = None
        else:
            app_state['clear_hold_start'] = None
        
        app_state['last_gesture'] = gesture
    
    return app_state['canvas'].get_display()


def generate_styled_image(style: str):
    """Trigger style transfer generation."""
    if not app_state['initialized']:
        return None, "❌ System not initialized"
    
    if app_state['generation_in_progress']:
        return None, "⏳ Generation already in progress..."
    
    try:
        # Load model if needed
        if not app_state['style_transfer'].is_loaded:
            app_state['style_transfer'].load_model(
                progress_callback=lambda msg: print(f"[SD] {msg}")
            )
            
            # Start generation thread
            app_state['threading_manager'].start_generation_thread(
                app_state['style_transfer']
            )
        
        # Create request
        request = GenerationRequest(
            request_id=f"req_{int(time.time()*1000)}",
            canvas_image=app_state['canvas'].get_canvas(),
            style=style,
            timestamp=time.time()
        )
        
        # Add to queue
        success = app_state['threading_manager'].generation_queue.add_request(request)
        
        if success:
            app_state['generation_in_progress'] = True
            return None, f"🎨 Generating {STYLE_PRESETS[style].name}... (Queue position: {app_state['threading_manager'].generation_queue.get_queue_size()})"
        else:
            return None, "❌ Generation queue full. Please wait."
    
    except Exception as e:
        return None, f"❌ Generation failed: {str(e)}"


def check_generation_results():
    """Check for completed generations (called periodically)."""
    if not app_state['initialized']:
        return None, ""
    
    try:
        result = app_state['threading_manager'].result_queue.get_nowait()
        app_state['generation_in_progress'] = False
        
        if result.success:
            app_state['latest_styled_image'] = result.styled_image
            return result.styled_image, f"✅ Generation complete! ({result.metadata.get('generation_time', 0):.1f}s)"
        else:
            return None, f"❌ Generation failed: {result.error}"
    
    except:
        return None, ""


def update_threshold(threshold_name: str, value: float):
    """Update gesture recognition threshold."""
    if threshold_name in GESTURE_THRESHOLDS:
        GESTURE_THRESHOLDS[threshold_name] = value
        return f"✓ Updated {threshold_name} to {value}"
    return f"Unknown threshold: {threshold_name}"


def build_interface():
    """Build Gradio interface."""
    
    with gr.Blocks(title="GestureCanvas - AI-Powered Interactive Art") as app:
        gr.Markdown("# 🎨 GestureCanvas - AI-Powered Interactive Art")
        gr.Markdown("Draw with hand gestures and transform your art with AI style transfer!")
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Webcam Feed")
                webcam_display = gr.Image(label="Hand Tracking", type="numpy", height=480)
                
                with gr.Row():
                    init_btn = gr.Button("🚀 Initialize System", variant="primary")
                    tutorial_btn = gr.Button("📖 Toggle Tutorial")
                
                status_text = gr.Textbox(label="Status", interactive=False)
            
            with gr.Column(scale=1):
                gr.Markdown("### Drawing Canvas")
                canvas_display = gr.Image(label="Canvas", type="numpy", height=480)
                
                with gr.Row():
                    clear_btn = gr.Button("🗑️ Clear Canvas")
                    undo_btn = gr.Button("↩️ Undo")
                    save_btn = gr.Button("💾 Save Canvas")
        
        with gr.Row():
            gr.Markdown("### 🎨 Style Transfer")
        
        with gr.Row():
            style_dropdown = gr.Dropdown(
                choices=list(STYLE_PRESETS.keys()),
                value="photorealistic",
                label="Select Style"
            )
            generate_btn = gr.Button("✨ Generate Styled Image", variant="primary")
        
        with gr.Row():
            styled_output = gr.Image(label="Styled Result", type="pil")
            generation_status = gr.Textbox(label="Generation Status", interactive=False)
        
        with gr.Accordion("⚙️ Calibration (Advanced)", open=False):
            gr.Markdown("Fine-tune gesture recognition for your hand size and style")
            
            hysteresis_slider = gr.Slider(
                minimum=1, maximum=10, value=GESTURE_THRESHOLDS['hysteresis_frames'],
                step=1, label="Hysteresis Frames (stability)"
            )
            cooldown_slider = gr.Slider(
                minimum=1, maximum=20, value=GESTURE_THRESHOLDS['cooldown_frames'],
                step=1, label="Cooldown Frames (transition delay)"
            )
        
        # Event handlers
        def toggle_tutorial():
            app_state['show_tutorial'] = not app_state['show_tutorial']
            return "Tutorial " + ("shown" if app_state['show_tutorial'] else "hidden")
        
        init_btn.click(initialize_system, outputs=[status_text])
        tutorial_btn.click(toggle_tutorial, outputs=[status_text])
        clear_btn.click(lambda: app_state['canvas'].clear() if app_state['canvas'] else None)
        undo_btn.click(lambda: app_state['canvas'].undo() if app_state['canvas'] else None)
        
        generate_btn.click(
            generate_styled_image,
            inputs=[style_dropdown],
            outputs=[styled_output, generation_status]
        )
        
        hysteresis_slider.change(
            lambda val: update_threshold('hysteresis_frames', int(val)),
            inputs=[hysteresis_slider],
            outputs=[status_text]
        )
        
        cooldown_slider.change(
            lambda val: update_threshold('cooldown_frames', int(val)),
            inputs=[cooldown_slider],
            outputs=[status_text]
        )
        
        # Periodic updates
        app.load(
            lambda: (process_frame_with_overlay(), update_canvas()),
            outputs=[webcam_display, canvas_display],
            every=0.033  # ~30 FPS
        )
        
        # Check for generation results
        app.load(
            check_generation_results,
            outputs=[styled_output, generation_status],
            every=0.5
        )
    
    return app


if __name__ == "__main__":
    app = build_interface()
    app.launch(share=False, server_name="0.0.0.0", server_port=7860)
