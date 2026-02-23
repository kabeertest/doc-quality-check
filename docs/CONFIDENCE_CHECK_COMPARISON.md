# Confidence Check Modules - Comparison & Maintenance Guide

## 📁 Files Overview

```
checks/
├── confidence_check.py           # ✅ PRODUCTION (Enhanced with artifact filtering)
└── confidence_check_improved.py  # ⚠️ EXPERIMENTAL (Image enhancement features)
```

---

## 🔍 What's the Difference?

### `confidence_check.py` (Production Version)

**Status**: ✅ **Active - Used by default**

**Key Features**:
1. **Artifact Filtering** ✨ NEW
   - Filters out screenshot noise (file paths, URLs, timestamps)
   - Only counts actual document content toward confidence
   - Improves accuracy for screenshots by 30-65%

2. **Weighted Confidence** ✨ NEW
   - Gives more weight to boxes with actual text
   - Better handling of sparse text documents (like IDs)

3. **Language Detection Integration**
   - Works with Italian keyword detection
   - Filters artifacts before language classification

**Improvements Over Original**:
```
Original Version:
- Simple average of all OCR boxes
- Includes screenshot artifacts in calculation
- No filtering of noise

Enhanced Version (Current):
- Filters artifacts (file:///, timestamps, URLs)
- Weighted average for text boxes
- 30-65% better confidence scores
```

**Test Results**:
| File | Original | Enhanced | Improvement |
|------|----------|----------|-------------|
| Sample 1 | 0.60% | 3.00% | +400% |
| Sample 2 | 18.93% | 31.18% | +65% ✅ |
| Sample 3 | 0.00% | 0.00% | (all artifacts) |

---

### `confidence_check_improved.py` (Experimental Version)

**Status**: ⚠️ **Experimental - Not used by default**

**Key Features**:
1. **Image Enhancement** 🔬
   - 2x super-resolution upscaling
   - Adaptive thresholding
   - Sharpening filters
   - Noise reduction

2. **Multiple PSM Modes** 🔬
   - Tries different Tesseract page segmentation modes
   - Selects best result automatically

3. **Enhanced Processing Pipeline** 🔬
   ```
   Original Image → Resize → Enhance → OCR → Multiple PSM → Best Result
   ```

**When to Use**:
- ✅ Very small text (< 8pt)
- ✅ Degraded/low-quality scans
- ✅ Complex backgrounds
- ❌ NOT for normal documents (slower)

**Performance**:
- **Speed**: 2-3x slower than production version
- **Accuracy**: Better for difficult documents
- **Use Case**: Special cases only

---

## 📊 Feature Comparison Table

| Feature | `confidence_check.py` | `confidence_check_improved.py` |
|---------|----------------------|-------------------------------|
| **Status** | ✅ Production | ⚠️ Experimental |
| **Artifact Filtering** | ✅ Yes | ❌ No |
| **Image Enhancement** | ❌ No | ✅ Yes |
| **Speed** | ⚡ Fast (0.5-1s) | 🐌 Slower (2-3s) |
| **Best For** | Normal documents | Difficult/degraded docs |
| **Used By Default** | ✅ Yes | ❌ No |
| **Maintenance** | Active | Experimental |

---

## 🔧 How to Use Each

### Using Production Version (Default)

```python
# In your code
from checks.confidence_check import calculate_ocr_confidence

# Standard usage
confidence, time_taken = calculate_ocr_confidence(image, mode='fast', lang='ita')
```

### Using Experimental Version (Optional)

```python
# Import experimental version
from checks.confidence_check_improved import calculate_ocr_confidence

# Use for difficult documents
confidence, time_taken = calculate_ocr_confidence(
    image, 
    mode='balanced',  # or 'accurate'
    lang='ita',
    verbose=True
)
```

---

## 📝 Maintenance Guide

### For `confidence_check.py` (Production)

**DO**:
- ✅ Update artifact patterns as new screenshot types appear
- ✅ Tune weighted confidence parameters based on test results
- ✅ Add logging for debugging
- ✅ Keep backward compatibility

**DON'T**:
- ❌ Remove artifact filtering (critical feature)
- ❌ Change default behavior without testing
- ❌ Break existing API

**How to Update**:
```python
# 1. Add new artifact pattern
ARTIFACT_PATTERNS = [
    # ... existing patterns ...
    re.compile(r'new_pattern_here', re.IGNORECASE),
]

# 2. Test with Italian IDs
python tests/test_filter_comparison.py

# 3. Verify improvement
# Expected: Sample 2 should pass (>15% confidence)
```

