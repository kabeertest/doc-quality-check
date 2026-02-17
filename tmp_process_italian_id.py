import json
from pathlib import Path

p = Path('dataset/italian_id_front_back.pdf')
if not p.exists():
    print('ERROR: dataset/italian_id_front_back.pdf not found')
    raise SystemExit(1)

# Try to use the project's processing function. Fall back to utils/document_processor if needed.
try:
    from modules.document_segmentation import detect_and_classify_documents_in_pdf
    func = detect_and_classify_documents_in_pdf
except Exception as e:
    try:
        from modules.identity_detection import process_identity_documents as func
    except Exception as e2:
        print('ERROR: could not import processing function:', e, e2)
        raise

with open(p, 'rb') as f:
    data = f.read()

res = func(data, p.name)
print(json.dumps(res, indent=2, ensure_ascii=False))
