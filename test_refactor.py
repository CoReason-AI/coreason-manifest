from typing import Any


def _resolve_path(pointer: str) -> list[str]:
    if pointer in ("", "/"):
        raise ValueError("Cannot resolve parent of root")
    return [p.replace("~1", "/").replace("~0", "~") for p in pointer.split("/")[1:]]


def _get_value(doc: Any, pointer: str) -> Any:
    if pointer in ("", "/"):
        return doc
    current = doc
    for part in _resolve_path(pointer):
        if isinstance(current, dict):
            current = current[part]
        elif isinstance(current, list):
            current = current[int(part)]
        elif hasattr(current, "model_copy"):
            current = getattr(current, part)
    return current


def _has_key(doc: Any, pointer: str) -> bool:
    if pointer in ("", "/"):
        return True
    parts = _resolve_path(pointer)
    parent = _get_value(doc, "/" + "/".join(parts[:-1]))
    last = parts[-1]
    if isinstance(parent, dict):
        return last in parent
    if isinstance(parent, list):
        return int(last) < len(parent) and last != "-"
    if hasattr(parent, "model_copy"):
        return hasattr(parent, last)
    return False


def _cow_update(current: Any, parts: list[str], op: str, value: Any = None) -> Any:
    if not parts:
        if op in ("add", "replace"):
            return value
        return current

    part = parts[0]
    is_last = len(parts) == 1

    if isinstance(current, dict):
        new_current: dict[str, Any] = current.copy()
        key: str | int = part
    elif isinstance(current, list):
        new_current = list(current)
        if part == "-":
            key = len(new_current)
        else:
            key = int(part)
    elif hasattr(current, "model_copy"):
        key = part
    else:
        raise ValueError(f"Cannot traverse type {type(current)}")

    if is_last:
        if op in ("add", "replace"):
            if isinstance(current, dict):
                new_current[key] = value  # type: ignore[index]
            elif isinstance(current, list):
                if op == "add":
                    new_current.insert(key, value)  # type: ignore[arg-type]
                else:
                    new_current[key] = value  # type: ignore[index]
            else:
                return current.model_copy(update={key: value})
        elif op == "remove":
            if isinstance(current, dict):
                del new_current[key]  # type: ignore[arg-type]
            elif isinstance(current, list):
                new_current.pop(key)  # type: ignore[arg-type]
    else:
        if isinstance(current, dict) or isinstance(current, list):
            new_current[key] = _cow_update(new_current[key], parts[1:], op, value)  # type: ignore[index]
        else:
            child_val = getattr(current, key)
            new_child = _cow_update(child_val, parts[1:], op, value)
            return current.model_copy(update={str(key): new_child})

    return new_current
