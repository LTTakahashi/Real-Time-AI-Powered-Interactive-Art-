# MediaPipe Hand Tracking Configuration
HAND_TRACKING_CONF = {
    'max_num_hands': 2,
    'min_detection_confidence': 0.7,  # Higher to reduce false positives
    'min_tracking_confidence': 0.5,
    'model_complexity': 1  # 0 or 1. 1 is more accurate but slower.
}

# Smoothing Configuration
SMOOTHING_ALPHA = 0.3  # Exponential Moving Average factor (0.0 - 1.0). Lower = more smooth, more lag.

# Gesture Recognition Thresholds
GESTURE_THRESHOLDS = {
    'finger_extended_ratio': 1.3,  # Tip-to-wrist / MCP-to-wrist ratio
    'pinch_distance_ratio': 0.04,  # Distance / Hand Scale
    'hysteresis_frames': 3,        # Frames to confirm gesture
    'cooldown_frames': 5           # Frames to ignore changes after trigger
}

# Canvas Configuration
CANVAS_SIZE = (1024, 1024)
DISPLAY_SIZE = (1280, 720)  # Target display size
