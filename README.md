# GestureCanvas - AI-Powered Interactive Art

![GestureCanvas Banner](https://via.placeholder.com/800x200?text=GestureCanvas+AI+Art)

**GestureCanvas** is a real-time, gesture-controlled digital art application that transforms hand-drawn sketches into professional-quality artwork using Generative AI (Stable Diffusion).

Experience the "Magical Mirror" effect where your hand movements instantly create glowing digital art, powered by a high-performance **FastAPI** backend and a sleek **React** frontend.

---

## Features

- **"Magical Mirror" Experience**: Zero-latency drawing on a glassmorphism UI.
- **Hand Tracking & Gestures**: Draw, Hover, and Command using natural hand movements (MediaPipe).
- **AI Style Transfer**: Instantly transform sketches into:
  - **Neon Cyberpunk**
  - **Pencil Sketch**
  - **Oil Painting**
  - **Watercolor**
  - **Pixel Art**
- **Dual Architecture**:
  - **Frontend**: React + Vite + Tailwind CSS (Visuals)
  - **Backend**: FastAPI + WebSockets + SDXL-Turbo (Logic)
- **Robustness**: 100% Test Coverage for core components.

---

## Quick Start

### Prerequisites
- **Node.js** v18+
- **Python** 3.10+
- **Webcam**
- (Optional) NVIDIA GPU (6GB+ VRAM) for faster AI generation.

### 1. Backend Setup (The Brain)
```bash
# Clone repository
git clone https://github.com/LTTakahashi/Real-Time-AI-Powered-Interactive-Art-.git
cd Real-Time-AI-Powered-Interactive-Art-

# Create & Activate Virtual Environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install Python Dependencies
pip install -r requirements.txt

# Start the API Server
python3.11 server.py
```
*Server runs at `http://localhost:8000`*

### 2. Frontend Setup (The Face)
Open a new terminal window:
```bash
cd frontend

# Install Node Dependencies
npm install

# Start the UI
npm run dev
```
*UI runs at `http://localhost:5173` (Open this in your browser)*

## Troubleshooting

- **"Disconnected" Status**: Refresh the page. The frontend will automatically reconnect to the backend via the configured proxy.
- **Generation Timeout**: If generation hangs or fails, restart the backend server (`Ctrl+C` then `python3.11 server.py`).
- **Camera Not Working**: Ensure you've granted browser permissions. If using WSL, ensure your camera is accessible or use a virtual webcam.

---

## User Guide

### Gestures
| Gesture | Action | Visual Feedback |
|---------|--------|-----------------|
| **POINTING** | **Draw** | Green Cursor + Trail |
| **OPEN PALM** | **Hover** | Blue Cursor (No Draw) |
| **FIST** | **Stop** | Cursor Disappears |
| **PINCH** | **Undo** | Flash Magenta |
| **HOLD PALM** (1s) | **Clear** | Flash Yellow |

### Controls
- **Style Selector**: Click the circular icons at the bottom to change the AI art style.
- **Generate**: Click the "GENERATE" button (or use a custom gesture if configured) to create AI art.
- **Status Pill**: Watch the top-left indicator for system state (Idle, Drawing, Processing).

---

## Architecture

GestureCanvas uses a decoupled **Client-Server** architecture:

1.  **Frontend (React)**: Captures webcam video, renders the drawing canvas, and handles user interaction. It streams video frames to the backend via **WebSockets**.
2.  **Backend (FastAPI)**:
    - **Hand Tracking**: Processes frames with MediaPipe.
    - **Gesture Engine**: Recognizes intent (Draw, Clear, Undo).
    - **Stable Diffusion**: Generates artwork on demand via REST API.

See [ARCHITECTURE.md](ARCHITECTURE.md) for deep dives.

---

## Testing

We maintain rigorous testing standards.

### Backend Tests
```bash
python verify_installation.py  # Run full suite
# OR
python -m unittest tests/test_canvas.py
```

### Frontend Tests
```bash
cd frontend
npm test  # Runs Vitest
```

---

## Legacy Mode (Gradio)
For the classic all-in-one Python interface (Week 1-4 version):
```bash
python app.py
```
*Runs at `http://localhost:7860`*

---

## License
MIT License - see [LICENSE](LICENSE).

*Created by Takahashi Team*
