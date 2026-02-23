"""
================================================================================
DOCUMENT READABILITY CHECK UTILITY
================================================================================

Test utility to run readability checks on a folder of documents.
Scans for PDF and image files, runs OCR confidence checks, and outputs results.

================================================================================
CONFIGURATION (Edit these values to change defaults)
================================================================================
"""

# Default thresholds (updated based on dataset analysis)
DEFAULT_READABILITY_THRESHOLD = 15  # OCR confidence threshold (0-100)
                                    # Lowered from 40 to 15 based on dataset analysis
                                    # 15 = Accepts Italian IDs & degraded documents
                                    # 25 = Balanced for mixed document types
                                    # 30 = Strict (only clear documents)
                                    # 40 = Too strict (rejects most documents)

DEFAULT_EMPTINESS_THRESHOLD = 0.5   # Ink ratio percentage threshold (0-10%)
                                    # Higher = stricter (e.g., 2.0 = pages with <2% ink are empty)
                                    # Lower = more lenient (e.g., 0.1 = only truly blank pages)
                                    # 0.5 = balanced (default in app.py)

# Output settings
DEFAULT_OUTPUT_FORMAT = 'html'      # 'html' or 'txt'
DEFAULT_OUTPUT_FOLDER = '.'         # Default output folder ('.' = current directory)

# File extensions to process
SUPPORTED_EXTENSIONS = ['.pdf', '.png', '.jpg', '.jpeg']

# OCR settings
OCR_MODE = 'fast'  # 'superfast', 'fast', 'balanced', or 'accurate'
                   # 'superfast' = quickest but less accurate
                   # 'fast' = good balance (recommended)
                   # 'accurate' = slowest but most accurate

# Debug settings
SHOW_FULL_TEXT = True  # Show full extracted text in output (for debugging)
                       # True = Show all extracted OCR text (useful for debugging language detection issues)
                       # False = Show only first 200 characters (cleaner output)
                       # Can be overridden with --full-text command line flag

"""
================================================================================
SAMPLE COMMANDS (Uncomment and modify as needed)
================================================================================

# Basic usage - scan folder with default settings
python test_readability.py ./dataset

# Include subfolders (recursive)
python test_readability.py ./dataset --recursive

# Verbose mode (show detailed progress)
python test_readability.py ./dataset -v

# Custom thresholds (readability=50%, emptiness=0.3%)
python test_readability.py ./dataset --threshold 50 --emptiness-threshold 0.3

# Custom output file (HTML format)
python test_readability.py ./dataset -o results.html

# Custom output file (TXT format)
python test_readability.py ./dataset -o results.txt

# All options combined
python test_readability.py ./dataset -r -v -t 45 -e 0.5 -o my_results.html

# Scan specific folder with full path (use forward slashes or escape backslashes)
python test_readability.py C:/Users/YourName/Documents/Scans -r -o report.html
python test_readability.py C:\\Users\\YourName\\Documents\\Scans -r -o report.html

================================================================================
"""

import os
import sys
import argparse
import pytesseract
import textwrap
from PIL import Image
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from checks.confidence_check import calculate_ocr_confidence
from checks.clarity_check import calculate_ink_ratio
from utils.document_processor import extract_page_data

# Default thresholds (updated based on dataset analysis)
DEFAULT_READABILITY_THRESHOLD = 15  # OCR confidence threshold (lowered from 40)
DEFAULT_EMPTINESS_THRESHOLD = 0.5   # Ink ratio percentage


def check_tesseract_availability():
    """Check if Tesseract OCR is available."""
    try:
        version = pytesseract.get_tesseract_version()
        print(f"[OK] Tesseract version: {version}")
        return True
    except Exception as e:
        print(f"[ERROR] Tesseract not available: {e}")
        return False


def configure_tesseract():
    """Configure Tesseract path for Windows if needed."""
    if os.name == 'nt':  # Windows
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Tesseract-OCR\tesseract.exe'
        ]

        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                print(f"[OK] Tesseract path set to: {path}")
                return True

        import shutil
        tesseract_path = shutil.which('tesseract')
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            print(f"[OK] Tesseract found in PATH: {tesseract_path}")
            return True

        print("[WARNING] Tesseract is not installed or not in PATH.")
        return False
    return True


