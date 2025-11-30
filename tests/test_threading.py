#!/usr/bin/env python3
"""
Comprehensive tests for threading architecture.
Tests race conditions, lock contention, queue handling, and stress scenarios.
"""

import unittest
import sys
import os
import time
import threading
import numpy as np
from unittest.mock import Mock, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from threading_manager import (
    ThreadSafeGestureState, ThreadSafeFrameBuffer, GenerationQueue,
    GenerationRequest, GenerationResult, ThreadingManager
)


class TestThreadSafeGestureState(unittest.TestCase):
    """Test thread-safe gesture state."""
    
    def setUp(self):
        self.state = ThreadSafeGestureState()
    
    def test_basic_update_and_get(self):
        """Test basic state update and retrieval."""
        self.state.update(gesture="FIST", hand_detected=True)
        
        state = self.state.get()
        self.assertEqual(state.gesture, "FIST")
        self.assertTrue(state.hand_detected)
    
    def test_concurrent_reads_writes(self):
        """Test 1000 concurrent reads and writes."""
        errors = []
        read_count = [0]
        write_count = [0]
        
        def writer():
            try:
                for i in range(500):
                    self.state.update(gesture=f"GESTURE_{i}")
                    write_count[0] += 1
            except Exception as e:
                errors.append(("write", e))
        
        def reader():
            try:
                for i in range(500):
                    state = self.state.get()
                    self.assertIsNotNone(state.gesture)
                    read_count[0] += 1
            except Exception as e:
                errors.append(("read", e))
        
        # Start threads
        threads = []
        for _ in range(2):
            threads.append(threading.Thread(target=writer))
            threads.append(threading.Thread(target=reader))
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join(timeout=5)
        
        # Check no errors
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(write_count[0], 1000)
        self.assertEqual(read_count[0], 1000)
    
    def test_lock_hold_time(self):
        """Test that lock hold time is tracked."""
        for _ in range(10):
            self.state.update(gesture="TEST")
        
        stats = self.state.get_lock_stats()
        
        self.assertIn('avg_ms', stats)
        self.assertIn('max_ms', stats)
        self.assertIn('count', stats)
        self.assertEqual(stats['count'], 10)
        
        # Lock should be held for < 0.5ms (target from plan)
        self.assertLess(stats['avg_ms'], 0.5, 
                       f"Lock held too long: {stats['avg_ms']:.3f}ms")
    
    def test_state_isolation(self):
        """Test that get() returns copy (no shared references)."""
        landmarks = [{'x': 100, 'y': 200}]
        self.state.update(hand_landmarks=landmarks)
        
        state1 = self.state.get()
        state2 = self.state.get()
        
        # Should be different objects
        self.assertIsNot(state1, state2)
        if state1.hand_landmarks and state2.hand_landmarks:
            self.assertIsNot(state1.hand_landmarks, state2.hand_landmarks)


