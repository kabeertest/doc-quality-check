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

    tesseract_found = False
    for path in possible_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            print(f"✓ Tesseract path set to: {path}")
            tesseract_found = True
            break
    
    if not tesseract_found:
        # If none of the common paths work, try to find tesseract in PATH
        import shutil
        tesseract_path = shutil.which('tesseract')
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            print(f"✓ Tesseract found in PATH: {tesseract_path}")
            tesseract_found = True
        else:
            print("✗ Warning: Tesseract is not installed or not in PATH. OCR functionality will be disabled.")

def main():
    st.set_page_config(
        page_title="Document Quality Validator",
        page_icon="📄",
        layout="wide"
    )
    
    # IMPORTANT: Ensure Tesseract path is set BEFORE checking languages
    if os.name == 'nt':  # Windows
        # Set both tesseract executable path and tessdata path
        tess_paths = [
            r'C:\Users\ahamed.kabeer\AppData\Local\Programs\Tesseract-OCR',
            r'C:\Program Files\Tesseract-OCR',
            r'C:\Program Files (x86)\Tesseract-OCR',
            r'C:\Tesseract-OCR'
        ]
        
        for tess_path in tess_paths:
            tesseract_exe = os.path.join(tess_path, 'tesseract.exe')
            tessdata_path = os.path.join(tess_path, 'tessdata')
            
            if os.path.exists(tesseract_exe):
                pytesseract.pytesseract.tesseract_cmd = tesseract_exe
                
                # Set TESSDATA_PREFIX environment variable if tessdata exists
                if os.path.exists(tessdata_path):
                    os.environ['TESSDATA_PREFIX'] = tessdata_path
                    print(f"✓ Tesseract path: {tesseract_exe}")
                    print(f"✓ Tessdata path: {tessdata_path}")
                break
        else:
            import shutil
            tesseract_path = shutil.which('tesseract')
            if tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                print(f"✓ Tesseract from PATH: {tesseract_path}")

    # Check Tesseract availability and languages (after path is set)
    def is_tesseract_available():
        try:
            version = pytesseract.get_tesseract_version()
            print(f"✓ Tesseract version: {version}")
            return True
        except Exception as e:
            print(f"✗ Tesseract not available: {e}")
            return False

    def get_tesseract_languages():
        """Get list of installed Tesseract language packs."""
        try:
            langs = pytesseract.get_languages(config='')
            print(f"✓ Tesseract languages ({len(langs)} total): {langs[:10]}...")  # Show first 10
            return langs
        except Exception as e:
            print(f"✗ Error getting languages: {e}")
            import traceback
            traceback.print_exc()
            return []

    print("\n=== Tesseract Configuration Check ===")
    TESSERACT_AVAILABLE = is_tesseract_available()
    TESSERACT_LANGS = get_tesseract_languages() if TESSERACT_AVAILABLE else []
    ITALIAN_SUPPORTED = 'ita' in TESSERACT_LANGS or 'ital' in TESSERACT_LANGS
    
    print(f"=== Italian Support: {ITALIAN_SUPPORTED} ===")
    print(f"=== Languages containing 'ita': {[l for l in TESSERACT_LANGS if 'ita' in l]} ===\n")

    # Helper function: get color based on confidence level
    def get_confidence_color(confidence: float) -> tuple:
        """Return RGB color based on confidence level."""
        conf = float(confidence)
        if conf >= 80:
            return (0, 200, 0)  # Green - high confidence
        elif conf >= 50:
            return (255, 165, 0)  # Amber - medium confidence
        else:
            return (255, 50, 50)  # Red - low confidence

    st.title("📄 Document Quality /Extract POC ")
    
    # Initialize variables at the start of the function
    invalid_pages = []
    df = pd.DataFrame()  # Initialize empty DataFrame
    
    # Show Tesseract availability status prominently at the top
    if TESSERACT_AVAILABLE:
        st.success("✅ **Tesseract OCR is available** - Full functionality enabled")
        
        # Show installed languages
        if TESSERACT_LANGS:
            lang_cols = st.columns([2, 1])
            with lang_cols[1]:
                if ITALIAN_SUPPORTED:
                    st.success("🇮🇹 **Italian Supported**")
                else:
                    st.warning("⚠️ Italian not installed")
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

        For Italian language support:
        - **Windows**: Select Italian language pack during installation
        - **macOS**: `brew install tesseract-lang`
        - **Linux**: `sudo apt install tesseract-ocr-ita`

        After installation, make sure to restart this application.
        """)
    elif not ITALIAN_SUPPORTED:
        st.info("""
        ℹ️ **Italian language pack not detected.**
        Italian document OCR may have reduced accuracy.
        
        To add Italian support:
        - **Windows**: Reinstall Tesseract and select Italian language pack
        - **macOS**: Run `brew install tesseract-lang`
        - **Linux**: Run `sudo apt install tesseract-ocr-ita`
        """)

    # Sidebar configuration
    st.sidebar.header("Configuration")

    # UX toggle: hide unknown detections by default to reduce confusion
    show_unknown_segments = st.sidebar.checkbox(
        "Show unknown segments on page visualization",
        value=False,
        help="When enabled, unknown/unclassified segments will be shown alongside detected document types."
    )

    # File uploader
    uploaded_file = st.sidebar.file_uploader(
        "Upload PDF or Image File",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        help="Supported formats: PDF, PNG, JPG, JPEG"
    )
    
    # Config viewer expander
    with st.sidebar.expander("📋 View Detection Configuration"):
        from modules.config_loader import get_config
        config = get_config()

        st.write("**Document Types:**")
        for doc_type, data in config.get_document_types().items():
            label = data.get('label', doc_type.upper())
            display_name = data.get('display_name', doc_type)
            st.write(f"📄 **{display_name}** `[{label}]`")
            st.write(f"   Aliases: {', '.join(data.get('aliases', []))}")
            keywords = data.get('keywords', {})
            all_keywords = []
            for lang, kw_list in keywords.items():
                all_keywords.extend(kw_list)
            st.write(f"   Keywords: {', '.join(all_keywords[:5])}...")

        st.write("**Document Sides:**")
        for side, data in config.get_document_sides().items():
            label = data.get('label', side.upper())
            display_name = data.get('display_name', side)
            st.write(f"🔖 **{display_name}** `[{label}]`")
            keywords = data.get('keywords', {})
            all_keywords = []
            for lang, kw_list in keywords.items():
                all_keywords.extend(kw_list)
            st.write(f"   Keywords: {', '.join(all_keywords[:5])}...")

        st.write("**Detection Settings:**")
        settings = config.get_detection_settings()
        for key, value in settings.items():
            st.write(f"   {key}: {value}")

        # Reload config button
        if st.button("Reload Configuration"):
            config.reload_config()
            st.success("Configuration reloaded!")
            st.rerun()
    
    # Group quality checks under a section
    st.sidebar.subheader("Quality Checks")

    emptiness_check_enabled = st.sidebar.checkbox(
        "Enable Emptiness Check",
        value=True,  # Default enabled
        help="Check this to enable emptiness validation"
    )

    readability_check_enabled = st.sidebar.checkbox(
        "Enable Readability Check",
        value=True,  # Default enabled
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

    # Identity Detection Configuration
    st.sidebar.subheader("Identity Detection")
    identity_confidence_threshold = st.sidebar.slider(
        "Identity Confidence Threshold (%)",
        min_value=0,
        max_value=100,
        value=50,
        step=5,
        help="Only show identity segments with confidence at or above this threshold"
    )
    
    show_unknown_segments = st.sidebar.checkbox(
        "Show low-confidence/unknown segments",
        value=False,
        help="When disabled, only segments with confidence above the threshold are shown"
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

            # Store page data in session state for re-processing when thresholds change
            st.session_state.page_data = page_data
            st.session_state.total_extraction_time = total_extraction_time
            st.session_state.uploaded_file_name = uploaded_file.name
            st.session_state.file_bytes = file_bytes  # Store file bytes for identity detection

        except Exception as e:
            st.error(f"An error occurred while processing the file: {str(e)}")
            st.info("Please check that you have properly installed Tesseract OCR and set the path correctly.")

        # Initialize variables for results processing
        df_data = []

    # Process and display results if page data exists in session state
    if 'page_data' in st.session_state and st.session_state.page_data:

        # Calculate total clarity and confidence times
        total_clarity_time = 0
        total_confidence_time = 0

        for page_info in st.session_state.page_data:
            page_num = page_info['page']

            # Calculate clarity metric with timing
            ink_ratio, clarity_time = calculate_ink_ratio(page_info['image'])
            total_clarity_time += clarity_time
            ink_ratio_pct = ink_ratio * 100

            # Calculate confidence metric with timing (using fast mode for better accuracy)
            ocr_conf, confidence_time = calculate_ocr_confidence(page_info['image'], mode='fast')
            total_confidence_time += confidence_time

            # Note: Text content extraction is done only when needed (on demand) for performance
            page_info['text_content'] = None  # Placeholder, will be populated when needed

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

            # Update page_info with the calculated metrics before checking validity
            page_info['ink_ratio'] = ink_ratio
            page_info['ocr_conf'] = ocr_conf

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
                'File': st.session_state.uploaded_file_name,
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
            st.metric("Total Pages", len(st.session_state.page_data))
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
            st.metric("File Upload & Extraction", f"{st.session_state.total_extraction_time:.2f}s")
        with timing_col2:
            st.metric("Clarity Calculation", f"{total_clarity_time:.2f}s")
        with timing_col3:
            st.metric("Readability Calculation", f"{total_confidence_time:.2f}s")

        # Identity Card Detection Section (Enabled by Default)
        st.subheader("Identity Card Detection")

        # Import the identity detection module
        from modules.identity_detection import process_identity_documents, group_identity_documents
        from modules.visualization import draw_bounding_boxes
        from modules.config_loader import get_config

        try:
            # Process the uploaded file for identity documents
            identity_results = process_identity_documents(st.session_state.file_bytes, uploaded_file.name)

            if identity_results:
                # Group results by document type
                grouped_results = group_identity_documents(identity_results)

                # Show prominent detection summary banner
                has_national_id = len(grouped_results['residential_id']) > 0
                if has_national_id:
                    st.success(f"✅ **NATIONAL ID DETECTED** — Found {len(grouped_results['residential_id'])} National ID(s)")
                else:
                    st.warning(f"⚠️ **NO NATIONAL ID DETECTED** — Found {len(grouped_results['unknown'])} unknown/unclassified documents")

                # Display summary
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Residential ID", len(grouped_results['residential_id']))
                with col2:
                    st.metric("Other", len(grouped_results['aadhaar']) + len(grouped_results['unknown']))
                with col3:
                    st.metric("Total Segments", len(identity_results))

                # Display detection summary
                st.subheader("Detection Summary")

                # Create a dataframe grouped by page so each page appears only once
                pages_map = {}
                for result in identity_results:
                    page = result.page_number
                    pages_map.setdefault(page, []).append(result)

                identity_df_data = []
                for page, results in pages_map.items():
                    has_national = False
                    best_national_conf = -1.0
                    best_national_label = ''
                    for r in results:
                        # Track national id presence and best national
                        if r.document_type.value == 'residential_id':
                            has_national = True
                            if float(r.confidence) > best_national_conf:
                                best_national_conf = float(r.confidence)
                                side_name = config.get_document_side_name(r.document_side.value) or r.document_side.value
                                best_national_label = f"National ID — {side_name.title()} ({float(r.confidence):.1f}%)"

                    identity_df_data.append({
                        'Page': page,
                        'National ID Present': '✅ Yes' if has_national else '❌ No',
                        'Detection': best_national_label if has_national else 'None detected'
                    })

                identity_df = pd.DataFrame(identity_df_data)
                st.dataframe(identity_df, use_container_width=True)

                # Show pages with detected documents and bounding boxes
                st.subheader("Page Visualizations")
                
                # Group results by page
                pages_with_docs = {}
                for result in identity_results:
                    page_num = result.page_number
                    if page_num not in pages_with_docs:
                        pages_with_docs[page_num] = []
                    pages_with_docs[page_num].append(result)
                
                # Display each page with bounding boxes - ONE IMAGE PER PAGE with all segments
                for page_num, page_results in pages_with_docs.items():
                    # Get original page image
                    try:
                        page_index = int(str(page_num).split('-')[0]) - 1
                    except Exception:
                        page_index = 0
                    page_info = st.session_state.page_data[page_index]
                    original_image = page_info['image']
                    
                    # Get colors from config
                    from modules.config_loader import get_config
                    config = get_config()
                    
                    # Filter segments by confidence threshold and unknown toggle
                    filtered_segments = []
                    for result in page_results:
                        bbox = result.features.get('bbox')
                        if not bbox:
                            continue
                        
                        conf = float(result.confidence)
                        raw_doc_type = result.document_type.value
                        is_unknown = (raw_doc_type == 'unknown')
                        
                        # Apply visibility rules
                        if not show_unknown_segments:
                            # Hide segments below threshold
                            if conf < identity_confidence_threshold:
                                continue
                        
                        filtered_segments.append(result)
                    
                    # Find best National ID segment for visual emphasis
                    best_national = None
                    for r in filtered_segments:
                        if r.document_type.value == 'residential_id':
                            if best_national is None or float(r.confidence) > float(best_national.confidence):
                                best_national = r
                    
                    # Collect bounding boxes and labels for drawing
                    bounding_boxes = []
                    labels = []
                    colors = []
                    line_widths = []
                    
                    for result in filtered_segments:
                        bbox = result.features.get('bbox')
                        raw_doc_type = result.document_type.value
                        conf = float(result.confidence)
                        
                        # Build label with confidence
                        if raw_doc_type == 'residential_id':
                            doc_type_name = 'National ID'
                        else:
                            doc_type_name = config.get_document_type_name(raw_doc_type) or raw_doc_type
                        
                        side_name = config.get_document_side_name(result.document_side.value) or result.document_side.value
                        label = f"{doc_type_name} — {side_name.title()} ({conf:.1f}%)"
                        
                        # Determine line width: best national gets thick line, others normal
                        is_best = (best_national is not None and result is best_national)
                        line_width = 6 if is_best else 3
                        
                        bounding_boxes.append(bbox)
                        labels.append(label)
                        color = config.get_document_type_color(raw_doc_type)
                        colors.append(color)
                        line_widths.append(line_width)
                    
                    # Draw all bounding boxes on a single image
                    if bounding_boxes:
                        # Draw normal segments first, then best national on top
                        annotated_image = original_image
                        
                        # Draw segments in order: non-best first (thin), then best (thick)
                        for bbox, label, color, lw in zip(bounding_boxes, labels, colors, line_widths):
                            if lw < 6:  # Not the best national
                                annotated_image = draw_bounding_boxes(annotated_image, [bbox], [label], [color], line_width=lw)
                        
                        # Draw best national last (on top) if exists
                        for bbox, label, color, lw in zip(bounding_boxes, labels, colors, line_widths):
                            if lw >= 6:  # Best national
                                annotated_image = draw_bounding_boxes(annotated_image, [bbox], [label], [color], line_width=lw)
                    else:
                        annotated_image = original_image
                    
                    # Show page with all segments
                    st.write(f"**Page {page_num}**")
                    st.image(annotated_image, caption=f"Page {page_num} - {len(filtered_segments)} segment(s) detected (Confidence threshold: {identity_confidence_threshold}%)", width="stretch")
                    
                    # Show segment summary as a compact list
                    if filtered_segments:
                        st.write("**Detected Segments:**")
                        seg_cols = st.columns(len(filtered_segments))
                        for idx, result in enumerate(filtered_segments):
                            with seg_cols[idx]:
                                raw_doc_type = result.document_type.value
                                if raw_doc_type == 'residential_id':
                                    doc_type_name = 'National ID'
                                else:
                                    doc_type_name = config.get_document_type_name(raw_doc_type) or raw_doc_type
                                side_name = config.get_document_side_name(result.document_side.value) or result.document_side.value
                                conf = float(result.confidence)
                                
                                st.metric(
                                    f"{doc_type_name}",
                                    f"{conf:.1f}%",
                                    delta=side_name.title(),
                                    delta_color="off"
                                )
                    else:
                        st.info(f"No segments above {identity_confidence_threshold}% confidence threshold.")
                    
                    st.divider()

                # Detailed/Advanced analysis - only for power users
                with st.expander("🔬 Advanced Analysis (Confidence Details, Keywords, OCR Data)", expanded=False):
                    for idx, result in enumerate(identity_results):
                        is_national = (result.document_type.value == 'residential_id')
                        exp_label = f"Page {result.page_number} - National ID {result.document_side.value.title()} ({float(result.confidence):.1f}%)" if is_national else f"Page {result.page_number} - {result.document_type.value} ({result.document_side.value}) - {float(result.confidence):.2f}%"
                        with st.expander(exp_label, expanded=is_national):
                            # Display the segmented image if available
                            if 'segmented_image' in result.features:
                                st.image(
                                    result.features['segmented_image'],
                                    caption=f"Segmented Document",
                                    width="stretch"
                                )
                            
                            st.write(f"**Document Type:** {result.document_type.value}")
                            st.write(f"**Document Side:** {result.document_side.value}")
                            st.write(f"**Final Confidence:** {result.confidence:.2f}%")
                        
                            # Show detailed confidence breakdown
                            st.write("**Confidence Breakdown:**")
                            
                            adjustment_details = result.features.get('confidence_adjustment', {})
                            if adjustment_details:
                                # Ensure confidence is a float
                                base_confidence = float(result.confidence) - float(adjustment_details.get('total_adjustment', 0))
                                st.write(f"  - Base Confidence: {base_confidence:.2f}%")
                                
                                # Frequency boost
                                freq_boost = float(adjustment_details.get('frequency_boost', 0))
                                if freq_boost > 0:
                                    cross_docs = int(adjustment_details.get('cross_document_matches', 0))
                                    st.write(f"  - Frequency Boost: +{freq_boost:.2f}% ({cross_docs} document(s) with similar keywords)")
                                
                                # Specificity bonus
                                spec_bonus = float(adjustment_details.get('specificity_bonus', 0))
                                if spec_bonus > 0:
                                    st.write(f"  - Specificity Bonus: +{spec_bonus:.2f}% (specific keywords detected)")
                                
                                # Consistency bonus
                                consist_bonus = float(adjustment_details.get('consistency_bonus', 0))
                                if consist_bonus > 0:
                                    st.write(f"  - Consistency Bonus: +{consist_bonus:.2f}% (multiple keyword matches)")
                                
                                # Quality factor
                                quality_factor = float(adjustment_details.get('quality_factor', 1.0))
                                if quality_factor < 1.0:
                                    st.warning(f"  - Quality Adjustment: ×{quality_factor:.2f} (reduced due to low document quality)")
                                else:
                                    st.write(f"  - Quality Factor: ×{quality_factor:.2f} (good quality)")
                                
                                # Total adjustment
                                total_adj = float(adjustment_details.get('total_adjustment', 0))
                                st.write(f"  - **Total Adjustment: +{total_adj:.2f}%**")
                                
                                # Visual indicator
                                if total_adj > 10:
                                    st.success("✅ High confidence due to consistent keyword patterns")
                                elif total_adj > 5:
                                    st.info("ℹ️ Moderate confidence boost from keyword matches")
                                else:
                                    st.write("ℹ️ Standard confidence (no significant keyword patterns)")
                            else:
                                st.write(f"  - No adjustment details available")
                            
                            # Show matched keywords with frequency
                            st.write("**Matched Keywords:**")
                            has_matches = False
                            
                            if 'document_type_keyword_matches' in result.features:
                                type_matches = result.features['document_type_keyword_matches']
                                matched_types = [t for t, m in type_matches.items() if m]
                                if matched_types:
                                    has_matches = True
                                    for doc_type in matched_types:
                                        # Get frequency info
                                        freq_info = ""
                                        if adjustment_details:
                                            cross_docs = adjustment_details.get('cross_document_matches', 0)
                                            if cross_docs > 1:
                                                freq_info = f" (found in {cross_docs} documents)"
                                        st.write(f"  📄 **{doc_type}**{freq_info}")
                            
                            if 'document_side_keyword_matches' in result.features:
                                side_matches = result.features['document_side_keyword_matches']
                                matched_sides = [s for s, m in side_matches.items() if m]
                                if matched_sides:
                                    has_matches = True
                                    for side in matched_sides:
                                        st.write(f"  🔖 **{side}**")
                            
                            if not has_matches:
                                st.write("  _No specific keywords matched_")
                            
                            # Show specific keywords that matched
                            st.write("**Specific Keywords Detected:**")
                            keyword_list = []
                            text_lower = result.text_content.lower()
                            
                            # Get keywords from config
                            from modules.config_loader import get_config
                            config = get_config()
                            doc_type_keywords = config.get_all_document_type_keywords()
                            doc_side_keywords = config.get_document_side_keywords('front')
                            doc_side_keywords.update(config.get_document_side_keywords('back'))
                            
                            # Check document type keywords
                            for doc_type, keywords in doc_type_keywords.items():
                                for lang, kw_list in keywords.items():
                                    for keyword in kw_list:
                                        if keyword.lower() in text_lower:
                                            keyword_list.append(f"🔹 {keyword} ({doc_type})")
                            
                            # Check document side keywords
                            for side, keywords in doc_side_keywords.items():
                                for lang, kw_list in keywords.items():
                                    for keyword in kw_list:
                                        if keyword.lower() in text_lower:
                                            keyword_list.append(f"🔸 {keyword} ({side})")
                            
                            if keyword_list:
                                # Show unique keywords
                                unique_keywords = list(set(keyword_list))[:10]  # Limit to 10
                                for kw in unique_keywords:
                                    st.write(f"  {kw}")
                            else:
                                st.write("  _No specific keywords detected_")
                            
                            st.write(f"**Text Content:**")
                            st.text_area("Extracted Text", value=result.text_content, height=150, key=f"text_area_{idx}")

            else:
                st.info("No identity documents detected in the uploaded file.")

        except Exception as e:
            st.error(f"An error occurred during identity card detection: {str(e)}")

        # Display results table
        st.subheader("Validation Results")
        st.dataframe(df.style.apply(
            lambda x: ['background-color: #ffcccc' if v == 'Invalid' else '' for v in x],
            subset=['Status']
        ))

    # Add content extraction functionality
    st.subheader("Content Extraction")
    if st.button("Extract All Pages Content"):
        # Check if content was already extracted to avoid redundant processing
        if hasattr(st.session_state, 'extracted_content') and st.session_state.extracted_content:
            st.info(f"Content already extracted for {len(st.session_state.extracted_content)} pages. Click again to re-extract.")
        else:
            extracted_content = {}
            for page_info in st.session_state.page_data:
                page_num = page_info['page']
                # Extract text content from the page image using OCR
                if TESSERACT_AVAILABLE:
                    try:
                        # Use the optimized content extraction function
                        text, _ = extract_text_content(page_info['image'], mode='fast')

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
            st.success(f"Content extracted for {len(st.session_state.page_data)} pages!")

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
                        width="stretch"
                    )

                    # Add Read Content button for each page
                    if st.button(f"Read Content (Page {page_info['page']})", key=f"read_content_{page_info['page']}_invalid"):
                        # Extract text content from the page image using OCR
                        if TESSERACT_AVAILABLE:
                            try:
                                # Use the optimized content extraction function
                                text, _ = extract_text_content(page_info['image'], mode='fast')

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
    if len(df) > 0:
        valid_pages_df = df[df['Status'] == 'Valid']
        if not valid_pages_df.empty:
            st.subheader("Valid Pages - Content Extraction")
            for idx, row in valid_pages_df.iterrows():
                page_num = int(row['Page'])

                # Find the corresponding page_info
                page_info = next((p for p in st.session_state.page_data if p['page'] == page_num), None)
                if page_info:
                    cols = st.columns([3, 1, 1])  # Image, Info, Buttons
                    with cols[0]:
                        st.image(
                            page_info['image'],
                            caption=f"Page {page_num} - Ink Ratio: {page_info['ink_ratio']*100:.2f}%, OCR Confidence: {page_info['ocr_conf']:.2f}",
                            width="stretch"
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
                                    # Use the optimized content extraction function
                                    text, _ = extract_text_content(page_info['image'], mode='fast')

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

        else:
            st.info("👆 Please upload a PDF or image file to begin validation.")

if __name__ == "__main__":
    main()