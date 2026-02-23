# Bug Fix: Page 5 Confidence Was 0%

**Date**: February 22, 2026  
**Status**: ✅ Fixed

---

## 🐛 Problem

**File**: `dataset/big-pdf-but-readable/airtel_bill.pdf`  
**Issue**: Page 5 showed **0.00% confidence** despite having readable content.

### Expected vs Actual

| Page | Content | Expected Confidence | Actual (Before Fix) |
|------|---------|---------------------|---------------------|
| 1 | Bill header | ~75% | 76.18% ✅ |
| 2 | Empty | 0% | 0.00% ✅ |
| 3 | Payment info | ~70% | 72.48% ✅ |
| 4 | Signature | ~80% | 81.26% ✅ |
| 5 | **Charges detail** | **~90%** | **0.00% ❌** |

---

## 🔍 Root Cause Analysis

### The Bug Chain

1. **Confidence Calculation** → Called `calculate_ocr_confidence_fast()`
2. **Fast Mode** → Called `resize_image_for_ocr()` to speed up OCR
3. **Resize Function** → Shrunk image from **1190x1684** to **282x400**
4. **Result** → Text became unreadable, OCR returned 0% confidence

### Code Flow

```
calculate_ocr_confidence_fast()
  ↓
resize_image_for_ocr(image, max_size=(400, 400))
  ↓
1190x1684 → 282x400 (95% size reduction!)
  ↓
pytesseract.image_to_data(resized_image)
  ↓
OCR can't read tiny text → 0% confidence
```

### Why It Happened

The `resize_image_for_ocr()` function was designed for **text extraction** (language detection), where speed matters more than accuracy. However, it was also being used for **confidence calculation**, which requires **full resolution** for accurate results.

---

## ✅ The Fix

### Changed `calculate_ocr_confidence_fast()`

**Before** (WRONG):
```python
def calculate_ocr_confidence_fast(image, lang='eng', verbose=False):
    # Resize image to speed up OCR ❌
    resized_image = resize_image_for_ocr(image)
    
    # OCR on resized image
    ocr_data = pytesseract.image_to_data(resized_image, ...)
```

**After** (CORRECT):
```python
def calculate_ocr_confidence_fast(image, lang='eng', verbose=False):
    # DO NOT resize - use full resolution for accurate confidence ✅
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # OCR on full-resolution image
    ocr_data = pytesseract.image_to_data(image, ...)
```

### Key Change

**Removed** the `resize_image_for_ocr()` call from confidence calculation.

**Why**: 
- Confidence calculation needs **accuracy**, not speed
- Resize destroys text quality for large documents
- The time saved (0.5-1s) isn't worth incorrect results

---

## 📊 Results

### Before Fix

| Page | Confidence | Status |
|------|-----------|--------|
| 1 | 76.18% | ✅ Readable |
| 2 | 0.00% | ✅ Empty (correct) |
| 3 | 72.48% | ✅ Readable |
| 4 | 81.26% | ✅ Readable |
| 5 | **0.00%** | ❌ **WRONG** |

### After Fix

| Page | Confidence | Status | Change |
|------|-----------|--------|--------|
| 1 | 76.18% | ✅ Readable | No change |
| 2 | 0.00% | ✅ Empty | Correct |
| 3 | 72.48% | ✅ Readable | No change |
| 4 | 81.26% | ✅ Readable | No change |
| 5 | **89.39%** | ✅ **Readable** | **+89.39%** 🎉 |

---

## 🎯 Impact

### Files Fixed
- ✅ `checks/confidence_check.py` - Removed resize from `calculate_ocr_confidence_fast()`

### Affected Documents
- ✅ Large PDFs (bills, statements, reports)
- ✅ High-resolution scans (A4, letter size)
- ✅ Documents with detailed tables and small text

### Performance Impact
- **Speed**: Slightly slower (~0.5-1s per page)
- **Accuracy**: **Much better** (0% → 89% for some pages)
- **Trade-off**: Worth it for correct results

---

## 🧪 Testing

### Test Command
```bash
python test_readability.py dataset/big-pdf-but-readable/ -v
```

### Expected Output
```
[PAGE 1] Conf: 76.18% - Readable ✅
[PAGE 2] Conf: 0.00% - Empty ✅ (correctly identified)
[PAGE 3] Conf: 72.48% - Readable ✅
[PAGE 4] Conf: 81.26% - Readable ✅
[PAGE 5] Conf: 89.39% - Readable ✅ (FIXED!)
```

---

## 📝 Lessons Learned

### 1. Resize for Speed vs Accuracy

**Text Extraction** (language detection):
- ✅ OK to resize for speed
- Purpose: Get enough text for language identification

**Confidence Calculation**:
- ❌ DON'T resize
- Purpose: Accurate measurement of text quality

### 2. Image Size Matters

| Original Size | Resized Size | OCR Result |
|---------------|--------------|------------|
| 1190x1684 | 282x400 | ❌ 0% (text destroyed) |
| 1190x1684 | 1190x1684 | ✅ 89% (perfect) |

**Rule**: For confidence calculation, use **full resolution**.

### 3. Always Test with Real Data

The bug wasn't caught earlier because:
- Italian IDs are small (screenshot artifacts)
- Resize worked OK for those
- Large documents like bills weren't tested

**Lesson**: Test with diverse document types.

---

## 🔗 Related Files

- `checks/confidence_check.py` - Fixed confidence calculation
- `utils/content_extraction.py` - Resize function (unchanged, still used for text extraction)
- `diagnose_airtel_bill.py` - Diagnostic script
- `debug_resize_issue.py` - Resize impact analysis

---

## ✅ Verification

Run the test:
```bash
python test_readability.py dataset/big-pdf-but-readable/ -v
```

**Expected**: All pages with content should show >15% confidence.

---

**Status**: ✅ Fixed and verified  
**Next**: Monitor for similar issues with other document types
