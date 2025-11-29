#!/usr/bin/env python3
"""
Comprehensive tests for Stable Diffusion style transfer system.
Tests smart cropping, image preparation, and (optionally) model loading.
"""

import unittest
import sys
import os
import numpy as np
import cv2
from PIL import Image

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from style_transfer import StableDiffusionStyleTransfer, STYLE_PRESETS

class TestSmartCrop(unittest.TestCase):
    """Test smart cropping functionality."""
    
    def setUp(self):
        self.sd = StableDiffusionStyleTransfer()
    
    def test_empty_canvas(self):
        """Test cropping empty (all-white) canvas."""
        empty = np.full((1024, 1024, 3), 255, dtype=np.uint8)
        cropped, info = self.sd.smart_crop(empty)
        
        # Should return full image when no content
        self.assertIsNone(info['bbox'])
        self.assertEqual(cropped.size, (1024, 1024))
    
    def test_single_stroke(self):
        """Test cropping canvas with single stroke."""
        canvas = np.full((1024, 1024, 3), 255, dtype=np.uint8)
        
        # Draw black rectangle in center
        cv2.rectangle(canvas, (400, 400), (600, 600), (0, 0, 0), -1)
        
        cropped, info = self.sd.smart_crop(canvas, margin_percent=0.15)
        
        # Should have bounding box
        self.assertIsNotNone(info['bbox'])
        x1, y1, x2, y2 = info['bbox']
        
        # Bbox should contain the rectangle with margin
        self.assertLess(x1, 400)
        self.assertLess(y1, 400)
        self.assertGreater(x2, 600)
        self.assertGreater(y2, 600)
        
        # Cropped should be smaller than original
        self.assertLess(cropped.size[0] + cropped.size[1], 2048)
    
    def test_margin_calculation(self):
        """Test that margin is correctly applied."""
        canvas = np.full((1024, 1024, 3), 255, dtype=np.uint8)
        
        # Draw small 100x100 square
        cv2.rectangle(canvas, (500, 500), (600, 600), (0, 0, 0), -1)
        
        # Test with 15% margin
        cropped_15, info_15 = self.sd.smart_crop(canvas, margin_percent=0.15)
        
        # Test with 30% margin
        cropped_30, info_30 = self.sd.smart_crop(canvas, margin_percent=0.30)
        
        # 30% margin should produce larger crop
        self.assertGreater(cropped_30.size[0], cropped_15.size[0])
        self.assertGreater(cropped_30.size[1], cropped_15.size[1])
    
    def test_edge_content(self):
        """Test cropping when content touches edges."""
        canvas = np.full((1024, 1024, 3), 255, dtype=np.uint8)
        
        # Draw at top-left corner
        cv2.rectangle(canvas, (0, 0), (100, 100), (0, 0, 0), -1)
        
        cropped, info = self.sd.smart_crop(canvas)
        
        # Should not go negative
        x1, y1, x2, y2 = info['bbox']
        self.assertGreaterEqual(x1, 0)
        self.assertGreaterEqual(y1, 0)


class TestImagePreparation(unittest.TestCase):
    """Test image preparation for SD."""
    
    def setUp(self):
        self.sd = StableDiffusionStyleTransfer()
    
    def test_resize_to_512(self):
        """Test resizing to 512x512."""
        canvas = np.full((1024, 1024, 3), 255, dtype=np.uint8)
        cv2.rectangle(canvas, (400, 400), (600, 600), (0, 0, 0), -1)
        
        prepared, info = self.sd.prepare_image(canvas, target_size=512)
        
        # Should be around 512 (might be slightly different due to aspect ratio + divisible by 8)
        self.assertLessEqual(max(prepared.size), 512)
        self.assertGreater(min(prepared.size), 400)  # Should not be too small
        
        # Dimensions should be divisible by 8
        self.assertEqual(prepared.size[0] % 8, 0)
        self.assertEqual(prepared.size[1] % 8, 0)
    
    def test_aspect_ratio_preservation(self):
        """Test that aspect ratio is roughly preserved."""
        # Create wide canvas content
        canvas = np.full((1024, 1024, 3), 255, dtype=np.uint8)
        cv2.rectangle(canvas, (200, 400), (800, 600), (0, 0, 0), -1)  # Wide rectangle
        
        prepared, info = self.sd.prepare_image(canvas, target_size=512)
        
        # Should be wider than tall
        self.assertGreater(prepared.size[0], prepared.size[1])
    
    def test_size_info_tracking(self):
        """Test that size information is tracked."""
        canvas = np.full((1024, 1024, 3), 255, dtype=np.uint8)
        cv2.rectangle(canvas, (400, 400), (600, 600), (0, 0, 0), -1)
        
        prepared, info = self.sd.prepare_image(canvas)
        
        self.assertIn('original_size', info)
        self.assertIn('cropped_size', info)
        self.assertIn('resized_size', info)
        
        # Resized should match prepared image dimensions
        self.assertEqual(info['resized_size'], prepared.size)


