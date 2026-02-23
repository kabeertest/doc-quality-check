# Code Organization Update - Experiments Folder

**Date**: February 22, 2026  
**Status**: ✅ Complete

---

## 🎯 Objective

Move experimental/unused code to dedicated `experiments/` folder while maintaining documentation for future reference.

---

## 📁 What Was Moved

### To `experiments/`

| File | From | Why Moved |
|------|------|-----------|
| `confidence_check_improved.py` | `checks/` | Experimental, not used in production |

---

## 🔍 Why This File Was Moved

### `confidence_check_improved.py`

**Status**: ⚠️ **Experimental - Not used in production**

**Features**:
- Image enhancement (2x upscaling, adaptive thresholding, sharpening)
- Multiple PSM mode testing
- Better OCR for very small/degraded text

**Why Not Production**:
- 2-3x slower than production version
- Production already has artifact filtering (better for screenshots)
- Only beneficial for specific difficult documents

**When to Use Later**:
```python
# Import from experiments
from experiments.confidence_check_improved import calculate_ocr_confidence

# Use for very difficult documents
confidence, time = calculate_ocr_confidence(
    image, 
    mode='balanced',  # or 'accurate'
    lang='ita'
)
```

---

## 📊 Current Structure

### Production Code (Used)
```
checks/
├── confidence_check.py       # ✅ PRODUCTION (artifact filtering)
├── clarity_check.py
└── __init__.py
```

### Experimental Code (Not Used)
```
experiments/
├── README.md                              # Documentation
└── confidence_check_improved.py           # ⚠️ Experimental
```

---

## 📝 Documentation Updates

### Files Updated
1. **`experiments/README.md`** - Created (new)
2. **`docs/README.md`** - Added experiments link
3. **`main README.md`** - Updated structure
4. **`.gitignore`** - Added `experiments/`
5. **`docs/CONFIDENCE_CHECK_COMPARISON.md`** - Reference maintained

### What's Documented
- Why file is experimental
- When to use it
- Performance comparison
- How to import and use

---

## 🎯 Benefits

### Before
```
checks/
├── confidence_check.py            # Production
└── confidence_check_improved.py   # Experimental (confusing!)
```

**Problem**: Unclear which file to use

### After
```
checks/
└── confidence_check.py            # ✅ Production (clear!)

experiments/
└── confidence_check_improved.py   # ⚠️ Experimental (clear!)
```

**Benefit**: Clear separation, documented for future

---

## 📋 Folder Policy

### `checks/` - Production Only
- ✅ Used by `app.py` and `test_readability.py`
- ✅ Tested and stable
- ✅ No experimental features

### `experiments/` - Experimental Code
- ⚠️ Not used in production
- 🧪 For testing new features
- 📚 Documented for future reference
- 🗑️ Can be deleted if not needed later

---

## 🔗 Related Documentation

- [Experiments README](../experiments/README.md) - Folder documentation
- [Confidence Check Comparison](./CONFIDENCE_CHECK_COMPARISON.md) - Full comparison
- [Main README](../README.md) - Project structure

---

## ✅ Verification

**Production still works**:
```bash
python test_readability.py dataset/italian_ids/
# ✅ Uses checks/confidence_check.py
# ✅ Sample 2 passes (31.18% confidence)
```

**Experimental available**:
```python
from experiments.confidence_check_improved import calculate_ocr_confidence
# ✅ Can import when needed
# ✅ Documented how to use
```

---

## 📊 Final File Count

| Folder | Files | Purpose |
|--------|-------|---------|
| `checks/` | 3 | Production quality checks |
| `experiments/` | 2 | Experimental code + docs |
| `docs/` | 9 | Documentation |
| `tests/` | 6 | Test utilities |
| `temp_debugs/` | 1 | Empty (ready for debug) |

---

**Summary**: Experimental code moved to `experiments/`, fully documented, production code is now clear and unambiguous! ✅
