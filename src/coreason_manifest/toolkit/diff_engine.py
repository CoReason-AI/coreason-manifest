import copy

from coreason_manifest.core.state.persistence import JSONPatchOperation, PatchOp


def _resolve_parent_and_key(doc: dict | list, pointer: str) -> tuple[dict | list, str | int]:
    if pointer == "" or pointer == "/":
        raise ValueError("Cannot resolve parent of root")
    parts = pointer.split("/")[1:]
    current = doc
    for part in parts[:-1]:
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            current = current[part]
        elif isinstance(current, list):
            current = current[int(part)]
    last_part = parts[-1].replace("~1", "/").replace("~0", "~")
    if isinstance(current, list):
        if last_part == "-":
            return current, len(current)
        return current, int(last_part)
    return current, last_part

def generate_inverse_patches(original_state: dict, patches: list[JSONPatchOperation]) -> list[JSONPatchOperation]:
    """
    Calculates the exact inverse of applied patches to support reverting state changes.
    """
    state = copy.deepcopy(original_state)
    inverses: list[JSONPatchOperation] = []

    for patch in patches:
        op = patch.op
        path = patch.path

        if op == PatchOp.TEST:
            continue

        parent, key = _resolve_parent_and_key(state, path)

        if op == PatchOp.ADD:
            if isinstance(parent, dict):
                if key in parent:
                    # Replacing existing key in dict
                    old_value = copy.deepcopy(parent[key])
                    inverses.append(JSONPatchOperation(op=PatchOp.REPLACE, path=path, value=old_value))
                    parent[key] = copy.deepcopy(patch.value)
                else:
                    # Adding new key to dict
                    inverses.append(JSONPatchOperation(op=PatchOp.REMOVE, path=path))
                    parent[key] = copy.deepcopy(patch.value)
            elif isinstance(parent, list):
                # Inserting into list
                # Inverse is remove at the same index
                idx = key
                if idx == len(parent):
                    # It was appended, so path might be /.../-
                    # In the inverse, we should remove the exact index it became
                    actual_path = f"{path.rsplit('/', 1)[0]}/{idx}" if path.endswith("/-") else path
                    inverses.append(JSONPatchOperation(op=PatchOp.REMOVE, path=actual_path))
                else:
                    inverses.append(JSONPatchOperation(op=PatchOp.REMOVE, path=path))
                parent.insert(idx, copy.deepcopy(patch.value))

        elif op == PatchOp.REMOVE:
            old_value = copy.deepcopy(parent[key])
            if isinstance(parent, dict):
                del parent[key]
            else:
                parent.pop(key)
            inverses.append(JSONPatchOperation(op=PatchOp.ADD, path=path, value=old_value))

        elif op == PatchOp.REPLACE:
            old_value = copy.deepcopy(parent[key])
            parent[key] = copy.deepcopy(patch.value)
            inverses.append(JSONPatchOperation(op=PatchOp.REPLACE, path=path, value=old_value))

        elif op == PatchOp.MOVE:
            from_path = patch.from_
            if from_path is None:
                raise ValueError("MOVE operation requires a 'from' path")

            from_parent, from_key = _resolve_parent_and_key(state, from_path)
            # Remove from from_path
            old_value = copy.deepcopy(from_parent[from_key])
            if isinstance(from_parent, dict):
                del from_parent[from_key]
            else:
                from_parent.pop(from_key)

            # Inverse: move from path to from_path
            inverses.append(JSONPatchOperation(op=PatchOp.MOVE, path=from_path, from_=path))

            # Add to path
            if isinstance(parent, dict):
                parent[key] = old_value
            elif isinstance(parent, list):
                if key == len(parent):
                    parent.append(old_value)
                else:
                    parent.insert(key, old_value)

        elif op == PatchOp.COPY:
            from_path = patch.from_
            if from_path is None:
                raise ValueError("COPY operation requires a 'from' path")

            from_parent, from_key = _resolve_parent_and_key(state, from_path)
            copied_value = copy.deepcopy(from_parent[from_key])

            # This is like an ADD. The inverse is a REMOVE at the target path.
            if isinstance(parent, dict) and key in parent:
                # Replaced existing value
                old_val = copy.deepcopy(parent[key])
                inverses.append(JSONPatchOperation(op=PatchOp.REPLACE, path=path, value=old_val))
                parent[key] = copied_value
            else:
                idx = key
                if isinstance(parent, list) and idx == len(parent):
                    actual_path = f"{path.rsplit('/', 1)[0]}/{idx}" if path.endswith("/-") else path
                    inverses.append(JSONPatchOperation(op=PatchOp.REMOVE, path=actual_path))
                    parent.insert(idx, copied_value)
                else:
                    inverses.append(JSONPatchOperation(op=PatchOp.REMOVE, path=path))
                    if isinstance(parent, dict):
                        parent[key] = copied_value
                    else:
                        parent.insert(idx, copied_value)

    inverses.reverse()
    return inverses

def apply_rewind(current_state: dict, reverse_patches: list[JSONPatchOperation]) -> dict:
    """
    Applies inverse patches cleanly to a state dictionary, simulating rollback.
    """
    state = copy.deepcopy(current_state)
    for patch in reverse_patches:
        op = patch.op
        path = patch.path

        if op == PatchOp.TEST:
            continue

        parent, key = _resolve_parent_and_key(state, path)

        if op == PatchOp.ADD:
            if isinstance(parent, dict):
                parent[key] = copy.deepcopy(patch.value)
            elif isinstance(parent, list):
                if key == len(parent):
                    parent.append(copy.deepcopy(patch.value))
                else:
                    parent.insert(key, copy.deepcopy(patch.value))

        elif op == PatchOp.REMOVE:
            if isinstance(parent, dict):
                del parent[key]
            elif isinstance(parent, list):
                parent.pop(key)

        elif op == PatchOp.REPLACE:
            parent[key] = copy.deepcopy(patch.value)

        elif op == PatchOp.MOVE:
            from_path = patch.from_
            if from_path is None:
                raise ValueError("MOVE operation requires a 'from' path")

            from_parent, from_key = _resolve_parent_and_key(state, from_path)
            old_value = copy.deepcopy(from_parent[from_key])

            if isinstance(from_parent, dict):
                del from_parent[from_key]
            else:
                from_parent.pop(from_key)

            if isinstance(parent, dict):
                parent[key] = old_value
            elif isinstance(parent, list):
                if key == len(parent):
                    parent.append(old_value)
                else:
                    parent.insert(key, old_value)

        elif op == PatchOp.COPY:
            from_path = patch.from_
            if from_path is None:
                raise ValueError("COPY operation requires a 'from' path")

            from_parent, from_key = _resolve_parent_and_key(state, from_path)
            copied_value = copy.deepcopy(from_parent[from_key])

            if isinstance(parent, dict):
                parent[key] = copied_value
            elif isinstance(parent, list):
                if key == len(parent):
                    parent.append(copied_value)
                else:
                    parent.insert(key, copied_value)

    return state
