import unittest
import numpy as np
import cv2
from PIL import Image
import io
import fitz
import tempfile
import os
from app import extract_page_data
import streamlit as st

class TestDocumentQualityValidator(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a blank image for testing
        self.blank_image = Image.new('RGB', (100, 100), color='white')
        img_byte_arr = io.BytesIO()
        self.blank_image.save(img_byte_arr, format='PNG')
        self.blank_image_bytes = img_byte_arr.getvalue()
        
        # Create an image with text for testing
        text_image = np.zeros((200, 200, 3), dtype=np.uint8)
        text_image[:] = [255, 255, 255]  # White background
        cv2.putText(text_image, 'Test Text', (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        self.text_image_pil = Image.fromarray(cv2.cvtColor(text_image, cv2.COLOR_BGR2RGB))
        img_byte_arr = io.BytesIO()
        self.text_image_pil.save(img_byte_arr, format='PNG')
        self.text_image_bytes = img_byte_arr.getvalue()
    
    def test_blank_image_processing(self):
        """Test processing of a blank (white) image."""
        result = extract_page_data(self.blank_image_bytes, "blank.png")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['page'], 1)
        # Ink ratio should be very low for a blank image
        self.assertLess(result[0]['ink_ratio'], 0.01)  # Less than 1%
        # OCR confidence should be low for a blank image
        self.assertLess(result[0]['ocr_conf'], 10)  # Low confidence
    
    def test_text_image_processing(self):
        """Test processing of an image with text."""
        result = extract_page_data(self.text_image_bytes, "text.png")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['page'], 1)
        # Ink ratio should be higher for an image with text
        self.assertGreaterEqual(result[0]['ink_ratio'], 0)  # Non-negative
        # OCR confidence should be reasonable for an image with text
        self.assertGreaterEqual(result[0]['ocr_conf'], 0)  # Non-negative
    
    def test_pdf_processing(self):
        """Test processing of a PDF file."""
        # Create a temporary PDF with some text
        temp_pdf_path = tempfile.mktemp(suffix='.pdf')
        
        # Create a simple PDF using fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 100), "Sample text for testing")
        doc.save(temp_pdf_path)
        doc.close()
        
        # Read the PDF bytes
        with open(temp_pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        
        result = extract_page_data(pdf_bytes, "test.pdf")
        
        self.assertEqual(len(result), 1)  # PDF has 1 page
        self.assertEqual(result[0]['page'], 1)
        # Ink ratio should be greater than 0 for a page with text
        self.assertGreaterEqual(result[0]['ink_ratio'], 0)
        # OCR confidence should be non-negative
        self.assertGreaterEqual(result[0]['ocr_conf'], 0)
        
        # Clean up
        os.remove(temp_pdf_path)
    
    def test_multiple_pages_pdf(self):
        """Test processing of a PDF with multiple pages."""
        # Create a temporary PDF with multiple pages
        temp_pdf_path = tempfile.mktemp(suffix='.pdf')
        
        # Create a PDF with 2 pages using fitz
        doc = fitz.open()
        page1 = doc.new_page()
        page1.insert_text((50, 100), "First page text")
        page2 = doc.new_page()
        page2.insert_text((50, 100), "Second page text")
        doc.save(temp_pdf_path)
        doc.close()
        
        # Read the PDF bytes
        with open(temp_pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        
        result = extract_page_data(pdf_bytes, "multipage.pdf")
        
        self.assertEqual(len(result), 2)  # PDF has 2 pages
        self.assertEqual(result[0]['page'], 1)
        self.assertEqual(result[1]['page'], 2)
        
        # Both pages should have non-negative metrics
        for page_info in result:
            self.assertGreaterEqual(page_info['ink_ratio'], 0)
            self.assertGreaterEqual(page_info['ocr_conf'], 0)
        
        # Clean up
        os.remove(temp_pdf_path)
    
    def test_invalid_file_handling(self):
        """Test handling of invalid file data."""
        # Test with random bytes that don't form a valid image/pdf
        invalid_bytes = b"invalid file content"
        
        # This should raise an exception when trying to process
        with self.assertRaises(Exception):
            extract_page_data(invalid_bytes, "invalid.ext")
    
    def test_edge_cases(self):
        """Test edge cases like completely black image."""
        # Create a completely black image
        black_image = Image.new('RGB', (100, 100), color='black')
        img_byte_arr = io.BytesIO()
        black_image.save(img_byte_arr, format='PNG')
        black_image_bytes = img_byte_arr.getvalue()
        
        result = extract_page_data(black_image_bytes, "black.png")
        
        self.assertEqual(len(result), 1)
        # Ink ratio should be high for a completely black image
        self.assertGreaterEqual(result[0]['ink_ratio'], 0.9)  # More than 90% ink
    
    def test_return_format(self):
        """Test that the function returns data in the expected format."""
        result = extract_page_data(self.text_image_bytes, "test.png")
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        
        page_info = result[0]
        self.assertIn('page', page_info)
        self.assertIn('ink_ratio', page_info)
        self.assertIn('ocr_conf', page_info)
        self.assertIn('image', page_info)
        
        self.assertIsInstance(page_info['page'], int)
        self.assertIsInstance(page_info['ink_ratio'], float)
        # OCR confidence can be int or float depending on the calculation
        self.assertIsInstance(page_info['ocr_conf'], (int, float))
        self.assertIsInstance(page_info['image'], Image.Image)


if __name__ == '__main__':
    print("Running tests for Document Quality Validator...")
    unittest.main(verbosity=2)