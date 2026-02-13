import streamlit as st
import pytesseract
from PIL import Image
import numpy as np
import pandas as pd
import os
import cv2
import time
from utils.document_processor import extract_page_data
from utils.content_extraction import display_content_in_sidebar, extract_text_content
from checks.clarity_check import calculate_ink_ratio
from checks.confidence_check import calculate_ocr_confidence

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
        "Auto Identify Document Type -Discuss with Gusseppe",
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
            page_data, total_extraction_time = extract_page_data(file_bytes, uploaded_file.name)
            
            # Update progress
            progress_bar.progress(100)
            status_text.text("Processing complete!")
            
            # Prepare results dataframe
            df_data = []
            invalid_pages = []

            # Calculate total clarity and confidence times
            total_clarity_time = 0
            total_confidence_time = 0
            
            for page_info in page_data:
                page_num = page_info['page']
                
                # Calculate clarity metric with timing
                ink_ratio, clarity_time = calculate_ink_ratio(page_info['image'])
                total_clarity_time += clarity_time
                ink_ratio_pct = ink_ratio * 100
                
                # Calculate confidence metric with timing
                ocr_conf, confidence_time = calculate_ocr_confidence(page_info['image'])
                total_confidence_time += confidence_time
                
                # Get text content with timing
                text_content, content_extraction_time = extract_text_content(page_info['image'])
                page_info['text_content'] = text_content

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

            # Display timing metrics
            st.subheader("Performance Metrics")
            timing_col1, timing_col2, timing_col3 = st.columns(3)
            with timing_col1:
                st.metric("File Upload & Extraction", f"{total_extraction_time:.2f}s")
            with timing_col2:
                st.metric("Clarity Calculation", f"{total_clarity_time:.2f}s")
            with timing_col3:
                st.metric("Readability Calculation", f"{total_confidence_time:.2f}s")

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
                            
                            # Add Read Content button for each page
                            if st.button(f"Read Content (Page {page_info['page']})", key=f"read_content_{page_info['page']}_invalid"):
                                # Extract text content from the page image using OCR
                                if TESSERACT_AVAILABLE:
                                    try:
                                        # Convert PIL image to OpenCV format
                                        img_cv = cv2.cvtColor(np.array(page_info['image']), cv2.COLOR_RGB2BGR)
                                        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                                        
                                        # Extract text using Tesseract
                                        text = pytesseract.image_to_string(gray)
                                        
                                        # Convert to HTML format
                                        html_content = f"<h3>Page {page_info['page']}</h3><div>{text.replace(chr(10), '<br>')}</div>"
                                        
                                        # Store in session state
                                        if 'page_content' not in st.session_state:
                                            st.session_state.page_content = {}
                                        st.session_state.page_content[f"page_{page_info['page']}"] = {
                                            "text": text,
                                            "html": html_content
                                        }
                                        
                                        # Store current page in session state to show in sidebar
                                        st.session_state.current_page = f"page_{page_info['page']}"
                                        st.session_state.show_sidebar = True
                                    except Exception as e:
                                        st.error(f"Error extracting content for Page {page_info['page']}: {str(e)}")
                                else:
                                    st.warning(f"Tesseract not available to extract content for Page {page_info['page']}")
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

            # Add Read Content buttons for valid pages as well
            if 'df' in locals() and len(df) > 0:
                valid_pages_df = df[df['Status'] == 'Valid']
                if not valid_pages_df.empty:
                    st.subheader("Valid Pages - Content Extraction")
                    for idx, row in valid_pages_df.iterrows():
                        page_num = int(row['Page'])
                        
                        # Find the corresponding page_info
                        page_info = next((p for p in page_data if p['page'] == page_num), None)
                        if page_info:
                            cols = st.columns([3, 1, 1])  # Image, Info, Buttons
                            with cols[0]:
                                st.image(
                                    page_info['image'],
                                    caption=f"Page {page_num} - Ink Ratio: {page_info['ink_ratio']*100:.2f}%, OCR Confidence: {page_info['ocr_conf']:.2f}",
                                    use_column_width=True
                                )
                            with cols[1]:
                                st.write(f"**Metrics:**")
                                st.write(f"- Ink Ratio: {page_info['ink_ratio']*100:.2f}%")
                                st.write(f"- OCR Confidence: {page_info['ocr_conf']:.2f}")
                                st.write(f"- Status: Valid")
                            with cols[2]:
                                if st.button(f"Read Content (Page {page_num})", key=f"read_content_{page_num}_valid"):
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
                                            
                                            # Store in session state
                                            if 'page_content' not in st.session_state:
                                                st.session_state.page_content = {}
                                            st.session_state.page_content[f"page_{page_num}"] = {
                                                "text": text,
                                                "html": html_content
                                            }
                                            
                                            # Store current page in session state to show in sidebar
                                            st.session_state.current_page = f"page_{page_num}"
                                            st.session_state.show_sidebar = True
                                        except Exception as e:
                                            st.error(f"Error extracting content for Page {page_num}: {str(e)}")
                                    else:
                                        st.warning(f"Tesseract not available to extract content for Page {page_num}")

                            # Add separator between pages
                            if idx < len(valid_pages_df) - 1:
                                st.divider()

            # Extract Data as JSON button
            if st.button("Extract Data as JSON"):
                if 'extracted_content' in st.session_state:
                    import json
                    # Convert the extracted content to JSON
                    json_data = json.dumps(st.session_state.extracted_content, indent=2)
                    
                    # Provide download button for JSON
                    st.download_button(
                        label="Download JSON Data",
                        data=json_data,
                        file_name="extracted_content.json",
                        mime="application/json"
                    )
                    st.success("JSON data ready for download!")
                else:
                    st.warning("Please extract content first using 'Extract All Pages Content' button.")

            # Sidebar for displaying content when a Read Content button is clicked
            if 'show_sidebar' in st.session_state and st.session_state.show_sidebar and 'current_page' in st.session_state:
                from utils.content_extraction import display_content_in_sidebar
                page_key = st.session_state.current_page
                content = st.session_state.page_content[page_key] if 'page_content' in st.session_state and page_key in st.session_state.page_content else {}
                if content:
                    display_content_in_sidebar(page_key, content)
                
        except Exception as e:
            st.error(f"An error occurred while processing the file: {str(e)}")
            st.info("Please check that you have properly installed Tesseract OCR and set the path correctly.")
    else:
        st.info("👆 Please upload a PDF or image file to begin validation.")

if __name__ == "__main__":
    main()