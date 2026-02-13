"""
DEPRECATED: Redirects to new modules. See utils/ directory.
"""

import warnings
from utils.content_extraction import extract_json_keys as _extract_json_keys
from utils.content_extraction import display_content_in_sidebar as _display_content_in_sidebar


def extract_json_keys(text):
    warnings.warn("content_extraction.extract_json_keys is deprecated.", DeprecationWarning)
    return _extract_json_keys(text)


def display_content_in_sidebar(page_key, content):
    warnings.warn("content_extraction.display_content_in_sidebar is deprecated.", DeprecationWarning)
    return _display_content_in_sidebar(page_key, content)