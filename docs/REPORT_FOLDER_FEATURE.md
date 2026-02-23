# Report Folder Feature

**Date**: February 22, 2026  
**Status**: ✅ Implemented

---

## 🎯 Feature Overview

All readability check reports are now automatically saved to a dedicated `report/` folder with:
- **Auto-increment ID** (001, 002, 003...)
- **Timestamp** (YYYYMMDD_HHMMSS)
- **Descriptive naming** (report_001_20260222_232904.html)

---

## 📁 File Naming Convention

```
report/
├── report_001_20260222_232904.html
├── report_002_20260222_232922.html
├── report_003_20260223_101530.txt
└── ...
```

### Format Breakdown

```
report_<ID>_<TIMESTAMP>.<EXTENSION>
   │      │        │
   │      │        └─ html or txt
   │      └─ YYYYMMDD_HHMMSS (local time)
   └─ Auto-increment (001, 002, 003...)
```

---

## 🚀 Usage

### Basic Usage (Auto-Generated Name)

```bash
# Reports automatically saved to report/ folder
python test_readability.py dataset/italian_ids/
```

**Output**:
```
[OK] Results saved to: C:\...\report\report_001_20260222_232904.html
     Report folder: C:\...\report
```

### Custom Output File

```bash
# Specify custom filename (bypasses auto-naming)
python test_readability.py dataset/italian_ids/ -o my_custom_report.html
```

**Output**:
```
[OK] Results saved to: C:\...\my_custom_report.html
```

---

## 📊 Features

### 1. Auto-Increment ID

- **Purpose**: Easily identify the latest report
- **Format**: 3-digit number (001, 002, 003...)
- **Logic**: Counts existing reports and increments

### 2. Timestamp

- **Purpose**: Track when report was generated
- **Format**: YYYYMMDD_HHMMSS (e.g., 20260222_232904)
- **Timezone**: Local PC time

### 3. Report Folder

- **Location**: `report/` in project root
- **Auto-Created**: Created automatically on first run
- **Organization**: All reports in one place

---

## 🎨 Example Output

### Console Output

```
============================================================
Document Readability Check Utility
============================================================

[OK] Tesseract path set to: C:\Program Files\Tesseract-OCR\tesseract.exe
[OK] Tesseract version: 5.5.0.20241111
Folder: C:\Users\ahamed.kabeer\Desktop\poc\doc-quality-check\dataset\italian_ids
Readability Threshold: 15%
Emptiness Threshold: 0.5%
Recursive: No (top-level only)
Output File: report/ (auto-generated with ID and timestamp)
Primary Language: ITA
Auto-Detect: Yes

Found 3 file(s) to process:
...

============================================================
RESULTS SUMMARY
============================================================
Total Pages Processed: 3
Readable Pages: 3 (100.0%)
Average Confidence Score: 49.46
Execution Time: 4.55 seconds

[OK] Results saved to: C:\Users\ahamed.kabeer\Desktop\poc\doc-quality-check\report\report_001_20260222_232904.html
     Report folder: C:\Users\ahamed.kabeer\Desktop\poc\doc-quality-check\report
============================================================
```

---

## 📋 Benefits

### Before

```
Root directory:
├── readability_results_20260222_100322.html
├── readability_results_20260222_104229.html
├── readability_results_20260222_105338.html
├── italian_ids_results.html
└── final_test.html
```

**Problems**:
- ❌ Clutters root directory
- ❌ Hard to find latest report
- ❌ Inconsistent naming
- ❌ Mixed with production files

### After

```
Root directory: (Clean!)
├── app.py
├── test_readability.py
└── config.json

report/ folder:
├── report_001_20260222_232904.html
├── report_002_20260222_232922.html
└── report_003_20260223_101530.html
```

**Benefits**:
- ✅ Clean root directory
- ✅ Easy to identify latest (highest ID)
- ✅ Consistent naming convention
- ✅ Organized in dedicated folder

---

## 🔧 Technical Details

### Implementation

**File**: `test_readability.py`

**Key Changes**:
```python
# Create report folder
report_folder = Path(DEFAULT_OUTPUT_FOLDER) / 'report'
report_folder.mkdir(exist_ok=True)

# Count existing reports
existing_reports = list(report_folder.glob('report_*.html'))
next_id = len(existing_reports) + 1

# Generate filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = report_folder / f'report_{next_id:03d}_{timestamp}.html'
```

### Git Ignore

Added to `.gitignore`:
```gitignore
# Generated reports
report/
```

**Reason**: Reports are generated artifacts, not source code.

---

## 📝 Usage Examples

### Example 1: Quick Test

```bash
python test_readability.py dataset/italian_ids/
```

**Result**: `report/report_004_20260223_143022.html`

### Example 2: With Verbose Output

```bash
python test_readability.py dataset/italian_ids/ -v
```

**Result**: `report/report_005_20260223_143530.html` (with detailed console output)

### Example 3: Custom Thresholds

```bash
python test_readability.py dataset/italian_ids/ --threshold 25
```

**Result**: `report/report_006_20260223_144215.html`

### Example 4: Custom Filename (Bypass Auto-Naming)

```bash
python test_readability.py dataset/italian_ids/ -o final_report.html
```

**Result**: `final_report.html` (in current directory, not report/)

---

## 🎯 Finding the Latest Report

### Method 1: By ID (Recommended)

```bash
# Windows
dir report /B /O-D

# Linux/Mac
ls -lt report/
```

**Result**: Latest report appears first (highest ID).

### Method 2: By Timestamp

Filename format ensures chronological sorting:
```
report_001_20260222_232904.html
report_002_20260222_232922.html
report_003_20260223_101530.html
```

---

## 🗂️ Folder Structure

```
doc-quality-check/
├── 📄 Root Files (Clean!)
│   ├── app.py
│   ├── test_readability.py
│   └── config.json
│
├── 📊 report/ (Generated Reports)
│   ├── report_001_20260222_232904.html
│   ├── report_002_20260222_232922.html
│   ├── report_003_20260223_101530.html
│   └── ...
│
├── 📚 docs/
├── 🧪 tests/
└── ...
```

---

## ✅ Summary

**What Changed**:
- ✅ Reports saved to `report/` folder
- ✅ Auto-increment ID (001, 002, 003...)
- ✅ Timestamp in filename (YYYYMMDD_HHMMSS)
- ✅ Clean root directory
- ✅ Easy to find latest report

**How to Use**:
```bash
python test_readability.py dataset/
# Check report/ folder for results
```

**Latest Report**: Look for highest ID number in `report/` folder.

---

**Status**: ✅ Implemented and tested  
**Next**: Use for all readability checks
