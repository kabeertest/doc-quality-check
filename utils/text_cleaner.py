"""
Text cleaning utilities to remove unwanted characters and improve text quality.
"""

import re


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
