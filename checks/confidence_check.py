"""
Module for checking document confidence based on OCR results.
"""

import cv2
import logging
import pytesseract
import numpy as np
import time
import re
from PIL import Image
from utils.logger import get_logger
from utils.content_extraction import resize_image_for_ocr

logger = get_logger(__name__)

# Artifact patterns that indicate screenshot noise (not document content)
ARTIFACT_PATTERNS = [
    re.compile(r'file:///[A-Za-z]:/[^\\s]+', re.IGNORECASE),  # file:///C:/Users/...
    re.compile(r'https?://[^\\s]+', re.IGNORECASE),  # URLs
    re.compile(r'\\d{1,2}/\\d{1,2}/\\d{2,4},?\\s*\\d{1,2}:\\d{2}', re.IGNORECASE),  # Timestamps
    re.compile(r'[A-Za-z0-9_-]+\\.(png|jpg|jpeg)\\s*\\(\\d+x\\d+\\)', re.IGNORECASE),  # Image files with dimensions
    re.compile(r'storyblok|wikimedia|upload\\.', re.IGNORECASE),  # Web artifacts
]


def _extract_confidences_from_ocr_data(ocr_data):
    """
    Extract numeric confidence values from pytesseract `image_to_data` output.

    This function returns confidence values for ALL boxes.
    Boxes with text use their actual confidence value.
    Empty boxes get 0.0 confidence.

    Args:
        ocr_data: dict returned by `pytesseract.image_to_data`

    Returns:
        list of float: Confidence values (0.0 - 100.0) for ALL boxes.
    """
    confidences = []
    n_boxes = len(ocr_data.get('text', []))
    for i in range(n_boxes):
        text = ocr_data.get('text', [])[i]
        conf_raw = ocr_data.get('conf', [])[i]

        # Try to parse confidence value
        try:
            conf_val = float(conf_raw)
        except (ValueError, TypeError):
            # Invalid confidence value - treat as 0
            confidences.append(0.0)
            continue

        # Check if confidence is valid (non-negative)
        if conf_val < 0:
            confidences.append(0.0)
            continue

        # If box has text, use its confidence; otherwise, count as 0
        if text and text.strip():
            confidences.append(conf_val)
        else:
            confidences.append(0.0)

    return confidences


def _extract_confidences_weighted(ocr_data):
    """
    Extract confidence values with weighted averaging for better accuracy.

    Calculates both overall average and text-weighted average.
    For documents with sparse text (like IDs), text-weighted is more accurate.

    Args:
        ocr_data: dict from pytesseract.image_to_data

    Returns:
        tuple: (overall_conf, text_conf, text_box_count, total_box_count)
    """
    all_confidences = []
    text_confidences = []
    n_boxes = len(ocr_data.get('text', []))

    for i in range(n_boxes):
        text = ocr_data.get('text', [])[i]
        conf_raw = ocr_data.get('conf', [])[i]

        try:
            conf_val = float(conf_raw)
        except (ValueError, TypeError):
            conf_val = 0.0

        if conf_val < 0:
            conf_val = 0.0

        # Include in overall average (all boxes)
        if text and text.strip():
            all_confidences.append(conf_val)
            text_confidences.append(conf_val)
        else:
            # Empty boxes contribute 0 to overall average
            all_confidences.append(0.0)

    overall_conf = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
    text_conf = sum(text_confidences) / len(text_confidences) if text_confidences else 0.0

    return overall_conf, text_conf, len(text_confidences), n_boxes


