import streamlit as st
import fitz  # PyMuPDF
import cv2
import pytesseract
from PIL import Image
import numpy as np
import pandas as pd
import io
import os

# IMPORTANT: Windows users should install Tesseract from https://github.com/UB-Mannheim/tesseract/wiki
# For Windows, set the path to Tesseract executable if installed in default location
if os.name == 'nt':  # Windows
    # Common installation paths for Tesseract on Windows
    possible_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'C:\Tesseract-OCR\tesseract.exe'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            break
    else:
        # If none of the common paths work, try to find tesseract in PATH
        import shutil
        if not shutil.which('tesseract'):
            print("Warning: Tesseract is not installed or not in PATH. OCR functionality will be disabled.")

# Try to detect if Tesseract is available
def is_tesseract_available():
    try:
        pytesseract.get_tesseract_version()
        return True
    except:
        return False

TESSERACT_AVAILABLE = is_tesseract_available()

@st.cache_data
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
                'image': None      # No image for empty page
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

                # Convert PIL image to OpenCV format
                img_cv = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

                # Convert to grayscale for processing
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

                # Enhance image for better OCR
                # Apply Gaussian blur to reduce noise
                blurred = cv2.GaussianBlur(gray, (1, 1), 0)

                # Apply adaptive threshold to enhance text
                enhanced = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

                # Metric 1: Pixel density (ink ratio)
                # Apply Otsu's thresholding to get binary image
                _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

                # Calculate ink ratio (non-zero pixels / total pixels)
                total_pixels = thresh.shape[0] * thresh.shape[1]
                ink_pixels = cv2.countNonZero(thresh)
                ink_ratio = ink_pixels / total_pixels if total_pixels > 0 else 0

                # Metric 2: OCR confidence
                if TESSERACT_AVAILABLE:
                    try:
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

                        ocr_conf = best_conf

                    except Exception as e:
                        # If OCR fails, set confidence to 0.0 (float)
                        ocr_conf = 0.0
                    finally:
                        # Ensure ocr_conf is always defined
                        if 'ocr_conf' not in locals() and 'ocr_conf' not in globals():
                            ocr_conf = 0.0
                else:
                    # If Tesseract is not available, set OCR confidence to 0.0 (float)
                    ocr_conf = 0.0

                # Store results for this page
                results.append({
                    'page': page_num + 1,
                    'ink_ratio': ink_ratio,
                    'ocr_conf': ocr_conf,
                    'image': pil_img
                })
    else:
        # Handle image files (png, jpg, jpeg)
        pil_img = Image.open(io.BytesIO(file_bytes))
        
        # Convert PIL image to OpenCV format
        img_cv = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        # Convert to grayscale for processing
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

        # Enhance image for better OCR
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (1, 1), 0)

        # Apply adaptive threshold to enhance text
        enhanced = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

        # Metric 1: Pixel density (ink ratio)
        # Apply Otsu's thresholding to get binary image
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Calculate ink ratio (non-zero pixels / total pixels)
        total_pixels = thresh.shape[0] * thresh.shape[1]
        ink_pixels = cv2.countNonZero(thresh)
        ink_ratio = ink_pixels / total_pixels if total_pixels > 0 else 0

        # Metric 2: OCR confidence
        if TESSERACT_AVAILABLE:
            try:
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

                ocr_conf = best_conf

            except Exception as e:
                # If OCR fails, set confidence to 0.0 (float)
                ocr_conf = 0.0
            finally:
                # Ensure ocr_conf is always defined
                if 'ocr_conf' not in locals() and 'ocr_conf' not in globals():
                    ocr_conf = 0.0
        else:
            # If Tesseract is not available, set OCR confidence to 0.0 (float)
            ocr_conf = 0.0
            
        # Store results for this image
        results.append({
            'page': 1,
            'ink_ratio': ink_ratio,
            'ocr_conf': ocr_conf,
            'image': pil_img
        })
    
    return results

