# Project Organization Specification

## Overview
This document outlines the organizational structure and rules for the doc-quality-check project. All future modifications should reference this specification to maintain consistent organization.

## Directory Structure
```
doc-quality-check/
├── app.py                    # Main application entry point
├── create_sample_pdfs.py     # Utility for creating sample PDFs
├── debug_confidence.py       # Debugging script for confidence issues
├── debug_empty_pdf.py        # Debugging script for empty PDF issues
├── PROJECT_SPEC.md          # This specification file
├── setup/                   # Setup and configuration files
│   ├── requirements.txt     # Python dependencies
│   ├── install_tesseract.bat # Tesseract OCR installation script
│   └── start_app.bat        # Application startup script
├── test/                    # Test files and utilities
│   ├── test_all_dataset_types.py
│   ├── test_app.py
│   ├── test_app_setup.py
│   ├── test_app_startup.py
│   ├── test_comprehensive_quality.py
│   ├── test_dataset_confidence.py
│   ├── test_ocr_direct.py
│   └── test_simple_app.py
├── dataset/                 # Dataset files for testing
│   ├── empty-pdfs/
│   ├── unclear-pdfs/
│   └── valid-pdfs/
└── other directories...     # Other supporting directories
```

## Organizational Rules

### 1. Setup Files
Files related to project setup, dependencies, and configuration must be placed in the `setup/` directory:
- `requirements.txt` - Contains all Python dependencies
- Installation scripts (e.g., `install_tesseract.bat`)
- Startup/configuration scripts (e.g., `start_app.bat`)
- Environment configuration files
- Docker/compose files if applicable

### 2. Test Files
All test-related files must be placed in the `test/` directory:
- Unit test files (files starting with `test_` or ending with `_test.py`)
- Integration test files
- Test utilities and helpers
- Test configuration files
- Mock data specifically for testing

### 3. Main Application Files
Core application files remain in the root directory:
- Main application entry points (e.g., `app.py`)
- Core business logic files
- Configuration files that are actively used by the main application
- Utility files that are central to the application's functionality

### 4. Dataset Files
Dataset files are kept in the `dataset/` directory and organized by type:
- `empty-pdfs/` - Contains PDFs that are intentionally empty
- `unclear-pdfs/` - Contains PDFs with low quality or unclear content
- `valid-pdfs/` - Contains properly formatted PDFs for testing

### 5. Debugging Files
Debugging and diagnostic files remain in the root directory as they are temporary utilities for troubleshooting.

## Modification Guidelines

Before making any structural changes to the project:

1. **Reference this specification** to ensure compliance with the organizational rules
2. **Consider the purpose** of the new file/component:
   - Is it for setup/configuration? → Place in `setup/`
   - Is it for testing? → Place in `test/`
   - Is it core functionality? → Place in root or appropriate module
   - Is it dataset/sample data? → Place in `dataset/`

3. **Update this specification** if new categories or exceptions are needed
4. **Maintain consistency** with existing patterns in the project

## Exceptions
Any deviation from these rules must be documented with justification in this specification.

## Version History
- v1.0 (February 12, 2026): Initial specification created after project reorganization
- v1.1 (February 12, 2026): Updated start_app.bat to correctly reference app.py in parent directory after reorganization
- v1.2 (February 12, 2026): Enhanced app.py with readability/emptiness checkboxes and additional columns
- v1.3 (February 12, 2026): Updated app.py to disable readability check by default, grouped quality checks, added document type identification checkbox