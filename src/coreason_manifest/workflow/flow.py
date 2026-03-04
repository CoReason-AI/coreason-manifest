import ast
import datetime
from collections import deque
from enum import StrEnum
from typing import Annotated, Any, Literal
from uuid import uuid4

from pydantic import Field, StringConstraints, field_validator, model_validator

from coreason_manifest.core.common.base import CoreasonModel
from coreason_manifest.core.common.exceptions import ManifestError, ManifestErrorCode
from coreason_manifest.core.common.semantic import SemanticRef
from coreason_manifest.core.primitives.types import MiddlewareDef, MiddlewareID, NodeID
from coreason_manifest.core.security.compliance import SecurityVisitor
from coreason_manifest.oversight.governance import Governance
from coreason_manifest.state.persistence import PersistenceConfig
from coreason_manifest.state.tools import AnyTool, ToolPack
from coreason_manifest.workflow.evals import EvalsManifest
from coreason_manifest.workflow.nodes import AnyNode
from coreason_manifest.workflow.nodes.base import Constraint
from coreason_manifest.workflow.utils import extract_fallbacks


class ProvenanceType(StrEnum):
    AI = "ai"
    HUMAN = "human"
    HYBRID = "hybrid"


class SignatureAlgorithm(StrEnum):
    ECDSA = "ecdsa"
    ED25519 = "ed25519"
    RSA = "rsa"


class CryptographicAttestation(CoreasonModel):
    signature: Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9+/]+={0,2}$")] = Field(
        ..., description="Base64 encoded cryptographic signature of the manifest's canonical hash."
    )
    public_key_ref: str = Field(..., description="URI or ID of the public key used to verify the signature.")
    algorithm: SignatureAlgorithm = Field(default=SignatureAlgorithm.ECDSA, description="The signing algorithm used.")
    signed_at: str = Field(..., description="ISO-8601 timestamp of when the manifest was cryptographically sealed.")

    @field_validator("signed_at")
    @classmethod
    def validate_iso8601(cls, v: str) -> str:
        """Enforce that signed_at is a valid ISO-8601 timestamp."""
        try:
            datetime.datetime.fromisoformat(v)
        except ValueError as e:
            raise ValueError(f"Invalid ISO-8601 timestamp: {v}") from e
        return v


class ProvenanceData(CoreasonModel):
    type: ProvenanceType = Field(..., description="Origin type of the workflow.")
    generated_by: str | None = Field(None, description="The system or model ID that generated this manifest.")
    derived_from: str | None = Field(None, description="The ID/URI of the parent flow this was forked from.")
    rationale: str | None = Field(None, description="Reasoning for why this specific topology was generated.")
    modifications: list[str] = Field(default_factory=list, description="Human-readable log of changes.")
    attestation: CryptographicAttestation | None = Field(
        None, description="Cryptographic proof that this workflow was authorized."
    )


__all__ = [
    "Blackboard",
    "DataSchema",
    "Edge",
    "FlowDefinitions",
    "FlowInterface",
    "FlowMetadata",
    "Graph",
    "GraphFlow",
    "LinearFlow",
    "VariableDef",
]


class FlowMetadata(CoreasonModel):
    name: str
    version: str
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None
    provenance: ProvenanceData | None = Field(
        None, description="Cryptographic/Lineage tracking for AI supply chain security."
    )


