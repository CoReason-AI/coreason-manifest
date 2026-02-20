# src/coreason_manifest/utils/diff.py

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from coreason_manifest.spec.core.flow import GraphFlow, LinearFlow


class BaseOperation(BaseModel):
    """
    Base class for RFC 6902 JSON Patch operations.
    """

    model_config = ConfigDict(extra="ignore", strict=True, frozen=True)

    op: Literal["add", "remove", "replace", "move", "copy", "test"]
    path: str
    value: Any = None
    from_: Annotated[str | None, Field(alias="from")] = None


class ResourceMutation(BaseOperation):
    """Mutation affecting resources or content (e.g. prompts, profiles)."""

    mutation_type: Literal["resource"] = "resource"


class TopologyMutation(BaseOperation):
    """Mutation affecting graph structure (nodes, edges)."""

    mutation_type: Literal["topology"] = "topology"


class GovernanceMutation(BaseOperation):
    """Mutation affecting governance policies."""

    mutation_type: Literal["governance"] = "governance"


ChangeOperation = Annotated[
    ResourceMutation | TopologyMutation | GovernanceMutation, Field(discriminator="mutation_type")
]


def _create_mutation(
    op: Literal["add", "remove", "replace", "move", "copy", "test"],
    path: str,
    value: Any = None,
    domain: Literal["resource", "topology", "governance"] = "resource",
) -> ChangeOperation:
    mutation_cls = {
        "resource": ResourceMutation,
        "topology": TopologyMutation,
        "governance": GovernanceMutation,
    }[domain]

    # Cast to ensure return type matches Union
    return mutation_cls(op=op, path=path, value=value)  # type: ignore[no-any-return]


def _escape_json_pointer(key: str) -> str:
    """
    Escapes a dictionary key for use in a JSON Pointer (RFC 6901).
    ~ -> ~0
    / -> ~1
    """
    return key.replace("~", "~0").replace("/", "~1")


def _generate_diff(
    path: str,
    obj1: Any,
    obj2: Any,
    domain: Literal["resource", "topology", "governance"] = "resource",
    recurse_domain_override: Literal["resource", "topology", "governance"] | None = None,
) -> list[ChangeOperation]:
    """
    Recursively generates JSON Patch operations with contextual domain awareness.
    """
    changes: list[ChangeOperation] = []

    if obj1 == obj2:
        return changes

    if isinstance(obj1, dict) and isinstance(obj2, dict):
        all_keys = set(obj1.keys()) | set(obj2.keys())
        for key in sorted(all_keys):
            # SOTA Fix: RFC 6901 Escaping
            escaped_key = _escape_json_pointer(key)
            new_path = f"{path}/{escaped_key}"

            # SOTA Fix: Contextual Domain Switching
            # Determine domain for the current key and subsequent recursion.
            next_domain = domain
            next_override: Literal["resource", "topology", "governance"] | None = None

            if key in ("graph", "edges"):
                next_domain = "topology"
            elif key in ("nodes", "sequence"):
                next_domain = "topology"
                # Items inside nodes/sequence (e.g. Agents) are structural additions (topology)
                # but their internal content (profile, tools) is resource.
                next_override = "resource"
            elif key == "governance":
                next_domain = "governance"

            if key not in obj1:
                changes.append(_create_mutation(op="add", path=new_path, value=obj2[key], domain=next_domain))
            elif key not in obj2:
                changes.append(_create_mutation(op="remove", path=new_path, domain=next_domain))
            else:
                # If we have an override for children, use it for the recursive call.
                # Otherwise, propagate the current next_domain.
                # However, if 'recurse_domain_override' was passed to US (e.g. we are inside 'nodes'),
                # we must use it for OUR children (the agents).
                effective_domain = recurse_domain_override or next_domain
                changes.extend(_generate_diff(new_path, obj1[key], obj2[key], effective_domain, next_override))

    elif isinstance(obj1, list) and isinstance(obj2, list):
        # List diffing is complex for optimal patching.
        # Simple strategy: strict index comparison (replace/add/remove at end).
        len1 = len(obj1)
        len2 = len(obj2)

        # For lists (like 'sequence' or 'edges'), the list itself inherited a domain.
        # If 'recurse_domain_override' is set (e.g. for sequence items), use it for recursion.
        child_domain = recurse_domain_override or domain

        for i in range(max(len1, len2)):
            new_path = f"{path}/{i}"
            if i < len1 and i < len2:
                changes.extend(_generate_diff(new_path, obj1[i], obj2[i], child_domain, None))
            elif i >= len1:
                # Add item. This is a structural change to the list, so use 'domain'.
                changes.append(_create_mutation(op="add", path=new_path, value=obj2[i], domain=domain))
            else:
                pass

        # Correct handling of removals:
        if len1 > len2:
            changes.extend(
                _create_mutation(op="remove", path=f"{path}/{i}", domain=domain) for i in range(len1 - 1, len2 - 1, -1)
            )
    else:
        # Primitive replacement
        changes.append(_create_mutation(op="replace", path=path, value=obj2, domain=domain))

    return changes


def compare_flows(old: GraphFlow | LinearFlow, new: GraphFlow | LinearFlow) -> list[ChangeOperation]:
    """
    Compares two flows and returns a list of semantic JSON Patch operations.
    """
    # Convert to dicts (using mode='json' to ensure serializable)
    d1 = old.model_dump(mode="json", exclude_none=True)
    d2 = new.model_dump(mode="json", exclude_none=True)

    return _generate_diff("", d1, d2)
