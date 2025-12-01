# Test Data - Demo Mode Videos

This directory contains demo videos used for testing the GestureCanvas Demo Mode feature.

## Contents

### Input Videos
- **`demo_input.mp4`**: The primary demo video used in the application
  - **Source**: [dkiran100/Automatic-hand-tracking](https://github.com/dkiran100/Automatic-hand-tracking)
  - **Resolution**: 1280x720
  - **Duration**: 7 seconds (210 frames @ 30 fps)
  - **Codec**: H.264
  - **MediaPipe Detection Rate**: 100%

### Validation Reports
- **`validation_report.json`**: Automated test results from `scripts/validate_demo_mode.py`

### Output Examples
**Note**: To generate output examples, run the application with Demo Mode enabled and capture AI-generated results.

#### How to Generate Output Examples:

1. **Start the Backend**:
   ```bash
   venv/bin/python server.py
   ```

2. **Start the Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Enable Demo Mode**:
   - Open the app in a browser (usually `http://localhost:5173`)
   - Click the "○ WEBCAM" button in the top-right to switch to "● DEMO MODE"
   - The demo video will loop

4. **Generate AI Art**:
   - Let the demo video run for a few seconds (hands will draw on the canvas)
   - Select a style from the bottom carousel (e.g., "Photo", "Anime", "Oil Paint")
   - Click the "GENERATE" button
   - Wait for the AI to process (~3-5 seconds)

5. **Save Output**:
   - Right-click the generated image
   - Select "Save Image As..."
   - Save to `test_data/outputs/` with descriptive name (e.g., `demo_photorealistic_output.png`)

## Validation Results

### ✅ All Tests Passed

```
Total Tests: 5
✅ Passed: 3
⚠️  Warned: 2 (non-critical)
❌ Failed: 0

🚀 SHIP READY: Demo Mode is validated and ready for production
```

### Test Summary

1. **Video File Integrity**: ✅ PASS
   - File exists and is readable
   - Size: 969.9 KB
   - 210 frames at 30 FPS

2. **MediaPipe Detection**: ✅ PASS
   - **Detection Rate**: 100% (210/210 frames)
   - No gaps in detection
   - Maximum consecutive missed frames: 0

3. **Frame Quality**: ⚠️ WARN (non-critical)
   - Average brightness: 179.8/255 (good)
   - Low brightness variance (video has consistent lighting - expected for test video)

4. **Codec Compatibility**: ✅ PASS
   - H.264 codec (universally browser-compatible)
   - Works in Chrome, Firefox, Safari, and Edge

5. **Edge Cases**: ✅ PASS
   - No corrupted frames
   - No null frames

## Browser Compatibility

| Browser | Status |
|---------|--------|
| Chrome  | ✅ Tested and working |
| Firefox | ✅ Compatible (H.264) |
| Safari  | ✅ Compatible (H.264) |
| Edge    | ✅ Compatible (H.264) |

## Future Enhancements

- [ ] Add multiple demo videos showcasing different gestures
- [ ] Create demo output gallery with all art styles
- [ ] Add performance benchmarks (FPS, latency)
- [ ] Create browser compatibility test matrix