class DataSchema(CoreasonModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    json_schema: dict[str, Any] = Field(default_factory=dict)


class Blackboard(CoreasonModel):
    variables: dict[str, Any] = Field(default_factory=dict)
    schemas: list[DataSchema] = Field(default_factory=list)
    persistence: PersistenceConfig | None = None


class Edge(CoreasonModel):
    from_node: NodeID
    to_node: NodeID
    condition: str | None = None
    cost_weight: float = Field(0.0, ge=0.0, description="Estimated financial cost (USD) to traverse this edge.")
    latency_weight_ms: float = Field(0.0, ge=0.0, description="Estimated latency in milliseconds.")
    is_feedback: bool = Field(
        default=False,
        description="Marks an edge as a backward loop for UI visualization and circuit-breaker routing.",
    )

    @field_validator("condition", mode="before")
    @classmethod
    def validate_condition_ast(cls, v: str | None) -> str | None:
        """
        Parse the condition string into an Abstract Syntax Tree (AST) and enforce the SecurityVisitor whitelist.

        Enforces a strict 2048-character limit to prevent AST parsing Denial of Service (DoS) memory exhaustion.

        Raises:
            ValueError: If the condition exceeds 2048 characters, contains invalid Python
                syntax, or uses unsafe AST nodes.
        """
        if v is None or not v.strip():
            return v
        if len(v) > 2048:
            raise ValueError(
                "Condition expression exceeds maximum safe length of 2048 characters to prevent AST parsing DoS."
            )
        try:
            tree = ast.parse(v, mode="eval")
        except SyntaxError as e:
            raise ValueError(f"Syntax error in condition '{v}': {e}") from e
        visitor = SecurityVisitor()
        visitor.visit(tree)
        return v


class Graph(CoreasonModel):
    nodes: dict[str, AnyNode]
    edges: list[Edge]
    entry_point: NodeID | None = None
    allow_cycles: bool = Field(
        default=False, description="If true, bypasses strict DAG validation to allow agentic feedback loops."
    )

    @model_validator(mode="after")
    def validate_graph_structure(self) -> "Graph":
        """
        Enforce topology constraints, missing entry point, dangling edges, and strict DAG properties.

        Utilizes Kahn's Algorithm (iterative topological sort) for cycle detection to guarantee memory
        safety and prevent RecursionErrors on massively deep graphs.

        Raises:
            ManifestError: For structural violations or if a cycle is detected.

        Notes:
            While dict keys are unique natively, we enforce key == node.id.
            The seen_ids check acts as a strict Defense-in-Depth against advanced
            Pydantic aliasing attacks where multiple distinct keys might resolve
            to pointers sharing the same inner ID.
        """
        valid_ids = set(self.nodes.keys())

        if not self.nodes:
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.VAL_TOPOLOGY_EMPTY,
                message="Graph must contain at least one node.",
            )

        seen_ids = set()
        for key, node in self.nodes.items():
            if key != node.id:
                raise ManifestError.critical_halt(
                    code=ManifestErrorCode.VAL_TOPOLOGY_ID_MISMATCH,
                    message=f"Routing contradiction: Node dictionary key '{key}' "
                    f"does not match inner Node ID '{node.id}'.",
                    context={"dict_key": key, "node_id": node.id},
                )
            if node.id in seen_ids:
                raise ManifestError.critical_halt(
                    code=ManifestErrorCode.VAL_TOPOLOGY_NODE_ID_COLLISION,
                    message=f"Internal collision defense: Node ID '{node.id}' appears multiple times.",
                    context={"node_id": node.id},
                )
            seen_ids.add(node.id)

        # Entry Point
        if self.entry_point and self.entry_point not in valid_ids:
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.VAL_TOPOLOGY_MISSING_ENTRY,
                message=f"Entry point '{self.entry_point}' not found in nodes.",
            )

        # Edges
        for edge in self.edges:
            if edge.from_node not in valid_ids:
                raise ManifestError.critical_halt(
                    code=ManifestErrorCode.VAL_TOPOLOGY_DANGLING_EDGE,
                    message=f"Source '{edge.from_node}' not found in graph nodes.",
                )
            if edge.to_node not in valid_ids:
                raise ManifestError.critical_halt(
                    code=ManifestErrorCode.VAL_TOPOLOGY_DANGLING_EDGE,
                    message=f"Target '{edge.to_node}' not found in graph nodes.",
                )

        # Fallback ID Integrity
        for node in self.nodes.values():
            node_data = node.model_dump(exclude_none=True)
            for fallback_id in extract_fallbacks(node_data):
                if fallback_id not in valid_ids:
                    raise ManifestError.critical_halt(
                        code=ManifestErrorCode.VAL_TOPOLOGY_DANGLING_EDGE,
                        message=f"Fallback target '{fallback_id}' in node '{node.id}' not found in graph nodes.",
                        context={"node_id": node.id, "fallback_id": fallback_id},
                    )

        # Cycle Detection
        adj_map: dict[str, set[str]] = {n: set() for n in valid_ids}
        in_degree: dict[str, int] = dict.fromkeys(valid_ids, 0)

        for edge in self.edges:
            adj_map[edge.from_node].add(edge.to_node)

        for neighbors in adj_map.values():
            for neighbor in neighbors:
                in_degree[neighbor] += 1

        queue = deque([n for n in valid_ids if in_degree[n] == 0])
        processed_nodes = 0

        while queue:
            current = queue.popleft()
            processed_nodes += 1
            for neighbor in adj_map.get(current, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if processed_nodes != len(valid_ids) and not self.allow_cycles:
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.VAL_TOPOLOGY_CYCLE,
                message="Execution graphs must be strict Directed Acyclic Graphs (DAGs). Cycle detected.",
            )

        return self


