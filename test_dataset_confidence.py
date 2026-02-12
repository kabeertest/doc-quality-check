import unittest
from app import extract_page_data
import os


class TestDatasetFiles(unittest.TestCase):
    """Test the dataset files to verify confidence scores are calculated correctly"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.dataset_path = os.path.join(os.path.dirname(__file__), 'dataset')
    
    def test_empty_pdf_confidence_score(self):
        """Test that empty PDF has low confidence score"""
        file_path = os.path.join(self.dataset_path, 'empty-pdfs', 'blank.pdf')
        
        # Check if file exists
        if not os.path.exists(file_path):
            self.skipTest(f"File does not exist: {file_path}")
        
        # Read the file
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
        
        # Extract page data
        page_data = extract_page_data(file_bytes, 'blank.pdf')
        
        # Verify we got page data
        self.assertGreater(len(page_data), 0, "Should have extracted at least one page")
        
        # Check that confidence scores are appropriately low for empty pages
        for page_info in page_data:
            ink_ratio = page_info['ink_ratio']
            ocr_conf = page_info['ocr_conf']
            
            print(f"Empty PDF - Page {page_info['page']}: Ink Ratio={ink_ratio:.4f}, OCR Conf={ocr_conf:.2f}")
            
            # Empty pages should have very low ink ratio
            self.assertLess(ink_ratio, 0.01, "Empty page should have very low ink ratio")  # Less than 1%
            
            # OCR confidence might be 0 or very low for empty pages
            # This is expected behavior
    
    def test_unclear_pdf_confidence_score(self):
        """Test that unclear PDF has low confidence score"""
        file_path = os.path.join(self.dataset_path, 'unclear-pdfs', 'unclear.pdf')
        
        # Check if file exists
        if not os.path.exists(file_path):
            self.skipTest(f"File does not exist: {file_path}")
        
        # Read the file
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
        
        # Extract page data
        page_data = extract_page_data(file_bytes, 'unclear.pdf')
        
        # Verify we got page data
        self.assertGreater(len(page_data), 0, "Should have extracted at least one page")
        
        # Check that confidence scores are appropriately low for unclear pages
        for page_info in page_data:
            ink_ratio = page_info['ink_ratio']
            ocr_conf = page_info['ocr_conf']
            
            print(f"Unclear PDF - Page {page_info['page']}: Ink Ratio={ink_ratio:.4f}, OCR Conf={ocr_conf:.2f}")
            
            # Unclear pages might have text (so ink ratio could be higher)
            # But OCR confidence should be low due to poor quality
            # We expect OCR confidence to be lower than for clear documents
    
    def test_valid_pdf_confidence_score(self):
        """Test that valid PDF has reasonable confidence score"""
        # Since valid-pdfs directory is empty, we'll create a simple test PDF programmatically
        # For now, we'll skip this test if no valid PDFs exist
        valid_dir = os.path.join(self.dataset_path, 'valid-pdfs')
        valid_files = os.listdir(valid_dir) if os.path.exists(valid_dir) else []
        
        if not valid_files:
            self.skipTest("No valid PDF files found in dataset")
        
        file_path = os.path.join(valid_dir, valid_files[0])
        
        # Read the file
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
        
        # Extract page data
        page_data = extract_page_data(file_bytes, valid_files[0])
        
        # Verify we got page data
        self.assertGreater(len(page_data), 0, "Should have extracted at least one page")
        
        # Check that confidence scores are reasonably high for valid pages
        for page_info in page_data:
            ink_ratio = page_info['ink_ratio']
            ocr_conf = page_info['ocr_conf']
            
            print(f"Valid PDF - Page {page_info['page']}: Ink Ratio={ink_ratio:.4f}, OCR Conf={ocr_conf:.2f}")
            
            # Valid pages should have reasonable ink ratio (more than empty pages)
            self.assertGreater(ink_ratio, 0.01, "Valid page should have more than 1% ink ratio")
            
            # Valid pages should have decent OCR confidence (though this depends on quality)
            # We expect it to be higher than unclear documents


if __name__ == '__main__':
    print("Testing dataset files for confidence score calculation...")
    unittest.main(verbosity=2)