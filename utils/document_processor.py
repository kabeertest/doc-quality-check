"""
Module for processing documents and extracting page data.
"""

import fitz  # PyMuPDF
import cv2
from PIL import Image
import numpy as np
import io
import time
import re
import json
import os
from checks.clarity_check import calculate_ink_ratio
from checks.confidence_check import calculate_ocr_confidence
from utils.content_extraction import extract_text_content


def load_ocr_settings():
    """Load OCR settings from config.json"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config.get('ocr_settings', {
            'primary_language': 'ita',
            'fallback_language': 'eng',
            'auto_detect_language': True
        })
    except:
        # Default settings if config.json not found
        return {
            'primary_language': 'ita',
            'fallback_language': 'eng',
            'auto_detect_language': True
        }


def detect_document_language(text_content, primary_language='ita'):
    """
    Detect document language based on text content.

    Uses keyword matching with support for multiple languages.
    Filters out screenshot artifacts before detection.
    If auto-detection is disabled, returns the primary language.

    Args:
        text_content: Extracted text from the document
        primary_language: Default language to use if no indicators found (default 'ita')

    Returns:
        str: Language code ('ita' for Italian, 'eng' for English, etc.)
    """
    if not text_content:
        return primary_language

    # Filter out artifacts before language detection
    from checks.confidence_check import ARTIFACT_PATTERNS
    filtered_text = text_content
    
    for pattern in ARTIFACT_PATTERNS:
        filtered_text = pattern.sub('', filtered_text)
    
    filtered_text = filtered_text.strip()
    
    if not filtered_text:
        # If all text was artifacts, use primary language
        return primary_language

    # Load language detection keywords from config
    ocr_settings = load_ocr_settings()
    lang_keywords = ocr_settings.get('language_detection_keywords', {})

    text_lower = filtered_text.lower()

    # Count keyword matches for each language
    lang_scores = {}
    for lang, keywords in lang_keywords.items():
        count = sum(1 for keyword in keywords if keyword in text_lower)
        if count > 0:
            lang_scores[lang] = count

    # If we found matches, return the language with highest score
    if lang_scores:
        best_lang = max(lang_scores, key=lang_scores.get)
        return best_lang

    # No matches found - return primary language
    return primary_language


def extract_page_data(file_bytes, file_name, primary_language=None, auto_detect=None):
    """
    Extracts page data from uploaded file (PDF or image) and calculates quality metrics.

    Args:
        file_bytes: Bytes of the uploaded file
        file_name: Name of the uploaded file
        primary_language: Primary OCR language (default from config: 'ita')
        auto_detect: If True, auto-detect language from content (default from config: True)

    Returns:
        List of dictionaries containing page data with quality metrics
    """
    results = []

    # Record extraction timing
    start_time = time.time()

    # Load OCR settings from config
    ocr_settings = load_ocr_settings()
    
    # Use provided values or fall back to config
    if primary_language is None:
        primary_language = ocr_settings.get('primary_language', 'ita')
    if auto_detect is None:
        auto_detect = ocr_settings.get('auto_detect_language', True)

    # Determine if file is PDF or image
    if file_name.lower().endswith('.pdf'):
        # Open PDF with PyMuPDF
        doc = fitz.open(stream=file_bytes, filetype="pdf")

        # Check if the PDF has any pages
        if len(doc) == 0:
            # Handle empty PDF - create a default result with zero ink ratio and zero confidence
            results.append({
                'page': 1,
                'ink_ratio': 0.0,  # No content means zero ink ratio
                'ocr_conf': 0.0,   # No content means zero OCR confidence
                'image': None,      # No image for empty page
                'text_content': '',  # No text for empty page
                'extraction_time': 0.0  # No extraction time for empty PDF
            })
        else:
            # Process each page
            for page_num in range(len(doc)):
                page_start_time = time.time()

                page = doc.load_page(page_num)

                # Render page at 2x resolution for better accuracy (approx 150-300 DPI)
                mat = fitz.Matrix(2, 2)
                pix = page.get_pixmap(matrix=mat)

                # Convert pixmap to image
                img_data = pix.tobytes("png")
                pil_img = Image.open(io.BytesIO(img_data))

                # First pass: Extract text to detect language
                text_content, _ = extract_text_content(pil_img, mode='fast')

                # Detect document language
                if auto_detect:
                    doc_lang = detect_document_language(text_content, primary_language)
                else:
                    doc_lang = primary_language

                # Calculate quality metrics with detected language
                ink_ratio, _ = calculate_ink_ratio(pil_img)
                ocr_conf, _ = calculate_ocr_confidence(pil_img, mode='fast', lang=doc_lang)

                # Store results for this page
                page_extraction_time = time.time() - page_start_time
                results.append({
                    'page': page_num + 1,
                    'ink_ratio': ink_ratio,
                    'ocr_conf': ocr_conf,
                    'image': pil_img,
                    'text_content': text_content,
                    'detected_language': doc_lang,
                    'extraction_time': page_extraction_time
                })
    else:
        # Handle image files (png, jpg, jpeg)
        image_start_time = time.time()
        pil_img = Image.open(io.BytesIO(file_bytes))

        # First pass: Extract text to detect language
        text_content, _ = extract_text_content(pil_img, mode='fast')

        # Detect document language
        if auto_detect:
            doc_lang = detect_document_language(text_content, primary_language)
        else:
            doc_lang = primary_language

        # Calculate quality metrics with detected language
        ink_ratio, _ = calculate_ink_ratio(pil_img)
        ocr_conf, _ = calculate_ocr_confidence(pil_img, mode='fast', lang=doc_lang)

        # Store results for this image
        image_extraction_time = time.time() - image_start_time
        results.append({
            'page': 1,
            'ink_ratio': ink_ratio,
            'ocr_conf': ocr_conf,
            'image': pil_img,
            'text_content': text_content,
            'detected_language': doc_lang,
            'extraction_time': image_extraction_time
        })

    total_extraction_time = time.time() - start_time
    
    # Return results with timing info
    return results, total_extraction_time