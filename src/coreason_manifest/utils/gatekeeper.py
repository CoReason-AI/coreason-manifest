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
    2. Cycle Detection: Checks for cycles. If found, checks for Bounded Loop Constraints
       on ANY node in the cycle path.
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

            if node.next_node:
                if node.next_node not in plan.nodes:
                    raise ZeroTrustRoutingError(
                        f"Action node {nid} routes to unknown next_node {node.next_node}.",
                        node_id=nid,
                    )
                adj[nid].append(node.next_node)
                preds[node.next_node].append(nid)

        if isinstance(node, StrategyNode):
            if node.default_route not in plan.nodes:
                raise ZeroTrustRoutingError(
                    f"Strategy node {nid} routes to unknown default_route {node.default_route}.",
                    node_id=nid,
                )
            adj[nid].append(node.default_route)
            preds[node.default_route].append(nid)

            for route_target in node.routes.values():
                if route_target not in plan.nodes:
                    raise ZeroTrustRoutingError(
                        f"Strategy node {nid} routes to unknown node {route_target}.",
                        node_id=nid,
                    )
                adj[nid].append(route_target)
                preds[route_target].append(nid)

    # 2. Strict Reachability Check (Ghost Cluster Protection)
    reachable = get_reachable_nodes(adj, [plan.root_node])
    all_nodes_set = set(plan.nodes.keys())

    if reachable != all_nodes_set:
        unreachable = all_nodes_set - reachable
        raise ZeroTrustRoutingError(
            f"Graph contains unreachable nodes/ghost clusters: {unreachable}. "
            "All nodes must be reachable from the root in a Zero-Trust Kernel.",
            node_id=list(unreachable)[0]
        )

    # 3. Cycle Detection (Bounded) & Back-Edge Identification
    visited = set()
    # SOTA Fix: Use ordered list to slice exact cycle path
    path_stack: list[str] = []
    back_edges: list[tuple[str, str]] = []

    def detect_cycle(current_node: str) -> None:
        visited.add(current_node)
        path_stack.append(current_node)

        for neighbor in adj[current_node]:
            if neighbor not in visited:
                detect_cycle(neighbor)
            elif neighbor in path_stack:
                # Cycle detected! (current -> neighbor)
                back_edges.append((current_node, neighbor))

                # SOTA Check: Is this cycle bounded?
                # Extract the exact cycle path from stack: [neighbor, ..., current_node]
                cycle_start_index = path_stack.index(neighbor)
                cycle_path = path_stack[cycle_start_index:]

                # Check ALL nodes in the cycle path for a constraint
                is_bounded = False
                for node_id_in_loop in cycle_path:
                    node_obj = plan.nodes[node_id_in_loop]
                    if hasattr(node_obj, "constraints"):
                        for c in node_obj.constraints:
                            if c.type in ("max_iterations", "timeout", "loop_limit"):
                                is_bounded = True
                                break
                    if is_bounded: break

                if not is_bounded:
                    raise ZeroTrustRoutingError(
                        f"Unbounded cycle detected: {' -> '.join(cycle_path)} -> {neighbor}. "
                        "Loops must be guarded by a Constraint (e.g. max_iterations) on at least one node in the loop.",
                        node_id=current_node
                    )

        path_stack.pop()

    try:
        detect_cycle(plan.root_node)
    except ZeroTrustRoutingError:
        raise
    except RecursionError:
        raise ZeroTrustRoutingError("Graph depth exceeded recursion limit (possible cycle).")

    # 4. Dominator Analysis (Iterative O(V+E)) on DAG (Back-edges removed)
    dag_preds = defaultdict(list)
    for target, sources in preds.items():
        for source in sources:
            if (source, target) in back_edges:
                continue
            dag_preds[target].append(source)

    # Init: Dom(root) = {root}, Dom(others) = All Nodes
    dom: dict[str, set[str]] = {nid: all_nodes_set.copy() for nid in all_nodes_set}
    dom[plan.root_node] = {plan.root_node}

    changed = True
    while changed:
        changed = False
        for nid in plan.nodes:
            if nid == plan.root_node:
                continue

            node_preds = dag_preds[nid]
            if not node_preds:
                continue

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
    # SOTA Fix: Removed the primitive `if not node.locked` check.
    # Compile-time dominance checking (in `compile_graph`) is the authoritative source of truth for high-risk guarding.

    # 2. Utility Islands (Unreachable nodes)
    adj: dict[str, list[str]] = {nid: [] for nid in plan.nodes}
    for nid, node in plan.nodes.items():
        if isinstance(node, StrategyNode):
            if node.default_route in plan.nodes:
                adj[nid].append(node.default_route)

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
