# src/coreason_manifest/utils/gatekeeper.py
from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from coreason_manifest.core.common.exceptions import ManifestError
from coreason_manifest.core.common.presentation import RenderStrategy
from coreason_manifest.core.oversight.resilience import EscalationStrategy
from coreason_manifest.core.primitives.constants import NodeCapability
from coreason_manifest.core.security.compliance import (
    ComplianceReport,
    ErrorCatalog,
    RemediationAction,
)
from coreason_manifest.core.workflow.flow import GraphFlow, LinearFlow
from coreason_manifest.core.workflow.nodes import AgentNode, AnyNode, HumanNode, SwarmNode
from coreason_manifest.core.workflow.topology import (
    get_reachable_nodes,
    get_strongly_connected_components,
    get_unified_topology,
)


def canonicalize_domain(domain: str) -> str:
    return domain.lower().strip()


if TYPE_CHECKING:
    from coreason_manifest.core.state.tools import AnyTool


def _get_capabilities(node: AnyNode, flow: LinearFlow | GraphFlow) -> list[str]:
    """Helper to resolve profile and get capabilities."""
    reasoning = None
    if isinstance(node, AgentNode):
        # Resolve profile
        if isinstance(node.profile, str):
            if flow.definitions and node.profile in flow.definitions.profiles:
                profile = flow.definitions.profiles[node.profile]
                reasoning = profile.reasoning
        elif hasattr(node.profile, "reasoning"):
            reasoning = node.profile.reasoning

    elif isinstance(node, SwarmNode) and flow.definitions and node.worker_profile in flow.definitions.profiles:
        # Resolve worker profile
        profile = flow.definitions.profiles[node.worker_profile]
        reasoning = profile.reasoning

    if reasoning and hasattr(reasoning, "required_capabilities"):
        return cast("list[str]", reasoning.required_capabilities())
    return []


def _check_domain_whitelist(flow: LinearFlow | GraphFlow, tool_map: dict[str, AnyTool]) -> list[ComplianceReport]:
    """0. Domain Policy Check (Pillar 3: High-Fidelity URI Governance)"""
    reports: list[ComplianceReport] = []
    allowed_domains_raw = []
    if flow.governance and flow.governance.allowed_domains:
        allowed_domains_raw = flow.governance.allowed_domains

    # Canonicalize allowed domains
    allowed_domains = {canonicalize_domain(d) for d in allowed_domains_raw}

    if allowed_domains:
        for tool_obj in tool_map.values():
            # Architectural Note: Utilize strict Pydantic HttpUrl object instead of manual string parsing
            if tool_obj.url and tool_obj.url.host:
                domain_raw = str(tool_obj.url.host)
                domain = canonicalize_domain(domain_raw)

                allowed = False
                for allowed_d in allowed_domains:
                    # Exact match or subdomain
                    if domain == allowed_d or (domain and domain.endswith("." + allowed_d)):
                        allowed = True
                        break

                if allowed:
                    continue

                reports.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_SEC_DOMAIN_BLOCKED_002,
                        severity="violation",
                        message=f"Tool '{tool_obj.name}' uses blocked domain: {domain}",
                        details={"domain": domain, "tool_name": tool_obj.name},
                        remediation=RemediationAction(
                            type="whitelist_domain",
                            format="json_patch",
                            patch_data=[{"op": "add", "path": "/governance/allowed_domains/-", "value": domain}],
                            description=f"Add '{domain}' to allowed_domains",
                        ),
                    )
                )
    return reports


