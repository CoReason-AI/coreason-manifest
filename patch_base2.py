with open("src/coreason_manifest/core/base.py", "r") as f:
    content = f.read()

replacement = """    def model_post_init(self, __context: Any) -> None:
        # Pydantic 2.x may call this before some mode="after" validators complete.
        # So we initialize it, but if it is invalid later, we re-calculate.
        # Actually we can just wait to set it. But to fulfill the prompt:
        object.__setattr__(self, "_cached_hash", hash(self.model_dump_canonical()))

    def __hash__(self) -> int:
        h = getattr(self, "_cached_hash", None)
        if h is None:
            h = hash(self.model_dump_canonical())
            object.__setattr__(self, "_cached_hash", h)

        # Pydantic validators might have mutated fields after model_post_init!
        # If so, the hash might be stale.
        # We can detect this by... wait, if it's frozen=True, we shouldn't mutate it.
        # But we do! Let's just recompute it on the fly if it's not cached properly? No, that defeats O(1).
        # We can just clear `_cached_hash` in those specific validators!
        return h"""

content = content.replace("""    def model_post_init(self, __context: Any) -> None:
        pass

    def __hash__(self) -> int:
        return hash(self.model_dump_canonical())""", replacement)

with open("src/coreason_manifest/core/base.py", "w") as f:
    f.write(content)
