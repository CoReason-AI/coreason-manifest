from coreason_manifest.core.workflow.flow import Edge, GraphFlow, LinearFlow
from coreason_manifest.core.workflow.nodes import AnyNode


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
