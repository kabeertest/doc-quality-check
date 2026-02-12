from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import os

# Create dataset directories if they don't exist
os.makedirs('dataset/valid-pdfs', exist_ok=True)
os.makedirs('dataset/unclear-pdfs', exist_ok=True)

# Create a valid PDF with clear text
def create_valid_pdf():
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    
    doc = SimpleDocTemplate("dataset/valid-pdfs/clear_document.pdf", pagesize=letter)
    styles = getSampleStyleSheet()
    
    story = []
    story.append(Paragraph("This is a clear, readable document for testing.", styles['Heading1']))
    story.append(Spacer(1, 12))
    story.append(Paragraph("The text in this document should be easily recognized by OCR systems.", styles['Normal']))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Additional content to test OCR confidence scoring.", styles['Normal']))
    
    doc.build(story)
    print("Created valid PDF: dataset/valid-pdfs/clear_document.pdf")

# Create an unclear PDF with low-quality text
def create_unclear_pdf():
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import black, lightgrey
    import random
    
    c = canvas.Canvas("dataset/unclear-pdfs/low_quality_document.pdf", pagesize=letter)
    width, height = letter
    
    # Add background noise
    for i in range(1000):
        x = random.randint(0, int(width))
        y = random.randint(0, int(height))
        size = random.uniform(0.1, 1)
        c.setFillColor(lightgrey)
        c.circle(x, y, size, fill=1)
    
    # Add barely visible text
    c.setFont("Helvetica", 8)  # Small font
    c.setFillColor(black)
    c.drawString(50, height - 100, "This is low quality text that should be hard to recognize.")
    c.drawString(50, height - 120, "OCR confidence should be low for this document.")
    
    # Add rotated text
    c.saveState()
    c.translate(100, height - 200)
    c.rotate(15)
    c.drawString(0, 0, "Rotated text for OCR challenge")
    c.restoreState()
    
    c.save()
    print("Created unclear PDF: dataset/unclear-pdfs/low_quality_document.pdf")

# Create an empty PDF
def create_empty_pdf():
    c = canvas.Canvas("dataset/empty-pdfs/actually_blank.pdf", pagesize=letter)
    # Just save without adding any content
    c.save()
    print("Created empty PDF: dataset/empty-pdfs/actually_blank.pdf")

if __name__ == "__main__":
    create_valid_pdf()
    create_unclear_pdf()
    create_empty_pdf()
    print("Sample PDFs created successfully!")