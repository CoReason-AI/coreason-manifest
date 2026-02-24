# src/coreason_manifest/utils/validator.py

import re

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
from coreason_manifest.spec.core.tools import ToolPack
from coreason_manifest.utils.topology import get_strongly_connected_components


def validate_flow(flow: LinearFlow | GraphFlow) -> list[str]:
    """
    Semantically validate a Flow (Linear or Graph).
    Returns a list of error strings. Empty list implies validity.
    """
    errors: list[str] = []

    # Flatten nodes based on flow type
    nodes: list[AnyNode] = []
    if isinstance(flow, GraphFlow):
        nodes = list(flow.graph.nodes.values())
    elif isinstance(flow, LinearFlow):
        nodes = flow.steps

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
        errors.extend(_validate_supervision(node, valid_ids))

    # 2. LinearFlow Specific Checks
    if isinstance(flow, LinearFlow):
        errors.extend(_validate_linear_integrity(flow))
        node_ids = {n.id for n in flow.steps}
        errors.extend(_validate_unique_ids(flow.steps))
        errors.extend(_validate_switch_logic(flow.steps, node_ids))

    # 3. GraphFlow Specific Checks
    if isinstance(flow, GraphFlow):
        if not flow.graph.nodes:
            errors.append("GraphFlow Error: Graph must contain at least one node.")

        errors.extend(_validate_graph_integrity(flow.graph))

        # Helper for extracting nodes for generic logic checks
        nodes_list = list(flow.graph.nodes.values())
        node_ids = set(flow.graph.nodes.keys())

        errors.extend(_validate_unique_ids(nodes_list))
        errors.extend(_validate_switch_logic(nodes_list, node_ids))
        errors.extend(_validate_orphan_nodes(flow.graph))

    # Global Unified Cycle Detection
    errors.extend(_validate_topology_cycles(flow))

    # 4. Domain 4: Static Data-Flow Analysis
    # Construct Symbol Table: Map variable name -> type (str)
    symbol_table: dict[str, str] = {}
    if hasattr(flow, "blackboard") and flow.blackboard:
        for name, var_def in flow.blackboard.variables.items():
            # Architectural Note: Normalize to lowercase to handle "List", "ARRAY", etc.
            symbol_table[name] = var_def.type.lower()
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
) -> list[str]:
    """
    Check if nodes reference variables that exist in the symbol table.
    Also validates type compatibility for specific node types.
    """
    errors: list[str] = []
    available_vars = set(symbol_table.keys())

    for node in nodes:
        if isinstance(node, SwarmNode):
            if node.workload_variable not in available_vars:
                errors.append(
                    f"Data Flow Error: SwarmNode '{node.id}' references missing variable '{node.workload_variable}'."
                )
            # MVP Type Safety: SwarmNode expects a list/array for workload
            elif node.workload_variable in symbol_table:
                var_type = symbol_table[node.workload_variable]
                # Check if 'array' is ANY of the permitted types
                if "array" not in var_type and "list" not in var_type and "unknown" not in var_type:
                    errors.append(
                        f"Type Mismatch: SwarmNode '{node.id}' expects a list for '{node.workload_variable}', "
                        f"but found type '{var_type}'."
                    )

            if node.output_variable not in available_vars:
                errors.append(
                    f"Data Flow Error: SwarmNode '{node.id}' writes to missing variable '{node.output_variable}'."
                )

        elif isinstance(node, SwitchNode):
            if node.variable not in available_vars:
                errors.append(f"Data Flow Error: SwitchNode '{node.id}' evaluates missing variable '{node.variable}'.")

        elif isinstance(node, (InspectorNode, EmergenceInspectorNode)):
            if node.to_node_variable not in available_vars:
                errors.append(
                    f"Data Flow Error: InspectorNode '{node.id}' inspects missing variable '{node.to_node_variable}'."
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
                    f"Type Warning: InspectorNode '{node.id}' uses regex mode on complex type '{var_type}' "
                    f"variable '{node.to_node_variable}'. Matching may fail."
                )

            if node.output_variable not in available_vars:
                errors.append(
                    f"Data Flow Error: InspectorNode '{node.id}' writes to missing variable '{node.output_variable}'."
                )

        elif isinstance(node, AgentNode):
            # Scan for prompt template variables
            refs = _scan_agent_templates(node, definitions)
            errors.extend(
                f"Data Flow Error: AgentNode '{node.id}' references missing variable '{var}' in templates."
                for var in refs
                if var not in available_vars
            )

    return errors


def _validate_governance(gov: Governance, valid_ids: set[str]) -> list[str]:
    errors: list[str] = []
    if gov.rate_limit_rpm is not None and gov.rate_limit_rpm < 0:
        errors.append("Governance Error: rate_limit_rpm cannot be negative.")
    if gov.cost_limit_usd is not None and gov.cost_limit_usd < 0:
        errors.append("Governance Error: cost_limit_usd cannot be negative.")
    if (
        gov.circuit_breaker
        and gov.circuit_breaker.fallback_node_id
        and gov.circuit_breaker.fallback_node_id not in valid_ids
    ):
        errors.append(
            f"Circuit Breaker Error: 'fallback_node_id' points to missing ID '{gov.circuit_breaker.fallback_node_id}'."
        )
    return errors


