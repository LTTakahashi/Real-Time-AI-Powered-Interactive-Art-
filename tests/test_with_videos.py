#!/usr/bin/env python3
"""
Automated test suite that validates gesture recognition using video files.
Tests performance metrics, accuracy, and robustness.
"""

import cv2
import sys
import os
import time
import json
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hand_tracking import HandTracker
from gesture_recognition import GestureRecognizer

class VideoTestRunner:
    def __init__(self, test_data_dir="test_data/gestures"):
        self.test_data_dir = test_data_dir
        self.tracker = HandTracker()
        self.recognizer = GestureRecognizer()
        self.results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "performance": {},
            "accuracy": {}
        }

    def test_video(self, video_path, expected_gesture, min_accuracy=0.75):
        """
        Test a video file and validate gesture detection accuracy.
        
        Args:
            video_path: Path to video file
            expected_gesture: Expected gesture (FIST, POINTING, etc.)
            min_accuracy: Minimum required accuracy (default 75%)
        
        Returns:
            dict: Test results
        """
        if not os.path.exists(video_path):
            return {
                "passed": False,
                "error": f"Video file not found: {video_path}"
            }

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {
                "passed": False,
                "error": f"Could not open video: {video_path}"
            }

        frame_count = 0
        detect_count = 0
        correct_count = 0
        fps_samples = []
        
        print(f"\nTesting: {os.path.basename(video_path)}")
        print(f"Expected gesture: {expected_gesture}")

        while True:
            start_time = time.time()
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            hands_data = self.tracker.process_frame(frame)
            
            if hands_data:
                detect_count += 1
                detected = self.recognizer.detect_gesture(hands_data[0]['landmarks'])
                
                if detected == expected_gesture:
                    correct_count += 1
            
            # Measure FPS
            fps = 1.0 / (time.time() - start_time) if time.time() > start_time else 0
            fps_samples.append(fps)

        cap.release()

        # Calculate metrics
        accuracy = correct_count / detect_count if detect_count > 0 else 0
        avg_fps = sum(fps_samples) / len(fps_samples) if fps_samples else 0
        detection_rate = detect_count / frame_count if frame_count > 0 else 0

        passed = accuracy >= min_accuracy and detection_rate >= 0.8 and avg_fps >= 20

        result = {
            "passed": passed,
            "frames": frame_count,
            "detections": detect_count,
            "correct": correct_count,
            "accuracy": accuracy,
            "detection_rate": detection_rate,
            "avg_fps": avg_fps,
            "min_fps": min(fps_samples) if fps_samples else 0,
            "max_fps": max(fps_samples) if fps_samples else 0
        }

        print(f"  Frames: {frame_count}, Detections: {detect_count}, Correct: {correct_count}")
        print(f"  Accuracy: {accuracy:.1%}, Detection Rate: {detection_rate:.1%}")
        print(f"  FPS: {avg_fps:.1f} avg, {result['min_fps']:.1f} min, {result['max_fps']:.1f} max")
        print(f"  Result: {'PASS' if passed else 'FAIL'}")

        return result

    def run_all_tests(self):
        """Run all available gesture tests."""
        print("=" * 60)
        print("AUTOMATED GESTURE RECOGNITION TEST SUITE")
        print("=" * 60)

        test_cases = [
            ("fist.mp4", "FIST"),
            ("open_palm.mp4", "OPEN_PALM"),
            ("pointing.mp4", "POINTING"),
            ("pinch.mp4", "PINCH")
        ]

        for filename, expected_gesture in test_cases:
            video_path = os.path.join(self.test_data_dir, filename)
            
            if not os.path.exists(video_path):
                print(f"\n[SKIP] {filename} - File not found")
                continue

            self.results["tests_run"] += 1
            result = self.test_video(video_path, expected_gesture)
            
            if result["passed"]:
                self.results["tests_passed"] += 1
            else:
                self.results["tests_failed"] += 1
            
            self.results["accuracy"][expected_gesture] = result.get("accuracy", 0)
            self.results["performance"][expected_gesture] = result.get("avg_fps", 0)

        self.print_summary()
        self.save_results()

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Run: {self.results['tests_run']}")
        print(f"Passed: {self.results['tests_passed']}")
        print(f"Failed: {self.results['tests_failed']}")
        
        if self.results['accuracy']:
            print("\nAccuracy by Gesture:")
            for gesture, acc in self.results['accuracy'].items():
                print(f"  {gesture}: {acc:.1%}")
        
        if self.results['performance']:
            print("\nPerformance (FPS) by Gesture:")
            for gesture, fps in self.results['performance'].items():
                print(f"  {gesture}: {fps:.1f}")

        overall_pass = self.results['tests_failed'] == 0 and self.results['tests_run'] > 0
        print(f"\nOVERALL: {'PASS' if overall_pass else 'FAIL'}")
        print("=" * 60)

    def save_results(self):
        """Save results to JSON file."""
        with open("test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\nResults saved to: test_results.json")

    def cleanup(self):
        """Cleanup resources."""
        self.tracker.close()

def main():
    runner = VideoTestRunner()
    try:
        runner.run_all_tests()
    finally:
        runner.cleanup()

if __name__ == "__main__":
    main()
