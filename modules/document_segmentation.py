"""
Document segmentation module for handling multiple documents on a single page.
"""

import cv2
import numpy as np
from PIL import Image
import math
from typing import List, Tuple, Dict
from dataclasses import dataclass


@dataclass
class DocumentSegment:
    """Data class for a segmented document with bounding box."""
    image: Image.Image
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    confidence: float = 1.0


def segment_documents_on_page(image: Image.Image, config: Dict = None) -> List[DocumentSegment]:
    """
    Segment a page image into individual document images with bounding boxes.

    Args:
        image: PIL Image of a page that may contain multiple documents
        config: Optional configuration dictionary for detection settings

    Returns:
        List of DocumentSegment objects containing images and bounding boxes
    """
    # Load default config if not provided
    if config is None:
        from modules.config_loader import get_config
        cfg = get_config()
        config = cfg.get_detection_settings()
    
    # Get detection settings from config
    min_area_percent = config.get('min_document_area_percent', 5.0) / 100
    max_area_percent = config.get('max_document_area_percent', 80.0) / 100
    min_aspect_ratio = config.get('min_aspect_ratio', 1.4)
    max_aspect_ratio = config.get('max_aspect_ratio', 2.0)
    padding_percent = config.get('padding_percent', 5.0) / 100
    
    # Convert PIL to OpenCV
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    img_height, img_width = img_cv.shape[:2]
    total_area = img_width * img_height
    
    # Apply threshold to get binary image
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Morphological operations to connect nearby regions
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    # Find contours (potential document boundaries)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter contours to find document-sized rectangles
    document_contours = []
    
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)
        
        # Calculate area percentage
        area_percent = area / total_area
        
        # Calculate aspect ratio
        aspect_ratio = w / h if h > 0 else 0
        
        # Check if contour matches document size criteria
        min_area = total_area * min_area_percent
        max_area = total_area * max_area_percent
        
        if min_area < area < max_area and min_aspect_ratio < aspect_ratio < max_aspect_ratio:
            document_contours.append((x, y, w, h))
    
    # Sort contours by x-coordinate to process left to right
    document_contours.sort(key=lambda c: c[0])
    
    # Remove overlapping contours (keep larger ones) - use stricter threshold to detect multiple documents
    # Lower threshold means more documents can coexist (only remove if heavily overlapping)
    document_contours = remove_overlapping_contours(document_contours, iou_threshold=0.3)
    
    segmented_docs = []
    for x, y, w, h in document_contours:
        # Add padding to ensure we capture the full document
        pad_x = int(w * padding_percent)
        pad_y = int(h * padding_percent)
        
        x_start = max(0, x - pad_x)
        y_start = max(0, y - pad_y)
        x_end = min(img_width, x + w + pad_x)
        y_end = min(img_height, y + h + pad_y)
        
        # Extract the document region
        doc_region = img_cv[y_start:y_end, x_start:x_end]
        
        # Convert back to PIL
        doc_pil = Image.fromarray(cv2.cvtColor(doc_region, cv2.COLOR_BGR2RGB))
        
        # Create DocumentSegment with bounding box (relative to original image)
        segment = DocumentSegment(
            image=doc_pil,
            bbox=(x_start, y_start, x_end - x_start, y_end - y_start),
            confidence=1.0
        )
        segmented_docs.append(segment)
    
    # Fix overlapping segments - adjust bounding boxes to eliminate overlaps
    if len(segmented_docs) > 1:
        segmented_docs = _fix_overlapping_bboxes(segmented_docs, img_cv)
    
    # If no documents were found using contours, return the whole page
    if not segmented_docs:
        # Try projection-based splitting first (better for clean front/back pairs)
        # Try horizontal projection split (double document stacked top/bottom)
        horiz_segments = _segment_by_horizontal_projection(gray, img_width, img_height, padding_percent)
        if horiz_segments:
            return horiz_segments

        # Try vertical projection split (documents placed side-by-side)
        vert_segments = _segment_by_vertical_projection(gray, img_width, img_height, padding_percent)
        if vert_segments:
            return vert_segments

        # Try an edge-detection based segmentation fallback
        edge_segments = _segment_with_edge_detection(img_cv, img_width, img_height,
                                                     min_area, max_area,
                                                     min_aspect_ratio, max_aspect_ratio,
                                                     padding_percent)
        if edge_segments:
            return edge_segments

        # Final fallback: return the whole page
        return [DocumentSegment(image=image, bbox=(0, 0, img_width, img_height), confidence=1.0)]
    
    return segmented_docs


