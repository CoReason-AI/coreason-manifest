from coreason_manifest.spec.core.flow import EdgeSpec, FlowSpec
from coreason_manifest.spec.core.contracts import NodeSpec
from coreason_manifest.spec.interop.exceptions import (
    FaultSeverity,
    ManifestError,
    RecoveryAction,
    SemanticFault,
)


class TopologyValidationError(ManifestError):
    """Raised when the flow topology violates structural constraints."""

    pass


def get_reachable_nodes(adj: dict[str, list[str]], entry_nodes: list[str]) -> set[str]:
    """BFS to find all nodes reachable from the entry points."""
    reachable = set(entry_nodes)
    queue = list(entry_nodes)

    while queue:
        curr = queue.pop(0)
        for neighbor in adj.get(curr or "", []):
            if neighbor not in reachable:
                reachable.add(neighbor)
                queue.append(neighbor)

    return reachable


def get_unified_topology(flow: FlowSpec) -> tuple[list[NodeSpec], list[EdgeSpec]]:
    """
    Returns a unified view of the flow topology (nodes and edges).
    """
    return list(flow.graph.nodes.values()), flow.graph.edges


def validate_topology(flow: FlowSpec) -> None:
    """
    Statically compiles and validates the flow topology.
    Enforces:
    1. Referential integrity (all edges point to valid nodes).
    2. Reachability (all nodes reachable from entry point in GraphFlow).
    3. Acyclicity (no infinite loops, unless explicitly handled - currently strict DAG).
    """
    nodes, edges = get_unified_topology(flow)
    node_ids = {node.id for node in nodes}

    # 1. Referential Integrity
    for edge in edges:
        if edge.from_node not in node_ids:
            raise TopologyValidationError(
                SemanticFault(
                    error_code="CRSN_VAL_TOPOLOGY_INVALID",
                    message=f"Edge source '{edge.from_node}' does not exist in the graph.",
                    severity=FaultSeverity.CRITICAL,
                    recovery_action=RecoveryAction.HALT,
                )
            )
        if edge.to_node not in node_ids:
            raise TopologyValidationError(
                SemanticFault(
                    error_code="CRSN_VAL_TOPOLOGY_INVALID",
                    message=f"Edge target '{edge.to_node}' does not exist in the graph.",
                    severity=FaultSeverity.CRITICAL,
                    recovery_action=RecoveryAction.HALT,
                )
            )

    # Build Adjacency List
    adj = {node_id: [] for node_id in node_ids}
    for edge in edges:
        adj[edge.from_node].append(edge.to_node)

    # 2. Reachability
    if flow.graph.entry_point:
        entry_point = flow.graph.entry_point
        if entry_point not in node_ids:
            raise TopologyValidationError(
                SemanticFault(
                    error_code="CRSN_VAL_ENTRY_POINT_MISSING",
                    message=f"Entry point '{entry_point}' not found in nodes.",
                    severity=FaultSeverity.CRITICAL,
                    recovery_action=RecoveryAction.HALT,
                )
            )

        reachable = get_reachable_nodes(adj, [entry_point])
        unreachable = node_ids - reachable
        if unreachable:
            # Sort for deterministic error message
            sorted_unreachable = sorted(list(unreachable))
            raise TopologyValidationError(
                SemanticFault(
                    error_code="CRSN_VAL_TOPOLOGY_UNREACHABLE",
                    message=f"Unreachable nodes detected: {sorted_unreachable}",
                    severity=FaultSeverity.CRITICAL,
                    recovery_action=RecoveryAction.HALT,
                )
            )

    # 3. Cycle Detection (Bounded Loop Contract)
    # We use DFS to find back-edges.

    # Map (from, to) -> EdgeSpec to check constraints easily
    edge_map = {}
    for edge in edges:
        key = (edge.from_node, edge.to_node)
        if key not in edge_map:
            edge_map[key] = []
        edge_map[key].append(edge)

    visited = set()
    path_stack = set()

    def dfs_cycle_check(current_node: str) -> None:
        visited.add(current_node)
        path_stack.add(current_node)

        for neighbor in adj.get(current_node, []):
            if neighbor in path_stack:
                # Cycle detected. Back-edge is current_node -> neighbor.
                # Check constraints on edges (current_node, neighbor)
                edges_between = edge_map.get((current_node, neighbor), [])
                is_bounded = False
                for e in edges_between:
                    if e.max_iterations is not None or e.timeout is not None:
                        is_bounded = True
                        break

                if not is_bounded:
                    raise TopologyValidationError(
                        SemanticFault(
                            error_code="CRSN_VAL_TOPOLOGY_CYCLE",
                            message=f"Unbounded infinite loop detected: {current_node} -> {neighbor}. Back-edge requires 'max_iterations' or 'timeout'.",
                            severity=FaultSeverity.CRITICAL,
                            recovery_action=RecoveryAction.HALT,
                        )
                    )
            elif neighbor not in visited:
                dfs_cycle_check(neighbor)

        path_stack.remove(current_node)

    # Run DFS from entry point first to establish canonical direction
    if flow.graph.entry_point and flow.graph.entry_point in node_ids:
        dfs_cycle_check(flow.graph.entry_point)

    # Then visit any remaining nodes (disjoint components)
    for node_id in sorted(node_ids):
        if node_id not in visited:
            dfs_cycle_check(node_id)