def _validate_tools(nodes: list[AnyNode], packs: list[ToolPack]) -> list[str]:
    errors: list[str] = []
    available_tools = {t.name for pack in packs for t in pack.tools}

    for node in nodes:
        if isinstance(node, AgentNode):
            errors.extend(
                f"Missing Tool Warning: Agent '{node.id}' requires tool '{tool}' "
                "but it is not provided by any attached ToolPack."
                for tool in node.tools
                if tool not in available_tools
            )
    return errors


def _validate_linear_integrity(flow: LinearFlow) -> list[str]:
    if not flow.steps:
        return ["LinearFlow Error: Sequence cannot be empty."]
    return []


def _validate_unique_ids(nodes: list[AnyNode]) -> list[str]:
    seen = set()
    errors: list[str] = []
    for node in nodes:
        if node.id in seen:
            errors.append(f"ID Collision Error: Duplicate Node ID '{node.id}' found.")
        seen.add(node.id)
    return errors


def _validate_graph_integrity(graph: Graph) -> list[str]:
    errors: list[str] = []
    valid_ids = set(graph.nodes.keys())

    # Check 1: Key/ID Integrity
    for key, node in graph.nodes.items():
        if key != node.id:
            errors.append(f"Graph Integrity Error: Node key '{key}' does not match Node ID '{node.id}'.")

    # Check 2: Edge Validity
    for edge in graph.edges:
        if edge.from_node not in valid_ids:
            errors.append(f"Dangling Edge Error: Source '{edge.from_node}' not found in graph nodes.")
        if edge.to_node not in valid_ids:
            errors.append(f"Dangling Edge Error: Target '{edge.to_node}' not found in graph nodes.")

    return errors


def _validate_switch_logic(nodes: list[AnyNode], valid_ids: set[str]) -> list[str]:
    errors: list[str] = []
    for node in nodes:
        if isinstance(node, SwitchNode):
            # Check Cases
            for condition, target_id in node.cases.items():
                if target_id not in valid_ids:
                    errors.append(
                        f"Broken Switch Error: Node '{node.id}' case '{condition}' points to missing ID '{target_id}'."
                    )
            # Check Default
            if node.default not in valid_ids:
                errors.append(
                    f"Broken Switch Error: Node '{node.id}' default route points to missing ID '{node.default}'."
                )
    return errors


def _validate_orphan_nodes(graph: Graph) -> list[str]:
    if not graph.nodes:
        return []

    # All nodes physically present in the dict
    all_ids = set(graph.nodes.keys())

    # Architectural Note: Use explicit entry point
    entry_point = graph.entry_point

    targeted_ids = {edge.to_node for edge in graph.edges}

    orphans = all_ids - targeted_ids

    # Remove entry point from orphans if present (it's expected to have no incoming edges)
    if entry_point in orphans:
        orphans.remove(entry_point)

    return [f"Orphan Node Warning: Node '{oid}' has no incoming edges." for oid in orphans]


def _validate_referential_integrity(nodes: list[AnyNode], definitions: FlowDefinitions | None) -> list[str]:
    """
    Validates string references (e.g. resilience templates, profiles).
    """
    errors: list[str] = []

    # Check supervision templates
    templates = definitions.supervision_templates if definitions and definitions.supervision_templates else {}
    profile_ids = set(definitions.profiles.keys()) if definitions and definitions.profiles else set()

    for node in nodes:
        # Check resilience references
        if isinstance(node.resilience, str):
            ref = node.resilience
            if not ref.startswith("ref:"):
                errors.append(
                    f"Resilience Error: Node '{node.id}' has invalid resilience reference '{ref}'. "
                    "Must start with 'ref:'."
                )
            else:
                tmpl_id = ref.removeprefix("ref:")
                if tmpl_id not in templates:
                    errors.append(
                        f"Resilience Error: Node '{node.id}' references undefined supervision template ID '{tmpl_id}'."
                    )

        # Check profile references (AgentNode)
        if isinstance(node, AgentNode) and isinstance(node.profile, str) and node.profile not in profile_ids:
            errors.append(f"Integrity Error: AgentNode '{node.id}' references undefined profile ID '{node.profile}'.")

        # Check worker profile references (SwarmNode)
        if isinstance(node, SwarmNode) and node.worker_profile not in profile_ids:
            errors.append(
                f"Integrity Error: SwarmNode '{node.id}' references undefined worker profile ID "
                f"'{node.worker_profile}'."
            )

    return errors