def remove_overlapping_contours(contours: List[Tuple[int, int, int, int]], 
                                iou_threshold: float = 0.3) -> List[Tuple[int, int, int, int]]:
    """
    Remove overlapping contours using IoU (Intersection over Union).
    Also ensures that contours that physically overlap in space are handled properly.
    
    Args:
        contours: List of (x, y, w, h) tuples
        iou_threshold: IoU threshold for considering contours as overlapping (default 0.3 to allow multiple documents)
        
    Returns:
        Filtered list of contours
    """
    if len(contours) <= 1:
        return contours
    
    def calculate_iou(c1, c2):
        """Calculate IoU between two contours."""
        x1, y1, w1, h1 = c1
        x2, y2, w2, h2 = c2
        
        # Calculate intersection
        xi1 = max(x1, x2)
        yi1 = max(y1, y2)
        xi2 = min(x1 + w1, x2 + w2)
        yi2 = min(y1 + h1, y2 + h2)
        
        inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
        
        # Calculate union
        area1 = w1 * h1
        area2 = w2 * h2
        union_area = area1 + area2 - inter_area
        
        # Calculate IoU
        return inter_area / union_area if union_area > 0 else 0
    
    def get_separation(c1, c2):
        """Calculate minimum separation between two contours (vertical or horizontal gap)."""
        x1, y1, w1, h1 = c1
        x2, y2, w2, h2 = c2
        
        # Get bounds
        c1_right = x1 + w1
        c1_bottom = y1 + h1
        c2_right = x2 + w2
        c2_bottom = y2 + h2
        
        # Calculate horizontal separation (gap between left/right)
        if c1_right < x2:
            h_sep = x2 - c1_right
        elif c2_right < x1:
            h_sep = x1 - c2_right
        else:
            h_sep = 0  # Overlapping horizontally
        
        # Calculate vertical separation (gap between top/bottom)
        if c1_bottom < y2:
            v_sep = y2 - c1_bottom
        elif c2_bottom < y1:
            v_sep = y1 - c2_bottom
        else:
            v_sep = 0  # Overlapping vertically
        
        return h_sep, v_sep
    
    # Sort by area (largest first)
    sorted_contours = sorted(contours, key=lambda c: c[2] * c[3], reverse=True)
    
    result = []
    for contour in sorted_contours:
        # Check if this contour overlaps with any already selected contour
        is_overlapping = False
        for selected in result:
            iou = calculate_iou(contour, selected)
            h_sep, v_sep = get_separation(contour, selected)
            
            # If IoU is above threshold OR they're physically overlapping (no gap), mark as overlapping
            if iou > iou_threshold or (h_sep == 0 and v_sep == 0):
                is_overlapping = True
                break
        
        if not is_overlapping:
            result.append(contour)
    
    return result


