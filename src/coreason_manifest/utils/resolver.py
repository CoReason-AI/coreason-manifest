# src/coreason_manifest/utils/resolver.py

from typing import Any, Callable

class CircularReferenceError(Exception):
    """Raised when a circular reference is detected during resolution."""

    def __init__(self, path: list[str]):
        self.path = path
        super().__init__(f"Circular reference detected: {' -> '.join(path)}")


class ResolutionContext:
    """
    Handles resolution of JSON references ($ref) with strict cycle detection
    and caching.
    """

    def __init__(self, loader: Callable[[str], dict[str, Any]]):
        """
        Args:
            loader: A callable that takes a URI/path and returns the loaded dictionary.
        """
        self.loader = loader
        self._cache: dict[str, Any] = {}
        self._active_refs: list[str] = []

    def _resolve_pointer(self, doc: Any, pointer: str) -> Any:
        """
        Resolves a JSON pointer within a document.
        Supported format: #/path/to/node
        """
        if not pointer.startswith("#/"):
            if pointer == "#" or pointer == "":
                return doc
            raise ValueError(f"Invalid local reference: {pointer}")

        path_parts = pointer[2:].split("/")
        current = doc

        for part in path_parts:
            # Handle escaping
            part = part.replace("~1", "/").replace("~0", "~")

            # Empty part from leading slash or double slash
            if part == "":
                continue

            if isinstance(current, dict):
                if part not in current:
                    raise ValueError(f"Reference not found: {pointer}")
                current = current[part]
            elif isinstance(current, list):
                try:
                    idx = int(part)
                    if idx < 0 or idx >= len(current):
                        raise ValueError(f"Index out of bounds: {pointer}")
                    current = current[idx]
                except ValueError as e:
                    raise ValueError(f"Invalid list index in pointer: {pointer}") from e
            else:
                raise ValueError(f"Cannot traverse scalar value at {part} in {pointer}")

        return current

    def resolve(self, data: Any, base_uri: str = "root", root_doc: Any = None) -> Any:
        """
        Recursively resolves all $refs in the data.
        Handles remote URIs and local fragments.
        Args:
            data: The current node to resolve.
            base_uri: The URI of the document containing 'data'.
            root_doc: The root of the document containing 'data' (for local ref resolution).
                      If None, 'data' is assumed to be the root.
        """
        # Initialize root_doc if not provided (start of recursion for a document)
        if root_doc is None:
            root_doc = data

        if isinstance(data, dict):
            if "$ref" in data:
                ref = data["$ref"]

                # Split URI and fragment
                if "#" in ref:
                    uri, fragment = ref.split("#", 1)
                    fragment = "#" + fragment
                else:
                    uri, fragment = ref, ""

                # Determine full key for cycle detection
                if uri:
                    # Remote Ref
                    # In real implementation, resolve 'uri' against 'base_uri'.
                    full_ref_key = uri + (fragment if fragment else "")

                    # Cycle Detection (Remote + Fragment)
                    if full_ref_key in self._active_refs:
                         raise CircularReferenceError(self._active_refs + [full_ref_key])

                    # Check Cache (for document level)
                    # We cache resolved DOCUMENTS, not fragments?
                    # Or we cache fragments?
                    # Cache logic: cache resolved full documents by URI.
                    if uri in self._cache:
                        doc = self._cache[uri]
                    else:
                        if uri in self._active_refs: # Check if document itself is being resolved
                             raise CircularReferenceError(self._active_refs + [uri])

                        self._active_refs.append(uri)
                        try:
                            # Load external document
                            raw_doc = self.loader(uri)
                            # Recursively resolve the loaded document
                            doc = self.resolve(raw_doc, base_uri=uri, root_doc=raw_doc)
                        finally:
                            self._active_refs.pop()

                        self._cache[uri] = doc

                    # Apply fragment
                    if fragment:
                        # We need to resolve the fragment within the resolved document.
                        # Since 'doc' is already resolved, we just traverse.
                        # But wait, 'doc' might contain already resolved objects.
                        return self._resolve_pointer(doc, fragment)

                    return doc

                else:
                    # Local Ref (uri is empty)
                    full_ref_key = f"{base_uri}{fragment}"

                    if full_ref_key in self._cache:
                        return self._cache[full_ref_key]

                    if full_ref_key in self._active_refs:
                        raise CircularReferenceError(self._active_refs + [full_ref_key])

                    self._active_refs.append(full_ref_key)
                    try:
                        # Resolve pointer in current root_doc
                        target = self._resolve_pointer(root_doc, fragment)

                        # Recurse to resolve the target
                        result = self.resolve(target, base_uri=base_uri, root_doc=root_doc)
                        self._cache[full_ref_key] = result
                        return result
                    finally:
                         self._active_refs.pop()

            # Recurse for children
            return {k: self.resolve(v, base_uri, root_doc) for k, v in data.items()}

        if isinstance(data, list):
            return [self.resolve(v, base_uri, root_doc) for v in data]

        return data
