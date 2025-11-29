#!/usr/bin/env python3
"""
Unit tests for hand tracking and gesture recognition logic.
These tests use mock data and don't require video files or webcam.
"""

import unittest
import sys
import os
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gesture_recognition import GestureRecognizer

class TestGestureRecognition(unittest.TestCase):
    def setUp(self):
        self.recognizer = GestureRecognizer()

    def create_mock_landmarks(self, gesture_type):
        """Create mock landmark data for testing."""
        # Create 21 landmarks (MediaPipe hand model)
        landmarks = []
        
        if gesture_type == "FIST":
            # All fingers curled - tips closer to wrist than MCPs
            base_x, base_y = 320, 400
            # Wrist
            landmarks.append({'x': base_x, 'y': base_y, 'z': 0.0})
            
            # Thumb (curled)
            landmarks.append({'x': base_x - 15, 'y': base_y - 10, 'z': 0.0})  #1
            landmarks.append({'x': base_x - 20, 'y': base_y - 15, 'z': 0.0})  #2
            landmarks.append({'x': base_x - 22, 'y': base_y - 18, 'z': 0.0})  #3
            landmarks.append({'x': base_x - 20, 'y': base_y - 20, 'z': 0.0})  #4 tip (back towards palm)
            
            # Index (curled) - MCP further, tip closer
            landmarks.append({'x': base_x - 5, 'y': base_y - 40, 'z': 0.0})   #5 MCP
            landmarks.append({'x': base_x - 5, 'y': base_y - 30, 'z': 0.0})   #6
            landmarks.append({'x': base_x - 5, 'y': base_y - 22, 'z': 0.0})   #7
            landmarks.append({'x': base_x - 5, 'y': base_y - 15, 'z': 0.0})   #8 tip (curled back)
            
            # Middle (curled)
            landmarks.append({'x': base_x, 'y': base_y - 42, 'z': 0.0})       #9 MCP
            landmarks.append({'x': base_x, 'y': base_y - 32, 'z': 0.0})       #10
            landmarks.append({'x': base_x, 'y': base_y - 24, 'z': 0.0})       #11
            landmarks.append({'x': base_x, 'y': base_y - 16, 'z': 0.0})       #12 tip
            
            # Ring (curled)
            landmarks.append({'x': base_x + 5, 'y': base_y - 40, 'z': 0.0})   #13 MCP
            landmarks.append({'x': base_x + 5, 'y': base_y - 30, 'z': 0.0})   #14
            landmarks.append({'x': base_x + 5, 'y': base_y - 22, 'z': 0.0})   #15
            landmarks.append({'x': base_x + 5, 'y': base_y - 15, 'z': 0.0})   #16 tip
            
            # Pinky (curled)
            landmarks.append({'x': base_x + 10, 'y': base_y - 35, 'z': 0.0})  #17 MCP
            landmarks.append({'x': base_x + 10, 'y': base_y - 26, 'z': 0.0})  #18
            landmarks.append({'x': base_x + 10, 'y': base_y - 19, 'z': 0.0})  #19
            landmarks.append({'x': base_x + 10, 'y': base_y - 13, 'z': 0.0})  #20 tip
        
        elif gesture_type == "OPEN_PALM":
            # All fingers extended
            base_x, base_y = 320, 400
            # Wrist
            landmarks.append({'x': base_x, 'y': base_y, 'z': 0.0})
            
            # Thumb (4 joints)
            for i in range(1, 5):
                landmarks.append({'x': base_x - 30 - i*10, 'y': base_y - i*15, 'z': 0.0})
            
            # Index (4 joints)
            for i in range(5, 9):
                landmarks.append({'x': base_x - 15, 'y': base_y - (i-4)*30, 'z': 0.0})
            
            # Middle (4 joints)
            for i in range(9, 13):
                landmarks.append({'x': base_x, 'y': base_y - (i-8)*32, 'z': 0.0})
            
            # Ring (4 joints)
            for i in range(13, 17):
                landmarks.append({'x': base_x + 15, 'y': base_y - (i-12)*30, 'z': 0.0})
            
            # Pinky (4 joints)
            for i in range(17, 21):
                landmarks.append({'x': base_x + 30, 'y': base_y - (i-16)*25, 'z': 0.0})
        
        elif gesture_type == "POINTING":
            # Only index finger extended
            base_x, base_y = 320, 400
            landmarks.append({'x': base_x, 'y': base_y, 'z': 0.0})
            
            # Thumb curled
            for i in range(1, 5):
                landmarks.append({'x': base_x - 20, 'y': base_y - 10, 'z': 0.0})
            
            # Index extended
            for i in range(5, 9):
                landmarks.append({'x': base_x, 'y': base_y - (i-4)*35, 'z': 0.0})
            
            # Others curled
            for i in range(9, 21):
                landmarks.append({'x': base_x + 10, 'y': base_y, 'z': 0.0})
        
        else:  # Default/Unknown
            for i in range(21):
                landmarks.append({'x': 320, 'y': 240, 'z': 0.0})
        
        return landmarks

    def test_fist_detection(self):
        """Test that FIST gesture is detected correctly."""
        landmarks = self.create_mock_landmarks("FIST")
        # Run multiple times for hysteresis
        for _ in range(5):
            result = self.recognizer.detect_gesture(landmarks)
        self.assertEqual(result, "FIST")

    def test_open_palm_detection(self):
        """Test that OPEN_PALM gesture is detected correctly."""
        landmarks = self.create_mock_landmarks("OPEN_PALM")
        for _ in range(5):
            result = self.recognizer.detect_gesture(landmarks)
        self.assertEqual(result, "OPEN_PALM")

    def test_pointing_detection(self):
        """Test that POINTING gesture is detected correctly."""
        landmarks = self.create_mock_landmarks("POINTING")
        for _ in range(5):
            result = self.recognizer.detect_gesture(landmarks)
        self.assertEqual(result, "POINTING")

    def test_hysteresis(self):
        """Test that hysteresis prevents rapid gesture switching."""
        fist_landmarks = self.create_mock_landmarks("FIST")
        palm_landmarks = self.create_mock_landmarks("OPEN_PALM")
        
        # Establish FIST
        for _ in range(5):
            self.recognizer.detect_gesture(fist_landmarks)
        
        # Single frame of OPEN_PALM shouldn't switch immediately
        result = self.recognizer.detect_gesture(palm_landmarks)
        self.assertEqual(result, "FIST", "Hysteresis should prevent immediate switch")
        
        # But sustained OPEN_PALM should eventually switch
        for _ in range(5):
            result = self.recognizer.detect_gesture(palm_landmarks)
        self.assertEqual(result, "OPEN_PALM", "Sustained gesture should switch")

class TestPerformance(unittest.TestCase):
    def setUp(self):
        self.recognizer = GestureRecognizer()

    def test_gesture_recognition_speed(self):
        """Test that gesture recognition is fast enough for real-time use."""
        import time
        
        landmarks = []
        for i in range(21):
            landmarks.append({'x': 320, 'y': 240, 'z': 0.0})
        
        iterations = 100
        start = time.time()
        for _ in range(iterations):
            self.recognizer.detect_gesture(landmarks)
        duration = time.time() - start
        
        fps = iterations / duration
        self.assertGreater(fps, 100, f"Gesture recognition too slow: {fps:.1f} FPS")

def run_tests():
    """Run all unit tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestGestureRecognition))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
