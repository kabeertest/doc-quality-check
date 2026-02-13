"""
Module for processing documents and extracting page data.
"""

import fitz  # PyMuPDF
import cv2
from PIL import Image
import numpy as np
import io
import time
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
    
    # Record extraction timing
    start_time = time.time()

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
                
                # Calculate quality metrics
                ink_ratio, _ = calculate_ink_ratio(pil_img)
                ocr_conf, _ = calculate_ocr_confidence(pil_img, mode='superfast')
                text_content, _ = extract_text_content(pil_img, mode='superfast')

                # Store results for this page
                page_extraction_time = time.time() - page_start_time
                results.append({
                    'page': page_num + 1,
                    'ink_ratio': ink_ratio,
                    'ocr_conf': ocr_conf,
                    'image': pil_img,
                    'text_content': text_content,
                    'extraction_time': page_extraction_time
                })
    else:
        # Handle image files (png, jpg, jpeg)
        image_start_time = time.time()
        pil_img = Image.open(io.BytesIO(file_bytes))

        # Calculate quality metrics
        ink_ratio, _ = calculate_ink_ratio(pil_img)
        ocr_conf, _ = calculate_ocr_confidence(pil_img, mode='superfast')
        text_content, _ = extract_text_content(pil_img, mode='superfast')

        # Store results for this image
        image_extraction_time = time.time() - image_start_time
        results.append({
            'page': 1,
            'ink_ratio': ink_ratio,
            'ocr_conf': ocr_conf,
            'image': pil_img,
            'text_content': text_content,
            'extraction_time': image_extraction_time
        })

    total_extraction_time = time.time() - start_time
    
    # Return results with timing info
    return results, total_extraction_time