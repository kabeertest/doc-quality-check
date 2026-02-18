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

# Default thresholds (same as app.py)
DEFAULT_READABILITY_THRESHOLD = 40  # OCR confidence threshold (0-100)
                                    # Higher = stricter (e.g., 60 = need clearer text)
                                    # Lower = more lenient (e.g., 20 = accept blurry text)
                                    # 40 = balanced (default in app.py)

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
from PIL import Image
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from checks.confidence_check import calculate_ocr_confidence
from checks.clarity_check import calculate_ink_ratio
from utils.document_processor import extract_page_data

# Default thresholds (same as app.py)
DEFAULT_READABILITY_THRESHOLD = 40  # OCR confidence threshold
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
        list: List of file paths
    """
    if extensions is None:
        extensions = SUPPORTED_EXTENSIONS

    files = []
    folder = Path(folder_path)

    for ext in extensions:
        if recursive:
            # Search recursively in subfolders
            files.extend(folder.rglob(f'*{ext}'))
            files.extend(folder.rglob(f'*{ext.upper()}'))
        else:
            # Search only in top-level folder
            files.extend(folder.glob(f'*{ext}'))
            files.extend(folder.glob(f'*{ext.upper()}'))

    return sorted(files)


def process_file(file_path, readability_threshold=DEFAULT_READABILITY_THRESHOLD, emptiness_threshold=DEFAULT_EMPTINESS_THRESHOLD, verbose=False):
    """
    Process a single file and return readability metrics.

    Args:
        file_path: Path to the file
        readability_threshold: OCR confidence threshold for readability (default: 40, same as app.py)
        emptiness_threshold: Ink ratio percentage threshold for emptiness (default: 0.5%, same as app.py)
        verbose: If True, print detailed progress

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

        # Extract pages
        page_data, _ = extract_page_data(file_bytes, file_name)

        if verbose:
            print(f"     Found {len(page_data)} page(s)")

        for page_info in page_data:
            page_num = page_info['page']

            # Calculate OCR confidence
            ocr_conf, conf_time = calculate_ocr_confidence(page_info['image'], mode=OCR_MODE)

            # Calculate ink ratio (for additional info)
            ink_ratio, ink_time = calculate_ink_ratio(page_info['image'])

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
                'ink_ratio': ink_ratio * 100
            })

            if verbose:
                status = "[OK] Readable" if is_readable else "[FAIL] Not Readable"
                empty_status = "Empty" if is_empty else "Not Empty"
                print(f"    +-- Page {page_num}: {status}, {empty_status} (Conf: {ocr_conf:.2f}, Ink: {ink_ratio*100:.2f}%)")

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
    Write results to an HTML file with simple formatted table.

    Args:
        output_path: Path to output HTML file
        folder_path: Scanned folder path
        all_results: List of result dictionaries
        duration: Processing time in seconds
        readability_threshold: Readability threshold used
        emptiness_threshold: Emptiness threshold used
    """
    # Group results by folder
    folders = {}
    for result in all_results:
        folder = result['folder']
        if folder not in folders:
            folders[folder] = []
        folders[folder].append(result)

    # Calculate statistics
    readable_count = sum(1 for r in all_results if r['readable'])
    unreadable_count = len(all_results) - readable_count
    empty_count = sum(1 for r in all_results if r['empty'])
    avg_confidence = sum(r['confidence'] for r in all_results) / len(all_results) if all_results else 0

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Readability Check Results</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: #667eea;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0 0 15px 0;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}
        .stat-box {{
            background: rgba(255,255,255,0.2);
            padding: 10px 20px;
            border-radius: 5px;
        }}
        .stat-box strong {{
            font-size: 18px;
        }}
        .folder-section {{
            background: white;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .folder-title {{
            background-color: #667eea;
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            margin: -15px -15px 15px -15px;
            font-size: 18px;
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }}
        th {{
            background-color: #f0f0f0;
            font-weight: bold;
        }}
        tr:hover {{
            background-color: #f9f9f9;
        }}
        .status {{
            padding: 5px 12px;
            border-radius: 4px;
            font-size: 13px;
            font-weight: bold;
            display: inline-block;
            min-width: 50px;
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
            width: 80px;
            height: 15px;
            background-color: #e0e0e0;
            border-radius: 3px;
            overflow: hidden;
            vertical-align: middle;
            margin-right: 8px;
        }}
        .confidence-fill {{
            height: 100%;
        }}
        .confidence-high {{ background-color: #48bb78; }}
        .confidence-medium {{ background-color: #ed8936; }}
        .confidence-low {{ background-color: #f56565; }}
        .error {{
            color: #e53e3e;
            font-size: 12px;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📄 Document Readability Check Results</h1>
        <div class="stats">
            <div class="stat-box"><strong>{len(all_results)}</strong> Total Pages</div>
            <div class="stat-box"><strong>{readable_count}</strong> Readable</div>
            <div class="stat-box"><strong>{unreadable_count}</strong> Unreadable</div>
            <div class="stat-box"><strong>{empty_count}</strong> Empty</div>
            <div class="stat-box"><strong>{avg_confidence:.2f}</strong> Avg Confidence</div>
            <div class="stat-box"><strong>{duration:.1f}s</strong> Duration</div>
        </div>
    </div>
"""

    for folder_name, folder_results in sorted(folders.items()):
        html_content += f"""    <div class="folder-section">
        <div class="folder-title">📁 {folder_name}</div>
        <table>
            <thead>
                <tr>
                    <th>File</th>
                    <th>Page</th>
                    <th>Empty</th>
                    <th>Readable</th>
                    <th>Confidence</th>
                    <th>Ink Ratio %</th>
                </tr>
            </thead>
            <tbody>
"""
        for result in folder_results:
            file_name = result['file']
            page = str(result['page'])
            empty = result['empty']
            readable = result['readable']
            confidence = result['confidence']
            ink_ratio = result['ink_ratio']

            if confidence >= 50:
                conf_class = 'confidence-high'
            elif confidence >= 30:
                conf_class = 'confidence-medium'
            else:
                conf_class = 'confidence-low'

            if 'error' in result:
                html_content += f"""                <tr>
                    <td colspan="6" class="error">⚠️ {file_name} (Page {page}): {result['error']}</td>
                </tr>
"""
            else:
                html_content += f"""                <tr>
                    <td>{file_name}</td>
                    <td>{page}</td>
                    <td><span class="status {"status-yes" if empty else "status-no"}'>{"Yes" if empty else "No"}</span></td>
                    <td><span class="status {"status-yes" if readable else "status-no"}'>{"Yes" if readable else "No"}</span></td>
                    <td>
                        <div class="confidence">
                            <div class="confidence-fill {conf_class}" style="width: {min(confidence, 100)}%;"></div>
                        </div>
                        {confidence:.2f}
                    </td>
                    <td>{ink_ratio:.2f}</td>
                </tr>
"""

        html_content += """            </tbody>
        </table>
    </div>
"""

    html_content += f"""    <div class="footer">
        Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Threshold: Readability ≥ {readability_threshold}%, Emptiness &lt; {emptiness_threshold}%
    </div>
</body>
</html>
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)


def write_txt_output(output_path, folder_path, all_results, duration, readability_threshold, emptiness_threshold, files_count):
    """
    Write results to a text file.

    Args:
        output_path: Path to output TXT file
        folder_path: Scanned folder path
        all_results: List of result dictionaries
        duration: Processing time in seconds
        readability_threshold: Readability threshold used
        emptiness_threshold: Emptiness threshold used
        files_count: Number of files processed
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("DOCUMENT READABILITY CHECK RESULTS\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Folder Scanned: {folder_path}\n")
        f.write(f"Readability Threshold: {readability_threshold}%\n")
        f.write(f"Emptiness Threshold: {emptiness_threshold}%\n")
        f.write(f"Files Processed: {files_count}\n")
        f.write(f"Total Pages: {len(all_results)}\n")
        f.write(f"Execution Time: {duration:.2f} seconds\n")
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("\n" + "-" * 80 + "\n\n")

        # Summary statistics
        readable_count = sum(1 for r in all_results if r['readable'])
        unreadable_count = len(all_results) - readable_count
        avg_confidence = sum(r['confidence'] for r in all_results) / len(all_results) if all_results else 0

        f.write("SUMMARY\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total Pages: {len(all_results)}\n")
        f.write(f"Readable Pages: {readable_count} ({readable_count/len(all_results)*100:.1f}%)\n")
        f.write(f"Unreadable Pages: {unreadable_count} ({unreadable_count/len(all_results)*100:.1f}%)\n")
        f.write(f"Average Confidence: {avg_confidence:.2f}\n")
        f.write("\n" + "-" * 80 + "\n\n")

        # Detailed results
        f.write("DETAILED RESULTS\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'Folder':<18} {'File':<22} {'Page':<6} {'Empty':<8} {'Readable':<10} {'Confidence':<12} {'Ink%':<8}\n")
        f.write("-" * 90 + "\n")

        for result in all_results:
            folder = result['folder'][:16] + '..' if len(result['folder']) > 18 else result['folder']
            file_name = result['file'][:20] + '..' if len(result['file']) > 22 else result['file']
            page = str(result['page'])
            empty = "Yes" if result['empty'] else "No"
            readable = "[YES]" if result['readable'] else "[NO] "
            confidence = f"{result['confidence']:.1f}"
            ink_ratio = f"{result['ink_ratio']:.1f}"

            f.write(f"{folder:<18} {file_name:<22} {page:<6} {empty:<8} {readable:<10} {confidence:<12} {ink_ratio:<8}\n")

            if 'error' in result:
                f.write(f"  Error: {result['error']}\n")

        f.write("-" * 80 + "\n")

        # List unreadable files
        unreadable_results = [r for r in all_results if not r['readable']]
        if unreadable_results:
            f.write("\nUNREADABLE PAGES\n")
            f.write("-" * 80 + "\n")
            for result in unreadable_results:
                folder = result['folder']
                f.write(f"  - {folder}/{result['file']} (Page {result['page']}): Confidence = {result['confidence']:.2f}\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 80 + "\n")


def run_readability_check(folder_path, output_file=None, readability_threshold=DEFAULT_READABILITY_THRESHOLD, emptiness_threshold=DEFAULT_EMPTINESS_THRESHOLD, recursive=False, verbose=False):
    """
    Run readability checks on all files in a folder.

    Args:
        folder_path: Path to the folder containing documents
        output_file: Path to output text file (default: readability_results_<timestamp>.txt)
        readability_threshold: OCR confidence threshold (0-100, default: 40 same as app.py)
        emptiness_threshold: Ink ratio percentage threshold (0-10, default: 0.5 same as app.py)
        recursive: If True, search subfolders recursively
        verbose: If True, print detailed progress

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
    print(f"Output File: {output_file if output_file else 'readability_results_<timestamp>.txt'}\n")

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
        results = process_file(file_path, readability_threshold, emptiness_threshold, verbose)
        all_results.extend(results)

    print("-" * 60)
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Generate output
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"readability_results_{timestamp}.{DEFAULT_OUTPUT_FORMAT}"

    output_path = Path(output_file)

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

    args = parser.parse_args()

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
        verbose=args.verbose
    )


if __name__ == '__main__':
    main()
