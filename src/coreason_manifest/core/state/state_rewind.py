from datetime import UTC, datetime
from typing import Any

from coreason_manifest.core.common.exceptions import ManifestError
from coreason_manifest.core.state.persistence import JSONPatchOperation, PatchOp
from coreason_manifest.core.telemetry.stream import StreamStateDeltaEnvelope
from coreason_manifest.utils.logger import logger


def _get_cow_parent(
    doc: dict[str, Any] | list[Any], pointer: str
) -> tuple[dict[str, Any] | list[Any], dict[str, Any] | list[Any], str | int]:
    """
    Traverses the document using Copy-on-Write semantics.
    Creates shallow copies of nodes along the path to ensure immutability.
    Returns:
        (new_root, copied_parent_node, resolved_key)
    """
    logger.trace("resolving_cow_path", pointer=pointer, doc_type=type(doc).__name__)
    if pointer == "" or pointer == "/":
        raise ValueError("Cannot resolve parent of root")

    parts = pointer.split("/")[1:]
    new_doc: dict[str, Any] | list[Any] = doc.copy() if isinstance(doc, dict) else list(doc)
    current = new_doc

    for part in parts[:-1]:
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            child = current[part]
            current[part] = child.copy() if isinstance(child, dict) else list(child)
            current = current[part]
        elif isinstance(current, list):
            try:
                idx = int(part)
                child = current[idx]
                current[idx] = child.copy() if isinstance(child, dict) else list(child)
                current = current[idx]
            except ValueError as e:
                raise ManifestError.critical_halt(
                    "VAL-SCHEMA-INVALID", f"Invalid array index in pointer: '{part}'"
                ) from e

    last_part = parts[-1].replace("~1", "/").replace("~0", "~")
    if isinstance(current, list):
        if last_part == "-":
            return new_doc, current, len(current)
        try:
            return new_doc, current, int(last_part)
        except ValueError as e:
            raise ManifestError.critical_halt(
                "VAL-SCHEMA-INVALID", f"Invalid array index in pointer: '{last_part}'"
            ) from e

    return new_doc, current, last_part


