import copy
import warnings
from collections.abc import Iterable
from typing import Annotated, Any, Literal

import jsonschema
from jsonschema.exceptions import SchemaError
from pydantic import BaseModel, ConfigDict, Field, model_validator

from coreason_manifest.spec.core.governance import Governance
from coreason_manifest.spec.core.nodes import (
    AgentNode,
    CognitiveProfile,
    EmergenceInspectorNode,
    HumanNode,
    InspectorNode,
    PlaceholderNode,
    PlannerNode,
    SwarmNode,
    SwitchNode,
)
from coreason_manifest.spec.core.resilience import SupervisionPolicy
from coreason_manifest.spec.core.tools import ToolPack

# Polymorphic Node Type
AnyNode = Annotated[
    AgentNode
    | SwitchNode
    | PlannerNode
    | HumanNode
    | PlaceholderNode
    | InspectorNode
    | EmergenceInspectorNode
    | SwarmNode,
    Field(discriminator="type"),
]


class FlowMetadata(BaseModel):
    """Standard metadata fields."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    name: str
    version: str
    description: str
    tags: list[str]


class DataSchema(BaseModel):
    """
    Strict data contract for inputs/outputs.
    Mandate 5: Contract-First Data I/O.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    schema_ref: Annotated[str | None, Field(description="URI to JSON Schema")] = None
    json_schema: dict[str, Any] | bool = Field(
        default_factory=dict,
        description="Full JSON Schema (Draft 7) definition for validation.",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_meta_schema(cls, data: Any) -> Any:
        # Check if we have json_schema key in the input dict
        if isinstance(data, dict) and "json_schema" in data:
            schema = data["json_schema"]

            # Directive 2: Boolean Schema Tolerance
            if isinstance(schema, bool):
                try:
                    jsonschema.Draft7Validator.check_schema(schema)
                    return data
                except SchemaError as e:
                    error_msg = getattr(e, "message", str(e)).split("\n")[0]
                    # Format path context if available
                    path_str = ""
                    if hasattr(e, "path") and e.path:
                        path_str = f" at '/{'/'.join(map(str, e.path))}'"
                    raise ValueError(f"Invalid JSON Schema{path_str}: {error_msg}") from e

            if schema:
                # Directive 4: Immutability Safety
                # Create a mutable copy of the input dictionary if needed
                if isinstance(data, dict):
                    data = data.copy()

                # Directive 3: Pre-Flight Sanitization
                # Always repair first to guarantee finite structure and correct types
                try:
                    repaired_schema = cls._attempt_repair(schema)

                    if repaired_schema != schema:
                        warnings.warn(
                            "Schema repaired automatically during pre-flight sanitization.",
                            category=UserWarning,
                            stacklevel=2,
                        )

                    # Now validate the safe schema
                    jsonschema.Draft7Validator.check_schema(repaired_schema)

                    # Update data with repaired schema
                    data["json_schema"] = repaired_schema

                except SchemaError as e:
                    # Directive 3: Robust Error Unwrapping
                    # Extract only the first line or message to prevent log bloat
                    error_msg = getattr(e, "message", str(e)).split("\n")[0]

                    # Directive 4: High-Fidelity Error Context
                    path_str = ""
                    if hasattr(e, "path") and e.path:
                        path_str = f" at '/{'/'.join(map(str, e.path))}'"

                    raise ValueError(f"Invalid JSON Schema{path_str}: {error_msg}") from e
                except Exception as e:
                    raise ValueError(f"Invalid JSON Schema definition: {e}") from e

        return data

    @staticmethod
    def _escape_ptr(key: str) -> str:
        """Escape JSON Pointer components per RFC 6901."""
        return key.replace("~", "~0").replace("/", "~1")

    @classmethod
    def _attempt_repair(
        cls,
        schema: dict[str, Any],
        current_path: str = "#",
        path_map: dict[int, str] | None = None,
        memo: dict[int, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Recursively repairs schema with:
        1. Cycle detection using JSON Pointer paths (Directive 1).
        2. DAG Memoization for O(N) complexity (Directive 2).
        3. Heuristic repairs for common errors.
        4. Comprehensive combinator traversal (Directive 2).
        """
        if path_map is None:
            path_map = {}
        if memo is None:
            memo = {}

        schema_id = id(schema)

        # Directive 1: Path-Aware Cycle Resolution
        if schema_id in path_map:
            return {"$ref": path_map[schema_id]}

        # Directive 2: Graph Memoization
        if schema_id in memo:
            return copy.deepcopy(memo[schema_id])

        # Track path for ancestors (Cycle Detection)
        path_map[schema_id] = current_path

        try:
            repaired = schema.copy()

            # --- Recursion Step: Schema Mappings ---
            # 1. Properties
            if "properties" in repaired and isinstance(repaired["properties"], dict):
                repaired["properties"] = {
                    k: cls._attempt_repair(
                        v,
                        current_path=f"{current_path}/properties/{cls._escape_ptr(k)}",
                        path_map=path_map,
                        memo=memo,
                    )
                    if isinstance(v, dict)
                    else v
                    for k, v in repaired["properties"].items()
                }

            # 2. Pattern Properties
            if "patternProperties" in repaired and isinstance(repaired["patternProperties"], dict):
                repaired["patternProperties"] = {
                    k: cls._attempt_repair(
                        v,
                        current_path=f"{current_path}/patternProperties/{cls._escape_ptr(k)}",
                        path_map=path_map,
                        memo=memo,
                    )
                    if isinstance(v, dict)
                    else v
                    for k, v in repaired["patternProperties"].items()
                }

            # 3. Definitions & $defs
            for def_key in ["definitions", "$defs"]:
                if def_key in repaired and isinstance(repaired[def_key], dict):
                    repaired[def_key] = {
                        k: cls._attempt_repair(
                            v,
                            current_path=f"{current_path}/{def_key}/{cls._escape_ptr(k)}",
                            path_map=path_map,
                            memo=memo,
                        )
                        if isinstance(v, dict)
                        else v
                        for k, v in repaired[def_key].items()
                    }

            # 4. Additional Properties (if dict)
            if "additionalProperties" in repaired and isinstance(repaired["additionalProperties"], dict):
                repaired["additionalProperties"] = cls._attempt_repair(
                    repaired["additionalProperties"],
                    current_path=f"{current_path}/additionalProperties",
                    path_map=path_map,
                    memo=memo,
                )

            # Directive 1: Exhaustive Draft 7 Schema Traversal (Single Schemas)
            for key in ["if", "then", "else", "not", "contains", "propertyNames", "additionalItems"]:
                if key in repaired and isinstance(repaired[key], dict):
                    repaired[key] = cls._attempt_repair(
                        repaired[key],
                        current_path=f"{current_path}/{key}",
                        path_map=path_map,
                        memo=memo,
                    )

            # Directive 1: Dependencies (Map)
            if "dependencies" in repaired and isinstance(repaired["dependencies"], dict):
                repaired["dependencies"] = {
                    k: cls._attempt_repair(
                        v,
                        current_path=f"{current_path}/dependencies/{cls._escape_ptr(k)}",
                        path_map=path_map,
                        memo=memo,
                    )
                    if isinstance(v, dict)
                    else v
                    for k, v in repaired["dependencies"].items()
                }

            # --- Recursion Step: Schema Arrays ---
            # 5. Combinators (anyOf, allOf, oneOf)
            for comb in ["anyOf", "allOf", "oneOf"]:
                if comb in repaired and isinstance(repaired[comb], list):
                    repaired[comb] = [
                        cls._attempt_repair(
                            sub,
                            current_path=f"{current_path}/{comb}/{idx}",
                            path_map=path_map,
                            memo=memo,
                        )
                        if isinstance(sub, dict)
                        else sub
                        for idx, sub in enumerate(repaired[comb])
                    ]

            # 6. Items (Polymorphic: Dict or List)
            if "items" in repaired:
                if isinstance(repaired["items"], dict):
                    repaired["items"] = cls._attempt_repair(
                        repaired["items"],
                        current_path=f"{current_path}/items",
                        path_map=path_map,
                        memo=memo,
                    )
                elif isinstance(repaired["items"], list):
                    repaired["items"] = [
                        cls._attempt_repair(
                            sub,
                            current_path=f"{current_path}/items/{idx}",
                            path_map=path_map,
                            memo=memo,
                        )
                        if isinstance(sub, dict)
                        else sub
                        for idx, sub in enumerate(repaired["items"])
                    ]

            # --- Heuristic Repairs ---
            # Fix 1: Missing "type": "object" when "properties" exists
            if "properties" in repaired and "type" not in repaired:
                repaired["type"] = "object"

            # Fix 2: Conflict between "default" and "type"
            if "default" in repaired and "type" in repaired:
                t = repaired["type"]
                d = repaired["default"]

                # Directive 3: Defensive Heuristic Typing (Unhashable Trap)
                if isinstance(t, list):
                    types = {str(x) for x in t if isinstance(x, (str, int, bool))}
                elif isinstance(t, (str, int, bool)):
                    types = {str(t)}
                else:
                    types = set()

                is_conflict = False
                new_default = d

                # Handle Null Default Logic (SOTA Hardening)
                if d is None:
                    # Allow null if explicitly nullable or union type includes "null"
                    nullable = repaired.get("nullable", False)
                    is_union_null = "null" in types
                    if not (nullable or is_union_null):
                        # Invalid null default -> remove it
                        is_conflict = True
                else:
                    # Smart Casting for non-null values
                    if "integer" in types and not isinstance(d, int):
                        try:
                            new_default = int(d)
                        except (ValueError, TypeError):
                            if len(types) == 1:
                                is_conflict = True

                    # 1. Integer
                    if "integer" in types and (not isinstance(d, int) or isinstance(d, bool)):
                        if isinstance(d, bool):
                            if len(types) == 1:
                                is_conflict = True
                        else:
                            try:
                                new_default = int(d)
                            except (ValueError, TypeError):
                                if len(types) == 1:
                                    is_conflict = True

                    # 2. String
                    elif "string" in types and not isinstance(d, str):
                        new_default = str(d)

                    # 3. Boolean
                    elif "boolean" in types and not isinstance(d, bool):
                        if str(d).lower() == "true":
                            new_default = True
                        elif str(d).lower() == "false":
                            new_default = False
                        else:
                            if len(types) == 1:
                                is_conflict = True

                    # 4. Float
                    elif "float" in types and not isinstance(d, float):
                        try:
                            new_default = float(d)
                        except (ValueError, TypeError):
                            if len(types) == 1:
                                is_conflict = True

                    # 5. Object & 6. Array
                    elif (
                        ("object" in types and not isinstance(d, dict))
                        or ("array" in types and not isinstance(d, list))
                    ) and len(types) == 1:
                        is_conflict = True

                if is_conflict:
                    del repaired["default"]
                elif new_default != d:
                    repaired["default"] = new_default

            # Directive 2: Store in Memo (fully processed)
            memo[schema_id] = repaired
            return repaired

        finally:
            # Backtrack path map (exit recursion stack)
            del path_map[schema_id]


class FlowInterface(BaseModel):
    """Input/Output JSON schema contracts."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    inputs: DataSchema
    outputs: DataSchema


class VariableDef(BaseModel):
    """Definition of a blackboard variable."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: str
    description: str | None = None


class Blackboard(BaseModel):
    """Shared, observable memory space."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    variables: dict[str, VariableDef]
    persistence: bool


class Edge(BaseModel):
    """Directed connection between nodes."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    source: str
    target: str
    condition: str | None = None


class Graph(BaseModel):
    """Directed execution graph."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    nodes: dict[str, AnyNode]
    edges: list[Edge]


class FlowDefinitions(BaseModel):
    """
    Registry for reusable components (The Blueprint).
    Separates 'definition' from 'usage' to reduce payload size.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    # Maps ID -> Configuration
    profiles: dict[str, CognitiveProfile] = Field(
        default_factory=dict, description="Reusable cognitive configurations."
    )
    tool_packs: dict[str, ToolPack] = Field(default_factory=dict, description="Reusable tool dependencies.")
    supervision_templates: dict[str, SupervisionPolicy] = Field(
        default_factory=dict, description="Reusable resilience policies."
    )
    skills: dict[str, Any] = Field(default_factory=dict, description="Reusable executable skills (Future use).")


def validate_integrity(definitions: FlowDefinitions | None, nodes: Iterable[AnyNode]) -> None:
    """Shared referential integrity validation logic."""
    valid_profiles = definitions.profiles.keys() if definitions else set()

    # SOTA: Create a set of all available tools from registered packs
    valid_tools: set[str] = set()
    if definitions and definitions.tool_packs:
        for pack in definitions.tool_packs.values():
            valid_tools.update(t.name for t in pack.tools)

    valid_policies = definitions.supervision_templates.keys() if definitions else set()

    for node in nodes:
        # Check resilience references
        if isinstance(node.resilience, str):
            if node.resilience.startswith("ref:"):
                ref_id = node.resilience[4:]  # Strip 'ref:' prefix
                if ref_id not in valid_policies:
                    raise ValueError(f"Node '{node.id}' references undefined supervision template ID '{ref_id}'")
            else:
                raise ValueError(
                    f"Node '{node.id}' has invalid resilience reference '{node.resilience}'. Must start with 'ref:'"
                )

        if isinstance(node, AgentNode):
            # 1. Profile Check
            if isinstance(node.profile, str) and node.profile not in valid_profiles:
                raise ValueError(f"AgentNode '{node.id}' references undefined profile ID '{node.profile}'")

            # 2. Tool Check
            for tool in node.tools:
                if tool not in valid_tools:
                    raise ValueError(
                        f"AgentNode '{node.id}' requires missing tool '{tool}'. Available: {list(valid_tools)}"
                    )

        elif isinstance(node, SwarmNode):
            if node.worker_profile not in valid_profiles:
                raise ValueError(
                    f"SwarmNode '{node.id}' references undefined worker profile ID '{node.worker_profile}'"
                )


class LinearFlow(BaseModel):
    """A deterministic script."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    kind: Literal["LinearFlow"]
    status: Annotated[Literal["draft", "published", "archived"], Field(description="Life-cycle state.")] = "draft"
    metadata: FlowMetadata
    definitions: Annotated[FlowDefinitions | None, Field(description="Shared registry for reusable components.")] = None
    sequence: list[AnyNode]
    governance: Annotated[Governance | None, Field(description="Governance policy.")] = None

    @model_validator(mode="after")
    def validate_referential_integrity(self) -> "LinearFlow":
        """Ensures all string-based profile references point to a valid definition."""
        if self.status == "draft":
            return self
        validate_integrity(self.definitions, self.sequence)
        return self


class GraphFlow(BaseModel):
    """Cyclic Graph structure."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    kind: Literal["GraphFlow"]
    status: Annotated[Literal["draft", "published", "archived"], Field(description="Life-cycle state.")] = "draft"
    metadata: FlowMetadata
    definitions: Annotated[FlowDefinitions | None, Field(description="Shared registry for reusable components.")] = None
    interface: FlowInterface
    blackboard: Blackboard | None
    graph: Graph
    governance: Annotated[Governance | None, Field(description="Governance policy.")] = None

    @model_validator(mode="after")
    def validate_referential_integrity(self) -> "GraphFlow":
        """Ensures all string-based profile references point to a valid definition."""
        if self.status == "draft":
            return self
        validate_integrity(self.definitions, self.graph.nodes.values())
        return self
