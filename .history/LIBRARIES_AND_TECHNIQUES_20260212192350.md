# Document Quality Checker - Libraries & Techniques

## 📚 Libraries Used

### **1. Streamlit (`streamlit`)**
- **Purpose**: Web UI framework
- **Usage**: 
  - Page configuration (`st.set_page_config`)
  - Sidebar controls (file uploader, sliders, checkboxes)
  - Data display (tables, metrics, images, expanders)
  - Session state management (`st.session_state`)
  - File download buttons
  - Progress tracking and warnings
- **Why**: Minimal boilerplate, auto hot-reload, fast prototyping

### **2. PyMuPDF (`fitz`)**
- **Purpose**: PDF document processing
- **Usage**:
  - Open and read PDF files (`fitz.open()`)
  - Load individual pages (`doc.load_page()`)
  - Render pages to images at high resolution (`page.get_pixmap()`)
  - Matrix transformation for scaling (`fitz.Matrix(2, 2)` for 2x resolution)
- **Why**: Fast, efficient PDF handling with high-quality rendering

### **3. OpenCV (`cv2`)**
- **Purpose**: Image processing and analysis
- **Usage**:
  - Color space conversion (`cv2.cvtColor()`)
    - RGB → BGR conversion
    - BGR → Grayscale conversion
  - Gaussian blur for noise reduction (`cv2.GaussianBlur()`)
  - Adaptive thresholding for text enhancement (`cv2.adaptiveThreshold()`)
  - Otsu's automatic thresholding (`cv2.threshold()` with `THRESH_OTSU`)
  - Pixel counting (`cv2.countNonZero()`)
- **Why**: Industry-standard for image processing, highly optimized

### **4. Tesseract OCR (`pytesseract`)**
- **Purpose**: Optical Character Recognition
- **Usage**:
  - Text extraction from images (`image_to_string()`)
  - Confidence score extraction (`image_to_data()`)
  - Version checking (`get_tesseract_version()`)
  - Multiple PSM (Page Segmentation Mode) configurations
- **Why**: Open-source, high accuracy OCR engine

### **5. PIL/Pillow (`PIL.Image`)**
- **Purpose**: Image file handling
- **Usage**:
  - Open image bytes (`Image.open()`)
  - Load from BytesIO streams
  - Display in UI
- **Why**: Python standard library for image I/O

### **6. NumPy (`numpy`)**
- **Purpose**: Numerical array operations
- **Usage**:
  - Convert PIL images to arrays (`np.array()`)
  - Array shape calculations for pixel counting
- **Why**: Foundation for array-based image processing

### **7. Pandas (`pandas`)**
- **Purpose**: Data frame and table operations
- **Usage**:
  - Create results dataframe (`pd.DataFrame()`)
  - Store validation results
  - Display styled tables with color coding
- **Why**: Tabular data organization and display

### **8. Built-in Libraries**
- **`io`**: BytesIO for in-memory file handling
- **`os`**: Path detection, OS checking (`os.name == 'nt'`)
- **`json`**: JSON serialization for download
- **`re`**: Regular expressions for key-value extraction from text

---

## 🛠️ Techniques Used

### **Image Preprocessing Pipeline**

#### 1. **Color Space Conversion**
```
PDF/Image → ByteStream → PIL Image → OpenCV BGR → Grayscale
```
- Standardizes input to grayscale for consistent processing
- Removes color information (not needed for quality metrics)

#### 2. **Gaussian Blur (Noise Reduction)**
- **Function**: `cv2.GaussianBlur(gray, (1, 1), 0)`
- **Purpose**: Smooths image to reduce noise while preserving edges
- **Benefit**: Improves both ink detection and OCR confidence

#### 3. **Adaptive Thresholding (Text Enhancement)**
- **Function**: `cv2.adaptiveThreshold()` with `GAUSSIAN_C` mode
- **Purpose**: Highlights text regions by comparing each pixel to local neighborhood mean
- **Benefit**: Better OCR accuracy on low-contrast documents
- **Fallback**: Used when initial OCR confidence < 10%

#### 4. **Otsu's Binary Thresholding (Ink Detection)**
- **Function**: `cv2.threshold(gray, 0, 255, THRESH_BINARY_INV + THRESH_OTSU)`
- **Purpose**: Automatically determines optimal threshold value
- **Result**: Binary image with ink = white (255), background = black (0)
- **Metric**: `ink_ratio = non_zero_pixels / total_pixels`

---

### **OCR Confidence Scoring**

#### 1. **Multi-Mode PSM Strategy**
```
PSM 6: Assume a single uniform block of text
PSM 4: Assume a single column of text
PSM 3: Automatic page segmentation (default)
```
- Tests 3 different page segmentation modes
- Keeps best confidence score
- Handles varied document layouts (forms, columns, mixed text)

#### 2. **Confidence Filtering & Averaging**
```
For each PSM mode:
  1. Extract OCR results with confidence scores
  2. Filter: Remove empty text & invalid confidence (-1)
  3. Calculate: Mean of valid confidences
  4. Keep: Best average across modes
```
- **Invalid detection**: Text = empty OR confidence = -1
- **Result**: Average confidence (0-100 scale)

