import ast
import datetime
from collections import deque
from enum import StrEnum
from typing import Annotated, Any, Literal
from uuid import uuid4

from pydantic import Field, StringConstraints, field_validator, model_validator

from coreason_manifest.adapters.mcp.server import MCPServerConfig
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
    "AnyTopology",
    "BaseTopology",
    "Blackboard",
    "CouncilTopology",
    "DAGTopology",
    "DCGTopology",
    "DataSchema",
    "EventDrivenTopology",
    "ExplicitGraphTopology",
    "FlowDefinitions",
    "FlowInterface",
    "FlowMetadata",
    "HierarchicalTopology",
    "MapReduceTopology",
    "SwarmTopology",
    "VariableDef",
    "WorkflowEnvelope",
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


class MCPServerExport(CoreasonModel):
    """Configuration to expose a workflow as an MCP Tool/Server."""

    expose_as_tool: bool = Field(default=True, description="If true, the workflow execution is exposed as an MCP Tool.")
    tool_name: str = Field(..., description="The exact name exposed to the calling MCP Client.")
    tool_description: str = Field(
        ..., description="Semantic description of the workflow's capability for the LLM tool-calling router."
    )
    expose_blackboard_as_resources: bool = Field(
        default=False, description="If True, blackboard variables become URI-addressable MCP resources."
    )
    propagate_trace_context: bool = Field(
        default=True,
        description="Enforces that W3C trace contexts from the caller are passed into this workflow's execution.",
    )


class BaseTopology(CoreasonModel):
    """Base boundary for all routing logic."""

    topology_type: str


class ExplicitGraphTopology(BaseTopology):
    """Intermediate boundary for topologies that rely on explicit node-to-node edges."""

    nodes: dict[str, AnyNode]
    edges: list[Edge]
    entry_point: NodeID | None = None

    @model_validator(mode="after")
    def validate_structural_integrity(self) -> "ExplicitGraphTopology":
        """Enforces base structural rules: No empty graphs, no dangling edges, valid entry points."""
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
                    message=f"Routing contradiction: Node dictionary key '{key}' does not match inner ID '{node.id}'.",
                    context={"dict_key": key, "node_id": node.id},
                )
            if node.id in seen_ids:
                raise ManifestError.critical_halt(
                    code=ManifestErrorCode.VAL_TOPOLOGY_NODE_ID_COLLISION,
                    message=f"Internal collision defense: Node ID '{node.id}' appears multiple times.",
                    context={"node_id": node.id},
                )
            seen_ids.add(node.id)

        if self.entry_point and self.entry_point not in valid_ids:
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.VAL_TOPOLOGY_MISSING_ENTRY,
                message=f"Entry point '{self.entry_point}' not found in nodes.",
            )

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
        return self


class DAGTopology(ExplicitGraphTopology):
    """A strict sequential/branching pipeline enforcing a Directed Acyclic Graph."""

    topology_type: Literal["dag"] = "dag"

    @model_validator(mode="after")
    def validate_dag_structure(self) -> "DAGTopology":
        """Utilizes Kahn's Algorithm for strict cycle detection."""
        valid_ids = set(self.nodes.keys())
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

        if processed_nodes != len(valid_ids):
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.VAL_TOPOLOGY_CYCLE,
                message="Execution graphs must be strict Directed Acyclic Graphs (DAGs). Cycle detected.",
            )

        return self


class DCGTopology(ExplicitGraphTopology):
    """A Directed Cyclic Graph for ReAct loops and reflection, explicitly allowing cycles."""

    topology_type: Literal["dcg"] = "dcg"
    max_iterations: int = Field(default=10, description="Circuit breaker for maximum loop iterations.")


class MapReduceTopology(BaseTopology):
    """A scatter-gather topology for mapping operations across a dataset and reducing results."""

    topology_type: Literal["map_reduce"] = "map_reduce"
    nodes: dict[str, AnyNode]
    iterator_variable: str = Field(..., description="Blackboard variable to iterate over.")
    mapper_node_id: NodeID = Field(..., description="Node ID of the mapper agent.")
    reducer_node_id: NodeID = Field(..., description="Node ID of the reducer agent.")
    max_concurrency: int = Field(default=10, description="Maximum number of parallel mappers.")


class CouncilTopology(BaseTopology):
    """A Mixture-of-Agents (MoA) topology where parallel proposer agents feed into an aggregator."""

    topology_type: Literal["moa"] = "moa"
    nodes: dict[str, AnyNode]
    layers: list[list[NodeID]] = Field(
        ..., description="Nested list where each sub-list represents a layer of parallel proposer agents."
    )
    aggregator_agent: NodeID = Field(..., description="Agent synthesizing the proposals.")
    diversity_maximization: bool = Field(
        default=True, description="If True, the orchestrator auto-injects divergent personas into parallel proposers."
    )


