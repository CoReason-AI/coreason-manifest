# src/coreason_manifest/utils/gatekeeper.py
from __future__ import annotations

from typing import TYPE_CHECKING, cast

from coreason_manifest.spec.core.flow import AnyNode, GraphFlow, LinearFlow
from coreason_manifest.spec.core.nodes import AgentNode, HumanNode, SwarmNode
from coreason_manifest.spec.interop.compliance import (
    ComplianceReport,
    ErrorCatalog,
    RemediationAction,
)
from coreason_manifest.utils.net_utils import canonicalize_domain

if TYPE_CHECKING:
    from coreason_manifest.spec.core.tools import ToolCapability


def validate_policy(flow: LinearFlow | GraphFlow) -> list[ComplianceReport]:
    """
    Enforces security policies and capability contracts.

    1. Capability Analysis: Ensures high-risk capabilities are declared.
    2. Topology Check (Red Button Rule): Critical nodes must be guarded by HumanNode.
    3. Swarm Safety: Recursively checks worker profiles in Swarms.
    4. Domain Policy: Checks tool URLs against allowed domains (Strict Canonicalization).
    5. Topology Analysis: Checks for hazardous utility islands using Tarjan's algorithm.
    """
    reports: list[ComplianceReport] = []

    # Extract all nodes
    nodes: list[AnyNode] = []
    if isinstance(flow, LinearFlow):
        nodes = flow.steps
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
            return cast("list[str]", reasoning.required_capabilities())
        return []

    # Build tool map: name -> tool_object
    tool_map: dict[str, ToolCapability] = {}
    if flow.definitions and flow.definitions.tool_packs:
        for pack in flow.definitions.tool_packs.values():
            for tool in pack.tools:
                tool_map[tool.name] = tool

    # 0. Domain Policy Check (Pillar 3: High-Fidelity URI Governance)
    allowed_domains_raw = []
    if flow.governance and flow.governance.allowed_domains:
        allowed_domains_raw = flow.governance.allowed_domains

    # Canonicalize allowed domains
    allowed_domains = {canonicalize_domain(d) for d in allowed_domains_raw}

    if allowed_domains:
        for tool_obj in tool_map.values():
            # Architectural Note: Utilize strict Pydantic HttpUrl object instead of manual string parsing
            if tool_obj.url and tool_obj.url.host:
                domain_raw = str(tool_obj.url.host)
                domain = canonicalize_domain(domain_raw)

                allowed = False
                for allowed_d in allowed_domains:
                    # Exact match or subdomain
                    if domain == allowed_d or (domain and domain.endswith("." + allowed_d)):
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
                # Fix 3: Fail-Open Vulnerability - Default to 'critical' if unknown
                risk = resolved_tool.risk_level if resolved_tool else "critical"
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
                for i, n in enumerate(flow.steps):
                    if n.id == node.id:
                        idx = i
                        break
                patch_ops.append({"op": "add", "path": f"/sequence/{idx}", "value": human_node.model_dump(mode="json")})
            elif isinstance(flow, GraphFlow):
                # Fix 1: Ghost Guard Graph Injection Failure - Rewire edges

                # 1. Add Guard Node
                patch_ops.append(
                    {"op": "add", "path": f"/graph/nodes/{human_node_id}", "value": human_node.model_dump(mode="json")}
                )

                # 2. Rewire incoming edges (Target -> Guard)
                for edge_idx, edge in enumerate(flow.graph.edges):
                    if edge.to_node == node.id:
                        patch_ops.append(
                            {"op": "replace", "path": f"/graph/edges/{edge_idx}/target", "value": human_node_id}
                        )

                # 3. Add edge (Guard -> Target)
                patch_ops.append(
                    {"op": "add", "path": "/graph/edges/-", "value": {"source": human_node_id, "target": node.id}}
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
            # SOTA Fix 1: Defensive check for Draft Mode Fatality
            if edge.from_node in adj:
                adj[edge.from_node].append(edge.to_node)

        # 5a. Tarjan's Algorithm for SCCs (Reachability Context)
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

        # Run Tarjan's
        for node_id in flow.graph.nodes:
            if node_id not in visited:
                dfs(node_id)

        # Build map of node_id -> SCC info
        node_cycle_map = {}
        for comp in sccs:
            is_cycle = False
            if len(comp) > 1:
                is_cycle = True
            elif len(comp) == 1:
                node_id_in_comp = comp[0]
                if node_id_in_comp in adj.get(node_id_in_comp, []):
                    is_cycle = True

            for nid in comp:
                node_cycle_map[nid] = is_cycle

        # 5b. Utility Island Detection (Unreachable from Entry)
        # Architectural Note: Use explicit entry point
        entry_nodes = []
        if flow.graph.entry_point:
            entry_nodes.append(flow.graph.entry_point)

        # BFS from entry nodes to find reachable set
        reachable = set(entry_nodes)
        queue = list(entry_nodes)

        while queue:
            curr = queue.pop(0)
            # Mypy fix: handle None key (if curr is None? no entry_nodes are str)
            # but adj dict expects str.
            for neighbor in adj.get(curr or "", []):
                if neighbor not in reachable:
                    reachable.add(neighbor)
                    queue.append(neighbor)

        # Identify Unreachable Nodes
        all_nodes = set(flow.graph.nodes.keys())
        unreachable = all_nodes - reachable

        # Fix 2: Sequential Patch Index Corruption - Aggregate ALL unreachable nodes
        if unreachable:
            safe_node_ids = set()
            dangerous_node_ids = set()
            risk_details = {}  # Map node_id -> list of risk reasons

            for node_id in unreachable:
                node = flow.graph.nodes[node_id]
                caps = get_capabilities(node)

                risk_reasons = []
                if "computer_use" in caps:
                    risk_reasons.append("computer_use")
                if "code_execution" in caps:
                    risk_reasons.append("code_execution")

                if risk_reasons:
                    dangerous_node_ids.add(node_id)
                    risk_details[node_id] = risk_reasons
                else:
                    safe_node_ids.add(node_id)

            # Gather all edges connected to ANY unreachable node
            bulk_edge_indices = set()
            for idx, edge in enumerate(flow.graph.edges):
                if edge.from_node in unreachable or edge.to_node in unreachable:
                    bulk_edge_indices.add(idx)

            # Sort descending to prevent index invalidation during sequential removal
            sorted_edge_indices = sorted(bulk_edge_indices, reverse=True)

            patch_list = []
            # 1. Remove Edges (must be done by index, high to low)
            patch_list.extend([{"op": "remove", "path": f"/graph/edges/{idx}"} for idx in sorted_edge_indices])

            # 2. Remove Nodes (by key, safe order)
            patch_list.extend([{"op": "remove", "path": f"/graph/nodes/{node_id}"} for node_id in unreachable])

            if dangerous_node_ids:
                # Severity violation if any dangerous nodes are present
                reports.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_TOPOLOGY_UNREACHABLE_RISK_003,
                        severity="violation",
                        message=(
                            f"Topology Violation: Found {len(dangerous_node_ids)} dangerous unreachable nodes "
                            f"and {len(safe_node_ids)} dead code nodes. "
                            "Pruning all unreachable topology to restore integrity."
                        ),
                        details={
                            "dangerous_nodes": list(dangerous_node_ids),
                            "safe_nodes": list(safe_node_ids),
                            "risk_details": risk_details,
                        },
                        remediation=RemediationAction(
                            type="prune_topology",
                            format="json_patch",
                            patch_data=patch_list,
                            description=(
                                f"Atomic Prune: Remove {len(unreachable)} unreachable nodes "
                                f"and {len(sorted_edge_indices)} connected edges."
                            ),
                        ),
                    )
                )
            elif safe_node_ids:
                # Just warning if only safe nodes
                reports.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_TOPOLOGY_ORPHAN_001,
                        severity="warning",
                        message=f"Topology Warning: Found {len(safe_node_ids)} unreachable nodes (Dead Code).",
                        details={"node_ids": list(safe_node_ids)},
                        remediation=RemediationAction(
                            type="prune_node",
                            format="json_patch",
                            patch_data=patch_list,
                            description=(
                                f"Tree Shake: Remove {len(safe_node_ids)} dead code nodes "
                                f"and {len(sorted_edge_indices)} edges."
                            ),
                        ),
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
        # Architectural Note: Match by ID to verify identity, not just value equality
        target_idx = -1
        for i, node in enumerate(flow.steps):
            if node.id == target_node.id:
                target_idx = i
                break

        if target_idx == -1:
            return False

        for i in range(target_idx - 1, -1, -1):
            node = flow.steps[i]
            if isinstance(node, HumanNode):
                return True
        return False

    if isinstance(flow, GraphFlow):
        # Reachability Analysis

        all_ids = set(flow.graph.nodes.keys())
        entry_id = flow.graph.entry_point

        # Valid guards: HumanNode only.
        valid_guards = (HumanNode,)

        # Construct adjacency map
        adj: dict[str, list[str]] = {nid: [] for nid in all_ids}
        for edge in flow.graph.edges:
            adj[edge.from_node].append(edge.to_node)

        guards = {nid for nid, node in flow.graph.nodes.items() if isinstance(node, valid_guards)}

        if entry_id:
            queue = [entry_id]
            visited = {entry_id}
        else:
            queue = []
            visited = set()

        # Handle case where target is the entry node
        if target_node.id == entry_id:
            return False

        # 1. Check strict reachability (ignoring guards) to identify Islands
        if entry_id:
            full_queue = [entry_id]
            full_visited = {entry_id}
        else:
            full_queue = []
            full_visited = set()

        reachable = False
        while full_queue:
            curr = full_queue.pop(0)
            if curr == target_node.id:
                reachable = True
                break
            for n in adj.get(curr or "", []):
                if n not in full_visited:
                    full_visited.add(n)
                    full_queue.append(n)

        if not reachable:
            return False  # Island -> Fail Closed

        # 2. Check guarded reachability
        while queue:
            curr_id = queue.pop(0)

            if curr_id == target_node.id:
                return False  # Reached target without passing a guard

            # If current node is a guard, we stop traversing this path
            # (because downstream is guarded by this node).
            if curr_id in guards:
                continue

            # Expand neighbors
            for neighbor in adj.get(curr_id or "", []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        # If reachable but not via unguarded path -> Guarded
        return True

    return False
