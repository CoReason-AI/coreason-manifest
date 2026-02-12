from typing import Any
from pydantic import BaseModel
from coreason_manifest.spec.core.flow import GraphFlow
from coreason_manifest.spec.core.nodes import (
    AgentNode, HumanNode, SwitchNode, CognitiveProfile
)
from coreason_manifest.spec.core.engines import ComputerUseReasoning
from coreason_manifest.spec.core.governance import Governance

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
                if isinstance(reasoning, ComputerUseReasoning) and "computer_use" not in allowed_caps:
                    violations.append(PolicyViolation(
                            node_id=node_id,
                            rule="Capability Check",
                            message=f"Node '{node_id}' uses 'computer_use' but it is not in allowed_capabilities."
                        ))

    # Rule 2: Topology Check (Red Button)
    for node_id, node in nodes.items():
        risk = node.metadata.get("risk_level")
        if risk == "critical":
            # Check ancestry for HumanNode or SwitchNode
            ancestors = set()
            queue = [node_id]
            visited = {node_id}
            has_guard = False

            while queue:
                curr = queue.pop(0)
                for parent_id in upstream_adj.get(curr, []):
                    if parent_id not in visited:
                        visited.add(parent_id)
                        ancestors.add(parent_id)
                        parent_node = nodes[parent_id]
                        if isinstance(parent_node, (HumanNode, SwitchNode)):
                            has_guard = True
                            break
                        queue.append(parent_id)
                if has_guard:
                    break

            if not has_guard:
                 violations.append(PolicyViolation(
                    node_id=node_id,
                    rule="Topology Check",
                    message=f"Critical node '{node_id}' lacks a HumanNode or SwitchNode in its ancestry."
                ))

    return violations
