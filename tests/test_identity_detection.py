import os
from modules.identity_detection import process_identity_documents, DocumentType, DocumentSide


def test_italian_id_front_back_detected():
    pdf_path = os.path.join(os.getcwd(), 'dataset', 'italian_id_front_back.pdf')
    assert os.path.exists(pdf_path), f"Test PDF not found: {pdf_path}"

    with open(pdf_path, 'rb') as f:
        res = process_identity_documents(f.read(), os.path.basename(pdf_path))

    # Expect at least one detected residential_id
    types = [c.document_type for c in res]
    assert any(t == DocumentType.RESIDENTIAL_ID for t in types), f"No residential_id detected, found: {types}"

    # Expect the second sub-document (page '1-2') to be detected as BACK
    back_found = False
    for c in res:
        try:
            if str(c.page_number).endswith('1-2') or str(c.page_number) == '1-2':
                if c.document_side == DocumentSide.BACK:
                    back_found = True
        except Exception:
            continue

    assert back_found, f"No BACK side detected for sub-document 1-2. Results: {[ (c.page_number, c.document_side) for c in res ]}"
