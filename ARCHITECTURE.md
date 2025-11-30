# GestureCanvas Architecture

## System Overview

GestureCanvas is a real-time interactive application that combines computer vision (MediaPipe), generative AI (Stable Diffusion), and a reactive user interface (Gradio).

### High-Level Diagram

```mermaid
graph TD
    Webcam -->|Frames| HandTracking[Hand Tracking Thread]
    HandTracking -->|Landmarks| GestureRec[Gesture Recognition]
    GestureRec -->|State| SharedState[Thread-Safe State]
    
    SharedState -->|Read| Canvas[Canvas System]
    Canvas -->|Draw| Buffer[Dual Buffers]
    
    User[User] -->|Interact| UI[Gradio UI (Main Thread)]
    UI -->|Display| WebBrowser
    
    UI -->|Request| GenQueue[Generation Queue]
    GenQueue -->|Process| SDThread[Generation Thread]
    SDThread -->|Image| ResultQueue
    ResultQueue -->|Update| UI
```

---

## Core Components

### 1. Threading Architecture (`threading_manager.py`)

The system uses a 3-thread design to ensure responsiveness:

- **Hand Tracking Thread**: 
  - dedicated to webcam capture and MediaPipe inference.
  - Runs at ~30 FPS independent of UI rendering.
  - Updates `ThreadSafeGestureState` with minimal lock contention (<0.5ms).

- **Main Thread (UI)**:
  - Runs the Gradio event loop.
  - Handles canvas rendering logic (`canvas.py`).
  - Polls for generation results.

- **Generation Thread**:
  - Dedicated to Stable Diffusion inference.
  - Processes requests from `GenerationQueue`.
  - Manages VRAM (clears cache after generation).

### 2. Canvas System (`canvas.py`)

- **Dual-Buffer Design**:
  - `internal_buffer`: 1024x1024 high-resolution state.
  - `display_buffer`: Viewport-sized for UI display.
  
- **Stroke Smoothing**:
  - Uses Catmull-Rom spline interpolation.
  - Generates 5 intermediate points between detected landmarks for smooth curves.

- **Undo/Redo**:
  - Diff-based storage strategy.
  - Stores only the bounding box of changed pixels.
  - Reduces memory usage by >90% compared to storing full frames.

### 3. Style Transfer (`style_transfer.py`)

- **Model**: SDXL-Turbo (default) for fast inference.
- **Smart Cropping**:
  1. Detects bounding box of drawn content.
  2. Adds 15% margin.
  3. Resizes to 512x512 (maintaining aspect ratio).
- **Optimization**:
  - Attention slicing enabled for lower VRAM usage.
  - VAE slicing enabled.

### 4. Performance Optimization (`performance.py`)

- **Dirty Rectangle Rendering**: Only redraws parts of the canvas that changed.
- **Gesture Caching**: Avoids recomputing gesture logic for the same frame.
- **Intelligent Frame Skipping**: Processes gestures at 20 FPS while displaying video at 30 FPS to save CPU.

---

## Data Flow

1. **Input**: Webcam frame captured.
2. **Processing**: Hand landmarks detected -> Gesture recognized (e.g., "POINTING").
3. **State Update**: Shared state updated with gesture and coordinates.
4. **Rendering**:
   - If "POINTING": Canvas adds point to current stroke.
   - If "FIST": Stroke ends.
   - If "PINCH": Undo action triggered.
5. **Generation**:
   - User clicks "Generate".
   - Canvas image captured -> Smart cropped -> Sent to Generation Queue.
   - SD Thread processes -> Returns result -> UI updates.

## Directory Structure

```
.
├── app.py                 # Main entry point (Gradio UI)
├── canvas.py              # Canvas logic & rendering
├── config.py              # Configuration constants
├── gesture_recognition.py # Rule-based gesture logic
├── hand_tracking.py       # MediaPipe wrapper
├── performance.py         # Optimization utilities
├── style_transfer.py      # Stable Diffusion integration
├── threading_manager.py   # Thread coordination
├── requirements.txt       # Dependencies
├── tests/                 # Comprehensive test suite
│   ├── test_canvas.py
│   ├── test_performance.py
│   ├── test_style_transfer.py
│   ├── test_threading.py
│   └── test_unit.py
└── test_data/             # Test assets
```