class SwarmTopology(BaseTopology):
    """A swarm topology allowing emergent agentic handoffs without static edges."""

    topology_type: Literal["swarm"] = "swarm"
    nodes: dict[str, AnyNode]
    entry_point: NodeID = Field(..., description="Starting node ID for the swarm.")
    swarm_type: Literal["mesh", "star", "ring"] = Field(
        default="mesh", description="The structural archetype of the dynamic handoff boundaries."
    )
    allowed_handoffs: dict[NodeID, list[NodeID]] = Field(
        ..., description="Access control matrix defining valid handoff paths."
    )
    max_turns: int = Field(default=20, description="Circuit breaker for maximum agentic handoffs.")


class EventDrivenTopology(BaseTopology):
    """An event-driven topology reactive to Pub-Sub or Blackboard variable changes."""

    topology_type: Literal["event_driven"] = "event_driven"
    nodes: dict[str, AnyNode]
    trigger_schemas: dict[NodeID, list[str]] = Field(
        ..., description="Mapping of agents to Blackboard variables that trigger them."
    )


class HierarchicalTopology(BaseTopology):
    """A Supervisor-Worker topology supporting infinitely nested sub-graphs."""

    topology_type: Literal["hierarchical"] = "hierarchical"
    nodes: dict[str, AnyNode]
    entry_point: NodeID = Field(..., description="The Supervisor Node ID.")
    sub_flows: dict[NodeID, "WorkflowEnvelope"] = Field(
        default_factory=dict, description="Maps a worker node ID to an entirely nested WorkflowEnvelope."
    )


AnyTopology = Annotated[
    DAGTopology
    | DCGTopology
    | MapReduceTopology
    | CouncilTopology
    | SwarmTopology
    | EventDrivenTopology
    | HierarchicalTopology,
    Field(discriminator="topology_type"),
]


class WorkflowEnvelope(CoreasonModel):
    """
    SOTA Multi-Agent Orchestration Engine Envelope.
    Decouples State, Governance, and Telemetry from the Routing Topology.
    """

    type: Literal["workflow"] = "workflow"
    status: Literal["draft", "published", "archived"] = "draft"

    # 2026 SOTA Envelope Execution Primitives
    execution_mode: Literal["sync", "async", "streaming"] = Field(
        default="async", description="The runtime execution concurrency model."
    )
    human_in_the_loop: bool = Field(
        default=False, description="If True, the orchestrator enforces HITL pause/resume checkpoints."
    )

    mcp_export: MCPServerExport | None = Field(
        default=None, description="Configuration to host this workflow as an MCP Server."
    )
    mcp_clients: list[MCPServerConfig] = Field(
        default_factory=list, description="External MCP Servers this workflow connects to, registered top-down."
    )

    # Shared State & Governance
    metadata: FlowMetadata
    interface: FlowInterface
    pre_flight_constraints: list[Constraint] = Field(
        default_factory=list, description="Feasibility gates evaluated before the workflow is allocated compute."
    )
    governance: Governance | None = None
    blackboard: Blackboard | None = Field(default_factory=Blackboard, description="The Shared State Object.")
    definitions: FlowDefinitions | None = None
    evals: EvalsManifest | None = Field(None, description="Embedded executable specifications and test scenarios.")

    # The plug-and-play polymorphic routing logic
    topology: AnyTopology

    @model_validator(mode="after")
    def validate_middleware_integrity(self) -> "WorkflowEnvelope":
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
    def enforce_aot_compilation(self) -> "WorkflowEnvelope":
        """Enforce that published flows have no unresolved semantic references.

        Raises:
            ManifestError: If unresolved references are found.
        """
        if self.status == "published":
            unresolved = [
                str(getattr(node, "id", ""))
                for node in self.topology.nodes.values()
                if getattr(node, "type", None) == "agent"
                and (
                    isinstance(getattr(node, "profile", None), SemanticRef)
                    or isinstance(getattr(node, "tools", None), SemanticRef)
                )
            ]
            if unresolved:
                msg = (
                    f"Lifecycle Violation: Cannot publish workflow. Nodes [{','.join(unresolved)}] "
                    "contain unresolved SemanticRefs. A Weaver must compile this workflow into "
                    "concrete profiles before publication."
                )
                raise ManifestError.critical_halt(code=ManifestErrorCode.VAL_LIFECYCLE_UNRESOLVED, message=msg)
        return self

    @model_validator(mode="after")
    def enforce_lifecycle_constraints(self) -> "WorkflowEnvelope":
        """Enforce that published flows have valid metadata, entry point, and no placeholders."""
        if self.status != "published":
            return self
        if getattr(self.metadata, "provenance", None) is None:
            raise ValueError(
                "Lifecycle Violation: Cannot publish flow without a signed ProvenanceData block. "
                "The Weaver must declare its lineage."
            )
        for node in self.topology.nodes.values():
            if node.type == "placeholder":
                raise ValueError("Cannot publish a flow with placeholder nodes")

        if (
            self.topology.topology_type in ["dag", "dcg", "swarm", "hierarchical"]
            and getattr(self.topology, "entry_point", None) is None
        ):
            raise ValueError(f"Cannot publish a {self.topology.topology_type} WorkflowEnvelope without an entry point")

        return self
