"""
Module for calculating quality metrics for document pages.
"""

import cv2
import pytesseract
import numpy as np
from PIL import Image
import io
import fitz  # PyMuPDF


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


def calculate_ocr_confidence(image):
    """
    Calculate the OCR confidence score for an image.
    
    Args:
        image: PIL Image object
    
    Returns:
        float: Average OCR confidence score (0.0 to 100.0)
    """
    # Convert PIL image to OpenCV format
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Convert to grayscale for OCR
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    
    # Enhance image for better OCR
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (1, 1), 0)
    
    # Apply adaptive threshold to enhance text
    enhanced = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    # Try multiple PSM modes to improve text detection
    psm_modes = ['--psm 6', '--psm 4', '--psm 3']  # Various modes for different text layouts
    best_conf = 0
    
    for psm_mode in psm_modes:
        config_str = psm_mode + ' -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ '
        
        # Try OCR on original image first
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
            
            # Update best confidence if this is better
            if avg_conf > best_conf:
                best_conf = avg_conf
                
        except:
            continue
    
    # If still low confidence, try with enhanced image
    if best_conf < 10:
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
                    
            except:
                continue
    
    return best_conf


def extract_text_content(image):
    """
    Extract text content from an image using OCR.
    
    Args:
        image: PIL Image object
    
    Returns:
        str: Extracted text content
    """
    # Convert PIL image to OpenCV format
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Convert to grayscale for OCR
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    
    # Extract text using Tesseract
    text = pytesseract.image_to_string(gray)
    
    return text