# Confidence Score - Quick Visual Guide

## 🎯 What is Confidence Score?

```
Confidence Score = How well the OCR can read the text

0% ─────────────────────────────────── 100%
│                                       │
Blank/Unreadable                    Perfect Scan
```

---

## 📊 How It's Calculated (Simple Version)

### Step 1: OCR Reads Text Boxes

```
Document Image
    ↓
[OCR Engine - Tesseract]
    ↓
Text Box 1: "Hello" (95% confident)
Text Box 2: "World" (87% confident)
Text Box 3: "" (0% - empty)
Text Box 4: "123" (92% confident)
    ↓
Average: (95 + 87 + 0 + 92) / 4 = 68.5%
```

### Step 2: Filter Out Junk

```
Before Filtering:
┌─────────────────────────────────┐
│ "file:///C:/Users/..." (90%)   │ ← JUNK
│ "2/17/26, 9:23 AM" (88%)       │ ← JUNK
│ "QUESTURA DI MILANO" (45%)     │ ← REAL
│ "LUOGO DI NASCITA" (42%)       │ ← REAL
└─────────────────────────────────┘
Average: (90+88+45+42)/4 = 66.25% ❌ WRONG

After Filtering:
┌─────────────────────────────────┐
│ "QUESTURA DI MILANO" (45%)     │ ← REAL
│ "LUOGO DI NASCITA" (42%)       │ ← REAL
└─────────────────────────────────┘
Average: (45+42)/2 = 43.5% ✅ CORRECT
```

### Step 3: Weighted Score (for sparse documents)

```
ID Card Example:
┌─────────────────────────────────┐
│ [Empty Space] [Empty Space]     │
│ [Empty Space] [Name: John]      │
│ [Empty Space] [Empty Space]     │
└─────────────────────────────────┘

Most boxes are EMPTY (0% confidence)
But text boxes have HIGH confidence

Weighted Formula:
Final = 70% × Text Confidence + 30% × Overall Confidence
      = 70% × 85% + 30% × 25%
      = 59.5% + 7.5%
      = 67% ✅ Fair score
```

---

## 📈 What Scores Mean

```
┌──────────────────────────────────────────────────────┐
│  0-15%  →  🔴 UNREADABLE (Fail)                     │
│            - Blank page or screenshot artifact       │
│            - Manual review needed                    │
├──────────────────────────────────────────────────────┤
│  15-30% →  🟡 LOW QUALITY (Pass, but marginal)      │
│            - Readable but poor quality               │
│            - Some OCR errors possible                │
├──────────────────────────────────────────────────────┤
│  30-50% →  🟢 MEDIUM QUALITY (Pass)                 │
│            - Decent quality document                 │
│            - Mostly reliable OCR                     │
├──────────────────────────────────────────────────────┤
│  50-70% →  🔵 GOOD QUALITY (Pass)                   │
│            - Clear document                          │
│            - Reliable OCR results                    │
├──────────────────────────────────────────────────────┤
│  70-100% → 🟣 EXCELLENT QUALITY (Pass)              │
│            - High-quality scan                       │
│            - Very reliable OCR                       │
└──────────────────────────────────────────────────────┘
```

---

## ✅ Real Examples

### Example 1: Italian ID (Good Quality)

```
Document: italian_id_sample2.pdf
┌─────────────────────────────────────┐
│ QUESTURA DI MILANO                  │
│ LUOGO DI NASCITA: TEXAS             │
│ GUILLORY<<SUSAN<MICHELLE            │
│ RESIDENCE PERMIT                    │
└─────────────────────────────────────┘

Confidence: 31.18% ✅
Status: READABLE (passes 15% threshold)
```

### Example 2: Screenshot with Artifacts

```
Document: italian_id_sample1.pdf
┌─────────────────────────────────────┐
│ 2/17/26, 9:23 AM ← ARTIFACT        │
│ file:///C:/Users/... ← ARTIFACT    │
│ ROSSI<<BIANCA ← REAL TEXT          │
└─────────────────────────────────────┘

Artifacts filtered out!
Confidence: 3.00% 🔴
Status: UNREADABLE (mostly artifacts)
```

### Example 3: Airtel Bill Page 5

```
Document: airtel_bill.pdf (Page 5)
┌─────────────────────────────────────┐
│ @ airtel                            │
│ YOUR CHARGES IN DETAIL              │
│ Rentals: 128.90                     │
│ Tax: 23.20                          │
│ Total: 152.10                       │
└─────────────────────────────────────┘

Confidence: 89.39% 🟣
Status: EXCELLENT QUALITY
```

---

## 🔧 How to Improve Scores

### ✅ DO This:

```
1. Use High-Quality Scans (300+ DPI)
   → Better text recognition → Higher confidence

2. Good Lighting/Contrast
   → Clear text → Higher confidence

3. Direct PDF Exports (not screenshots)
   → No artifacts → Accurate confidence

4. Crop to Document Area
   → Less noise → Better focus on content
```

### ❌ AVOID This:

```
1. Screenshots with Browser UI
   → File paths, timestamps → Filtered out → Low score

2. Blurry/Low-Resolution Images
   → OCR can't read → Low confidence

3. Complex Backgrounds
   → Confuses OCR → Lower confidence

4. Very Small Text (< 8pt)
   → Hard to recognize → Lower confidence
```

---

## 🎯 Reliability Check

### When to Trust the Score:

```
✅ Standard printed documents (bills, IDs, statements)
✅ Scanned at 300+ DPI
✅ Good contrast and lighting
✅ Latin script (English, Italian, French, etc.)
✅ No complex backgrounds

→ Reliability: 85-90%
```

### When to Double-Check:

```
⚠️ Very small text (< 8pt)
⚠️ Handwritten documents
⚠️ Non-Latin scripts (Arabic, Chinese, etc.)
⚠️ Heavily degraded documents
⚠️ Complex backgrounds

→ Reliability: 50-70%
```

### When NOT to Trust:

```
❌ Handwriting recognition
❌ Non-Latin scripts (without training)
❌ 100% accuracy requirements
❌ Legal/forensic documents

→ Use specialized tools instead
```

---

## 🧪 Quick Test

```bash
# Run readability check
python test_readability.py dataset/ -v

# Check output:
[OK] Readable, Not Empty (Conf: 89.39, Ink: 7.55%, Lang: eng)
    |   Extracted Text:
    |   @ airtel
    |   YOUR CHARGES IN DETAIL
    |   Rentals: 128.90
    |   ...

# Interpretation:
✅ High confidence (89.39%) = Reliable OCR
✅ Text matches document = Score is accurate
✅ Can trust this result
```

---

## 📊 Summary

```
┌─────────────────────────────────────────────────┐
│ Confidence Score Calculation                    │
├─────────────────────────────────────────────────┤
│ 1. OCR reads text boxes with confidence values │
│ 2. Filter out artifacts (URLs, timestamps)     │
│ 3. Calculate weighted average                   │
│ 4. Final score: 0-100%                         │
├─────────────────────────────────────────────────┤
│ Reliability: 85-90% for standard documents     │
│ Threshold: ≥15% passes, <15% fails             │
│ Best for: Printed Latin script documents        │
└─────────────────────────────────────────────────┘
```

**For detailed technical explanation**: See `CONFIDENCE_SCORE_EXPLAINED.md`
