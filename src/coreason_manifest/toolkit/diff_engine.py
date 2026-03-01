# src/coreason_manifest/utils/diff.py

from copy import deepcopy
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from coreason_manifest.core.state.persistence import JSONPatchOperation, PatchOp
from coreason_manifest.core.workflow.flow import GraphFlow, LinearFlow

type DomainType = Literal["resource", "topology", "governance", "evals"]
type MutationOp = Literal["add", "remove", "replace", "move", "copy", "test"]
type CategoryType = Literal["BREAKING", "FEATURE", "GOVERNANCE", "RESOURCE", "TEST"]


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


class EvalsMutation(BaseOperation):
    """Mutation affecting embedded tests and executable specifications."""

    mutation_type: Literal["evals"] = "evals"


ChangeOperation = Annotated[
    ResourceMutation | TopologyMutation | GovernanceMutation | EvalsMutation, Field(discriminator="mutation_type")
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
    if domain == "evals" or "/evals" in path:
        return "TEST"

    if (
        domain == "governance"
        or "/policy" in path
        or "/governance" in path
        or "/attestation" in path
        or "/unicode_sanitization" in path
    ):
        return "GOVERNANCE"

    if "/presentation" in path or "/routing" in path or "/render_strategy" in path or "/ui_contract" in path:
        return "FEATURE"

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
    if domain == "evals":
        return EvalsMutation(op=op, path=path, value=value, category=category)

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
        elif key == "evals":
            next_domain = "evals"

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


def compare_flows(old: GraphFlow | LinearFlow, new: GraphFlow | LinearFlow) -> SemanticPatchReport:
    """
    Compares two flows and returns a list of semantic JSON Patch operations.
    """
    # Convert to dicts (using mode='json' to ensure serializable)
    d1 = old.model_dump(mode="json", exclude_none=True, by_alias=True)
    d2 = new.model_dump(mode="json", exclude_none=True, by_alias=True)

    changes = _generate_diff("", d1, d2)
    return SemanticPatchReport(changes=changes)


def _resolve_json_pointer(obj: Any, pointer: str) -> tuple[Any, str]:
    """
    Resolves a JSON Pointer to return the parent object and the specific key/index.
    """
    if pointer == "" or pointer == "/":
        return obj, ""

    parts = pointer.strip("/").split("/")
    current = obj
    for _, part in enumerate(parts[:-1]):
        key = part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            current = current[key]
        elif isinstance(current, list):
            current = current[int(key)]
        else:
            raise KeyError(f"Cannot resolve path segment '{part}' in '{pointer}'")

    final_key = parts[-1].replace("~1", "/").replace("~0", "~")
    return current, final_key


def _apply_patch_in_place(state: Any, patch: JSONPatchOperation) -> None:
    """
    Applies a single RFC 6902 operation in-place to the state.
    """
    if patch.op == PatchOp.ADD:
        parent, key = _resolve_json_pointer(state, patch.path)
        if isinstance(parent, dict):
            parent[key] = deepcopy(patch.value)
        elif isinstance(parent, list):
            parent.insert(int(key), deepcopy(patch.value))
    elif patch.op == PatchOp.REMOVE:
        parent, key = _resolve_json_pointer(state, patch.path)
        if isinstance(parent, dict):
            del parent[key]
        elif isinstance(parent, list):
            del parent[int(key)]
    elif patch.op == PatchOp.REPLACE:
        parent, key = _resolve_json_pointer(state, patch.path)
        if isinstance(parent, dict):
            parent[key] = deepcopy(patch.value)
        elif isinstance(parent, list):
            parent[int(key)] = deepcopy(patch.value)
    elif patch.op == PatchOp.MOVE:
        if patch.from_ is None:
            raise ValueError("move requires from")
        source_parent, source_key = _resolve_json_pointer(state, patch.from_)
        val = source_parent.pop(source_key) if isinstance(source_parent, dict) else source_parent.pop(int(source_key))
        target_parent, target_key = _resolve_json_pointer(state, patch.path)
        if isinstance(target_parent, dict):
            target_parent[target_key] = val
        else:
            target_parent.insert(int(target_key), val)
    elif patch.op == PatchOp.COPY:
        if patch.from_ is None:
            raise ValueError("copy requires from")
        source_parent, source_key = _resolve_json_pointer(state, patch.from_)
        if isinstance(source_parent, dict):
            val = deepcopy(source_parent[source_key])
        else:
            val = deepcopy(source_parent[int(source_key)])
        target_parent, target_key = _resolve_json_pointer(state, patch.path)
        if isinstance(target_parent, dict):
            target_parent[target_key] = val
        else:
            target_parent.insert(int(target_key), val)
    elif patch.op == PatchOp.TEST:
        parent, key = _resolve_json_pointer(state, patch.path)
        current_val = parent.get(key) if isinstance(parent, dict) else parent[int(key)]
        if current_val != patch.value:
            raise ValueError(f"Test failed at {patch.path}: expected {patch.value}, got {current_val}")


def generate_inverse_patches(
    original_state: dict[str, Any], patches: list[JSONPatchOperation]
) -> list[JSONPatchOperation]:
    """
    Calculates the exact inverse of an applied patch list.
    """
    inverse_patches: list[JSONPatchOperation] = []
    current_state = deepcopy(original_state)

    for patch in patches:
        if patch.op == PatchOp.ADD:
            # Reversing an add is a remove
            inverse_patches.append(JSONPatchOperation(op=PatchOp.REMOVE, path=patch.path, value=None, from_=None))
            _apply_patch_in_place(current_state, patch)

        elif patch.op == PatchOp.REMOVE:
            # Reversing a remove is an add, needing the original value
            parent, key = _resolve_json_pointer(current_state, patch.path)
            original_value = parent[key] if isinstance(parent, dict) else parent[int(key)]
            inverse_patches.append(
                JSONPatchOperation(op=PatchOp.ADD, path=patch.path, value=deepcopy(original_value), from_=None)
            )
            _apply_patch_in_place(current_state, patch)

        elif patch.op == PatchOp.REPLACE:
            # Reversing a replace is a replace with the old value
            parent, key = _resolve_json_pointer(current_state, patch.path)
            old_value = parent.get(key) if isinstance(parent, dict) else parent[int(key)]
            inverse_patches.append(
                JSONPatchOperation(op=PatchOp.REPLACE, path=patch.path, value=deepcopy(old_value), from_=None)
            )
            _apply_patch_in_place(current_state, patch)

        elif patch.op == PatchOp.MOVE:
            # Reversing a move is a move back
            if patch.from_ is None:
                raise ValueError("move requires from")
            inverse_patches.append(JSONPatchOperation(op=PatchOp.MOVE, path=patch.from_, value=None, from_=patch.path))
            _apply_patch_in_place(current_state, patch)

        elif patch.op == PatchOp.COPY:
            # Reversing a copy is a remove at the target
            inverse_patches.append(JSONPatchOperation(op=PatchOp.REMOVE, path=patch.path, value=None, from_=None))
            _apply_patch_in_place(current_state, patch)

        elif patch.op == PatchOp.TEST:
            # Test has no state effect, its inverse is the same test
            inverse_patches.append(
                JSONPatchOperation(op=PatchOp.TEST, path=patch.path, value=deepcopy(patch.value), from_=None)
            )
            _apply_patch_in_place(current_state, patch)

    inverse_patches.reverse()
    return inverse_patches


def apply_rewind(current_state: dict[str, Any], reverse_patches: list[JSONPatchOperation]) -> dict[str, Any]:
    """
    Applies inverse patches to a state dictionary.
    """
    rewound_state = deepcopy(current_state)
    for patch in reverse_patches:
        _apply_patch_in_place(rewound_state, patch)
    return rewound_state
