"""
Performance optimization utilities for GestureCanvas.
Includes profiling, dirty rectangle rendering, gesture caching, and frame skipping.
"""

import time
import cProfile
import pstats
import io
from typing import Optional, Tuple, Dict, Any
from collections import deque
import numpy as np

class PerformanceProfiler:
    """Performance profiling utility."""
    
    def __init__(self):
        self.profiler = cProfile.Profile()
        self.stats = None
    
    def start(self):
        """Start profiling."""
        self.profiler.enable()
    
    def stop(self):
        """Stop profiling and generate stats."""
        self.profiler.disable()
        s = io.StringIO()
        ps = pstats.Stats(self.profiler, stream=s)
        ps.sort_stats('cumulative')
        ps.print_stats(20)  # Top 20 functions
        self.stats = s.getvalue()
        return self.stats
    
    def get_top_bottlenecks(self, n=10) -> str:
        """Get top N bottlenecks."""
        if self.stats is None:
            return "No profiling data available"
        
        lines = self.stats.split('\n')
        header = '\n'.join(lines[:6])
        top_n = '\n'.join(lines[6:6+n])
        return f"{header}\n{top_n}"


class DirtyRectangleTracker:
    """Track dirty regions for optimized rendering."""
    
    def __init__(self, canvas_size: Tuple[int, int]):
        self.canvas_size = canvas_size
        self.dirty_rect: Optional[Tuple[int, int, int, int]] = None
        self.full_redraw_needed = True
    
    def mark_region(self, x1: int, y1: int, x2: int, y2: int):
        """Mark a region as dirty."""
        x1 = max(0, min(x1, self.canvas_size[0]))
        y1 = max(0, min(y1, self.canvas_size[1]))
        x2 = max(0, min(x2, self.canvas_size[0]))
        y2 = max(0, min(y2, self.canvas_size[1]))
        
        if self.dirty_rect is None:
            self.dirty_rect = (x1, y1, x2, y2)
        else:
            # Expand to include new region
            dx1, dy1, dx2, dy2 = self.dirty_rect
            self.dirty_rect = (
                min(dx1, x1),
                min(dy1, y1),
                max(dx2, x2),
                max(dy2, y2)
            )
    
    def get_dirty_rect(self) -> Optional[Tuple[int, int, int, int]]:
        """Get current dirty rectangle."""
        return self.dirty_rect
    
    def clear(self):
        """Clear dirty region."""
        self.dirty_rect = None
        self.full_redraw_needed = False
    
    def mark_full_redraw(self):
        """Mark that full redraw is needed."""
        self.full_redraw_needed = True
        self.dirty_rect = (0, 0, self.canvas_size[0], self.canvas_size[1])
    
    def needs_full_redraw(self) -> bool:
        """Check if full redraw is needed."""
        return self.full_redraw_needed
    
    def get_savings(self) -> float:
        """Calculate percentage of canvas that needs redraw."""
        if self.dirty_rect is None or self.full_redraw_needed:
            return 0.0
        
        x1, y1, x2, y2 = self.dirty_rect
        dirty_area = (x2 - x1) * (y2 - y1)
        total_area = self.canvas_size[0] * self.canvas_size[1]
        
        if total_area == 0:
            return 0.0
        
        return (1.0 - dirty_area / total_area) * 100.0


