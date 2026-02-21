# src/coreason_manifest/utils/diff.py

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

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
    category: Literal["BREAKING", "FEATURE", "GOVERNANCE", "RESOURCE"] = "FEATURE"


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
    SOTA Semantic Patch Report containing RFC 6902 operations.
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


def _determine_category(
    op: str, path: str, domain: Literal["resource", "topology", "governance"]
) -> Literal["BREAKING", "FEATURE", "GOVERNANCE", "RESOURCE"]:
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

    category = _determine_category(op, path, domain)

    # Cast to ensure return type matches Union
    return mutation_cls(op=op, path=path, value=value, category=category)  # type: ignore[no-any-return]


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
                effective_domain = recurse_domain_override if recurse_domain_override else next_domain
                changes.extend(_generate_diff(new_path, obj1[key], obj2[key], effective_domain, next_override))

    elif isinstance(obj1, list) and isinstance(obj2, list):
        child_domain = recurse_domain_override if recurse_domain_override else domain

        # SOTA Fix: Identity-based alignment to prevent semantic destruction
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

            # Note: Order matters for JSON Patch indices.
            # Identity diffing for list is complex because removal changes indices.
            # However, prompt directive implies simple set-based comparison.
            # If we just generate add/remove/replace based on ID, the paths might be off if we process out of order.
            # But the prompt logic iterates over `all_ids` (which is unordered set).
            # This implies the order of operations might be random, which is risky for JSON Patch arrays.
            # But let's follow the directive logic precisely as requested.

            # Wait, prompt code iterates `for item_id in all_ids`. Set iteration order is arbitrary.
            # If I remove index 0, index 1 becomes 0. If I then remove (old) index 1, I might remove wrong item.
            # JSON Patch operations are applied sequentially.
            # RFC 6902 requires index adjustments.
            # But the directive says "Implement the exact logic blocks provided below".
            # The provided block iterates `all_ids`.
            # This is flawed if executed as a patch, but the directive demands it.
            # Wait, `_generate_diff` returns a list of operations.
            # If I return `remove /path/0` and `remove /path/2`.
            # If I apply them: remove 0. Original 1 becomes 0. Original 2 becomes 1.
            # Then remove 2. This removes original 3 (which is now 2).
            # So indices refer to the document state *at that time*.

            # The provided logic:
            # `if item_id not in dict1: ... op=add path={path}/{idx2}`
            # `idx2` is the index in `obj2`. Adding at `idx2` implies we construct `obj2`.
            # `elif item_id not in dict2: ... op=remove path={path}/{idx1}`
            # `idx1` is index in `obj1`.

            # This logic assumes "set diffing" and doesn't account for index shifting.
            # However, I MUST follow the directive.
            # I will use `sorted(all_ids)` to at least have deterministic output, but the prompt says "Implement the exact logic".
            # I will paste the logic exactly, but maybe sort `all_ids` for stability if possible,
            # or just iterate `all_ids` as is.
            # But `all_ids` is a set.
            # I will stick to the provided block structure.

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

    else:
        # Primitive replacement
        changes.append(_create_mutation(op="replace", path=path, value=obj2, domain=domain))

    return changes


def compare_flows(old: GraphFlow | LinearFlow, new: GraphFlow | LinearFlow) -> SemanticPatchReport:
    """
    Compares two flows and returns a list of semantic JSON Patch operations.
    """
    # Convert to dicts (using mode='json' to ensure serializable)
    d1 = old.model_dump(mode="json", exclude_none=True)
    d2 = new.model_dump(mode="json", exclude_none=True)

    changes = _generate_diff("", d1, d2)
    return SemanticPatchReport(changes=changes)
