"""
Module for checking document confidence based on OCR results.
"""

import cv2
import pytesseract
import numpy as np
import time
from PIL import Image
from functools import lru_cache


def resize_image_for_ocr(image, max_size=(800, 800)):
    """
    Resize image to reduce processing time while maintaining aspect ratio.
    
    Args:
        image: PIL Image object
        max_size: Tuple of (max_width, max_height)
        
    Returns:
        PIL Image: Resized image
    """
    img_cv = np.array(image)
    height, width = img_cv.shape[:2]
    
    # Calculate scaling factor to fit within max_size
    scale = min(max_size[0]/width, max_size[1]/height, 1.0)  # Don't upscale
    
    if scale < 1.0:
        new_width = int(width * scale)
        new_height = int(height * scale)
        img_cv = cv2.resize(img_cv, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # Convert back to PIL Image
        if len(img_cv.shape) == 3:
            img_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
        else:
            img_pil = Image.fromarray(img_cv)
        return img_pil
    
    return image


def calculate_ocr_confidence_fast(image):
    """
    Fast version of OCR confidence calculation - single PSM mode only with image resizing.

    Args:
        image: PIL Image object

    Returns:
        tuple: (confidence_score (float), calculation_time (float)) - Confidence score (0.0 to 100.0) and time taken in seconds
    """
    start_time = time.time()

    # Resize image to speed up OCR
    resized_image = resize_image_for_ocr(image)
    
    # Convert PIL image to OpenCV format
    img_cv = cv2.cvtColor(np.array(resized_image), cv2.COLOR_RGB2BGR)

    # Convert to grayscale for OCR
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    # Single PSM mode for speed with minimal whitelist
    config_str = '--psm 6 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

    try:
        ocr_data = pytesseract.image_to_data(
            gray,
            output_type=pytesseract.Output.DICT,
            config=config_str
        )

        # Filter out rows with empty text/whitespace and invalid confidence values
        confidences = []
        n_boxes = len(ocr_data['text'])
        for i in range(n_boxes):
            text = ocr_data['text'][i]
            # Check if the text is not empty and confidence is valid (0-100)
            if text.strip() and ocr_data['conf'][i] != -1:
                confidences.append(ocr_data['conf'][i])

        # Calculate average confidence
        avg_conf = sum(confidences) / len(confidences) if confidences else 0

    except Exception:
        avg_conf = 0

    calculation_time = time.time() - start_time
    return avg_conf, calculation_time


def calculate_ocr_confidence_superfast(image):
    """
    Super fast version of OCR confidence calculation - minimal processing.

    Args:
        image: PIL Image object

    Returns:
        tuple: (confidence_score (float), calculation_time (float)) - Confidence score (0.0 to 100.0) and time taken in seconds
    """
    start_time = time.time()

    # Resize image significantly to speed up OCR
    resized_image = resize_image_for_ocr(image, max_size=(400, 400))
    
    # Convert PIL image to OpenCV format
    img_cv = cv2.cvtColor(np.array(resized_image), cv2.COLOR_RGB2BGR)

    # Convert to grayscale for OCR
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    # Use the simplest PSM mode for speed
    config_str = '--psm 7'  # Treat the image as a single text line

    try:
        ocr_data = pytesseract.image_to_data(
            gray,
            output_type=pytesseract.Output.DICT,
            config=config_str
        )

        # Filter out rows with empty text/whitespace and invalid confidence values
        confidences = []
        n_boxes = len(ocr_data['text'])
        for i in range(n_boxes):
            text = ocr_data['text'][i]
            # Check if the text is not empty and confidence is valid (0-100)
            if text.strip() and ocr_data['conf'][i] != -1:
                confidences.append(ocr_data['conf'][i])

        # Calculate average confidence
        avg_conf = sum(confidences) / len(confidences) if confidences else 0

    except Exception:
        avg_conf = 0

    calculation_time = time.time() - start_time
    return avg_conf, calculation_time


def calculate_ocr_confidence_balanced(image):
    """
    Balanced version of OCR confidence calculation - moderate accuracy and speed.

    Args:
        image: PIL Image object

    Returns:
        tuple: (confidence_score (float), calculation_time (float)) - Confidence score (0.0 to 100.0) and time taken in seconds
    """
    start_time = time.time()

    # Resize image to speed up OCR
    resized_image = resize_image_for_ocr(image)
    
    # Convert PIL image to OpenCV format
    img_cv = cv2.cvtColor(np.array(resized_image), cv2.COLOR_RGB2BGR)

    # Convert to grayscale for OCR
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    # Try single PSM mode first (most common and fastest)
    config_str = '--psm 6 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

    try:
        ocr_data = pytesseract.image_to_data(
            gray,
            output_type=pytesseract.Output.DICT,
            config=config_str
        )

        # Filter out rows with empty text/whitespace and invalid confidence values
        confidences = []
        n_boxes = len(ocr_data['text'])
        for i in range(n_boxes):
            text = ocr_data['text'][i]
            # Check if the text is not empty and confidence is valid (0-100)
            if text.strip() and ocr_data['conf'][i] != -1:
                confidences.append(ocr_data['conf'][i])

        # Calculate average confidence
        best_conf = sum(confidences) / len(confidences) if confidences else 0

        # If confidence is reasonably high, return early (optimization)
        if best_conf >= 15:  # If we have decent confidence, no need to try other modes
            calculation_time = time.time() - start_time
            return best_conf, calculation_time

    except Exception:
        best_conf = 0

    # If confidence is low, try enhancement and one more PSM mode
    if best_conf < 10:
        # Enhance image for better OCR
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (1, 1), 0)

        # Apply adaptive threshold to enhance text
        enhanced = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

        # Try one more PSM mode only if needed
        psm_mode = '--psm 4'
        config_str = psm_mode + ' -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

        try:
            enhanced_ocr_data = pytesseract.image_to_data(
                enhanced,
                output_type=pytesseract.Output.DICT,
                config=config_str
            )

            enhanced_confidences = []
            n_boxes = len(enhanced_ocr_data['text'])
            for i in range(n_boxes):
                text = enhanced_ocr_data['text'][i]
                # Check if the text is not empty and confidence is valid (0-100)
                if text.strip() and enhanced_ocr_data['conf'][i] != -1:
                    enhanced_confidences.append(enhanced_ocr_data['conf'][i])

            enhanced_avg_conf = sum(enhanced_confidences) / len(enhanced_confidences) if enhanced_confidences else 0

            # Update best confidence if this is better
            if enhanced_avg_conf > best_conf:
                best_conf = enhanced_avg_conf

        except Exception:
            pass

    calculation_time = time.time() - start_time
    return best_conf, calculation_time


def calculate_ocr_confidence(image, mode='balanced'):
    """
    Calculate the OCR confidence score for an image with configurable speed/accuracy.

    Args:
        image: PIL Image object
        mode: 'superfast', 'fast', 'balanced', or 'accurate' (default 'balanced')

    Returns:
        tuple: (confidence_score (float), calculation_time (float)) - Confidence score (0.0 to 100.0) and time taken in seconds
    """
    if mode == 'superfast':
        return calculate_ocr_confidence_superfast(image)
    elif mode == 'fast':
        return calculate_ocr_confidence_fast(image)
    elif mode == 'balanced':
        return calculate_ocr_confidence_balanced(image)
    else:  # accurate (original behavior)
        # Keep the original balanced implementation as default
        return calculate_ocr_confidence_balanced(image)


def is_page_readable(image, threshold=40):
    """
    Check if a page is readable based on OCR confidence.

    Args:
        image: PIL Image object
        threshold: Minimum OCR confidence threshold (default 40)

    Returns:
        bool: True if page is readable, False otherwise
    """
    confidence, _ = calculate_ocr_confidence(image, mode='superfast')
    return confidence >= threshold