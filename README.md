# GestureCanvas - AI-Powered Interactive Art

![GestureCanvas Banner](https://via.placeholder.com/800x200?text=GestureCanvas+AI+Art)

**GestureCanvas** is a real-time, gesture-controlled digital art application that transforms hand-drawn sketches into professional-quality artwork using Generative AI (Stable Diffusion).

Built with Python, OpenCV, MediaPipe, and Gradio, it offers a seamless "magical" experience where your hand movements in the air become digital art on the screen.

---

## Features

- **Hand Tracking & Gestures**: Draw in the air using natural hand movements.
- **Real-Time Canvas**: Smooth, high-quality drawing with Catmull-Rom spline interpolation.
- **AI Style Transfer**: Transform sketches into Photorealistic, Anime, Oil Painting, and more using SDXL-Turbo.
- **High Performance**: 30 FPS tracking, <2s generation, optimized with threading and dirty rectangle rendering.
- **Interactive UI**: Complete web interface with webcam streaming, gesture feedback, and calibration.

---

##  Installation

### Prerequisites
- Python 3.10 or higher
- Webcam
- (Optional) NVIDIA GPU with 6GB+ VRAM for faster generation

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/LTTakahashi/Real-Time-AI-Powered-Interactive-Art-.git
   cd Real-Time-AI-Powered-Interactive-Art-
   ```

2. **Set up environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```
   Open your browser to `http://localhost:7860`

---

## 🚀 Modern UI (React + FastAPI) - Week 5 Update

We have introduced a new, high-performance UI architecture.

### Prerequisites
- Node.js v18+
- Python 3.10+

### 1. Start the Backend
The backend handles hand tracking, gesture recognition, and Stable Diffusion generation.

```bash
# Activate virtual environment
source venv/bin/activate

# Run the server
python server.py
```
The server will start on `http://localhost:8000`.

### 2. Start the Frontend
The frontend provides a zero-latency drawing experience with a glassmorphism UI.

```bash
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```
Open `http://localhost:5173` in your browser.

### 3. Usage
- **Draw**: Point with your index finger.
- **Stop Drawing**: Close your hand or stop pointing.
- **Clear**: Hold an Open Palm for 1 second.
- **Undo**: Pinch (Thumb + Index).
- **Generate**: Select a style and click the "GENERATE" button.

---

## 🐍 Classic UI (Gradio)
If you prefer the classic all-in-one Python interface:

### Gestures

| Gesture | Action | Description |
|---------|--------|-------------
| **POINTING**  | **Draw** | Move index finger to draw. Green border. |
| **FIST**  | **Stop** | Clench fist to stop drawing/hover. Blue border. |
| **OPEN PALM**  | **Clear** | Hold open palm for 1 second to clear canvas. Yellow border. |
| **PINCH**  | **Undo** | Pinch thumb and index finger to undo last stroke. Magenta border. |

### Interface Controls

- **Initialize System**: Starts the webcam and AI models.
- **Style Selection**: Choose from Photorealistic, Anime, Oil Painting, Watercolor, or Sketch.
- **Generate**: Transform your current canvas into the selected style.
- **Calibration**: Adjust sensitivity in the "Calibration" accordion.

---

## Architecture

GestureCanvas uses a multi-threaded architecture for maximum performance:

1. **Hand Tracking Thread**: Captures webcam frames and processes MediaPipe landmarks (30 FPS).
2. **Main Thread**: Handles UI event loop, canvas rendering, and user interaction.
3. **Generation Thread**: Processes Stable Diffusion requests asynchronously to prevent UI freezing.

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system design.

---

## Testing

Run the comprehensive test suite to verify installation:

```bash
# Run all tests
python verify_installation.py

# Run specific test suites
python tests/test_unit.py         # Week 1: Gestures
python tests/test_canvas.py       # Week 2: Canvas
python tests/test_threading.py    # Week 3: Threading
python tests/test_performance.py  # Week 3: Optimization
```

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*Created by Takahashi Team*
