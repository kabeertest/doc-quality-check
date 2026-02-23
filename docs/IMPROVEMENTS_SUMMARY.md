# Document Quality Check - Recent Improvements

## Overview

This document summarizes recent improvements to the document quality checking system, specifically addressing issues with Italian ID documents.

---

## Key Features Implemented

### 1. Artifact Filtering ✅

**Problem**: PDFs created from screenshots contained file paths, timestamps, and URLs that lowered confidence scores.

**Solution**: Intelligent filtering excludes screenshot artifacts from confidence calculation.

**Result**: 
- Sample 2: 18.93% → **31.18%** (+65% improvement) ✅
- Sample 1: 0.60% → **3.00%** (+400% improvement)

**Files Modified**:
- `checks/confidence_check.py` - Added artifact pattern detection
- `utils/document_processor.py` - Filter artifacts in language detection

### 2. Full Text Extraction ✅

**Problem**: Difficult to debug OCR and language detection issues without seeing extracted text.

**Solution**: Added `SHOW_FULL_TEXT` configuration to display all extracted OCR text.

**Usage**:
```python
# In test_readability.py (top of file)
SHOW_FULL_TEXT = True  # Enabled by default
```

```bash
# Command line override
python test_readability.py dataset/ --full-text -v
```

**Files Modified**:
- `test_readability.py` - Added full text output feature

### 3. Weighted Confidence Calculation ✅

**Problem**: Original confidence calculation treated all OCR boxes equally, penalizing documents with sparse text.

**Solution**: Weighted averaging gives more importance to boxes containing actual text.

**Result**: Better accuracy for ID cards and documents with sparse text layouts.

**Files Modified**:
- `checks/confidence_check.py` - Added `_extract_confidences_filtered()`

### 4. Expanded Language Detection ✅

**Problem**: Italian ID documents were misclassified as English due to limited keyword list.

**Solution**: Added 30+ Italian keywords specific to ID cards.

**Keywords Added**:
- Personal data: `cognome`, `nome`, `luogo di nascita`, `sesso`
- Document info: `scadenza`, `tipo di documento`, `rilascio`
- Locations: `questura`, `milano`, `roma`, `provincia di`

**Files Modified**:
- `config.json` - Expanded Italian language keywords

---

## Test Results

| File | Original | After All Fixes | Status |
|------|----------|----------------|--------|
| `sample1.pdf` | 0.60% | 3.00% | Improved (still low due to artifacts) |
| `sample2.pdf` | 18.93% | **31.18%** | ✅ **PASSES** (threshold: 15%) |
| `sample3.pdf` | 0.00% | 0.00% | Unreadable (all artifacts) |

---

## Usage

### Basic Readability Check

```bash
# Scan folder with default settings
python test_readability.py dataset/italian_ids/

# Verbose mode with full text output
python test_readability.py dataset/italian_ids/ -v

# Custom thresholds
python test_readability.py dataset/italian_ids/ --threshold 20 --full-text
```

### Configuration

Edit `test_readability.py` (top of file):

```python
# Thresholds
DEFAULT_READABILITY_THRESHOLD = 15  # OCR confidence (0-100)
DEFAULT_EMPTINESS_THRESHOLD = 0.5   # Ink ratio (%)

# Debug settings
SHOW_FULL_TEXT = True  # Show full extracted text
```

---

## Project Structure

```
doc-quality-check/
├── checks/                     # Quality check modules
│   ├── confidence_check.py    # OCR confidence calculation
│   └── clarity_check.py       # Ink ratio calculation
├── utils/                      # Utility modules
│   ├── document_processor.py  # Document processing
│   └── text_filter.py         # Text filtering utilities
├── modules/                    # Feature modules
├── dataset/                    # Test documents
├── temp_debugs/               # Debug scripts (temporary)
├── test_readability.py        # Main test utility
├── app.py                     # Streamlit application
└── config.json                # Configuration
```

---

## Recommendations

### For Best Results

1. **Use Direct PDF Exports** (not screenshots)
   - Artifact filtering helps, but clean sources are better

2. **Enable Verbose Mode for Debugging**
   ```bash
   python test_readability.py dataset/ -v
   ```

3. **Review Extracted Text**
   - Check what OCR is actually reading
   - Identify documents with screenshot artifacts

### Known Limitations

- **Sample 3** (0.00%): PDF is entirely a web screenshot with no readable document content
- **Sample 1** (3.00%): Contains significant screenshot artifacts that limit accuracy

---

## Debug Tools

Debug scripts and temporary files are kept in `temp_debugs/` folder:

```bash
temp_debugs/
├── diagnose_italian_ids.py    # Detailed diagnostic tool
├── test_filter_comparison.py  # Artifact filtering comparison
├── test_improved_confidence.py # Confidence tests
└── *.html                      # Generated reports
```

These can be safely deleted if not needed.

---

## Documentation

- `README.md` - Main project documentation
- `LANGUAGE_CONFIGURATION_GUIDE.md` - Language configuration guide
- `THRESHOLD_ANALYSIS_REPORT.md` - Threshold analysis
- `temp_debugs/ARTIFACT_FILTERING.md` - Detailed artifact filtering docs
- `temp_debugs/FULL_TEXT_FEATURE.md` - Full text extraction feature docs

---

## Next Steps

1. **Re-capture Problematic PDFs**
   - Sample 1 and Sample 3 need clean source files
   - Export directly from original documents (not screenshots)

2. **Fine-tune Thresholds**
   - Current: 15% readability threshold
   - Adjust based on production document quality

3. **Add More Artifact Patterns**
   - Browser window titles
   - Email headers/footers
   - PDF reader UI elements

---

## Summary

✅ **Artifact Filtering** - Excludes screenshot noise from confidence calculation
✅ **Full Text Output** - Shows all extracted OCR text for debugging
✅ **Weighted Confidence** - Better accuracy for sparse text documents
✅ **Expanded Language Detection** - 30+ new Italian keywords

**Overall Improvement**: Sample 2 now passes readability check (31.18% vs 18.93% original).
