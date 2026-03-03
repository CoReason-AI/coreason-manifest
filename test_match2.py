from coreason_manifest.core.state.persistence import JSONPatchOperation, PatchOp

p = JSONPatchOperation(op=PatchOp.ADD, path="/a", value=5)
match p.model_dump(exclude_unset=True):
    case {"op": "add", "path": path, "value": val}:
        print("ADD", path, val)
    case _:
        print("MISS")
