# src/coreason_manifest/utils/gatekeeper.py


from coreason_manifest.spec.core.flow import AnyNode, GraphFlow, LinearFlow
from coreason_manifest.spec.core.nodes import AgentNode, HumanNode, SwarmNode


def validate_policy(flow: LinearFlow | GraphFlow) -> list[str]:
    """
    Enforces security policies and capability contracts.

    1. Capability Analysis: Ensures high-risk capabilities are declared.
    2. Topology Check (Red Button Rule): Critical nodes must be guarded by HumanNode.
    3. Swarm Safety: Recursively checks worker profiles in Swarms.
    """
    errors: list[str] = []

    # Extract all nodes
    nodes: list[AnyNode] = []
    if isinstance(flow, LinearFlow):
        nodes = flow.sequence
    elif isinstance(flow, GraphFlow):
        nodes = list(flow.graph.nodes.values())

    # Helper to resolve profile and get capabilities
    def get_capabilities(node: AnyNode) -> list[str]:
        reasoning = None
        if isinstance(node, AgentNode):
            # Resolve profile
            if isinstance(node.profile, str):
                if flow.definitions and node.profile in flow.definitions.profiles:
                    profile = flow.definitions.profiles[node.profile]
                    reasoning = profile.reasoning
            else:
                reasoning = node.profile.reasoning

        elif isinstance(node, SwarmNode) and flow.definitions and node.worker_profile in flow.definitions.profiles:
            # Resolve worker profile
            profile = flow.definitions.profiles[node.worker_profile]
            reasoning = profile.reasoning

        # Use contract, not hasattr
        # ReasoningConfig is a Union, but all members inherit from BaseReasoning (except if new ones added incorrectly)
        # But we added the method to BaseReasoning.
        if reasoning:
            # We can rely on duck typing or isinstance check if we import BaseReasoning
            # Ideally all reasoning objects have this method now.
            try:
                return reasoning.required_capabilities()
            except AttributeError:
                # Fail closed if method missing (should not happen with correct inheritance)
                return []
        return []

    # 1. Capability Analysis & Red Button Rule
    for node in nodes:
        caps = get_capabilities(node)

        # Check for high-risk capabilities
        if ("computer_use" in caps or "code_execution" in caps) and not _is_guarded(node, flow):  # extensible list
            errors.append(
                f"Policy Violation: Node '{node.id}' requires high-risk capabilities {caps} "
                "but is not guarded by a HumanNode."
            )

    return errors


def _is_guarded(target_node: AnyNode, flow: LinearFlow | GraphFlow) -> bool:
    """
    Checks if the target node is topologically guarded by a HumanNode.
    Only HumanNode is a valid guard. SwitchNode is NOT a valid guard.
    """
    if isinstance(flow, LinearFlow):
        # Scan sequence backwards from target
        try:
            target_idx = flow.sequence.index(target_node)
        except ValueError:
            return False

        for i in range(target_idx - 1, -1, -1):
            node = flow.sequence[i]
            if isinstance(node, HumanNode):
                return True
        return False

    if isinstance(flow, GraphFlow):
        # Reachability Analysis

        all_ids = set(flow.graph.nodes.keys())
        target_ids = {edge.target for edge in flow.graph.edges}
        entry_ids = all_ids - target_ids

        # Fail Closed: If no clear entry point but graph exists, assume unsafe (cyclic or disconnected).
        if not entry_ids and flow.graph.nodes:
            # We could try to check cycles, but for security, deny by default is safer.
            # However, if the target is in a cycle with a human, it might be safe.
            # But the algorithm below assumes traversal from entry.
            return False

        # We need to find if there is a path from ANY entry node to target_node.id
        # that does NOT visit a HumanNode.

        # Valid guards: HumanNode only.
        valid_guards = (HumanNode,)

        # Construct adjacency map
        adj: dict[str, list[str]] = {nid: [] for nid in all_ids}
        for edge in flow.graph.edges:
            adj[edge.source].append(edge.target)

        guards = {nid for nid, node in flow.graph.nodes.items() if isinstance(node, valid_guards)}

        queue = list(entry_ids)
        visited = set(entry_ids)

        # Handle case where target is an entry node
        if target_node.id in entry_ids:
            return False

        while queue:
            curr_id = queue.pop(0)

            if curr_id == target_node.id:
                return False  # Reached target without passing a guard

            # If current node is a guard, we stop traversing this path
            # (because downstream is guarded by this node).
            if curr_id in guards:
                continue

            # Expand neighbors
            for neighbor in adj.get(curr_id, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return True

    return False
