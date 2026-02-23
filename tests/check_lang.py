import sys
sys.path.insert(0, '.')

from utils.document_processor import detect_document_language

# Text from sample2
text = '''ANNOTAZIONI / REMARKS
QUESTURA DI MILANO
LUOGO DI NASCITA (PLACE OF BIRTH)
TEXAS
GUILLORY<<SUSAN<MICHELLE
DI PERMESSO / SCADENZA DOCUMENTO
RESIDENCE PERMIT'''

print('Text sample:', text[:100])
print()
print('Detected language:', detect_document_language(text))

# Check indicators
italian_indicators = [
    'residenza', 'residenziale', 'certificato', 'attestato', 'domicilio',
    'fronte', 'retro', 'firma', 'nato', 'nazionale', 'cittadinanza',
    'documento', 'identità', 'carta d', 'numero', 'data di',
    'comune', 'provincia', 'regione', 'indirizzo', 'via', 'corso'
]

text_lower = text.lower()
found = [ind for ind in italian_indicators if ind in text_lower]
print(f'Italian indicators found: {found}')
print(f'Count: {len(found)}')
