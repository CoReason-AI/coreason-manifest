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


def _classify_path(path: str) -> Literal["resource", "topology", "governance"]:
    """
    Classifies a JSON path into a mutation domain.
    """
    if path.startswith(("/graph", "/sequence", "/edges")):
        # Determine if it's structural or content.

        # Heuristic:
        if "/edges" in path:
            return "topology"
        if "/nodes/" in path:
            # Check if it's the node itself or a property
            parts = path.split("/")
            # /graph/nodes/NODE_ID -> Topology (add/remove)
            # Note: IDs might contain escaped chars (~1), so splitting by / works if we assume standard structure.
            # But "graph" "nodes" "id" is 4 parts (empty string first).
            if len(parts) == 4:  # ['', 'graph', 'nodes', 'id']
                return "topology"
            # /graph/nodes/id/PROPERTY -> Resource
            return "resource"
        if "/sequence" in path:
            # Linear flow
            # /sequence/INDEX
            parts = path.split("/")
            if len(parts) == 3:  # ['', 'sequence', '0']
                return "topology"
            return "resource"

        return "topology"

    if path.startswith("/governance"):
        return "governance"

    return "resource"


def _create_mutation(
    op: Literal["add", "remove", "replace", "move", "copy", "test"], path: str, value: Any = None
) -> ChangeOperation:
    category = _classify_path(path)
    # Explicit typing to satisfy Mypy
    mutation_cls = {
        "resource": ResourceMutation,
        "topology": TopologyMutation,
        "governance": GovernanceMutation,
    }[category]

    # Cast to ensure return type matches Union
    return mutation_cls(op=op, path=path, value=value)  # type: ignore[no-any-return]


def _escape_json_pointer(key: str) -> str:
    """
    Escapes a dictionary key for use in a JSON Pointer (RFC 6901).
    ~ -> ~0
    / -> ~1
    """
    return key.replace("~", "~0").replace("/", "~1")


def _generate_diff(path: str, obj1: Any, obj2: Any) -> list[ChangeOperation]:
    """
    Recursively generates JSON Patch operations.
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

            if key not in obj1:
                changes.append(_create_mutation(op="add", path=new_path, value=obj2[key]))
            elif key not in obj2:
                changes.append(_create_mutation(op="remove", path=new_path))
            else:
                changes.extend(_generate_diff(new_path, obj1[key], obj2[key]))
    elif isinstance(obj1, list) and isinstance(obj2, list):
        # List diffing is complex for optimal patching.
        # Simple strategy: strict index comparison (replace/add/remove at end).
        # We explicitly document this behavior as requested.
        len1 = len(obj1)
        len2 = len(obj2)

        for i in range(max(len1, len2)):
            new_path = f"{path}/{i}"
            if i < len1 and i < len2:
                changes.extend(_generate_diff(new_path, obj1[i], obj2[i]))
            elif i >= len1:
                # Add
                changes.append(_create_mutation(op="add", path=new_path, value=obj2[i]))
            else:
                pass

        # Correct handling of removals:
        if len1 > len2:
            changes.extend(_create_mutation(op="remove", path=f"{path}/{i}") for i in range(len1 - 1, len2 - 1, -1))
    else:
        # Primitive replacement
        changes.append(_create_mutation(op="replace", path=path, value=obj2))

    return changes


def compare_flows(old: GraphFlow | LinearFlow, new: GraphFlow | LinearFlow) -> list[ChangeOperation]:
    """
    Compares two flows and returns a list of semantic JSON Patch operations.
    """
    # Convert to dicts (using mode='json' to ensure serializable)
    d1 = old.model_dump(mode="json", exclude_none=True)
    d2 = new.model_dump(mode="json", exclude_none=True)

    return _generate_diff("", d1, d2)
