# src/coreason_manifest/utils/validator.py

import re
from typing import Any

from pydantic import BaseModel

from coreason_manifest.spec.core.flow import (
    AnyNode,
    FlowDefinitions,
    Graph,
    GraphFlow,
    LinearFlow,
)
from coreason_manifest.spec.core.governance import Governance
from coreason_manifest.spec.core.nodes import (
    AgentNode,
    CognitiveProfile,
    EmergenceInspectorNode,
    InspectorNode,
    SwarmNode,
    SwitchNode,
)
from coreason_manifest.spec.core.resilience import (
    EscalationStrategy,
    FallbackStrategy,
    ReflexionStrategy,
    ResilienceStrategy,
)
from coreason_manifest.spec.core.tools import ToolCapability, ToolPack
from coreason_manifest.spec.core.types import RiskLevel
from coreason_manifest.spec.interop.compliance import ComplianceReport, ErrorCatalog, RemediationAction
from coreason_manifest.spec.interop.exceptions import ManifestError, ManifestErrorCode
from coreason_manifest.utils.topology import get_strongly_connected_components, get_unified_topology


def validate_flow(flow: LinearFlow | GraphFlow) -> list[ComplianceReport]:
    """
    Semantically validate a Flow (Linear or Graph).
    Returns a list of structured ComplianceReport objects. Empty list implies validity.
    """
    errors: list[ComplianceReport] = []

    # Flatten nodes based on flow type
    nodes, _ = get_unified_topology(flow)

    valid_ids = {n.id for n in nodes}

    # 1. Common Checks
    if flow.governance:
        errors.extend(_validate_governance(flow.governance, valid_ids))

    if flow.definitions:
        # Convert dict to list for backward compatibility with _validate_tools
        tool_packs = list(flow.definitions.tool_packs.values()) if flow.definitions.tool_packs else []
        errors.extend(_validate_tools(nodes, tool_packs))
        errors.extend(_validate_referential_integrity(nodes, flow.definitions))
    else:
        # If no definitions, ensure no references exist
        errors.extend(_validate_referential_integrity(nodes, None))

    for node in nodes:
        errors.extend(_validate_supervision(node, valid_ids, flow.definitions))

    # 2. LinearFlow Specific Checks
    if isinstance(flow, LinearFlow):
        errors.extend(_validate_linear_integrity(flow))
        node_ids = {n.id for n in flow.steps}
        errors.extend(_validate_unique_ids(flow.steps))
        errors.extend(_validate_switch_logic(flow.steps, node_ids))

    # 3. GraphFlow Specific Checks
    if isinstance(flow, GraphFlow):
        if not flow.graph.nodes:
            errors.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_TOPOLOGY_EMPTY_GRAPH,
                    severity="violation",
                    message="GraphFlow Error: Graph must contain at least one node.",
                )
            )

        # Entry Point Existence
        if flow.graph.entry_point and flow.graph.entry_point not in valid_ids:
            errors.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_TOPOLOGY_MISSING_ENTRY,
                    severity="violation",
                    message=f"GraphFlow Error: Entry point '{flow.graph.entry_point}' not found in nodes.",
                    details={"entry_point": flow.graph.entry_point},
                )
            )

        errors.extend(_validate_graph_integrity(flow.graph))

        # Helper for extracting nodes for generic logic checks
        nodes_list = list(flow.graph.nodes.values())
        node_ids = set(flow.graph.nodes.keys())

        errors.extend(_validate_unique_ids(nodes_list))
        errors.extend(_validate_switch_logic(nodes_list, node_ids))
        errors.extend(_validate_orphan_nodes(flow))

    # Global Unified Cycle Detection
    errors.extend(_validate_topology_cycles(flow))

    # 4. Domain 4: Static Data-Flow Analysis
    # Construct Symbol Table: Map variable name -> type (str)
    symbol_table: dict[str, str] = {}
    if hasattr(flow, "blackboard") and flow.blackboard:
        for name, var_def in flow.blackboard.variables.items():
            # Architectural Note: Normalize to lowercase to handle "List", "ARRAY", etc.
            if hasattr(var_def, "type"):
                symbol_table[name] = var_def.type.lower()
            else:
                symbol_table[name] = "unknown"
    if hasattr(flow, "interface") and flow.interface:
        inputs = flow.interface.inputs
        in_schema = getattr(inputs, "json_schema", inputs)
        if isinstance(in_schema, dict):
            # Extract properties from input schema
            # Heuristic: extract property type if simple, else "unknown"
            props = in_schema.get("properties", {})
            for name, schema in props.items():
                raw_type = schema.get("type", "unknown")
                if isinstance(raw_type, list):
                    # Sort to ensure deterministic symbol table regardless of input order
                    # Result: "array|string"
                    types = sorted([x for x in raw_type if x != "null"])
                    if types:
                        symbol_table[name] = "|".join(types)
                    else:
                        symbol_table[name] = "union"
                else:
                    symbol_table[name] = str(raw_type)

        errors.extend(_validate_data_flow(nodes, symbol_table, flow.definitions))

    # 5. Security & Kill Switch
    if flow.governance and flow.governance.max_risk_level:
        errors.extend(_validate_kill_switch(flow))

    # 6. Middleware References
    errors.extend(_validate_middleware_refs(flow))

    return errors


