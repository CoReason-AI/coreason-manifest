with open("src/coreason_manifest/core/base.py", "r") as f:
    content = f.read()

content = content.replace('            return object.__getattribute__(self, "_cached_hash")', '            h: int = object.__getattribute__(self, "_cached_hash")\n            return h')

with open("src/coreason_manifest/core/base.py", "w") as f:
    f.write(content)
