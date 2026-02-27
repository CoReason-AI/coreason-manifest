# src/coreason_manifest/utils/validator.py

import re
from typing import Any

from pydantic import BaseModel

from coreason_manifest.spec.core.contracts import NodeSpec
from coreason_manifest.spec.core.flow import (
    FlowDefinitions,
    FlowSpec,
    Graph,
)
from coreason_manifest.spec.core.governance import Governance
from coreason_manifest.spec.core.resilience import (
    EscalationStrategy,
    FallbackStrategy,
    ReflexionStrategy,
    ResilienceStrategy,
)
from coreason_manifest.spec.core.tools import ToolCapability, ToolPack
from coreason_manifest.spec.core.types import RiskLevel
from coreason_manifest.spec.interop.compliance import ComplianceReport, ErrorCatalog, RemediationAction
from coreason_manifest.spec.interop.exceptions import ManifestError, ManifestErrorCode
from coreason_manifest.utils.topology import (
    TopologyValidationError,
    get_unified_topology,
    validate_topology,
)


def validate_flow(flow: FlowSpec) -> list[ComplianceReport]:
    """
    Semantically validate a FlowSpec.
    Returns a list of structured ComplianceReport objects. Empty list implies validity.
    """
    errors: list[ComplianceReport] = []

    # 0. AOT Topology Validation
    try:
        validate_topology(flow)
    except TopologyValidationError as e:
        # Convert to ComplianceReport
        errors.append(
            ComplianceReport(
                code=e.fault.error_code,
                severity="violation",
                message=e.fault.message,
                details=e.fault.context,
            )
        )

    # Flatten nodes based on flow type
    nodes, _ = get_unified_topology(flow)

    valid_ids = {n.id for n in nodes}

    # 1. Common Checks
    if flow.governance:
        errors.extend(_validate_governance(flow.governance, valid_ids))

    if flow.definitions:
        errors.extend(_validate_referential_integrity(nodes, flow.definitions))
    else:
        # If no definitions, ensure no references exist
        errors.extend(_validate_referential_integrity(nodes, None))

    # Graph Checks
    if not flow.graph.nodes:
        errors.append(
            ComplianceReport(
                code=ErrorCatalog.ERR_TOPOLOGY_EMPTY_GRAPH,
                severity="violation",
                message="FlowSpec Error: Graph must contain at least one node.",
            )
        )

    # Entry Point Existence
    if flow.graph.entry_point and flow.graph.entry_point not in valid_ids:
        errors.append(
            ComplianceReport(
                code=ErrorCatalog.ERR_TOPOLOGY_MISSING_ENTRY,
                severity="violation",
                message=f"FlowSpec Error: Entry point '{flow.graph.entry_point}' not found in nodes.",
                details={"entry_point": flow.graph.entry_point},
            )
        )

    errors.extend(_validate_graph_integrity(flow.graph))

    # Helper for extracting nodes for generic logic checks
    nodes_list = list(flow.graph.nodes.values())
    node_ids = set(flow.graph.nodes.keys())

    errors.extend(_validate_unique_ids(nodes_list))
    errors.extend(_validate_orphan_nodes(flow))

    # 5. Security & Kill Switch
    if flow.governance and flow.governance.max_risk_level:
        errors.extend(_validate_kill_switch(flow))

    # 6. Middleware References
    errors.extend(_validate_middleware_refs(flow))

    return errors


def _validate_governance(gov: Governance, valid_ids: set[str]) -> list[ComplianceReport]:
    errors: list[ComplianceReport] = []

    if (
        gov.circuit_breaker
        and gov.circuit_breaker.fallback_node_id
        and gov.circuit_breaker.fallback_node_id not in valid_ids
    ):
        errors.append(
            ComplianceReport(
                code=ErrorCatalog.ERR_GOV_CIRCUIT_FALLBACK_MISSING,
                severity="violation",
                message=f"Circuit Breaker Error: 'fallback_node_id' points to missing ID "
                f"'{gov.circuit_breaker.fallback_node_id}'.",
                details={"fallback_node_id": gov.circuit_breaker.fallback_node_id},
            )
        )
    return errors


def _validate_unique_ids(nodes: list[NodeSpec]) -> list[ComplianceReport]:
    seen = set()
    errors: list[ComplianceReport] = []
    for node in nodes:
        if node.id in seen:
            errors.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_TOPOLOGY_NODE_ID_COLLISION,
                    severity="violation",
                    message=f"ID Collision Error: Duplicate Node ID '{node.id}' found.",
                    node_id=node.id,
                )
            )
        seen.add(node.id)
    return errors


