#!/usr/bin/env python3
"""
Script to record test videos for gesture validation.
Usage: venv/bin/python scripts/record_test_video.py --gesture fist --duration 5 --output test_data/gestures/fist.mp4
"""

import cv2
import argparse
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hand_tracking import HandTracker
from gesture_recognition import GestureRecognizer

def main():
    parser = argparse.ArgumentParser(description="Record test video for gesture validation")
    parser.add_argument("--gesture", type=str, required=True, help="Target gesture to record (fist, pointing, pinch, open_palm)")
    parser.add_argument("--duration", type=int, default=5, help="Duration in seconds")
    parser.add_argument("--output", type=str, required=True, help="Output video path")
    parser.add_argument("--camera", type=int, default=0, help="Camera index")
    args = parser.parse_args()

    # Create output directory if needed
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    tracker = HandTracker()
    recognizer = GestureRecognizer()
    
    # Find working camera
    cap = None
    for i in range(args.camera, args.camera + 4):
        test_cap = cv2.VideoCapture(i)
        if test_cap.isOpened():
            ret, _ = test_cap.read()
            if ret:
                cap = test_cap
                print(f"Using camera index {i}")
                break
            test_cap.release()
    
    if cap is None:
        print("No working camera found!")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    if fps == 0: fps = 30
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(args.output, fourcc, fps, (640, 480))

    print(f"\nRecording {args.gesture.upper()} gesture for {args.duration} seconds...")
    print("Press 'q' to quit early, 's' to start recording")
    
    recording = False
    frame_count = 0
    max_frames = fps * args.duration

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        hands_data = tracker.process_frame(frame)
        
        detected = "NONE"
        if hands_data:
            detected = recognizer.detect_gesture(hands_data[0]['landmarks'])
            # Draw hand
            for lm in hands_data[0]['landmarks']:
                cv2.circle(frame, (lm['x'], lm['y']), 3, (0, 255, 0), -1)
        
        # UI
        if recording:
            cv2.putText(frame, f"RECORDING: {frame_count}/{max_frames}", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, f"Target: {args.gesture.upper()}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(frame, f"Detected: {detected}", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            out.write(frame)
            frame_count += 1
            
            if frame_count >= max_frames:
                break
        else:
            cv2.putText(frame, "Press 's' to start recording", (10, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(frame, f"Target: {args.gesture.upper()}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(frame, f"Detected: {detected}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow('Record Test Video', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s') and not recording:
            recording = True

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    tracker.close()
    
    print(f"\nSaved to: {args.output}")
    print(f"Frames recorded: {frame_count}")

if __name__ == "__main__":
    main()
