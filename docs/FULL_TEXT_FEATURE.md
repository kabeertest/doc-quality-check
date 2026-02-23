# Full Text Extraction Feature - Added to test_readability.py

## Summary

Added configuration option to show **full extracted OCR text** in the output for debugging purposes.

---

## Changes Made

### 1. Configuration Flag (Top of File)

```python
# Debug settings
SHOW_FULL_TEXT = True  # Show full extracted text in output (for debugging)
                       # True = Show all extracted OCR text
                       # False = Show only first 200 characters
                       # Can be overridden with --full-text command line flag
```

**Default**: `True` (enabled by default for debugging)

---

### 2. Command-Line Argument

Added new `--full-text` flag:

```bash
# Use config default
python test_readability.py dataset/italian_ids/

# Force enable full text output
python test_readability.py dataset/italian_ids/ --full-text

# Verbose mode with full text
python test_readability.py dataset/italian_ids/ -v --full-text
```

---

### 3. Console Output (Verbose Mode)

When `-v` (verbose) is enabled with `SHOW_FULL_TEXT=True`:

```
[FILE] Processing: italian_ids/italian_id_front_back_sample1.pdf
   Found 1 page(s)
    +-- Page 1: [FAIL] Not Readable, Not Empty (Conf: 2.28, Ink: 18.87%, Lang: eng)
    |   Extracted Text:
    |   2/17/26, 9:23 AM Italian_electronic_ID_card_(front-back).png (600*772)
    |   z y= |  = z  \ /_ == 
    |   = 2A Be  = = 2 = i Nv e423  = . 2#-\ rN TLS GF
    |   CK1TACADOOODAAS<<K<<<<K<<ccx<<
    |   ROSSI<<BI1, NCA<<< < <<k<
```

---

### 4. HTML Output

Enhanced HTML table with:
- **Wider text column** (400px)
- **Scrollable text area** (max-height: 150px)
- **Monospace font** for better readability
- **"EXTRACTED TEXT (FULL):" label** to indicate full text mode

```html
<th style="width: 400px;">Extracted Text (Full)</th>
...
<div class="text-preview-full">
  EXTRACTED TEXT (FULL):
  <pre>
  2/17/26, 9:23 AM Italian_electronic_ID_card_(front-back).png
  QUESTURA DI MILANO
  LUOGO DI NASCITA...
  </pre>
</div>
```

---

## Use Cases

### Debugging Language Detection Issues

```bash
python test_readability.py dataset/italian_ids/ -v
```

**Output shows**:
- Extracted Italian text: `QUESTURA DI MILANO`, `LUOGO DI NASCITA`, `CODICE FISCALE`
- Detected language: `ita` ✓
- Confidence: `18.93%` (passes threshold)

### Identifying Screenshot Artifacts

```bash
python test_readability.py dataset/italian_ids/ -v
```

**Output reveals problems**:
- Timestamp: `2/17/26, 9:23 AM`
- File name: `Italian_electronic_ID_card_(front-back).png`
- URL: `https://upload.wikimedia.org/...`
- Browser path: `file:///C:/Users/ahamed.kabeer/Desktop/...`

**Root cause**: PDFs are screenshots, not direct document scans!

### Analyzing OCR Quality

```bash
python test_readability.py dataset/italian_ids/ -v
```

**Shows OCR struggles**:
- Garbled characters: ``, ``
- Broken words: `ANNOTAZION!`, `autHonY`
- Misread text: `GUILLORY` vs `GUTLLORY`

**Impact**: Low confidence scores (0-18%) due to poor OCR quality.

---

## Benefits

1. **Faster Debugging**: See exactly what OCR extracts without running separate tools
2. **Language Detection Analysis**: Verify if Italian keywords are being detected
3. **Quality Assessment**: Identify documents with screenshot artifacts or poor scan quality
4. **Threshold Tuning**: Understand why documents pass/fail readability checks

---

## Example Output Analysis

### Sample 1: Screenshot with URL Artifacts
```
Extracted Text:
  2/17/26, 9:23 AM Italian_electronic_ID_card_(front-back).png
  https://upload.wikimedia.org/wikipedia/commons/...
  ROSSI<<BI1, NCA<<<
```
**Issues**:
- Contains browser timestamp
- Includes URL paths
- MRZ text present but garbled
- **Result**: 2.28% confidence (UNREADABLE)

### Sample 2: Actual Italian ID Content
```
Extracted Text:
  QUESTURA DI MILANO
  LUOGO DI NASCITA (PLACE OF BIRTH): TEXAS
  GUILLORY<<SUSAN<MICHELLE
  RESIDENCE PERMIT
```
**Good content**:
- Italian keywords detected
- MRZ data readable
- Document structure clear
- **Result**: 18.93% confidence (READABLE) ✓

### Sample 3: Web Page Screenshot
```
Extracted Text:
  2/17/26, 5:43 PM storyblok.png
  file:///C:/Users/ahamed.kabeer/Desktop/storyblok.png
  TIPO DI SCADENZA
```
**Issues**:
- Browser screenshot (storyblok.png)
- File path visible
- Some Italian text but degraded
- **Result**: 0.00% confidence (UNREADABLE)

---

## Configuration Options

### Option 1: Enable in Config (Permanent)
```python
# In test_readability.py (top of file)
SHOW_FULL_TEXT = True  # Always show full text
```

### Option 2: Command-Line Flag (One-time)
```bash
python test_readability.py dataset/ --full-text
```

### Option 3: Disable for Clean Output
```python
SHOW_FULL_TEXT = False  # Show only 200 chars
```

```bash
python test_readability.py dataset/  # Uses config default
```

---

## Files Modified

- ✅ `test_readability.py`
  - Added `SHOW_FULL_TEXT` config flag
  - Added `--full-text` CLI argument
  - Updated `process_file()` to include full text
  - Updated `write_html_output()` with enhanced text styling
  - Added verbose text output in console

---

## Related Files

- `view_results.py` - Helper script to parse HTML output
- `ITALIAN_ID_ISSUE_ANALYSIS.md` - Detailed analysis of Italian ID confidence issues
- `diagnose_italian_ids.py` - Diagnostic tool for detailed OCR analysis

---

## Next Steps

1. **Review extracted text** to identify patterns in failing documents
2. **Re-capture problematic PDFs** without screenshot artifacts
3. **Adjust thresholds** based on actual content quality
4. **Consider pre-processing** to crop out browser UI elements
