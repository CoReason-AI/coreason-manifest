# src/coreason_manifest/utils/diff.py

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from coreason_manifest.spec.core.flow import FlowSpec

type DomainType = Literal["resource", "topology", "governance"]
type MutationOp = Literal["add", "remove", "replace", "move", "copy", "test"]
type CategoryType = Literal["BREAKING", "FEATURE", "GOVERNANCE", "RESOURCE"]


class BaseOperation(BaseModel):
    """
    Base class for RFC 6902 JSON Patch operations.
    """

    model_config = ConfigDict(extra="ignore", strict=True, frozen=True)

    op: MutationOp
    path: str
    value: Any = None
    from_: Annotated[str | None, Field(alias="from")] = None
    category: CategoryType = "FEATURE"


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


class SemanticPatchReport(BaseModel):
    """
    Semantic Patch Report containing RFC 6902 operations.
    Computes breaking changes and semantic categories.
    """

    model_config = ConfigDict(extra="ignore", strict=True, frozen=True)

    changes: list[ChangeOperation]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_breaking(self) -> bool:
        """
        Determines if the patch contains breaking changes.
        """
        return any(op.category == "BREAKING" for op in self.changes)


def _determine_category(op: str, path: str, domain: DomainType) -> CategoryType:
    """
    Determines the semantic category of an operation.
    """
    if domain == "governance" or "/policy" in path or "/governance" in path:
        return "GOVERNANCE"

    if domain == "resource":
        return "RESOURCE"

    # Topology and other structural changes
    if op == "remove":
        return "BREAKING"
    if op == "replace":
        # Replacing a value might be breaking depending on what it is, assume breaking for safety in topology
        return "BREAKING"

    # Additions are generally features
    return "FEATURE"


def _create_mutation(
    op: MutationOp,
    path: str,
    value: Any = None,
    domain: DomainType = "resource",
) -> ChangeOperation:
    category = _determine_category(op, path, domain)

    if domain == "resource":
        return ResourceMutation(op=op, path=path, value=value, category=category)
    if domain == "topology":
        return TopologyMutation(op=op, path=path, value=value, category=category)
    if domain == "governance":
        return GovernanceMutation(op=op, path=path, value=value, category=category)

    # Should be unreachable with strict types
    return ResourceMutation(op=op, path=path, value=value, category=category)  # pragma: no cover


def _escape_json_pointer(key: str) -> str:
    """
    Escapes a dictionary key for use in a JSON Pointer (RFC 6901).
    ~ -> ~0
    / -> ~1
    """
    return key.replace("~", "~0").replace("/", "~1")


def _diff_dicts(
    path: str,
    obj1: dict[str, Any],
    obj2: dict[str, Any],
    domain: DomainType,
    recurse_domain_override: DomainType | None,
) -> list[ChangeOperation]:
    changes: list[ChangeOperation] = []
    all_keys = set(obj1.keys()) | set(obj2.keys())
    for key in sorted(all_keys):
        # Architectural Note: RFC 6901 Escaping
        escaped_key = _escape_json_pointer(key)
        new_path = f"{path}/{escaped_key}"

        # Architectural Note: Contextual Domain Switching
        # Determine domain for the current key and subsequent recursion.
        next_domain = domain
        next_override: DomainType | None = None

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
    return changes


def _diff_lists(
    path: str,
    obj1: list[Any],
    obj2: list[Any],
    domain: DomainType,
    recurse_domain_override: DomainType | None,
) -> list[ChangeOperation]:
    changes: list[ChangeOperation] = []
    child_domain = recurse_domain_override or domain

    # Architectural Note: Identity-based alignment to prevent semantic destruction
    def get_identity(item: Any) -> Any:
        if isinstance(item, dict):
            return item.get("id") or item.get("name") or item.get("key")
        return None

    # Create lookup maps for identity-based diffing
    dict1 = {get_identity(item): (i, item) for i, item in enumerate(obj1) if get_identity(item)}
    dict2 = {get_identity(item): (i, item) for i, item in enumerate(obj2) if get_identity(item)}

    # Only use identity diffing if all items have identities and there are no duplicate identities
    if dict1 and dict2 and len(dict1) == len(obj1) and len(dict2) == len(obj2):
        # All items have identities, diff by identity
        all_ids = set(dict1.keys()) | set(dict2.keys())

        # Identity Heuristic: Iterate over all unique IDs found in either list.

        for item_id in all_ids:
            if item_id not in dict1:
                idx2, val2 = dict2[item_id]
                changes.append(_create_mutation(op="add", path=f"{path}/{idx2}", value=val2, domain=domain))
            elif item_id not in dict2:
                idx1, val1 = dict1[item_id]
                changes.append(_create_mutation(op="remove", path=f"{path}/{idx1}", domain=domain))
            else:
                idx1, val1 = dict1[item_id]
                idx2, val2 = dict2[item_id]
                # If index changed, we might need 'move', but prompt logic just recurses.
                # It uses idx2 for path? "changes.extend(_generate_diff(f"{path}/{idx2}", ...))"
                # This seems to assume alignment or in-place update.
                changes.extend(_generate_diff(f"{path}/{idx2}", val1, val2, child_domain, None))
    else:
        # Fallback to standard index diffing if identities are missing
        for i in range(max(len(obj1), len(obj2))):
            if i < len(obj1) and i < len(obj2):
                changes.extend(_generate_diff(f"{path}/{i}", obj1[i], obj2[i], child_domain, None))
            elif i >= len(obj1):
                changes.append(_create_mutation(op="add", path=f"{path}/{i}", value=obj2[i], domain=domain))
            else:
                changes.append(_create_mutation(op="remove", path=f"{path}/{i}", domain=domain))
    return changes


def _generate_diff(
    path: str,
    obj1: Any,
    obj2: Any,
    domain: DomainType = "resource",
    recurse_domain_override: DomainType | None = None,
) -> list[ChangeOperation]:
    """
    Recursively generates JSON Patch operations with contextual domain awareness.
    """
    changes: list[ChangeOperation] = []

    if obj1 == obj2:
        return changes

    if isinstance(obj1, dict) and isinstance(obj2, dict):
        changes.extend(_diff_dicts(path, obj1, obj2, domain, recurse_domain_override))
    elif isinstance(obj1, list) and isinstance(obj2, list):
        changes.extend(_diff_lists(path, obj1, obj2, domain, recurse_domain_override))
    else:
        # Primitive replacement
        changes.append(_create_mutation(op="replace", path=path, value=obj2, domain=domain))

    return changes


def compare_flows(old: FlowSpec, new: FlowSpec) -> SemanticPatchReport:
    """
    Compares two flows and returns a list of semantic JSON Patch operations.
    """
    # Convert to dicts (using mode='json' to ensure serializable)
    d1 = old.model_dump(mode="json", exclude_none=True, by_alias=True)
    d2 = new.model_dump(mode="json", exclude_none=True, by_alias=True)

    changes = _generate_diff("", d1, d2)
    return SemanticPatchReport(changes=changes)
