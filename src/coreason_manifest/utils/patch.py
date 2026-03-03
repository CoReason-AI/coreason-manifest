def generate_safe_array_removal_patch(path: str, indices: list[int]) -> list[dict[str, str]]:
    """Generates JSON Patch ops for safely removing array elements by index without corruption.

    Inherently reverse-sorts indices to ensure sequential removals do not invalidate
    the targeted arrays remaining layout index spaces.
    """
    sorted_indices = sorted(set(indices), reverse=True)
    return [{"op": "remove", "path": f"{path}/{idx}"} for idx in sorted_indices]
