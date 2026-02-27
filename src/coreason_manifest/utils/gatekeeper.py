# src/coreason_manifest/utils/gatekeeper.py
from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, cast, Any

from coreason_manifest.spec.core.constants import NodeCapability
from coreason_manifest.spec.core.contracts import (
    ActionNode,
    NodeSpec,
    PlanTree,
    StrategyNode,
)
# Deprecated types imported for limited backward-compat in private helpers if needed,
# but public API is now PlanTree based.
from coreason_manifest.spec.core.flow import GraphFlow, LinearFlow
from coreason_manifest.spec.core.nodes import AgentNode, AnyNode, HumanNode, SwarmNode
from coreason_manifest.spec.core.resilience import EscalationStrategy
from coreason_manifest.spec.interop.compliance import (
    ComplianceReport,
    ErrorCatalog,
    RemediationAction,
)
from coreason_manifest.utils.net_utils import canonicalize_domain
from coreason_manifest.utils.topology import (
    get_reachable_nodes,
    get_strongly_connected_components,
)

if TYPE_CHECKING:
    from coreason_manifest.spec.core.tools import ToolCapability


class ZeroTrustRoutingError(Exception):
    """
    Fatal error raised when a graph violates zero-trust constraints,
    such as bypassing a locked node or creating an unguarded cycle.
    """

    def __init__(self, message: str, node_id: str | None = None) -> None:
        super().__init__(message)
        self.node_id = node_id


def compile_graph(plan: PlanTree) -> None:
    """
    Compiles and strictly validates a PlanTree for execution.

    SOTA Enforcement:
    1. Reachability (Ghost Cluster) Check: Ensures entire graph is connected from root.
    2. Cycle Detection: Checks for cycles. If found, checks for Bounded Loop Constraints.
       If unbounded, raises fatal error.
    3. Dominator Tree Analysis: Calculates dominators for every node.
       Enforces that for every 'High-Risk' node (ActionNode with dangerous capabilities),
       its dominator set MUST contain at least one `locked=True` node.

    Args:
        plan: The strict execution plan.

    Raises:
        ZeroTrustRoutingError: If validation fails.
    """
    if not plan.nodes:
        raise ZeroTrustRoutingError("Plan is empty.")

    if plan.root_node not in plan.nodes:
        raise ZeroTrustRoutingError(f"Root node {plan.root_node} not found in plan.", node_id=plan.root_node)

    # 1. Build Adjacency List & Identifiers
    adj: dict[str, list[str]] = {nid: [] for nid in plan.nodes}
    # Reverse adjacency for dominator calculation
    preds: dict[str, list[str]] = {nid: [] for nid in plan.nodes}

    locked_nodes: set[str] = set()
    high_risk_nodes: set[str] = set()

    for nid, node in plan.nodes.items():
        if isinstance(node, (ActionNode, StrategyNode)):
            if node.locked:
                locked_nodes.add(nid)

        # Identify High Risk Nodes
        if isinstance(node, ActionNode):
            caps = node.skill.capabilities
            if NodeCapability.COMPUTER_USE in caps or NodeCapability.CODE_EXECUTION in caps:
                high_risk_nodes.add(nid)

            # SOTA Fix: Add next_node logic for chaining ActionNodes
            if node.next_node:
                if node.next_node not in plan.nodes:
                    raise ZeroTrustRoutingError(
                        f"Action node {nid} routes to unknown next_node {node.next_node}.",
                        node_id=nid,
                    )
                adj[nid].append(node.next_node)
                preds[node.next_node].append(nid)

        if isinstance(node, StrategyNode):
            for route_target in node.routes.values():
                if route_target not in plan.nodes:
                    raise ZeroTrustRoutingError(
                        f"Strategy node {nid} routes to unknown node {route_target}.",
                        node_id=nid,
                    )
                adj[nid].append(route_target)
                preds[route_target].append(nid)

    # 2. Strict Reachability Check (Ghost Cluster Protection)
    # Before initializing Dominators, we MUST verify reachability.
    reachable = get_reachable_nodes(adj, [plan.root_node])
    all_nodes_set = set(plan.nodes.keys())

    # If any defined node is unreachable, it's a Ghost Cluster (or dead code),
    # which invalidates the dominator assumption that "All nodes are potential dominators".
    if reachable != all_nodes_set:
        unreachable = all_nodes_set - reachable
        raise ZeroTrustRoutingError(
            f"Graph contains unreachable nodes/ghost clusters: {unreachable}. "
            "All nodes must be reachable from the root in a Zero-Trust Kernel.",
            node_id=list(unreachable)[0]
        )

    # 3. Cycle Detection (Bounded)
    visited = set()
    recursion_stack = set()

    def detect_cycle(current_node: str) -> bool:
        visited.add(current_node)
        recursion_stack.add(current_node)

        for neighbor in adj[current_node]:
            if neighbor not in visited:
                if detect_cycle(neighbor):
                    return True
            elif neighbor in recursion_stack:
                # Cycle detected! SOTA Check: Is this cycle bounded?
                node_obj = plan.nodes[current_node]

                is_bounded = False
                if hasattr(node_obj, "constraints"):
                    for c in node_obj.constraints:
                        # Allow standard loop constraints
                        if c.type in ("max_iterations", "timeout", "loop_limit"):
                            is_bounded = True
                            break

                if not is_bounded:
                    raise ZeroTrustRoutingError(
                        f"Unbounded cycle detected at node '{current_node}' -> '{neighbor}'. "
                        "Loops must be guarded by a Constraint (e.g. max_iterations).",
                        node_id=current_node
                    )
                # If bounded, allow and continue.
                pass

        recursion_stack.remove(current_node)
        return False

    try:
        detect_cycle(plan.root_node)
    except ZeroTrustRoutingError:
        raise
    except RecursionError:
        raise ZeroTrustRoutingError("Graph depth exceeded recursion limit (possible cycle).")

    # 4. Dominator Analysis (Iterative O(V+E))
    # Init: Dom(root) = {root}, Dom(others) = All Nodes
    dom: dict[str, set[str]] = {nid: all_nodes_set.copy() for nid in all_nodes_set}
    dom[plan.root_node] = {plan.root_node}

    changed = True
    while changed:
        changed = False
        # Simple iterative order (can be optimized but sufficient for kernel validation)
        for nid in plan.nodes:
            if nid == plan.root_node:
                continue

            node_preds = preds[nid]
            if not node_preds:
                # Should not happen due to Reachability Check above, but as a safeguard:
                # Unreachable node's dom stays as All Nodes? No, unreachable nodes maintain {all}
                # which causes the ghost cluster exploit if we didn't check reachability.
                # Since we checked reachability, node_preds IS NOT EMPTY.
                continue

            # Intersection of preds dominators
            # Start with the first pred's dom
            intersection = dom[node_preds[0]].copy()
            for p in node_preds[1:]:
                intersection &= dom[p]

            new_dom = {nid} | intersection

            if new_dom != dom[nid]:
                dom[nid] = new_dom
                changed = True

    # 5. Enforce High-Risk Dominance
    for hr_node in high_risk_nodes:
        dominators = dom[hr_node]
        guards = dominators.intersection(locked_nodes)

        if not guards:
            # Violation
            # Double check reachability just in case logic drifts (though enforced above)
            if plan.root_node in dominators:
                raise ZeroTrustRoutingError(
                    f"High-Risk Node '{hr_node}' is not dominated by any Locked Node. "
                    "Critical capabilities must be guarded by a locked compliance step.",
                    node_id=hr_node
                )

    return


