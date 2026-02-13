"""
DEPRECATED: Redirects to new modules. See utils/ directory.
"""

import warnings
from utils.document_processor import extract_page_data as _extract_page_data


def extract_page_data(file_bytes, file_name):
    warnings.warn("document_processor.extract_page_data is deprecated.", DeprecationWarning)
    result = _extract_page_data(file_bytes, file_name)
    # If the new function returns a tuple (results, time), return just the results for backward compatibility
    if isinstance(result, tuple):
        return result[0]
    return result