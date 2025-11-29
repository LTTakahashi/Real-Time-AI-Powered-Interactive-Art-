# Test Data Directory

This directory contains video files for automated testing of the hand tracking and gesture recognition system.

## Structure

```
test_data/
├── gestures/
│   ├── fist.mp4
│   ├── open_palm.mp4
│   ├── pointing.mp4
│   └── pinch.mp4
├── scenarios/
│   ├── rapid_transitions.mp4
│   ├── poor_lighting.mp4
│   └── multiple_hands.mp4
└── README.md
```

## Dataset Sources

### Recommended Public Datasets

1. **HaGRID (Hand Gesture Recognition Image Dataset)**
   - URL: https://github.com/hukenovs/hagrid
   - Contains 18 gesture classes with 550k+ images
   - Can be converted to video sequences

2. **NUS Hand Posture Dataset II**
   - URL: https://www.ece.nus.edu.sg/stfpage/elepv/NUS-HandSet/
   - Contains various hand gestures in different conditions

3. **20BN Jester Dataset**
   - URL: https://developer.qualcomm.com/software/ai-datasets/jester
   - 148k video clips of hand gestures

### Creating Your Own Test Videos

If you have a webcam, you can record your own test videos using:

```bash
venv/bin/python scripts/record_test_video.py --gesture fist --output test_data/gestures/fist.mp4
```

## Usage

Run automated tests:
```bash
venv/bin/python tests/test_with_videos.py
```
