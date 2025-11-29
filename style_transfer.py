"""
Stable Diffusion style transfer system.
Uses SDXL-Turbo for fast (0.8-2s) style transfer.
Includes smart cropping, async generation, and style presets.
"""

import torch
import numpy as np
from PIL import Image
import cv2
from typing import Optional, Tuple, Callable
from dataclasses import dataclass
import time

# Lazy imports for diffusers (only when needed)
_diffusers_loaded = False
_pipeline = None

@dataclass
class StylePreset:
    name: str
    prompt: str
    negative_prompt: str
    strength: float
    guidance_scale: float

# Style presets based on implementation plan
STYLE_PRESETS = {
    'photorealistic': StylePreset(
        name='Photorealistic',
        prompt='professional photography, highly detailed, sharp focus, 8k resolution, natural lighting, award winning photo',
        negative_prompt='cartoon, digital art, illustration, painting, drawing, anime',
        strength=0.70,
        guidance_scale=8.0
    ),
    'anime': StylePreset(
        name='Anime Style',
        prompt='anime illustration, clean line art, vibrant colors, Studio Ghibli style, high quality, cel shading',
        negative_prompt='photo, realistic, 3d render, blurry, low quality',
        strength=0.75,
        guidance_scale=7.5
    ),
    'oil_painting': StylePreset(
        name='Oil Painting',
        prompt='oil painting on canvas, brushstrokes visible, impressionist style, classical art, museum quality, rich colors',
        negative_prompt='photo, digital art, 3d render, low quality',
        strength=0.80,
        guidance_scale=9.0
    ),
    'watercolor': StylePreset(
        name='Watercolor',
        prompt='watercolor painting, soft edges, translucent colors, artistic, high quality, on textured paper',
        negative_prompt='photo, digital art, sharp edges, low quality',
        strength=0.75,
        guidance_scale=8.0
    ),
    'sketch': StylePreset(
        name='Pencil Sketch',
        prompt='pencil sketch, graphite drawing, artistic shading, detailed linework, high quality illustration',
        negative_prompt='photo, color, digital art, low quality',
        strength=0.70,
        guidance_scale=7.0
    )
}


