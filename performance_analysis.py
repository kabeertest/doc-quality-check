"""
Performance analysis script for document quality checks.
Measures execution time of clarity and confidence checks.
"""

import time
import numpy as np
from PIL import Image
import cv2
import pytesseract

# Import the check functions
from checks.clarity_check import calculate_ink_ratio
from checks.confidence_check import calculate_ocr_confidence
from utils.content_extraction import extract_text_content


def create_test_images():
    """Create various test images to simulate different document qualities."""
    # Create a white image (empty page simulation)
    white_img = Image.new('RGB', (500, 700), color='white')
    
    # Create a text-heavy image (simulating a filled page)
    text_img = Image.new('RGB', (500, 700), color='white')
    # We'll simulate text by drawing some rectangles and lines
    import PIL.ImageDraw
    draw = PIL.ImageDraw.Draw(text_img)
    # Draw some simulated text lines
    for i in range(20):
        y_pos = 50 + i * 30
        draw.rectangle([50, y_pos, 450, y_pos + 20], fill='black')
    
    # Create a medium content image
    medium_img = Image.new('RGB', (500, 700), color='lightgray')
    draw = PIL.ImageDraw.Draw(medium_img)
    # Draw fewer elements
    for i in range(5):
        y_pos = 100 + i * 100
        draw.rectangle([100, y_pos, 400, y_pos + 30], fill='darkgray')
    
    return {
        'white': white_img,
        'text_heavy': text_img,
        'medium': medium_img
    }


def benchmark_function(func, image, iterations=5):
    """Benchmark a function with multiple iterations."""
    times = []
    for _ in range(iterations):
        start_time = time.time()
        result = func(image)
        end_time = time.time()
        times.append(end_time - start_time)
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    return avg_time, min_time, max_time


def analyze_clarity_check(images):
    """Analyze performance of clarity check."""
    print("=== CLARITY CHECK ANALYSIS ===")
    
    for name, img in images.items():
        avg_time, min_time, max_time = benchmark_function(calculate_ink_ratio, img)
        print(f"{name.upper()} image:")
        print(f"  Average time: {avg_time:.4f}s")
        print(f"  Min time: {min_time:.4f}s")
        print(f"  Max time: {max_time:.4f}s")
        print()


def analyze_confidence_check(images):
    """Analyze performance of confidence check."""
    print("=== CONFIDENCE CHECK ANALYSIS (BALANCED MODE) ===")
    
    for name, img in images.items():
        avg_time, min_time, max_time = benchmark_function(lambda x: calculate_ocr_confidence(x, mode='balanced'), img)
        print(f"{name.upper()} image:")
        print(f"  Average time: {avg_time:.4f}s")
        print(f"  Min time: {min_time:.4f}s")
        print(f"  Max time: {max_time:.4f}s")
        print()
    
    print("=== CONFIDENCE CHECK ANALYSIS (FAST MODE) ===")
    
    for name, img in images.items():
        avg_time, min_time, max_time = benchmark_function(lambda x: calculate_ocr_confidence(x, mode='fast'), img)
        print(f"{name.upper()} image:")
        print(f"  Average time: {avg_time:.4f}s")
        print(f"  Min time: {min_time:.4f}s")
        print(f"  Max time: {max_time:.4f}s")
        print()


def analyze_content_extraction(images):
    """Analyze performance of content extraction."""
    print("=== CONTENT EXTRACTION ANALYSIS ===")
    
    for name, img in images.items():
        avg_time, min_time, max_time = benchmark_function(extract_text_content, img)
        print(f"{name.upper()} image:")
        print(f"  Average time: {avg_time:.4f}s")
        print(f"  Min time: {min_time:.4f}s")
        print(f"  Max time: {max_time:.4f}s")
        print()


def analyze_tesseract_availability():
    """Check if Tesseract is available and its version."""
    print("=== TESSERACT INFORMATION ===")
    try:
        version = pytesseract.get_tesseract_version()
        print(f"Tesseract version: {version}")
        print("Tesseract is available")
    except:
        print("Tesseract is NOT available")
    print()


def main():
    print("Document Quality Check Performance Analysis")
    print("=" * 50)
    
    # Check Tesseract availability
    analyze_tesseract_availability()
    
    # Create test images
    print("Creating test images...")
    images = create_test_images()
    print("Test images created.\n")
    
    # Analyze each check
    analyze_clarity_check(images)
    analyze_confidence_check(images)
    analyze_content_extraction(images)
    
    print("Analysis complete.")


if __name__ == "__main__":
    main()