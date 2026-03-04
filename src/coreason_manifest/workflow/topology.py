from coreason_manifest.telemetry.logger import logger
from coreason_manifest.workflow.flow import Edge, WorkflowEnvelope
from coreason_manifest.workflow.nodes import AnyNode


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


def get_unified_topology(envelope: WorkflowEnvelope) -> tuple[list[AnyNode], list[Edge]]:
    """Construct a unified, canonical graph representation from polymorphic workflow topologies.

    Implements SOTA Virtual Adjacency Synthesis. For edge-less topologies (Swarms, MoA, MapReduce),
    this middleware dynamically synthesizes virtual edges from access matrices and structural schemas.
    This normalizes the execution space for downstream security scanners, telemetry, and UI rendering.

    Complexity:
        Time: $O(V+E)$, constrained by the node extraction and virtual edge synthesis process.
        Space: $O(V+E)$, allocating memory for the canonical representation of the entire workflow.

    Args:
        envelope: The SOTA multi-agent WorkflowEnvelope containing a polymorphic topology.

    Returns:
        A strictly normalized tuple of sequential execution nodes and synthesized routing edges.
    """
    topology = envelope.topology
    nodes = list(topology.nodes.values())
    synthesized_edges: list[Edge] = []

    match topology.topology_type:
        case "dag" | "dcg":
            synthesized_edges = topology.edges

        case "swarm":
            # Synthesize edges from the dynamic Access Control matrix
            for source, targets in getattr(topology, "allowed_handoffs", {}).items():
                for target in targets:
                    synthesized_edges.append(Edge(from_node=source, to_node=target))

        case "moa":
            # Synthesize fan-out / fan-in edges for the Mixture-of-Agents layers
            layers = getattr(topology, "layers", [])
            aggregator = getattr(topology, "aggregator_agent", "")

            # Connect adjacent layers
            for i in range(len(layers) - 1):
                current_layer = layers[i]
                next_layer = layers[i + 1]
                for source in current_layer:
                    for target in next_layer:
                        synthesized_edges.append(Edge(from_node=source, to_node=target))

            # Connect the final layer to the aggregator
            if layers:
                final_layer = layers[-1]
                for source in final_layer:
                    synthesized_edges.append(Edge(from_node=source, to_node=aggregator))

        case "map_reduce":
            # Synthesize generic parallel pathways
            mapper = getattr(topology, "mapper_node_id", "")
            reducer = getattr(topology, "reducer_node_id", "")
            if mapper and reducer:
                synthesized_edges.append(Edge(from_node=mapper, to_node=reducer))

        case "hierarchical":
            # Synthesize edges from the supervisor to all worker nodes in the subgraph dictionary
            supervisor = getattr(topology, "entry_point", "")
            sub_flows = getattr(topology, "sub_flows", {})
            for worker_id in sub_flows:
                synthesized_edges.append(Edge(from_node=supervisor, to_node=worker_id))

        case "event_driven":
            # Event-Driven architectures are fundamentally disjointed graph islands.
            # They rely entirely on asynchronous Blackboard diffs, so no static edges exist.
            pass

        case _:
            raise ValueError(f"Unknown topology type: {topology.topology_type}. Cannot synthesize edges.")

    return nodes, synthesized_edges