def _scan_string_for_vars(text: str) -> set[str]:
    """
    Scan a string for Jinja2-style variable references: {{ var_name }}
    Handles filters like {{ var | lower }} by stripping them.
    """
    return set(re.findall(r"\{\{\s*([a-zA-Z_][\w\.]*)(?:\s*\|.*?)?\s*\}\}", text))


def _scan_agent_templates(node: AgentNode, definitions: FlowDefinitions | None) -> set[str]:
    """
    Extract variable references from AgentNode fields.
    Scans:
    - Inline profile role/persona
    - Referenced profiles (from definitions)
    - Metadata values (if strings)
    """
    refs = set()

    # Scan profile
    if isinstance(node.profile, CognitiveProfile):
        # Inline profile
        refs.update(_scan_string_for_vars(node.profile.role))
        refs.update(_scan_string_for_vars(node.profile.persona))
    elif isinstance(node.profile, str):
        # Referenced profile
        if definitions and node.profile in definitions.profiles:
            profile_def = definitions.profiles[node.profile]
            if isinstance(profile_def, CognitiveProfile):
                refs.update(_scan_string_for_vars(profile_def.role))
                refs.update(_scan_string_for_vars(profile_def.persona))

    # Scan metadata values
    for val in node.metadata.values():
        if isinstance(val, str):
            refs.update(_scan_string_for_vars(val))

    return refs


