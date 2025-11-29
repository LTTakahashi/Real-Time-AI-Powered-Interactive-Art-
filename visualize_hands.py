import cv2
import time
from hand_tracking import HandTracker
import mediapipe as mp

def main():
    tracker = HandTracker()
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Webcam not accessible.")
        return

    # Set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles

    print("Starting Hand Tracking Visualization...")
    print("Press 'q' to quit.")

    prev_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Flip frame for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Process
        hands_data = tracker.process_frame(frame)
        
        # Draw
        for hand in hands_data:
            # We need to convert our dictionary landmarks back to a format mp_drawing accepts 
            # OR just draw manually. Drawing manually gives us more control (and we can verify our pixel coords).
            
            # Draw connections
            # MediaPipe connections are tuples of indices
            for connection in mp.solutions.hands.HAND_CONNECTIONS:
                start_idx = connection[0]
                end_idx = connection[1]
                
                start_pt = (hand['landmarks'][start_idx]['x'], hand['landmarks'][start_idx]['y'])
                end_pt = (hand['landmarks'][end_idx]['x'], hand['landmarks'][end_idx]['y'])
                
                cv2.line(frame, start_pt, end_pt, (0, 255, 0), 2)
            
            # Draw points
            for lm in hand['landmarks']:
                cv2.circle(frame, (lm['x'], lm['y']), 4, (0, 0, 255), -1)
            
            # Draw Label
            wrist = hand['landmarks'][0]
            cv2.putText(frame, f"{hand['label']} ({int(hand['score']*100)}%)", 
                        (wrist['x'], wrist['y'] - 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        # FPS Calculation
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time) if prev_time > 0 else 0
        prev_time = curr_time
        
        cv2.putText(frame, f"FPS: {int(fps)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow('Hand Tracking Verification', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    tracker.close()

if __name__ == "__main__":
    main()