def _enforce_red_button_rule(
    nodes: list[AnyNode], flow: LinearFlow | GraphFlow, tool_map: dict[str, AnyTool]
) -> list[ComplianceReport]:
    """1. Capability Analysis & Red Button Rule"""
    reports: list[ComplianceReport] = []
    for node in nodes:
        caps = _get_capabilities(node, flow)

        # Check tool risks for AgentNode
        critical_tools = []
        if isinstance(node, AgentNode) and isinstance(node.tools, list):
            for tool_name in node.tools:
                resolved_tool = tool_map.get(tool_name)
                if not resolved_tool or not getattr(resolved_tool, "risk_level", None):
                    raise ManifestError.critical_halt(
                        code="VAL-TOOL-MISSING",
                        message=f"Tool '{tool_name}' lacks a valid risk level.",
                    )
                risk = resolved_tool.risk_level
                if risk == "critical":
                    critical_tools.append(tool_name)

        # Check for high-risk capabilities
        needs_guard = False
        violation_reason = []

        if NodeCapability.COMPUTER_USE in caps:
            needs_guard = True
            violation_reason.append("computer_use capability")
        if NodeCapability.CODE_EXECUTION in caps:
            needs_guard = True
            violation_reason.append("code_execution capability")

        if critical_tools:
            needs_guard = True
            violation_reason.append(f"critical tools {critical_tools}")

        if needs_guard and not _is_guarded(node, flow):
            from coreason_manifest.core.workflow.nodes.human import CollaborationMode

            human_node_id = f"guard_{node.id}"
            human_node = HumanNode(
                id=human_node_id,
                type="human",
                prompt=f"Approve unsafe action by {node.id}",
                escalation=EscalationStrategy(
                    queue_name="default_guard_queue",
                    notification_level="warning",
                    timeout_seconds=300,
                ),
                collaboration_mode=CollaborationMode.APPROVAL_ONLY,
                metadata={},
            )

            # Construct Patch
            patch_ops = []
            if isinstance(flow, LinearFlow):
                # Find index
                idx = 0
                for i, n in enumerate(flow.steps):
                    if n.id == node.id:
                        idx = i
                        break
                patch_ops.append({"op": "add", "path": f"/sequence/{idx}", "value": human_node.model_dump(mode="json")})
            elif isinstance(flow, GraphFlow):
                # Handle non-linear edge rewiring for dynamic security guard insertion.

                # 1. Add Guard Node
                patch_ops.append(
                    {"op": "add", "path": f"/graph/nodes/{human_node_id}", "value": human_node.model_dump(mode="json")}
                )

                # 2. Rewire incoming edges (Target -> Guard)
                for edge_idx, edge in enumerate(flow.graph.edges):
                    if edge.to_node == node.id:
                        patch_ops.append(
                            {"op": "replace", "path": f"/graph/edges/{edge_idx}/to_node", "value": human_node_id}
                        )

                # 3. Add edge (Guard -> Target)
                patch_ops.append(
                    {"op": "add", "path": "/graph/edges/-", "value": {"from_node": human_node_id, "to_node": node.id}}
                )

            reports.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_SEC_UNGUARDED_CRITICAL_003,
                    severity="violation",
                    message=(
                        f"Policy Violation: Node '{node.id}' requires high-risk features "
                        f"({', '.join(violation_reason)}) but is not guarded by a HumanNode."
                    ),
                    node_id=node.id,
                    details={"reason": ", ".join(violation_reason)},
                    remediation=RemediationAction(
                        type="add_guard_node",
                        target_node_id=node.id,
                        format="json_patch",
                        patch_data=patch_ops,
                        description=f"Insert HumanNode '{human_node_id}' before '{node.id}'",
                    ),
                )
            )
    return reports