def _validate_data_flow(
    nodes: list[AnyNode],
    symbol_table: dict[str, str],
    definitions: FlowDefinitions | None,
) -> list[ComplianceReport]:
    """
    Check if nodes reference variables that exist in the symbol table.
    Also validates type compatibility for specific node types.
    """
    errors: list[ComplianceReport] = []
    available_vars = set(symbol_table.keys())

    for node in nodes:
        if isinstance(node, SwarmNode):
            if node.workload_variable not in available_vars:
                errors.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_CAP_MISSING_VAR,
                        severity="violation",
                        message=f"Data Flow Error: SwarmNode '{node.id}' references missing variable "
                        f"'{node.workload_variable}'.",
                        node_id=node.id,
                        details={"variable": node.workload_variable},
                        remediation=RemediationAction(
                            type="update_field",
                            description=f"Add variable '{node.workload_variable}' to blackboard.",
                            patch_data=[
                                {
                                    "op": "add",
                                    "path": f"/blackboard/variables/{node.workload_variable}",
                                    "value": [],
                                }
                            ],
                        ),
                    )
                )
            # MVP Type Safety: SwarmNode expects a list/array for workload
            elif node.workload_variable in symbol_table:
                var_type = symbol_table[node.workload_variable]
                # Check if 'array' is ANY of the permitted types
                if "array" not in var_type and "list" not in var_type and "unknown" not in var_type:
                    errors.append(
                        ComplianceReport(
                            code=ErrorCatalog.ERR_CAP_TYPE_MISMATCH,
                            severity="violation",
                            message=f"Type Mismatch: SwarmNode '{node.id}' expects a list for "
                            f"'{node.workload_variable}', but found type '{var_type}'.",
                            node_id=node.id,
                            details={"variable": node.workload_variable, "found_type": var_type},
                        )
                    )

            if node.output_variable not in available_vars:
                errors.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_CAP_MISSING_VAR,
                        severity="violation",
                        message=f"Data Flow Error: SwarmNode '{node.id}' writes to missing variable "
                        f"'{node.output_variable}'.",
                        node_id=node.id,
                        details={"variable": node.output_variable},
                    )
                )

        elif isinstance(node, SwitchNode):
            if node.variable not in available_vars:
                errors.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_CAP_MISSING_VAR,
                        severity="violation",
                        message=f"Data Flow Error: SwitchNode '{node.id}' evaluates missing variable "
                        f"'{node.variable}'.",
                        node_id=node.id,
                        details={"variable": node.variable},
                    )
                )

        elif isinstance(node, (InspectorNode, EmergenceInspectorNode)):
            if node.to_node_variable not in available_vars:
                errors.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_CAP_MISSING_VAR,
                        severity="violation",
                        message=f"Data Flow Error: InspectorNode '{node.id}' inspects missing variable "
                        f"'{node.to_node_variable}'.",
                        node_id=node.id,
                        details={"variable": node.to_node_variable},
                    )
                )
            # MVP Type Safety: Regex matching on complex objects is risky
            elif (
                node.to_node_variable in symbol_table
                and hasattr(node, "mode")
                and node.mode == "programmatic"
                and symbol_table[node.to_node_variable] in ("object", "array")
            ):
                var_type = symbol_table[node.to_node_variable]
                # Just a warning for now
                errors.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_CAP_TYPE_MISMATCH,
                        severity="warning",
                        message=f"Type Warning: InspectorNode '{node.id}' uses regex mode on complex type '{var_type}' "
                        f"variable '{node.to_node_variable}'. Matching may fail.",
                        node_id=node.id,
                        details={"variable": node.to_node_variable, "found_type": var_type},
                    )
                )

            if node.output_variable not in available_vars:
                errors.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_CAP_MISSING_VAR,
                        severity="violation",
                        message=f"Data Flow Error: InspectorNode '{node.id}' writes to missing variable "
                        f"'{node.output_variable}'.",
                        node_id=node.id,
                        details={"variable": node.output_variable},
                    )
                )

        elif isinstance(node, AgentNode):
            # Scan for prompt template variables
            refs = _scan_agent_templates(node, definitions)
            errors.extend(
                ComplianceReport(
                    code=ErrorCatalog.ERR_CAP_MISSING_VAR,
                    severity="violation",
                    message=f"Data Flow Error: AgentNode '{node.id}' references missing variable '{var}' in templates.",
                    node_id=node.id,
                    details={"variable": var},
                )
                for var in refs
                if var not in available_vars
            )

    return errors


def _validate_governance(gov: Governance, valid_ids: set[str]) -> list[ComplianceReport]:
    errors: list[ComplianceReport] = []

    # Check Operational Policy
    if gov.operational_policy:
        if gov.operational_policy.financial:
            fin = gov.operational_policy.financial
            if fin.max_cost_usd is not None and fin.max_cost_usd < 0:
                 errors.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_GOV_INVALID_CONFIG,
                        severity="violation",
                        message="Governance Error: max_cost_usd cannot be negative.",
                    )
                )

    if (
        gov.circuit_breaker
        and gov.circuit_breaker.fallback_node_id
        and gov.circuit_breaker.fallback_node_id not in valid_ids
    ):
        errors.append(
            ComplianceReport(
                code=ErrorCatalog.ERR_GOV_CIRCUIT_FALLBACK_MISSING,
                severity="violation",
                message=f"Circuit Breaker Error: 'fallback_node_id' points to missing ID "
                f"'{gov.circuit_breaker.fallback_node_id}'.",
                details={"fallback_node_id": gov.circuit_breaker.fallback_node_id},
            )
        )
    return errors


def _validate_tools(nodes: list[AnyNode], packs: list[ToolPack]) -> list[ComplianceReport]:
    errors: list[ComplianceReport] = []
    available_tools = {t.name for pack in packs for t in pack.tools}

    for node in nodes:
        if isinstance(node, AgentNode):
            errors.extend(
                ComplianceReport(
                    code=ErrorCatalog.ERR_CAP_MISSING_TOOL_001,
                    severity="warning",
                    message=f"Missing Tool Warning: Agent '{node.id}' requires tool '{tool}' but it is not provided by "
                    "any attached ToolPack.",
                    node_id=node.id,
                    details={"tool": tool},
                )
                for tool in node.tools
                if tool not in available_tools
            )
    return errors


