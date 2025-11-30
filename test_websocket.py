import asyncio
import websockets
import cv2
import numpy as np
import base64
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/tracking"
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")
        
        # Create a dummy black image
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        _, buffer = cv2.imencode('.jpg', img)
        img_str = base64.b64encode(buffer).decode('utf-8')
        
        # Send frame
        await websocket.send(img_str)
        print("Sent frame")
        
        # Receive response
        response = await websocket.recv()
        data = json.loads(response)
        
        print(f"Received response: {data.keys()}")
        print(f"Gesture: {data.get('gesture')}")
        
        assert "gesture" in data
        assert "landmarks" in data
        assert "cursor" in data

if __name__ == "__main__":
    asyncio.run(test_websocket())
