from typing import Any


def extract_fallbacks(data: Any) -> list[str]:
    """Recursively scan dynamic execution parameters identifying implicit edge routing declarations.

    Preconditions:
        - Complex nested mappings configure target nodes leveraging automated error handling configurations.

    Postconditions:
        - Guarantees exhaustive isolation of dynamically assigned edge routes embedded deep within node configurations.

    Malicious States Prevented:
        - Disables clandestine route manipulation via unstructured fallback parameters resolving around oversight nodes.

    Args:
        data: The structural context parameter isolated for recursive routing evaluation.

    Returns:
        The complete sequential extraction of unmapped fallback node identifiers.
    """
    fallbacks = []
    if isinstance(data, dict):
        for k, v in data.items():
            if k == "fallback_node_id" and isinstance(v, str):
                fallbacks.append(v)
            else:
                fallbacks.extend(extract_fallbacks(v))
    elif isinstance(data, list):
        for item in data:
            fallbacks.extend(extract_fallbacks(item))
    return fallbacks
