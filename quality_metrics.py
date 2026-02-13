"""
DEPRECATED: Redirects to new modules. See checks/ and utils/ directories.
"""

import warnings
from checks.clarity_check import calculate_ink_ratio as _calculate_ink_ratio
from checks.confidence_check import calculate_ocr_confidence as _calculate_ocr_confidence
from utils.content_extraction import extract_text_content as _extract_text_content


def calculate_ink_ratio(image):
    warnings.warn("quality_metrics.calculate_ink_ratio is deprecated.", DeprecationWarning)
    return _calculate_ink_ratio(image)


def calculate_ocr_confidence(image):
    warnings.warn("quality_metrics.calculate_ocr_confidence is deprecated.", DeprecationWarning)
    return _calculate_ocr_confidence(image)


def extract_text_content(image):
    warnings.warn("quality_metrics.extract_text_content is deprecated.", DeprecationWarning)
    return _extract_text_content(image)