#### 3. **Adaptive Enhancement Fallback**
- If confidence < 10%, retry OCR with enhanced image
- Enhanced image = adaptive threshold version (better for degraded docs)
- Improves detection on:
  - Scanned documents with noise
  - Low-contrast text
  - Faded documents

---

### **Quality Metrics**

#### **Metric 1: Ink Ratio** (Emptiness Detection)
```
ink_ratio = (non_white_pixels) / (total_pixels) × 100
```
- **Range**: 0% (blank page) → ~40-60% (typical document)
- **Threshold**: Configurable, default 0.5%
- **Use Case**: Detect blank/blank-looking pages before OCR

#### **Metric 2: OCR Confidence** (Readability)
```
ocr_confidence = average(valid_confidence_scores)
```
- **Range**: 0 (no text detected) → 100 (perfect recognition)
- **Threshold**: Configurable, default 40
- **Use Case**: Detect unreadable/degraded text quality

---

### **Data Flow & Caching**

#### 1. **Streamlit Caching**
```python
@st.cache_data
def extract_page_data(file_bytes, file_name):
    ...
```
- Cache key: file contents + filename
- Prevents re-processing on page refresh
- Improves UX performance significantly

#### 2. **Session State Management**
```python
st.session_state.extracted_content  # Store OCR results
st.session_state.page_content       # Store per-page text
st.session_state.current_page       # Track active page
```
- Persists data across re-runs
- Enables sidebar content display
- Stores for JSON download

---

### **Text Extraction & Parsing**

#### 1. **Full Text Extraction**
- `pytesseract.image_to_string(image)` → Raw text
- Store in session state for download

#### 2. **Key-Value Pattern Detection** (Optional)
```
Regex patterns for common document formats:
- "Key: Value"  → Named captures
- "Key - Value" → Dash-separated
- Fall back to line-by-line if no pattern matches
```
- Enables structured JSON export
- Useful for form extraction

#### 3. **HTML Formatting**
```
text.replace('\n', '<br>') → Preserve line breaks in display
```

---

## 📊 Processing Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERACTION                          │
│  (File Upload → Configure Thresholds → View Results)        │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              EXTRACTION LAYER (@st.cache_data)               │
│  PDF/Image → Render → Convert → PyMuPDF + PIL + OpenCV      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│          IMAGE PREPROCESSING (OpenCV Pipeline)               │
│  Grayscale → Blur → Adaptive Threshold → Binary             │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
┌───────▼────────────┐        ┌──────────▼──────────┐
│  METRIC 1: INK     │        │ METRIC 2: CONFIDENCE│
│  Otsu Threshold    │        │ Tesseract PSM Modes │
│  Pixel Counting    │        │ Confidence Averaging│
│  ink_ratio = X%    │        │ ocr_conf = Y/100   │
└───────┬────────────┘        └──────────┬──────────┘
        │                                 │
        └────────────────┬────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│           VALIDATION LAYER (Apply Thresholds)                │
│  Compare metrics → Assign Status (Valid/Invalid) + Reason   │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              DISPLAY LAYER (Streamlit UI)                    │
│  Summary Metrics → Results Table → Visual Inspection         │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│           CONTENT EXTRACTION (Optional, On-Demand)           │
│  Full Text → Key-Value Parsing → JSON/TXT Download          │
└─────────────────────────────────────────────────────────────┘
```

---

## 💡 Key Design Decisions

| Decision | Why |
|----------|-----|
| **Multi-mode OCR** | Different docs have different layouts (forms, columns, single-block) |
| **Ink Ratio first** | Fast pre-filter before expensive OCR; catch blanks immediately |
| **Adaptive enhancement fallback** | Handles degraded PDFs (fax, scans, compressed) |
| **Streamlit caching** | Re-rendering PDFs is expensive; cache saves time |
| **Session state** | Enables stateful UX (sidebar content, per-page extraction) |
| **Configurable thresholds** | Different use cases (strict validation vs. lenient tolerance) |
| **High-res rendering (2x)** | Improves OCR accuracy on small text |

---

## 🚀 Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Render PDF page @ 2x | ~100-500ms | PyMuPDF is fast; high-res helps OCR |
| Preprocessing (blur, threshold) | ~50-100ms | OpenCV is optimized |
| Tesseract OCR (single mode) | ~200-500ms | Variable by image quality & language |
| All 3 PSM modes + fallback | ~1-2sec | Worst case; usually faster with good images |
| Cache hit (re-render) | ~0ms | Instant if file unchanged |

---

## 📦 Dependency Summary

```
Core Libraries:
├── streamlit         [UI Framework]
├── PyMuPDF (fitz)    [PDF Processing]
├── OpenCV (cv2)      [Image Processing]
├── pytesseract       [OCR]
├── Pillow (PIL)      [Image I/O]
├── pandas            [Data Tables]
└── numpy             [Array Operations]

System Dependency:
└── Tesseract-OCR     [Binary executable required]
```

---

## ⚙️ Configuration & Installation

See `setup/requirements.txt` and `setup/install_tesseract.bat` for setup instructions.

**Key requirement**: Tesseract-OCR must be installed separately and registered in PATH or specified via `pytesseract.pytesseract.tesseract_cmd`.
