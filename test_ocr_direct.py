import pytesseract
import cv2
from PIL import Image
import numpy as np
import io
import fitz  # PyMuPDF

def test_ocr_directly():
    """Test OCR functionality directly on the PDF"""
    print("Testing OCR directly...")
    
    # Load the valid PDF
    doc = fitz.open("dataset/valid-pdfs/clear_document.pdf")
    page = doc.load_page(0)  # First page
    
    # Render page at 2x resolution for better accuracy
    mat = fitz.Matrix(2, 2)
    pix = page.get_pixmap(matrix=mat)
    
    # Convert pixmap to image
    img_data = pix.tobytes("png")
    pil_img = Image.open(io.BytesIO(img_data))
    
    # Convert PIL image to OpenCV format
    img_cv = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    
    # Convert to grayscale for OCR
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    
    print(f"Image shape: {gray.shape}")
    print(f"Image dtype: {gray.dtype}")
    print(f"Image min/max values: {gray.min()}/{gray.max()}")
    
    # Try basic OCR
    try:
        text = pytesseract.image_to_string(gray)
        print(f"Basic OCR text: '{text.strip()}'")
    except Exception as e:
        print(f"Basic OCR failed: {e}")
    
    # Try OCR with data
    try:
        ocr_data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
        print(f"OCR data keys: {list(ocr_data.keys())}")
        print(f"Number of text elements: {len(ocr_data['text'])}")
        
        # Look at actual text and confidence values
        valid_texts = []
        for i, (text, conf) in enumerate(zip(ocr_data['text'], ocr_data['conf'])):
            if text.strip():  # Non-empty text
                valid_texts.append((text.strip(), conf))
                print(f"Text element {i}: '{text.strip()}', conf: {conf}")
        
        if valid_texts:
            avg_conf = sum(conf for _, conf in valid_texts) / len(valid_texts)
            print(f"Average confidence for valid texts: {avg_conf}")
        else:
            print("No valid text found in OCR data")
            
    except Exception as e:
        print(f"OCR with data failed: {e}")
    
    # Try with different PSM modes
    print("\nTrying different PSM modes:")
    psm_modes = ['--psm 6', '--psm 4', '--psm 3']
    for psm_mode in psm_modes:
        try:
            config_str = psm_mode + ' -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ '
            text = pytesseract.image_to_string(gray, config=config_str)
            print(f"PSM {psm_mode}: '{text.strip()}'")
        except Exception as e:
            print(f"PSM {psm_mode} failed: {e}")

if __name__ == "__main__":
    test_ocr_directly()