"""
MediGuide Vision AI — Image Preprocessing and Verification Tools
===============================================================
Provides image handling utilities to support the Image Processing domain.
Uses Pillow to validate, resize, format, and normalize medical images, prescription scans,
and pill bottles before they are passed to the multimodal LLM agents.
"""

import io
import os
from typing import Tuple, Optional
from PIL import Image

def validate_image_file(image_path: str) -> dict:
    """
    Validates that an image file exists, is not empty, and is of a supported format.

    Args:
        image_path: The absolute or relative path to the image file.

    Returns:
        dict containing 'valid' (bool), 'reason' (str or None), 'format' (str),
        and 'dimensions' (tuple).
    """
    result = {
        "valid": False,
        "reason": None,
        "format": None,
        "dimensions": None,
        "size_bytes": 0
    }

    if not os.path.exists(image_path):
        result["reason"] = f"Image file does not exist: {image_path}"
        return result

    result["size_bytes"] = os.path.getsize(image_path)
    if result["size_bytes"] == 0:
        result["reason"] = "Image file is empty (0 bytes)."
        return result

    try:
        with Image.open(image_path) as img:
            result["valid"] = True
            result["format"] = img.format
            result["dimensions"] = img.size
    except Exception as e:
        result["reason"] = f"Failed to open/parse image: {str(e)}"

    return result


def preprocess_image(image_path: str, max_size: Tuple[int, int] = (1024, 1024)) -> bytes:
    """
    Preprocesses an image file by:
      1. Validating the file
      2. Downscaling/resizing if it exceeds max_size (preserving aspect ratio)
      3. Normalizing format to JPEG
      4. Returning raw bytes ready for the Generative Multimodal API

    This ensures optimal token usage, protects against API payload size limits,
    and standardizes input for downstream multimodal agents.

    Args:
        image_path: Path to the input image file.
        max_size: Maximum width/height boundary for scaling.

    Returns:
        bytes: Raw JPEG image bytes.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the image cannot be processed.
    """
    validation = validate_image_file(image_path)
    if not validation["valid"]:
        raise ValueError(f"Invalid image file: {validation['reason']}")

    try:
        with Image.open(image_path) as img:
            # Convert to RGB (in case of PNG alpha transparency or grayscale)
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Check if resizing is necessary
            width, height = img.size
            max_w, max_h = max_size

            if width > max_w or height > max_h:
                # Calculate scale factor maintaining aspect ratio
                ratio = min(max_w / width, max_h / height)
                new_size = (int(width * ratio), int(height * ratio))
                # Image processing: Resize with Lanczos interpolation for high quality downscaling
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            # Save rescaled image to a byte buffer
            byte_arr = io.BytesIO()
            img.save(byte_arr, format="JPEG", quality=85)
            return byte_arr.getvalue()

    except Exception as e:
        raise ValueError(f"Failed during image preprocessing: {str(e)}")
