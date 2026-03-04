import json
from typing import Any

from pydantic import BaseModel, ConfigDict


class CoreasonBaseModel(BaseModel):
    """
    Base class for all domain models in the Coreason Manifest.

    Enforces:
    1. Immutability (frozen=True) - Essential for distributed state consistency.
    2. Strict validation (strict=True) - No silent coercion.
    3. Forbidden extra fields (extra='forbid') - Schema strictness.
    4. Deterministic serialization - Keys are sorted for hash consistency.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_assignment=True,
        strict=True,
    )

    def __hash__(self) -> int:
        return hash(self.model_dump_canonical())

    def model_dump_canonical(self) -> bytes:
        """Return a strictly sorted, canonical JSON serialization for cryptographic hashing."""
        raw_dict = self.model_dump(mode="json", exclude_none=True, by_alias=True)

        def _sort_collections(obj: Any) -> Any:
            """
            Recursively sorts dictionaries for canonical serialization while explicitly preserving
            RFC 8785 array ordering.
            """
            if isinstance(obj, dict):
                return {k: _sort_collections(v) for k, v in sorted(obj.items())}
            if isinstance(obj, list):
                # Arrays in JSON are strictly ordered (RFC 8785). We must not sort them.
                return [_sort_collections(v) for v in obj]
            return obj

        canonical_dict = _sort_collections(raw_dict)

        return json.dumps(
            canonical_dict,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
