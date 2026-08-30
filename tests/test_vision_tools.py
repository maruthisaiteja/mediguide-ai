"""Unit and integration tests for MediGuide Vision AI tools."""
import pytest
import os
import sys
import tempfile
from PIL import Image

# Ensure src is importable
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.tools.vision_tools import validate_image_file, preprocess_image

def test_validate_image_file_valid(tmp_path):
    img_file = tmp_path / "test_valid.png"
    img = Image.new("RGB", (200, 200), color="white")
    img.save(img_file)
    
    res = validate_image_file(str(img_file))
    assert res["valid"] is True
    assert res["format"] == "PNG"
    assert res["dimensions"] == (200, 200)

def test_validate_image_file_nonexistent():
    res = validate_image_file("nonexistent_path_12345.png")
    assert res["valid"] is False
    assert "does not exist" in res["reason"]

def test_validate_image_file_empty(tmp_path):
    empty_file = tmp_path / "empty.jpg"
    empty_file.write_bytes(b"")
    
    res = validate_image_file(str(empty_file))
    assert res["valid"] is False
    assert "empty" in res["reason"]

def test_preprocess_image_rescaling(tmp_path):
    # Large 2000x1500 image should be rescaled to max dim 1024
    img_file = tmp_path / "large_img.jpg"
    img = Image.new("RGB", (2000, 1500), color="blue")
    img.save(img_file, format="JPEG")
    
    processed_bytes = preprocess_image(str(img_file), max_size=(1024, 1024))
    
    import io
    processed_img = Image.open(io.BytesIO(processed_bytes))
    assert max(processed_img.size) <= 1024
    assert processed_img.mode == "RGB"

def test_preprocess_image_rgba_to_rgb(tmp_path):
    # RGBA image should be converted to RGB without transparency
    img_file = tmp_path / "rgba_img.png"
    img = Image.new("RGBA", (500, 500), color=(255, 0, 0, 128))
    img.save(img_file, format="PNG")
    
    processed_bytes = preprocess_image(str(img_file))
    
    import io
    processed_img = Image.open(io.BytesIO(processed_bytes))
    assert processed_img.mode == "RGB"