def _fix_overlapping_bboxes(segments: List[DocumentSegment], img_cv) -> List[DocumentSegment]:
    """
    Fix overlapping document segments by adjusting their bounding boxes and re-extracting.
    When two segments overlap, the overlap region is assigned to the segment that comes first.
    
    Args:
        segments: List of DocumentSegment objects (assumed to be sorted top-to-bottom)
        img_cv: Original image in OpenCV format
        
    Returns:
        List of DocumentSegment objects with non-overlapping bounding boxes
    """
    if len(segments) <= 1:
        return segments
    
    # Sort by Y coordinate (top to bottom)
    sorted_segments = sorted(segments, key=lambda s: s.bbox[1])
    
    adjusted_bboxes = [list(s.bbox) for s in sorted_segments]
    
    # Fix overlaps by adjusting Y coordinates
    for i in range(len(adjusted_bboxes) - 1):
        curr_x, curr_y, curr_w, curr_h = adjusted_bboxes[i]
        next_x, next_y, next_w, next_h = adjusted_bboxes[i + 1]
        
        curr_bottom = curr_y + curr_h
        
        # If current segment's bottom overlaps with next segment's top
        if curr_bottom > next_y:
            # Calculate the overlap
            overlap = curr_bottom - next_y
            
            # Adjust by moving the split point to the middle of the overlap
            # Current segment loses the bottom part of the overlap
            split_point = curr_y + (curr_h - overlap // 2)
            
            # Adjust current segment (make it shorter)
            adjusted_bboxes[i][3] = split_point - curr_y
            
            # Adjust next segment (make it start lower and shorter)
            adjusted_bboxes[i + 1][1] = split_point
            adjusted_bboxes[i + 1][3] = next_y + next_h - split_point
    
    # Re-extract segments with adjusted bounding boxes
    img_height, img_width = img_cv.shape[:2]
    result = []
    
    for i, (bbox, orig_segment) in enumerate(zip(adjusted_bboxes, sorted_segments)):
        x, y, w, h = bbox
        
        # Ensure dimensions are valid
        if w > 20 and h > 20:
            # Clamp to image bounds
            x = max(0, min(x, img_width - 1))
            y = max(0, min(y, img_height - 1))
            x_end = min(x + w, img_width)
            y_end = min(y + h, img_height)
            
            # Re-extract from original image
            doc_region = img_cv[y:y_end, x:x_end]
            doc_pil = Image.fromarray(cv2.cvtColor(doc_region, cv2.COLOR_BGR2RGB))
            
            adjusted_segment = DocumentSegment(
                image=doc_pil,
                bbox=(x, y, x_end - x, y_end - y),
                confidence=orig_segment.confidence
            )
            result.append(adjusted_segment)
    
    return result


def _remove_overlapping_segments(segments: List[DocumentSegment]) -> List[DocumentSegment]:
    """
    Remove or adjust overlapping document segments to ensure clean separation.
    
    Args:
        segments: List of DocumentSegment objects
        
    Returns:
        List of DocumentSegment objects with overlaps removed/adjusted
    """
    if len(segments) <= 1:
        return segments
    
    # Sort segments by position (top-to-bottom, left-to-right)
    segments = sorted(segments, key=lambda s: (s.bbox[1], s.bbox[0]))
    
    result = []
    for current in segments:
        x_c, y_c, w_c, h_c = current.bbox
        overlaps = False
        
        # Check if this segment overlaps with any previously accepted segment
        for prev in result:
            x_p, y_p, w_p, h_p = prev.bbox
            
            # Calculate overlap
            overlap_left = max(x_c, x_p)
            overlap_right = min(x_c + w_c, x_p + w_p)
            overlap_top = max(y_c, y_p)
            overlap_bottom = min(y_c + h_c, y_p + h_p)
            
            # Check if there's actual overlap
            if overlap_right > overlap_left and overlap_bottom > overlap_top:
                overlap_area = (overlap_right - overlap_left) * (overlap_bottom - overlap_top)
                current_area = w_c * h_c
                prev_area = w_p * h_p
                
                # If overlap is significant (>10% of either segment), consider them overlapping
                if overlap_area > max(current_area, prev_area) * 0.1:
                    overlaps = True
                    break
        
        if not overlaps:
            result.append(current)
    
    return result



def _segment_with_edge_detection(img_cv, img_width, img_height,
                                  min_area, max_area,
                                  min_aspect_ratio, max_aspect_ratio,
                                  padding_percent) -> List[DocumentSegment]:
    """
    Try segmentation using Canny edges + contour approximation to find rectangular documents.
    """
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    # Smooth and detect edges
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    # Dilate edges to close gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    dilated = cv2.dilate(edges, kernel, iterations=2)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    segments = []
    total_area = img_width * img_height
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < total_area * min_area or area > total_area * max_area:
            continue

        # Approximate polygon and look for quadrilaterals
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        if len(approx) < 4:
            continue

        x, y, w, h = cv2.boundingRect(approx)
        aspect_ratio = w / h if h > 0 else 0
        if not (min_aspect_ratio < aspect_ratio < max_aspect_ratio):
            continue

        pad_x = int(w * padding_percent)
        pad_y = int(h * padding_percent)

        x_start = max(0, x - pad_x)
        y_start = max(0, y - pad_y)
        x_end = min(img_width, x + w + pad_x)
        y_end = min(img_height, y + h + pad_y)

        doc_region = img_cv[y_start:y_end, x_start:x_end]
        doc_pil = Image.fromarray(cv2.cvtColor(doc_region, cv2.COLOR_BGR2RGB))
        segments.append(DocumentSegment(image=doc_pil, bbox=(x_start, y_start, x_end-x_start, y_end-y_start), confidence=0.9))

    # Sort left-to-right
    segments.sort(key=lambda s: s.bbox[0])
    return segments


def _segment_by_horizontal_projection(gray, img_width, img_height, padding_percent) -> List[DocumentSegment]:
    """
    Split image horizontally by finding a strong horizontal valley in the projection profile.
    Useful for pages with two documents stacked vertically (front/back).
    """
    # Compute binary projection (sum of dark pixels per row)
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # In bw, text is white(255) on black(0) typically; invert if needed
    if np.mean(bw) > 127:
        bw = cv2.bitwise_not(bw)

    row_sums = np.sum(bw == 255, axis=1)
    max_row = row_sums.max() if row_sums.size else 0
    if max_row == 0:
        return []

    # Find low regions where row_sums drop below a small fraction of max (gap between docs)
    threshold = max(5, int(0.05 * max_row))
    low_rows = np.where(row_sums < threshold)[0]
    if low_rows.size == 0:
        return []

    # Find the largest continuous low region
    gaps = np.split(low_rows, np.where(np.diff(low_rows) != 1)[0]+1)
    largest_gap = max(gaps, key=lambda g: g.size)
    gap_height = largest_gap.size

    # Require gap to be reasonably large (e.g., >= 3% of image height)
    if gap_height < max(3, int(0.03 * img_height)):
        return []

    # Choose split row as the middle of the largest gap
    split_row = int(largest_gap.mean())

    # Create two segments: top and bottom
    pad_y = int(0.01 * img_height)
    top_y0 = 0
    top_y1 = max(0, split_row - pad_y)
    bot_y0 = min(img_height, split_row + pad_y)
    bot_y1 = img_height

    segments = []
    for y0, y1 in [(top_y0, top_y1), (bot_y0, bot_y1)]:
        if y1 - y0 <= 10:
            continue
        doc_region = gray[y0:y1, :]
        # Convert to RGB for PIL
        doc_rgb = cv2.cvtColor(cv2.merge([doc_region, doc_region, doc_region]), cv2.COLOR_BGR2RGB)
        doc_pil = Image.fromarray(doc_rgb)
        segments.append(DocumentSegment(image=doc_pil, bbox=(0, y0, img_width, y1-y0), confidence=0.6))

    return segments


def _segment_by_vertical_projection(gray, img_width, img_height, padding_percent) -> List[DocumentSegment]:
    """
    Split image vertically by finding a strong vertical valley in the projection profile.
    Useful for pages with two documents placed side-by-side (left/right).
    """
    # Compute binary projection (sum of dark pixels per column)
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # In bw, text is white(255) on black(0) typically; invert if needed
    if np.mean(bw) > 127:
        bw = cv2.bitwise_not(bw)

    col_sums = np.sum(bw == 255, axis=0)
    max_col = col_sums.max() if col_sums.size else 0
    if max_col == 0:
        return []

    # Find low regions where col_sums drop below a small fraction of max (gap between docs)
    threshold = max(5, int(0.05 * max_col))
    low_cols = np.where(col_sums < threshold)[0]
    if low_cols.size == 0:
        return []

    # Find the largest continuous low region
    gaps = np.split(low_cols, np.where(np.diff(low_cols) != 1)[0]+1)
    largest_gap = max(gaps, key=lambda g: g.size)
    gap_width = largest_gap.size

    # Require gap to be reasonably large (e.g., >= 3% of image width)
    if gap_width < max(3, int(0.03 * img_width)):
        return []

    # Choose split column as the middle of the largest gap
    split_col = int(largest_gap.mean())

    # Create two segments: left and right
    pad_x = int(0.01 * img_width)
    left_x0 = 0
    left_x1 = max(0, split_col - pad_x)
    right_x0 = min(img_width, split_col + pad_x)
    right_x1 = img_width

    segments = []
    for x0, x1 in [(left_x0, left_x1), (right_x0, right_x1)]:
        if x1 - x0 <= 10:
            continue
        doc_region = gray[:, x0:x1]
        # Convert to RGB for PIL
        doc_rgb = cv2.cvtColor(cv2.merge([doc_region, doc_region, doc_region]), cv2.COLOR_BGR2RGB)
        doc_pil = Image.fromarray(doc_rgb)
        segments.append(DocumentSegment(image=doc_pil, bbox=(x0, 0, x1-x0, img_height), confidence=0.6))

    return segments



def process_page_with_multiple_documents(image: Image.Image, text_content: str, page_number: int) -> List['IdentityCardClassification']:
    """
    Process a page that may contain multiple documents.

    Args:
        image: PIL Image of the page
        text_content: OCR text from the entire page
        page_number: Original page number

    Returns:
        List of IdentityCardClassification objects for each detected document
    """
    # Import locally to avoid circular dependency
    from modules.identity_detection import IdentityCardClassification, IdentityCardDetector
    from modules.config_loader import get_config
    from utils.content_extraction import extract_text_content
    from utils.text_cleaner import clean_text
    from checks.clarity_check import calculate_ink_ratio
    
    # First, try to segment the page into individual documents
    segmented_docs = segment_documents_on_page(image)

    results = []

    for idx, segment in enumerate(segmented_docs):
        # Perform OCR on the individual document image with adaptive mode selection
        # First try fast mode
        individual_text, _ = extract_text_content(segment.image, mode='fast')
        
        # If text is too short or quality is poor, retry with full mode
        if len(individual_text) < 30:  # If less than 30 chars, quality is likely poor
            individual_text_full, _ = extract_text_content(segment.image, mode='full')
            # Use full mode result if it's significantly better
            if len(individual_text_full) > len(individual_text) * 1.5:
                individual_text = individual_text_full

        # Clean the extracted text to remove unwanted characters
        individual_text = clean_text(individual_text)

        # Classify this individual document
        detector = IdentityCardDetector()
        classification = detector.classify_identity_document(
            segment.image,
            individual_text,
            f"{page_number}-{idx+1}"  # Indicate this is sub-document
        )
        
        # Store bounding box in features for visualization
        classification.features['bbox'] = segment.bbox
        classification.features['segmented_image'] = segment.image

        results.append(classification)

    return results


def detect_and_classify_documents_in_pdf(file_bytes: bytes, file_name: str) -> List['IdentityCardClassification']:
    """
    Main function to detect and classify documents in a PDF, handling multiple docs per page.

    Args:
        file_bytes: Bytes of the uploaded PDF file
        file_name: Name of the uploaded file

    Returns:
        List of IdentityCardClassification objects with detection results
    """
    # Import locally to avoid circular dependency
    from modules.identity_detection import IdentityCardClassification, IdentityCardDetector
    from utils.document_processor import extract_page_data

    results = []

    # Extract page data using existing functionality
    page_data_list, _ = extract_page_data(file_bytes, file_name)

    for page_data in page_data_list:
        page_num = page_data['page']
        image = page_data['image']
        text_content = page_data['text_content']

        # Check if this page might contain multiple documents
        # This could be determined by layout analysis or document count estimation
        page_results = process_page_with_multiple_documents(image, text_content, page_num)

        results.extend(page_results)

    return results