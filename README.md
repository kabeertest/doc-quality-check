# Document Quality Validator with Identity Card Detection

A Streamlit application for validating document quality and automatically detecting identity cards with bounding box visualization.

## Features

### Document Quality Validation
- **Emptiness Check**: Detects blank or near-blank pages
- **Readability Check**: Validates OCR confidence scores
- **Quality Metrics**: Ink ratio and OCR confidence for each page

### Identity Card Detection (Enabled by Default)
- **Document Type Classification**: National ID, Driver's License, Passport, Residence Permit
- **Side Detection**: Front, Back, or Both
- **Multi-Document Support**: Handles multiple documents on a single page
- **Bounding Box Visualization**: Shows detected document locations with colored boxes
- **Confidence Scoring**: Provides confidence percentage for each classification
- **Configurable Keywords**: Easy to customize via config.json
- **Keyword Frequency Boost**: Confidence increases when same keywords appear across multiple documents

## Project Structure

```
doc-quality-check/
├── app.py                      # Main Streamlit application
├── config.json                 # Configuration for keywords and detection
├── content_extraction.py       # OCR and text extraction
├── document_processor.py       # Document processing utilities
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── modules/                    # Identity detection modules
│   ├── __init__.py
│   ├── identity_detection.py   # Core identity classification
│   ├── document_segmentation.py # Multi-document handling
│   ├── config_loader.py        # Configuration management
│   └── visualization.py        # Bounding box drawing
├── checks/                     # Quality check modules
│   ├── clarity_check.py
│   └── confidence_check.py
├── utils/                      # Utility modules
│   ├── document_processor.py
│   └── content_extraction.py
└── dataset/                    # Sample test files
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. For Windows users, install Tesseract OCR:
   - Download from: https://github.com/UB-Mannheim/tesseract/wiki
   - Default installation path is automatically detected

## Usage

1. Start the application:
```bash
streamlit run app.py
```

2. Upload a PDF or image file

3. The application will automatically:
   - Validate document quality
   - Detect and classify identity cards
   - Display bounding boxes around detected documents
   - Show classification results with confidence scores

## Configuration

### Single Source of Truth: config.json

**All configuration is centralized in `config.json`** - no hardcoded values in Python files.

#### Document Types Configuration
```json
{
  "document_types": {
    "national_id": {
      "name": "National ID",
      "display_name": "National ID",
      "aliases": ["id card", "identity card"],
      "keywords": {
        "en": ["national id", "identity card"],
        "other": ["carte nationale"]
      },
      "color": [255, 0, 0],
      "enabled": true
    }
  }
}
```

**Configuration Options for Document Types:**
- `name`: Internal key (used in code)
- `display_name`: Display name shown in UI
- `aliases`: Alternative names for matching
- `keywords`: Keywords for detection (English + other languages)
- `color`: RGB color for bounding box visualization
- `enabled`: Toggle document type on/off

#### Document Sides
```json
{
  "document_sides": {
    "front": {
      "name": "Front",
      "display_name": "Front",
      "aliases": ["face", "front side"],
      "keywords": {
        "en": ["photo", "name", "date of birth"],
        "other": ["avant"]
      },
      "short_code": "F",
      "enabled": true
    }
  }
}
```

**Configuration Options for Document Sides:**
- `name`: Internal key
- `display_name`: Display name in UI
- `aliases`: Alternative names
- `keywords`: Keywords for side detection
- `short_code`: Short code for bounding box labels (e.g., "F" for front)
- `enabled`: Toggle side detection on/off

#### UI Settings
```json
{
  "ui_settings": {
    "max_keywords_display": 10,
    "show_confidence_breakdown": true,
    "show_specific_keywords": true,
    "enable_visualization": true
  }
}
```

#### Detection Settings
```json
{
  "detection_settings": {
    "min_document_area_percent": 5.0,
    "max_document_area_percent": 80.0,
    "min_aspect_ratio": 1.4,
    "max_aspect_ratio": 2.0,
    "padding_percent": 5.0,
    "min_confidence_threshold": 30.0
  }
}
```

#### Confidence Boost Settings
```json
{
  "confidence_boost_settings": {
    "single_match_boost": 5.0,
    "double_match_boost": 10.0,
    "triple_plus_match_boost": 15.0,
    "side_single_match_boost": 4.0,
    "side_double_match_boost": 8.0,
    "side_triple_plus_match_boost": 12.0,
    "max_confidence_cap": 100.0
  }
}
```

**How Confidence Boost Works:**
- **Frequency Boost**: Based on how many documents share the same keywords
  - 1 document: +5% confidence
  - 2 documents: +10% confidence
  - 3+ documents: +15% confidence
- **Specificity Bonus**: Longer, more specific keywords get higher bonuses (up to +10%)
  - 3+ word keywords: +3% each
  - 2 word keywords: +2% each
  - 1 word keywords: +1% each
- **Consistency Bonus**: Multiple different keyword matches
  - 3+ matches: +5%
  - 2 matches: +3%
- **Quality Adjustment**: Boosts are reduced for low-quality documents
  - Poor OCR (<30% confidence): 50% reduction
  - Medium OCR (<50% confidence): 25% reduction
  - Poor ink ratio: 20% reduction

**Example:**
If 3 ID cards in a PDF all contain "National Identity Card" (3 words):
- Frequency Boost: +15% (3 documents)
- Specificity Bonus: +9% (3 words × 3%, capped at 10%)
- Consistency Bonus: +5% (multiple keyword types match)
- Base Adjustment: +29%
- If OCR is good (quality factor 1.0): **Final Boost: +29%**
- If OCR is poor (quality factor 0.5): **Final Boost: +14.5%**

### Sidebar Options
- **Emptiness Threshold**: Minimum ink ratio for valid pages
- **Readability Threshold**: Minimum OCR confidence score
- **Enable/Disable Checks**: Toggle individual quality checks
- **View Detection Configuration**: Expandable section showing current config

## Supported Formats

- PDF documents
- Images: PNG, JPG, JPEG

## Identity Card Detection

The system automatically detects:
- **National ID Cards**: Front and back sides
- **Driver's Licenses**: Front and back sides
- **Passports**: Configurable
- **Residence Permits**: Configurable
- **Multiple Documents**: Handles several documents on one page

### Visualization Features
- **Colored Bounding Boxes**: Different colors for different document types
  - Red: National ID
  - Green: Driver License
  - Blue: Passport
  - Gray: Unknown
- **Labels**: Short codes showing document type and side (e.g., "NAT-F" for National ID Front)
- **Segmented Views**: Individual document images in expandable sections
- **Matched Keywords**: Shows which keywords triggered the classification

## Adding Custom Document Types

1. Edit `config.json`
2. Add new document type under `document_types`
3. Add keywords in English and other languages
4. Restart the application or click "Reload Configuration"

Example:
```json
"voter_id": {
  "name": "Voter ID",
  "aliases": ["voter card", "election card"],
  "keywords": {
    "en": ["voter id", "election commission", "voter card"],
    "other": ["carte d'électeur"]
  }
}
```
