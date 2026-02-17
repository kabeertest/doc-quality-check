"""
Module for checking document confidence based on OCR results.
"""

import cv2
import logging
import pytesseract
import numpy as np
import time
from PIL import Image
from functools import lru_cache
from utils.logger import get_logger

logger = get_logger(__name__)


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


def _extract_confidences_from_ocr_data(ocr_data):
    """
    Extract numeric confidence values from pytesseract `image_to_data` output.

    Args:
        ocr_data: dict returned by `pytesseract.image_to_data`

    Returns:
        list of float: Valid confidence values (0.0 - 100.0)
    """
    confidences = []
    n_boxes = len(ocr_data.get('text', []))
    for i in range(n_boxes):
        text = ocr_data.get('text', [])[i]
        conf_raw = ocr_data.get('conf', [])[i]
        try:
            conf_val = float(conf_raw)
        except Exception:
            continue

        if text and text.strip() and conf_val >= 0:
            confidences.append(conf_val)

    return confidences


def calculate_ocr_confidence_fast(image, lang='eng', verbose: bool = False):
    """
    Fast version of OCR confidence calculation - single PSM mode only with image resizing.

    Args:
        image: PIL Image object
        lang: OCR language (default 'eng', use 'ita' for Italian)

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

    # Single PSM mode for speed with language support
    config_str = f'--psm 6 -l {lang}'

    try:
        # Use PIL Image for pytesseract to avoid channel/depth issues
        pil_for_ocr = resized_image.convert('RGB')
        ocr_data = pytesseract.image_to_data(
            pil_for_ocr,
            output_type=pytesseract.Output.DICT,
            config=config_str
        )

        # Extract numeric confidences safely
        confidences = _extract_confidences_from_ocr_data(ocr_data)
        avg_conf = sum(confidences) / len(confidences) if confidences else 0

        if verbose or any(h.level == logging.DEBUG for h in logger.handlers):
            # Log per-box info for debugging
            try:
                boxes = len(ocr_data.get('text', []))
                logger.debug(f"FAST OCR boxes={boxes}, confidences_count={len(confidences)}")
                for i in range(min(50, boxes)):
                    logger.debug(f"box[{i}] text={repr(ocr_data['text'][i])} conf={ocr_data['conf'][i]}")
            except Exception:
                pass

    except Exception as e:
        # If language not available, try English
        if lang != 'eng':
            try:
                config_str = '--psm 6 -l eng'
                pil_for_ocr = resized_image.convert('RGB')
                ocr_data = pytesseract.image_to_data(
                    pil_for_ocr,
                    output_type=pytesseract.Output.DICT,
                    config=config_str
                )
                confidences = _extract_confidences_from_ocr_data(ocr_data)
                avg_conf = sum(confidences) / len(confidences) if confidences else 0
            except:
                avg_conf = 0
        else:
            avg_conf = 0

    calculation_time = time.time() - start_time
    return avg_conf, calculation_time


def calculate_ocr_confidence_superfast(image, lang='eng', verbose: bool = False):
    """
    Super fast version of OCR confidence calculation - minimal processing.

    Args:
        image: PIL Image object
        lang: OCR language (default 'eng', use 'ita' for Italian)

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

    # Use the simplest PSM mode for speed with language support
    config_str = f'--psm 7 -l {lang}'

    try:
        pil_for_ocr = resized_image.convert('RGB')
        ocr_data = pytesseract.image_to_data(
            pil_for_ocr,
            output_type=pytesseract.Output.DICT,
            config=config_str
        )

        # Extract numeric confidences safely
        confidences = _extract_confidences_from_ocr_data(ocr_data)
        avg_conf = sum(confidences) / len(confidences) if confidences else 0

        if verbose or any(h.level == logging.DEBUG for h in logger.handlers):
            try:
                logger.debug(f"SUPERFAST OCR boxes={len(ocr_data.get('text', []))}, confidences_count={len(confidences)}")
            except Exception:
                pass

    except Exception:
        # If language not available, try English
        if lang != 'eng':
            try:
                config_str = '--psm 7 -l eng'
                pil_for_ocr = resized_image.convert('RGB')
                ocr_data = pytesseract.image_to_data(
                    pil_for_ocr,
                    output_type=pytesseract.Output.DICT,
                    config=config_str
                )
                confidences = _extract_confidences_from_ocr_data(ocr_data)
                avg_conf = sum(confidences) / len(confidences) if confidences else 0
            except:
                avg_conf = 0
        else:
            avg_conf = 0

    calculation_time = time.time() - start_time
    return avg_conf, calculation_time


