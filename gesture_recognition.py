import numpy as np
import math
from collections import deque
from config import GESTURE_THRESHOLDS

class GestureRecognizer:
    def __init__(self):
        self.history = deque(maxlen=20) # For motion detection (Circle)
        self.gesture_buffer = deque(maxlen=GESTURE_THRESHOLDS['hysteresis_frames'])
        self.cooldown_counter = 0
        self.last_gesture = "NONE"

    def _get_distance(self, p1, p2):
        return math.sqrt((p1['x'] - p2['x'])**2 + (p1['y'] - p2['y'])**2)

    def _get_3d_distance(self, p1, p2):
        # Note: z is relative, x/y are pixels. This is a rough approximation.
        # Ideally we'd de-normalize x/y or normalize z to aspect ratio.
        # For now, we use a simple Euclidean check assuming z scale is somewhat comparable after tuning.
        return math.sqrt((p1['x'] - p2['x'])**2 + (p1['y'] - p2['y'])**2 + (p1['z']*1000 - p2['z']*1000)**2)

    def detect_gesture(self, hand_landmarks):
        """
        Detects gesture from a single hand's landmarks.
        Returns: gesture_name (str)
        """
        if self.cooldown_counter > 0:
            self.cooldown_counter -= 1
            return self.last_gesture

        # Shortcuts for landmarks
        wrist = hand_landmarks[0]
        thumb_tip = hand_landmarks[4]
        index_mcp = hand_landmarks[5]
        index_tip = hand_landmarks[8]
        middle_mcp = hand_landmarks[9]
        middle_tip = hand_landmarks[12]
        ring_tip = hand_landmarks[16]
        pinky_tip = hand_landmarks[20]

        # Calculate hand scale (Wrist to Middle MCP)
        hand_scale = self._get_distance(wrist, middle_mcp)
        if hand_scale == 0: hand_scale = 1 # Prevent div by zero

        # --- Rule Checks ---

        # 1. Check Finger Extensions
        # A finger is extended if tip is further from wrist than MCP is.
        # We can use a ratio threshold.
        
        def is_extended(tip, mcp):
            return self._get_distance(wrist, tip) > self._get_distance(wrist, mcp) * 1.2

        index_ext = is_extended(index_tip, index_mcp)
        middle_ext = is_extended(middle_tip, middle_mcp)
        ring_ext = is_extended(ring_tip, hand_landmarks[13])
        pinky_ext = is_extended(pinky_tip, hand_landmarks[17])

        # 2. Pinch Check (Thumb to Index)
        pinch_dist = self._get_distance(thumb_tip, index_tip)
        is_pinch = pinch_dist < (hand_scale * 0.3) # Threshold from plan: 0.04 * diagonal? Let's tune. 0.3 of palm size is reasonable.
        
        # Plan says: "less than 0.04 times the hand bounding box diagonal distance"
        # Let's approximate bounding box diagonal as 2.5 * hand_scale
        # 0.04 * 2.5 = 0.1. So 0.1 * hand_scale might be too tight.
        # Let's stick to a safe 0.2 for now.

        # --- Priority Logic ---
        
        current_gesture = "UNKNOWN"

        # PINCH (Highest Priority)
        if is_pinch:
            current_gesture = "PINCH"
        
        # FIST (All fingers closed)
        elif not index_ext and not middle_ext and not ring_ext and not pinky_ext:
            current_gesture = "FIST"

        # INDEX POINTING (Index open, others closed)
        elif index_ext and not middle_ext and not ring_ext and not pinky_ext:
            current_gesture = "POINTING"
            
            # Update history for Circle detection
            self.history.append(index_tip)
            # TODO: Implement circle detection logic here if needed
            
        # OPEN PALM (All open)
        elif index_ext and middle_ext and ring_ext and pinky_ext:
            current_gesture = "OPEN_PALM"
        
        else:
            current_gesture = "NONE"

        # --- Hysteresis ---
        self.gesture_buffer.append(current_gesture)
        
        # Only change state if all frames in buffer match
        if all(g == current_gesture for g in self.gesture_buffer):
            if current_gesture != self.last_gesture:
                self.last_gesture = current_gesture
                self.cooldown_counter = GESTURE_THRESHOLDS['cooldown_frames']
        
        return self.last_gesture
