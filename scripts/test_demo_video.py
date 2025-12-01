"""Test if MediaPipe can detect hands in the demo video."""
import cv2
import mediapipe as mp

def test_demo_video():
    mp_hands = mp.solutions.hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    
    cap = cv2.VideoCapture('frontend/public/demo.mp4')
    
    if not cap.isOpened():
        print("ERROR: Cannot open demo video")
        return
    
    detections = []
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Process every 30th frame (1 per second)
        if frame_count % 30 != 0:
            continue
            
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect
        results = mp_hands.process(rgb_frame)
        
        detected = results.multi_hand_landmarks is not None
        detections.append(detected)
        
        print(f"Frame {frame_count}: {'✓ HAND DETECTED' if detected else '✗ No hand'}")
    
    cap.release()
    mp_hands.close()
    
    print(f"\n=== SUMMARY ===")
    print(f"Total frames: {frame_count}")
    print(f"Sampled frames: {len(detections)}")
    print(f"Detections: {sum(detections)}/{len(detections)}")
    print(f"Detection rate: {sum(detections)/len(detections)*100:.1f}%")
    
    if sum(detections) == 0:
        print("\n🚨 CRITICAL: MediaPipe detected NO hands in demo video!")
        print("   This means the demo mode will NOT work.")
    elif sum(detections) < len(detections) * 0.5:
        print("\n⚠️  WARNING: Low detection rate. Demo may be unreliable.")
    else:
        print("\n✅ Demo video is compatible with MediaPipe.")

if __name__ == "__main__":
    test_demo_video()
