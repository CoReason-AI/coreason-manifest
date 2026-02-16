# src/coreason_manifest/utils/gatekeeper.py
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel

from coreason_manifest.spec.core.flow import AnyNode, GraphFlow, LinearFlow
from coreason_manifest.spec.core.nodes import AgentNode, HumanNode, SwarmNode

if TYPE_CHECKING:
    from coreason_manifest.spec.core.tools import ToolCapability


class RemediationAction(BaseModel):
    type: Literal["add_guard_node", "whitelist_domain"]
    target_node_id: str | None = None
    patch_data: dict[str, Any]
    description: str


class ComplianceReport(BaseModel):
    severity: Literal["violation", "warning", "info"]
    message: str
    node_id: str | None = None
    remediation: RemediationAction | None = None


def validate_policy(flow: LinearFlow | GraphFlow) -> list[ComplianceReport]:
    """
    Enforces security policies and capability contracts.

    1. Capability Analysis: Ensures high-risk capabilities are declared.
    2. Topology Check (Red Button Rule): Critical nodes must be guarded by HumanNode.
    3. Swarm Safety: Recursively checks worker profiles in Swarms.
    4. Domain Policy: Checks tool URLs against allowed domains.
    """
    reports: list[ComplianceReport] = []

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

        if reasoning:
            try:
                return reasoning.required_capabilities()
            except AttributeError:
                return []
        return []

    # Build tool map: name -> tool_object
    tool_map: dict[str, ToolCapability] = {}
    if flow.definitions and flow.definitions.tool_packs:
        for pack in flow.definitions.tool_packs.values():
            for tool in pack.tools:
                tool_map[tool.name] = tool

    # 0. Domain Policy Check
    allowed_domains = []
    if flow.governance and flow.governance.allowed_domains:
        allowed_domains = flow.governance.allowed_domains

    if allowed_domains:
        for tool_obj in tool_map.values():
            if tool_obj.url:
                parsed = urlparse(tool_obj.url)
                domain = parsed.netloc.lower() or tool_obj.url.lower().rstrip("/")

                allowed = False
                for allowed_d in allowed_domains:
                    if domain == allowed_d or domain.endswith("." + allowed_d):
                        allowed = True
                        break

                if not allowed:
                    reports.append(ComplianceReport(
                        severity="violation",
                        message=f"Tool '{tool_obj.name}' uses blocked domain: {domain}",
                        remediation=RemediationAction(
                            type="whitelist_domain",
                            patch_data={"domain": domain},
                            description=f"Add '{domain}' to allowed_domains"
                        )
                    ))

    # 1. Capability Analysis & Red Button Rule
    for node in nodes:
        caps = get_capabilities(node)

        # Check tool risks for AgentNode
        critical_tools = []
        if isinstance(node, AgentNode):
            for tool_name in node.tools:
                resolved_tool = tool_map.get(tool_name)
                risk = resolved_tool.risk_level if resolved_tool else "standard"
                if risk == "critical":
                    critical_tools.append(tool_name)

        # Check for high-risk capabilities
        needs_guard = False
        violation_reason = []

        if "computer_use" in caps:
            needs_guard = True
            violation_reason.append("computer_use capability")
        if "code_execution" in caps:
            needs_guard = True
            violation_reason.append("code_execution capability")

        if critical_tools:
            needs_guard = True
            violation_reason.append(f"critical tools {critical_tools}")

        if needs_guard and not _is_guarded(node, flow):
            human_node_id = f"guard_{node.id}"
            human_node = HumanNode(
                id=human_node_id,
                type="human",
                prompt=f"Approve unsafe action by {node.id}",
                timeout_seconds=300,
                interaction_mode="blocking",
                metadata={}
            )

            reports.append(ComplianceReport(
                severity="violation",
                message=(
                    f"Policy Violation: Node '{node.id}' requires high-risk features "
                    f"({', '.join(violation_reason)}) but is not guarded by a HumanNode."
                ),
                node_id=node.id,
                remediation=RemediationAction(
                    type="add_guard_node",
                    target_node_id=node.id,
                    patch_data=human_node.model_dump(mode="json"),
                    description=f"Insert HumanNode '{human_node_id}' before '{node.id}'"
                )
            ))

    return reports


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