class TestStylePresets(unittest.TestCase):
    """Test style preset definitions."""
    
    def test_all_presets_valid(self):
        """Test that all presets have required fields."""
        for style_name, preset in STYLE_PRESETS.items():
            self.assertIsInstance(preset.name, str)
            self.assertIsInstance(preset.prompt, str)
            self.assertIsInstance(preset.negative_prompt, str)
            self.assertIsInstance(preset.strength, float)
            self.assertIsInstance(preset.guidance_scale, float)
            
            # Strength should be in valid range
            self.assertGreater(preset.strength, 0.5)
            self.assertLess(preset.strength, 1.0)
            
            # Guidance scale should be reasonable
            self.assertGreater(preset.guidance_scale, 5.0)
            self.assertLess(preset.guidance_scale, 15.0)
    
    def test_prompts_are_detailed(self):
        """Test that prompts are detailed (not single words)."""
        for preset in STYLE_PRESETS.values():
            # Should have multiple words
            self.assertGreater(len(preset.prompt.split()), 3)
            
            # Should not be just the style name
            self.assertGreater(len(preset.prompt), 20)
    
    def test_all_required_styles_present(self):
        """Test that required styles from plan are present."""
        required = ['photorealistic', 'anime', 'oil_painting']
        for style in required:
            self.assertIn(style, STYLE_PRESETS)


class TestModelInterface(unittest.TestCase):
    """Test model interface (without actually loading heavy model)."""
    
    def setUp(self):
        self.sd = StableDiffusionStyleTransfer()
    
    def test_device_detection(self):
        """Test that device is detected."""
        self.assertIn(self.sd.device, ['cuda', 'cpu'])
    
    def test_unloaded_generation_raises(self):
        """Test that generation fails if model not loaded."""
        canvas = np.full((512, 512, 3), 255, dtype=np.uint8)
        
        with self.assertRaises(RuntimeError):
            self.sd.generate(canvas, style='photorealistic')
    
    def test_invalid_style_raises(self):
        """Test that invalid style raises error."""
        # Mock loaded state
        self.sd.is_loaded = True
        self.sd.pipeline = lambda: None  # Mock pipeline
        
        canvas = np.full((512, 512, 3), 255, dtype=np.uint8)
        
        with self.assertRaises(ValueError):
            self.sd.generate(canvas, style='invalid_style_name')


# Optional: Model Loading Test (only runs if explicitly enabled)
class TestModelLoading(unittest.TestCase):
    """Optional tests that actually load the model (slow!)."""
    
    @unittest.skipUnless(os.environ.get('TEST_SD_MODEL') == '1', 
                        "Skipping model loading test (set TEST_SD_MODEL=1 to enable)")
    def test_model_loads(self):
        """Test that model actually loads (SLOW - downloads ~6GB)."""
        sd = StableDiffusionStyleTransfer('stabilityai/sdxl-turbo')
        
        progress_messages = []
        sd.load_model(progress_callback=lambda msg: progress_messages.append(msg))
        
        self.assertTrue(sd.is_loaded)
        self.assertIsNotNone(sd.pipeline)
        self.assertGreater(sd.load_time, 0)
        
        # Should have progress messages
        self.assertGreater(len(progress_messages), 0)
    
    @unittest.skipUnless(os.environ.get('TEST_SD_MODEL') == '1',
                        "Skipping generation test")
    def test_generation(self):
        """Test actual image generation (VERY SLOW)."""
        sd = StableDiffusionStyleTransfer('stabilityai/sdxl-turbo')
        sd.load_model()
        
        # Create test canvas
        canvas = np.full((1024, 1024, 3), 255, dtype=np.uint8)
        cv2.rectangle(canvas, (400, 400), (600, 600), (0, 0, 0), -1)
        
        # Generate
        result, metadata = sd.generate(canvas, style='photorealistic', num_inference_steps=1)
        
        self.assertIsInstance(result, Image.Image)
        self.assertIn('generation_time', metadata)
        self.assertIn('style', metadata)
        
        print(f"\nGeneration time: {metadata['generation_time']:.2f}s")
        
        # Should be fast (<5s for 1 step)
        self.assertLess(metadata['generation_time'], 5.0)


def run_style_transfer_tests():
    """Run all style transfer tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Always run these
    suite.addTests(loader.loadTestsFromTestCase(TestSmartCrop))
    suite.addTests(loader.loadTestsFromTestCase(TestImagePreparation))
    suite.addTests(loader.loadTestsFromTestCase(TestStylePresets))
    suite.addTests(loader.loadTestsFromTestCase(TestModelInterface))
    
    # Optionally run model tests
    suite.addTests(loader.loadTestsFromTestCase(TestModelLoading))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("="*60)
    print("STYLE TRANSFER TESTS")
    print("="*60)
    print("Note: Model loading tests are skipped by default.")
    print("To enable: export TEST_SD_MODEL=1")
    print("="*60 + "\n")
    
    success = run_style_transfer_tests()
    sys.exit(0 if success else 1)
