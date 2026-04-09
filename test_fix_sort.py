with open("src/coreason_manifest/spec/ontology.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

with open("src/coreason_manifest/spec/ontology.py", "w", encoding="utf-8") as f:
    for line in lines:
        if "object.__setattr__(self, \"concurrent_branch_cids\", sorted(self.concurrent_branch_cids))" in line:
            line = '        if getattr(self, "concurrent_branch_cids", None) is not None:\n            object.__setattr__(self, "concurrent_branch_cids", sorted(self.concurrent_branch_cids))\n'
        elif "object.__setattr__(self, \"protected_event_cids\", sorted(self.protected_event_cids))" in line:
            line = '        if getattr(self, "protected_event_cids", None) is not None:\n            object.__setattr__(self, "protected_event_cids", sorted(self.protected_event_cids))\n'
        f.write(line)
