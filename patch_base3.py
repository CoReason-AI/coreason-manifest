with open("src/coreason_manifest/core/base.py", "r") as f:
    content = f.read()

target = """    def __hash__(self) -> int:
        return getattr(self, "_cached_hash")"""

replacement = """    def __hash__(self) -> int:
        try:
            return object.__getattribute__(self, "_cached_hash")
        except AttributeError:
            h = hash(self.model_dump_canonical())
            object.__setattr__(self, "_cached_hash", h)
            return h"""

content = content.replace(target, replacement)

with open("src/coreason_manifest/core/base.py", "w") as f:
    f.write(content)
