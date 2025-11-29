"""
Canvas system with dual-buffer architecture, stroke smoothing, and efficient undo/redo.
Implements high-resolution 1024x1024 internal canvas with viewport rendering.
"""

import numpy as np
import cv2
from typing import List, Tuple, Optional
from dataclasses import dataclass
import time

@dataclass
class Point:
    x: float
    y: float

@dataclass
class Stroke:
    points: List[Point]
    color: Tuple[int, int, int]
    thickness: int
    timestamp: float

class CanvasUndoManager:
    """Efficient undo/redo using diff-based storage."""
    
    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.history = []  # List of (bbox, diff_data)
        self.redo_stack = []
    
    def save_state(self, canvas_before: np.ndarray, canvas_after: np.ndarray):
        """Save only the changed region (diff-based compression)."""
        # Find bounding box of changes
        diff = np.any(canvas_before != canvas_after, axis=2)
        if not diff.any():
            return  # No changes
        
        rows, cols = np.where(diff)
        y1, y2 = rows.min(), rows.max() + 1
        x1, x2 = cols.min(), cols.max() + 1
        
        # Store bbox and the diff region
        bbox = (x1, y1, x2, y2)
        diff_data = canvas_before[y1:y2, x1:x2].copy()
        
        self.history.append((bbox, diff_data))
        self.redo_stack.clear()  # Clear redo on new action
        
        # Limit history size
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    def undo(self, canvas: np.ndarray) -> Optional[np.ndarray]:
        """Undo last change."""
        if not self.history:
            return None
        
        bbox, diff_data = self.history.pop()
        x1, y1, x2, y2 = bbox
        
        # Save current state to redo stack
        self.redo_stack.append((bbox, canvas[y1:y2, x1:x2].copy()))
        
        # Restore previous state
        canvas[y1:y2, x1:x2] = diff_data
        return canvas
    
    def redo(self, canvas: np.ndarray) -> Optional[np.ndarray]:
        """Redo last undone change."""
        if not self.redo_stack:
            return None
        
        bbox, diff_data = self.redo_stack.pop()
        x1, y1, x2, y2 = bbox
        
        # Save to history
        self.history.append((bbox, canvas[y1:y2, x1:x2].copy()))
        
        # Restore redo state
        canvas[y1:y2, x1:x2] = diff_data
        return canvas
    
    def get_memory_usage(self) -> int:
        """Calculate approximate memory usage in bytes."""
        total = 0
        for bbox, data in self.history + self.redo_stack:
            total += data.nbytes
        return total


class CatmullRomSpline:
    """Catmull-Rom spline interpolation for smooth strokes."""
    
    @staticmethod
    def interpolate(points: List[Point], num_segments: int = 5) -> List[Point]:
        """Generate smooth curve through points."""
        if len(points) < 2:
            return points
        
        if len(points) == 2:
            return CatmullRomSpline._linear_interpolate(points[0], points[1], num_segments)
        
        # Need at least 4 points for Catmull-Rom, pad if necessary
        padded = [points[0]] + points + [points[-1]]
        
        smooth_points = []
        for i in range(len(points) - 1):
            p0 = padded[i]
            p1 = padded[i + 1]
            p2 = padded[i + 2]
            p3 = padded[i + 3] if i + 3 < len(padded) else padded[-1]
            
            segment = CatmullRomSpline._catmull_rom_segment(p0, p1, p2, p3, num_segments)
            smooth_points.extend(segment[:-1])  # Avoid duplicates
        
        smooth_points.append(points[-1])
        return smooth_points
    
    @staticmethod
    def _catmull_rom_segment(p0: Point, p1: Point, p2: Point, p3: Point, 
                            num_segments: int) -> List[Point]:
        """Interpolate between p1 and p2 using p0 and p3 for curvature."""
        result = []
        for i in range(num_segments + 1):
            t = i / num_segments
            t2 = t * t
            t3 = t2 * t
            
            # Catmull-Rom matrix
            x = 0.5 * ((2 * p1.x) +
                       (-p0.x + p2.x) * t +
                       (2 * p0.x - 5 * p1.x + 4 * p2.x - p3.x) * t2 +
                       (-p0.x + 3 * p1.x - 3 * p2.x + p3.x) * t3)
            
            y = 0.5 * ((2 * p1.y) +
                       (-p0.y + p2.y) * t +
                       (2 * p0.y - 5 * p1.y + 4 * p2.y - p3.y) * t2 +
                       (-p0.y + 3 * p1.y - 3 * p2.y + p3.y) * t3)
            
            result.append(Point(x, y))
        
        return result
    
    @staticmethod
    def _linear_interpolate(p1: Point, p2: Point, num_segments: int) -> List[Point]:
        """Simple linear interpolation for 2-point case."""
        result = []
        for i in range(num_segments + 1):
            t = i / num_segments
            x = p1.x + (p2.x - p1.x) * t
            y = p1.y + (p2.y - p1.y) * t
            result.append(Point(x, y))
        return result


