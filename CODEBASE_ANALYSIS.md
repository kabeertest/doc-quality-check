# Document Quality Check - Codebase Analysis Report

**Date**: February 17, 2026  
**Analyzed**: Python codebase for identity card detection and document quality validation

---

## EXECUTIVE SUMMARY

This codebase has a **well-structured core** but contains several **unused modules, functions, and deprecated files** that can be safely removed. The main app flow is clean, but there are optimizations possible.

- **Total unused files**: 5 files (2 temporary, 1 unused check module, 2 documentation)
- **Total deprecated files**: 2 files (wrappers at project root)
- **Unused functions**: 8+ functions defined but never called
- **Core files essential**: 11 files

---

## 1. UNUSED FILES - CAN BE SAFELY DELETED

### Temporary Files (Test/Debug)
These files were created for testing Italian ID documents and are not part of the production flow:

| File | Size | Purpose | Action |
|------|------|---------|--------|
| [tmp_process_italian_id.py](tmp_process_italian_id.py) | ~300 bytes | Temporary Italian ID processing test | **DELETE** |
| [tmp_run_italian_id.py](tmp_run_italian_id.py) | ~400 bytes | Temporary Italian ID test runner | **DELETE** |

### Unused Check Module
| File | Size | Purpose | Action |
|------|------|---------|--------|
| [checks/confidence_check_optimized.py](checks/confidence_check_optimized.py) | ~7 KB | Alternative confidence calculation module (never imported) | **DELETE** |

### Development/Info Files (Optional)
| File | Purpose | Keep? |
|------|---------|-------|
| [dev_notes.txt](dev_notes.txt) | Tesseract installation notes | Optional - can delete if info is documented elsewhere |
| [IMPROVEMENTS.md](IMPROVEMENTS.md) | Documentation of UI improvements | Keep for reference/history |
| [README.md](README.md) | Project documentation | Keep - essential for users |

### Deprecated Root-Level Wrappers
These files redirect to newer implementations in `/utils` directory with deprecation warnings:

| File | Status | Reason | Action |
|------|--------|--------|--------|
| [content_extraction.py](content_extraction.py) | DEPRECATED | Wraps `utils/content_extraction.py` | **DELETE** or keep for backward compatibility |
| [document_processor.py](document_processor.py) | DEPRECATED | Wraps `utils/document_processor.py` | **DELETE** or keep for backward compatibility |

> **Note**: If no external code depends on these root-level wrappers, delete them. The real implementations in `/utils` are the ones being used.

---

## 2. UNUSED MODULES - Functions Defined But Never Called

### In `utils/text_cleaner.py`
These utility functions are defined but **never called** in the codebase. Only `clean_text()` is actively used.

| Function | Lines | Called From | Status | Recommendation |
|----------|-------|-------------|--------|-----------------|
| `sanitize_for_display()` | 55-73 | Never | **UNUSED** | DELETE if not needed for future features |
| `is_garbage_text()` | 75-94 | Never | **UNUSED** | DELETE if not needed for future features |
| `clean_label_text()` | 96-109 | Never | **UNUSED** | DELETE if not needed for future features |