def _detect_utility_islands(flow: GraphFlow) -> list[ComplianceReport]:
    """5. Topology Analysis (GraphFlow Only)"""
    reports: list[ComplianceReport] = []

    # Build Adjacency List
    _, edges = get_unified_topology(flow)
    adj: dict[str, list[str]] = {nid: [] for nid in flow.graph.nodes}
    for edge in edges:
        # Hotfix 1: Prevent null reference exception during draft mode traversal.
        if edge.from_node in adj:
            adj[edge.from_node].append(edge.to_node)

    # 5a. Tarjan's Algorithm for SCCs (Reachability Context)
    sccs = get_strongly_connected_components(adj)

    # Build map of node_id -> SCC info
    node_cycle_map = {}
    for comp in sccs:
        is_cycle = False
        if len(comp) > 1:
            is_cycle = True
        elif len(comp) == 1:
            node_id_in_comp = comp[0]
            if node_id_in_comp in adj.get(node_id_in_comp, []):
                is_cycle = True

        for nid in comp:
            node_cycle_map[nid] = is_cycle

    # 5b. Utility Island Detection (Unreachable from Entry)
    # Architectural Note: Use explicit entry point
    entry_nodes = []
    if flow.graph.entry_point:
        entry_nodes.append(flow.graph.entry_point)

    # BFS from entry nodes to find reachable set
    reachable = get_reachable_nodes(adj, entry_nodes)

    # Identify Unreachable Nodes
    all_nodes = set(flow.graph.nodes.keys())
    unreachable = all_nodes - reachable

    # Sequential Patch Index Corruption - Aggregate ALL unreachable nodes
    if unreachable:
        safe_node_ids = set()
        dangerous_node_ids = set()
        risk_details = {}  # Map node_id -> list of risk reasons

        for node_id in unreachable:
            node = flow.graph.nodes[node_id]
            caps = _get_capabilities(node, flow)

            risk_reasons = []
            if NodeCapability.COMPUTER_USE in caps:
                risk_reasons.append(NodeCapability.COMPUTER_USE)
            if NodeCapability.CODE_EXECUTION in caps:
                risk_reasons.append(NodeCapability.CODE_EXECUTION)

            if risk_reasons:
                dangerous_node_ids.add(node_id)
                risk_details[node_id] = risk_reasons
            else:
                safe_node_ids.add(node_id)

        # Gather all edges connected to ANY unreachable node
        bulk_edge_indices = set()
        for idx, edge in enumerate(flow.graph.edges):
            if edge.from_node in unreachable or edge.to_node in unreachable:
                bulk_edge_indices.add(idx)

        # Sort descending to prevent index invalidation during sequential removal
        sorted_edge_indices = sorted(bulk_edge_indices, reverse=True)

        patch_list = []
        # 1. Remove Edges (must be done by index, high to low)
        patch_list.extend([{"op": "remove", "path": f"/graph/edges/{idx}"} for idx in sorted_edge_indices])

        # 2. Remove Nodes (by key, safe order)
        patch_list.extend([{"op": "remove", "path": f"/graph/nodes/{node_id}"} for node_id in unreachable])

        if dangerous_node_ids:
            # Severity violation if any dangerous nodes are present
            reports.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_TOPOLOGY_UNREACHABLE_RISK_003,
                    severity="violation",
                    message=(
                        f"Topology Violation: Found {len(dangerous_node_ids)} dangerous unreachable nodes "
                        f"and {len(safe_node_ids)} dead code nodes. "
                        "Pruning all unreachable topology to restore integrity."
                    ),
                    details={
                        "dangerous_nodes": list(dangerous_node_ids),
                        "safe_nodes": list(safe_node_ids),
                        "risk_details": risk_details,
                    },
                    remediation=RemediationAction(
                        type="prune_topology",
                        format="json_patch",
                        patch_data=patch_list,
                        description=(
                            f"Atomic Prune: Remove {len(unreachable)} unreachable nodes "
                            f"and {len(sorted_edge_indices)} connected edges."
                        ),
                    ),
                )
            )
        elif safe_node_ids:
            # Just warning if only safe nodes
            reports.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_TOPOLOGY_ORPHAN_001,
                    severity="warning",
                    message=f"Topology Warning: Found {len(safe_node_ids)} unreachable nodes (Dead Code).",
                    details={"node_ids": list(safe_node_ids)},
                    remediation=RemediationAction(
                        type="prune_node",
                        format="json_patch",
                        patch_data=patch_list,
                        description=(
                            f"Tree Shake: Remove {len(safe_node_ids)} dead code nodes "
                            f"and {len(sorted_edge_indices)} edges."
                        ),
                    ),
                )
            )
    return reports


