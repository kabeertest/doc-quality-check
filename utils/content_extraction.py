"""
Module for content extraction and text processing functionality.
"""

import re
import json
import streamlit as st
import cv2
import pytesseract
import numpy as np
import time
from PIL import Image


def resize_image_for_ocr(image, max_size=(400, 400)):
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


def extract_text_content_superfast(image):
    """
    Super fast version of text content extraction using OCR.

    Args:
        image: PIL Image object

    Returns:
        tuple: (text_content (str), extraction_time (float)) - Extracted text and time taken in seconds
    """
    start_time = time.time()

    # Resize image to speed up OCR
    resized_image = resize_image_for_ocr(image)
    
    # Convert PIL image to OpenCV format
    img_cv = cv2.cvtColor(np.array(resized_image), cv2.COLOR_RGB2BGR)

    # Convert to grayscale for OCR
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    # Extract text using Tesseract with fastest PSM mode
    pil_for_ocr = resized_image.convert('RGB')
    text = pytesseract.image_to_string(pil_for_ocr, config='--psm 7')  # Single text line mode

    extraction_time = time.time() - start_time

    return text, extraction_time


def extract_text_content_fast(image):
    """
    Fast version of text content extraction using OCR.

    Args:
        image: PIL Image object

    Returns:
        tuple: (text_content (str), extraction_time (float)) - Extracted text and time taken in seconds
    """
    start_time = time.time()

    # Convert PIL image to OpenCV format
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # Convert to grayscale for OCR
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    # Extract text using Tesseract with a more appropriate PSM for multi-line content
    pil_for_ocr = image.convert('RGB')
    text = pytesseract.image_to_string(pil_for_ocr, config='--psm 6')  # Assume a single uniform block of text

    extraction_time = time.time() - start_time

    return text, extraction_time


def extract_text_content(image, mode='fast'):
    """
    Extract text content from an image using OCR with configurable speed.

    Args:
        image: PIL Image object
        mode: 'superfast', 'fast' or 'balanced' (default 'fast')

    Returns:
        tuple: (text_content (str), extraction_time (float)) - Extracted text and time taken in seconds
    """
    if mode == 'superfast':
        return extract_text_content_superfast(image)
    elif mode == 'fast':
        return extract_text_content_fast(image)
    else:  # balanced
        return extract_text_content_balanced(image)


def extract_text_content_balanced(image):
    """
    Balanced version of text content extraction using OCR.

    Args:
        image: PIL Image object

    Returns:
        tuple: (text_content (str), extraction_time (float)) - Extracted text and time taken in seconds
    """
    start_time = time.time()
    
    # Convert PIL image to OpenCV format
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # Convert to grayscale for OCR
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    # Extract text using Tesseract with optimized PSM mode
    pil_for_ocr = image.convert('RGB')
    text = pytesseract.image_to_string(pil_for_ocr, config='--psm 6')
    
    extraction_time = time.time() - start_time

    return text, extraction_time


def extract_json_keys(text):
    """
    Extract potential key-value pairs from text content.

    Args:
        text (str): Input text to analyze

    Returns:
        dict: Dictionary of extracted key-value pairs
    """
    # Look for potential key-value patterns in the text
    lines = text.split('\n')
    potential_keys = {}

    for line in lines:
        # Look for patterns like "Key: Value" or "Key - Value"
        colon_pattern = r'^\s*([^:]+):\s*(.+)$'
        dash_pattern = r'^\s*([^-\n]+)-\s*(.+)$'

        colon_match = re.match(colon_pattern, line)
        if colon_match:
            key = colon_match.group(1).strip()
            value = colon_match.group(2).strip()
            potential_keys[key] = value
        else:
            dash_match = re.match(dash_pattern, line)
            if dash_match:
                key = dash_match.group(1).strip()
                value = dash_match.group(2).strip()
                potential_keys[key] = value

    # If no patterns matched, just split by lines and use as key-value pairs
    if not potential_keys and text.strip():
        # Basic approach: treat each non-empty line as a potential key
        for i, line in enumerate(lines):
            line = line.strip()
            if line:
                potential_keys[f"line_{i+1}"] = line

    return potential_keys


def display_content_in_sidebar(page_key, content):
    """
    Display content in the sidebar with extraction options.

    Args:
        page_key (str): Key identifying the page
        content (dict): Content to display
    """
    with st.sidebar:
        st.subheader(f"Content for {page_key}")

        # Display the HTML content
        st.markdown(content['html'], unsafe_allow_html=True)

        # Add download button for the content
        st.download_button(
            label=f"Download Content ({page_key})",
            data=content['text'],
            file_name=f"{page_key}_content.txt",
            mime="text/plain"
        )

        # Add button to extract JSON keys
        if st.button("Extract JSON Keys"):
            # Extract potential keys from the text
            potential_keys = extract_json_keys(content['text'])

            # Display the extracted keys
            if potential_keys:
                st.subheader("Extracted JSON Keys:")
                for key, value in potential_keys.items():
                    st.write(f"**{key}**: {value}")

                # Provide download button for JSON
                json_data = json.dumps(potential_keys, indent=2)
                st.download_button(
                    label="Download JSON Keys",
                    data=json_data,
                    file_name=f"{page_key}_keys.json",
                    mime="application/json"
                )
            else:
                st.info("No key-value patterns detected in the content.")

        # Close sidebar button
        if st.button("Close Sidebar"):
            st.session_state.show_sidebar = False
            st.rerun()