def calculate_ocr_confidence_balanced(image, lang='eng', verbose: bool = False):
    """
    Balanced version of OCR confidence calculation - moderate accuracy and speed.

    Args:
        image: PIL Image object
        lang: OCR language (default 'eng')
        verbose: If True, log per-box OCR outputs at DEBUG level

    Returns:
        tuple: (confidence_score (float), calculation_time (float))
    """
    start_time = time.time()

    # Resize image to speed up OCR
    resized_image = resize_image_for_ocr(image)

    # Prepare PIL image for pytesseract
    pil_for_ocr = resized_image.convert('RGB')

    # Try single PSM mode first with language support
    config_str = f'--psm 6 -l {lang}'

    try:
        ocr_data = pytesseract.image_to_data(
            pil_for_ocr,
            output_type=pytesseract.Output.DICT,
            config=config_str
        )

        # Extract numeric confidences safely
        confidences = _extract_confidences_from_ocr_data(ocr_data)
        best_conf = sum(confidences) / len(confidences) if confidences else 0

        if verbose or any(h.level == logging.DEBUG for h in logger.handlers):
            try:
                logger.debug(f"BALANCED OCR boxes={len(ocr_data.get('text', []))}, confidences_count={len(confidences)}")
            except Exception:
                pass

        # If confidence is reasonably high, return early (optimization)
        if best_conf >= 15:
            calculation_time = time.time() - start_time
            return best_conf, calculation_time

    except Exception:
        best_conf = 0

    # Convert PIL to OpenCV for enhancement
    img_cv = cv2.cvtColor(np.array(resized_image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    # If confidence is low, try enhancement and one more PSM mode
    if best_conf < 10:
        # Enhance image for better OCR
        blurred = cv2.GaussianBlur(gray, (1, 1), 0)
        enhanced = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

        # Try one more PSM mode only if needed
        psm_mode = '--psm 4'
        config_str = psm_mode + ' -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

        try:
            # Convert enhanced (numpy) image back to PIL for pytesseract
            if isinstance(enhanced, np.ndarray):
                try:
                    pil_enhanced = Image.fromarray(enhanced)
                except Exception:
                    pil_enhanced = Image.fromarray(cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB))
            else:
                pil_enhanced = enhanced

            enhanced_ocr_data = pytesseract.image_to_data(
                pil_enhanced,
                output_type=pytesseract.Output.DICT,
                config=config_str
            )

            enhanced_confidences = _extract_confidences_from_ocr_data(enhanced_ocr_data)
            enhanced_avg_conf = sum(enhanced_confidences) / len(enhanced_confidences) if enhanced_confidences else 0

            # Update best confidence if this is better
            if enhanced_avg_conf > best_conf:
                best_conf = enhanced_avg_conf

        except Exception:
            pass

    calculation_time = time.time() - start_time
    return best_conf, calculation_time


def calculate_ocr_confidence(image, mode='balanced', lang='eng', verbose: bool = False):
    """
    Calculate the OCR confidence score for an image with configurable speed/accuracy.

    Args:
        image: PIL Image object
        mode: 'superfast', 'fast', 'balanced', or 'accurate' (default 'balanced')
        lang: OCR language (default 'eng', use 'ita' for Italian)

    Returns:
        tuple: (confidence_score (float), calculation_time (float)) - Confidence score (0.0 to 100.0) and time taken in seconds
    """
    try:
        if mode == 'superfast':
            return calculate_ocr_confidence_superfast(image, lang, verbose=verbose)
        elif mode == 'fast':
            return calculate_ocr_confidence_fast(image, lang, verbose=verbose)
        elif mode == 'balanced':
            return calculate_ocr_confidence_balanced(image, lang, verbose=verbose)
        else:  # accurate (original behavior)
            # Keep the original balanced implementation as default
            return calculate_ocr_confidence_balanced(image, lang, verbose=verbose)
    except Exception as e:
        # If language not found, fallback to English
        if lang != 'eng':
            print(f"Warning: Language '{lang}' not available, falling back to English")
            if mode == 'superfast':
                return calculate_ocr_confidence_superfast(image, 'eng', verbose=verbose)
            elif mode == 'fast':
                return calculate_ocr_confidence_fast(image, 'eng', verbose=verbose)
            else:
                return calculate_ocr_confidence_balanced(image, 'eng', verbose=verbose)
        else:
            # Even English failed, return 0
            return 0.0, 0.0


def is_page_readable(image, threshold=40):
    """
    Check if a page is readable based on OCR confidence.

    Args:
        image: PIL Image object
        threshold: Minimum OCR confidence threshold (default 40)

    Returns:
        bool: True if page is readable, False otherwise
    """
    confidence, _ = calculate_ocr_confidence(image, mode='fast')
    return confidence >= threshold