def get_files_in_folder(folder_path, extensions=None, recursive=False):
    """
    Get all files with specified extensions in a folder.

    Args:
        folder_path: Path to the folder
        extensions: List of file extensions to include (default: SUPPORTED_EXTENSIONS)
        recursive: If True, search subfolders recursively

    Returns:
        list: List of file paths (deduplicated)
    """
    if extensions is None:
        extensions = SUPPORTED_EXTENSIONS

    files = set()  # Use set to automatically deduplicate
    folder = Path(folder_path)

    for ext in extensions:
        if recursive:
            # Search recursively in subfolders (case-insensitive)
            files.update(folder.rglob(f'*{ext}'))
        else:
            # Search only in top-level folder (case-insensitive)
            files.update(folder.glob(f'*{ext}'))

    return sorted(files)


def process_file(file_path, readability_threshold=DEFAULT_READABILITY_THRESHOLD, emptiness_threshold=DEFAULT_EMPTINESS_THRESHOLD, verbose=False, primary_language='ita', auto_detect=True):
    """
    Process a single file and return readability metrics.

    Args:
        file_path: Path to the file
        readability_threshold: OCR confidence threshold for readability (default: 15)
        emptiness_threshold: Ink ratio percentage threshold for emptiness (default: 0.5%)
        verbose: If True, print detailed progress
        primary_language: Primary OCR language (default: 'ita' for Italian)
        auto_detect: If True, auto-detect language from content (default: True)

    Returns:
        list: List of dicts with page metrics
    """
    results = []
    file_name = os.path.basename(file_path)
    parent_folder = os.path.basename(os.path.dirname(file_path))

    try:
        if verbose:
            if parent_folder:
                print(f"  [FILE] Processing: {parent_folder}/{file_name}")
            else:
                print(f"  [FILE] Processing: {file_name}")
        else:
            if parent_folder:
                print(f"  [FILE] {parent_folder}/{file_name}...", end=" ", flush=True)
            else:
                print(f"  [FILE] {file_name}...", end=" ", flush=True)

        # Read file
        with open(file_path, 'rb') as f:
            file_bytes = f.read()

        # Extract pages with language configuration
        page_data, _ = extract_page_data(file_bytes, file_name, primary_language=primary_language, auto_detect=auto_detect)

        if verbose:
            print(f"     Found {len(page_data)} page(s)")

        for page_info in page_data:
            page_num = page_info['page']

            # Use pre-calculated metrics from extract_page_data (avoids double analysis)
            ocr_conf = page_info.get('ocr_conf', 0.0)
            ink_ratio = page_info.get('ink_ratio', 0.0)

            # Determine if readable (same logic as app.py)
            is_readable = ocr_conf >= readability_threshold

            # Determine if empty (same logic as app.py: ink_ratio_pct < emptiness_threshold)
            # Note: emptiness_threshold is already in percentage (e.g., 0.5 means 0.5%)
            ink_ratio_pct = ink_ratio * 100
            is_empty = ink_ratio_pct < emptiness_threshold

            results.append({
                'file': file_name,
                'folder': parent_folder if parent_folder else '(root)',
                'page': page_num,
                'confidence': ocr_conf,
                'readable': is_readable,
                'empty': is_empty,
                'ink_ratio': ink_ratio_pct,
                'language': page_info.get('detected_language', 'eng'),
                'text_content': page_info.get('text_content', '') if SHOW_FULL_TEXT else page_info.get('text_content', '')[:200]  # Full text or first 200 chars
            })

            if verbose:
                status = "[OK] Readable" if is_readable else "[FAIL] Not Readable"
                empty_status = "Empty" if is_empty else "Not Empty"
                lang = page_info.get('detected_language', 'eng')
                print(f"    +-- Page {page_num}: {status}, {empty_status} (Conf: {ocr_conf:.2f}, Ink: {ink_ratio_pct:.2f}%, Lang: {lang})")
                
                # Show extracted text in verbose mode
                if SHOW_FULL_TEXT:
                    text_content = page_info.get('text_content', '')
                    if text_content:
                        print(f"    |   Extracted Text:")
                        # Wrap text to 100 chars for readability
                        wrapped = textwrap.fill(text_content, width=100)
                        for line in wrapped.split('\n'):
                            print(f"    |   {line}")
                    else:
                        print(f"    |   (No text extracted)")

        if not verbose:
            status = f"[OK] {len(page_data)} page(s)" if results else "[FAIL] Error"
            print(status)

    except Exception as e:
        if verbose:
            print(f"  [ERROR] Error processing {file_name}: {str(e)}")
        else:
            print(f"[FAIL]")
        results.append({
            'file': file_name,
            'folder': parent_folder if parent_folder else '(root)',
            'page': 'N/A',
            'confidence': 0.0,
            'readable': False,
            'empty': False,
            'ink_ratio': 0.0,
            'error': str(e)
        })

    return results


