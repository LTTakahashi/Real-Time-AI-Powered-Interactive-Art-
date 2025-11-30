"""
Threading manager for GestureCanvas application.
Coordinates 3 concurrent threads: UI/main, hand tracking, and SD generation.
Implements thread-safe state synchronization and proper resource management.
"""

import threading
import queue
import time
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
import numpy as np
from collections import deque

@dataclass
class GestureState:
    """Thread-safe gesture state container."""
    gesture: str = "NONE"
    hand_landmarks: Optional[list] = None
    index_tip_pos: Optional[tuple] = None  # (x, y)
    timestamp: float = 0.0
    hand_detected: bool = False

@dataclass
class GenerationRequest:
    """Style transfer generation request."""
    request_id: str
    canvas_image: np.ndarray
    style: str
    timestamp: float
    callback: Optional[Callable] = None

@dataclass
class GenerationResult:
    """Style transfer generation result."""
    request_id: str
    styled_image: Any  # PIL Image
    metadata: Dict[str, Any]
    success: bool
    error: Optional[str] = None


class ThreadSafeGestureState:
    """Thread-safe wrapper for gesture state with minimal lock hold time."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._state = GestureState()
        self._lock_hold_times = deque(maxlen=1000)  # Track lock performance
    
    def update(self, gesture: str = None, hand_landmarks: list = None,
               index_tip_pos: tuple = None, hand_detected: bool = None):
        """Update state with minimal lock hold time."""
        start = time.perf_counter()
        
        with self._lock:
            if gesture is not None:
                self._state.gesture = gesture
            if hand_landmarks is not None:
                self._state.hand_landmarks = hand_landmarks
            if index_tip_pos is not None:
                self._state.index_tip_pos = index_tip_pos
            if hand_detected is not None:
                self._state.hand_detected = hand_detected
            self._state.timestamp = time.time()
        
        hold_time = (time.perf_counter() - start) * 1000  # ms
        self._lock_hold_times.append(hold_time)
    
    def get(self) -> GestureState:
        """Get current state (creates copy to avoid holding lock)."""
        with self._lock:
            # Deep copy to release lock quickly
            return GestureState(
                gesture=self._state.gesture,
                hand_landmarks=self._state.hand_landmarks.copy() if self._state.hand_landmarks else None,
                index_tip_pos=self._state.index_tip_pos,
                timestamp=self._state.timestamp,
                hand_detected=self._state.hand_detected
            )
    
    def get_lock_stats(self) -> Dict[str, float]:
        """Get lock contention statistics."""
        if not self._lock_hold_times:
            return {'avg_ms': 0, 'max_ms': 0, 'count': 0}
        
        return {
            'avg_ms': sum(self._lock_hold_times) / len(self._lock_hold_times),
            'max_ms': max(self._lock_hold_times),
            'count': len(self._lock_hold_times)
        }


class ThreadSafeFrameBuffer:
    """Non-blocking frame buffer for webcam frames."""
    
    def __init__(self, maxsize: int = 2):
        self._queue = queue.Queue(maxsize=maxsize)
        self._latest_frame = None
        self._lock = threading.Lock()
    
    def put(self, frame: np.ndarray):
        """Put frame (non-blocking, drops old if full)."""
        # Try to put, if full, drop oldest and try again
        try:
            self._queue.put_nowait(frame)
        except queue.Full:
            try:
                self._queue.get_nowait()  # Drop oldest
                self._queue.put_nowait(frame)
            except:
                pass
        
        # Also keep latest for immediate access
        with self._lock:
            self._latest_frame = frame
    
    def get_latest(self) -> Optional[np.ndarray]:
        """Get latest frame (non-blocking)."""
        with self._lock:
            return self._latest_frame.copy() if self._latest_frame is not None else None


class GenerationQueue:
    """Thread-safe generation request queue with VRAM management."""
    
    def __init__(self, max_queue_size: int = 5):
        self._queue = queue.Queue(maxsize=max_queue_size)
        self._lock = threading.Lock()
        self._current_request: Optional[GenerationRequest] = None
        self._queue_position = {}  # request_id -> position
    
    def add_request(self, request: GenerationRequest) -> bool:
        """Add generation request (non-blocking)."""
        try:
            self._queue.put_nowait(request)
            self._update_positions()
            return True
        except queue.Full:
            return False  # Queue full
    
    def get_request(self, timeout: float = 0.1) -> Optional[GenerationRequest]:
        """Get next request (blocking with timeout)."""
        try:
            request = self._queue.get(timeout=timeout)
            with self._lock:
                self._current_request = request
            self._update_positions()
            return request
        except queue.Empty:
            return None
    
    def mark_complete(self):
        """Mark current request as complete."""
        with self._lock:
            self._current_request = None
    
    def get_queue_position(self, request_id: str) -> Optional[int]:
        """Get position of request in queue (0 = currently processing)."""
        return self._queue_position.get(request_id)
    
    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()
    
    def is_processing(self) -> bool:
        """Check if currently processing a request."""
        with self._lock:
            return self._current_request is not None
    
    def _update_positions(self):
        """Update queue position tracking."""
        with self._lock:
            self._queue_position.clear()
            
            # Current request is position 0
            if self._current_request:
                self._queue_position[self._current_request.request_id] = 0
            
            # Queue items are positions 1, 2, 3...
            items = list(self._queue.queue)
            for i, req in enumerate(items):
                self._queue_position[req.request_id] = i + 1


class ThreadingManager:
    """Central coordinator for all threading operations."""
    
    def __init__(self):
        # Thread-safe state
        self.gesture_state = ThreadSafeGestureState()
        self.frame_buffer = ThreadSafeFrameBuffer()
        self.generation_queue = GenerationQueue()
        self.result_queue = queue.Queue()
        
        # Thread references
        self.hand_tracking_thread: Optional[threading.Thread] = None
        self.generation_thread: Optional[threading.Thread] = None
        
        # Control flags
        self._shutdown = threading.Event()
        self._tracking_enabled = threading.Event()
        self._tracking_enabled.set()  # Start enabled
        
        # Error tracking
        self._errors = queue.Queue()
    
    def start_hand_tracking_thread(self, hand_tracker, gesture_recognizer, 
                                   camera_index: int = 0):
        """Start hand tracking thread."""
        def tracking_loop():
            import cv2
            
            # Open camera in this thread
            cap = cv2.VideoCapture(camera_index)
            if not cap.isOpened():
                self._errors.put(("hand_tracking", "Failed to open camera"))
                return
            
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            
            try:
                while not self._shutdown.is_set():
                    if not self._tracking_enabled.is_set():
                        time.sleep(0.1)
                        continue
                    
                    ret, frame = cap.read()
                    if not ret:
                        continue
                    
                    frame = cv2.flip(frame, 1)
                    
                    # Put in frame buffer
                    self.frame_buffer.put(frame)
                    
                    # Process hand tracking
                    hands_data = hand_tracker.process_frame(frame)
                    
                    if hands_data:
                        hand = hands_data[0]
                        gesture = gesture_recognizer.detect_gesture(hand['landmarks'])
                        index_tip = hand['landmarks'][8]
                        
                        self.gesture_state.update(
                            gesture=gesture,
                            hand_landmarks=hand['landmarks'],
                            index_tip_pos=(index_tip['x'], index_tip['y']),
                            hand_detected=True
                        )
                    else:
                        self.gesture_state.update(
                            gesture="NONE",
                            hand_landmarks=None,
                            index_tip_pos=None,
                            hand_detected=False
                        )
            
            except Exception as e:
                self._errors.put(("hand_tracking", str(e)))
            
            finally:
                cap.release()
        
        self.hand_tracking_thread = threading.Thread(target=tracking_loop, daemon=True)
        self.hand_tracking_thread.start()
    
    def start_generation_thread(self, style_transfer_system):
        """Start style transfer generation thread."""
        def generation_loop():
            try:
                while not self._shutdown.is_set():
                    # Get next request
                    request = self.generation_queue.get_request(timeout=0.5)
                    
                    if request is None:
                        continue
                    
                    try:
                        # Generate
                        styled_image, metadata = style_transfer_system.generate(
                            request.canvas_image,
                            style=request.style,
                            num_inference_steps=4
                        )
                        
                        # Clear VRAM cache
                        style_transfer_system.clear_cache()
                        
                        # Queue result
                        result = GenerationResult(
                            request_id=request.request_id,
                            styled_image=styled_image,
                            metadata=metadata,
                            success=True
                        )
                        self.result_queue.put(result)
                        
                        # Callback if provided
                        if request.callback:
                            request.callback(result)
                    
                    except Exception as e:
                        result = GenerationResult(
                            request_id=request.request_id,
                            styled_image=None,
                            metadata={},
                            success=False,
                            error=str(e)
                        )
                        self.result_queue.put(result)
                    
                    finally:
                        self.generation_queue.mark_complete()
            
            except Exception as e:
                self._errors.put(("generation", str(e)))
        
        self.generation_thread = threading.Thread(target=generation_loop, daemon=True)
        self.generation_thread.start()
    
    def pause_hand_tracking(self):
        """Pause hand tracking (for performance)."""
        self._tracking_enabled.clear()
    
    def resume_hand_tracking(self):
        """Resume hand tracking."""
        self._tracking_enabled.set()
    
    def shutdown(self, timeout: float = 5.0):
        """Shutdown all threads gracefully."""
        self._shutdown.set()
        
        # Wait for threads
        threads = [t for t in [self.hand_tracking_thread, self.generation_thread] if t]
        for thread in threads:
            thread.join(timeout=timeout)
    
    def get_errors(self) -> list:
        """Get all errors."""
        errors = []
        while not self._errors.empty():
            try:
                errors.append(self._errors.get_nowait())
            except queue.Empty:
                break
        return errors
    
    def get_stats(self) -> Dict[str, Any]:
        """Get threading statistics."""
        return {
            'gesture_lock_stats': self.gesture_state.get_lock_stats(),
            'generation_queue_size': self.generation_queue.get_queue_size(),
            'is_generating': self.generation_queue.is_processing(),
            'errors': len(self.get_errors())
        }
