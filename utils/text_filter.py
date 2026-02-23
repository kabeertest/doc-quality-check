"""
Module for filtering out OCR artifacts and noise from extracted text.

This removes common screenshot artifacts like:
- File paths (file:///C:/Users/...)
- Timestamps (2/17/26, 9:23 AM)
- URLs (https://...)
- Browser UI elements
- Window titles and file names

This ensures confidence scores reflect actual document content, not screenshot artifacts.
"""

import re


# Common artifact patterns to remove
ARTIFACT_PATTERNS = [
    # File paths (Windows, Mac, Linux)
    r'file:///[A-Za-z]:/[^\\s]+',  # file:///C:/Users/...
    r'file:///[^\\s]+',             # file:///home/user/...
    r'[A-Za-z]:\\[^\\s]+',          # C:\Users\...
    r'/Users/[^\\s]+',              # /Users/username/...
    r'/home/[^\\s]+',               # /home/user/...
    
    # URLs
    r'https?://[^\\s]+',            # http://... or https://...
    r'www\\.[^\\s]+',               # www.example.com
    
    # Timestamps (various formats)
    r'\\d{1,2}/\\d{1,2}/\\d{2,4},?\\s*\\d{1,2}:\\d{2}(?::\\d{2})?\\s*(?:AM|PM|am|pm)?',  # 2/17/26, 9:23 AM
    r'\\d{4}-\\d{2}-\\d{2}[T\\s]\\d{2}:\\d{2}',  # 2024-01-15 10:30
    r'\\d{2}-\\d{2}-\\d{4}\\s+\\d{2}:\\d{2}',  # 15-01-2024 10:30
    
    # File names with extensions (common in screenshots)
    r'[A-Za-z0-9_-]+\\.(png|jpg|jpeg|gif|bmp|pdf|txt|doc|docx)(?:\\s*\\(\\d+x\\d+\\))?',  # filename.png (1280x802)
    
    # Browser/application UI patterns
    r'storyblok\\.png',
    r'Italian_electronic_ID_card',
    r'wikimedia\\.org',
    r'upload\\.',
    
    # Dimension patterns (from image info)
    r'\\(\\d+x\\d+\\)',  # (1280x802)
    r'\\d{3,4}\\*\\d{3,4}',  # 600*772
    
    # Common screenshot artifacts
    r'Adobe Acrobat',
    r'PDF Reader',
    r'Microsoft Edge',
    r'Google Chrome',
    r'Preview',
]

# Compile patterns for efficiency
COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in ARTIFACT_PATTERNS]


def filter_artifacts(text):
    """
    Remove screenshot artifacts and noise from OCR text.
    
    Args:
        text (str): Raw OCR-extracted text
    
    Returns:
        str: Cleaned text with artifacts removed
    """
    if not text:
        return text
    
    cleaned_text = text
    
    # Remove each artifact pattern
    for pattern in COMPILED_PATTERNS:
        cleaned_text = pattern.sub('', cleaned_text)
    
    # Clean up multiple spaces and empty lines
    cleaned_text = re.sub(r'\\s{2,}', ' ', cleaned_text)  # Multiple spaces to single
    cleaned_text = re.sub(r'\\n\\s*\\n', '\\n', cleaned_text)  # Multiple blank lines
    cleaned_text = cleaned_text.strip()
    
    return cleaned_text


def filter_text_for_confidence(text):
    """
    Filter text specifically for confidence calculation.
    
    This is more aggressive than filter_artifacts() and removes:
    - All file paths and URLs
    - Timestamps and dates not part of document content
    - Single characters and noise
    - Very short words that are likely OCR errors
    
    Args:
        text (str): Raw OCR-extracted text
    
    Returns:
        str: Filtered text for confidence calculation
    """
    if not text:
        return text
    
    # First pass: remove obvious artifacts
    cleaned = filter_artifacts(text)
    
    # Second pass: remove lines that are mostly noise
    lines = cleaned.split('\\n')
    meaningful_lines = []
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Skip lines that are mostly special characters
        alpha_count = sum(1 for c in line if c.isalpha())
        if len(line) > 0 and alpha_count / len(line) < 0.3:
            continue
        
        # Skip lines that are just numbers and symbols (likely noise)
        if re.match(r'^[\\d\\s\\W]+$', line) and len(line) < 10:
            continue
        
        meaningful_lines.append(line)
    
    return '\\n'.join(meaningful_lines)


def has_artifacts(text):
    """
    Check if text contains screenshot artifacts.
    
    Args:
        text (str): Text to check
    
    Returns:
        bool: True if artifacts detected, False otherwise
    """
    if not text:
        return False
    
    for pattern in COMPILED_PATTERNS:
        if pattern.search(text):
            return True
    
    return False


def get_artifact_types(text):
    """
    Identify which types of artifacts are present in the text.
    
    Args:
        text (str): Text to analyze
    
    Returns:
        list: List of artifact type descriptions found
    """
    if not text:
        return []
    
    artifact_types = []
    
    # Check for file paths
    if re.search(r'file:///', text, re.IGNORECASE):
        artifact_types.append('File path (file:///)')
    if re.search(r'[A-Za-z]:\\\\', text):
        artifact_types.append('Windows path (C:\\\\)')
    
    # Check for URLs
    if re.search(r'https?://', text, re.IGNORECASE):
        artifact_types.append('URL')
    
    # Check for timestamps
    if re.search(r'\\d{1,2}/\\d{1,2}/\\d{2,4}', text):
        artifact_types.append('Timestamp')
    
    # Check for image file names
    if re.search(r'\\.(png|jpg|jpeg)\\s*\\(\\d+x\\d+\\)', text, re.IGNORECASE):
        artifact_types.append('Image filename with dimensions')
    
    # Check for browser artifacts
    if re.search(r'storyblok|wikimedia|upload\\.', text, re.IGNORECASE):
        artifact_types.append('Web/browser content')
    
    return artifact_types