class GestureCacheEvaluator:
    """Cache computed gesture values to avoid redundant calculations."""
    
    def __init__(self):
        self.cache: Dict[str, Any] = {}
        self.cache_age = 0
        self.max_age = 1  # Recompute every frame
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if still valid."""
        if self.cache_age > self.max_age:
            self.cache.clear()
            self.cache_age = 0
            return None
        
        return self.cache.get(key)
    
    def set(self, key: str, value: Any):
        """Set cached value."""
        self.cache[key] = value
    
    def increment_age(self):
        """Increment cache age."""
        self.cache_age += 1
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            'size': len(self.cache),
            'age': self.cache_age
        }


class IntelligentFrameSkipper:
    """Intelligent frame skipping for gesture processing."""
    
    def __init__(self, target_fps: int = 20, display_fps: int = 30):
        """
        Args:
            target_fps: Target FPS for gesture processing (20)
            display_fps: Display FPS (30)
        """
        self.target_interval = 1.0 / target_fps
        self.display_interval = 1.0 / display_fps
        self.last_process_time = 0
        self.frame_count = 0
        self.skipped_count = 0
    
    def should_process_gesture(self) -> bool:
        """Check if current frame should be processed for gestures."""
        current_time = time.time()
        
        if current_time - self.last_process_time >= self.target_interval:
            self.last_process_time = current_time
            self.frame_count += 1
            return True
        else:
            self.skipped_count += 1
            return False
    
    def get_skip_ratio(self) -> float:
        """Get ratio of skipped frames."""
        total = self.frame_count + self.skipped_count
        if total == 0:
            return 0.0
        return self.skipped_count / total
    
    def get_actual_fps(self) -> float:
        """Get actual gesture processing FPS."""
        if self.frame_count == 0:
            return 0.0
        elapsed = time.time() - self.last_process_time
        if elapsed == 0:
            return 0.0
        return 1.0 / elapsed


class FPSCounter:
    """Accurate FPS counter with smoothing."""
    
    def __init__(self, window_size: int = 30):
        self.frame_times = deque(maxlen=window_size)
        self.last_time = time.time()
    
    def tick(self) -> float:
        """Record frame and return current FPS."""
        current_time = time.time()
        frame_time = current_time - self.last_time
        self.last_time = current_time
        
        self.frame_times.append(frame_time)
        
        if len(self.frame_times) == 0:
            return 0.0
        
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        if avg_frame_time == 0:
            return 0.0
        
        return 1.0 / avg_frame_time
    
    def get_stats(self) -> Dict[str, float]:
        """Get detailed FPS statistics."""
        if not self.frame_times:
            return {'avg_fps': 0, 'min_fps': 0, 'max_fps': 0}
        
        fps_values = [1.0/ft if ft > 0 else 0 for ft in self.frame_times]
        
        return {
            'avg_fps': sum(fps_values) / len(fps_values),
            'min_fps': min(fps_values),
            'max_fps': max(fps_values)
        }


class ResourceMonitor:
    """Monitor system resource usage."""
    
    def __init__(self):
        self.samples = deque(maxlen=100)
    
    def sample(self):
        """Take resource sample."""
        import psutil
        import torch
        
        sample = {
            'timestamp': time.time(),
            'cpu_percent': psutil.cpu_percent(interval=None),
            'memory_mb': psutil.Process().memory_info().rss / 1024 / 1024
        }
        
        if torch.cuda.is_available():
            sample['gpu_memory_mb'] = torch.cuda.memory_allocated() / 1024 / 1024
            sample['gpu_memory_reserved_mb'] = torch.cuda.memory_reserved() / 1024 / 1024
        
        self.samples.append(sample)
    
    def get_stats(self) -> Dict[str, float]:
        """Get resource usage statistics."""
        if not self.samples:
            return {}
        
        cpu_values = [s['cpu_percent'] for s in self.samples]
        mem_values = [s['memory_mb'] for s in self.samples]
        
        stats = {
            'avg_cpu_percent': sum(cpu_values) / len(cpu_values),
            'max_cpu_percent': max(cpu_values),
            'avg_memory_mb': sum(mem_values) / len(mem_values),
            'max_memory_mb': max(mem_values)
        }
        
        if 'gpu_memory_mb' in self.samples[0]:
            gpu_mem_values = [s['gpu_memory_mb'] for s in self.samples]
            stats['avg_gpu_memory_mb'] = sum(gpu_mem_values) / len(gpu_mem_values)
            stats['max_gpu_memory_mb'] = max(gpu_mem_values)
        
        return stats
    
    def check_limits(self, cpu_limit: float = 60.0, memory_limit_mb: float = 8000) -> Dict[str, bool]:
        """Check if resource usage is within limits."""
        stats = self.get_stats()
        
        return {
            'cpu_ok': stats.get('avg_cpu_percent', 0) < cpu_limit,
            'memory_ok': stats.get('avg_memory_mb', 0) < memory_limit_mb
        }


class PerformanceOptimizer:
    """Central performance optimization manager."""
    
    def __init__(self):
        self.dirty_tracker = DirtyRectangleTracker((1024, 1024))
        self.gesture_cache = GestureCacheEvaluator()
        self.frame_skipper = IntelligentFrameSkipper(target_fps=20, display_fps=30)
        self.fps_counter = FPSCounter()
        self.resource_monitor = ResourceMonitor()
        self.profiler = PerformanceProfiler()
    
    def start_profiling(self):
        """Start performance profiling."""
        self.profiler.start()
    
    def stop_profiling(self) -> str:
        """Stop profiling and get report."""
        return self.profiler.stop()
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Get comprehensive optimization report."""
        return {
            'fps_stats': self.fps_counter.get_stats(),
            'skip_ratio': self.frame_skipper.get_skip_ratio(),
            'dirty_rect_savings': self.dirty_tracker.get_savings(),
            'cache_stats': self.gesture_cache.get_cache_stats(),
            'resource_stats': self.resource_monitor.get_stats(),
            'resource_limits_ok': self.resource_monitor.check_limits()
        }
