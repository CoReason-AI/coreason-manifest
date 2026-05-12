import glob
import re


def clean_file(path):
    with open(path, encoding='utf-8') as f:
        text = f.read()
    
    classes_to_remove = [
        'FederatedSecurityMacroManifest',
        'FederatedPeftContract',
        'FederatedStateSnapshot',
        'FederatedCapabilityAttestationReceipt',
        'FederatedCIDFetchIntent'
    ]

    for cls in classes_to_remove:
        # remove class definition
        pattern = r'\nclass ' + cls + r'\(.*?(?=\nclass |\Z)'
        text = re.sub(pattern, '', text, flags=re.DOTALL)
        
        # remove from Unions
        text = re.sub(r'^\s*' + cls + r'\s*\|?\s*\n', '', text, flags=re.MULTILINE)
        text = re.sub(r'\s*\|\s*' + cls, '', text)
        text = re.sub(r'^\s*\|\s*' + cls + r'\n', '', text, flags=re.MULTILINE)
        
        # remove model_rebuild
        text = re.sub(r'^' + cls + r'\.model_rebuild\(\)\n', '', text, flags=re.MULTILINE)
        
        # remove from __all__ and synergistic classes
        text = re.sub(r'[\'"]' + cls + r'[\'"],?\s*\n?', '', text)
        
        # remove imports
        text = re.sub(r'^\s*' + cls + r',?\s*\n', '', text, flags=re.MULTILINE)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

files_to_clean = [
    'src/coreason_manifest/spec/ontology.py',
    'src/coreason_manifest/spec/__init__.py',
    'src/coreason_manifest/__init__.py',
]
for f in files_to_clean:
    clean_file(f)

# Also test files
for f in glob.glob('tests/**/*.py', recursive=True):
    clean_file(f)