def _check_neuro_symbolic_guard(flow: LinearFlow | GraphFlow) -> list[ComplianceReport]:
    """Ensure Evolutionary pipelines are guarded by Symbolic Execution."""
    reports: list[ComplianceReport] = []

    if not isinstance(flow, GraphFlow):
        return reports

    nodes, edges = get_unified_topology(flow)
    node_map = {n.id: n for n in nodes}

    # Map outgoing edges
    outgoing_edges: dict[str, list[str]] = {n.id: [] for n in nodes}
    for edge in edges:
        outgoing_edges[edge.from_node].append(edge.to_node)

    for node in nodes:
        is_evolutionary = False

        # Safely check for evolutionary reasoning without importing the class
        if isinstance(node, (AgentNode, SwarmNode)):
            profile_ref = getattr(node, "profile", None) or getattr(node, "worker_profile", None)

            if isinstance(profile_ref, str) and flow.definitions and profile_ref in flow.definitions.profiles:
                reasoning = flow.definitions.profiles[profile_ref].reasoning
                if getattr(reasoning, "type", "") == "evolutionary":
                    is_evolutionary = True

        if is_evolutionary:
            # Check if it points to a symbolic_execution inspector
            is_guarded = False
            for next_node_id in outgoing_edges[node.id]:
                target = node_map.get(next_node_id)
                from coreason_manifest.core.workflow.nodes.oversight import InspectorNode

                if isinstance(target, InspectorNode) and target.mode == "symbolic_execution":
                    is_guarded = True
                    break

            if not is_guarded:
                reports.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_SEC_MISSING_SYMBOLIC_GUARD_004,
                        severity="violation",
                        message=(
                            f"Node '{node.id}' uses EvolutionaryReasoning but is not "
                            "guarded by a symbolic_execution InspectorNode."
                        ),
                        node_id=node.id,
                        remediation=RemediationAction(
                            type="update_field",
                            target_node_id=node.id,
                            patch_data=[],
                            description="Route this node's output to an InspectorNode with mode='symbolic_execution'.",
                        ),
                    )
                )
    return reports


def _check_island_evolution_binding(flow: LinearFlow | GraphFlow) -> list[ComplianceReport]:
    """Cohesion: Ensure Island Model swarms are utilizing Evolutionary Reasoning."""
    reports: list[ComplianceReport] = []
    nodes, _ = get_unified_topology(flow)

    for node in nodes:
        if isinstance(node, SwarmNode) and node.distribution_strategy == "island_model":
            profile_ref = node.worker_profile
            is_evolutionary = False

            if flow.definitions and profile_ref in flow.definitions.profiles:
                reasoning = flow.definitions.profiles[profile_ref].reasoning
                if getattr(reasoning, "type", "") == "evolutionary":
                    is_evolutionary = True

            if not is_evolutionary:
                reports.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_SWARM_ISLAND_NON_EVOLUTIONARY_005,
                        severity="violation",
                        message=(
                            f"SwarmNode '{node.id}' uses 'island_model' but its "
                            f"worker_profile '{profile_ref}' does not use EvolutionaryReasoning."
                        ),
                        node_id=node.id,
                        remediation=RemediationAction(
                            type="update_field",
                            target_node_id=node.id,
                            patch_data=[],
                            description="Change the worker_profile to an AgentProfile utilizing EvolutionaryReasoning.",
                        ),
                    )
                )
    return reports


