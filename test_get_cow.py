from typing import Any

def _get_cow_parent(
    doc: dict[str, Any] | list[Any], pointer: str
) -> tuple[dict[str, Any] | list[Any], dict[str, Any] | list[Any], str | int]:
    if pointer == "" or pointer == "/":
        raise ValueError("Cannot resolve parent of root")

    parts = pointer.split("/")[1:]

    if isinstance(doc, dict):
        new_doc: dict[str, Any] | list[Any] = doc.copy()
    else:
        new_doc = list(doc)

    current = new_doc

    for part in parts[:-1]:
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            child = current[part]
            if isinstance(child, dict):
                current[part] = child.copy()
            else:
                current[part] = list(child)
            current = current[part]
        elif isinstance(current, list):
            try:
                idx = int(part)
                child = current[idx]
                if isinstance(child, dict):
                    current[idx] = child.copy()
                else:
                    current[idx] = list(child)
                current = current[idx]
            except ValueError as e:
                raise ValueError(f"Invalid array index in pointer: '{part}'") from e

    last_part = parts[-1].replace("~1", "/").replace("~0", "~")
    if isinstance(current, list):
        if last_part == "-":
            return new_doc, current, len(current)
        try:
            return new_doc, current, int(last_part)
        except ValueError as e:
            raise ValueError(f"Invalid array index in pointer: '{last_part}'") from e

    return new_doc, current, last_part

d = {"a": {"b": [1, 2, 3]}}
new_d, parent, key = _get_cow_parent(d, "/a/b/-")
print("Original:", d)
print("New root:", new_d)
print("Parent:", parent)
print("Key:", key)
parent.append(4)
print("Original after mutation:", d)
print("New after mutation:", new_d)
