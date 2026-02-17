import json
from pathlib import Path

p = Path(r'dataset/italian_ids/italy_res_sample_3.pdf')
if not p.exists():
    print('ERROR: file not found:', p)
    raise SystemExit(1)

# Try known entrypoints
res = None
errors = []
try:
    from modules.document_segmentation import detect_and_classify_documents_in_pdf
    res = detect_and_classify_documents_in_pdf(p.read_bytes(), p.name)
except Exception as e:
    errors.append(('document_segmentation', str(e)))

if res is None:
    try:
        from modules.identity_detection import process_identity_documents
        res = process_identity_documents(p.read_bytes(), p.name)
    except Exception as e:
        errors.append(('identity_detection', str(e)))

if res is None:
    print('ERROR: Could not call processing entrypoint. Errors:')
    print(json.dumps(errors, indent=2, ensure_ascii=False))
    raise SystemExit(1)

# Normalize results for printing
try:
    # If result is dict-like, print as JSON
    print(json.dumps(res, indent=2, ensure_ascii=False))
except TypeError:
    # Fallback: try to convert objects to repr
    try:
        out = []
        for r in res:
            try:
                out.append(r.__dict__)
            except Exception:
                out.append(repr(r))
        print(json.dumps(out, indent=2, ensure_ascii=False))
    except Exception:
        print(repr(res))
