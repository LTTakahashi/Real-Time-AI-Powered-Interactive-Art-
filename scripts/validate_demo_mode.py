"""
Comprehensive Edge Case Validation for Demo Mode
Tests all potential failure modes and edge cases before shipping.
"""
import cv2
import mediapipe as mp
import os
import json
from datetime import datetime

class DemoModeValidator:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {}
        }
        
    def test_video_file_integrity(self):
        """Test 1: Video file exists and is readable"""
        test_name = "video_file_integrity"
        print(f"\n{'='*60}")
        print(f"TEST 1: Video File Integrity")
        print(f"{'='*60}")
        
        issues = []
        
        # Check file exists
        if not os.path.exists('frontend/public/demo.mp4'):
            issues.append("demo.mp4 not found in frontend/public/")
            self.results["tests"][test_name] = {"status": "FAIL", "issues": issues}
            print("❌ FAIL: Video file not found")
            return False
        
        # Check file size
        size = os.path.getsize('frontend/public/demo.mp4')
        print(f"✓ File size: {size / 1024:.1f} KB")
        
        if size < 10000:  # Less than 10KB is suspicious
            issues.append(f"File size too small: {size} bytes")
        
        if size > 10_000_000:  # More than 10MB is too large
            issues.append(f"File size too large: {size} bytes (>10MB)")
        
        # Check file is readable by OpenCV
        cap = cv2.VideoCapture('frontend/public/demo.mp4')
        if not cap.isOpened():
            issues.append("Video cannot be opened by OpenCV")
            self.results["tests"][test_name] = {"status": "FAIL", "issues": issues}
            print("❌ FAIL: Video cannot be opened")
            return False
        
        # Get video properties
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        codec = int(cap.get(cv2.CAP_PROP_FOURCC))
        
        print(f"✓ Frames: {frame_count}")
        print(f"✓ FPS: {fps}")
        print(f"✓ Resolution: {width}x{height}")
        print(f"✓ Codec: {chr(codec & 0xFF)}{chr((codec >> 8) & 0xFF)}{chr((codec >> 16) & 0xFF)}{chr((codec >> 24) & 0xFF)}")
        
        # Validate properties
        if frame_count < 30:  # Less than 1 second at 30fps
            issues.append(f"Video too short: {frame_count} frames")
        
        if fps < 15 or fps > 60:
            issues.append(f"Unusual FPS: {fps}")
        
        if width != 640 or height != 480:
            issues.append(f"Non-standard resolution: {width}x{height} (expected 640x480)")
        
        cap.release()
        
        status = "PASS" if not issues else "WARN"
        self.results["tests"][test_name] = {
            "status": status,
            "issues": issues,
            "properties": {
                "size_kb": size / 1024,
                "frames": frame_count,
                "fps": fps,
                "resolution": f"{width}x{height}",
                "codec": f"{chr(codec & 0xFF)}{chr((codec >> 8) & 0xFF)}{chr((codec >> 16) & 0xFF)}{chr((codec >> 24) & 0xFF)}"
            }
        }
        
        if issues:
            print(f"⚠️  WARN: {len(issues)} issue(s) found")
            for issue in issues:
                print(f"    - {issue}")
        else:
            print("✅ PASS")
        
        return True
    
    def test_mediapipe_detection(self):
        """Test 2: MediaPipe hand detection reliability"""
        test_name = "mediapipe_detection"
        print(f"\n{'='*60}")
        print(f"TEST 2: MediaPipe Detection Reliability")
        print(f"{'='*60}")
        
        mp_hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        cap = cv2.VideoCapture('frontend/public/demo.mp4')
        
        total_frames = 0
        detected_frames = 0
        detection_sequence = []
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            total_frames += 1
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = mp_hands.process(rgb_frame)
            
            detected = results.multi_hand_landmarks is not None
            detected_frames += detected
            detection_sequence.append(1 if detected else 0)
        
        cap.release()
        mp_hands.close()
        
        detection_rate = (detected_frames / total_frames) * 100 if total_frames > 0 else 0
        
        print(f"✓ Total frames: {total_frames}")
        print(f"✓ Detected frames: {detected_frames}")
        print(f"✓ Detection rate: {detection_rate:.1f}%")
        
        # Check for gaps
        max_gap = 0
        current_gap = 0
        for detected in detection_sequence:
            if detected == 0:
                current_gap += 1
                max_gap = max(max_gap, current_gap)
            else:
                current_gap = 0
        
        print(f"✓ Max consecutive missed frames: {max_gap}")
        
        issues = []
        if detection_rate < 90:
            issues.append(f"Detection rate too low: {detection_rate:.1f}% (expected >90%)")
        
        if max_gap > 10:
            issues.append(f"Large detection gap: {max_gap} frames")
        
        status = "PASS" if detection_rate >= 95 else ("WARN" if detection_rate >= 80 else "FAIL")
        
        self.results["tests"][test_name] = {
            "status": status,
            "issues": issues,
            "metrics": {
                "total_frames": total_frames,
                "detected_frames": detected_frames,
                "detection_rate": round(detection_rate, 2),
                "max_gap": max_gap
            }
        }
        
        if issues:
            print(f"⚠️  {status}: {len(issues)} issue(s) found")
            for issue in issues:
                print(f"    - {issue}")
        else:
            print("✅ PASS")
        
        return status != "FAIL"
    
    def test_frame_quality(self):
        """Test 3: Video frame quality (brightness, contrast, noise)"""
        test_name = "frame_quality"
        print(f"\n{'='*60}")
        print(f"TEST 3: Video Frame Quality")
        print(f"{'='*60}")
        
        import numpy as np
        
        cap = cv2.VideoCapture('frontend/public/demo.mp4')
        
        brightness_values = []
        contrast_values = []
        
        frame_count = 0
        sample_interval = 30  # Sample every 30 frames
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            if frame_count % sample_interval != 0:
                continue
            
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Calculate brightness (mean)
            brightness = np.mean(gray)
            brightness_values.append(brightness)
            
            # Calculate contrast (std dev)
            contrast = np.std(gray)
            contrast_values.append(contrast)
        
        cap.release()
        
        avg_brightness = np.mean(brightness_values)
        avg_contrast = np.std(brightness_values)
        
        print(f"✓ Average brightness: {avg_brightness:.1f} (0-255)")
        print(f"✓ Brightness variance: {avg_contrast:.1f}")
        
        issues = []
        
        # Too dark
        if avg_brightness < 50:
            issues.append(f"Video too dark: {avg_brightness:.1f} (expected >50)")
        
        # Too bright
        if avg_brightness > 200:
            issues.append(f"Video too bright: {avg_brightness:.1f} (expected <200)")
        
        # Too uniform (low contrast)
        if avg_contrast < 10:
            issues.append(f"Low contrast: {avg_contrast:.1f}")
        
        status = "PASS" if not issues else "WARN"
        
        self.results["tests"][test_name] = {
            "status": status,
            "issues": issues,
            "metrics": {
                "avg_brightness": round(avg_brightness, 2),
                "brightness_variance": round(avg_contrast, 2)
            }
        }
        
        if issues:
            print(f"⚠️  WARN: {len(issues)} issue(s) found")
            for issue in issues:
                print(f"    - {issue}")
        else:
            print("✅ PASS")
        
        return True
    
    def test_codec_compatibility(self):
        """Test 4: Video codec is browser-compatible"""
        test_name = "codec_compatibility"
        print(f"\n{'='*60}")
        print(f"TEST 4: Codec Browser Compatibility")
        print(f"{'='*60}")
        
        cap = cv2.VideoCapture('frontend/public/demo.mp4')
        codec = int(cap.get(cv2.CAP_PROP_FOURCC))
        codec_str = f"{chr(codec & 0xFF)}{chr((codec >> 8) & 0xFF)}{chr((codec >> 16) & 0xFF)}{chr((codec >> 24) & 0xFF)}"
        cap.release()
        
        print(f"✓ Codec: {codec_str}")
        
        # H.264/AVC is the gold standard
        compatible_codecs = ['h264', 'avc1', 'H264', 'AVC1']
        issues = []
        
        if codec_str not in compatible_codecs:
            issues.append(f"Non-standard codec: {codec_str} (expected H.264/avc1)")
            status = "FAIL"
        else:
            status = "PASS"
            print("✓ Codec is H.264 (universally compatible)")
        
        self.results["tests"][test_name] = {
            "status": status,
            "issues": issues,
            "codec": codec_str
        }
        
        if status == "FAIL":
            print(f"❌ FAIL: Codec not compatible")
        else:
            print("✅ PASS")
        
        return status != "FAIL"
    
    def test_edge_cases(self):
        """Test 5: Edge cases (corrupted frames, etc.)"""
        test_name = "edge_cases"
        print(f"\n{'='*60}")
        print(f"TEST 5: Edge Cases")
        print(f"{'='*60}")
        
        cap = cv2.VideoCapture('frontend/public/demo.mp4')
        
        null_frames = 0
        total_frames = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            total_frames += 1
            
            if frame is None or frame.size == 0:
                null_frames += 1
        
        cap.release()
        
        print(f"✓ Total frames read: {total_frames}")
        print(f"✓ Null/corrupted frames: {null_frames}")
        
        issues = []
        if null_frames > 0:
            issues.append(f"Found {null_frames} corrupted frames")
        
        status = "PASS" if null_frames == 0 else "FAIL"
        
        self.results["tests"][test_name] = {
            "status": status,
            "issues": issues,
            "null_frames": null_frames,
            "total_frames": total_frames
        }
        
        if status == "FAIL":
            print(f"❌ FAIL: Found corrupted frames")
        else:
            print("✅ PASS")
        
        return status != "FAIL"
    
    def generate_report(self):
        """Generate final validation report"""
        print(f"\n{'='*60}")
        print(f"VALIDATION SUMMARY")
        print(f"{'='*60}")
        
        total_tests = len(self.results["tests"])
        passed = sum(1 for t in self.results["tests"].values() if t["status"] == "PASS")
        warned = sum(1 for t in self.results["tests"].values() if t["status"] == "WARN")
        failed = sum(1 for t in self.results["tests"].values() if t["status"] == "FAIL")
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed": passed,
            "warned": warned,
            "failed": failed,
            "ship_ready": failed == 0
        }
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"⚠️  Warned: {warned}")
        print(f"❌ Failed: {failed}")
        
        if failed == 0:
            print(f"\n🚀 SHIP READY: Demo Mode is validated and ready for production")
        else:
            print(f"\n🚫 NOT READY: {failed} critical issue(s) must be fixed before shipping")
        
        # Save report
        os.makedirs('test_data', exist_ok=True)
        with open('test_data/validation_report.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Report saved to test_data/validation_report.json")
        
        return failed == 0

if __name__ == "__main__":
    validator = DemoModeValidator()
    
    # Run all tests
    validator.test_video_file_integrity()
    validator.test_mediapipe_detection()
    validator.test_frame_quality()
    validator.test_codec_compatibility()
    validator.test_edge_cases()
    
    # Generate report
    ship_ready = validator.generate_report()
    
    exit(0 if ship_ready else 1)