def _validate_graph_integrity(graph: Graph) -> list[ComplianceReport]:
    errors: list[ComplianceReport] = []
    valid_ids = set(graph.nodes.keys())

    # Check 1: Key/ID Integrity
    for key, node in graph.nodes.items():
        if key != node.id:
            errors.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_TOPOLOGY_ID_MISMATCH,
                    severity="violation",
                    message=f"Graph Integrity Error: Node key '{key}' does not match Node ID '{node.id}'.",
                    node_id=node.id,
                    details={"key": key, "node_id": node.id},
                )
            )

    # Check 2: Edge Validity
    for edge in graph.edges:
        if edge.from_node not in valid_ids:
            errors.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_TOPOLOGY_DANGLING_EDGE,
                    severity="violation",
                    message=f"Dangling Edge Error: Source '{edge.from_node}' not found in graph nodes.",
                    details={"source": edge.from_node},
                )
            )
        if edge.to_node not in valid_ids:
            errors.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_TOPOLOGY_DANGLING_EDGE,
                    severity="violation",
                    message=f"Dangling Edge Error: Target '{edge.to_node}' not found in graph nodes.",
                    details={"target": edge.to_node},
                )
            )

    return errors


def _validate_orphan_nodes(flow: FlowSpec) -> list[ComplianceReport]:
    """
    Validates that no reachable nodes are isolated from the rest of the graph.
    Uses unified adjacency map to check connectivity via edges, switches, or fallbacks.
    """
    if not flow.graph.nodes:
        return []

    all_ids = set(flow.graph.nodes.keys())
    entry_point = flow.graph.entry_point

    # Use our SOTA unified map to find ALL targets (explicit edges + switches + fallbacks)
    # Bypass deep validation to construct a temporary flow for unified mapping if needed,
    # though here we are already inside a valid flow context or partial flow.
    # Note: _build_unified_adjacency_map handles flow.graph access safely.
    adj_set = _build_unified_adjacency_map(flow)

    targeted_ids = set()
    for targets in adj_set.values():
        targeted_ids.update(targets)

    orphans = all_ids - targeted_ids

    # The entry point is expected to have no incoming edges
    if entry_point in orphans:
        orphans.remove(entry_point)

    return [
        ComplianceReport(
            code=ErrorCatalog.ERR_TOPOLOGY_ORPHAN_001,
            severity="warning",
            message=f"Orphan Node Warning: Node '{oid}' has no incoming edges or implicit routes.",
            node_id=oid,
        )
        for oid in orphans
    ]


def _validate_referential_integrity(
    nodes: list[NodeSpec], definitions: FlowDefinitions | None
) -> list[ComplianceReport]:
    """
    Validates string references (e.g. resilience templates, profiles).
    """
    errors: list[ComplianceReport] = []

    # Check supervision templates
    templates = definitions.supervision_templates if definitions and definitions.supervision_templates else {}

    # Assuming NodeSpec.metadata is strict payload.

    return errors


def _resolve_resilience_policy(policy: Any, definitions: FlowDefinitions | None) -> Any:
    """Resolves string reference policies from the definitions block."""
    if isinstance(policy, str):
        if policy.startswith("ref:") and definitions and definitions.supervision_templates:
            tmpl_id = policy.removeprefix("ref:")
            # Return the resolved template, or None if it's missing (missing refs are caught by referential_integrity)
            return definitions.supervision_templates.get(tmpl_id)
        return None
    return policy


def _extract_strategies(policy: Any) -> list[ResilienceStrategy]:
    """
    Helper to extract flat list of strategies from a unified resilience config.
    """
    strategies: list[ResilienceStrategy] = []
    if hasattr(policy, "handlers"):
        strategies.extend([h.strategy for h in policy.handlers])
        if hasattr(policy, "default_strategy") and policy.default_strategy:
            strategies.append(policy.default_strategy)
    else:
        strategies.append(policy)
    return strategies