def _validate_linear_integrity(flow: LinearFlow) -> list[ComplianceReport]:
    if not flow.steps:
        return [
            ComplianceReport(
                code=ErrorCatalog.ERR_TOPOLOGY_LINEAR_EMPTY,
                severity="violation",
                message="LinearFlow Error: Sequence cannot be empty.",
            )
        ]
    return []


def _validate_unique_ids(nodes: list[AnyNode]) -> list[ComplianceReport]:
    seen = set()
    errors: list[ComplianceReport] = []
    for node in nodes:
        if node.id in seen:
            errors.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_TOPOLOGY_NODE_ID_COLLISION,
                    severity="violation",
                    message=f"ID Collision Error: Duplicate Node ID '{node.id}' found.",
                    node_id=node.id,
                )
            )
        seen.add(node.id)
    return errors


def _validate_graph_integrity(graph: Graph) -> list[ComplianceReport]:
    errors: list[ComplianceReport] = []
    valid_ids = set(graph.nodes.keys())

    # Check 1: Key/ID Integrity
    for key, node in graph.nodes.items():
        if key != node.id:
            errors.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_TOPOLOGY_ID_MISMATCH,
                    severity="violation",
                    message=f"Graph Integrity Error: Node key '{key}' does not match Node ID '{node.id}'.",
                    node_id=node.id,
                    details={"key": key, "node_id": node.id},
                )
            )

    # Check 2: Edge Validity
    for edge in graph.edges:
        if edge.from_node not in valid_ids:
            errors.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_TOPOLOGY_DANGLING_EDGE,
                    severity="violation",
                    message=f"Dangling Edge Error: Source '{edge.from_node}' not found in graph nodes.",
                    details={"source": edge.from_node},
                )
            )
        if edge.to_node not in valid_ids:
            errors.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_TOPOLOGY_DANGLING_EDGE,
                    severity="violation",
                    message=f"Dangling Edge Error: Target '{edge.to_node}' not found in graph nodes.",
                    details={"target": edge.to_node},
                )
            )

    return errors


def _validate_switch_logic(nodes: list[AnyNode], valid_ids: set[str]) -> list[ComplianceReport]:
    errors: list[ComplianceReport] = []
    for node in nodes:
        if isinstance(node, SwitchNode):
            # Check Cases
            for condition, target_id in node.cases.items():
                if target_id not in valid_ids:
                    errors.append(
                        ComplianceReport(
                            code=ErrorCatalog.ERR_TOPOLOGY_BROKEN_SWITCH,
                            severity="violation",
                            message=f"Broken Switch Error: Node '{node.id}' case '{condition}' points to missing ID "
                            f"'{target_id}'.",
                            node_id=node.id,
                            details={"condition": condition, "target_id": target_id},
                        )
                    )
            # Check Default
            if node.default not in valid_ids:
                errors.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_TOPOLOGY_BROKEN_SWITCH,
                        severity="violation",
                        message=f"Broken Switch Error: Node '{node.id}' default route points to missing ID "
                        f"'{node.default}'.",
                        node_id=node.id,
                        details={"target_id": node.default},
                    )
                )
    return errors


def _validate_orphan_nodes(flow: GraphFlow) -> list[ComplianceReport]:
    """
    Validates that no reachable nodes are isolated from the rest of the graph.
    Uses unified adjacency map to check connectivity via edges, switches, or fallbacks.
    """
    if not flow.graph.nodes:
        return []

    all_ids = set(flow.graph.nodes.keys())
    entry_point = flow.graph.entry_point

    # Use our SOTA unified map to find ALL targets (explicit edges + switches + fallbacks)
    # Bypass deep validation to construct a temporary flow for unified mapping if needed,
    # though here we are already inside a valid flow context or partial flow.
    # Note: _build_unified_adjacency_map handles flow.graph access safely.
    adj_set = _build_unified_adjacency_map(flow)

    targeted_ids = set()
    for targets in adj_set.values():
        targeted_ids.update(targets)

    orphans = all_ids - targeted_ids

    # The entry point is expected to have no incoming edges
    if entry_point in orphans:
        orphans.remove(entry_point)

    return [
        ComplianceReport(
            code=ErrorCatalog.ERR_TOPOLOGY_ORPHAN_001,
            severity="warning",
            message=f"Orphan Node Warning: Node '{oid}' has no incoming edges or implicit routes.",
            node_id=oid,
        )
        for oid in orphans
    ]


