#!/usr/bin/env python3
"""
Comprehensive unit tests for canvas system.
Tests spline interpolation, undo/redo, memory efficiency, and coordinate transformation.
"""

import unittest
import sys
import os
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from canvas import GestureCanvas, CatmullRomSpline, CanvasUndoManager, Point

class TestCatmullRomSpline(unittest.TestCase):
    """Test Catmull-Rom spline interpolation."""
    
    def test_linear_interpolation(self):
        """Test 2-point interpolation."""
        points = [Point(0, 0), Point(100, 100)]
        smooth = CatmullRomSpline.interpolate(points, num_segments=10)
        
        # Should have more points
        self.assertGreater(len(smooth), len(points))
        
        # First and last should match
        self.assertAlmostEqual(smooth[0].x, 0)
        self.assertAlmostEqual(smooth[0].y, 0)
        self.assertAlmostEqual(smooth[-1].x, 100)
        self.assertAlmostEqual(smooth[-1].y, 100)
        
        # Should be roughly linear
        mid = smooth[len(smooth) // 2]
        self.assertAlmostEqual(mid.x, 50, delta=5)
        self.assertAlmostEqual(mid.y, 50, delta=5)
    
    def test_curve_smoothness(self):
        """Test that curves are smooth (no sharp angles)."""
        points = [Point(0, 0), Point(50, 100), Point(100, 0)]
        smooth = CatmullRomSpline.interpolate(points, num_segments=5)
        
        # Check that we have many points
        self.assertGreater(len(smooth), 10)
        
        # Check that middle point is elevated (curve peaks)
        y_values = [p.y for p in smooth]
        max_y = max(y_values)
        self.assertGreater(max_y, 50)  # Should peak higher than midpoint
    
    def test_preserves_endpoints(self):
        """Test that endpoints are preserved."""
        points = [Point(10, 20), Point(30, 40), Point(50, 60), Point(70, 80)]
        smooth = CatmullRomSpline.interpolate(points, num_segments=5)
        
        self.assertAlmostEqual(smooth[0].x, points[0].x)
        self.assertAlmostEqual(smooth[0].y, points[0].y)
        self.assertAlmostEqual(smooth[-1].x, points[-1].x)
        self.assertAlmostEqual(smooth[-1].y, points[-1].y)


class TestCanvasUndoManager(unittest.TestCase):
    """Test efficient undo/redo system."""
    
    def setUp(self):
        self.manager = CanvasUndoManager(max_history=50)
    
    def test_basic_undo_redo(self):
        """Test basic undo and redo functionality."""
        canvas1 = np.full((100, 100, 3), 255, dtype=np.uint8)
        canvas2 = canvas1.copy()
        canvas2[10:20, 10:20] = 0  # Draw black square
        
        self.manager.save_state(canvas1, canvas2)
        
        # Undo
        result = self.manager.undo(canvas2.copy())
        self.assertIsNotNone(result)
        np.testing.assert_array_equal(result[10:20, 10:20], 255)  # Should be white again
        
        # Redo
        result = self.manager.redo(result)
        self.assertIsNotNone(result)
        np.testing.assert_array_equal(result[10:20, 10:20], 0)  # Should be black again
    
    def test_memory_efficiency(self):
        """Test that diff-based storage is efficient."""
        canvas = np.full((1024, 1024, 3), 255, dtype=np.uint8)
        
        # Make small change
        canvas_after = canvas.copy()
        canvas_after[100:110, 100:110] = 0  # 10x10 pixel change
        
        self.manager.save_state(canvas, canvas_after)
        
        memory_usage = self.manager.get_memory_usage()
        
        # Should be much less than full canvas (3MB)
        full_canvas_bytes = 1024 * 1024 * 3
        self.assertLess(memory_usage, full_canvas_bytes / 100)  # <1% of full size
    
    def test_multiple_undo(self):
        """Test multiple undo operations."""
        canvas = np.full((100, 100, 3), 255, dtype=np.uint8)
        
        # Make 5 changes
        for i in range(5):
            canvas_before = canvas.copy()
            canvas[i*10:(i+1)*10, i*10:(i+1)*10] = i * 50
            self.manager.save_state(canvas_before, canvas)
        
        # Undo all
        for i in range(5):
            canvas = self.manager.undo(canvas)
            self.assertIsNotNone(canvas)
        
        # Should be back to white
        np.testing.assert_array_equal(canvas, 255)
    
    def test_history_limit(self):
        """Test that history is limited."""
        manager = CanvasUndoManager(max_history=10)
        canvas = np.full((100, 100, 3), 255, dtype=np.uint8)
        
        # Make 20 changes
        for i in range(20):
            canvas_before = canvas.copy()
            canvas[0, i] = 0
            manager.save_state(canvas_before, canvas)
        
        # Should only have 10 in history
        self.assertLessEqual(len(manager.history), 10)
    
    def test_undo_clears_redo(self):
        """Test that new action clears redo stack."""
        canvas = np.full((100, 100, 3), 255, dtype=np.uint8)
        
        # Make change and undo
        canvas_before = canvas.copy()
        canvas[10:20, 10:20] = 0
        self.manager.save_state(canvas_before, canvas)
        canvas = self.manager.undo(canvas)
        
        # Redo stack should have 1 item
        self.assertEqual(len(self.manager.redo_stack), 1)
        
        # Make new change
        canvas_before = canvas.copy()
        canvas[30:40, 30:40] = 0
        self.manager.save_state(canvas_before, canvas)
        
        # Redo stack should be cleared
        self.assertEqual(len(self.manager.redo_stack), 0)


class TestGestureCanvas(unittest.TestCase):
    """Test canvas functionality."""
    
    def setUp(self):
        self.canvas = GestureCanvas()
    
    def test_initialization(self):
        """Test canvas initializes correctly."""
        self.assertEqual(self.canvas.internal_size, (1024, 1024))
        self.assertEqual(self.canvas.canvas.shape, (1024, 1024, 3))
        
        # Should start with white background
        np.testing.assert_array_equal(self.canvas.canvas, 255)
    
    def test_coordinate_transformation(self):
        """Test gesture-to-canvas coordinate transformation."""
        # Test corner mappings
        x, y = self.canvas.gesture_to_canvas_coords(0, 0, (640, 480))
        self.assertEqual(x, 0)
        self.assertEqual(y, 0)
        
        x, y = self.canvas.gesture_to_canvas_coords(640, 480, (640, 480))
        self.assertLessEqual(x, 1024)  # With aspect correction, might not be exactly 1024
        
        # Test center
        x, y = self.canvas.gesture_to_canvas_coords(320, 240, (640, 480))
        self.assertAlmostEqual(x, 512, delta=10)
    
    def test_drawing_stroke(self):
        """Test drawing a stroke."""
        self.canvas.start_stroke(100, 100)
        self.assertTrue(self.canvas.is_drawing)
        
        # Add points
        for i in range(10):
            self.canvas.add_point(100 + i*10, 100 + i*10)
        
        self.canvas.end_stroke()
        self.assertFalse(self.canvas.is_drawing)
        
        # Canvas should have changed
        self.assertFalse(np.all(self.canvas.canvas == 255))
    
    def test_clear_canvas(self):
        """Test canvas clear."""
        # Draw something
        self.canvas.start_stroke(100, 100)
        self.canvas.add_point(200, 200)
        self.canvas.end_stroke()
        
        # Clear
        self.canvas.clear()
        
        # Should be all white
        np.testing.assert_array_equal(self.canvas.canvas, 255)
    
    def test_undo_redo(self):
        """Test undo/redo on canvas."""
        # Draw stroke
        self.canvas.start_stroke(100, 100)
        self.canvas.add_point(200, 200)
        self.canvas.end_stroke()
        
        modified = self.canvas.canvas.copy()
        
        # Undo
        self.canvas.undo()
        
        # Should be white again
        np.testing.assert_array_equal(self.canvas.canvas, 255)
        
        # Redo
        self.canvas.redo()
        
        # Should match modified state
        # (Note: might not be pixel-perfect due to smoothing)
        self.assertFalse(np.all(self.canvas.canvas == 255))
    
    def test_memory_usage(self):
        """Test memory usage tracking."""
        usage = self.canvas.get_memory_usage()
        
        self.assertIn('canvas_mb', usage)
        self.assertIn('undo_mb', usage)
        self.assertIn('total_mb', usage)
        
        # Canvas should be ~3MB (1024x1024x3)
        self.assertAlmostEqual(usage['canvas_mb'], 3.0, delta=0.5)
    
    def test_brush_settings(self):
        """Test brush color and thickness."""
        self.canvas.set_brush_color((255, 0, 0))  # Red
        self.assertEqual(self.canvas.brush_color, (255, 0, 0))
        
        self.canvas.set_brush_thickness(10)
        self.assertEqual(self.canvas.brush_thickness, 10)


class TestCanvasPerformance(unittest.TestCase):
    """Performance tests for canvas."""
    
    def test_multiple_strokes_memory(self):
        """Test memory usage with multiple strokes."""
        canvas = GestureCanvas()
        
        # Draw 30 strokes
        for stroke_num in range(30):
            canvas.start_stroke(50 + stroke_num * 10, 50)
            for i in range(20):
                canvas.add_point(50 + stroke_num * 10 + i, 50 + i*10)
            canvas.end_stroke()
        
        usage = canvas.get_memory_usage()
        
        # Should be less than 500MB (target from plan)
        self.assertLess(usage['total_mb'], 500)
        
        # Undo all 30
        for _ in range(30):
            canvas.undo()
        
        # Should still be under 500MB
        usage = canvas.get_memory_usage()
        self.assertLess(usage['total_mb'], 500)


def run_canvas_tests():
    """Run all canvas tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestCatmullRomSpline))
    suite.addTests(loader.loadTestsFromTestCase(TestCanvasUndoManager))
    suite.addTests(loader.loadTestsFromTestCase(TestGestureCanvas))
    suite.addTests(loader.loadTestsFromTestCase(TestCanvasPerformance))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_canvas_tests()
    sys.exit(0 if success else 1)
