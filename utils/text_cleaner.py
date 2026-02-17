"""
Text cleaning utilities to remove unwanted characters and improve text quality.
"""

import re
from typing import Optional


def clean_text(text: str) -> str:
    """
    Clean extracted text by removing unwanted characters and normalizing whitespace.
    
    Removes:
    - Replacement characters (????, ?, etc.)
    - Control characters and zero-width characters
    - Excessive whitespace
    - Null bytes
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned text with unwanted characters removed
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Remove replacement character and similar unwanted chars
    # Common replacement characters: ? • ▯ ░ ▤ ▨ 
    text = re.sub(r'[?\x00-\x08\x0B\x0C\x0E-\x1F\x7F\uFFFD]', '', text)
    
    # Remove multiple consecutive ???? patterns (likely OCR garbage)
    text = re.sub(r'\?{4,}', '', text)
    text = re.sub(r'•{4,}', '', text)
    
    # Remove excessive whitespace but preserve single spaces and newlines
    text = re.sub(r' {2,}', ' ', text)  # Multiple spaces -> single space
    text = re.sub(r'\t+', ' ', text)    # Tabs -> single space
    text = re.sub(r'\n{3,}', '\n', text)  # Multiple newlines -> double newline
    
    # Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # Remove empty lines and clean up overall structure
    lines = [line for line in lines if line]
    text = '\n'.join(lines)
    
    return text.strip()


def sanitize_for_display(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize text for safe display in UI.
    Applies text cleaning and optionally truncates.
    
    Args:
        text: Text to sanitize
        max_length: Optional maximum length (truncates with ellipsis if exceeded)
        
    Returns:
        Sanitized and optionally truncated text
    """
    sanitized = clean_text(text)
    
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip() + "..."
    
    return sanitized


def is_garbage_text(text: str, min_length: int = 5) -> bool:
    """
    Check if text appears to be mostly garbage/corrupted.
    
    Args:
        text: Text to check
        min_length: Minimum expected length of valid text
        
    Returns:
        True if text appears to be garbage, False otherwise
    """
    if not text or len(text) < min_length:
        return True
    
    # Count replacement characters and control chars
    problem_chars = len(re.findall(r'[?\x00-\x1F\x7F\uFFFD]', text))
    
    # If more than 30% of text is problematic characters, it's likely garbage
    return problem_chars / len(text) > 0.3


def clean_label_text(text: str) -> str:
    """
    Clean text for use in label/title display.
    Removes unwanted characters and limits length for display.
    
    Args:
        text: Text for label
        
    Returns:
        Cleaned label text (max 100 chars)
    """
    cleaned = clean_text(text)
    return sanitize_for_display(cleaned, max_length=100)
