import copy
from datetime import UTC, datetime
from typing import Any

from coreason_manifest.core.common.exceptions import ManifestError
from coreason_manifest.core.state.persistence import JSONPatchOperation, PatchOp
from coreason_manifest.core.telemetry.stream import StreamStateDeltaEnvelope


def _resolve_parent_and_key(
    doc: dict[str, Any] | list[Any], pointer: str
) -> tuple[dict[str, Any] | list[Any], str | int]:
    if pointer == "" or pointer == "/":
        raise ValueError("Cannot resolve parent of root")
    parts = pointer.split("/")[1:]
    current = doc
    for part in parts[:-1]:
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            current = current[part]
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except ValueError as e:
                raise ManifestError.critical_halt(
                    "VAL-SCHEMA-INVALID", f"Invalid array index in pointer: '{part}'"
                ) from e
    last_part = parts[-1].replace("~1", "/").replace("~0", "~")
    if isinstance(current, list):
        if last_part == "-":
            return current, len(current)
        try:
            return current, int(last_part)
        except ValueError as e:
            raise ManifestError.critical_halt(
                "VAL-SCHEMA-INVALID", f"Invalid array index in pointer: '{last_part}'"
            ) from e
    return current, last_part


def generate_inverse_patches(
    original_state: dict[str, Any], patches: list[JSONPatchOperation]
) -> list[JSONPatchOperation]:
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
                if str(key) in parent:
                    # Replacing existing key in dict
                    old_value = copy.deepcopy(parent[str(key)])
                    inverses.append(JSONPatchOperation(op=PatchOp.REPLACE, path=path, value=old_value, from_=None))
                    parent[str(key)] = copy.deepcopy(patch.value)
                else:
                    # Adding new key to dict
                    inverses.append(JSONPatchOperation(op=PatchOp.REMOVE, path=path, value=None, from_=None))
                    parent[str(key)] = copy.deepcopy(patch.value)
            elif isinstance(parent, list):
                # Inserting into list
                # Inverse is remove at the same index
                idx = int(key)
                if idx == len(parent):
                    # It was appended, so path might be /.../-
                    # In the inverse, we should remove the exact index it became
                    actual_path = f"{path.rsplit('/', 1)[0]}/{idx}" if path.endswith("/-") else path
                    inverses.append(JSONPatchOperation(op=PatchOp.REMOVE, path=actual_path, value=None, from_=None))
                else:
                    inverses.append(JSONPatchOperation(op=PatchOp.REMOVE, path=path, value=None, from_=None))
                parent.insert(idx, copy.deepcopy(patch.value))

        elif op == PatchOp.REMOVE:
            old_value = copy.deepcopy(parent[key])  # type: ignore[index]
            if isinstance(parent, dict):
                del parent[str(key)]
            else:
                parent.pop(int(key))
            inverses.append(JSONPatchOperation(op=PatchOp.ADD, path=path, value=old_value, from_=None))

        elif op == PatchOp.REPLACE:
            old_value = copy.deepcopy(parent[key])  # type: ignore[index]
            if isinstance(parent, dict):
                parent[str(key)] = copy.deepcopy(patch.value)
            else:
                parent[int(key)] = copy.deepcopy(patch.value)
            inverses.append(JSONPatchOperation(op=PatchOp.REPLACE, path=path, value=old_value, from_=None))

        elif op == PatchOp.MOVE:
            from_path = patch.from_
            if from_path is None:
                raise ValueError("MOVE operation requires a 'from' path")

            from_parent, from_key = _resolve_parent_and_key(state, from_path)
            # Remove from from_path
            old_value = copy.deepcopy(from_parent[from_key])  # type: ignore[index]
            if isinstance(from_parent, dict):
                del from_parent[str(from_key)]
            else:
                from_parent.pop(int(from_key))

            # Inverse: move from path to from_path
            inverses.append(JSONPatchOperation(op=PatchOp.MOVE, path=from_path, from_=path, value=None))

            # Add to path
            if isinstance(parent, dict):
                parent[str(key)] = old_value
            elif isinstance(parent, list):
                if int(key) == len(parent):
                    parent.append(old_value)
                else:
                    parent.insert(int(key), old_value)

        elif op == PatchOp.COPY:
            from_path = patch.from_
            if from_path is None:
                raise ValueError("COPY operation requires a 'from' path")

            from_parent, from_key = _resolve_parent_and_key(state, from_path)
            copied_value = copy.deepcopy(from_parent[from_key])  # type: ignore[index]

            # This is like an ADD. The inverse is a REMOVE at the target path.
            if isinstance(parent, dict) and key in parent:
                # Replaced existing value
                old_val = copy.deepcopy(parent[str(key)])
                inverses.append(JSONPatchOperation(op=PatchOp.REPLACE, path=path, value=old_val, from_=None))
                parent[str(key)] = copied_value
            else:
                idx = int(key)
                if isinstance(parent, list) and idx == len(parent):
                    actual_path = f"{path.rsplit('/', 1)[0]}/{idx}" if path.endswith("/-") else path
                    inverses.append(JSONPatchOperation(op=PatchOp.REMOVE, path=actual_path, value=None, from_=None))
                    parent.insert(idx, copied_value)
                else:
                    inverses.append(JSONPatchOperation(op=PatchOp.REMOVE, path=path, value=None, from_=None))
                    if isinstance(parent, dict):
                        parent[str(key)] = copied_value
                    else:
                        parent.insert(idx, copied_value)

    inverses.reverse()
    return inverses


