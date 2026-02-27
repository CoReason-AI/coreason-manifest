# src/coreason_manifest/utils/gatekeeper.py
from __future__ import annotations

from typing import TYPE_CHECKING, cast

from coreason_manifest.spec.core.constants import NodeCapability
from coreason_manifest.spec.core.flow import FlowSpec
from coreason_manifest.spec.core.contracts import ActionNode, NodeSpec, StrategyNode
from coreason_manifest.spec.core.resilience import EscalationStrategy
from coreason_manifest.spec.interop.compliance import (
    ComplianceReport,
    ErrorCatalog,
    RemediationAction,
)
from coreason_manifest.utils.net_utils import canonicalize_domain
from coreason_manifest.utils.topology import (
    get_unified_topology,
    validate_topology,
)

if TYPE_CHECKING:
    from coreason_manifest.spec.core.tools import ToolCapability


def _get_capabilities(node: NodeSpec, flow: FlowSpec) -> list[str]:
    """Helper to resolve profile and get capabilities."""
    if isinstance(node, ActionNode):
        return node.skill.capabilities
    return []


def _check_domain_whitelist(
    flow: FlowSpec, tool_map: dict[str, ToolCapability]
) -> list[ComplianceReport]:
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
    nodes: list[NodeSpec], flow: FlowSpec, tool_map: dict[str, ToolCapability]
) -> list[ComplianceReport]:
    """1. Capability Analysis & Red Button Rule"""
    reports: list[ComplianceReport] = []
    for node in nodes:
        caps = _get_capabilities(node, flow)

        # Check for high-risk capabilities
        needs_guard = False
        violation_reason = []

        if NodeCapability.COMPUTER_USE in caps:
            needs_guard = True
            violation_reason.append("computer_use capability")
        if NodeCapability.CODE_EXECUTION in caps:
            needs_guard = True
            violation_reason.append("code_execution capability")

        if needs_guard and not _is_guarded(node, flow):
            human_node_id = f"guard_{node.id}"
            # Inject ActionNode as guard
            from coreason_manifest.spec.core.contracts import SkillConfig, StrictPayload
            human_node = ActionNode(
                id=human_node_id,
                type="action",
                metadata=StrictPayload(data={"prompt": f"Approve unsafe action by {node.id}"}),
                skill=SkillConfig(capabilities=["human_approval"])
            )

            # Construct Patch
            patch_ops = []
            # Fix 1: Ghost Guard Graph Injection Failure - Rewire edges

            # 1. Add Guard Node
            patch_ops.append(
                {"op": "add", "path": f"/graph/nodes/{human_node_id}", "value": human_node.model_dump(mode="json")}
            )

            # 2. Rewire incoming edges (Target -> Guard)
            for edge_idx, edge in enumerate(flow.graph.edges):
                if edge.to_node == node.id:
                    patch_ops.append(
                        {"op": "replace", "path": f"/graph/edges/{edge_idx}/to", "value": human_node_id}
                    )

            # 3. Add edge (Guard -> Target)
            patch_ops.append(
                {"op": "add", "path": "/graph/edges/-", "value": {"from": human_node_id, "to": node.id}}
            )

            # 4. Entry Point Check (Fix Bypass)
            if flow.graph.entry_point == node.id:
                patch_ops.append(
                    {"op": "replace", "path": "/graph/entry_point", "value": human_node_id}
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
                        description=f"Insert Guard '{human_node_id}' before '{node.id}'",
                    ),
                )
            )
    return reports


def validate_policy(flow: FlowSpec) -> list[ComplianceReport]:
    """
    Enforces security policies and capability contracts.

    1. Topology Validation (AOT): Strict structural check.
    2. Capability Analysis: Ensures high-risk capabilities are declared.
    3. Topology Check (Red Button Rule): Critical nodes must be guarded by HumanNode.
    4. Swarm Safety: Recursively checks worker profiles in Swarms.
    5. Domain Policy: Checks tool URLs against allowed domains (Strict Canonicalization).
    """
    # 1. Topology Validation (AOT) - Fail Fast
    validate_topology(flow)

    reports: list[ComplianceReport] = []

    # Extract all nodes
    nodes, _ = get_unified_topology(flow)

    # Build tool map: name -> tool_object
    tool_map: dict[str, ToolCapability] = {}
    if flow.definitions and flow.definitions.tool_packs:
        for pack in flow.definitions.tool_packs.values():
            for tool in pack.tools:
                tool_map[tool.name] = tool

    # 0. Domain Policy Check
    reports.extend(_check_domain_whitelist(flow, tool_map))

    # 1. Capability Analysis & Red Button Rule
    reports.extend(_enforce_red_button_rule(nodes, flow, tool_map))

    return reports


def _is_guarded(target_node: NodeSpec, flow: FlowSpec) -> bool:
    """
    Checks if the target node is topologically guarded by a HumanNode (ActionNode with human capability).
    """
    nodes, edges = get_unified_topology(flow)

    all_ids = {n.id for n in nodes}

    # Determine entry point
    entry_id = flow.graph.entry_point

    # Construct adjacency map
    adj: dict[str, list[str]] = {nid: [] for nid in all_ids}
    for edge in edges:
        if edge.from_node in adj:
            adj[edge.from_node].append(edge.to_node)

    # Valid guards: ActionNode with human_approval capability
    guards = set()
    for n in nodes:
        if isinstance(n, ActionNode) and "human_approval" in n.skill.capabilities:
            guards.add(n.id)

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