def _get_capabilities_from_skill(node: ActionNode | StrategyNode) -> list[str]:
    """Extract capabilities from AtomicSkill definition if present."""
    if isinstance(node, ActionNode) and hasattr(node.skill, "capabilities"):
        return node.skill.capabilities
    return []


def validate_policy(plan: PlanTree) -> list[ComplianceReport]:
    """
    Enforces security policies on the strict PlanTree.
    Refactored to support SOTA NodeSpec and PlanTree.
    """
    reports: list[ComplianceReport] = []

    # 1. Capability Analysis & Red Button Rule
    # Enforced by compile_graph, but we can add warnings or specific remediation hints here if needed.
    # Leaving largely empty as compile_graph is the primary enforcement mechanism now.

    # 2. Utility Islands (Unreachable nodes)
    # Check is also performed by compile_graph as a hard error.
    # validate_policy serves as a linter before compilation if used separately.
    adj: dict[str, list[str]] = {nid: [] for nid in plan.nodes}
    for nid, node in plan.nodes.items():
        if isinstance(node, StrategyNode):
            for target in node.routes.values():
                 if target in plan.nodes:
                     adj[nid].append(target)
        if isinstance(node, ActionNode) and node.next_node:
             if node.next_node in plan.nodes:
                 adj[nid].append(node.next_node)

    reachable = get_reachable_nodes(adj, [plan.root_node])
    all_nodes = set(plan.nodes.keys())
    unreachable = all_nodes - reachable

    if unreachable:
        reports.append(
            ComplianceReport(
                code=ErrorCatalog.ERR_TOPOLOGY_ORPHAN_001,
                severity="warning",
                message=f"Topology Warning: Found {len(unreachable)} unreachable nodes (Dead Code).",
                details={"node_ids": list(unreachable)},
                remediation=RemediationAction(type="prune_node", description="Remove dead nodes", patch_data=[])
            )
        )

    return reports
