from app import extract_page_data
import os

# Debug script to check confidence scores for dataset files
dataset_path = os.path.join(os.getcwd(), 'dataset')

# Test empty PDF
print("=== Testing Empty PDF ===")
empty_pdf_path = os.path.join(dataset_path, 'empty-pdfs', 'blank.pdf')
if os.path.exists(empty_pdf_path):
    with open(empty_pdf_path, 'rb') as f:
        file_bytes = f.read()
    page_data = extract_page_data(file_bytes, 'blank.pdf')
    for page_info in page_data:
        print(f"Empty PDF - Page {page_info['page']}: Ink Ratio={page_info['ink_ratio']:.4f}, OCR Conf={page_info['ocr_conf']:.2f}")
else:
    print("Empty PDF file not found")

# Test unclear PDF
print("\n=== Testing Unclear PDF ===")
unclear_pdf_path = os.path.join(dataset_path, 'unclear-pdfs', 'unclear.pdf')
if os.path.exists(unclear_pdf_path):
    with open(unclear_pdf_path, 'rb') as f:
        file_bytes = f.read()
    page_data = extract_page_data(file_bytes, 'unclear.pdf')
    for page_info in page_data:
        print(f"Unclear PDF - Page {page_info['page']}: Ink Ratio={page_info['ink_ratio']:.4f}, OCR Conf={page_info['ocr_conf']:.2f}")
else:
    print("Unclear PDF file not found")

# Test valid PDFs (if any exist)
print("\n=== Testing Valid PDFs ===")
valid_dir = os.path.join(dataset_path, 'valid-pdfs')
if os.path.exists(valid_dir):
    valid_files = os.listdir(valid_dir)
    if valid_files:
        for valid_file in valid_files:
            valid_path = os.path.join(valid_dir, valid_file)
            with open(valid_path, 'rb') as f:
                file_bytes = f.read()
            page_data = extract_page_data(file_bytes, valid_file)
            for page_info in page_data:
                print(f"Valid PDF {valid_file} - Page {page_info['page']}: Ink Ratio={page_info['ink_ratio']:.4f}, OCR Conf={page_info['ocr_conf']:.2f}")
    else:
        print("No valid PDF files found")
else:
    print("Valid PDF directory not found")