def generate_inverse_patches(
    original_state: dict[str, Any], patches: list[JSONPatchOperation]
) -> list[JSONPatchOperation]:
    """
    Calculates the exact inverse of applied patches to support reverting state changes.
    """
    logger.trace(
        "generating_inverse_patches",
        original_state_keys=list(original_state.keys()) if isinstance(original_state, dict) else len(original_state),
        num_patches=len(patches),
    )
    state: dict[str, Any] | list[Any] = original_state
    inverses: list[JSONPatchOperation] = []

    for patch in patches:
        match patch.model_dump(exclude_unset=True, by_alias=True):
            case {"op": "test"}:
                continue
            case {"op": "add", "path": path, "value": val}:
                state, parent, key = _get_cow_parent(state, path)
                if isinstance(parent, dict):
                    if str(key) in parent:
                        old_value = parent[str(key)]
                        inverses.append(JSONPatchOperation(op=PatchOp.REPLACE, path=path, value=old_value, from_=None))
                        parent[str(key)] = val
                    else:
                        inverses.append(JSONPatchOperation(op=PatchOp.REMOVE, path=path, value=None, from_=None))
                        parent[str(key)] = val
                elif isinstance(parent, list):
                    idx = int(key)
                    if idx == len(parent):
                        actual_path = f"{path.rsplit('/', 1)[0]}/{idx}" if path.endswith("/-") else path
                        inverses.append(JSONPatchOperation(op=PatchOp.REMOVE, path=actual_path, value=None, from_=None))
                    else:
                        inverses.append(JSONPatchOperation(op=PatchOp.REMOVE, path=path, value=None, from_=None))
                    parent.insert(idx, val)

            case {"op": "remove", "path": path}:
                state, parent, key = _get_cow_parent(state, path)
                if isinstance(parent, dict):
                    old_value = parent[str(key)]
                    del parent[str(key)]
                else:
                    old_value = parent[int(key)]
                    parent.pop(int(key))
                inverses.append(JSONPatchOperation(op=PatchOp.ADD, path=path, value=old_value, from_=None))

            case {"op": "replace", "path": path, "value": val}:
                state, parent, key = _get_cow_parent(state, path)
                if isinstance(parent, dict):
                    old_value = parent[str(key)]
                    parent[str(key)] = val
                else:
                    old_value = parent[int(key)]
                    parent[int(key)] = val
                inverses.append(JSONPatchOperation(op=PatchOp.REPLACE, path=path, value=old_value, from_=None))

            case {"op": "move", "path": path, "from": from_path}:
                # Note: `from_` is aliased to `from` in Pydantic serialization
                state, from_parent, from_key = _get_cow_parent(state, from_path)

                if isinstance(from_parent, dict):
                    old_value = from_parent[str(from_key)]
                    del from_parent[str(from_key)]
                else:
                    old_value = from_parent[int(from_key)]
                    from_parent.pop(int(from_key))

                state, parent, key = _get_cow_parent(state, path)
                inverses.append(JSONPatchOperation(op=PatchOp.MOVE, path=from_path, from_=path, value=None))

                if isinstance(parent, dict):
                    parent[str(key)] = old_value
                elif isinstance(parent, list):
                    if int(key) == len(parent):
                        parent.append(old_value)
                    else:
                        parent.insert(int(key), old_value)

            case {"op": "copy", "path": path, "from": from_path}:
                state, from_parent, from_key = _get_cow_parent(state, from_path)
                if isinstance(from_parent, dict):
                    copied_value = from_parent[str(from_key)]
                else:
                    copied_value = from_parent[int(from_key)]

                state, parent, key = _get_cow_parent(state, path)
                if isinstance(parent, dict) and str(key) in parent:
                    old_val = parent[str(key)]
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
            case _:
                raise ValueError("Malformed patch operation")

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
    logger.trace("applying_inverse_patch", num_reverse_patches=len(reverse_patches))
    state: dict[str, Any] | list[Any] = current_state
    for patch in reverse_patches:
        match patch.model_dump(exclude_unset=True, by_alias=True):
            case {"op": "test"}:
                continue
            case {"op": "add", "path": path, "value": val}:
                state, parent, key = _get_cow_parent(state, path)
                if isinstance(parent, dict):
                    parent[str(key)] = val
                elif isinstance(parent, list):
                    if int(key) == len(parent):
                        parent.append(val)
                    else:
                        parent.insert(int(key), val)

            case {"op": "remove", "path": path}:
                state, parent, key = _get_cow_parent(state, path)
                if isinstance(parent, dict):
                    del parent[str(key)]
                elif isinstance(parent, list):
                    parent.pop(int(key))

            case {"op": "replace", "path": path, "value": val}:
                state, parent, key = _get_cow_parent(state, path)
                if isinstance(parent, dict):
                    parent[str(key)] = val
                else:
                    parent[int(key)] = val

            case {"op": "move", "path": path, "from": from_path}:
                state, from_parent, from_key = _get_cow_parent(state, from_path)
                if isinstance(from_parent, dict):
                    old_value = from_parent[str(from_key)]
                    del from_parent[str(from_key)]
                else:
                    old_value = from_parent[int(from_key)]
                    from_parent.pop(int(from_key))

                state, parent, key = _get_cow_parent(state, path)
                if isinstance(parent, dict):
                    parent[str(key)] = old_value
                elif isinstance(parent, list):
                    if int(key) == len(parent):
                        parent.append(old_value)
                    else:
                        parent.insert(int(key), old_value)

            case {"op": "copy", "path": path, "from": from_path}:
                state, from_parent, from_key = _get_cow_parent(state, from_path)
                if isinstance(from_parent, dict):
                    copied_value = from_parent[str(from_key)]
                else:
                    copied_value = from_parent[int(from_key)]

                state, parent, key = _get_cow_parent(state, path)
                if isinstance(parent, dict):
                    parent[str(key)] = copied_value
                elif isinstance(parent, list):
                    if int(key) == len(parent):
                        parent.append(copied_value)
                    else:
                        parent.insert(int(key), copied_value)
            case _:
                raise ValueError("Malformed patch operation")

    if not isinstance(state, dict):
        raise ManifestError.critical_halt("STATE-TYPE-ERROR", "Rewind resulted in non-dict state root")
    return state