def _check_meta_analysis_export_contract(flow: LinearFlow | GraphFlow) -> list[ComplianceReport]:
    """Cohesion: Meta-Analysis swarms MUST define interoperability exports."""
    nodes, _ = get_unified_topology(flow)

    return [
        ComplianceReport(
            code=ErrorCatalog.ERR_SWARM_META_ANALYSIS_MISSING_EXPORT_006,
            severity="violation",
            message=(
                f"SwarmNode '{node.id}' uses a 'meta_analysis_matrix' reducer but "
                "fails to define 'export_interoperability'. Downstream biostatistics will fail."
            ),
            node_id=node.id,
            remediation=RemediationAction(
                type="update_field",
                target_node_id=node.id,
                patch_data=[],
                description="Add formats like 'csv' or 'revman' to the export_interoperability list.",
            ),
        )
        for node in nodes
        if (
            isinstance(node, SwarmNode)
            and node.reducer_function == "meta_analysis_matrix"
            and (not node.export_interoperability or len(node.export_interoperability) == 0)
        )
    ]


def _check_meta_analysis_provenance_contract(flow: LinearFlow | GraphFlow) -> list[ComplianceReport]:
    """Cohesion Rule: Meta-Analysis swarms MUST enforce visual bounding box provenance."""
    reports: list[ComplianceReport] = []
    nodes, _ = get_unified_topology(flow)

    for node in nodes:
        if isinstance(node, SwarmNode) and node.reducer_function == "meta_analysis_matrix":
            has_visual_provenance = False

            if flow.definitions and node.worker_profile in flow.definitions.profiles:
                profile = flow.definitions.profiles[node.worker_profile]
                # Safely traverse the profile -> memory -> semantic -> provenance tree
                if getattr(profile, "memory", None):
                    semantic = getattr(profile.memory, "semantic", None)
                    if (
                        semantic
                        and getattr(semantic, "provenance", None)
                        and getattr(semantic.provenance, "required_level", "") == "visual_bounding_box"
                    ):
                        has_visual_provenance = True

            if not has_visual_provenance:
                reports.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_SWARM_META_ANALYSIS_UNGROUNDED_007,
                        severity="violation",
                        message=(
                            f"SwarmNode '{node.id}' performs meta-analysis but its worker profile "
                            "lacks strict 'visual_bounding_box' provenance. FDA auditability is compromised."
                        ),
                        node_id=node.id,
                        remediation=RemediationAction(
                            type="update_field",
                            target_node_id=node.id,
                            patch_data=[],
                            description="Update worker_profile's SemanticMemoryConfig to use visual_bounding_box.",
                        ),
                    )
                )
    return reports


def _check_prisma_s_ontological_guard(flow: LinearFlow | GraphFlow) -> list[ComplianceReport]:
    """Cohesion Rule: PRISMA-S Search generation MUST be guarded by an Ontological Validator."""
    reports: list[ComplianceReport] = []

    if not isinstance(flow, GraphFlow):
        return reports

    nodes, edges = get_unified_topology(flow)
    node_map = {n.id: n for n in nodes}

    outgoing_edges: dict[str, list[str]] = {n.id: [] for n in nodes}
    for edge in edges:
        outgoing_edges[edge.from_node].append(edge.to_node)

    for node in nodes:
        is_prisma_s = False

        if isinstance(node, (AgentNode, SwarmNode)):
            profile_ref = getattr(node, "profile", None) or getattr(node, "worker_profile", None)
            if isinstance(profile_ref, str) and flow.definitions and profile_ref in flow.definitions.profiles:
                reasoning = flow.definitions.profiles[profile_ref].reasoning
                # Check if it's a CouncilReasoning with methodology.standard == "prisma_s"
                if (
                    getattr(reasoning, "type", "") == "council"
                    and getattr(reasoning, "methodology", None)
                    and getattr(reasoning.methodology, "standard", "") == "prisma_s"
                ):
                    is_prisma_s = True

        if is_prisma_s:
            is_guarded = False
            for next_node_id in outgoing_edges[node.id]:
                target = node_map.get(next_node_id)
                from coreason_manifest.core.workflow.nodes.oversight import InspectorNode

                if (
                    isinstance(target, InspectorNode)
                    and target.mode == "symbolic_execution"
                    and target.target_solver in ["mesh_ontology_validator", "emtree_validator", "meddra_validator"]
                ):
                    is_guarded = True
                    break

            if not is_guarded:
                reports.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_COUNCIL_PRISMA_S_UNGUARDED_008,
                        severity="violation",
                        message=(
                            f"Node '{node.id}' uses PRISMA-S methodology but its output is not "
                            "topologically guarded by an Ontological InspectorNode (e.g., mesh_ontology_validator)."
                        ),
                        node_id=node.id,
                        remediation=RemediationAction(
                            type="update_field",
                            target_node_id=node.id,
                            patch_data=[],
                            description="Route this node's output to an ontological InspectorNode.",
                        ),
                    )
                )
    return reports


