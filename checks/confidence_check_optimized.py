"""
Optimized confidence check with configurable speed/accuracy tradeoff.
"""

import cv2
import pytesseract
import numpy as np
import time
from PIL import Image


def calculate_ocr_confidence_fast(image):
    """
    Fast version of OCR confidence calculation - single PSM mode only.
    
    Args:
        image: PIL Image object

    Returns:
        tuple: (confidence_score (float), calculation_time (float)) - Confidence score (0.0 to 100.0) and time taken in seconds
    """
    start_time = time.time()
    
    # Convert PIL image to OpenCV format
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # Convert to grayscale for OCR
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    # Single PSM mode for speed
    config_str = '--psm 6 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ '
    
    try:
        ocr_data = pytesseract.image_to_data(
            gray,
            output_type=pytesseract.Output.DICT,
            config=config_str
        )

        # Filter out rows with empty text/whitespace and invalid confidence values
        confidences = []
        for i, text in enumerate(ocr_data['text']):
            # Check if the text is not empty and confidence is valid (0-100)
            if text.strip() and ocr_data['conf'][i] != -1:
                confidences.append(ocr_data['conf'][i])

        # Calculate average confidence
        avg_conf = sum(confidences) / len(confidences) if confidences else 0

    except:
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
    
    # Convert PIL image to OpenCV format
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # Convert to grayscale for OCR
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    # Try single PSM mode first (most common and fastest)
    config_str = '--psm 6 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ '
    
    try:
        ocr_data = pytesseract.image_to_data(
            gray,
            output_type=pytesseract.Output.DICT,
            config=config_str
        )

        # Filter out rows with empty text/whitespace and invalid confidence values
        confidences = []
        for i, text in enumerate(ocr_data['text']):
            # Check if the text is not empty and confidence is valid (0-100)
            if text.strip() and ocr_data['conf'][i] != -1:
                confidences.append(ocr_data['conf'][i])

        # Calculate average confidence
        best_conf = sum(confidences) / len(confidences) if confidences else 0
        
        # If confidence is reasonably high, return early (optimization)
        if best_conf >= 15:  # If we have decent confidence, no need to try other modes
            calculation_time = time.time() - start_time
            return best_conf, calculation_time

    except:
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
        config_str = psm_mode + ' -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ '

        try:
            enhanced_ocr_data = pytesseract.image_to_data(
                enhanced,
                output_type=pytesseract.Output.DICT,
                config=config_str
            )

            enhanced_confidences = []
            for i, text in enumerate(enhanced_ocr_data['text']):
                # Check if the text is not empty and confidence is valid (0-100)
                if text.strip() and enhanced_ocr_data['conf'][i] != -1:
                    enhanced_confidences.append(enhanced_ocr_data['conf'][i])

            enhanced_avg_conf = sum(enhanced_confidences) / len(enhanced_confidences) if enhanced_confidences else 0

            # Update best confidence if this is better
            if enhanced_avg_conf > best_conf:
                best_conf = enhanced_avg_conf

        except:
            pass

    calculation_time = time.time() - start_time
    return best_conf, calculation_time


def calculate_ocr_confidence(image, mode='balanced'):
    """
    Calculate the OCR confidence score for an image with configurable speed/accuracy.

    Args:
        image: PIL Image object
        mode: 'fast', 'balanced', or 'accurate' (default 'balanced')

    Returns:
        tuple: (confidence_score (float), calculation_time (float)) - Confidence score (0.0 to 100.0) and time taken in seconds
    """
    if mode == 'fast':
        return calculate_ocr_confidence_fast(image)
    elif mode == 'balanced':
        return calculate_ocr_confidence_balanced(image)
    else:  # accurate (original behavior)
        return calculate_ocr_confidence_accurate(image)


def calculate_ocr_confidence_accurate(image):
    """
    Original accurate version of OCR confidence calculation - full processing.
    """
    start_time = time.time()
    
    # Convert PIL image to OpenCV format
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # Convert to grayscale for OCR
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    # Try single PSM mode first (most common and fastest)
    config_str = '--psm 6 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ '
    
    try:
        ocr_data = pytesseract.image_to_data(
            gray,
            output_type=pytesseract.Output.DICT,
            config=config_str
        )

        # Filter out rows with empty text/whitespace and invalid confidence values
        confidences = []
        for i, text in enumerate(ocr_data['text']):
            # Check if the text is not empty and confidence is valid (0-100)
            if text.strip() and ocr_data['conf'][i] != -1:
                confidences.append(ocr_data['conf'][i])

        # Calculate average confidence
        best_conf = sum(confidences) / len(confidences) if confidences else 0
        
        # If confidence is reasonably high, return early (optimization)
        if best_conf >= 15:  # If we have decent confidence, no need to try other modes
            calculation_time = time.time() - start_time
            return best_conf, calculation_time

    except:
        best_conf = 0

    # If confidence is low, try enhancement and other PSM modes
    if best_conf < 10:
        # Enhance image for better OCR
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (1, 1), 0)

        # Apply adaptive threshold to enhance text
        enhanced = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

        # Try multiple PSM modes only if needed
        psm_modes = ['--psm 4', '--psm 3']  # Reduced set of modes for performance
        
        for psm_mode in psm_modes:
            config_str = psm_mode + ' -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ '

            try:
                enhanced_ocr_data = pytesseract.image_to_data(
                    enhanced,
                    output_type=pytesseract.Output.DICT,
                    config=config_str
                )

                enhanced_confidences = []
                for i, text in enumerate(enhanced_ocr_data['text']):
                    # Check if the text is not empty and confidence is valid (0-100)
                    if text.strip() and enhanced_ocr_data['conf'][i] != -1:
                        enhanced_confidences.append(enhanced_ocr_data['conf'][i])

                enhanced_avg_conf = sum(enhanced_confidences) / len(enhanced_confidences) if enhanced_confidences else 0

                # Update best confidence if this is better
                if enhanced_avg_conf > best_conf:
                    best_conf = enhanced_avg_conf
                    
                # Early exit if we get good confidence
                if best_conf >= 20:
                    break

            except:
                continue

    calculation_time = time.time() - start_time
    return best_conf, calculation_time