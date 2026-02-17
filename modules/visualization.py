"""
Visualization utilities for identity card detection.
"""

import cv2
import numpy as np
from PIL import Image
from typing import List, Tuple, Dict
from modules.document_segmentation import DocumentSegment


def draw_bounding_boxes(image: Image.Image, 
                       bounding_boxes: List[Tuple[int, int, int, int]], 
                       labels: List[str] = None,
                       colors: List[Tuple[int, int, int]] = None,
                       line_width: int = 3) -> Image.Image:
    """
    Draw bounding boxes on an image.
    
    Args:
        image: PIL Image to draw on
        bounding_boxes: List of (x, y, width, height) tuples
        labels: Optional list of labels for each box
        colors: Optional list of RGB colors for each box
        line_width: Width of bounding box lines
        
    Returns:
        PIL Image with bounding boxes drawn
    """
    # Convert to OpenCV format
    img_cv = np.array(image)
    if len(img_cv.shape) == 2:
        img_cv = cv2.cvtColor(img_cv, cv2.COLOR_GRAY2BGR)
    else:
        img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)
    
    # Default colors if not provided
    if colors is None:
        colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Cyan
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Yellow
        ]
    
    for idx, bbox in enumerate(bounding_boxes):
        x, y, w, h = bbox
        
        # Get color (cycle through if not enough colors)
        color = colors[idx % len(colors)] if colors else (255, 0, 0)
        
        # Draw rectangle
        cv2.rectangle(img_cv, (x, y), (x + w, y + h), color, line_width)
        
        # Draw label if provided
        if labels:
            label = labels[idx % len(labels)]
            
            # Calculate label background size
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            (text_width, text_height), baseline = cv2.getTextSize(
                label, font, font_scale, line_width
            )
            
            # Draw label background
            cv2.rectangle(
                img_cv,
                (x, y - text_height - baseline - 5),
                (x + text_width, y),
                color,
                -1  # Filled rectangle
            )
            
            # Draw label text
            cv2.putText(
                img_cv,
                label,
                (x, y - baseline),
                font,
                font_scale,
                (255, 255, 255),  # White text
                line_width,
                cv2.LINE_AA
            )
    
    # Convert back to PIL
    img_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
    return img_pil


def draw_segmentation_results(image: Image.Image, 
                             segments: List[DocumentSegment],
                             classifications: List[Dict] = None) -> Image.Image:
    """
    Draw segmentation results with bounding boxes and labels.
    
    Args:
        image: Original PIL Image
        segments: List of DocumentSegment objects
        classifications: Optional list of classification results for labels
        
    Returns:
        PIL Image with segmentation visualization
    """
    bounding_boxes = [segment.bbox for segment in segments]
    
    # Create labels if classifications provided
    labels = []
    if classifications:
        for idx, classification in enumerate(classifications):
            doc_type = classification.get('document_type', 'Unknown')
            doc_side = classification.get('document_side', 'Unknown')
            confidence = classification.get('confidence', 0)
            labels.append(f"{doc_type} - {doc_side} ({confidence:.1f}%)")
    else:
        labels = [f"Document {i+1}" for i in range(len(segments))]
    
    # Draw bounding boxes
    return draw_bounding_boxes(image, bounding_boxes, labels)