def _check_federated_search_press_guard(flow: LinearFlow | GraphFlow) -> list[ComplianceReport]:
    """Cohesion: Federated Search MUST be peer-reviewed by a PRESS-2015 Council."""
    reports: list[ComplianceReport] = []
    if not isinstance(flow, GraphFlow):
        return reports

    nodes, edges = get_unified_topology(flow)
    node_map = {n.id: n for n in nodes}

    outgoing_edges: dict[str, list[str]] = {n.id: [] for n in nodes}
    for edge in edges:
        outgoing_edges[edge.from_node].append(edge.to_node)

    for node in nodes:
        if isinstance(node, AgentNode) and getattr(node, "federated_search", None) is not None:
            is_guarded = False
            for next_node_id in outgoing_edges.get(node.id, []):
                target = node_map.get(next_node_id)
                # Check if target uses CouncilReasoning with PRESS_2015
                if isinstance(target, (AgentNode, SwarmNode)):
                    profile_ref = getattr(target, "profile", None) or getattr(target, "worker_profile", None)
                    if isinstance(profile_ref, str) and flow.definitions and profile_ref in flow.definitions.profiles:
                        reasoning = flow.definitions.profiles[profile_ref].reasoning
                        if (
                            getattr(reasoning, "type", "") == "council"
                            and getattr(reasoning, "methodology", None)
                            and getattr(reasoning.methodology, "standard", "") == "press_2015"
                        ):
                            is_guarded = True
                            break
            if not is_guarded:
                reports.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_SEARCH_PRESS_UNGUARDED_009,
                        severity="violation",
                        message=(
                            f"AgentNode '{node.id}' executes a FederatedSearchConfig but its output is not "
                            "topologically guarded by a PRESS_2015 Council peer-review."
                        ),
                        node_id=node.id,
                        remediation=RemediationAction(
                            type="add_press_guard",
                            target_node_id=node.id,
                            patch_data=[],
                            description=(
                                "Route this node's output to an Agent/Swarm powered by "
                                "a PRESS-2015 CouncilReasoning profile."
                            ),
                        ),
                    )
                )
    return reports


def _check_genui_rbac(flow: LinearFlow | GraphFlow) -> list[ComplianceReport]:
    """Cohesion: Zero-Trust GenUI Fencing"""
    reports: list[ComplianceReport] = []
    nodes, _ = get_unified_topology(flow)

    for node in nodes:
        if isinstance(node, AgentNode):
            presentation = getattr(node, "presentation", None)
            if presentation and getattr(presentation, "render_strategy", None) == RenderStrategy.GEN_UI:
                profile_ref = getattr(node, "profile", None)

                # Try to get ui_capabilities from the profile
                ui_capabilities = None
                if isinstance(profile_ref, str) and flow.definitions and profile_ref in flow.definitions.profiles:
                    profile = flow.definitions.profiles[profile_ref]
                    ui_capabilities = getattr(profile, "ui_capabilities", None)
                elif hasattr(profile_ref, "ui_capabilities"):
                    ui_capabilities = getattr(profile_ref, "ui_capabilities", None)

                if not ui_capabilities:
                    reports.append(
                        ComplianceReport(
                            code=ErrorCatalog.ERR_SEC_GENUI_UNAUTHORIZED_011,
                            severity="violation",
                            message="Agent is assigned to render GenUI but lacks explicit ui_capabilities.",
                            node_id=node.id,
                            remediation=RemediationAction(
                                type="update_field",
                                target_node_id=node.id,
                                patch_data=[],
                                description="Populate the AgentProfile's ui_capabilities list.",
                            ),
                        )
                    )

    return reports


