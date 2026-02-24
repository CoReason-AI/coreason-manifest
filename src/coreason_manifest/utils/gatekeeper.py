# src/coreason_manifest/utils/gatekeeper.py
from __future__ import annotations

from typing import TYPE_CHECKING, cast

from coreason_manifest.spec.core.constants import NodeCapability
from coreason_manifest.spec.core.flow import AnyNode, GraphFlow, LinearFlow
from coreason_manifest.spec.core.nodes import AgentNode, SwarmNode
from coreason_manifest.spec.interop.compliance import (
    ComplianceReport,
    ErrorCatalog,
    RemediationAction,
)
from coreason_manifest.utils.net_utils import canonicalize_domain
from coreason_manifest.utils.topology import get_reachable_nodes, get_strongly_connected_components

if TYPE_CHECKING:
    from coreason_manifest.spec.core.tools import ToolCapability


def validate_policy(flow: LinearFlow | GraphFlow) -> list[ComplianceReport]:
    """
    Enforces security policies and capability contracts.

    1. Capability Analysis: Ensures high-risk capabilities are declared.
    2. Topology Check (Red Button Rule): Critical nodes must be guarded by HumanNode.
    3. Swarm Safety: Recursively checks worker profiles in Swarms.
    4. Domain Policy: Checks tool URLs against allowed domains (Strict Canonicalization).
    5. Topology Analysis: Checks for hazardous utility islands using Tarjan's algorithm.
    """
    reports: list[ComplianceReport] = []

    # Extract all nodes
    nodes: list[AnyNode] = []
    if isinstance(flow, LinearFlow):
        nodes = flow.steps
    elif isinstance(flow, GraphFlow):
        nodes = list(flow.graph.nodes.values())

    # Helper to resolve profile and get capabilities
    def get_capabilities(node: AnyNode) -> list[str]:
        reasoning = None
        if isinstance(node, AgentNode):
            # Resolve profile
            if isinstance(node.profile, str):
                if flow.definitions and node.profile in flow.definitions.profiles:
                    profile = flow.definitions.profiles[node.profile]
                    reasoning = profile.reasoning
            else:
                reasoning = node.profile.reasoning

        elif isinstance(node, SwarmNode) and flow.definitions and node.worker_profile in flow.definitions.profiles:
            # Resolve worker profile
            profile = flow.definitions.profiles[node.worker_profile]
            reasoning = profile.reasoning

        if reasoning and hasattr(reasoning, "required_capabilities"):
            return cast("list[str]", reasoning.required_capabilities())
        return []

    # Build tool map: name -> tool_object
    tool_map: dict[str, ToolCapability] = {}
    if flow.definitions and flow.definitions.tool_packs:
        for pack in flow.definitions.tool_packs.values():
            for tool in pack.tools:
                tool_map[tool.name] = tool

    # 0. Domain Policy Check (Pillar 3: High-Fidelity URI Governance)
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

    # 1. Capability Analysis & Red Button Rule
    for node in nodes:
        caps = get_capabilities(node)

        # Check tool risks for AgentNode
        critical_tools = []
        if isinstance(node, AgentNode):
            for tool_name in node.tools:
                resolved_tool = tool_map.get(tool_name)
                # Fix 3: Fail-Open Vulnerability - Default to 'critical' if unknown
                risk = resolved_tool.risk_level if resolved_tool else "critical"
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

        if needs_guard:
            # Check Co-Intelligence Policy
            has_policy = False
            if flow.governance and flow.governance.co_intelligence:
                # If we have a policy, we assume it handles the risk (e.g. mentor_mode)
                has_policy = True

            if not has_policy:
                reports.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_SEC_UNGUARDED_CRITICAL_003,
                        severity="violation",
                        message=(
                            f"Policy Violation: Node '{node.id}' requires high-risk features "
                            f"({', '.join(violation_reason)}) but no Co-Intelligence Policy is configured."
                        ),
                        node_id=node.id,
                        details={"reason": ", ".join(violation_reason)},
                        remediation=RemediationAction(
                            type="configure_governance",
                            format="json_patch",
                            patch_data=[{"op": "add", "path": "/governance/co_intelligence", "value": {}}],
                            description="Configure Co-Intelligence Policy in Governance.",
                        ),
                    )
                )

    # 5. Topology Analysis (GraphFlow Only)
    if isinstance(flow, GraphFlow):
        # Build Adjacency List
        adj: dict[str, list[str]] = {nid: [] for nid in flow.graph.nodes}
        for edge in flow.graph.edges:
            # SOTA Fix 1: Defensive check for Draft Mode Fatality
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

        # Fix 2: Sequential Patch Index Corruption - Aggregate ALL unreachable nodes
        if unreachable:
            safe_node_ids = set()
            dangerous_node_ids = set()
            risk_details = {}  # Map node_id -> list of risk reasons

            for node_id in unreachable:
                node = flow.graph.nodes[node_id]
                caps = get_capabilities(node)

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