def main():
    st.set_page_config(
        page_title="Document Quality Validator",
        page_icon="📄",
        layout="wide"
    )

    st.title("📄 Document Quality /Extract POC ")
    
    # Show Tesseract availability status prominently at the top
    if TESSERACT_AVAILABLE:
        st.success("✅ **Tesseract OCR is available** - Full functionality enabled")
    else:
        st.error("❌ **Tesseract OCR is NOT available** - Readability validation disabled")
    
    st.markdown("""
    Upload PDF or image files to validate their quality based on:
    - **Emptiness**: Is the page blank?
    - **Readability**: Is the text clear enough to read?
    """)

    # Check if Tesseract is available
    if not TESSERACT_AVAILABLE:
        st.warning("""
        ⚠️ **Tesseract OCR is not available.**
        Readability validation will be disabled.
        Please install Tesseract OCR to enable full functionality:

        - **Windows**: Download from https://github.com/UB-Mannheim/tesseract/wiki
        - **macOS**: Install with `brew install tesseract`
        - **Linux**: Install with `sudo apt install tesseract-ocr`

        After installation, make sure to restart this application.
        """)

    # Sidebar configuration
    st.sidebar.header("Configuration")
    
    # File uploader
    uploaded_file = st.sidebar.file_uploader(
        "Upload PDF or Image File",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        help="Supported formats: PDF, PNG, JPG, JPEG"
    )
    
    # Group quality checks under a section
    st.sidebar.subheader("Quality Checks")

    emptiness_check_enabled = st.sidebar.checkbox(
        "Enable Emptiness Check",
        value=True,  # Default enabled
        help="Check this to enable emptiness validation"
    )

    readability_check_enabled = st.sidebar.checkbox(
        "Enable Readability Check",
        value=False,  # Default disabled
        help="Check this to enable readability validation"
    )

    # Sliders for thresholds (only enabled when the corresponding check is enabled)
    emptiness_threshold = st.sidebar.slider(
        "Emptiness Threshold (%)",
        min_value=0.0,
        max_value=10.0,
        value=0.5,
        step=0.1,
        help="If ink ratio is below this percentage, page is marked as empty",
        disabled=not emptiness_check_enabled
    ) / 100  # Convert percentage to decimal

    readability_threshold = st.sidebar.slider(
        "Readability Threshold (Confidence)",
        min_value=0,
        max_value=100,
        value=40,
        step=1,
        help="If OCR confidence is below this value, page is marked as unreadable",
        disabled=not readability_check_enabled
    )

    # Additional document type identification check
    identify_document_type = st.sidebar.checkbox(
        "Identify Document Type",
        value=False,
        help="Check this to enable document type identification"
    )
    
    # Main area
    if uploaded_file is not None:
        # Show progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.text("Processing file...")
        
        try:
            # Extract page data using cached function
            file_bytes = uploaded_file.read()
            page_data = extract_page_data(file_bytes, uploaded_file.name)
            
            # Update progress
            progress_bar.progress(100)
            status_text.text("Processing complete!")
            
            # Prepare results dataframe
            df_data = []
            invalid_pages = []

            for page_info in page_data:
                page_num = page_info['page']
                ink_ratio_pct = page_info['ink_ratio'] * 100
                ocr_conf = page_info['ocr_conf']

                # Determine emptiness and readability status based on thresholds and enabled checks
                is_empty = False
                is_readable = True  # Default to readable when readability check is disabled

                if emptiness_check_enabled and ink_ratio_pct < emptiness_threshold * 100:
                    is_empty = True

                if readability_check_enabled:
                    if TESSERACT_AVAILABLE:
                        is_readable = ocr_conf >= readability_threshold
                    else:
                        is_readable = False  # If Tesseract is not available but readability check is enabled, mark as not readable
                # If readability_check_enabled is False, is_readable remains True (default)

                # Determine overall status based on thresholds
                status = "Valid"
                reason = "OK"

                if is_empty:
                    status = "Invalid"
                    reason = "Empty page"
                    invalid_pages.append((page_info, reason))
                elif not is_readable:
                    status = "Invalid"
                    reason = "Low readability"
                    invalid_pages.append((page_info, reason))

                # Build row dynamically based on enabled checks
                row = {
                    'File': uploaded_file.name,
                    'Page': page_num,
                    'Status': status,
                    'Ink%': f"{ink_ratio_pct:.2f}",
                    'Conf Score': f"{ocr_conf:.2f}"
                }
                
                if emptiness_check_enabled:
                    row['Empty'] = "Yes" if is_empty else "No"
                    
                if readability_check_enabled:
                    row['Readable'] = "Yes" if is_readable else "No"
                    
                # Add reason as the last column
                row['Reason'] = reason
                
                df_data.append(row)
            
            # Create dataframe
            df = pd.DataFrame(df_data)
            
            # Display summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Pages", len(page_data))
            with col2:
                valid_count = len([item for item in df_data if item['Status'] == 'Valid'])
                st.metric("Valid Pages", valid_count)
            with col3:
                flagged_count = len([item for item in df_data if item['Status'] == 'Invalid'])
                st.metric("Flagged/Invalid", flagged_count)
            
            # Display results table
            st.subheader("Validation Results")
            st.dataframe(df.style.apply(
                lambda x: ['background-color: #ffcccc' if v == 'Invalid' else '' for v in x],
                subset=['Status']
            ))

            # Add content extraction functionality
            st.subheader("Content Extraction")
            if st.button("Extract All Pages Content"):
                extracted_content = {}
                for page_info in page_data:
                    page_num = page_info['page']
                    # Extract text content from the page image using OCR
                    if TESSERACT_AVAILABLE:
                        try:
                            # Convert PIL image to OpenCV format
                            img_cv = cv2.cvtColor(np.array(page_info['image']), cv2.COLOR_RGB2BGR)
                            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                            
                            # Extract text using Tesseract
                            text = pytesseract.image_to_string(gray)
                            
                            # Convert to HTML format
                            html_content = f"<h3>Page {page_num}</h3><div>{text.replace(chr(10), '<br>')}</div>"
                            extracted_content[f"page_{page_num}"] = {
                                "text": text,
                                "html": html_content
                            }
                        except Exception as e:
                            extracted_content[f"page_{page_num}"] = {
                                "text": f"Error extracting content: {str(e)}",
                                "html": f"<h3>Page {page_num}</h3><div>Error extracting content: {str(e)}</div>"
                            }
                    else:
                        extracted_content[f"page_{page_num}"] = {
                            "text": "Tesseract not available",
                            "html": f"<h3>Page {page_num}</h3><div>Tesseract not available</div>"
                        }

                # Store extracted content in session state
                st.session_state.extracted_content = extracted_content
                st.success(f"Content extracted for {len(page_data)} pages!")
            
            # Visual inspection of invalid pages
            if invalid_pages:
                st.subheader("Invalid Pages - Visual Inspection")
                
                with st.expander(f"Show {len(invalid_pages)} invalid page(s)", expanded=True):
                    for idx, (page_info, reason) in enumerate(invalid_pages):
                        st.write(f"**Page {page_info['page']} - Reason: {reason}**")
                        
                        # Display image
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.image(
                                page_info['image'],
                                caption=f"Page {page_info['page']} - Ink Ratio: {page_info['ink_ratio']*100:.2f}%, OCR Confidence: {page_info['ocr_conf']:.2f}",
                                use_column_width=True
                            )
                        with col2:
                            st.write(f"**Metrics:**")
                            st.write(f"- Ink Ratio: {page_info['ink_ratio']*100:.2f}%")
                            st.write(f"- OCR Confidence: {page_info['ocr_conf']:.2f}")
                            st.write(f"- Status: Invalid")
                            st.write(f"- Reason: {reason}")
                        
                        # Add separator between pages
                        if idx < len(invalid_pages) - 1:
                            st.divider()
            else:
                st.success("✅ All pages passed validation!")
                
        except Exception as e:
            st.error(f"An error occurred while processing the file: {str(e)}")
            st.info("Please check that you have properly installed Tesseract OCR and set the path correctly.")
    else:
        st.info("👆 Please upload a PDF or image file to begin validation.")

if __name__ == "__main__":
    main()