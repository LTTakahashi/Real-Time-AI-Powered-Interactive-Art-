import cv2
import time
import sys
import subprocess
from hand_tracking import HandTracker
from gesture_recognition import GestureRecognizer

import argparse

def run_env_check():
    print("Running Environment Check...")
    try:
        subprocess.check_call([sys.executable, "validate_env.py"])
        return True
    except subprocess.CalledProcessError:
        return False

def draw_text_centered(img, text, y, color=(255, 255, 255), scale=1.0):
    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 2)[0]
    text_x = (img.shape[1] - text_size[0]) // 2
    cv2.putText(img, text, (text_x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, 2)

def main():
    parser = argparse.ArgumentParser(description="Week 1 Verification Suite")
    parser.add_argument("--video", type=str, help="Path to video file for testing (instead of webcam)")
    parser.add_argument("--skip-env", action="store_true", help="Skip environment validation check")
    args = parser.parse_args()

    # Step 1: Env Check
    if not args.skip_env:
        if not run_env_check():
            print("\n[WARNING] Environment check failed.")
            if args.video:
                print("Proceeding because --video was provided.")
            else:
                response = input("Do you want to proceed anyway? (y/N): ").strip().lower()
                if response != 'y':
                    print("Aborting.")
                    return

    tracker = HandTracker()
    recognizer = GestureRecognizer()
    
    source = 0
    if args.video:
        source = args.video
        print(f"Using video file: {source}")
    else:
        # Try to find a working webcam index if not provided
        found = False
        for i in range(4):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    source = i
                    found = True
                    cap.release()
                    break
                cap.release()
        
        if not found:
            print("[ERROR] No working webcam found.")
            if not args.video:
                print("Please provide a video file using --video <path> to test logic without a webcam.")
                return

    cap = cv2.VideoCapture(source)
    
    if not cap.isOpened():
        print(f"Error: Could not open source {source}")
        return

    # If video file, don't force 640x480, use file dims
    if not args.video:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    challenges = ["OPEN_PALM", "FIST", "POINTING", "PINCH"]
    current_challenge_idx = 0
    challenge_start_time = time.time()
    results = {}

    state = "INSTRUCTION" # INSTRUCTION, CHALLENGE, SUCCESS, REPORT
    success_timer = 0

    print("\nStarting Interactive Verification...")
    print("Press 'q' to quit.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            if args.video:
                print("End of video file reached.")
                break
            else:
                print("Failed to grab frame.")
                break

        if not args.video:
            frame = cv2.flip(frame, 1)
        
        h, w, _ = frame.shape

        hands_data = tracker.process_frame(frame)
        detected_gesture = "NONE"
        
        if hands_data:
            detected_gesture = recognizer.detect_gesture(hands_data[0]['landmarks'])
            # Draw skeleton
            for lm in hands_data[0]['landmarks']:
                cv2.circle(frame, (lm['x'], lm['y']), 3, (0, 255, 0), -1)

        # UI Logic
        if state == "INSTRUCTION":
            draw_text_centered(frame, "Week 1 Verification", 50, scale=1.2)
            draw_text_centered(frame, "Press SPACE to start", h//2)
            
            key = cv2.waitKey(1)
            if key == 32: # Space
                state = "CHALLENGE"
                challenge_start_time = time.time()

        elif state == "CHALLENGE":
            target = challenges[current_challenge_idx]
            draw_text_centered(frame, f"Challenge {current_challenge_idx+1}/{len(challenges)}", 50)
            draw_text_centered(frame, f"Show me: {target}", h//2, color=(0, 255, 255), scale=1.5)
            draw_text_centered(frame, f"Detected: {detected_gesture}", h - 50, color=(200, 200, 200))

            if detected_gesture == target:
                state = "SUCCESS"
                success_timer = time.time()
                results[target] = "PASS"

        elif state == "SUCCESS":
            target = challenges[current_challenge_idx]
            draw_text_centered(frame, f"Challenge {current_challenge_idx+1}/{len(challenges)}", 50)
            draw_text_centered(frame, "SUCCESS!", h//2, color=(0, 255, 0), scale=2.0)
            
            if time.time() - success_timer > 1.5: # Wait 1.5s
                current_challenge_idx += 1
                if current_challenge_idx >= len(challenges):
                    state = "REPORT"
                else:
                    state = "CHALLENGE"
                    challenge_start_time = time.time()

        elif state == "REPORT":
            draw_text_centered(frame, "Verification Complete", 50)
            y_offset = 100
            for k, v in results.items():
                draw_text_centered(frame, f"{k}: {v}", y_offset)
                y_offset += 40
            
            draw_text_centered(frame, "Press Q to exit", h - 50)

        cv2.imshow('Verification Suite', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Save Report
    with open("verification_report_week1.txt", "w") as f:
        f.write("Week 1 Verification Report\n")
        f.write("==========================\n")
        for k, v in results.items():
            f.write(f"{k}: {v}\n")
    
    print("Report saved to verification_report_week1.txt")
    cap.release()
    cv2.destroyAllWindows()
    tracker.close()

if __name__ == "__main__":
    main()
