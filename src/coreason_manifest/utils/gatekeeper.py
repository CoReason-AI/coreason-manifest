from pydantic import BaseModel

from coreason_manifest.spec.core.flow import GraphFlow, AnyNode
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile, HumanNode, SwitchNode


class PolicyViolation(BaseModel):
    node_id: str
    rule: str
    message: str
    severity: str = "error"


def validate_policy(flow: GraphFlow) -> list[PolicyViolation]:
    """
    Validates a GraphFlow against its Governance policy.
    """
    violations = []

    # Check if governance exists
    if not flow.governance or not flow.governance.policy:
        return []

    policy = flow.governance.policy
    allowed_caps = set(policy.allowed_capabilities)

    # Build graph helpers
    nodes = flow.graph.nodes
    edges = flow.graph.edges

    # Adjacency list for upstream traversal (Reverse Graph)
    upstream_adj: dict[str, list[str]] = {nid: [] for nid in nodes}
    for edge in edges:
        if edge.target in upstream_adj:
            upstream_adj[edge.target].append(edge.source)

    # Rule 1: Capability Check
    for node_id, node in nodes.items():
        if isinstance(node, AgentNode):
            profile = node.profile
            # Resolve profile if string
            if isinstance(profile, str):
                if flow.definitions and profile in flow.definitions.profiles:
                    profile = flow.definitions.profiles[profile]
                else:
                    # Missing profile definition is referential integrity issue
                    continue

            if isinstance(profile, CognitiveProfile) and profile.reasoning:
                reasoning = profile.reasoning
                # Use extensible capability check
                if hasattr(reasoning, "required_capabilities"):
                    req_caps = reasoning.required_capabilities()
                    for cap in req_caps:
                        if cap not in allowed_caps:
                            violations.append(
                                PolicyViolation(
                                    node_id=node_id,
                                    rule="Capability Check",
                                    message=f"Node '{node_id}' uses '{cap}' but it is not in allowed_capabilities.",
                                )
                            )

    # Rule 2: Topology Check (The SOTA Red Button)
    # Identify Critical Nodes
    critical_nodes = [
        nid for nid, n in nodes.items()
        if n.metadata.get("risk_level") == "critical"
    ]

    for target_id in critical_nodes:
        # DFS to find ANY path to a root that does NOT pass through a guard
        # State: (current_node, path_trace)
        stack = [(target_id, [target_id])]

        # We need to track visited for the current DFS path to avoid cycles,
        # but also globally if we want to optimize.
        # For simplicity and correctness with "path trace", we check path membership.

        while stack:
            curr_id, path = stack.pop()

            # 1. Stop if we hit a Guard (This path is safe)
            # IMPORTANT: The target node itself cannot be its own upstream guard unless it's a SwitchNode acting as a gate?
            # Usually the guard is *before* the critical action.
            # If the critical node is ITSELF a HumanNode, is it guarded? Yes.
            curr_node = nodes[curr_id]
            if isinstance(curr_node, (HumanNode, SwitchNode)):
                # If we hit a guard, this path is secured. We stop traversing this branch.
                # NOTE: If target_id IS a HumanNode, it is safe.
                continue

            # 2. Get parents
            parents = upstream_adj.get(curr_id, [])

            # 3. If no parents, we reached a ROOT without hitting a guard -> VIOLATION
            if not parents:
                # We found an exposed root!
                violations.append(PolicyViolation(
                    node_id=target_id,
                    rule="Topology Check",
                    message=f"Critical node '{target_id}' is accessible via unguarded path: {' <- '.join(path)}"
                ))
                # Break to avoid duplicate violations for the same node
                break

            # 4. Continue searching upstream
            for pid in parents:
                if pid not in path: # simple cycle avoidance
                    stack.append((pid, path + [pid]))

    return violations
