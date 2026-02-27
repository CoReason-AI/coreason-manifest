from coreason_manifest.spec.core.flow import Edge, GraphFlow, LinearFlow
from coreason_manifest.spec.core.nodes import AnyNode
from coreason_manifest.spec.interop.exceptions import (
    FaultSeverity,
    ManifestError,
    RecoveryAction,
    SemanticFault,
)


class TopologyValidationError(ManifestError):
    """Raised when the flow topology violates structural constraints."""

    pass


def get_strongly_connected_components(adj: dict[str, list[str]]) -> list[list[str]]:
    """Tarjan's algorithm to find strongly connected components."""
    visited: set[str] = set()
    stack: list[str] = []
    on_stack: set[str] = set()
    ids: dict[str, int] = {}
    low: dict[str, int] = {}
    sccs: list[list[str]] = []
    id_counter = 0

    def dfs(at: str) -> None:
        nonlocal id_counter
        stack.append(at)
        on_stack.add(at)
        visited.add(at)
        ids[at] = low[at] = id_counter
        id_counter += 1

        for to in adj.get(at, []):
            if to not in visited:
                dfs(to)
                low[at] = min(low[at], low[to])
            elif to in on_stack:
                low[at] = min(low[at], ids[to])

        if ids[at] == low[at]:
            component = []
            while stack:
                node = stack.pop()
                on_stack.remove(node)
                component.append(node)
                if node == at:
                    break
            sccs.append(component)

    for node_id in adj:
        if node_id not in visited:
            dfs(node_id)

    return sccs


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


def get_unified_topology(flow: LinearFlow | GraphFlow) -> tuple[list[AnyNode], list[Edge]]:
    """
    Returns a unified view of the flow topology (nodes and edges).
    For LinearFlow, it generates implicit edges between sequential steps.
    """
    if isinstance(flow, GraphFlow):
        return list(flow.graph.nodes.values()), flow.graph.edges
    if isinstance(flow, LinearFlow):
        nodes = flow.steps
        # Use model_construct to bypass validation for generated edges
        # This is important for testing scenarios where node IDs might be invalid (e.g. escaping tests)
        edges = [Edge.model_construct(from_node=nodes[i].id, to_node=nodes[i + 1].id) for i in range(len(nodes) - 1)]
        return nodes, edges
    # Raise error for unknown flow types to ensure strict typing/handling
    raise ValueError(f"Unknown flow type: {type(flow)}. Expected LinearFlow or GraphFlow.")


def validate_topology(flow: GraphFlow | LinearFlow) -> None:
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

    # 2. Reachability (GraphFlow only)
    if isinstance(flow, GraphFlow) and flow.graph.entry_point:
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

    # 3. Cycle Detection
    sccs = get_strongly_connected_components(adj)
    for scc in sccs:
        # A component has a cycle if it has > 1 node, or 1 node with a self-loop
        has_cycle = False
        if len(scc) > 1:
            has_cycle = True
        elif len(scc) == 1:
            node = scc[0]
            if node in adj[node]:
                has_cycle = True

        if has_cycle:
            raise TopologyValidationError(
                SemanticFault(
                    error_code="CRSN_VAL_TOPOLOGY_CYCLE",
                    message=f"Infinite loop detected involving nodes: {sorted(scc)}",
                    severity=FaultSeverity.CRITICAL,
                    recovery_action=RecoveryAction.HALT,
                )
            )
