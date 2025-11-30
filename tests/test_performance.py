#!/usr/bin/env python3
"""
Tests for performance optimization utilities.
"""

import unittest
import sys
import os
import time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from performance import (
    DirtyRectangleTracker, GestureCacheEvaluator, IntelligentFrameSkipper,
    FPSCounter, PerformanceOptimizer
)


class TestDirtyRectangleTracker(unittest.TestCase):
    """Test dirty Rectangle tracking."""
    
    def setUp(self):
        self.tracker = DirtyRectangleTracker((1024, 1024))
    
    def test_mark_region(self):
        """Test marking a region as dirty."""
        self.tracker.mark_region(100, 100, 200, 200)
        
        rect = self.tracker.get_dirty_rect()
        self.assertIsNotNone(rect)
        self.assertEqual(rect, (100, 100, 200, 200))
    
    def test_expand_region(self):
        """Test that marking multiple regions expands the dirty rect."""
        self.tracker.mark_region(100, 100, 200, 200)
        self.tracker.mark_region(150, 150, 250, 250)
        
        rect = self.tracker.get_dirty_rect()
        self.assertEqual(rect, (100, 100, 250, 250))  # Expanded
    
    def test_savings_calculation(self):
        """Test dirty rect savings calculation."""
        # Small region
        self.tracker.mark_region(0, 0, 100, 100)
        self.tracker.full_redraw_needed = False  # Clear full redraw flag
        savings = self.tracker.get_savings()
        
        # Should be >90% savings (100x100 vs 1024x1024)
        self.assertGreater(savings, 90.0)
    
    def test_bounds_clipping(self):
        """Test that bounds are clipped to canvas size."""
        self.tracker.mark_region(-50, -50, 2000, 2000)
        
        rect = self.tracker.get_dirty_rect()
        x1, y1, x2, y2 = rect
        
        # Should be clipped
        self.assertGreaterEqual(x1, 0)
        self.assertGreaterEqual(y1, 0)
        self.assertLessEqual(x2, 1024)
        self.assertLessEqual(y2, 1024)


class TestGestureCacheEvaluator(unittest.TestCase):
    """Test gesture cache."""
    
    def setUp(self):
        self.cache = GestureCacheEvaluator()
    
    def test_set_and_get(self):
        """Test basic cache operations."""
        self.cache.set('test_key', 'test_value')
        
        value = self.cache.get('test_key')
        self.assertEqual(value, 'test_value')
    
    def test_cache_expiry(self):
        """Test that cache expires after max age."""
        self.cache.set('key', 'value')
        
        # Increment age beyond max
        for _ in range(3):
            self.cache.increment_age()
        
        # Should return None (expired)
        value = self.cache.get('key')
        self.assertIsNone(value)
    
    def test_cache_stats(self):
        """Test cache statistics."""
        self.cache.set('key1', 'value1')
        self.cache.set('key2', 'value2')
        
        stats = self.cache.get_cache_stats()
        
        self.assertEqual(stats['size'], 2)
        self.assertGreaterEqual(stats['age'], 0)


class TestIntelligentFrameSkipper(unittest.TestCase):
    """Test intelligent frame skipping."""
    
    def test_skip_ratio(self):
        """Test that frames are skipped to meet target FPS."""
        skipper = IntelligentFrameSkipper(target_fps=10, display_fps=30)
        
        processed = 0
        skipped = 0
        
        # Simulate 30 frames (1 second at 30 FPS)
        for _ in range(30):
            if skipper.should_process_gesture():
                processed += 1
            else:
                skipped += 1
            time.sleep(1/30)
        
        # Should process ~10 frames (target_fps=10)
        self.assertGreater(processed, 5)  # At least some processing
        self.assertLess(processed, 15)    # But not all frames
    
    def test_skip_ratio_calculation(self):
        """Test skip ratio calculation."""
        skipper = IntelligentFrameSkipper(target_fps=20)
        
        for _ in range(100):
            skipper.should_process_gesture()
            time.sleep(1/30)  # 30 FPS
        
        ratio = skipper.get_skip_ratio()
        
        # Should skip some frames
        self.assertGreater(ratio, 0.1)  # At least 10% skipped
        self.assertLess(ratio, 0.9)     # But not everything


class TestFPSCounter(unittest.TestCase):
    """Test FPS counter."""
    
    def test_fps_tracking(self):
        """Test FPS tracking."""
        counter = FPSCounter()
        
        # Simulate frames with known timing
        for _ in range(5):
            time.sleep(0.05)  # 50ms between frames = 20 FPS
            counter.tick()
        
        stats = counter.get_stats()
        
        # Should track FPS (allow wide range due to timing variability)
        self.assertGreater(stats['avg_fps'], 5)
        self.assertLess(stats['avg_fps'], 100)
    
    def test_stats_available(self):
        """Test that stats are available."""
        counter = FPSCounter()
        counter.tick()
        
        stats = counter.get_stats()
        
        self.assertIn('avg_fps', stats)
        self.assertIn('min_fps', stats)
        self.assertIn('max_fps', stats)


class TestPerformanceOptimizer(unittest.TestCase):
    """Test performance optimizer."""
    
    def test_initialization(self):
        """Test optimizer initializes all components."""
        optimizer = PerformanceOptimizer()
        
        self.assertIsNotNone(optimizer.dirty_tracker)
        self.assertIsNotNone(optimizer.gesture_cache)
        self.assertIsNotNone(optimizer.frame_skipper)
        self.assertIsNotNone(optimizer.fps_counter)
    
    def test_optimization_report(self):
        """Test comprehensive optimization report."""
        optimizer = PerformanceOptimizer()
        
        # Generate some activity
        optimizer.fps_counter.tick()
        optimizer.dirty_tracker.mark_region(0, 0, 100, 100)
        
        report = optimizer.get_optimization_report()
        
        self.assertIn('fps_stats', report)
        self.assertIn('skip_ratio', report)
        self.assertIn('dirty_rect_savings', report)
        self.assertIn('cache_stats', report)


def run_performance_tests():
    """Run all performance tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestDirtyRectangleTracker))
    suite.addTests(loader.loadTestsFromTestCase(TestGestureCacheEvaluator))
    suite.addTests(loader.loadTestsFromTestCase(TestIntelligentFrameSkipper))
    suite.addTests(loader.loadTestsFromTestCase(TestFPSCounter))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceOptimizer))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("="*60)
    print("PERFORMANCE OPTIMIZATION TESTS")
    print("="*60 + "\n")
    
    success = run_performance_tests()
    sys.exit(0 if success else 1)