class FlowInterface(CoreasonModel):
    inputs: dict[str, Any] | DataSchema = Field(default_factory=dict)
    outputs: dict[str, Any] | DataSchema = Field(default_factory=dict)


class FlowDefinitions(CoreasonModel):
    profiles: dict[str, Any] = Field(default_factory=dict)
    schemas: dict[str, Any] = Field(default_factory=dict)
    tools: dict[str, AnyTool] = Field(default_factory=dict)
    tool_packs: dict[str, ToolPack] = Field(default_factory=dict)
    skills: dict[str, Any] = Field(default_factory=dict)
    middlewares: dict[MiddlewareID, MiddlewareDef] = Field(default_factory=dict)
    supervision_templates: Any | None = None


class VariableDef(CoreasonModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str
    description: str | None = None


class GraphFlow(CoreasonModel):
    """
    Standard graph-based execution flow.

    """

    type: Literal["graph"] = "graph"
    kind: Literal["GraphFlow"] = "GraphFlow"
    status: Literal["draft", "published", "archived"] = "draft"
    metadata: FlowMetadata
    interface: FlowInterface
    pre_flight_constraints: list[Constraint] = Field(
        default_factory=list, description="Feasibility gates evaluated before the workflow is allocated compute."
    )
    governance: Governance | None = None
    blackboard: Blackboard | None = Field(default_factory=Blackboard)
    definitions: FlowDefinitions | None = None
    graph: Graph
    max_iterations: int | None = Field(
        default=None, description="Circuit breaker for cyclic graphs to prevent infinite token burn."
    )
    evals: EvalsManifest | None = Field(None, description="Embedded executable specifications and test scenarios.")

    @model_validator(mode="after")
    def enforce_circuit_breaker(self) -> "GraphFlow":
        """Enforce that cyclic graphs have a strictly positive max_iterations circuit breaker."""
        if self.graph.allow_cycles and (self.max_iterations is None or self.max_iterations < 1):
            raise ValueError(
                "A GraphFlow with 'allow_cycles=True' must define a valid 'max_iterations' circuit breaker."
            )
        return self

    @model_validator(mode="after")
    def validate_middleware_integrity(self) -> "GraphFlow":
        """Verify that all active middlewares are defined in the manifest to prevent fail-open bypass."""
        if self.governance and self.governance.active_middlewares:
            available_middlewares = (
                self.definitions.middlewares.keys() if self.definitions and self.definitions.middlewares else set()
            )
            for middleware_id in self.governance.active_middlewares:
                if middleware_id not in available_middlewares:
                    msg = (
                        f"Security Fail-Open Risk: Active middleware '{middleware_id}' "
                        "is not defined in definitions.middlewares."
                    )
                    raise ManifestError.critical_halt(
                        code=ManifestErrorCode.VAL_LIFECYCLE_UNRESOLVED,
                        message=msg,
                        context={"middleware_id": middleware_id},
                    )
        return self

    @model_validator(mode="after")
    def enforce_lifecycle_constraints(self) -> "GraphFlow":
        """Enforce that published flows have valid metadata, entry point, and no placeholders."""
        if self.status != "published":
            return self
        if getattr(self.metadata, "provenance", None) is None:
            raise ValueError(
                "Lifecycle Violation: Cannot publish flow without a signed ProvenanceData block. "
                "The Weaver must declare its lineage."
            )
        for node in self.graph.nodes.values():
            if node.type == "placeholder":
                raise ValueError("Cannot publish a flow with placeholder nodes")
        if self.graph.entry_point is None:
            raise ValueError("Cannot publish a GraphFlow without an entry point")
        return self

    @model_validator(mode="after")
    def enforce_aot_compilation(self) -> "GraphFlow":
        """Enforce that published flows have no unresolved semantic references.

        Raises:
            ManifestError: If unresolved references are found.
        """
        if self.status == "published":
            unresolved = [
                str(getattr(node, "id", ""))
                for node in self.graph.nodes.values()
                if getattr(node, "type", None) == "agent"
                and (
                    isinstance(getattr(node, "profile", None), SemanticRef)
                    or isinstance(getattr(node, "tools", None), SemanticRef)
                )
            ]
            if unresolved:
                msg = (
                    f"Lifecycle Violation: Cannot publish graph. Nodes [{','.join(unresolved)}] "
                    "contain unresolved SemanticRefs. A Weaver must compile this graph into "
                    "concrete profiles before publication."
                )
                raise ManifestError.critical_halt(code=ManifestErrorCode.VAL_LIFECYCLE_UNRESOLVED, message=msg)
        return self


class LinearFlow(CoreasonModel):
    """
    Simplified linear execution flow (sequence of steps).

    """

    type: Literal["linear"] = "linear"
    kind: Literal["LinearFlow"] = "LinearFlow"
    status: Literal["draft", "published", "archived"] = "draft"
    metadata: FlowMetadata
    pre_flight_constraints: list[Constraint] = Field(
        default_factory=list, description="Feasibility gates evaluated before the workflow is allocated compute."
    )
    steps: list[AnyNode] = Field(default_factory=list)
    governance: Governance | None = None
    definitions: FlowDefinitions | None = None
    evals: EvalsManifest | None = Field(None, description="Embedded executable specifications and test scenarios.")

    @model_validator(mode="after")
    def validate_middleware_integrity(self) -> "LinearFlow":
        """Verify that all active middlewares are defined in the manifest to prevent fail-open bypass."""
        if self.governance and self.governance.active_middlewares:
            available_middlewares = (
                self.definitions.middlewares.keys() if self.definitions and self.definitions.middlewares else set()
            )
            for middleware_id in self.governance.active_middlewares:
                if middleware_id not in available_middlewares:
                    msg = (
                        f"Security Fail-Open Risk: Active middleware '{middleware_id}' "
                        "is not defined in definitions.middlewares."
                    )
                    raise ManifestError.critical_halt(
                        code=ManifestErrorCode.VAL_LIFECYCLE_UNRESOLVED,
                        message=msg,
                        context={"middleware_id": middleware_id},
                    )
        return self

    @model_validator(mode="after")
    def validate_linear_structure(self) -> "LinearFlow":
        """Enforce that linear sequence is not empty and has unique step IDs.

        Raises:
            ManifestError: For structural violations.
        """
        if not self.steps:
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.VAL_TOPOLOGY_LINEAR_EMPTY,
                message="Sequence cannot be empty.",
            )

        seen = set()
        for step in self.steps:
            if step.id in seen:
                raise ManifestError.critical_halt(
                    code=ManifestErrorCode.VAL_TOPOLOGY_NODE_ID_COLLISION,
                    message=f"Duplicate Node ID '{step.id}' found in LinearFlow steps.",
                    context={"node_id": step.id},
                )
            seen.add(step.id)

        return self

    @model_validator(mode="after")
    def enforce_lifecycle_constraints(self) -> "LinearFlow":
        """Enforce that published flows have valid metadata, entry point, and no placeholders."""
        if self.status != "published":
            return self
        if getattr(self.metadata, "provenance", None) is None:
            raise ValueError(
                "Lifecycle Violation: Cannot publish flow without a signed ProvenanceData block. "
                "The Weaver must declare its lineage."
            )
        for node in self.steps:
            if node.type == "placeholder":
                raise ValueError("Cannot publish a flow with placeholder nodes")
        return self

    @model_validator(mode="after")
    def enforce_aot_compilation(self) -> "LinearFlow":
        """Enforce that published flows have no unresolved semantic references.

        Raises:
            ManifestError: If unresolved references are found.
        """
        if self.status == "published":
            unresolved = [
                str(getattr(node, "id", ""))
                for node in self.steps
                if getattr(node, "type", None) == "agent"
                and (
                    isinstance(getattr(node, "profile", None), SemanticRef)
                    or isinstance(getattr(node, "tools", None), SemanticRef)
                )
            ]
            if unresolved:
                msg = (
                    f"Lifecycle Violation: Cannot publish linear flow. Nodes [{','.join(unresolved)}] "
                    "contain unresolved SemanticRefs. A Weaver must compile this linear flow into "
                    "concrete profiles before publication."
                )
                raise ManifestError.critical_halt(code=ManifestErrorCode.VAL_LIFECYCLE_UNRESOLVED, message=msg)
        return self
