"""
Script to generate demo outputs from demo.mp4 using the actual application logic.
"""
import cv2
import numpy as np
import os
import sys
from PIL import Image

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hand_tracking import HandTracker
from gesture_recognition import GestureRecognizer
from style_transfer import StableDiffusionStyleTransfer, STYLE_PRESETS

def generate_demo_outputs():
    print("Initializing systems...")
    tracker = HandTracker()
    recognizer = GestureRecognizer()
    style_transfer = StableDiffusionStyleTransfer()
    
    # Load video
    video_path = 'frontend/public/demo.mp4'
    if not os.path.exists(video_path):
        print(f"Error: {video_path} not found")
        return
    
    cap = cv2.VideoCapture(video_path)
    
    # Create canvas (black background)
    canvas_width = 640
    canvas_height = 480
    canvas = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)
    
    print("Processing video to generate drawing...")
    
    prev_point = None
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_count += 1
        
        # Resize to match app logic
        frame = cv2.resize(frame, (canvas_width, canvas_height))
        
        # Process frame
        hands_data = tracker.process_frame(frame)
        
        if hands_data:
            hand = hands_data[0]
            landmarks = hand['landmarks']
            
            # Detect gesture
            gesture = recognizer.detect_gesture(landmarks)
            
            # Get index tip coordinates
            index_tip = landmarks[8]
            x = int(index_tip['x'])
            y = int(index_tip['y'])
            current_point = (x, y)
            
            # Draw if pointing
            if gesture == "POINTING":
                if prev_point:
                    # Draw white line
                    cv2.line(canvas, prev_point, current_point, (255, 255, 255), 5)
                prev_point = current_point
            else:
                prev_point = None
        else:
            prev_point = None
            
    cap.release()
    print(f"Processed {frame_count} frames.")
    
    # Save the raw canvas drawing
    os.makedirs('test_data/outputs', exist_ok=True)
    cv2.imwrite('test_data/outputs/demo_canvas_drawing.png', canvas)
    print("Saved raw canvas drawing to test_data/outputs/demo_canvas_drawing.png")
    
    # Generate styles
    print("\nLoading Style Transfer Model...")
    style_transfer.load_model(lambda msg: print(f"  {msg}"))
    
    styles = ['photorealistic', 'anime', 'oil_painting', 'watercolor', 'sketch']
    
    print("\nGenerating outputs...")
    for style in styles:
        print(f"Generating {style}...")
        try:
            result_image, metadata = style_transfer.generate(
                input_image=canvas,
                style=style,
                num_inference_steps=4  # Turbo speed
            )
            
            output_filename = f"test_data/outputs/demo_{style}_output.png"
            result_image.save(output_filename)
            print(f"  Saved to {output_filename}")
            
        except Exception as e:
            print(f"  Error generating {style}: {e}")
            
    print("\nDone! All outputs generated.")

if __name__ == "__main__":
    generate_demo_outputs()
