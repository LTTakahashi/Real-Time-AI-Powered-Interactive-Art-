# GestureCanvas - Week 1 Testing Guide

## Testing Infrastructure

This project includes comprehensive testing at multiple levels:

### 1. **Unit Tests** (No hardware required)
Tests core logic with mock data:
```bash
venv/bin/python tests/test_unit.py
```

**What it tests:**
- Gesture recognition algorithms
- Hysteresis logic
- Performance (>100 FPS processing)

### 2. **Video-Based Tests** (Requires test videos)
Automated validation using pre-recorded videos:
```bash
venv/bin/python tests/test_with_videos.py
```

**What it tests:**
- End-to-end gesture detection
- Accuracy metrics (target: >85%)
- FPS performance (target: >20 FPS)
- Detection rate (target: >80%)

### 3. **Interactive Verification** (Requires webcam)
User-guided testing with real-time feedback:
```bash
venv/bin/python verify_week1.py
```

**What it tests:**
- Real-world usability
- All 4 core gestures
- Visual feedback quality

## Setting Up Test Data

### Option A: Record Your Own (Recommended)

1. Create test videos for each gesture:
```bash
venv/bin/python scripts/record_test_video.py --gesture fist --duration 5 --output test_data/gestures/fist.mp4
venv/bin/python scripts/record_test_video.py --gesture open_palm --duration 5 --output test_data/gestures/open_palm.mp4
venv/bin/python scripts/record_test_video.py --gesture pointing --duration 5 --output test_data/gestures/pointing.mp4
venv/bin/python scripts/record_test_video.py --gesture pinch --duration 5 --output test_data/gestures/pinch.mp4
```

2. Run automated tests:
```bash
venv/bin/python tests/test_with_videos.py
```

### Option B: Download Public Datasets

See [`test_data/README.md`](test_data/README.md) for dataset sources:
- **HaGRID**: 550k+ gesture images
- **Kaggle MediaPipe Hand Landmarks**: Pre-processed videos
- **20BN Jester**: Professional gesture videos

### Option C: Quick Validation (No videos)

Run unit tests only:
```bash
venv/bin/python tests/test_unit.py
```

## Test Results Interpretation

### Unit Tests
- **PASS**: All gesture logic and hysteresis working correctly
- **FAIL**: Review specific test failures, likely threshold tuning needed

### Video Tests
Results saved to `test_results.json`:
```json
{
  "tests_run": 4,
  "tests_passed": 4,
  "accuracy": {
    "FIST": 0.95,
    "OPEN_PALM": 0.92,
    "POINTING": 0.88,
    "PINCH": 0.85
  },
  "performance": {
    "FIST": 28.5,
    "OPEN_PALM": 29.1
  }
}
```

**Quality Thresholds (from plan):**
- ✅ Accuracy: >85% per gesture
- ✅ FPS: >20 (target 30)
- ✅ Detection rate: >80%

## Troubleshooting

### "No module named 'cv2'"
Use the virtual environment: `venv/bin/python` instead of `python`

### "Webcam NOT detected"
- WSL users: Webcam access is limited, use `--video` flag
- Check camera permissions
- Try different camera indices: `--camera 1`

### Low accuracy in video tests
- Check video quality (resolution, lighting)
- Verify gestures match expected (review video)
- Tune thresholds in `config.py`

### Low FPS
- Reduce input resolution
- Check CPU/GPU usage
- Verify MediaPipe installation

## Continuous Testing

During development, run tests frequently:
```bash
# Quick check (5 seconds)
venv/bin/python tests/test_unit.py

# Full validation (requires videos, ~1 minute)
venv/bin/python tests/test_with_videos.py
```

## Production Readiness Checklist

- [ ] Unit tests pass (100%)
- [ ] Video tests pass with >85% accuracy
- [ ] FPS consistently >25 in tests
- [ ] All 4 gestures recognized correctly
- [ ] Hysteresis prevents false triggers
- [ ] Works across different lighting conditions
- [ ] Works at different camera distances (30cm-100cm)