def _check_cal_deduplication_guard(flow: LinearFlow | GraphFlow) -> list[ComplianceReport]:
    """Cohesion: Conformal Active Learning MUST be preceded by Epistemic Deduplication."""
    reports: list[ComplianceReport] = []
    if not isinstance(flow, GraphFlow):
        return reports

    nodes, edges = get_unified_topology(flow)
    node_map = {n.id: n for n in nodes}

    incoming_edges: dict[str, list[str]] = {n.id: [] for n in nodes}
    for edge in edges:
        incoming_edges[edge.to_node].append(edge.from_node)

    for node in nodes:
        if isinstance(node, SwarmNode) and getattr(node, "cal_config", None) is not None:
            is_guarded = False
            for prev_node_id in incoming_edges.get(node.id, []):
                source = node_map.get(prev_node_id)
                if (
                    isinstance(source, SwarmNode)
                    and getattr(source, "reducer_function", None) == "epistemic_deduplication"
                ):
                    is_guarded = True
                    break

            if not is_guarded:
                reports.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_SWARM_CAL_POISONING_010,
                        severity="violation",
                        message=(
                            f"SwarmNode '{node.id}' uses Conformal Active Learning (CAL) but is not "
                            "immediately preceded by an 'epistemic_deduplication' Swarm. This risks double-counting."
                        ),
                        node_id=node.id,
                        remediation=RemediationAction(
                            type="add_deduplication_guard",
                            target_node_id=node.id,
                            patch_data=[],
                            description=(
                                "Insert a SwarmNode with reducer_function='epistemic_deduplication' "
                                "before this CAL node."
                            ),
                        ),
                    )
                )
    return reports


def validate_policy(flow: LinearFlow | GraphFlow) -> list[ComplianceReport]:
    """
    Enforces security policies and capability contracts.

    1. Capability Analysis: Ensures high-risk capabilities are declared.
    2. Topology Check (Red Button Rule): Critical nodes must be guarded by HumanNode.
    3. Swarm Safety: Recursively checks worker profiles in Swarms.
    4. Domain Policy: Checks tool URLs against allowed domains (Strict Canonicalization).
    5. Topology Analysis: Checks for hazardous utility islands using Tarjan's algorithm.
    6. Neuro-Symbolic Gatekeeping: Ensure Evolutionary pipelines are guarded by Symbolic Execution.
    """
    reports: list[ComplianceReport] = []

    # Extract all nodes
    nodes, _ = get_unified_topology(flow)

    # Build tool map: name -> tool_object
    tool_map: dict[str, AnyTool] = {}
    if flow.definitions and flow.definitions.tool_packs:
        for pack in flow.definitions.tool_packs.values():
            for tool in pack.tools:
                tool_map[tool.name] = tool

    # 0. Domain Policy Check
    reports.extend(_check_domain_whitelist(flow, tool_map))

    # 1. Capability Analysis & Red Button Rule
    reports.extend(_enforce_red_button_rule(nodes, flow, tool_map))

    # 5. Topology Analysis (GraphFlow Only)
    if isinstance(flow, GraphFlow):
        reports.extend(_detect_utility_islands(flow))

    # 6. Neuro-Symbolic Gatekeeping
    reports.extend(_check_neuro_symbolic_guard(flow))

    # 7. Swarm-Evolution Cohesion (Ref: ADR-011: Swarm-Evolution Cohesion)
    reports.extend(_check_island_evolution_binding(flow))

    # 8. Regulatory-Grade Meta-Analysis Cohesion (Ref: ADR-012: Regulatory-Grade Meta-Analysis Cohesion)
    reports.extend(_check_meta_analysis_export_contract(flow))

    # 9. Meta-Analysis Provenance Binding
    reports.extend(_check_meta_analysis_provenance_contract(flow))

    # 10. PRISMA-S Ontological Guarding
    reports.extend(_check_prisma_s_ontological_guard(flow))

    # 11. Federated Search PRESS Guard (Ref: ADR-014: Federated Search Guarding)
    reports.extend(_check_federated_search_press_guard(flow))

    # 12. Epistemic Deduplication Guard (Ref: ADR-014: Federated Search Guarding)
    reports.extend(_check_cal_deduplication_guard(flow))

    # 13. Zero-Trust GenUI Fencing
    reports.extend(_check_genui_rbac(flow))

    return reports


