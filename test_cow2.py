from typing import Any
from pydantic import BaseModel

class MyModel(BaseModel, frozen=True):
    name: str
    items: list[int]

def _resolve_parts(pointer: str) -> list[str]:
    if pointer == "" or pointer == "/":
        return []
    return [p.replace("~1", "/").replace("~0", "~") for p in pointer.split("/")[1:]]

def _get_value(current: Any, parts: list[str]) -> Any:
    for part in parts:
        if isinstance(current, dict):
            current = current[part]
        elif isinstance(current, list):
            current = current[int(part)]
        elif hasattr(current, "model_copy"):
            current = getattr(current, part)
    return current

def _cow_update(current: Any, parts: list[str], op: str, value: Any = None) -> Any:
    if not parts:
        if op in ("add", "replace"):
            return value
        return current

    part = parts[0]
    is_last = len(parts) == 1

    if isinstance(current, dict):
        new_current = current.copy()
        key = part
    elif isinstance(current, list):
        new_current = list(current)
        key = len(new_current) if part == "-" else int(part)
    elif hasattr(current, "model_copy"):
        key = part
    else:
        raise ValueError("Unsupported type for CoW")

    if is_last:
        if op in ("add", "replace"):
            if isinstance(current, dict):
                new_current[key] = value
            elif isinstance(current, list):
                if op == "add":
                    new_current.insert(key, value)
                else:
                    new_current[key] = value
            else:
                return current.model_copy(update={key: value})
        elif op == "remove":
            if isinstance(current, dict):
                del new_current[key]
            elif isinstance(current, list):
                new_current.pop(key)
            else:
                # Assuming model fields can't be "deleted", we set them to None or ignore.
                # Actually pydantic has fields.
                pass
    else:
        if isinstance(current, dict):
            new_current[key] = _cow_update(new_current[key], parts[1:], op, value)
        elif isinstance(current, list):
            new_current[key] = _cow_update(new_current[key], parts[1:], op, value)
        else:
            child_val = getattr(current, key)
            new_child = _cow_update(child_val, parts[1:], op, value)
            return current.model_copy(update={key: new_child})

    return new_current

state = {
    "a": MyModel(name="test", items=[1, 2, 3])
}

new_state = _cow_update(state, _resolve_parts("/a/items/1"), "replace", 99)
print("Original:", state)
print("New:", new_state)

new_state2 = _cow_update(state, _resolve_parts("/a/name"), "replace", "updated")
print("New2:", new_state2)