def write_html_output(output_path, folder_path, all_results, duration, readability_threshold, emptiness_threshold):
    """
    Write results to an HTML file with detailed page-wise reporting and document viewer.

    Args:
        output_path: Path to output HTML file
        folder_path: Scanned folder path
        all_results: List of result dictionaries
        duration: Processing time in seconds
        readability_threshold: Readability threshold used
        emptiness_threshold: Emptiness threshold used
    """
    # Group results by folder, then by file
    folders = {}
    for result in all_results:
        folder = result['folder']
        if folder not in folders:
            folders[folder] = {}
        file_name = result['file']
        if file_name not in folders[folder]:
            folders[folder][file_name] = []
        folders[folder][file_name].append(result)

    # Calculate statistics
    readable_count = sum(1 for r in all_results if r['readable'])
    unreadable_count = len(all_results) - readable_count
    empty_count = sum(1 for r in all_results if r['empty'])
    avg_confidence = sum(r['confidence'] for r in all_results) / len(all_results) if all_results else 0

    # Count unique files
    unique_files = len(set((r['folder'], r['file']) for r in all_results))

    # Build relative paths for documents
    output_dir = os.path.dirname(os.path.abspath(output_path))
    folder_abs_path = os.path.abspath(folder_path)

    # Start building HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Readability Check Results</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0 0 20px 0;
            font-size: 28px;
        }}
        .stats {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }}
        .stat-box {{
            background: rgba(255,255,255,0.15);
            padding: 15px 25px;
            border-radius: 8px;
            backdrop-filter: blur(10px);
        }}
        .stat-box strong {{
            font-size: 22px;
            display: block;
        }}
        .stat-box span {{
            font-size: 13px;
            opacity: 0.9;
        }}
        .folder-section {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .folder-title {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            margin: -20px -20px 20px -20px;
            font-size: 20px;
            font-weight: bold;
        }}
        .file-section {{
            background: #fafafa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }}
        .file-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        .file-name {{
            font-size: 16px;
            font-weight: bold;
            color: #333;
        }}
        .file-stats {{
            display: flex;
            gap: 15px;
        }}
        .file-stat {{
            font-size: 13px;
            padding: 4px 10px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .file-stat-total {{
            background-color: #e2e8f0;
            color: #4a5568;
        }}
        .file-stat-readable {{
            background-color: #c6f6d5;
            color: #22543d;
        }}
        .file-stat-unreadable {{
            background-color: #fed7d7;
            color: #742a2a;
        }}
        .file-stat-empty {{
            background-color: #feebc8;
            color: #744210;
        }}
        .view-btn {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: transform 0.2s, box-shadow 0.2s;
            text-decoration: none;
        }}
        .view-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }}
        .view-btn:active {{
            transform: translateY(0);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }}
        th {{
            background-color: #f0f0f0;
            font-weight: 600;
            color: #4a5568;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        tr:hover {{
            background-color: #f9f9f9;
        }}
        .status {{
            padding: 6px 14px;
            border-radius: 5px;
            font-size: 12px;
            font-weight: bold;
            display: inline-block;
            min-width: 60px;
            text-align: center;
        }}
        .status-yes {{
            background-color: #c6f6d5;
            color: #22543d;
            border: 1px solid #22543d;
        }}
        .status-no {{
            background-color: #fed7d7;
            color: #742a2a;
            border: 1px solid #742a2a;
        }}
        .confidence {{
            display: inline-block;
            width: 100px;
            height: 18px;
            background-color: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
            vertical-align: middle;
            margin-right: 8px;
        }}
        .confidence-fill {{
            height: 100%;
            transition: width 0.3s ease;
        }}
        .confidence-high {{ background-color: #48bb78; }}
        .confidence-medium {{ background-color: #ed8936; }}
        .confidence-low {{ background-color: #f56565; }}
        .language-badge {{
            display: inline-block;
            padding: 3px 8px;
            background-color: #e2e8f0;
            color: #4a5568;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .text-preview {{
            max-width: 600px;
            max-height: 150px;
            overflow-y: auto;
            font-size: 11px;
            color: #666;
            font-style: italic;
            white-space: pre-wrap;
            word-wrap: break-word;
            line-height: 1.4;
            background-color: #f9f9f9;
            padding: 8px;
            border-radius: 4px;
            border: 1px solid #e0e0e0;
        }}
        .text-preview-full {{
            max-width: 800px;
            font-size: 11px;
            color: #555;
            font-family: 'Consolas', 'Monaco', monospace;
            white-space: pre-wrap;
            word-wrap: break-word;
            line-height: 1.5;
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 4px;
            border: 1px solid #ddd;
            overflow-y:scroll;
            max-height: 100px;
        }}
        .text-label {{
            font-size: 10px;
            font-weight: 600;
            color: #888;
            text-transform: uppercase;
            margin-bottom: 4px;
        }}
        .error {{
            color: #e53e3e;
            font-size: 12px;
            font-style: italic;
        }}
        .legend {{
            background: white;
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .legend-title {{
            font-weight: bold;
            margin-bottom: 10px;
            color: #4a5568;
        }}
        .legend-items {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 3px;
        }}
        .footer {{
            text-align: center;
            padding: 25px;
            color: #666;
            font-size: 13px;
            border-top: 1px solid #e0e0e0;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Document Readability Check Results</h1>
        <div class="stats">
            <div class="stat-box"><strong>{len(all_results)}</strong><span>Total Pages</span></div>
            <div class="stat-box"><strong>{unique_files}</strong><span>Files</span></div>
            <div class="stat-box"><strong>{readable_count}</strong><span>Readable</span></div>
            <div class="stat-box"><strong>{unreadable_count}</strong><span>Unreadable</span></div>
            <div class="stat-box"><strong>{empty_count}</strong><span>Empty</span></div>
            <div class="stat-box"><strong>{avg_confidence:.2f}</strong><span>Avg Confidence</span></div>
            <div class="stat-box"><strong>{duration:.1f}s</strong><span>Duration</span></div>
        </div>
    </div>

    <div class="legend">
        <div class="legend-title">Legend</div>
        <div class="legend-items">
            <div class="legend-item"><div class="legend-color" style="background: #48bb78;"></div> High Confidence (&ge;50%)</div>
            <div class="legend-item"><div class="legend-color" style="background: #ed8936;"></div> Medium Confidence (30-50%)</div>
            <div class="legend-item"><div class="legend-color" style="background: #f56565;"></div> Low Confidence (&lt;30%)</div>
            <div class="legend-item"><span class="status status-yes">Yes</span> Passes Check</div>
            <div class="legend-item"><span class="status status-no">No</span> Fails Check</div>
        </div>
    </div>

"""

    for folder_name, files in sorted(folders.items()):
        html_content += f"""    <div class="folder-section">
        <div class="folder-title">Folder: {folder_name}</div>
"""
        for file_name, file_results in sorted(files.items()):
            # Calculate per-file statistics
            file_readable = sum(1 for r in file_results if r['readable'])
            file_unreadable = len(file_results) - file_readable
            file_empty = sum(1 for r in file_results if r['empty'])
            file_total = len(file_results)
            file_avg_conf = sum(r['confidence'] for r in file_results) / len(file_results) if file_results else 0

            # Build actual file path including subfolder
            if folder_name and folder_name != '(root)':
                actual_file_path = os.path.join(folder_abs_path, folder_name, file_name)
                # Also create relative path from output file location
                rel_path = os.path.relpath(actual_file_path, output_dir)
            else:
                actual_file_path = os.path.join(folder_abs_path, file_name)
                rel_path = os.path.relpath(actual_file_path, output_dir)

            # Use relative path for better browser compatibility
            doc_path = rel_path.replace('\\', '/')
            full_path = actual_file_path.replace('\\', '/')

            # Escape quotes in paths for JavaScript
            doc_path_escaped = doc_path.replace("'", "\\'")
            full_path_escaped = full_path.replace("'", "\\'")
            file_name_escaped = file_name.replace("'", "\\'")
            folder_name_escaped = folder_name.replace("'", "\\'")

            html_content += f"""        <div class="file-section">
            <div class="file-header">
                <div class="file-name">File: {file_name}</div>
                <div style="display: flex; align-items: center; gap: 15px;">
                    <div class="file-stats">
                        <span class="file-stat file-stat-total">Total: {file_total}</span>
                        <span class="file-stat file-stat-readable">Readable: {file_readable}</span>
                        <span class="file-stat file-stat-unreadable">Unreadable: {file_unreadable}</span>
                        <span class="file-stat file-stat-empty">Empty: {file_empty}</span>
                    </div>
                    <a href="{doc_path}" target="_blank" class="view-btn" title="Open {file_name}">
                        Open Document
                    </a>
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th style="width: 60px;">Page</th>
                        <th style="width: 80px;">View</th>
                        <th style="width: 80px;">Empty</th>
                        <th style="width: 80px;">Readable</th>
                        <th style="width: 130px;">Confidence</th>
                        <th style="width: 90px;">Ink Ratio %</th>
                        <th style="width: 60px;">Lang</th>
                        <th style="width: 400px;">{'Extracted Text (Full)' if SHOW_FULL_TEXT else 'Text Preview'}</th>
                    </tr>
                </thead>
                <tbody>
"""
            for result in file_results:
                page = str(result['page'])
                empty = result['empty']
                readable = result['readable']
                confidence = result['confidence']
                ink_ratio = result['ink_ratio']
                language = result.get('language', 'eng')
                text_preview = result.get('text_content', '')

                if confidence >= 50:
                    conf_class = 'confidence-high'
                elif confidence >= 30:
                    conf_class = 'confidence-medium'
                else:
                    conf_class = 'confidence-low'

                if 'error' in result:
                    html_content += f"""                    <tr>
                        <td colspan="8" class="error">Error: Page {page}: {result['error']}</td>
                    </tr>
"""
                else:
                    # Determine status classes
                    empty_class = "status-yes" if empty else "status-no"
                    empty_text = "Yes" if empty else "No"
                    readable_class = "status-yes" if readable else "status-no"
                    readable_text = "Yes" if readable else "No"

                    # Escape text preview for HTML
                    text_preview_escaped = text_preview.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;') if text_preview else '(No text detected)'
                    
                    # Use full text style if SHOW_FULL_TEXT is enabled
                    text_class = 'text-preview-full' if SHOW_FULL_TEXT else 'text-preview'
                    text_label = '<div class="text-label">EXTRACTED TEXT (FULL):</div>' if SHOW_FULL_TEXT else ''

                    html_content += f"""                    <tr>
                        <td><strong>#{page}</strong></td>
                        <td>
                            <a href="{doc_path}#page={page}" target="_blank" class="view-btn" style="padding: 4px 10px; font-size: 11px;" title="View page {page} of {file_name}">
                                View
                            </a>
                        </td>
                        <td><span class="status {empty_class}">{empty_text}</span></td>
                        <td><span class="status {readable_class}">{readable_text}</span></td>
                        <td>
                            <div class="confidence">
                                <div class="confidence-fill {conf_class}" style="width: {min(confidence, 100)}%;"></div>
                            </div>
                            {confidence:.2f}
                        </td>
                        <td>{ink_ratio:.2f}%</td>
                        <td><span class="language-badge">{language}</span></td>
                        <td><div class="{text_class}">{text_label}{text_preview_escaped}</div></td>
                    </tr>
"""

            html_content += """                </tbody>
            </table>
        </div>
"""

        html_content += """    </div>
"""

    html_content += f"""
    <div class="footer">
        <div><strong>Report Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        <div style="margin-top: 8px;"><strong>Thresholds Used:</strong> Readability &ge; {readability_threshold}% | Emptiness &lt; {emptiness_threshold}%</div>
        <div style="margin-top: 8px; font-size: 12px;"><strong>Note:</strong> Each document was analyzed page-by-page. OCR confidence and ink ratio were calculated once per page.</div>
    </div>
</body>
</html>
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)


def write_txt_output(output_path, folder_path, all_results, duration, readability_threshold, emptiness_threshold, files_count):
    """
    Write results to a text file with detailed page-wise reporting.

    Args:
        output_path: Path to output TXT file
        folder_path: Scanned folder path
        all_results: List of result dictionaries
        duration: Processing time in seconds
        readability_threshold: Readability threshold used
        emptiness_threshold: Emptiness threshold used
        files_count: Number of files processed
    """
    # Group results by folder, then by file
    folders = {}
    for result in all_results:
        folder = result['folder']
        if folder not in folders:
            folders[folder] = {}
        file_name = result['file']
        if file_name not in folders[folder]:
            folders[folder][file_name] = []
        folders[folder][file_name].append(result)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 100 + "\n")
        f.write("                         DOCUMENT READABILITY CHECK RESULTS\n")
        f.write("=" * 100 + "\n\n")

        f.write(f"Folder Scanned: {folder_path}\n")
        f.write(f"Readability Threshold: {readability_threshold}%\n")
        f.write(f"Emptiness Threshold: {emptiness_threshold}%\n")
        f.write(f"Files Processed: {files_count}\n")
        f.write(f"Total Pages: {len(all_results)}\n")
        f.write(f"Execution Time: {duration:.2f} seconds\n")
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("\n" + "-" * 100 + "\n\n")

        # Summary statistics
        readable_count = sum(1 for r in all_results if r['readable'])
        unreadable_count = len(all_results) - readable_count
        empty_count = sum(1 for r in all_results if r['empty'])
        avg_confidence = sum(r['confidence'] for r in all_results) / len(all_results) if all_results else 0

        f.write("SUMMARY\n")
        f.write("-" * 60 + "\n")
        f.write(f"  Total Pages:        {len(all_results)}\n")
        f.write(f"  Readable Pages:     {readable_count} ({readable_count/len(all_results)*100:.1f}%)\n")
        f.write(f"  Unreadable Pages:   {unreadable_count} ({unreadable_count/len(all_results)*100:.1f}%)\n")
        f.write(f"  Empty Pages:        {empty_count} ({empty_count/len(all_results)*100:.1f}%)\n")
        f.write(f"  Average Confidence: {avg_confidence:.2f}\n")
        f.write("\n" + "-" * 100 + "\n\n")

        # Detailed results grouped by folder and file
        f.write("DETAILED PAGE-WISE RESULTS\n")
        f.write("=" * 100 + "\n\n")

        for folder_name, files in sorted(folders.items()):
            f.write(f"\n{'='*80}\n")
            f.write(f"FOLDER: {folder_name}\n")
            f.write(f"{'='*80}\n")

            for file_name, file_results in sorted(files.items()):
                # Calculate per-file statistics
                file_readable = sum(1 for r in file_results if r['readable'])
                file_unreadable = len(file_results) - file_readable
                file_empty = sum(1 for r in file_results if r['empty'])
                file_total = len(file_results)
                file_avg_conf = sum(r['confidence'] for r in file_results) / len(file_results) if file_results else 0

                f.write(f"\n  📄 FILE: {file_name}\n")
                f.write(f"     {'─' * 70}\n")
                f.write(f"     File Summary: {file_total} pages | Readable: {file_readable} | Unreadable: {file_unreadable} | Empty: {file_empty} | Avg Conf: {file_avg_conf:.2f}\n\n")

                # Page-wise table header
                f.write(f"     {'Page':<6} {'Empty':<8} {'Readable':<10} {'Confidence':<14} {'Ink %':<10} {'Lang':<6} {'Text Preview'}\n")
                f.write(f"     {'─' * 6} {'─' * 8} {'─' * 10} {'─' * 14} {'─' * 10} {'─' * 6} {'─' * 40}\n")

                for result in file_results:
                    page = str(result['page'])
                    empty = "Yes" if result['empty'] else "No"
                    readable = "Yes" if result['readable'] else "No"
                    confidence = f"{result['confidence']:.2f}"
                    ink_ratio = f"{result['ink_ratio']:.2f}"
                    language = result.get('language', 'eng')[:3].upper()
                    text_preview = result.get('text_content', '')

                    if 'error' in result:
                        f.write(f"     ⚠️ ERROR (Page {page}): {result['error']}\n")
                    else:
                        # Truncate text preview for TXT output
                        preview_text = (text_preview[:40] + '...') if text_preview and len(text_preview) > 40 else (text_preview if text_preview else '(No text)')
                        # Clean preview text of newlines
                        preview_text = preview_text.replace('\n', ' ').replace('\r', '')
                        f.write(f"     {page:<6} {empty:<8} {readable:<10} {confidence:<14} {ink_ratio:<10} {language:<6} {preview_text}\n")

                f.write(f"     {'─' * 70}\n")

            f.write("\n")

        # List unreadable pages
        unreadable_results = [r for r in all_results if not r['readable']]
        if unreadable_results:
            f.write("\n" + "=" * 100 + "\n")
            f.write("UNREADABLE PAGES (Action Required)\n")
            f.write("=" * 100 + "\n\n")
            for result in unreadable_results:
                folder = result['folder']
                f.write(f"  ❌ {folder}/{result['file']} (Page {result['page']})\n")
                f.write(f"     Confidence: {result['confidence']:.2f}% | Ink Ratio: {result['ink_ratio']:.2f}%\n")
                if 'error' in result:
                    f.write(f"     Error: {result['error']}\n")
                f.write("\n")

        # List empty pages
        empty_results = [r for r in all_results if r['empty']]
        if empty_results:
            f.write("\n" + "=" * 100 + "\n")
            f.write("EMPTY PAGES (Possible Blank Pages)\n")
            f.write("=" * 100 + "\n\n")
            for result in empty_results:
                folder = result['folder']
                f.write(f"  ⚪ {folder}/{result['file']} (Page {result['page']})\n")
                f.write(f"     Ink Ratio: {result['ink_ratio']:.2f}% (below {emptiness_threshold}% threshold)\n")
                f.write("\n")

        f.write("\n" + "=" * 100 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 100 + "\n")
        f.write("\nNote: Each document was analyzed page-by-page. OCR confidence and ink ratio were calculated once per page.\n")


def run_readability_check(folder_path, output_file=None, readability_threshold=DEFAULT_READABILITY_THRESHOLD, emptiness_threshold=DEFAULT_EMPTINESS_THRESHOLD, recursive=False, verbose=False, auto_open=False, primary_language='ita', auto_detect=True):
    """
    Run readability checks on all files in a folder.

    Args:
        folder_path: Path to the folder containing documents
        output_file: Path to output text file (default: readability_results_<timestamp>.txt)
        readability_threshold: OCR confidence threshold (0-100, default: 15)
        emptiness_threshold: Ink ratio percentage threshold (0-10, default: 0.5)
        recursive: If True, search subfolders recursively
        verbose: If True, print detailed progress
        auto_open: If True, automatically open HTML output in browser
        primary_language: Primary OCR language (default: 'ita' for Italian)
        auto_detect: If True, auto-detect language from content (default: True)

    Returns:
        tuple: (all_results, output_path)
    """
    print(f"\n{'='*60}")
    print("Document Readability Check Utility")
    print(f"{'='*60}\n")

    # Configure Tesseract
    configure_tesseract()
    tesseract_available = check_tesseract_availability()

    if not tesseract_available:
        print("\n[WARNING] Tesseract OCR is not available.")
        print("Readability checks will be limited.\n")

    # Validate folder
    folder = Path(folder_path)
    if not folder.exists():
        print(f"[ERROR] Folder '{folder_path}' does not exist.")
        sys.exit(1)

    if not folder.is_dir():
        print(f"[ERROR] '{folder_path}' is not a directory.")
        sys.exit(1)

    print(f"Folder: {folder.absolute()}")
    print(f"Readability Threshold: {readability_threshold}%")
    print(f"Emptiness Threshold: {emptiness_threshold}%")
    print(f"Recursive: {'Yes (include subfolders)' if recursive else 'No (top-level only)'}")
    print(f"Output File: {output_file if output_file else 'report/ (auto-generated with ID and timestamp)'}")
    print(f"Primary Language: {primary_language.upper()}")
    print(f"Auto-Detect: {'Yes' if auto_detect else 'No (use primary only)'}\n")

    # Get files
    files = get_files_in_folder(folder_path, recursive=recursive)

    if not files:
        print("[ERROR] No PDF or image files found in the folder.")
        sys.exit(0)

    print(f"Found {len(files)} file(s) to process:\n")
    for f in files:
        print(f"  - {f.name}")
    print()

    # Process files
    all_results = []
    start_time = datetime.now()

    print("Processing files...")
    print("-" * 60)
    for idx, file_path in enumerate(files, 1):
        if not verbose:
            print(f"[{idx}/{len(files)}]", end=" ")
        results = process_file(file_path, readability_threshold, emptiness_threshold, verbose, primary_language, auto_detect)
        all_results.extend(results)

    print("-" * 60)
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Generate output with auto-increment ID and timestamp
    if output_file is None:
        # Create report folder if it doesn't exist
        report_folder = Path(DEFAULT_OUTPUT_FOLDER) / 'report'
        report_folder.mkdir(exist_ok=True)
        
        # Generate auto-increment ID based on existing files
        existing_reports = list(report_folder.glob('report_*.html')) + list(report_folder.glob('report_*.txt'))
        next_id = len(existing_reports) + 1
        
        # Generate timestamp with local time
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = report_folder / f'report_{next_id:03d}_{timestamp}.{DEFAULT_OUTPUT_FORMAT}'
    else:
        # If output file is specified, use it as-is
        output_file = Path(output_file)

    output_path = output_file

    # Determine output format from file extension
    output_format = output_path.suffix.lower()
    if output_format == '.html':
        # Write HTML output
        write_html_output(
            output_path, 
            folder.absolute(), 
            all_results, 
            duration, 
            readability_threshold, 
            emptiness_threshold
        )
    else:
        # Write TXT output (default)
        write_txt_output(
            output_path,
            folder.absolute(),
            all_results,
            duration,
            readability_threshold,
            emptiness_threshold,
            len(files)
        )

    # Print summary to console
    # Calculate statistics for console output
    readable_count = sum(1 for r in all_results if r['readable'])
    unreadable_count = len(all_results) - readable_count
    empty_count = sum(1 for r in all_results if r['empty'])
    avg_confidence = sum(r['confidence'] for r in all_results) / len(all_results) if all_results else 0
    unique_files = len(set(r['file'] for r in all_results))

    print(f"\n{'='*60}")
    print("RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"Total Pages Processed: {len(all_results)}")
    print(f"Readable Pages: {readable_count} ({readable_count/len(all_results)*100:.1f}%)")
    print(f"Unreadable Pages: {unreadable_count} ({unreadable_count/len(all_results)*100:.1f}%)")
    print(f"Average Confidence Score: {avg_confidence:.2f}")
    print(f"Execution Time: {duration:.2f} seconds")

    # Show empty pages info
    if empty_count > 0:
        print(f"Empty Pages: {empty_count} ({empty_count/len(all_results)*100:.1f}%)")

    # Show files processed
    print(f"Files Processed: {unique_files}")

    print(f"\n[OK] Results saved to: {output_path.absolute()}")
    print(f"     Report folder: {output_path.parent.absolute()}")

    # Auto-open HTML file in browser if requested
    if output_format == '.html' and auto_open:
        try:
            import webbrowser
            webbrowser.open(output_path.absolute().as_uri())
            print(f"[OK] Opening results in browser...")
        except Exception as e:
            print(f"[WARNING] Could not open browser: {e}")

    print(f"{'='*60}\n")

    return all_results, output_path


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Run readability checks on a folder of documents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_readability.py ./dataset
  python test_readability.py ./dataset --output results.html    (HTML format)
  python test_readability.py ./dataset --output results.txt     (TXT format)
  python test_readability.py ./dataset --threshold 50 --emptiness-threshold 0.3 --verbose
  python test_readability.py ./dataset -o my_results.html -t 45 -e 0.5 -v
  python test_readability.py ./dataset --recursive
  python test_readability.py ./dataset -r -v
  python test_readability.py ./dataset -r -v --open              (Open results in browser)
  
Language Options:
  python test_readability.py ./dataset -l ita                    (Use Italian OCR)
  python test_readability.py ./dataset -l eng                    (Use English OCR)
  python test_readability.py ./dataset --language fra            (Use French OCR)
  python test_readability.py ./dataset -l ita --no-auto-detect   (Force Italian, no detection)
        """
    )

    parser.add_argument(
        'folder',
        help='Path to the folder containing PDF/image files'
    )

    parser.add_argument(
        '-o', '--output',
        help='Output file path (default: readability_results_<timestamp>.html). Use .html or .txt extension',
        default=None
    )

    parser.add_argument(
        '-t', '--threshold',
        type=int,
        help='Readability threshold (0-100, default: 40 same as app.py)',
        default=DEFAULT_READABILITY_THRESHOLD
    )

    parser.add_argument(
        '-e', '--emptiness-threshold',
        type=float,
        help='Emptiness threshold in percentage (0-10, default: 0.5 same as app.py - means 0.5%%)',
        default=DEFAULT_EMPTINESS_THRESHOLD
    )

    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='Search subfolders recursively'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--open',
        action='store_true',
        help='Automatically open HTML results in browser after completion'
    )

    parser.add_argument(
        '-l', '--language',
        type=str,
        default='ita',
        help='Primary OCR language: eng, ita, fra, deu, spa (default: ita for Italian)'
    )

    parser.add_argument(
        '--no-auto-detect',
        action='store_false',
        dest='auto_detect',
        help='Disable automatic language detection (use primary language only)'
    )

    parser.add_argument(
        '--full-text',
        action='store_true',
        dest='full_text',
        help='Show full extracted text in output (for debugging). Overrides SHOW_FULL_TEXT config'
    )

    args = parser.parse_args()

    # Override SHOW_FULL_TEXT if --full-text flag is provided
    if args.full_text:
        global SHOW_FULL_TEXT
        SHOW_FULL_TEXT = True

    # Validate thresholds
    if args.threshold < 0 or args.threshold > 100:
        print("[ERROR] Readability threshold must be between 0 and 100.")
        sys.exit(1)

    if args.emptiness_threshold < 0 or args.emptiness_threshold > 10:
        print("[ERROR] Emptiness threshold must be between 0 and 10.")
        sys.exit(1)

    # Run the check
    run_readability_check(
        folder_path=args.folder,
        output_file=args.output,
        readability_threshold=args.threshold,
        emptiness_threshold=args.emptiness_threshold,
        recursive=args.recursive,
        verbose=args.verbose,
        auto_open=args.open,
        primary_language=args.language,
        auto_detect=args.auto_detect
    )


if __name__ == '__main__':
    main()
