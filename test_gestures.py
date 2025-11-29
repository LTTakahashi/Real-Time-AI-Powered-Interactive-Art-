import cv2
import time
from hand_tracking import HandTracker
from gesture_recognition import GestureRecognizer

def main():
    tracker = HandTracker()
    recognizer = GestureRecognizer()
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Webcam not accessible.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("Starting Gesture Recognition Test...")
    print("Press 'q' to quit.")

    prev_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        hands_data = tracker.process_frame(frame)
        
        for hand in hands_data:
            # Detect Gesture
            gesture = recognizer.detect_gesture(hand['landmarks'])
            
            # Visualize
            wrist = hand['landmarks'][0]
            
            # Color based on gesture
            color = (255, 255, 255)
            if gesture == "PINCH": color = (0, 255, 255) # Yellow
            elif gesture == "FIST": color = (0, 0, 255) # Red
            elif gesture == "POINTING": color = (0, 255, 0) # Green
            elif gesture == "OPEN_PALM": color = (255, 0, 0) # Blue
            
            cv2.putText(frame, f"Gesture: {gesture}", (wrist['x'], wrist['y'] - 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            
            # Draw skeleton
            for lm in hand['landmarks']:
                cv2.circle(frame, (lm['x'], lm['y']), 3, color, -1)

        # FPS
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time) if prev_time > 0 else 0
        prev_time = curr_time
        cv2.putText(frame, f"FPS: {int(fps)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow('Gesture Test', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    tracker.close()

if __name__ == "__main__":
    main()
