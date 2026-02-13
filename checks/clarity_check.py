"""
Module for checking document clarity based on ink ratio.
"""

import cv2
import numpy as np
from PIL import Image


def calculate_ink_ratio(image):
    """
    Calculate the ink ratio (density of content) for an image.

    Args:
        image: PIL Image object

    Returns:
        float: Ink ratio (0.0 to 1.0)
    """
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

    return ink_ratio


def is_page_clear(image, threshold=0.005):
    """
    Check if a page has sufficient content based on ink ratio.

    Args:
        image: PIL Image object
        threshold: Minimum ink ratio threshold (default 0.005 = 0.5%)

    Returns:
        bool: True if page is clear/enough content, False otherwise
    """
    ink_ratio = calculate_ink_ratio(image)
    return ink_ratio >= threshold