class GestureCanvas:
    """High-resolution canvas with gesture-controlled drawing."""
    
    def __init__(self, internal_size=(1024, 1024), display_size=(1280, 720)):
        self.internal_size = internal_size
        self.display_size = display_size
        
        # Dual buffers
        self.canvas = np.full((*internal_size, 3), 255, dtype=np.uint8)  # White background
        self.display_buffer = np.full((*display_size, 3), 255, dtype=np.uint8)
        
        # Drawing state
        self.current_stroke: List[Point] = []
        self.is_drawing = False
        self.brush_color = (0, 0, 0)  # Black
        self.brush_thickness = 3
        
        # Undo/redo
        self.undo_manager = CanvasUndoManager(max_history=50)
        
        # Performance tracking
        self.dirty_rect: Optional[Tuple[int, int, int, int]] = None
    
    def gesture_to_canvas_coords(self, gesture_x: int, gesture_y: int,
                                 gesture_frame_size: Tuple[int, int]) -> Tuple[int, int]:
        """
        Transform gesture coordinates to canvas coordinates.
        Handles aspect ratio differences between gesture space and canvas.
        """
        gw, gh = gesture_frame_size
        cw, ch = self.internal_size
        
        # Normalize to [0, 1]
        norm_x = gesture_x / gw
        norm_y = gesture_y / gh
        
        # Apply aspect ratio correction
        # Vertical range is typically more limited in gestures
        # Apply a slight vertical scaling to compensate
        aspect_correction = 1.2
        norm_y = norm_y * aspect_correction
        norm_y = np.clip(norm_y, 0, 1)
        
        # Map to canvas
        canvas_x = int(norm_x * cw)
        canvas_y = int(norm_y * ch)
        
        return canvas_x, canvas_y
    
    def start_stroke(self, x: int, y: int):
        """Begin a new stroke."""
        self.is_drawing = True
        self.current_stroke = [Point(x, y)]
        self._save_undo_checkpoint()
    
    def add_point(self, x: int, y: int):
        """Add point to current stroke."""
        if not self.is_drawing:
            return
        
        self.current_stroke.append(Point(x, y))
        
        # Draw smooth line from previous point
        if len(self.current_stroke) >= 2:
            self._draw_smooth_segment()
    
    def end_stroke(self):
        """Finish current stroke."""
        if self.is_drawing and len(self.current_stroke) > 1:
            # Final smoothing pass
            self._draw_final_stroke()
        
        self.is_drawing = False
        self.current_stroke = []
    
    def _save_undo_checkpoint(self):
        """Save current canvas state for undo."""
        self.canvas_before_stroke = self.canvas.copy()
    
    def _draw_smooth_segment(self):
        """Draw smoothed segment using Catmull-Rom splines."""
        if len(self.current_stroke) < 2:
            return
        
        # Get recent points for local smoothing
        recent = self.current_stroke[-4:] if len(self.current_stroke) >= 4 else self.current_stroke
        smooth = CatmullRomSpline.interpolate(recent, num_segments=5)
        
        # Draw only the new segment
        for i in range(len(smooth) - 1):
            p1 = smooth[i]
            p2 = smooth[i + 1]
            cv2.line(self.canvas,
                    (int(p1.x), int(p1.y)),
                    (int(p2.x), int(p2.y)),
                    self.brush_color,
                    self.brush_thickness)
    
    def _draw_final_stroke(self):
        """Draw final smoothed stroke and save to undo."""
        # Full stroke smoothing
        smooth = CatmullRomSpline.interpolate(self.current_stroke, num_segments=5)
        
        # Clear and redraw entire stroke with full smoothing
        # (This ensures best quality for the final result)
        temp = self.canvas_before_stroke.copy()
        
        for i in range(len(smooth) - 1):
            p1 = smooth[i]
            p2 = smooth[i + 1]
            cv2.line(temp,
                    (int(p1.x), int(p1.y)),
                    (int(p2.x), int(p2.y)),
                    self.brush_color,
                    self.brush_thickness)
        
        # Save to undo
        self.undo_manager.save_state(self.canvas_before_stroke, temp)
        self.canvas = temp
    
    def clear(self):
        """Clear canvas."""
        self._save_undo_checkpoint()
        self.undo_manager.save_state(self.canvas, np.full_like(self.canvas, 255))
        self.canvas.fill(255)
    
    def undo(self):
        """Undo last operation."""
        result = self.undo_manager.undo(self.canvas)
        if result is not None:
            self.canvas = result
    
    def redo(self):
        """Redo last undone operation."""
        result = self.undo_manager.redo(self.canvas)
        if result is not None:
            self.canvas = result
    
    def get_display(self) -> np.ndarray:
        """Get resized canvas for display."""
        return cv2.resize(self.canvas, self.display_size)
    
    def get_canvas(self) -> np.ndarray:
        """Get full-resolution canvas."""
        return self.canvas.copy()
    
    def set_brush_color(self, color: Tuple[int, int, int]):
        """Set brush color (BGR)."""
        self.brush_color = color
    
    def set_brush_thickness(self, thickness: int):
        """Set brush thickness."""
        self.brush_thickness = max(1, thickness)
    
    def get_memory_usage(self) -> dict:
        """Get memory usage statistics."""
        return {
            'canvas_mb': self.canvas.nbytes / (1024 * 1024),
            'undo_mb': self.undo_manager.get_memory_usage() / (1024 * 1024),
            'total_mb': (self.canvas.nbytes + self.undo_manager.get_memory_usage()) / (1024 * 1024)
        }
