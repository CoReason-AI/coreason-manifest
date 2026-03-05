with open("src/coreason_manifest/core/base.py", "r") as f:
    content = f.read()

import re
content = re.sub(r'    def __hash__\(self\) -> int:\n        return getattr\(self, "_cached_hash"\)', r'    def __hash__(self) -> int:\n        h: int = getattr(self, "_cached_hash")\n        return h', content)

with open("src/coreason_manifest/core/base.py", "w") as f:
    f.write(content)