def _is_guarded(target_node: AnyNode, flow: LinearFlow | GraphFlow) -> bool:
    """
    Checks if the target node is topologically guarded by a HumanNode.
    Only HumanNode is a valid guard. SwitchNode is NOT a valid guard.
    """
    nodes, edges = get_unified_topology(flow)

    all_ids = {n.id for n in nodes}

    # Determine entry point
    entry_id = None
    if isinstance(flow, GraphFlow):
        entry_id = flow.graph.entry_point
    elif isinstance(flow, LinearFlow) and flow.steps:
        entry_id = flow.steps[0].id

    # Valid guards: HumanNode only.
    valid_guards = (HumanNode,)

    # Construct adjacency map
    adj: dict[str, list[str]] = {nid: [] for nid in all_ids}
    for edge in edges:
        if edge.from_node in adj:
            adj[edge.from_node].append(edge.to_node)

    # Detect implicit fallback routes to prevent security "wormholes"
    def extract_fallbacks(data: Any) -> list[str]:
        fallbacks = []
        if isinstance(data, dict):
            for k, v in data.items():
                if k == "fallback_node_id" and isinstance(v, str):
                    fallbacks.append(v)
                else:
                    fallbacks.extend(extract_fallbacks(v))
        elif isinstance(data, list):
            for item in data:
                fallbacks.extend(extract_fallbacks(item))
        return fallbacks

    for node in nodes:
        node_data = node.model_dump(exclude_none=True)
        for fallback_id in extract_fallbacks(node_data):
            if node.id in adj and fallback_id in adj and fallback_id not in adj[node.id]:
                # Add implicit fallback edge to adjacency map
                adj[node.id].append(fallback_id)

    guards = {n.id for n in nodes if isinstance(n, valid_guards)}

    if entry_id:
        queue = [entry_id]
        visited = {entry_id}
    else:
        queue = []
        visited = set()

    # Handle case where target is the entry node
    if entry_id and target_node.id == entry_id:
        return False

    # 1. Check strict reachability (ignoring guards) to identify Islands
    if entry_id:
        full_queue = [entry_id]
        full_visited = {entry_id}
    else:
        full_queue = []
        full_visited = set()

    reachable = False
    while full_queue:
        curr = full_queue.pop(0)
        if curr == target_node.id:
            reachable = True
            break
        for n in adj.get(curr or "", []):
            if n not in full_visited:
                full_visited.add(n)
                full_queue.append(n)

    if not reachable:
        return False  # Island -> Fail Closed

    # 2. Check guarded reachability
    while queue:
        curr_id = queue.pop(0)

        if curr_id == target_node.id:
            return False  # Reached target without passing a guard

        # If current node is a guard, we stop traversing this path
        # (because downstream is guarded by this node).
        if curr_id in guards:
            continue

        # Expand neighbors
        for neighbor in adj.get(curr_id or "", []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    # If reachable but not via unguarded path -> Guarded
    return True
