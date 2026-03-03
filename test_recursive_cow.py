from typing import Any

from pydantic import BaseModel, ConfigDict


class Inner(BaseModel):
    model_config = ConfigDict(frozen=True)
    val: int


class Outer(BaseModel):
    model_config = ConfigDict(frozen=True)
    inner: Inner


def _cow_update(current: Any, parts: list[str], op: str, value: Any = None, from_value: Any = None) -> Any:
    if not parts:
        if op in ("add", "replace", "copy", "move"):
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
        raise ValueError(f"Cannot traverse type {type(current)}")

    if is_last:
        if op in ("add", "replace", "copy", "move"):
            if isinstance(current, dict):
                new_current[key] = value
            elif isinstance(current, list):
                if op == "add" or op == "copy" or op == "move":
                    if key == len(new_current):
                        new_current.append(value)
                    else:
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
                # Pydantic removal usually means setting to None, but RFC6902 on objects means removing key.
                pass
    else:
        if isinstance(current, dict) or isinstance(current, list):
            new_current[key] = _cow_update(current[key], parts[1:], op, value, from_value)
        else:
            child_val = getattr(current, key)
            new_child = _cow_update(child_val, parts[1:], op, value, from_value)
            return current.model_copy(update={str(key): new_child})

    return new_current


state = {"outer": Outer(inner=Inner(val=1))}
parts = ["outer", "inner", "val"]
new_state = _cow_update(state, parts, "replace", 2)
print("Old:", state)
print("New:", new_state)
