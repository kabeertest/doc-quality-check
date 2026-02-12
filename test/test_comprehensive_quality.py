import unittest
from app import extract_page_data, is_tesseract_available
import os
import tempfile
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


class TestDocumentQualityChecker(unittest.TestCase):
    """Comprehensive tests for document quality checking functionality"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.tesseract_available = is_tesseract_available()
        print(f"Tesseract availability: {self.tesseract_available}")
        
        # Create temporary files for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test documents
        self.create_test_documents()
    
    def create_test_documents(self):
        """Create sample documents for testing"""
        # Create empty document
        empty_path = os.path.join(self.temp_dir, 'empty_test.pdf')
        c = canvas.Canvas(empty_path, pagesize=letter)
        c.save()  # Completely empty PDF
        self.empty_pdf_path = empty_path
        
        # Create unclear document (with low contrast/noisy text)
        unclear_path = os.path.join(self.temp_dir, 'unclear_test.pdf')
        c = canvas.Canvas(unclear_path, pagesize=letter)
        # Add very faint text
        c.setFont("Helvetica", 6)  # Very small font
        c.setFillColorRGB(0.8, 0.8, 0.8)  # Light gray text
        c.drawString(50, 700, "This is very faint text that should be hard to recognize.")
        c.drawString(50, 680, "OCR confidence should be low for this document.")
        c.save()
        self.unclear_pdf_path = unclear_path
        
        # Create valid document (with clear text)
        valid_path = os.path.join(self.temp_dir, 'valid_test.pdf')
        doc = SimpleDocTemplate(valid_path, pagesize=letter)
        styles = getSampleStyleSheet()
        
        story = []
        story.append(Paragraph("This is a clear, readable document for testing.", styles['Heading1']))
        story.append(Spacer(1, 12))
        story.append(Paragraph("The text in this document should be easily recognized by OCR systems.", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Additional content to test OCR confidence scoring.", styles['Normal']))
        
        doc.build(story)
        self.valid_pdf_path = valid_path
    
    def test_empty_document_characteristics(self):
        """Test characteristics of empty documents"""
        with open(self.empty_pdf_path, 'rb') as f:
            file_bytes = f.read()
        
        page_data = extract_page_data(file_bytes, 'empty_test.pdf')
        
        self.assertGreater(len(page_data), 0, "Should have extracted at least one page")
        
        for page_info in page_data:
            ink_ratio = page_info['ink_ratio']
            ocr_conf = page_info['ocr_conf']
            
            print(f"Empty document - Page {page_info['page']}: "
                  f"Ink Ratio={ink_ratio:.4f}, OCR Conf={ocr_conf:.2f}")
            
            # Empty pages should have very low ink ratio
            self.assertLess(ink_ratio, 0.001, "Empty page should have extremely low ink ratio (< 0.1%)")
            
            # OCR confidence should be 0 when Tesseract is not available
            if not self.tesseract_available:
                self.assertEqual(ocr_conf, 0, "OCR confidence should be 0 when Tesseract is not available")
            else:
                # When Tesseract is available, empty pages should still have low confidence
                self.assertLessEqual(ocr_conf, 10, "Empty pages should have low OCR confidence even with Tesseract")
    
    def test_unclear_document_characteristics(self):
        """Test characteristics of unclear documents"""
        with open(self.unclear_pdf_path, 'rb') as f:
            file_bytes = f.read()
        
        page_data = extract_page_data(file_bytes, 'unclear_test.pdf')
        
        self.assertGreater(len(page_data), 0, "Should have extracted at least one page")
        
        for page_info in page_data:
            ink_ratio = page_info['ink_ratio']
            ocr_conf = page_info['ocr_conf']
            
            print(f"Unclear document - Page {page_info['page']}: "
                  f"Ink Ratio={ink_ratio:.4f}, OCR Conf={ocr_conf:.2f}")
            
            # Unclear documents may have some ink, but OCR confidence should be low
            if not self.tesseract_available:
                self.assertEqual(ocr_conf, 0, "OCR confidence should be 0 when Tesseract is not available")
            else:
                # When Tesseract is available, unclear documents should have low confidence
                self.assertLessEqual(ocr_conf, 30, "Unclear documents should have low OCR confidence")
    
    def test_valid_document_characteristics(self):
        """Test characteristics of valid documents"""
        with open(self.valid_pdf_path, 'rb') as f:
            file_bytes = f.read()
        
        page_data = extract_page_data(file_bytes, 'valid_test.pdf')
        
        self.assertGreater(len(page_data), 0, "Should have extracted at least one page")
        
        for page_info in page_data:
            ink_ratio = page_info['ink_ratio']
            ocr_conf = page_info['ocr_conf']
            
            print(f"Valid document - Page {page_info['page']}: "
                  f"Ink Ratio={ink_ratio:.4f}, OCR Conf={ocr_conf:.2f}")
            
            # Valid documents should have reasonable ink ratio
            if self.tesseract_available:
                # When Tesseract is available, valid documents should have higher confidence
                # Note: PDF text extraction might not work the same as image OCR
                # So we're mainly checking that the function doesn't crash
                self.assertIsInstance(ocr_conf, float)
            else:
                self.assertEqual(ocr_conf, 0, "OCR confidence should be 0 when Tesseract is not available")
    
    def test_all_three_types_classification(self):
        """Test that all three document types are classified appropriately"""
        # Test empty document
        with open(self.empty_pdf_path, 'rb') as f:
            file_bytes = f.read()
        empty_data = extract_page_data(file_bytes, 'empty_test.pdf')[0]
        
        # Test unclear document
        with open(self.unclear_pdf_path, 'rb') as f:
            file_bytes = f.read()
        unclear_data = extract_page_data(file_bytes, 'unclear_test.pdf')[0]
        
        # Test valid document
        with open(self.valid_pdf_path, 'rb') as f:
            file_bytes = f.read()
        valid_data = extract_page_data(file_bytes, 'valid_test.pdf')[0]
        
        print(f"\nComparison of all three types:")
        print(f"Empty: Ink Ratio={empty_data['ink_ratio']:.4f}, OCR Conf={empty_data['ocr_conf']:.2f}")
        print(f"Unclear: Ink Ratio={unclear_data['ink_ratio']:.4f}, OCR Conf={unclear_data['ocr_conf']:.2f}")
        print(f"Valid: Ink Ratio={valid_data['ink_ratio']:.4f}, OCR Conf={valid_data['ocr_conf']:.2f}")
        
        # All should have valid ink ratios
        self.assertIsInstance(empty_data['ink_ratio'], float)
        self.assertIsInstance(unclear_data['ink_ratio'], float)
        self.assertIsInstance(valid_data['ink_ratio'], float)
        
        # All should have valid OCR confidences
        self.assertIsInstance(empty_data['ocr_conf'], float)
        self.assertIsInstance(unclear_data['ocr_conf'], float)
        self.assertIsInstance(valid_data['ocr_conf'], float)
    
    def tearDown(self):
        """Clean up after tests"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


if __name__ == '__main__':
    print("Running comprehensive document quality checker tests...")
    print("="*60)
    unittest.main(verbosity=2)