class TestThreadSafeFrameBuffer(unittest.TestCase):
    """Test non-blocking frame buffer."""
    
    def setUp(self):
        self.buffer = ThreadSafeFrameBuffer(maxsize=2)
    
    def test_put_and_get(self):
        """Test basic put and get."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        self.buffer.put(frame)
        
        retrieved = self.buffer.get_latest()
        self.assertIsNotNone(retrieved)
        np.testing.assert_array_equal(retrieved, frame)
    
    def test_non_blocking_get(self):
        """Test that get is non-blocking."""
        start = time.time()
        result = self.buffer.get_latest()
        duration = time.time() - start
        
        # Should be instant (< 1ms)
        self.assertLess(duration, 0.001)
        self.assertIsNone(result)  # Nothing in buffer
    
    def test_drops_old_frames_when_full(self):
        """Test that old frames are dropped when buffer is full."""
        frames = [
            np.full((10, 10, 3), i, dtype=np.uint8) 
            for i in range(5)
        ]
        
        for frame in frames:
            self.buffer.put(frame)
        
        # Should have latest frame
        latest = self.buffer.get_latest()
        self.assertIsNotNone(latest)
        np.testing.assert_array_equal(latest, frames[-1])
    
    def test_concurrent_put_get(self):
        """Test concurrent puts and gets."""
        errors = []
        
        def producer():
            try:
                for i in range(100):
                    frame = np.full((10, 10, 3), i, dtype=np.uint8)
                    self.buffer.put(frame)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(("producer", e))
        
        def consumer():
            try:
                for _ in range(100):
                    self.buffer.get_latest()
                    time.sleep(0.001)
            except Exception as e:
                errors.append(("consumer", e))
        
        threads = [
            threading.Thread(target=producer),
            threading.Thread(target=consumer)
        ]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join(timeout=5)
        
        self.assertEqual(len(errors), 0, f"Errors: {errors}")


class TestGenerationQueue(unittest.TestCase):
    """Test generation request queue."""
    
    def setUp(self):
        self.queue = GenerationQueue(max_queue_size=5)
    
    def test_add_and_get_request(self):
        """Test basic add and get."""
        request = GenerationRequest(
            request_id="test1",
            canvas_image=np.zeros((100, 100, 3)),
            style="photorealistic",
            timestamp=time.time()
        )
        
        success = self.queue.add_request(request)
        self.assertTrue(success)
        
        retrieved = self.queue.get_request(timeout=0.1)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.request_id, "test1")
    
    def test_queue_full_handling(self):
        """Test that queue rejects when full."""
        # Fill queue
        for i in range(5):
            request = GenerationRequest(
                request_id=f"req{i}",
                canvas_image=np.zeros((10, 10, 3)),
                style="anime",
                timestamp=time.time()
            )
            success = self.queue.add_request(request)
            self.assertTrue(success)
        
        # Try to add one more
        overflow_request = GenerationRequest(
            request_id="overflow",
            canvas_image=np.zeros((10, 10, 3)),
            style="anime",
            timestamp=time.time()
        )
        success = self.queue.add_request(overflow_request)
        self.assertFalse(success)  # Should be rejected
    
    def test_queue_position_tracking(self):
        """Test queue position tracking."""
        requests = []
        for i in range(3):
            req = GenerationRequest(
                request_id=f"req{i}",
                canvas_image=np.zeros((10, 10, 3)),
                style="anime",
                timestamp=time.time()
            )
            self.queue.add_request(req)
            requests.append(req)
        
        # Get first request (now processing)
        first = self.queue.get_request(timeout=0.1)
        
        # Check positions
        self.assertEqual(self.queue.get_queue_position(first.request_id), 0)  # Processing
        self.assertEqual(self.queue.get_queue_position("req1"), 1)  # First in queue
        self.assertEqual(self.queue.get_queue_position("req2"), 2)  # Second in queue
    
    def test_mark_complete(self):
        """Test marking request as complete."""
        request = GenerationRequest(
            request_id="test",
            canvas_image=np.zeros((10, 10, 3)),
            style="anime",
            timestamp=time.time()
        )
        self.queue.add_request(request)
        
        self.queue.get_request(timeout=0.1)
        self.assertTrue(self.queue.is_processing())
        
        self.queue.mark_complete()
        self.assertFalse(self.queue.is_processing())
    
    def test_rapid_double_trigger(self):
        """Test rapid double trigger scenario."""
        req1 = GenerationRequest(
            request_id="req1",
            canvas_image=np.zeros((10, 10, 3)),
            style="anime",
            timestamp=time.time()
        )
        req2 = GenerationRequest(
            request_id="req2",
            canvas_image=np.zeros((10, 10, 3)),
            style="anime",
            timestamp=time.time()
        )
        
        # Add both
        self.assertTrue(self.queue.add_request(req1))
        self.assertTrue(self.queue.add_request(req2))
        
        # Get first
        first = self.queue.get_request(timeout=0.1)
        self.assertEqual(first.request_id, "req1")
        
        # Second should be queued
        self.assertEqual(self.queue.get_queue_position("req2"), 1)
        self.assertEqual(self.queue.get_queue_size(), 1)


class TestThreadingManager(unittest.TestCase):
    """Test threading manager integration."""
    
    def test_initialization(self):
        """Test that manager initializes correctly."""
        manager = ThreadingManager()
        
        self.assertIsNotNone(manager.gesture_state)
        self.assertIsNotNone(manager.frame_buffer)
        self.assertIsNotNone(manager.generation_queue)
        self.assertIsNotNone(manager.result_queue)
    
    def test_shutdown(self):
        """Test graceful shutdown."""
        manager = ThreadingManager()
        
        # Start with mocks
        mock_tracker = Mock()
        mock_tracker.process_frame = Mock(return_value=[])
        mock_recognizer = Mock()
        
        # This would normally start threads, but we'll test shutdown mechanism
        manager._shutdown.clear()
        
        start = time.time()
        manager.shutdown(timeout=1.0)
        duration = time.time() - start
        
        # Should set shutdown flag
        self.assertTrue(manager._shutdown.is_set())
        
        # Should complete quickly
        self.assertLess(duration, 2.0)
    
    def test_pause_resume_tracking(self):
        """Test pause and resume functionality."""
        manager = ThreadingManager()
        
        # Should start enabled
        self.assertTrue(manager._tracking_enabled.is_set())
        
        manager.pause_hand_tracking()
        self.assertFalse(manager._tracking_enabled.is_set())
        
        manager.resume_hand_tracking()
        self.assertTrue(manager._tracking_enabled.is_set())
    
    def test_stats_collection(self):
        """Test statistics collection."""
        manager = ThreadingManager()
        
        stats = manager.get_stats()
        
        self.assertIn('gesture_lock_stats', stats)
        self.assertIn('generation_queue_size', stats)
        self.assertIn('is_generating', stats)
    
    def test_error_tracking(self):
        """Test error tracking."""
        manager = ThreadingManager()
        
        # Inject errors
        manager._errors.put(("test_thread", "test error"))
        
        errors = manager.get_errors()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0], ("test_thread", "test error"))
        
        # Should clear after getting
        errors2 = manager.get_errors()
        self.assertEqual(len(errors2), 0)


class TestStressScenarios(unittest.TestCase):
    """Stress tests for threading system."""
    
    def test_high_frequency_state_updates(self):
        """Test handling high-frequency state updates."""
        state = ThreadSafeGestureState()
        
        def rapid_updates():
            for i in range(1000):
                state.update(gesture=f"G{i % 5}")
        
        threads = [threading.Thread(target=rapid_updates) for _ in range(3)]
        
        start = time.time()
        for t in threads:
            t.start()
        
        for t in threads:
            t.join(timeout=5)
        
        duration = time.time() - start
        
        # Should complete in reasonable time
        self.assertLess(duration, 3.0)
        
        # Lock should still be fast
        stats = state.get_lock_stats()
        self.assertLess(stats['avg_ms'], 1.0)


def run_threading_tests():
    """Run all threading tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestThreadSafeGestureState))
    suite.addTests(loader.loadTestsFromTestCase(TestThreadSafeFrameBuffer))
    suite.addTests(loader.loadTestsFromTestCase(TestGenerationQueue))
    suite.addTests(loader.loadTestsFromTestCase(TestThreadingManager))
    suite.addTests(loader.loadTestsFromTestCase(TestStressScenarios))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("="*60)
    print("THREADING ARCHITECTURE TESTS")
    print("="*60 + "\n")
    
    success = run_threading_tests()
    sys.exit(0 if success else 1)
