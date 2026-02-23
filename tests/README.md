# Tests

This folder contains test utilities and test scripts for the document quality checker.

## 🧪 Available Tests

### Main Test Utility
- **[test_readability.py](../test_readability.py)** - Main readability test CLI tool

### Test Scripts
- **[analyze_thresholds.py](./analyze_thresholds.py)** - Threshold analysis tests
- **[check_lang.py](./check_lang.py)** - Language detection tests
- **[test_filter_comparison.py](./test_filter_comparison.py)** - Artifact filtering comparison
- **[test_improved_confidence.py](./test_improved_confidence.py)** - Confidence calculation tests
- **[test_italian_summary.py](./test_italian_summary.py)** - Italian ID summary tests

## 📁 Test Structure

```
tests/
├── README.md (this file)
├── analyze_thresholds.py           # Threshold analysis
├── check_lang.py                   # Language detection tests
├── test_filter_comparison.py       # Artifact filtering comparison
├── test_improved_confidence.py     # Confidence calculation tests
└── test_italian_summary.py         # Italian ID tests
```

## 🚀 Running Tests

### Basic Readability Test
```bash
python test_readability.py dataset/italian_ids/
```

### Verbose Mode with Full Text
```bash
python test_readability.py dataset/italian_ids/ -v --full-text
```

### Custom Thresholds
```bash
python test_readability.py dataset/italian_ids/ --threshold 20 --emptiness-threshold 0.3
```

### Filter Comparison Test
```bash
python test_filter_comparison.py
```

### Italian ID Summary
```bash
python test_italian_summary.py
```

## 📊 Test Dataset

Test documents are located in:
- `../dataset/` - Current test documents
- `../dataset-v1/` - Previous version test documents

### Italian ID Test Files
- `italian_id_front_back_sample1.pdf` - Screenshot with artifacts
- `italian_id_front_back_sample2.pdf` - Clean Italian ID (passes) ✅
- `italian_id_front_back_sample3_only_front.pdf` - Web screenshot (fails)

## 🔗 Related Folders

- [Main Test Utility](../test_readability.py)
- [Documentation](../docs/)
- [Temp Debugs](../temp_debugs/)
