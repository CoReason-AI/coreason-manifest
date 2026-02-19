# src/coreason_manifest/utils/gatekeeper.py
from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from coreason_manifest.spec.core.flow import AnyNode, GraphFlow, LinearFlow
from coreason_manifest.spec.core.nodes import AgentNode, HumanNode, SwarmNode
from coreason_manifest.spec.interop.compliance import (
    ComplianceReport,
    ErrorCatalog,
    RemediationAction,
)

if TYPE_CHECKING:
    from coreason_manifest.spec.core.tools import ToolCapability


def validate_policy(flow: LinearFlow | GraphFlow) -> list[ComplianceReport]:
    """
    Enforces security policies and capability contracts.

    1. Capability Analysis: Ensures high-risk capabilities are declared.
    2. Topology Check (Red Button Rule): Critical nodes must be guarded by HumanNode.
    3. Swarm Safety: Recursively checks worker profiles in Swarms.
    4. Domain Policy: Checks tool URLs against allowed domains.
    5. Topology Analysis: Checks for hazardous utility islands using Tarjan's algorithm.
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

        if reasoning and hasattr(reasoning, "required_capabilities"):
            return reasoning.required_capabilities()
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
                # SOTA Fix: Handle schemeless URLs and strict netloc parsing
                url_to_parse = tool_obj.url
                if "://" not in url_to_parse:
                    url_to_parse = "https://" + url_to_parse

                parsed = urlparse(url_to_parse)
                domain = parsed.netloc.lower()
                if ":" in domain:
                    domain = domain.split(":")[0]

                allowed = False
                for allowed_d in allowed_domains:
                    if domain == allowed_d or domain.endswith("." + allowed_d):
                        allowed = True
                        break

                if allowed:
                    continue

                reports.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_SEC_DOMAIN_BLOCKED_002,
                        severity="violation",
                        message=f"Tool '{tool_obj.name}' uses blocked domain: {domain}",
                        details={"domain": domain, "tool_name": tool_obj.name},
                        remediation=RemediationAction(
                            type="whitelist_domain",
                            format="json_patch",
                            # JSON Patch for array update is complex if we don't know the index in tool_packs.
                            # For simplicity/robustness in this specific case,
                            # we might just describe the operation or assume appending to governance.
                            # Governance allowed_domains is a list.
                            patch_data=[{"op": "add", "path": "/governance/allowed_domains/-", "value": domain}],
                            description=f"Add '{domain}' to allowed_domains",
                        ),
                    )
                )

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
                metadata={},
            )

            # Construct Patch
            patch_ops = []
            if isinstance(flow, LinearFlow):
                # Find index
                idx = 0
                for i, n in enumerate(flow.sequence):
                    if n.id == node.id:
                        idx = i
                        break
                patch_ops.append({"op": "add", "path": f"/sequence/{idx}", "value": human_node.model_dump(mode="json")})
            elif isinstance(flow, GraphFlow):
                # For graph, we just add the node to the nodes map.
                # Rewiring edges is complex and context-dependent.
                patch_ops.append(
                    {"op": "add", "path": f"/graph/nodes/{human_node_id}", "value": human_node.model_dump(mode="json")}
                )

            reports.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_SEC_UNGUARDED_CRITICAL_003,
                    severity="violation",
                    message=(
                        f"Policy Violation: Node '{node.id}' requires high-risk features "
                        f"({', '.join(violation_reason)}) but is not guarded by a HumanNode."
                    ),
                    node_id=node.id,
                    details={"reason": ", ".join(violation_reason)},
                    remediation=RemediationAction(
                        type="add_guard_node",
                        target_node_id=node.id,
                        format="json_patch",
                        patch_data=patch_ops,
                        description=f"Insert HumanNode '{human_node_id}' before '{node.id}'",
                    ),
                )
            )

    # 5. Topology Analysis (GraphFlow Only)
    if isinstance(flow, GraphFlow):
        # Build Adjacency List
        adj: dict[str, list[str]] = {nid: [] for nid in flow.graph.nodes}
        for edge in flow.graph.edges:
            adj[edge.source].append(edge.target)

        # 5a. Tarjan's Algorithm for SCCs (Reachability Context)
        # While strict SCC isn't solely needed for "utility islands", it's the SOTA mandate for analysis.
        visited: set[str] = set()
        stack: list[str] = []
        on_stack: set[str] = set()
        ids: dict[str, int] = {}
        low: dict[str, int] = {}
        sccs: list[list[str]] = []
        id_counter = 0

        def dfs(at: str):
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

        # Run Tarjan's
        for node_id in flow.graph.nodes:
            if node_id not in visited:
                dfs(node_id)

        # Build map of node_id -> SCC info
        # If SCC has size > 1 or (size==1 and self loop), it's a cycle.
        node_cycle_map = {}
        for comp in sccs:
            is_cycle = False
            if len(comp) > 1:
                is_cycle = True
            elif len(comp) == 1:
                # Check self-loop
                node = comp[0]
                if node in adj.get(node, []):
                    is_cycle = True

            for nid in comp:
                node_cycle_map[nid] = is_cycle

        # 5b. Utility Island Detection (Unreachable from Entry)
        # Identify entry nodes (in-degree 0)
        in_degree = {nid: 0 for nid in flow.graph.nodes}
        for edge in flow.graph.edges:
            in_degree[edge.target] += 1

        entry_nodes = [nid for nid, d in in_degree.items() if d == 0]

        # BFS from entry nodes to find reachable set
        reachable = set(entry_nodes)
        queue = list(entry_nodes)

        while queue:
            curr = queue.pop(0)
            for neighbor in adj.get(curr, []):
                if neighbor not in reachable:
                    reachable.add(neighbor)
                    queue.append(neighbor)

        # Identify Unreachable Nodes
        all_nodes = set(flow.graph.nodes.keys())
        unreachable = all_nodes - reachable

        # 5c. Fail Open but Guarded
        for node_id in unreachable:
            node = flow.graph.nodes[node_id]
            caps = get_capabilities(node)

            # Check for high-risk capabilities
            risk_reasons = []
            if "computer_use" in caps:
                risk_reasons.append("computer_use")
            if "code_execution" in caps:
                risk_reasons.append("code_execution")

            if risk_reasons:
                is_cycle = node_cycle_map.get(node_id, False)
                structure_type = "cyclic island" if is_cycle else "island"

                reports.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_TOPOLOGY_UNREACHABLE_RISK_003,
                        severity="violation",
                        message=(
                            f"Topology Violation: Node '{node.id}' is unreachable ({structure_type}) "
                            f"but requires high-risk capabilities: {', '.join(risk_reasons)}."
                        ),
                        node_id=node.id,
                        details={
                            "reason": ", ".join(risk_reasons),
                            "component": "unreachable",
                            "structure": structure_type
                        },
                        remediation=RemediationAction(
                            type="prune_node",
                            target_node_id=node.id,
                            format="json_patch",
                            patch_data={"op": "remove", "path": f"/graph/nodes/{node.id}"},
                            description=f"Remove dangerous unreachable node '{node.id}'",
                        )
                    )
                )

    return reports


def _is_guarded(target_node: AnyNode, flow: LinearFlow | GraphFlow) -> bool:
    """
    Checks if the target node is topologically guarded by a HumanNode.
    Only HumanNode is a valid guard. SwitchNode is NOT a valid guard.
    """
    if isinstance(flow, LinearFlow):
        # Scan sequence backwards from target
        # SOTA Fix: Match by ID to verify identity, not just value equality
        target_idx = -1
        for i, node in enumerate(flow.sequence):
            if node.id == target_node.id:
                target_idx = i
                break

        if target_idx == -1:
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
            # If everything is a cycle, and no entry, it's ambiguous.
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
