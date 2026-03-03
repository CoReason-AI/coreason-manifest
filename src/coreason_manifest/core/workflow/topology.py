from coreason_manifest.core.workflow.flow import Edge, GraphFlow, LinearFlow
from coreason_manifest.core.workflow.nodes import AnyNode
from coreason_manifest.utils.logger import logger


def get_strongly_connected_components(adj: dict[str, list[str]]) -> list[list[str]]:
    """Identify strongly connected components within a workflow graph using Tarjan's algorithm.

    This algorithm is heuristically leveraged to detect cycles, deadlocks, and
    isolated utility islands within complex agentic workflows, enabling robust
    structural validation and reachability context analysis.

    Complexity:
        Time: $O(V+E)$, where $V$ is the number of vertices and $E$ is the number of edges.
        Space: $O(V)$, auxiliary space utilized by the recursion stack and state tracking structures.

    Args:
        adj: The adjacency list mapping each node identifier to its direct outgoing successors.

    Returns:
        A collection of grouped node identifiers, each representing a discrete, strongly connected component.
    """
    visited: set[str] = set()
    stack: list[str] = []
    on_stack: set[str] = set()
    ids: dict[str, int] = {}
    low: dict[str, int] = {}
    sccs: list[list[str]] = []
    id_counter = 0

    def dfs(at: str) -> None:
        """Execute a depth-first traversal to discover components and identify back-edges.

        Recursively explores the workflow topology, tracking discovery times and lowest
        reachable ancestral nodes to isolate cycles within the execution graph.

        Complexity:
            Time: $O(V+E)$, processing each node and edge exactly once across the graph.
            Space: $O(V)$, bounded by the maximum depth of the graph topology on the call stack.

        Args:
            at: The unique identifier of the node currently being traversed.
        """
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

    logger.debug("detected_strongly_connected_components", component_count=len(sccs))
    return sccs


def get_reachable_nodes(adj: dict[str, list[str]], entry_nodes: list[str]) -> set[str]:
    """Determine the exhaustive set of reachable nodes from specified entry points using Breadth-First Search.

    This search guarantees topological integrity by mapping the valid execution space.
    It isolates dead code or unreachable utility islands which may pose security risks
    or indicate architectural flaws within the workflow definition.

    Complexity:
        Time: $O(V+E)$, strictly traversing accessible nodes and their respective edges.
        Space: $O(V)$, maintaining the visited set and the exploration queue.

    Args:
        adj: The adjacency list mapping each node identifier to its outgoing successors.
        entry_nodes: The collection of node identifiers acting as starting execution points.

    Returns:
        The universally unique identifiers for all execution nodes accessible from the defined entry points.
    """
    reachable = set(entry_nodes)
    queue = list(entry_nodes)

    while queue:
        curr = queue.pop(0)
        for neighbor in adj.get(curr or "", []):
            if neighbor not in reachable:
                reachable.add(neighbor)
                queue.append(neighbor)

    logger.debug("detected_reachable_nodes", entry_count=len(entry_nodes), reachable_count=len(reachable))
    return reachable


def get_unified_topology(flow: LinearFlow | GraphFlow) -> tuple[list[AnyNode], list[Edge]]:
    """Construct a unified, canonical graph representation from disparate flow definitions.

    This abstraction layer normalizes sequential and explicitly defined graph flows
    into a cohesive node-edge topology, allowing unified downstream algorithmic processing,
    policy validation, and static analysis without divergent logic paths.

    Complexity:
        Time: $O(V+E)$, constrained by the node extraction and edge synthesis process.
        Space: $O(V+E)$, allocating memory for the canonical representation of the entire workflow.

    Args:
        flow: The execution flow object containing either a sequential or graph-based routing structure.

    Returns:
        A strictly normalized tuple containing the sequential collection of execution nodes and the synthesized routing edges.
    """  # noqa: E501
    if isinstance(flow, GraphFlow):
        return list(flow.graph.nodes.values()), flow.graph.edges
    if isinstance(flow, LinearFlow):
        nodes = flow.steps
        edges = [Edge(from_node=nodes[i].id, to_node=nodes[i + 1].id) for i in range(len(nodes) - 1)]
        return nodes, edges
    # Raise error for unknown flow types to ensure strict typing/handling
    raise ValueError(f"Unknown flow type: {type(flow)}. Expected LinearFlow or GraphFlow.")