def generate_revert_envelope(
    original_state: dict[str, Any], patches: list[JSONPatchOperation], trace_id: str | None = None
) -> StreamStateDeltaEnvelope:
    """
    Generates a reverting state delta envelope to broadcast to edge observers.
    """
    inverse_patches = generate_inverse_patches(original_state, patches)
    return StreamStateDeltaEnvelope(
        op="state_delta",
        p=inverse_patches,
        trace_id=trace_id,
        timestamp=datetime.now(UTC).timestamp(),
    )


def apply_rewind(current_state: dict[str, Any], reverse_patches: list[JSONPatchOperation]) -> dict[str, Any]:
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
                parent[str(key)] = copy.deepcopy(patch.value)
            elif isinstance(parent, list):
                if int(key) == len(parent):
                    parent.append(copy.deepcopy(patch.value))
                else:
                    parent.insert(int(key), copy.deepcopy(patch.value))

        elif op == PatchOp.REMOVE:
            if isinstance(parent, dict):
                del parent[str(key)]
            elif isinstance(parent, list):
                parent.pop(int(key))

        elif op == PatchOp.REPLACE:
            if isinstance(parent, dict):
                parent[str(key)] = copy.deepcopy(patch.value)
            else:
                parent[int(key)] = copy.deepcopy(patch.value)

        elif op == PatchOp.MOVE:
            from_path = patch.from_
            if from_path is None:
                raise ValueError("MOVE operation requires a 'from' path")

            from_parent, from_key = _resolve_parent_and_key(state, from_path)
            old_value = copy.deepcopy(from_parent[from_key])  # type: ignore[index]

            if isinstance(from_parent, dict):
                del from_parent[str(from_key)]
            else:
                from_parent.pop(int(from_key))

            if isinstance(parent, dict):
                parent[str(key)] = old_value
            elif isinstance(parent, list):
                if int(key) == len(parent):
                    parent.append(old_value)
                else:
                    parent.insert(int(key), old_value)

        elif op == PatchOp.COPY:
            from_path = patch.from_
            if from_path is None:
                raise ValueError("COPY operation requires a 'from' path")

            from_parent, from_key = _resolve_parent_and_key(state, from_path)
            copied_value = copy.deepcopy(from_parent[from_key])  # type: ignore[index]

            if isinstance(parent, dict):
                parent[str(key)] = copied_value
            elif isinstance(parent, list):
                if int(key) == len(parent):
                    parent.append(copied_value)
                else:
                    parent.insert(int(key), copied_value)

    return state
