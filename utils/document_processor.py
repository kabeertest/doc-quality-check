"""
Module for processing documents and extracting page data.
"""

import fitz  # PyMuPDF
import cv2
from PIL import Image
import numpy as np
import io
from checks.clarity_check import calculate_ink_ratio
from checks.confidence_check import calculate_ocr_confidence
from utils.content_extraction import extract_text_content


def extract_page_data(file_bytes, file_name):
    """
    Extracts page data from uploaded file (PDF or image) and calculates quality metrics.

    Args:
        file_bytes: Bytes of the uploaded file
        file_name: Name of the uploaded file

    Returns:
        List of dictionaries containing page data with quality metrics
    """
    results = []

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
                'text_content': ''  # No text for empty page
            })
        else:
            # Process each page
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)

                # Render page at 2x resolution for better accuracy (approx 150-300 DPI)
                mat = fitz.Matrix(2, 2)
                pix = page.get_pixmap(matrix=mat)

                # Convert pixmap to image
                img_data = pix.tobytes("png")
                pil_img = Image.open(io.BytesIO(img_data))

                # Calculate quality metrics
                ink_ratio = calculate_ink_ratio(pil_img)
                ocr_conf = calculate_ocr_confidence(pil_img)
                text_content = extract_text_content(pil_img)

                # Store results for this page
                results.append({
                    'page': page_num + 1,
                    'ink_ratio': ink_ratio,
                    'ocr_conf': ocr_conf,
                    'image': pil_img,
                    'text_content': text_content
                })
    else:
        # Handle image files (png, jpg, jpeg)
        pil_img = Image.open(io.BytesIO(file_bytes))

        # Calculate quality metrics
        ink_ratio = calculate_ink_ratio(pil_img)
        ocr_conf = calculate_ocr_confidence(pil_img)
        text_content = extract_text_content(pil_img)

        # Store results for this image
        results.append({
            'page': 1,
            'ink_ratio': ink_ratio,
            'ocr_conf': ocr_conf,
            'image': pil_img,
            'text_content': text_content
        })

    return results