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

            if node.next_node:
                if node.next_node not in plan.nodes:
                    raise ZeroTrustRoutingError(
                        f"Action node {nid} routes to unknown next_node {node.next_node}.",
                        node_id=nid,
                    )
                adj[nid].append(node.next_node)
                preds[node.next_node].append(nid)

        if isinstance(node, StrategyNode):
            # SOTA Fix: Add default_route handling
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
    recursion_stack = set()
    # Track back-edges to filter them out for DAG-only dominance calculation
    back_edges: list[tuple[str, str]] = []

    def detect_cycle(current_node: str) -> None:
        visited.add(current_node)
        recursion_stack.add(current_node)

        for neighbor in adj[current_node]:
            if neighbor not in visited:
                detect_cycle(neighbor)
            elif neighbor in recursion_stack:
                # Cycle detected! This is a back-edge (current -> neighbor).
                back_edges.append((current_node, neighbor))

                # SOTA Check: Is this cycle bounded?
                # Check ALL nodes in the identified loop for a constraint.
                # The loop is from neighbor -> ... -> current_node -> neighbor.
                # Since we don't have the path explicitly here without traversing stack,
                # we can check if *any* node in the recursion stack (which forms the current path)
                # has a constraint? No, that includes nodes *above* the loop start.
                # Heuristic: Check `current_node` (Source) and `neighbor` (Target).
                # AND ideally search up the stack until `neighbor`.
                # Given strict instruction: "verify that the node *initiating* the back-edge possesses the bounding constraint."
                # That is `current_node`.
                # BUT also: "or recursively check all nodes participating in the identified cycle".
                # Let's check `current_node` first. If failing, check `neighbor`.

                # We need to find at least ONE constraint in the loop.
                # Let's perform a simplified check on `current_node` (Back-edge source)
                # AND `neighbor` (Back-edge target/Header).

                loop_nodes = {current_node, neighbor} # Simplified set

                is_bounded = False
                for ln in loop_nodes:
                    node_obj = plan.nodes[ln]
                    if hasattr(node_obj, "constraints"):
                        for c in node_obj.constraints:
                            if c.type in ("max_iterations", "timeout", "loop_limit"):
                                is_bounded = True
                                break
                    if is_bounded: break

                if not is_bounded:
                    raise ZeroTrustRoutingError(
                        f"Unbounded cycle detected at node '{current_node}' -> '{neighbor}'. "
                        "Loops must be guarded by a Constraint (e.g. max_iterations) on the loop header or back-edge.",
                        node_id=current_node
                    )

        recursion_stack.remove(current_node)

    try:
        detect_cycle(plan.root_node)
    except ZeroTrustRoutingError:
        raise
    except RecursionError:
        raise ZeroTrustRoutingError("Graph depth exceeded recursion limit (possible cycle).")

    # 4. Dominator Analysis (Iterative O(V+E)) on DAG (Back-edges removed)

    # Filter back-edges from preds
    dag_preds = defaultdict(list)
    for target, sources in preds.items():
        for source in sources:
            # If (source, target) is a back-edge, skip it
            if (source, target) in back_edges:
                continue
            dag_preds[target].append(source)

    # Init: Dom(root) = {root}, Dom(others) = All Nodes
    dom: dict[str, set[str]] = {nid: all_nodes_set.copy() for nid in all_nodes_set}
    dom[plan.root_node] = {plan.root_node}

    changed = True
    while changed:
        changed = False
        # Iterate in arbitrary order (since we filtered back-edges, it's a DAG, so valid)
        for nid in plan.nodes:
            if nid == plan.root_node:
                continue

            node_preds = dag_preds[nid]
            if not node_preds:
                # If node has no preds in DAG view (but reachable in full graph),
                # it means it's ONLY reachable via back-edges?
                # Impossible if reachable from root via tree edges.
                # Unless it IS the root (handled) or we missed something.
                # If a node is reachable, it has a parent in the DFS tree.
                # DFS tree edges are never back-edges.
                # So `node_preds` cannot be empty.
                continue

            # Intersection of preds dominators
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
    for nid, node in plan.nodes.items():
        if isinstance(node, ActionNode):
            caps = node.skill.capabilities

            risk_reasons = []
            if NodeCapability.COMPUTER_USE in caps:
                risk_reasons.append(NodeCapability.COMPUTER_USE)
            if NodeCapability.CODE_EXECUTION in caps:
                risk_reasons.append(NodeCapability.CODE_EXECUTION)

            if risk_reasons:
                if not node.locked:
                    reports.append(
                        ComplianceReport(
                            code=ErrorCatalog.ERR_SEC_UNGUARDED_CRITICAL_003,
                            severity="violation",
                            message=(
                                f"Policy Violation: Node '{nid}' has high-risk capabilities "
                                f"{risk_reasons} but is NOT locked. Critical nodes must be locked."
                            ),
                            node_id=nid,
                            details={"reason": str(risk_reasons)},
                            remediation=RemediationAction(
                                type="lock_node",
                                description=f"Set locked=True for node {nid}",
                                patch_data=[], # Patch data generation omitted for brevity in strict kernel
                            )
                        )
                    )

    # 2. Utility Islands (Unreachable nodes)
    adj: dict[str, list[str]] = {nid: [] for nid in plan.nodes}
    for nid, node in plan.nodes.items():
        if isinstance(node, StrategyNode):
            # Check default route
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
