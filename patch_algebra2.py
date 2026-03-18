import re

with open("src/coreason_manifest/utils/algebra.py", "r") as f:
    content = f.read()

# I accidentally added ManifestViolationReceipt into the dictionary when replacing
content = content.replace('"system2_remediation": System2RemediationIntent,\n    ManifestViolationReceipt,\n}', '"system2_remediation": System2RemediationIntent,\n}')
content = content.replace("System2RemediationIntent", "System2RemediationIntent, ManifestViolationReceipt", 1)

with open("src/coreason_manifest/utils/algebra.py", "w") as f:
    f.write(content)
