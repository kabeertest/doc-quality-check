"""
Module for checking document clarity based on ink ratio.
"""

import cv2
import numpy as np
import time
from PIL import Image


def calculate_ink_ratio(image):
    """
    Calculate the ink ratio (density of content) for an image.

    Args:
        image: PIL Image object

    Returns:
        tuple: (ink_ratio (float), calculation_time (float)) - Ink ratio (0.0 to 1.0) and time taken in seconds
    """
    start_time = time.time()
    
    # Convert PIL image to OpenCV format
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # Convert to grayscale for processing
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    # Apply Otsu's thresholding to get binary image
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Calculate ink ratio (non-zero pixels / total pixels)
    total_pixels = thresh.shape[0] * thresh.shape[1]
    ink_pixels = cv2.countNonZero(thresh)
    ink_ratio = ink_pixels / total_pixels if total_pixels > 0 else 0

    calculation_time = time.time() - start_time
    return ink_ratio, calculation_time