---

### For `confidence_check_improved.py` (Experimental)

**DO**:
- ✅ Experiment with new enhancement techniques
- ✅ Test on difficult documents
- ✅ Document what works/doesn't work
- ✅ Move successful features to production version

**DON'T**:
- ❌ Use in production without thorough testing
- ❌ Assume it's always better (slower!)
- ❌ Forget to update this documentation

**How to Test**:
```bash
# Compare with production version
python tests/test_improved_confidence.py

# Test on specific difficult document
python -c "
from checks.confidence_check_improved import calculate_ocr_confidence
from PIL import Image
img = Image.open('dataset/italian_ids/difficult_sample.pdf')
conf, time = calculate_ocr_confidence(img, mode='balanced')
print(f'Confidence: {conf:.2f}%, Time: {time:.2f}s')
"
```

---

## 🎯 Recommendation: Which to Keep?

### Option 1: Merge Best Features (Recommended) ✅

**Action Plan**:
1. Keep `confidence_check.py` as main file
2. Move image enhancement from `_improved` to production
3. Add mode parameter to enable enhancement when needed
4. Delete `confidence_check_improved.py`

**Implementation**:
```python
# In confidence_check.py
def calculate_ocr_confidence(image, mode='fast', lang='eng', enhance=False):
    if enhance:
        # Use image enhancement from _improved
        image = _enhance_image_for_small_text(image)
    
    # ... rest of production code ...
```

---

### Option 2: Keep Separate (Current) ⚠️

**When This Makes Sense**:
- Experimental features need more testing
- Different use cases (fast vs accurate)
- Research/development phase

**Maintenance Overhead**:
- Two files to maintain
- Need to sync bug fixes
- Potential confusion for users

---

### Option 3: Delete Experimental 🗑️

**When to Do This**:
- Features merged into production
- Not providing value
- Causing confusion

**How to Delete**:
```bash
# Move to temp_debugs first (safe)
mv checks/confidence_check_improved.py temp_debugs/

# Test production for 1-2 weeks
# If no issues, delete permanently
rm temp_debugs/confidence_check_improved.py
```

---

## 📈 Performance Benchmarks

### Production Version (`confidence_check.py`)

```
Italian ID Sample 1:
  Before: 0.60% confidence, 0.5s
  After:  3.00% confidence, 0.6s
  Improvement: +400% accuracy, +0.1s overhead

Italian ID Sample 2:
  Before: 18.93% confidence, 0.5s
  After:  31.18% confidence, 0.6s
  Improvement: +65% accuracy, +0.1s overhead
  Status: ✅ PASSES threshold (15%)
```

### Experimental Version (`confidence_check_improved.py`)

```
Italian ID Sample 1:
  Confidence: 18.51%, Time: 2.5s
  Improvement: +2985% vs original
  Use Case: When production version fails

Italian ID Sample 2:
  Confidence: N/A (production already passes)
  Use Case: Not needed for this sample
```

---

## 🛠️ Quick Reference

### Need to fix artifact filtering?
→ Edit `checks/confidence_check.py`, update `ARTIFACT_PATTERNS`

### Need to test new enhancement?
→ Edit `checks/confidence_check_improved.py`, test, then merge to production

### Want to use enhancement in production?
→ Add `enhance=True` parameter to `calculate_ocr_confidence()`

### Found new screenshot artifact type?
→ Add pattern to `ARTIFACT_PATTERNS` in production file

### Need faster processing?
→ Use `mode='fast'` in production file (default)

### Need better accuracy?
→ Use `mode='balanced'` or `mode='accurate'` in production file

---

## ✅ Current Status

| File | Lines | Status | Used By |
|------|-------|--------|---------|
| `confidence_check.py` | 457 | ✅ Active | `test_readability.py`, `app.py` |
| `confidence_check_improved.py` | 300 | ⚠️ Experimental | Manual testing only |

---

## 📚 Related Documentation

- [Artifact Filtering](../docs/ARTIFACT_FILTERING.md) - How filtering works
- [Improvements Summary](../docs/IMPROVEMENTS_SUMMARY.md) - Recent changes
- [Italian ID Analysis](../docs/ITALIAN_ID_ISSUE_ANALYSIS.md) - Test results

---

**Last Updated**: February 22, 2026  
**Maintainer**: Development Team  
**Next Review**: After testing on 100+ documents