def _validate_referential_integrity(
    nodes: list[AnyNode], definitions: FlowDefinitions | None
) -> list[ComplianceReport]:
    """
    Validates string references (e.g. resilience templates, profiles).
    """
    errors: list[ComplianceReport] = []

    # Check supervision templates
    templates = definitions.supervision_templates if definitions and definitions.supervision_templates else {}
    profile_ids = set(definitions.profiles.keys()) if definitions and definitions.profiles else set()

    for node in nodes:
        # Check resilience references
        if isinstance(node.resilience, str):
            ref = node.resilience
            if not ref.startswith("ref:"):
                errors.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_RESILIENCE_INVALID_REF,
                        severity="violation",
                        message=f"Resilience Error: Node '{node.id}' has invalid resilience reference '{ref}'. "
                        "Must start with 'ref:'.",
                        node_id=node.id,
                        details={"reference": ref},
                    )
                )
            else:
                tmpl_id = ref.removeprefix("ref:")
                if tmpl_id not in templates:
                    errors.append(
                        ComplianceReport(
                            code=ErrorCatalog.ERR_RESILIENCE_MISSING_TEMPLATE,
                            severity="violation",
                            message=f"Resilience Error: Node '{node.id}' references undefined supervision template ID "
                            f"'{tmpl_id}'.",
                            node_id=node.id,
                            details={"template_id": tmpl_id},
                        )
                    )

        # Check profile references (AgentNode)
        if isinstance(node, AgentNode) and isinstance(node.profile, str) and node.profile not in profile_ids:
            errors.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_CAP_UNDEFINED_PROFILE_002,
                    severity="violation",
                    message=f"Integrity Error: AgentNode '{node.id}' references undefined profile ID '{node.profile}'.",
                    node_id=node.id,
                    details={"profile_id": node.profile},
                )
            )

        # Check worker profile references (SwarmNode)
        if isinstance(node, SwarmNode) and node.worker_profile not in profile_ids:
            errors.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_CAP_UNDEFINED_PROFILE_002,
                    severity="violation",
                    message=f"Integrity Error: SwarmNode '{node.id}' references undefined worker profile ID "
                    f"'{node.worker_profile}'.",
                    node_id=node.id,
                    details={"profile_id": node.worker_profile},
                )
            )

    return errors


def _validate_supervision(
    node: AnyNode, valid_ids: set[str], definitions: FlowDefinitions | None
) -> list[ComplianceReport]:
    errors: list[ComplianceReport] = []

    # Check unified resilience field on any node type
    policy = node.resilience
    if not policy:
        return errors

    resolved_policy = _resolve_resilience_policy(policy, definitions)
    if not resolved_policy:
        return errors

    # Collect strategies
    strategies = _extract_strategies(resolved_policy)

    for strategy in strategies:
        if isinstance(strategy, ReflexionStrategy) and node.type not in (
            "agent",
            "inspector",
            "emergence_inspector",
            "swarm",
            "planner",
        ):
            errors.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_RESILIENCE_MISMATCH,
                    severity="violation",
                    message=f"Resilience Error: Node '{node.id}' uses ReflexionStrategy but is of type '{node.type}'. "
                    "Only Agent/Inspector/Swarm/Planner nodes support reflexion.",
                    node_id=node.id,
                )
            )

        if isinstance(strategy, FallbackStrategy) and strategy.fallback_node_id not in valid_ids:
            errors.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_RESILIENCE_FALLBACK_MISSING,
                    severity="violation",
                    message=f"Resilience Error: Node '{node.id}' fallback points to missing ID "
                    f"'{strategy.fallback_node_id}'.",
                    node_id=node.id,
                    details={"fallback_node_id": strategy.fallback_node_id},
                )
            )

        if isinstance(strategy, EscalationStrategy) and not strategy.queue_name:
            errors.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_RESILIENCE_ESCALATION_INVALID,
                    severity="violation",
                    message=f"Resilience Error: Node '{node.id}' uses EscalationStrategy with empty queue_name.",
                    node_id=node.id,
                )
            )

    return errors


