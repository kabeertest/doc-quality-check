"""
Test script to compare original vs improved confidence calculation.
"""

import os
import sys
import fitz  # PyMuPDF
from PIL import Image
import io

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from checks.confidence_check import calculate_ocr_confidence as original_confidence
from checks.confidence_check_improved import calculate_ocr_confidence as improved_confidence

# Test files
TEST_FILES = [
    "dataset/italian_ids/italian_id_front_back_sample1.pdf",
    "dataset/italian_ids/italian_id_front_back_sample3_only_front.pdf"
]

def test_pdf(pdf_path):
    """Test a single PDF with both methods."""
    print(f"\n{'='*80}")
    print(f"Testing: {pdf_path}")
    print(f"{'='*80}")
    
    if not os.path.exists(pdf_path):
        print(f"[ERROR] File not found: {pdf_path}")
        return
    
    # Open PDF
    doc = fitz.open(pdf_path)
    print(f"\n[TOTAL] Pages: {len(doc)}")
    
    for page_num in range(len(doc)):
        print(f"\n{'-'*80}")
        print(f"PAGE {page_num + 1}")
        print(f"{'-'*80}")
        
        # Render page
        page = doc.load_page(page_num)
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        pil_img = Image.open(io.BytesIO(img_data))
        
        # Test with English
        print("\n[ENGLISH OCR]")
        print("-" * 40)
        
        orig_conf_eng, orig_time_eng = original_confidence(pil_img, mode='fast', lang='eng')
        impr_conf_eng, impr_time_eng = improved_confidence(pil_img, mode='balanced', lang='eng')
        
        print(f"  Original: {orig_conf_eng:.2f} ({orig_time_eng:.2f}s)")
        print(f"  Improved: {impr_conf_eng:.2f} ({impr_time_eng:.2f}s)")
        print(f"  Improvement: +{impr_conf_eng - orig_conf_eng:.2f} ({((impr_conf_eng/orig_conf_eng)-1)*100 if orig_conf_eng > 0 else 0:.1f}%)")
        
        # Test with Italian
        print("\n[ITALIAN OCR]")
        print("-" * 40)
        
        orig_conf_ita, orig_time_ita = original_confidence(pil_img, mode='fast', lang='ita')
        impr_conf_ita, impr_time_ita = improved_confidence(pil_img, mode='balanced', lang='ita')
        
        print(f"  Original: {orig_conf_ita:.2f} ({orig_time_ita:.2f}s)")
        print(f"  Improved: {impr_conf_ita:.2f} ({impr_time_ita:.2f}s)")
        print(f"  Improvement: +{impr_conf_ita - orig_conf_ita:.2f} ({((impr_conf_ita/orig_conf_ita)-1)*100 if orig_conf_ita > 0 else 0:.1f}%)")
        
        # Recommendation
        print("\n[RECOMMENDATION]")
        print("-" * 40)
        best_conf = max(orig_conf_eng, orig_conf_ita, impr_conf_eng, impr_conf_ita)
        if best_conf == impr_conf_eng:
            print(f"  Use IMPROVED method with ENGLISH ({impr_conf_eng:.2f})")
        elif best_conf == impr_conf_ita:
            print(f"  Use IMPROVED method with ITALIAN ({impr_conf_ita:.2f})")
        elif best_conf == orig_conf_eng:
            print(f"  Use ORIGINAL method with ENGLISH ({orig_conf_eng:.2f})")
        else:
            print(f"  Use ORIGINAL method with ITALIAN ({orig_conf_ita:.2f})")

if __name__ == "__main__":
    print("="*80)
    print("CONFIDENCE CALCULATION COMPARISON")
    print("="*80)
    
    for pdf_file in TEST_FILES:
        test_pdf(pdf_file)
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
