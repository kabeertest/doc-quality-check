import fitz
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Test what happens with empty PDF
empty_pdf_path = "dataset/empty-pdfs/actually_blank.pdf"
if os.path.exists(empty_pdf_path):
    print("Testing empty PDF...")
    doc = fitz.open(empty_pdf_path)
    print(f"Number of pages in empty PDF: {len(doc)}")
    
    for i in range(len(doc)):
        page = doc.load_page(i)
        print(f"Page {i} loaded successfully")
        
        # Try to render the page
        try:
            mat = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=mat)
            print(f"Page {i} pixmap created, width: {pix.width}, height: {pix.height}")
        except Exception as e:
            print(f"Error creating pixmap for page {i}: {e}")
    
    doc.close()
else:
    print("Empty PDF file does not exist")

# Create and test a minimal PDF with just a border/frame
minimal_pdf_path = "temp_test_minimal.pdf"
c = canvas.Canvas(minimal_pdf_path, pagesize=letter)
# Draw a minimal frame to ensure there's some content
c.rect(50, 50, 400, 600)  # Draw a rectangle
c.save()
print(f"\nTesting minimal PDF with border...")
doc = fitz.open(minimal_pdf_path)
print(f"Number of pages in minimal PDF: {len(doc)}")
for i in range(len(doc)):
    page = doc.load_page(i)
    mat = fitz.Matrix(2, 2)
    pix = page.get_pixmap(matrix=mat)
    print(f"Minimal PDF Page {i} pixmap created, width: {pix.width}, height: {pix.height}")
doc.close()
os.remove(minimal_pdf_path)  # Clean up