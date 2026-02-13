"""
DEPRECATED: Redirects to new modules. See utils/ directory.
"""

import warnings
from utils.document_processor import extract_page_data as _extract_page_data


def extract_page_data(file_bytes, file_name):
    warnings.warn("document_processor.extract_page_data is deprecated.", DeprecationWarning)
    return _extract_page_data(file_bytes, file_name)