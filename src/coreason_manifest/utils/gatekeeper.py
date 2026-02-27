# src/coreason_manifest/utils/gatekeeper.py
from __future__ import annotations

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
    1. Cycle Detection: Raises fatal error on cycles (unless strictly guarded, but strict mode defaults to reject).
    2. Dominance Check: Ensures that ALL valid paths from root to any sink node MUST traverse
       every node marked `locked=True`.

    Args:
        plan: The strict execution plan.

    Raises:
        ZeroTrustRoutingError: If validation fails.
    """
    if not plan.nodes:
        raise ZeroTrustRoutingError("Plan is empty.")

    if plan.root_node not in plan.nodes:
        raise ZeroTrustRoutingError(f"Root node {plan.root_node} not found in plan.", node_id=plan.root_node)

    # 1. Build Adjacency List & Identify Locked Nodes
    adj: dict[str, list[str]] = {nid: [] for nid in plan.nodes}
    locked_nodes: set[str] = set()
    sinks: set[str] = set()

    for nid, node in plan.nodes.items():
        if isinstance(node, (ActionNode, StrategyNode)):
            if node.locked:
                locked_nodes.add(nid)

        has_outgoing = False
        if isinstance(node, StrategyNode):
            for route_target in node.routes.values():
                if route_target not in plan.nodes:
                    raise ZeroTrustRoutingError(
                        f"Strategy node {nid} routes to unknown node {route_target}.",
                        node_id=nid,
                    )
                adj[nid].append(route_target)
                has_outgoing = True

        # ActionNode is a sink (terminal) in this graph structure unless we implicitly chain?
        # Assuming ActionNode is a leaf or end of a branch.
        if not has_outgoing:
            sinks.add(nid)

    # 2. Cycle Detection (Strict)
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
                return True

        recursion_stack.remove(current_node)
        return False

    if detect_cycle(plan.root_node):
        raise ZeroTrustRoutingError("Unbounded cycles forbidden in Zero-Trust Kernel.")

    # 3. Path Dominance Check (Anti-Bypass)

    all_paths: list[list[str]] = []

    def find_paths(current: str, path: list[str]) -> None:
        path.append(current)
        if current in sinks or not adj[current]:
            all_paths.append(list(path))
        else:
            for neighbor in adj[current]:
                find_paths(neighbor, path)
        path.pop()

    find_paths(plan.root_node, [])

    if locked_nodes:
        for path in all_paths:
            path_set = set(path)
            missing = locked_nodes - path_set
            if missing:
                # We found a path that skips a locked node.
                # Violation!
                raise ZeroTrustRoutingError(
                    f"Path {'->'.join(path)} bypasses locked mandatory nodes: {missing}",
                    node_id=list(missing)[0]
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
            for target in node.routes.values():
                 if target in plan.nodes:
                     adj[nid].append(target)

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