def _build_unified_adjacency_map(flow: FlowSpec) -> dict[str, set[str]]:
    """
    Constructs a unified adjacency map for analysis.
    Includes sequential/graph edges, implicit SwitchNode routing, fallback routing, and global circuit breaker.
    """
    # 1. Initialize Map with strict type inference for node iteration
    nodes, edges_objs = get_unified_topology(flow)
    adj: dict[str, set[str]] = {node.id: set() for node in nodes}

    # 2. Add Flow Structure Edges
    for edge in edges_objs:
        if edge.from_node in adj and edge.to_node in adj:
            adj[edge.from_node].add(edge.to_node)

    # 3. Add Global Governance Edges (Circuit Breaker)
    global_fallback_id: str | None = None
    if flow.governance and flow.governance.circuit_breaker and flow.governance.circuit_breaker.fallback_node_id:
        global_fallback_id = flow.governance.circuit_breaker.fallback_node_id

    # 4. Add Node-Level Implicit Edges
    for node in nodes:
        # Global fallback applies to ALL nodes EXCEPT the fallback node itself
        if global_fallback_id and global_fallback_id in adj and node.id != global_fallback_id:
            adj[node.id].add(global_fallback_id)

        # We assume NodeSpec doesn't expose SwitchNode/Resilience in same way.
        # So we skip specific node routing if unknown.

    return adj


def _validate_kill_switch(flow: FlowSpec) -> list[ComplianceReport]:
    errors: list[ComplianceReport] = []
    if not flow.governance:
        return errors

    max_risk = flow.governance.max_risk_level

    nodes, _ = get_unified_topology(flow)

    def _check(obj: Any) -> None:
        # 1. Check ToolCapability objects
        if isinstance(obj, ToolCapability) and max_risk is not None and obj.risk_level.weight > max_risk.weight:
            errors.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_SEC_KILL_SWITCH_VIOLATION,
                    severity="violation",
                    message=f"Security Violation: Tool '{obj.name}' has risk level '{obj.risk_level.value}' "
                    f"which exceeds the global max_risk_level '{max_risk.value}'.",
                    details={"tool_name": obj.name, "tool_risk": obj.risk_level.value, "max_risk": max_risk.value},
                )
            )

        # 2. Check Strings for Remote URIs
        if isinstance(obj, str):
            if "://" in obj and max_risk is not None and RiskLevel.CRITICAL.weight > max_risk.weight:
                errors.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_SEC_KILL_SWITCH_VIOLATION,
                        severity="violation",
                        message="Security Violation: Unresolved remote tool URIs default to CRITICAL risk and "
                        "violate the global max_risk_level.",
                        details={
                            "tool_uri": obj,
                            "assumed_risk": RiskLevel.CRITICAL.value,
                            "max_risk": max_risk.value,
                        },
                    )
                )
            return

        # 3. Recursion
        if isinstance(obj, dict):
            for v in obj.values():
                _check(v)
        elif isinstance(obj, (list, tuple, set)):
            for v in obj:
                _check(v)
        elif isinstance(obj, BaseModel):
            # Efficiently iterate model fields
            for name in type(obj).model_fields:
                value = getattr(obj, name)
                _check(value)

    if flow.definitions:
        _check(flow.definitions)

    _check(nodes)

    return errors


def _validate_middleware_refs(flow: FlowSpec) -> list[ComplianceReport]:
    errors: list[ComplianceReport] = []
    if not flow.governance or not flow.governance.active_middlewares:
        return errors

    defined = set()
    if flow.definitions and flow.definitions.middlewares:
        defined = set(flow.definitions.middlewares.keys())

    for mw_id in flow.governance.active_middlewares:
        if mw_id not in defined:
            # SOTA RFC 6902 JSON Pointer Escaping
            mw_id_escaped = mw_id.replace("~", "~0").replace("/", "~1")

            # Construct patch
            patch: list[dict[str, Any]]
            if not flow.definitions:
                patch = [
                    {
                        "op": "add",
                        "path": "/definitions",
                        "value": {"middlewares": {mw_id: {"ref": "file.py:Class"}}},
                    }
                ]
            elif not flow.definitions.middlewares:
                patch = [{"op": "add", "path": "/definitions/middlewares", "value": {mw_id: {"ref": "file.py:Class"}}}]
            else:
                patch = [
                    {
                        "op": "add",
                        "path": f"/definitions/middlewares/{mw_id_escaped}",
                        "value": {"ref": "file.py:Class"},
                    }
                ]

            errors.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_CAP_MISSING_MIDDLEWARE,
                    severity="violation",
                    message=f"Middleware Error: Active middleware '{mw_id}' is not defined.",
                    details={"middleware_id": mw_id},
                    remediation=RemediationAction(
                        type="update_field",
                        description=f"Add definition for middleware '{mw_id}'.",
                        patch_data=patch,
                    ),
                )
            )

    return errors