def _validate_supervision(node: AnyNode, valid_ids: set[str]) -> list[str]:
    errors: list[str] = []

    # Check unified resilience field on any node type
    policy = node.resilience
    if not policy:
        return errors

    # If policy is a string reference, validation happens in validate_referential_integrity.
    if isinstance(policy, str):
        return errors

    # Collect strategies
    strategies: list[ResilienceStrategy] = []

    # If it's a SupervisionPolicy (complex)
    if hasattr(policy, "handlers"):
        strategies.extend([h.strategy for h in policy.handlers])
        if hasattr(policy, "default_strategy") and policy.default_strategy:
            strategies.append(policy.default_strategy)
    # If it's a simple RecoveryStrategy (ResilienceConfig which is a Union)
    else:
        # It's a single strategy
        strategies.append(policy)

    for strategy in strategies:
        if isinstance(strategy, ReflexionStrategy) and node.type not in (
            "agent",
            "inspector",
            "emergence_inspector",
            "swarm",
            "planner",
        ):
            errors.append(
                f"Resilience Error: Node '{node.id}' uses ReflexionStrategy but is of type '{node.type}'. "
                "Only Agent/Inspector/Swarm/Planner nodes support reflexion."
            )

        if isinstance(strategy, FallbackStrategy) and strategy.fallback_node_id not in valid_ids:
            errors.append(
                f"Resilience Error: Node '{node.id}' fallback points to missing ID '{strategy.fallback_node_id}'."
            )

        if isinstance(strategy, EscalationStrategy) and not strategy.queue_name:
            errors.append(f"Resilience Error: Node '{node.id}' uses EscalationStrategy with empty queue_name.")

    return errors


def _build_unified_adjacency_map(flow: LinearFlow | GraphFlow) -> dict[str, list[str]]:
    """
    Constructs a unified adjacency map for cycle detection.
    Includes sequential/graph edges, implicit SwitchNode routing, fallback routing, and global circuit breaker.
    """
    # 1. Initialize Map
    nodes = flow.steps if isinstance(flow, LinearFlow) else list(flow.graph.nodes.values())
    adj: dict[str, list[str]] = {node.id: [] for node in nodes}

    # 2. Add Flow Structure Edges
    if isinstance(flow, LinearFlow):
        # Sequential edges: step i -> step i+1
        for i in range(len(flow.steps) - 1):
            curr_id = flow.steps[i].id
            next_id = flow.steps[i + 1].id
            if curr_id in adj and next_id in adj:
                adj[curr_id].append(next_id)
    elif isinstance(flow, GraphFlow):
        # Graph edges
        for edge in flow.graph.edges:
            if edge.from_node in adj and edge.to_node in adj:
                adj[edge.from_node].append(edge.to_node)

    # 3. Add Global Governance Edges (Circuit Breaker)
    global_fallback_id = None
    if flow.governance and flow.governance.circuit_breaker and flow.governance.circuit_breaker.fallback_node_id:
        global_fallback_id = flow.governance.circuit_breaker.fallback_node_id

    # 4. Add Node-Level Implicit Edges
    for node in nodes:
        # Global fallback applies to ALL nodes (any node can fail)
        if global_fallback_id and global_fallback_id in adj:
            adj[node.id].append(global_fallback_id)

        # SwitchNode routing
        if isinstance(node, SwitchNode):
            for target_id in node.cases.values():
                if target_id in adj:
                    adj[node.id].append(target_id)
            if node.default in adj:
                adj[node.id].append(node.default)

        # Local Fallback routing
        if node.resilience and not isinstance(node.resilience, str):
            policy = node.resilience
            strategies: list[ResilienceStrategy] = []

            # Expand policy if complex
            if hasattr(policy, "handlers"):
                strategies.extend([h.strategy for h in policy.handlers])
                if hasattr(policy, "default_strategy") and policy.default_strategy:
                    strategies.append(policy.default_strategy)
            else:
                strategies.append(policy)

            for strategy in strategies:
                if isinstance(strategy, FallbackStrategy) and strategy.fallback_node_id in adj:
                    adj[node.id].append(strategy.fallback_node_id)

    return adj


def _validate_topology_cycles(flow: LinearFlow | GraphFlow) -> list[str]:
    """
    Enforces Strict DAG Topology on the unified execution graph.
    Uses Tarjan's algorithm to detect unified cycles.
    """
    errors: list[str] = []

    adj = _build_unified_adjacency_map(flow)
    sccs = get_strongly_connected_components(adj)

    for scc in sccs:
        # A cycle exists if:
        # 1. SCC has more than 1 node (A -> B -> A)
        # 2. SCC has exactly 1 node AND it has a self-loop (A -> A)
        is_cycle = False
        if len(scc) > 1:
            is_cycle = True
        elif len(scc) == 1:
            node_id = scc[0]
            if node_id in adj and node_id in adj[node_id]:
                is_cycle = True

        if is_cycle:
            cycle_nodes = ", ".join(sorted(scc))
            msg = (
                "Topology Integrity Error: Unified execution/fallback cycle detected involving nodes: "
                f"[{cycle_nodes}]. Execution graphs must be strict Directed Acyclic Graphs (DAGs)."
            )
            errors.append(msg)

    return errors