def _extract_confidences_filtered(ocr_data):
    """
    Extract confidence values excluding artifact/noise text boxes.
    
    Filters out:
    - File paths (file:///C:/Users/...)
    - URLs (https://...)
    - Timestamps (2/17/26, 9:23 AM)
    - Image filenames with dimensions
    
    This gives confidence scores based on actual document content only.
    
    Args:
        ocr_data: dict from pytesseract.image_to_data
    
    Returns:
        tuple: (filtered_conf, total_conf, filtered_box_count, total_box_count, has_artifacts)
    """
    all_confidences = []
    text_confidences = []
    filtered_confidences = []
    n_boxes = len(ocr_data.get('text', []))
    artifact_count = 0

    for i in range(n_boxes):
        text = ocr_data.get('text', [])[i]
        conf_raw = ocr_data.get('conf', [])[i]

        try:
            conf_val = float(conf_raw)
        except (ValueError, TypeError):
            conf_val = 0.0

        if conf_val < 0:
            conf_val = 0.0

        # Include in total average (all boxes with text)
        if text and text.strip():
            all_confidences.append(conf_val)
            
            # Check if this is an artifact
            is_artifact = False
            for pattern in ARTIFACT_PATTERNS:
                if pattern.search(text):
                    is_artifact = True
                    artifact_count += 1
                    break
            
            # Only include non-artifact text in filtered confidence
            if not is_artifact:
                filtered_confidences.append(conf_val)
                text_confidences.append(conf_val)
            else:
                # Log artifact for debugging
                logger.debug(f"Filtered artifact: '{text}' (conf: {conf_val})")

    # Calculate averages
    total_conf = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
    filtered_conf = sum(filtered_confidences) / len(filtered_confidences) if filtered_confidences else 0.0
    text_conf = sum(text_confidences) / len(text_confidences) if text_confidences else 0.0
    
    has_artifacts = artifact_count > 0

    return filtered_conf, total_conf, text_conf, len(filtered_confidences), n_boxes, has_artifacts


def calculate_ocr_confidence_fast(image, lang='eng', verbose: bool = False):
    """
    Fast version of OCR confidence calculation - uses filtered confidence to exclude artifacts.

    Filters out screenshot artifacts (file paths, URLs, timestamps) from confidence calculation.
    This gives more accurate scores based on actual document content.
    
    NOTE: Does NOT resize the image to preserve text quality for confidence calculation.

    Args:
        image: PIL Image object
        lang: OCR language (default 'eng', use 'ita' for Italian)
        verbose: Enable debug logging

    Returns:
        tuple: (confidence_score (float), calculation_time (float))
    """
    start_time = time.time()

    # DO NOT resize - use full resolution for accurate confidence calculation
    # Resize destroys text quality for large documents
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # Convert to grayscale for OCR
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    # Single PSM mode for speed with language support
    config_str = f'--psm 6 -l {lang}'

    try:
        # Use PIL Image for pytesseract to avoid channel/depth issues
        pil_for_ocr = image.convert('RGB')
        ocr_data = pytesseract.image_to_data(
            pil_for_ocr,
            output_type=pytesseract.Output.DICT,
            config=config_str
        )

        # Extract filtered confidences (excludes artifacts)
        filtered_conf, total_conf, text_conf, filtered_boxes, total_boxes, has_artifacts = _extract_confidences_filtered(ocr_data)

        # For sparse text documents (like IDs), use weighted confidence
        # This gives more weight to actual text regions
        if filtered_boxes > 0 and filtered_boxes < total_boxes * 0.5:
            # Sparse text: 70% text confidence + 30% filtered confidence
            avg_conf = 0.7 * text_conf + 0.3 * filtered_conf
        else:
            # Normal document: use filtered confidence (artifacts excluded)
            avg_conf = filtered_conf

        if verbose or any(h.level == logging.DEBUG for h in logger.handlers):
            # Log per-box info for debugging
            try:
                boxes = len(ocr_data.get('text', []))
                logger.debug(f"FAST OCR boxes={boxes}, filtered_boxes={filtered_boxes}/{total_boxes}, has_artifacts={has_artifacts}, total={total_conf:.2f}, filtered={filtered_conf:.2f}, final={avg_conf:.2f}")
                for i in range(min(50, boxes)):
                    logger.debug(f"box[{i}] text={repr(ocr_data['text'][i])} conf={ocr_data['conf'][i]}")
            except Exception:
                pass

    except Exception as e:
        # If language not available, try English
        if lang != 'eng':
            # Silently fall back to English if specified language fails
            try:
                config_str = '--psm 6 -l eng'
                pil_for_ocr = image.convert('RGB')
                ocr_data = pytesseract.image_to_data(
                    pil_for_ocr,
                    output_type=pytesseract.Output.DICT,
                    config=config_str
                )
                filtered_conf, total_conf, text_conf, filtered_boxes, total_boxes, has_artifacts = _extract_confidences_filtered(ocr_data)
                if filtered_boxes > 0 and filtered_boxes < total_boxes * 0.5:
                    avg_conf = 0.7 * text_conf + 0.3 * filtered_conf
                else:
                    avg_conf = filtered_conf
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

