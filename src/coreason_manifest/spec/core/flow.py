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
    json_schema: dict[str, Any] = Field(
        default_factory=dict,
        description="Full JSON Schema (Draft 7) definition for validation.",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_meta_schema(cls, data: Any) -> Any:
        # Check if we have json_schema key in the input dict
        if isinstance(data, dict) and "json_schema" in data:
            schema = data["json_schema"]
            if schema:
                try:
                    # SOTA: Validates that the dictionary is ACTUALLY a valid JSON Schema.
                    jsonschema.Draft7Validator.check_schema(schema)
                except SchemaError as e:
                    # Domain 3: Adaptive Schema Repair
                    try:
                        repaired_schema = cls._attempt_repair(schema)

                        # Verify repair worked
                        jsonschema.Draft7Validator.check_schema(repaired_schema)

                        # Log warning
                        warnings.warn(
                            f"Schema repaired automatically. Original error: {e.message}",
                            category=UserWarning,
                            stacklevel=2,
                        )

                        # Update data dict with repaired schema
                        data["json_schema"] = repaired_schema

                    except Exception:
                        # Repair failed or verification failed
                        raise ValueError(f"Invalid JSON Schema definition: {e.message}") from e
        return data

    @staticmethod
    def _attempt_repair(schema: dict[str, Any]) -> dict[str, Any]:
        """
        Heuristics to repair common schema errors.
        Returns a NEW dict with repairs applied.
        """
        repaired = schema.copy()

        # Fix 1: Missing "type": "object" when "properties" exists
        if "properties" in repaired and "type" not in repaired:
            repaired["type"] = "object"

        # Fix 2: Conflict between "default" and "type"
        if "default" in repaired and "type" in repaired:
            t = repaired["type"]
            d = repaired["default"]

            # Normalize type to set for consistent union handling
            types = set(t) if isinstance(t, list) else {t}

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
                        # If integer conversion fails, only conflict if no other type matches
                        # But for simplicity in repair, if we target int and fail, it's likely bad.
                        # However, with union types (e.g. string|int), 'abc' is valid.
                        # We only force-repair if the VALUE doesn't match ANY of the types.
                        # Since we are doing smart casting, we try to cast to the 'primary' type if apparent.
                        # SOTA: If multiple types, we shouldn't aggressively cast unless unambiguous.
                        # But the goal here is to fix BROKEN defaults (e.g. "123" for int).
                        # We proceed with casting if it matches one of the target types.
                        is_conflict = True

                # Note: The logic below sequentially tries to cast/validate.
                # If union type ["string", "integer"], and value is "123":
                # - integer check tries to cast "123" -> 123.
                # - string check sees "123" is string.
                # If we convert to 123, is it valid? Yes.
                # If we leave as "123", is it valid? Yes.
                # We should prefer the original if valid.
                # BUT the original code was aggressive.
                # Let's check validity against ANY type first.

                # Simplified robust repair:
                # 1. Integer
                # Note: isinstance(True, int) is True, so we must explicitly check for bool
                if "integer" in types and (not isinstance(d, int) or isinstance(d, bool)):
                    # Prevent bool -> int casting (False becomes 0, True becomes 1)
                    if isinstance(d, bool):
                        if len(types) == 1:
                            is_conflict = True
                    else:
                        try:
                            new_default = int(d)
                        except (ValueError, TypeError):
                            # If it's not int, maybe it matches another type in union?
                            # If simple type 'integer', then it IS a conflict.
                            if len(types) == 1:
                                is_conflict = True

                # 2. String
                elif "string" in types and not isinstance(d, str):
                    # Don't coerce if we just successfully cast to int above?
                    # Actually logic flow needs care.
                    # Reverting to linear checks with 'types' set membership for robustness.
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
                    ("object" in types and not isinstance(d, dict)) or ("array" in types and not isinstance(d, list))
                ) and len(types) == 1:
                    is_conflict = True

            if is_conflict:
                del repaired["default"]
            elif new_default != d:
                repaired["default"] = new_default

        return repaired


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
