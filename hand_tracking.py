import cv2
import mediapipe as mp
import numpy as np
from config import HAND_TRACKING_CONF, SMOOTHING_ALPHA

class HandTracker:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=HAND_TRACKING_CONF['max_num_hands'],
            min_detection_confidence=HAND_TRACKING_CONF['min_detection_confidence'],
            min_tracking_confidence=HAND_TRACKING_CONF['min_tracking_confidence'],
            model_complexity=HAND_TRACKING_CONF['model_complexity']
        )

        
        # History for smoothing: {hand_id: {landmark_id: (x, y)}}
        # Since MediaPipe doesn't provide persistent IDs across frames easily without extra logic,
        # we will assume index 0 is always the first hand and index 1 is the second for simplicity in Week 1.
        # A more robust ID tracking would be needed for complex interactions, but this suffices for basic smoothing.
        self.prev_landmarks = {} 

    def process_frame(self, frame):
        """
        Process a BGR frame and return tracked hand data.
        """
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        tracked_hands = []
        
        if results.multi_hand_landmarks:
            for i, (hand_landmarks, handedness) in enumerate(zip(results.multi_hand_landmarks, results.multi_handedness)):
                # Get Hand Label (Left/Right)
                # MediaPipe assumes mirrored image by default? No, it depends on input.
                # Usually: Label 'Left' means it appears on the left side of the image (which is the user's right hand if mirrored).
                # We will store the label as given by MediaPipe.
                label = handedness.classification[0].label
                score = handedness.classification[0].score
                
                # Convert to pixel coordinates and smooth
                smoothed_landmarks = []
                
                # Initialize history for this hand index if needed
                if i not in self.prev_landmarks:
                    self.prev_landmarks[i] = {}

                for idx, lm in enumerate(hand_landmarks.landmark):
                    px, py = int(lm.x * w), int(lm.y * h)
                    
                    # Apply EMA Smoothing
                    if idx in self.prev_landmarks[i]:
                        prev_x, prev_y = self.prev_landmarks[i][idx]
                        smooth_x = int(prev_x * (1 - SMOOTHING_ALPHA) + px * SMOOTHING_ALPHA)
                        smooth_y = int(prev_y * (1 - SMOOTHING_ALPHA) + py * SMOOTHING_ALPHA)
                    else:
                        smooth_x, smooth_y = px, py
                    
                    # Update history
                    self.prev_landmarks[i][idx] = (smooth_x, smooth_y)
                    
                    # Store smoothed landmark (including z for depth, not smoothed yet as per plan)
                    smoothed_landmarks.append({
                        'x': smooth_x,
                        'y': smooth_y,
                        'z': lm.z  # Relative depth
                    })
                
                tracked_hands.append({
                    'id': i,
                    'label': label,
                    'score': score,
                    'landmarks': smoothed_landmarks,
                    'raw_landmarks': hand_landmarks # Keep raw for debug if needed
                })
        else:
            self.prev_landmarks = {} # Reset history if no hands found
            
        return tracked_hands

    def close(self):
        self.hands.close()
