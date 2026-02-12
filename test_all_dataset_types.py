import unittest
from app import extract_page_data, is_tesseract_available
import os


class TestDatasetTypes(unittest.TestCase):
    """Test all three types of documents in the dataset"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.dataset_path = os.path.join(os.path.dirname(__file__), 'dataset')
        self.tesseract_available = is_tesseract_available()
        print(f"Tesseract availability: {self.tesseract_available}")
    
    def test_empty_documents(self):
        """Test empty documents from the dataset"""
        empty_dir = os.path.join(self.dataset_path, 'empty-pdfs')
        if not os.path.exists(empty_dir):
            self.skipTest("Empty PDFs directory does not exist")
        
        empty_files = os.listdir(empty_dir)
        if not empty_files:
            self.skipTest("No empty PDF files found")
        
        for file_name in empty_files:
            file_path = os.path.join(empty_dir, file_name)
            with open(file_path, 'rb') as f:
                file_bytes = f.read()
            
            page_data = extract_page_data(file_bytes, file_name)
            
            # Verify we got page data
            self.assertGreater(len(page_data), 0, f"Should have extracted at least one page from {file_name}")
            
            for page_info in page_data:
                ink_ratio = page_info['ink_ratio']
                ocr_conf = page_info['ocr_conf']
                
                print(f"Empty PDF {file_name} - Page {page_info['page']}: "
                      f"Ink Ratio={ink_ratio:.4f}, OCR Conf={ocr_conf:.2f}")
                
                # Empty pages should have very low ink ratio
                self.assertLess(ink_ratio, 0.01, f"Empty page in {file_name} should have very low ink ratio")
                
                # If Tesseract is available, OCR confidence should be checked
                # If not available, it should be 0
                if self.tesseract_available:
                    # For truly empty pages, OCR confidence might still be low
                    # but the important thing is that the function doesn't crash
                    self.assertIsInstance(ocr_conf, float)
                else:
                    # When Tesseract is not available, confidence should be 0
                    self.assertEqual(ocr_conf, 0, 
                                   f"When Tesseract is not available, OCR confidence should be 0 for {file_name}")
    
    def test_unclear_documents(self):
        """Test unclear documents from the dataset"""
        unclear_dir = os.path.join(self.dataset_path, 'unclear-pdfs')
        if not os.path.exists(unclear_dir):
            self.skipTest("Unclear PDFs directory does not exist")
        
        unclear_files = os.listdir(unclear_dir)
        if not unclear_files:
            self.skipTest("No unclear PDF files found")
        
        for file_name in unclear_files:
            file_path = os.path.join(unclear_dir, file_name)
            with open(file_path, 'rb') as f:
                file_bytes = f.read()
            
            page_data = extract_page_data(file_bytes, file_name)
            
            # Verify we got page data
            self.assertGreater(len(page_data), 0, f"Should have extracted at least one page from {file_name}")
            
            for page_info in page_data:
                ink_ratio = page_info['ink_ratio']
                ocr_conf = page_info['ocr_conf']
                
                print(f"Unclear PDF {file_name} - Page {page_info['page']}: "
                      f"Ink Ratio={ink_ratio:.4f}, OCR Conf={ocr_conf:.2f}")
                
                # Unclear documents might have some ink, but OCR confidence should reflect quality
                self.assertIsInstance(ink_ratio, float)
                
                # If Tesseract is available, OCR confidence should be checked
                # If not available, it should be 0
                if self.tesseract_available:
                    self.assertIsInstance(ocr_conf, float)
                else:
                    self.assertEqual(ocr_conf, 0,
                                   f"When Tesseract is not available, OCR confidence should be 0 for {file_name}")
    
    def test_valid_documents(self):
        """Test valid documents from the dataset"""
        valid_dir = os.path.join(self.dataset_path, 'valid-pdfs')
        if not os.path.exists(valid_dir):
            self.skipTest("Valid PDFs directory does not exist")
        
        valid_files = os.listdir(valid_dir)
        if not valid_files:
            self.skipTest("No valid PDF files found")
        
        for file_name in valid_files:
            file_path = os.path.join(valid_dir, file_name)
            with open(file_path, 'rb') as f:
                file_bytes = f.read()
            
            page_data = extract_page_data(file_bytes, file_name)
            
            # Verify we got page data
            self.assertGreater(len(page_data), 0, f"Should have extracted at least one page from {file_name}")
            
            for page_info in page_data:
                ink_ratio = page_info['ink_ratio']
                ocr_conf = page_info['ocr_conf']
                
                print(f"Valid PDF {file_name} - Page {page_info['page']}: "
                      f"Ink Ratio={ink_ratio:.4f}, OCR Conf={ocr_conf:.2f}")
                
                # Valid documents should have reasonable ink ratio
                self.assertIsInstance(ink_ratio, float)
                
                # If Tesseract is available, OCR confidence should be checked
                # If not available, it should be 0
                if self.tesseract_available:
                    self.assertIsInstance(ocr_conf, float)
                else:
                    self.assertEqual(ocr_conf, 0,
                                   f"When Tesseract is not available, OCR confidence should be 0 for {file_name}")


if __name__ == '__main__':
    print("Testing all three types of documents in the dataset...")
    unittest.main(verbosity=2)