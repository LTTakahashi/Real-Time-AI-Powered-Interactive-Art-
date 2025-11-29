#!/usr/bin/env python3
"""
Demo: Gesture-controlled canvas system.
Tests integration of hand tracking, gesture recognition, and canvas drawing.
"""

import cv2
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hand_tracking import HandTracker
from gesture_recognition import GestureRecognizer
from canvas import GestureCanvas

def main():
    tracker = HandTracker()
    recognizer = GestureRecognizer()
    canvas = GestureCanvas(internal_size=(1024, 1024), display_size=(640, 480))
    
    # Find working camera
    cap = None
    for i in range(4):
        test_cap = cv2.VideoCapture(i)
        if test_cap.isOpened():
            ret, _ = test_cap.read()
            if ret:
                cap = test_cap
                print(f"Using camera index {i}")
                break
            test_cap.release()
    
    if cap is None:
        print("No webcam found. Try: python demo_canvas.py --help")
        print("For video file mode, run: python demo_canvas.py --video <path>")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    print("\n" + "="*60)
    print("GESTURE-CONTROLLED CANVAS DEMO")
    print("="*60)
    print("Gestures:")
    print("  POINTING - Draw")
    print("  FIST - Stop drawing")
    print("  OPEN_PALM - Clear canvas (hold for 1s)")
    print("  PINCH - Undo")
    print("\nPress 'q' to quit, 's' to save canvas")
    print("="*60 + "\n")

    prev_gesture = "NONE"
    prev_time = time.time()
    fps_samples = []
    clear_hold_time = None
    
    while True:
        frame_start = time.time()
        
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        
        # Track hands and recognize gestures
        hands_data = tracker.process_frame(frame)
        gesture = "NONE"
        
        if hands_data:
            hand = hands_data[0]
            gesture = recognizer.detect_gesture(hand['landmarks'])
            
            # Get index fingertip position
            index_tip = hand['landmarks'][8]
            
            # Transform to canvas coordinates
            canvas_x, canvas_y = canvas.gesture_to_canvas_coords(
                index_tip['x'], index_tip['y'], (w, h)
            )
            
            # Handle gestures
            if gesture == "POINTING":
                if not canvas.is_drawing:
                    canvas.start_stroke(canvas_x, canvas_y)
                else:
                    canvas.add_point(canvas_x, canvas_y)
                clear_hold_time = None
            
            elif gesture != "POINTING" and canvas.is_drawing:
                canvas.end_stroke()
            
            if gesture == "PINCH" and prev_gesture != "PINCH":
                canvas.undo()
                clear_hold_time = None
            
            if gesture == "OPEN_PALM":
                if clear_hold_time is None:
                    clear_hold_time = time.time()
                elif time.time() - clear_hold_time > 1.0:
                    canvas.clear()
                    clear_hold_time = None
            else:
                clear_hold_time = None
            
            # Draw hand skeleton
            for lm in hand['landmarks']:
                color = (0, 255, 0) if gesture == "POINTING" else (255, 255, 255)
                cv2.circle(frame, (lm['x'], lm['y']), 3, color, -1)
            
            # Draw cursor on canvas
            if gesture == "POINTING":
                cv2.circle(frame, (index_tip['x'], index_tip['y']), 8, (0, 255, 0), 2)
        
        # Get canvas display
        canvas_display = canvas.get_display()
        
        # Create combined view (webcam + canvas side by side)
        combined = np.hstack([frame, canvas_display])
        
        # FPS calculation
        fps = 1.0 / (time.time() - frame_start)
        fps_samples.append(fps)
        if len(fps_samples) > 30:
            fps_samples.pop(0)
        avg_fps = sum(fps_samples) / len(fps_samples)
        
        # UI Overlays
        cv2.putText(combined, f"FPS: {int(avg_fps)}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(combined, f"Gesture: {gesture}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        # Memory usage
        mem = canvas.get_memory_usage()
        cv2.putText(combined, f"Memory: {mem['total_mb']:.1f}MB", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Clear countdown
        if clear_hold_time is not None:
            time_held = time.time() - clear_hold_time
            cv2.putText(combined, f"Hold to clear: {time_held:.1f}s", (10, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        cv2.imshow('Canvas Demo', combined)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            filename = f"canvas_save_{int(time.time())}.png"
            cv2.imwrite(filename, canvas.get_canvas())
            print(f"Saved to {filename}")
        elif key == ord('u'):
            canvas.undo()
        elif key == ord('r'):
            canvas.redo()
        elif key == ord('c'):
            canvas.clear()
        
        prev_gesture = gesture
    
    cap.release()
    cv2.destroyAllWindows()
    tracker.close()
    
    print(f"\nFinal Stats:")
    print(f"  Average FPS: {avg_fps:.1f}")
    print(f"  Memory Usage: {mem['total_mb']:.1f}MB")


if __name__ == "__main__":
    import numpy as np  # Import here for the demo
    main()