class StableDiffusionStyleTransfer:
    """Manager for Stable Diffusion style transfer operations."""
    
    def __init__(self, model_id: str = "stabilityai/sdxl-turbo", device: Optional[str] = None):
        """
        Initialize SD style transfer.
        
        Args:
            model_id: Model to use (default: SDXL-Turbo for speed)
            device: Device to use ('cuda', 'cpu', or None for auto)
        """
        self.model_id = model_id
        
        # Auto-detect device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        self.pipeline = None
        self.is_loaded = False
        self.load_time = 0
    
    def load_model(self, progress_callback: Optional[Callable[[str], None]] = None):
        """
        Load the SD model.
        
        Args:
            progress_callback: Function to call with progress updates
        """
        if self.is_loaded:
            return
        
        global _diffusers_loaded, _pipeline
        
        start_time = time.time()
        
        if progress_callback:
            progress_callback("Importing diffusers library...")
        
        # Lazy import
        if not _diffusers_loaded:
            from diffusers import AutoPipelineForImage2Image
            import torch
            _diffusers_loaded = True
        
        if progress_callback:
            progress_callback(f"Loading {self.model_id}...")
        
        # Load pipeline
        from diffusers import AutoPipelineForImage2Image
        
        self.pipeline = AutoPipelineForImage2Image.from_pretrained(
            self.model_id,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            variant="fp16" if self.device == "cuda" else None
        )
        
        if self.device == "cuda":
            self.pipeline = self.pipeline.to("cuda")
            
            # Enable memory optimizations
            if progress_callback:
                progress_callback("Enabling memory optimizations...")
            self.pipeline.enable_attention_slicing()
            self.pipeline.enable_vae_slicing()
        
        self.is_loaded = True
        self.load_time = time.time() - start_time
        
        if progress_callback:
            progress_callback(f"Model loaded in {self.load_time:.1f}s")
    
    def smart_crop(self, image: np.ndarray, margin_percent: float = 0.15) -> Tuple[Image.Image, dict]:
        """
        Intelligently crop canvas to content with margin.
        
        Args:
            image: Input image (numpy array, BGR)
            margin_percent: Margin to add around content (0.15 = 15%)
        
        Returns:
            Cropped PIL Image and crop info dict
        """
        # Convert to grayscale for content detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Threshold to find non-white pixels (content)
        _, thresh = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)
        
        # Find bounding box of content
        coords = cv2.findNonZero(thresh)
        
        if coords is None:
            # No content, return full image
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            return pil_image, {'bbox': None, 'margin': margin_percent}
        
        x, y, w, h = cv2.boundingRect(coords)
        
        # Add margin
        img_h, img_w = image.shape[:2]
        margin_w = int(w * margin_percent)
        margin_h = int(h * margin_percent)
        
        x1 = max(0, x - margin_w)
        y1 = max(0, y - margin_h)
        x2 = min(img_w, x + w + margin_w)
        y2 = min(img_h, y + h + margin_h)
        
        # Crop
        cropped = image[y1:y2, x1:x2]
        
        # Convert to RGB PIL Image
        pil_image = Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))
        
        crop_info = {
            'bbox': (x1, y1, x2, y2),
            'original_size': (img_w, img_h),
            'cropped_size': (x2-x1, y2-y1),
            'margin': margin_percent
        }
        
        return pil_image, crop_info
    
    def prepare_image(self, image: np.ndarray, target_size: int = 512) -> Tuple[Image.Image, dict]:
        """
        Prepare image for SD: smart crop + resize.
        
        Args:
            image: Input canvas (numpy array, BGR)
            target_size: Target size for SD (512 or 768)
        
        Returns:
            Prepared PIL Image and processing info
        """
        # Smart crop
        cropped, crop_info = self.smart_crop(image)
        
        # Resize to target while maintaining aspect ratio
        original_size = cropped.size
        aspect = original_size[0] / original_size[1]
        
        if aspect > 1:  # Wider than tall
            new_w = target_size
            new_h = int(target_size / aspect)
        else:
            new_h = target_size
            new_w = int(target_size * aspect)
        
        # Make dimensions multiples of 8 (SD requirement)
        new_w = (new_w // 8) * 8
        new_h = (new_h // 8) * 8
        
        resized = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        crop_info['resized_size'] = (new_w, new_h)
        
        return resized, crop_info
    
    def generate(self,
                input_image: np.ndarray,
                style: str = 'photorealistic',
                num_inference_steps: int = 4,
                progress_callback: Optional[Callable[[int, int], None]] = None) -> Tuple[Image.Image, dict]:
        """
        Generate styled image.
        
        Args:
            input_image: Canvas image (numpy array, BGR)
            style: Style preset name
            num_inference_steps: Number of diffusion steps (1-4 for Turbo)
            progress_callback: Function(current_step, total_steps)
        
        Returns:
            Styled PIL Image and generation metadata
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        start_time = time.time()
        
        # Get style preset
        if style not in STYLE_PRESETS:
            raise ValueError(f"Unknown style: {style}. Available: {list(STYLE_PRESETS.keys())}")
        
        preset = STYLE_PRESETS[style]
        
        # Prepare image
        prepared_image, prep_info = self.prepare_image(input_image)
        
        # Generate
        result = self.pipeline(
            prompt=preset.prompt,
            negative_prompt=preset.negative_prompt,
            image=prepared_image,
            strength=preset.strength,
            guidance_scale=preset.guidance_scale,
            num_inference_steps=num_inference_steps,
            callback=lambda step, *args: progress_callback(step, num_inference_steps) if progress_callback else None
        )
        
        generation_time = time.time() - start_time
        
        metadata = {
            'style': style,
            'preset': preset.name,
            'generation_time': generation_time,
            'num_steps': num_inference_steps,
            'device': self.device,
            'prep_info': prep_info
        }
        
        return result.images[0], metadata
    
    def get_vram_usage(self) -> Optional[dict]:
        """Get current VRAM usage (CUDA only)."""
        if self.device != "cuda" or not torch.cuda.is_available():
            return None
        
        allocated = torch.cuda.memory_allocated() / (1024**3)  # GB
        reserved = torch.cuda.memory_reserved() / (1024**3)   # GB
        
        return {
            'allocated_gb': allocated,
            'reserved_gb': reserved
        }
    
    def clear_cache(self):
        """Clear CUDA cache to free VRAM."""
        if self.device == "cuda" and torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    def unload_model(self):
        """Unload model from memory."""
        if self.pipeline is not None:
            del self.pipeline
            self.pipeline = None
            self.is_loaded = False
            
            if self.device == "cuda":
                self.clear_cache()
