"""
Identity card detection modules.
"""

from modules.identity_detection import process_identity_documents, group_identity_documents
from modules.document_segmentation import segment_documents_on_page, DocumentSegment
from modules.config_loader import get_config, Config
from modules.visualization import draw_bounding_boxes, draw_segmentation_results

__all__ = [
    'process_identity_documents',
    'group_identity_documents',
    'segment_documents_on_page',
    'DocumentSegment',
    'get_config',
    'Config',
    'draw_bounding_boxes',
    'draw_segmentation_results'
]