def _resolve_resilience_policy(policy: Any, definitions: FlowDefinitions | None) -> Any:
    """Resolves string reference policies from the definitions block."""
    if isinstance(policy, str):
        if policy.startswith("ref:") and definitions and definitions.supervision_templates:
            tmpl_id = policy.removeprefix("ref:")
            # Return the resolved template, or None if it's missing (missing refs are caught by referential_integrity)
            return definitions.supervision_templates.get(tmpl_id)
        return None
    return policy


def _extract_strategies(policy: Any) -> list[ResilienceStrategy]:
    """
    Helper to extract flat list of strategies from a unified resilience config.

    Args:
        policy: Can be ResilienceConfig (duck-typed with 'handlers'), a single Strategy,
               or SupervisionPolicy. We use Any here to avoid circular dependencies with
               complex Pydantic unions in the core spec.

    Returns:
        List of strategies extracted from the policy.
    """
    strategies: list[ResilienceStrategy] = []
    if hasattr(policy, "handlers"):
        strategies.extend([h.strategy for h in policy.handlers])
        if hasattr(policy, "default_strategy") and policy.default_strategy:
            strategies.append(policy.default_strategy)
    else:
        strategies.append(policy)
    return strategies


def _build_unified_adjacency_map(flow: LinearFlow | GraphFlow) -> dict[str, set[str]]:
    """
    Constructs a unified adjacency map for cycle detection.
    Includes sequential/graph edges, implicit SwitchNode routing, fallback routing, and global circuit breaker.
    """
    # 1. Initialize Map with strict type inference for node iteration
    nodes, edges_objs = get_unified_topology(flow)
    adj: dict[str, set[str]] = {node.id: set() for node in nodes}

    # 2. Add Flow Structure Edges
    for edge in edges_objs:
        if edge.from_node in adj and edge.to_node in adj:
            adj[edge.from_node].add(edge.to_node)

    # 3. Add Global Governance Edges (Circuit Breaker)
    global_fallback_id: str | None = None
    if flow.governance and flow.governance.circuit_breaker and flow.governance.circuit_breaker.fallback_node_id:
        global_fallback_id = flow.governance.circuit_breaker.fallback_node_id

    # 4. Add Node-Level Implicit Edges
    for node in nodes:
        # Global fallback applies to ALL nodes EXCEPT the fallback node itself
        if global_fallback_id and global_fallback_id in adj and node.id != global_fallback_id:
            adj[node.id].add(global_fallback_id)

        # SwitchNode routing
        if isinstance(node, SwitchNode):
            for target_id in node.cases.values():
                if target_id in adj:
                    adj[node.id].add(target_id)
            if node.default in adj:
                adj[node.id].add(node.default)

        # Local Fallback routing (Resolving templates to catch Trojan cycles)
        if node.resilience:
            resolved_policy = _resolve_resilience_policy(node.resilience, getattr(flow, "definitions", None))
            if resolved_policy:
                strategies = _extract_strategies(resolved_policy)
                for strategy in strategies:
                    if isinstance(strategy, FallbackStrategy) and strategy.fallback_node_id in adj:
                        adj[node.id].add(strategy.fallback_node_id)

    return adj


def _validate_topology_cycles(flow: LinearFlow | GraphFlow) -> list[ComplianceReport]:
    """
    Enforces Strict DAG Topology on the unified execution graph.
    Uses Tarjan's algorithm to detect unified cycles.
    """
    errors: list[ComplianceReport] = []

    adj_set = _build_unified_adjacency_map(flow)
    # SOTA FIX: Sort the sets into lists to guarantee 100% deterministic DFS traversal
    adj_list = {k: sorted(adj_set[k]) for k in sorted(adj_set.keys())}

    sccs = get_strongly_connected_components(adj_list)

    for scc in sccs:
        # A cycle exists if:
        # 1. SCC has more than 1 node (A -> B -> A)
        # 2. SCC has exactly 1 node AND it has a self-loop (A -> A)
        is_cycle = False
        if len(scc) > 1:
            is_cycle = True
        elif len(scc) == 1:
            node_id = scc[0]
            if node_id in adj_set and node_id in adj_set[node_id]:
                is_cycle = True

        if is_cycle:
            cycle_nodes = ", ".join(sorted(scc))
            errors.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_TOPOLOGY_CYCLE_002,
                    severity="violation",
                    message=f"Topology Integrity Error: Unified execution/fallback cycle detected involving nodes: "
                    f"[{cycle_nodes}]. Execution graphs must be strict Directed Acyclic Graphs (DAGs).",
                    details={"cycle_nodes": scc},
                )
            )

    return errors


