# GestureCanvas User Guide

## Getting Started

### 1. Setup
Ensure you have a webcam connected and the application is running (`python app.py`).
Open your browser to the URL shown in the terminal (usually `http://localhost:7860`).

### 2. Initialization
Click the **"🚀 Initialize System"** button. Wait for the status message to say "System initialized successfully".

---

## Mastering Gestures

### ☝️ Drawing (POINTING)
- **How**: Extend your index finger while keeping other fingers closed.
- **Action**: A green border will appear. Move your hand to draw lines on the canvas.
- **Tip**: Move smoothly for best results. The system automatically smooths your strokes.

### ✊ Stop/Hover (FIST)
- **How**: Clench your hand into a fist.
- **Action**: A blue border will appear. You can move your hand without drawing.
- **Use**: Use this to reposition your hand between strokes.

### ✋ Clear Canvas (OPEN PALM)
- **How**: Open your hand flat with all fingers extended.
- **Action**: A yellow border will appear. **Hold for 1 second** to clear the entire canvas.
- **Feedback**: A countdown timer will appear on the screen.

### 👌 Undo (PINCH)
- **How**: Pinch your thumb and index finger together.
- **Action**: A magenta border will appear. The last stroke will be removed.
- **Tip**: Pinch and release quickly to undo one step.

---

## Creating AI Art

1. **Draw**: Create a simple sketch on the canvas using gestures.
2. **Select Style**: Use the dropdown menu to choose a style:
   - **Photorealistic**: Turns sketches into real photos.
   - **Anime**: Creates Japanese animation style art.
   - **Oil Painting**: Simulates classical canvas art.
   - **Watercolor**: Soft, artistic watercolor look.
   - **Sketch**: Refines your sketch into a professional drawing.
3. **Generate**: Click **"✨ Generate Styled Image"**.
4. **Wait**: The system will process your request (usually 2-5 seconds). The result will appear on the right.

---

## Troubleshooting

### "System not initialized"
- **Cause**: You tried to draw or generate before clicking Initialize.
- **Fix**: Click the "Initialize System" button and wait for confirmation.

### Gestures not recognized
- **Lighting**: Ensure your room is well-lit. Avoid strong backlighting (windows behind you).
- **Distance**: Keep your hand 1-3 feet from the camera.
- **Background**: A plain background works best.

### Drawing feels laggy
- **Hardware**: Ensure no other heavy apps are running.
- **Browser**: Use Chrome or Firefox for best performance.
- **GPU**: If available, ensure CUDA is installed for faster AI generation.

### "Generation queue full"
- **Cause**: You clicked Generate too many times quickly.
- **Fix**: Wait for the current image to finish before clicking again.

---

## Calibration (Advanced)

If gestures feel too sensitive or unresponsive, open the **"⚙️ Calibration"** menu:

- **Hysteresis Frames**: Increase this (e.g., to 5-8) if the gesture flickers between Draw and Stop.
- **Cooldown Frames**: Increase this if you accidentally draw while trying to stop.