**Only Used Function**: `clean_text()` - Lines 9-54  
  ✓ Called in [app.py](app.py#L770) and [modules/document_segmentation.py](modules/document_segmentation.py#L552)

---

### In `checks/clarity_check.py`
| Function | Lines | Called From | Status | Recommendation |
|----------|-------|-------------|--------|-----------------|
| `is_page_clear()` | 41-55 | Never | **UNUSED** | DELETE - app uses `calculate_ink_ratio()` instead |

**Only Used Function**: `calculate_ink_ratio()` - Lines 11-40  
  ✓ Called in [app.py](app.py#L241), [utils/document_processor.py](utils/document_processor.py#L12), [modules/identity_detection.py](modules/identity_detection.py#L15)

---

### In `checks/confidence_check.py`
| Function | Lines | Called From | Status | Recommendation |
|----------|-------|-------------|--------|-----------------|
| `is_page_readable()` | 339-350 | Never | **UNUSED** | DELETE - app uses `calculate_ocr_confidence()` wrapper instead |
| `resize_image_for_ocr()` | 17-48 | Internal use | **INTERNAL** | Keep - used by confidence functions |
| `_extract_confidences_from_ocr_data()` | 49-73 | Internal use | **INTERNAL** | Keep - used by confidence functions |
| `calculate_ocr_confidence_fast()` | 75-144 | Via wrapper | **USED** | Keep |
| `calculate_ocr_confidence_superfast()` | 145-209 | Via wrapper | **USED** | Keep |
| `calculate_ocr_confidence_balanced()` | 210-301 | Via wrapper | **USED** | Keep |

**Main Wrapper Used**: `calculate_ocr_confidence()` - Lines 302-337  
  ✓ Called in [app.py](app.py#L242), [utils/document_processor.py](utils/document_processor.py#L13), [modules/identity_detection.py](modules/identity_detection.py#L16)

---

### In `modules/visualization.py`
| Function | Lines | Called From | Status | Recommendation |
|----------|-------|-------------|--------|-----------------|
| `create_document_type_colors()` | 125-142 | Never | **UNUSED** | DELETE - app uses `config.get_document_type_color()` instead |
| `create_side_colors()` | 145-158 | Never | **UNUSED** | DELETE - app uses config colors instead |

**Only Used Functions**:
- `draw_bounding_boxes()` - Lines 12-92  
  ✓ Called in [app.py](app.py#L538)
- `draw_segmentation_results()` - Lines 94-123  
  ✓ Defined but may not be called (check if needed for future)

---

### In `utils/content_extraction.py`
These functions are designed as alternative modes, but only called indirectly through the wrapper:

| Function | Purpose | Called From | Status |
|----------|---------|-------------|--------|
| `extract_text_content_superfast()` | Lines 47-75 | Only via `extract_text_content()` with mode='superfast' | **Available but rarely used** |
| `extract_text_content_fast()` | Lines 77-102 | Via wrapper, and directly in app | **USED** ✓ |
| `extract_text_content_balanced()` | Lines 123-149 | Via wrapper with mode='balanced' | **Available but not used by app** |

**Main Wrapper Used**: `extract_text_content()` - Lines 104-121  
  ✓ Called in [app.py](app.py) at lines 732 and 831

**Other Used Functions**:
- `extract_json_keys()` - Lines 150-191  
  ✓ Called in [utils/content_extraction.py](utils/content_extraction.py#L217) (internal use)
- `display_content_in_sidebar()` - Lines 192-230  
  ✓ Called in [app.py](app.py#L876)

---

## 3. UNUSED IMPORTS IN KEY FILES

### In `app.py` (Lines 1-12)

| Import | Used | Evidence |
|--------|------|----------|
| `streamlit as st` | ✓ YES | Used throughout (st.set_page_config, st.title, etc.) |
| `pytesseract` | ✓ YES | Used for Tesseract path setup (lines 19-42) |
| `PIL.Image` | ✓ YES | Used for image handling |
| `numpy as np` | ✗ **NO** | Imported but never used directly in app.py |
| `pandas as pd` | ✓ YES | Used for DataFrames (st.dataframe calls) |
| `os` | ✓ YES | Used for os.name, os.path.join, os.environ |
| `cv2` | ✗ **NO** | Imported but never used directly in app.py |
| `time` | ✗ **NO** | Imported but never used directly in app.py |
| `extract_page_data` | ✓ YES | Called at line 363 |
| `display_content_in_sidebar, extract_text_content` | ✓ YES | Called at lines 876 and 732, 831 |
| `calculate_ink_ratio` | ✓ YES | Called at line 241 |
| `calculate_ocr_confidence` | ✓ YES | Called at line 242 |

**UNUSED IMPORTS TO REMOVE FROM app.py**:
- `numpy as np` (line 4)
- `cv2` (line 7)
- `time` (line 8)

---

### In `utils/document_processor.py`

| Import | Used | Evidence |
|--------|------|----------|
| `fitz` (PyMuPDF) | ✓ YES | Used for PDF processing (fitz.open) |
| `cv2` | ✓ YES | Used for image operations |
| `PIL.Image` | ✓ YES | Used for image handling |
| `numpy` | ✓ YES | Used for image arrays |
| `io` | ✓ YES | Used for BytesIO |
| `time` | ✓ YES | Used for timing metrics |
| `re` | ✓ YES | Used in detect_document_language() |
| `calculate_ink_ratio` | ✓ YES | Used for quality metrics |
| `calculate_ocr_confidence` | ✓ YES | Used for OCR metrics |
| `extract_text_content` | ✓ YES | Used for text extraction |

**All imports used** ✓

---

### In `modules/identity_detection.py`

| Import | Used | Evidence |
|--------|------|----------|
| `fitz` | ✓ YES | Used for PDF pages |
| `cv2` | ✓ YES | Used for image operations |
| `numpy` | ✓ YES | Used for image arrays |
| `PIL.Image` | ✓ YES | Used for image handling |
| `io` | ✓ YES | Used for BytesIO |
| `Enum` | ✓ YES | DocumentType and DocumentSide enums |
| `typing` | ✓ YES | Type hints |
| `dataclass` | ✓ YES | IdentityCardClassification |
| `extract_page_data` | ✓ YES | Used in detect_identity_documents() |
| `calculate_ink_ratio` | ✓ YES | Used in classification |
| `calculate_ocr_confidence` | ✓ YES | Used in classification |
| `logging` | ✓ YES | For logger |
| `get_logger` | ✓ YES | For debug logging |
| `extract_text_content` | ✓ YES | For text extraction |

**All imports used** ✓

---

## 4. FILES TO KEEP - Core Dependencies

### Critical Files (Main Flow)

**Primary Entry Point:**
1. [app.py](app.py) - ✓ **KEEP** - Main Streamlit application

**Configuration:**
2. [config.json](config.json) - ✓ **KEEP** - Detection keywords and settings
3. [modules/config_loader.py](modules/config_loader.py) - ✓ **KEEP** - Loads and manages config

**Quality Checks:**
4. [checks/clarity_check.py](checks/clarity_check.py) - ✓ **KEEP** - Ink ratio calculation
5. [checks/confidence_check.py](checks/confidence_check.py) - ✓ **KEEP** - OCR confidence scoring

**Document Processing:**
6. [utils/document_processor.py](utils/document_processor.py) - ✓ **KEEP** - PDF/image extraction
7. [utils/content_extraction.py](utils/content_extraction.py) - ✓ **KEEP** - Text extraction via OCR

**Identity Detection:**
8. [modules/identity_detection.py](modules/identity_detection.py) - ✓ **KEEP** - Core detection logic
9. [modules/document_segmentation.py](modules/document_segmentation.py) - ✓ **KEEP** - Multi-document handling

**Utilities:**
10. [modules/visualization.py](modules/visualization.py) - ✓ **KEEP** - Bounding box drawing
11. [utils/text_cleaner.py](utils/text_cleaner.py) - ✓ **KEEP** (keep at least `clean_text()`)
12. [utils/logger.py](utils/logger.py) - ✓ **KEEP** - Debug logging

### Optional/Reference Files:
- [requirements.txt](requirements.txt) - ✓ **KEEP** - Dependency list
- [README.md](README.md) - ✓ **KEEP** - User documentation
- [IMPROVEMENTS.md](IMPROVEMENTS.md) - ✓ **KEEP** - Change history
- [setup/start.bat](setup/start.bat) - ✓ **KEEP** - Windows startup script
- [dataset/](dataset/) - ✓ **KEEP** - Test files (if actively used)

### All __init__.py files:
- ✓ **KEEP** - [modules/__init__.py](modules/__init__.py), [checks/__init__.py](checks/__init__.py), [utils/__init__.py](utils/__init__.py)
- These are required for Python package imports

---

## 5. DEPENDENCY FLOW DIAGRAM

```
app.py (MAIN)
├── utils/document_processor.py ✓
│   ├── checks/clarity_check.py ✓
│   ├── checks/confidence_check.py ✓
│   └── utils/content_extraction.py ✓
├── utils/content_extraction.py ✓
├── checks/clarity_check.py ✓
├── checks/confidence_check.py ✓
├── modules/config_loader.py ✓
├── modules/identity_detection.py ✓
│   ├── utils/document_processor.py ✓
│   ├── checks/clarity_check.py ✓
│   ├── checks/confidence_check.py ✓
│   ├── utils/logger.py ✓
│   └── utils/content_extraction.py ✓
├── modules/document_segmentation.py ✓
│   ├── utils/text_cleaner.py ✓ (clean_text only)
│   └── modules/config_loader.py ✓
├── modules/visualization.py ✓
│   └── modules/document_segmentation.py ✓
├── utils/text_cleaner.py ✓ (clean_text only)
└── config.json ✓

Legend:
✓ = KEEP
✗ = DELETE or OPTIONAL
```

---

## 6. CLEANUP RECOMMENDATIONS

### PHASE 1: Safe Deletions (No Impact)

**Delete these files immediately:**
```
1. tmp_process_italian_id.py       (temp test file)
2. tmp_run_italian_id.py           (temp test file)
3. checks/confidence_check_optimized.py  (unused module)
```

**Delete or keep based on need:**
```
4. dev_notes.txt    (keep if no other doc exists, else delete)
5. content_extraction.py     (delete if no external code uses it)
6. document_processor.py     (delete if no external code uses it)
```

---

### PHASE 2: Code Cleanup

**Delete unused functions:**

| Location | Functions | Impact |
|----------|-----------|--------|
| [utils/text_cleaner.py](utils/text_cleaner.py) | `sanitize_for_display()`, `is_garbage_text()`, `clean_label_text()` | **LOW** - Keep `clean_text()` only |
| [checks/clarity_check.py](checks/clarity_check.py) | `is_page_clear()` | **LOW** - Not used |
| [checks/confidence_check.py](checks/confidence_check.py) | `is_page_readable()` | **LOW** - Not used |
| [modules/visualization.py](modules/visualization.py) | `create_document_type_colors()`, `create_side_colors()` | **LOW** - App uses config colors |

---

### PHASE 3: Import Cleanup

**Remove unused imports from [app.py](app.py#L1-L8):**

```python
# DELETE these lines:
import numpy as np      # (line 4) - Never used
import cv2              # (line 7) - Never used  
import time             # (line 8) - Never used

# KEEP these lines - all are used
import streamlit as st
import pytesseract
from PIL import Image
import pandas as pd
import os
from utils.document_processor import extract_page_data
from utils.content_extraction import display_content_in_sidebar, extract_text_content
from checks.clarity_check import calculate_ink_ratio
from checks.confidence_check import calculate_ocr_confidence
```

---

### PHASE 4: Reorganization (Optional)

**Consider moving test file:**
- Move [tests/test_identity_detection.py](tests/test_identity_detection.py) to a separate test runner (pytest) if tests need to be executed
- Currently not integrated into the main flow

---

## 7. SUMMARY TABLE

| Category | Count | Status | Action |
|----------|-------|--------|--------|
| **Total Python Files** | 26 | - | - |
| Files to DELETE | 3-5 | Temp/Unused | Delete immediately |
| Deprecated Wrappers | 2 | Optional | Delete or keep for compatibility |
| Core Files to KEEP | 11 | Essential | No changes |
| Unused Functions | 8+ | Can remove | Phase 2 cleanup |
| Unused Imports | 3 | In app.py | Phase 3 cleanup |
| **Total Lines of Dead Code** | ~500+ | - | Can be removed |

---

## 8. CONCLUSION

Your codebase is **well-organized overall** with:
- ✅ Clear modular structure
- ✅ Good configuration management
- ✅ Proper separation of concerns
- ⚠️ Some unused convenience functions
- ⚠️ A few temporary test files

**Recommended cleanup would save ~10% of codebase size** and improve maintainability by removing dead code.

**Priority**: Delete temporary files first (Phase 1), then consider function cleanup (Phase 2-3).

---

**End of Report**