def _validate_kill_switch(flow: LinearFlow | GraphFlow) -> list[ComplianceReport]:
    errors: list[ComplianceReport] = []
    if not flow.governance:
        return errors

    max_risk = flow.governance.max_risk_level

    nodes, _ = get_unified_topology(flow)

    def _check(obj: Any) -> None:
        # 1. Check ToolCapability objects
        if isinstance(obj, ToolCapability) and max_risk is not None and obj.risk_level.weight > max_risk.weight:
            errors.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_SEC_KILL_SWITCH_VIOLATION,
                    severity="violation",
                    message=f"Security Violation: Tool '{obj.name}' has risk level '{obj.risk_level.value}' "
                    f"which exceeds the global max_risk_level '{max_risk.value}'.",
                    details={"tool_name": obj.name, "tool_risk": obj.risk_level.value, "max_risk": max_risk.value},
                )
            )

        # 2. Check Strings for Remote URIs
        if isinstance(obj, str):
            if "://" in obj and max_risk is not None and RiskLevel.CRITICAL.weight > max_risk.weight:
                errors.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_SEC_KILL_SWITCH_VIOLATION,
                        severity="violation",
                        message="Security Violation: Unresolved remote tool URIs default to CRITICAL risk and "
                        "violate the global max_risk_level.",
                        details={
                            "tool_uri": obj,
                            "assumed_risk": RiskLevel.CRITICAL.value,
                            "max_risk": max_risk.value,
                        },
                    )
                )
            return

        # 3. Recursion
        if isinstance(obj, dict):
            for v in obj.values():
                _check(v)
        elif isinstance(obj, (list, tuple, set)):
            for v in obj:
                _check(v)
        elif isinstance(obj, BaseModel):
            # Efficiently iterate model fields
            for name in type(obj).model_fields:
                value = getattr(obj, name)
                _check(value)

    if flow.definitions:
        _check(flow.definitions)

    _check(nodes)

    return errors


def _validate_middleware_refs(flow: LinearFlow | GraphFlow) -> list[ComplianceReport]:
    errors: list[ComplianceReport] = []
    if not flow.governance or not flow.governance.active_middlewares:
        return errors

    defined = set()
    if flow.definitions and flow.definitions.middlewares:
        defined = set(flow.definitions.middlewares.keys())

    for mw_id in flow.governance.active_middlewares:
        if mw_id not in defined:
            # SOTA RFC 6902 JSON Pointer Escaping
            mw_id_escaped = mw_id.replace("~", "~0").replace("/", "~1")

            # Construct patch
            patch: list[dict[str, Any]]
            if not flow.definitions:
                patch = [
                    {
                        "op": "add",
                        "path": "/definitions",
                        "value": {"middlewares": {mw_id: {"ref": "file.py:Class"}}},
                    }
                ]
            elif not flow.definitions.middlewares:
                patch = [{"op": "add", "path": "/definitions/middlewares", "value": {mw_id: {"ref": "file.py:Class"}}}]
            else:
                patch = [
                    {
                        "op": "add",
                        "path": f"/definitions/middlewares/{mw_id_escaped}",
                        "value": {"ref": "file.py:Class"},
                    }
                ]

            errors.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_CAP_MISSING_MIDDLEWARE,
                    severity="violation",
                    message=f"Middleware Error: Active middleware '{mw_id}' is not defined.",
                    details={"middleware_id": mw_id},
                    remediation=RemediationAction(
                        type="update_field",
                        description=f"Add definition for middleware '{mw_id}'.",
                        patch_data=patch,
                    ),
                )
            )

    return errors


def validate_integrity(definitions: FlowDefinitions, nodes: list[AnyNode]) -> None:
    """
    Legacy helper for tests.
    Validates integrity of nodes against definitions.
    Strictly raises ManifestError to maintain backward compatibility with tests.
    """
    profile_ids = set(definitions.profiles.keys())
    for node in nodes:
        if isinstance(node, SwarmNode) and node.worker_profile not in profile_ids:
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.CRSN_VAL_INTEGRITY_PROFILE_MISSING,
                message=f"SwarmNode '{node.id}' references missing profile '{node.worker_profile}'.",
                context={},
            )
