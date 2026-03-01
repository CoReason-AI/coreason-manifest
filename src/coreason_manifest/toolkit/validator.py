# src/coreason_manifest/utils/validator.py

import re
from typing import Any

from pydantic import BaseModel

from coreason_manifest.core.oversight.governance import Governance
from coreason_manifest.core.oversight.resilience import (
    EscalationStrategy,
    FallbackStrategy,
    ReflexionStrategy,
    ResilienceStrategy,
)
from coreason_manifest.core.primitives.types import RiskLevel
from coreason_manifest.core.security.compliance import ComplianceReport, ErrorCatalog, RemediationAction
from coreason_manifest.core.state.tools import ToolCapability, ToolPack
from coreason_manifest.core.workflow.flow import (
    AnyNode,
    FlowDefinitions,
    GraphFlow,
    LinearFlow,
)
from coreason_manifest.core.workflow.nodes import (
    AgentNode,
    CognitiveProfile,
    EmergenceInspectorNode,
    HumanNode,
    InspectorNode,
    PlannerNode,
    SwarmNode,
    SwitchNode,
)
from coreason_manifest.core.workflow.topology import get_unified_topology


def _validate_traffic_policy(flow: LinearFlow | GraphFlow) -> list[ComplianceReport]:
    errors: list[ComplianceReport] = []

    if not flow.governance or not flow.governance.operational_policy or not flow.governance.operational_policy.traffic:
        return errors

    traffic = flow.governance.operational_policy.traffic

    if traffic.rate_limit_rpm is not None and traffic.rate_limit_rpm <= 0:
        errors.append(
            ComplianceReport(
                code="ERR_GOV_INVALID_CONFIG",
                severity="violation",
                message=(
                    "Traffic Policy Error: rate_limit_rpm must be strictly greater than 0, "
                    f"got {traffic.rate_limit_rpm}."
                ),
                details={"rate_limit_rpm": traffic.rate_limit_rpm},
            )
        )

    if traffic.rate_limit_tpm is not None and traffic.rate_limit_tpm <= 0:
        errors.append(
            ComplianceReport(
                code="ERR_GOV_INVALID_CONFIG",
                severity="violation",
                message=(
                    "Traffic Policy Error: rate_limit_tpm must be strictly greater than 0, "
                    f"got {traffic.rate_limit_tpm}."
                ),
                details={"rate_limit_tpm": traffic.rate_limit_tpm},
            )
        )

    from coreason_manifest.core.oversight.governance import RequestCriticality

    if (
        traffic.criticality == RequestCriticality.CRITICAL
        and traffic.rate_limit_tpm is not None
        and traffic.rate_limit_tpm < 100
    ):
        errors.append(
            ComplianceReport(
                code="ERR_GOV_INVALID_CONFIG",
                severity="warning",
                message=(
                    "Traffic Policy Warning: CRITICAL priority combined with "
                    f"extremely low TPM limits ({traffic.rate_limit_tpm})."
                ),
                details={"criticality": "CRITICAL", "rate_limit_tpm": traffic.rate_limit_tpm},
            )
        )

    return errors


def validate_flow(flow: LinearFlow | GraphFlow) -> list[ComplianceReport]:
    """
    Semantically validate a Flow (Linear or Graph).
    Returns a list of structured ComplianceReport objects. Empty list implies validity.
    """
    errors: list[ComplianceReport] = []

    errors.extend(_validate_traffic_policy(flow))

    # Flatten nodes based on flow type
    nodes, edges_objs = get_unified_topology(flow)

    valid_ids = set()
    collision_detected = False
    for node in nodes:
        if node.id in valid_ids:
            errors.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_TOPOLOGY_NODE_ID_COLLISION,
                    severity="violation",
                    message=f"Topology Error: Duplicate Node ID '{node.id}' detected in unified topology.",
                    node_id=node.id,
                )
            )
            collision_detected = True
        valid_ids.add(node.id)

    # SOTA Short-Circuit: Halt static analysis on mathematically unstable graphs
    if collision_detected:
        return errors

    # Build simple adjacency map from explicit edges
    adj_map: dict[str, set[str]] = {n_id: set() for n_id in valid_ids}
    for edge in edges_objs:
        if edge.from_node in adj_map and edge.to_node in adj_map:
            adj_map[edge.from_node].add(edge.to_node)

    # 1. Common Checks
    if flow.governance:
        errors.extend(_validate_governance(flow.governance, valid_ids))

    if flow.definitions:
        # Convert dict to list for backward compatibility with _validate_tools
        tool_packs = list(flow.definitions.tool_packs.values()) if flow.definitions.tool_packs else []
        errors.extend(_validate_tools(nodes, tool_packs))
        errors.extend(_validate_referential_integrity(nodes, flow.definitions))
    else:
        # If no definitions, ensure no references exist
        errors.extend(_validate_referential_integrity(nodes, None))

    for node in nodes:
        errors.extend(_validate_supervision(node, valid_ids, flow.definitions))

    # 2. LinearFlow Specific Checks
    if isinstance(flow, LinearFlow):
        errors.extend(_validate_switch_logic(flow.steps, valid_ids))
        errors.extend(_validate_swarm_concurrency(flow.steps))

    # 3. GraphFlow Specific Checks
    if isinstance(flow, GraphFlow):
        # Helper for extracting nodes for generic logic checks
        nodes_list = list(flow.graph.nodes.values())
        node_ids = set(flow.graph.nodes.keys())

        errors.extend(_validate_switch_logic(nodes_list, node_ids))
        errors.extend(_validate_human_routes(nodes_list, node_ids))
        errors.extend(_validate_orphan_nodes(flow))
        errors.extend(_validate_swarm_concurrency(nodes_list))

    # Epic 11: Graph-Theoretic Financial Budgets
    errors.extend(_validate_budget_constraints(flow))

    # 4. Domain 4: Static Data-Flow Analysis
    # Construct Symbol Table: Map variable name -> type (str)
    symbol_table: dict[str, str] = {}
    if hasattr(flow, "blackboard") and flow.blackboard:
        for name, var_def in flow.blackboard.variables.items():
            # Architectural Note: Normalize to lowercase to handle "List", "ARRAY", etc.
            if hasattr(var_def, "type"):
                symbol_table[name] = var_def.type.lower()
            else:
                symbol_table[name] = "unknown"
    if hasattr(flow, "interface") and flow.interface:
        inputs = flow.interface.inputs
        in_schema = getattr(inputs, "json_schema", inputs)
        if isinstance(in_schema, dict):

            def _extract_schema_types(schema_dict: dict[str, Any], prefix: str = "") -> None:
                props = schema_dict.get("properties", {})
                for name, schema in props.items():
                    key = f"{prefix}{name}"
                    if not isinstance(schema, dict):
                        symbol_table[key] = "unknown"
                        continue

                    raw_type = schema.get("type", "unknown")
                    if isinstance(raw_type, list):
                        types = sorted([x for x in raw_type if x != "null"])
                        symbol_table[key] = "|".join(types) if types else "union"
                    else:
                        symbol_table[key] = str(raw_type)

                    if raw_type == "object" or "object" in str(raw_type):
                        _extract_schema_types(schema, prefix=f"{key}.")

            _extract_schema_types(in_schema)

        errors.extend(_validate_data_flow(nodes, symbol_table, flow.definitions, adj_map))

    # 5. Security & Kill Switch
    if flow.governance and flow.governance.max_risk_level:
        errors.extend(_validate_kill_switch(flow))

    # 6. Middleware References
    errors.extend(_validate_middleware_refs(flow))

    return errors


def _scan_string_for_vars(text: str) -> set[str]:
    """
    Scan a string for Jinja2-style variable references: {{ var_name }}
    Handles filters like {{ var | lower }} by stripping them.
    """
    return set(re.findall(r"\{\{\s*([a-zA-Z_][\w\.]*)(?:\s*\|.*?)?\s*\}\}", text))


def _scan_agent_templates(node: AgentNode, definitions: FlowDefinitions | None) -> set[str]:
    """
    Extract variable references from AgentNode fields.
    Scans:
    - Inline profile role/persona
    - Referenced profiles (from definitions)
    - Metadata values (if strings)
    """
    refs = set()

    # Scan profile
    if isinstance(node.profile, CognitiveProfile):
        # Inline profile
        refs.update(_scan_string_for_vars(node.profile.role))
        refs.update(_scan_string_for_vars(node.profile.persona))
    elif isinstance(node.profile, str):
        # Referenced profile
        if definitions and node.profile in definitions.profiles:
            profile_def = definitions.profiles[node.profile]
            if isinstance(profile_def, CognitiveProfile):
                refs.update(_scan_string_for_vars(profile_def.role))
                refs.update(_scan_string_for_vars(profile_def.persona))

    # Scan metadata values
    for val in node.metadata.values():
        if isinstance(val, str):
            refs.update(_scan_string_for_vars(val))

    return refs


def _validate_data_flow(
    nodes: list[AnyNode],
    symbol_table: dict[str, str],
    definitions: FlowDefinitions | None,
    adj_map: dict[str, set[str]] | None = None,
) -> list[ComplianceReport]:
    """
    Check if nodes reference variables that exist in the symbol table.
    Also validates type compatibility for specific node types.
    """
    errors: list[ComplianceReport] = []
    available_vars = set(symbol_table.keys())

    for node in nodes:
        if hasattr(node, "constraints"):
            for constraint in node.constraints:
                base_var = constraint.variable.split(".")[0]
                if base_var not in available_vars:
                    errors.append(
                        ComplianceReport(
                            code=ErrorCatalog.ERR_CAP_MISSING_VAR,
                            severity="violation",
                            message=(
                                f"Constraint Error: Node '{node.id}' references "
                                f"missing variable '{constraint.variable}'."
                            ),
                            node_id=node.id,
                            details={"variable": constraint.variable},
                        )
                    )

        if isinstance(node, SwarmNode):
            if node.workload_variable not in available_vars:
                errors.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_CAP_MISSING_VAR,
                        severity="violation",
                        message=f"Data Flow Error: SwarmNode '{node.id}' references missing variable "
                        f"'{node.workload_variable}'.",
                        node_id=node.id,
                        details={"variable": node.workload_variable},
                        remediation=RemediationAction(
                            type="update_field",
                            description=f"Add variable '{node.workload_variable}' to blackboard.",
                            patch_data=[
                                {
                                    "op": "add",
                                    "path": f"/blackboard/variables/{node.workload_variable}",
                                    "value": [],
                                }
                            ],
                        ),
                    )
                )
            # MVP Type Safety: SwarmNode expects a list/array for workload
            elif node.workload_variable in symbol_table:
                var_type = symbol_table[node.workload_variable]
                # Check if 'array' is ANY of the permitted types
                if "array" not in var_type and "list" not in var_type and "unknown" not in var_type:
                    errors.append(
                        ComplianceReport(
                            code=ErrorCatalog.ERR_CAP_TYPE_MISMATCH,
                            severity="violation",
                            message=f"Type Mismatch: SwarmNode '{node.id}' expects a list for "
                            f"'{node.workload_variable}', but found type '{var_type}'.",
                            node_id=node.id,
                            details={"variable": node.workload_variable, "found_type": var_type},
                        )
                    )

            if node.output_variable not in available_vars:
                errors.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_CAP_MISSING_VAR,
                        severity="violation",
                        message=f"Data Flow Error: SwarmNode '{node.id}' writes to missing variable "
                        f"'{node.output_variable}'.",
                        node_id=node.id,
                        details={"variable": node.output_variable},
                    )
                )

        elif isinstance(node, PlannerNode):
            try:
                import jsonschema  # type: ignore
                from jsonschema.exceptions import SchemaError  # type: ignore

                jsonschema.validators.validator_for(node.output_schema).check_schema(node.output_schema)

                # SOTA 2026: Shift-Left Reliability
                # Find structurally expected schemas from true *downstream connected* neighbors.
                downstream_ids = adj_map.get(node.id, set()) if adj_map else set()
                downstream_expectations: list[tuple[str, dict[str, Any]]] = []

                # Map node ID to its instance for easy lookup
                node_map = {n.id: n for n in nodes}

                for d_id in downstream_ids:
                    d_node = node_map.get(d_id)
                    if not d_node:
                        continue
                    # Hardcoded structural constraints based on node type
                    if isinstance(d_node, SwarmNode):
                        downstream_expectations.append(
                            (
                                d_id,
                                {
                                    "type": "object",
                                    "required": [d_node.workload_variable],
                                    "properties": {d_node.workload_variable: {"type": "array"}},
                                },
                            )
                        )
                    # If other nodes have explicit input schemas in the future, we would add them here.
                    from coreason_manifest.core.workflow.nodes import HumanNode

                    if isinstance(d_node, HumanNode) and getattr(d_node, "input_schema", None):
                        downstream_expectations.append((d_id, d_node.input_schema))  # type: ignore

                # Mathematical Verification: does Planner's output_schema satisfy downstream's expected input schema?
                # We achieve this by validating a "dummy" full JSON object matching the Planner's exact shape
                # against the downstream jsonschema if possible, or by structural overlap checking.
                def _check_schema_satisfaction(
                    provided: dict[str, Any], expected: dict[str, Any], path: str = ""
                ) -> list[str]:
                    errs = []
                    # Check types
                    prov_type = provided.get("type", "object")
                    exp_type = expected.get("type", "object")
                    if prov_type != exp_type:
                        errs.append(f"Type mismatch at '{path}': expected {exp_type}, got {prov_type}")
                        return errs

                    if exp_type == "object":
                        prov_props = provided.get("properties", {})
                        exp_props = expected.get("properties", {})
                        exp_req = expected.get("required", [])
                        prov_req = provided.get("required", [])

                        # To satisfy the downstream node, the upstream node MUST also strictly require the field
                        errs.extend(
                            [
                                f"Property '{req}' is required by downstream but not guaranteed "
                                f"(missing from 'required' array) at '{path}'"
                                for req in exp_req
                                if req not in prov_req
                            ]
                        )

                        # Recurse for nested properties
                        for p_name, p_schema in exp_props.items():
                            if p_name in prov_props:
                                errs.extend(
                                    _check_schema_satisfaction(
                                        prov_props[p_name], p_schema, path=f"{path}.{p_name}" if path else p_name
                                    )
                                )
                    elif exp_type == "array":
                        # Recurse into array items
                        prov_items = provided.get("items", {})
                        exp_items = expected.get("items", {})
                        if exp_items and prov_items:
                            errs.extend(_check_schema_satisfaction(prov_items, exp_items, path=f"{path}[]"))

                    return errs

                for target_id, exp_schema in downstream_expectations:
                    schema_errs = _check_schema_satisfaction(node.output_schema, exp_schema)
                    errors.extend(
                        [
                            ComplianceReport(
                                code=ErrorCatalog.ERR_CAP_TYPE_MISMATCH,
                                severity="violation",
                                message=f"Structural Misalignment: PlannerNode '{node.id}' output does not satisfy "
                                f"downstream node '{target_id}': {err_msg}.",
                                node_id=node.id,
                            )
                            for err_msg in schema_errs
                        ]
                    )

            except SchemaError as e:
                errors.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_CAP_TYPE_MISMATCH,
                        severity="violation",
                        message=f"PlannerNode schema validation failed: {e!s}",
                        node_id=node.id,
                    )
                )

        elif isinstance(node, SwitchNode):
            if node.variable not in available_vars:
                errors.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_CAP_MISSING_VAR,
                        severity="violation",
                        message=f"Data Flow Error: SwitchNode '{node.id}' evaluates missing variable "
                        f"'{node.variable}'.",
                        node_id=node.id,
                        details={"variable": node.variable},
                    )
                )

        elif isinstance(node, (InspectorNode, EmergenceInspectorNode)):
            if node.to_node_variable not in available_vars:
                errors.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_CAP_MISSING_VAR,
                        severity="violation",
                        message=f"Data Flow Error: InspectorNode '{node.id}' inspects missing variable "
                        f"'{node.to_node_variable}'.",
                        node_id=node.id,
                        details={"variable": node.to_node_variable},
                    )
                )
            # MVP Type Safety: Regex matching on complex objects is risky
            elif (
                node.to_node_variable in symbol_table
                and hasattr(node, "mode")
                and node.mode == "programmatic"
                and symbol_table[node.to_node_variable] in ("object", "array")
            ):
                var_type = symbol_table[node.to_node_variable]
                # Just a warning for now
                errors.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_CAP_TYPE_MISMATCH,
                        severity="warning",
                        message=f"Type Warning: InspectorNode '{node.id}' uses regex mode on complex type '{var_type}' "
                        f"variable '{node.to_node_variable}'. Matching may fail.",
                        node_id=node.id,
                        details={"variable": node.to_node_variable, "found_type": var_type},
                    )
                )

            if node.output_variable not in available_vars:
                errors.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_CAP_MISSING_VAR,
                        severity="violation",
                        message=f"Data Flow Error: InspectorNode '{node.id}' writes to missing variable "
                        f"'{node.output_variable}'.",
                        node_id=node.id,
                        details={"variable": node.output_variable},
                    )
                )

        elif isinstance(node, AgentNode):
            # Scan for prompt template variables
            refs = _scan_agent_templates(node, definitions)
            errors.extend(
                ComplianceReport(
                    code=ErrorCatalog.ERR_CAP_MISSING_VAR,
                    severity="violation",
                    message=f"Data Flow Error: AgentNode '{node.id}' references missing variable '{var}' in templates.",
                    node_id=node.id,
                    details={"variable": var},
                )
                for var in refs
                if var not in available_vars
            )

    return errors


def _validate_opa_policies(gov: Governance) -> list[ComplianceReport]:
    errors: list[ComplianceReport] = []
    if gov.opa_policies and gov.max_risk_level is None:
        errors.append(
            ComplianceReport(
                # Use literal string to avoid dependency issues if it's not in ErrorCatalog
                code="ERR_GOV_INVALID_CONFIG",
                severity="violation",
                message=(
                    "Declarative OPA policies must be mathematically backed by "
                    "a hard risk ceiling in a zero-trust architecture."
                ),
            )
        )
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

    errors.extend(_validate_opa_policies(gov))

    return errors


def _validate_tools(nodes: list[AnyNode], packs: list[ToolPack]) -> list[ComplianceReport]:
    errors: list[ComplianceReport] = []
    available_tools = {t.name for pack in packs for t in pack.tools}

    for node in nodes:
        if isinstance(node, AgentNode):
            errors.extend(
                ComplianceReport(
                    code=ErrorCatalog.ERR_CAP_MISSING_TOOL_001,
                    severity="warning",
                    message=f"Missing Tool Warning: Agent '{node.id}' requires tool '{tool}' but it is not provided by "
                    "any attached ToolPack.",
                    node_id=node.id,
                    details={"tool": tool},
                )
                for tool in node.tools
                if tool not in available_tools
            )
    return errors


def _validate_swarm_concurrency(nodes: list[AnyNode]) -> list[ComplianceReport]:
    return [
        ComplianceReport(
            code=ErrorCatalog.ERR_TOPOLOGY_RACE_CONDITION,
            severity="violation",
            message=f"Concurrency Error: SwarmNode '{node.id}' uses replicated distribution but lacks a "
            "reducer_function or lock_config, risking race conditions on the output variable.",
            node_id=node.id,
        )
        for node in nodes
        if isinstance(node, SwarmNode)
        and node.distribution_strategy == "replicated"
        and not node.reducer_function
        and not node.lock_config
    ]


def _validate_human_routes(nodes: list[AnyNode], valid_ids: set[str]) -> list[ComplianceReport]:
    errors: list[ComplianceReport] = []
    for node in nodes:
        if isinstance(node, HumanNode) and getattr(node, "routes", None):
            errors.extend(
                ComplianceReport(
                    code=ErrorCatalog.ERR_TOPOLOGY_BROKEN_SWITCH,
                    severity="violation",
                    message=f"HumanNode '{node.id}' route points to missing ID '{target_id}'.",
                    node_id=node.id,
                    details={"target_id": target_id},
                )
                for target_id in node.routes.values()
                if target_id not in valid_ids
            )
    return errors


def _validate_switch_logic(nodes: list[AnyNode], valid_ids: set[str]) -> list[ComplianceReport]:
    errors: list[ComplianceReport] = []
    for node in nodes:
        if isinstance(node, SwitchNode):
            # Check Cases
            for condition, target_id in node.cases.items():
                if target_id not in valid_ids:
                    errors.append(
                        ComplianceReport(
                            code=ErrorCatalog.ERR_TOPOLOGY_BROKEN_SWITCH,
                            severity="violation",
                            message=f"Broken Switch Error: Node '{node.id}' case '{condition}' points to missing ID "
                            f"'{target_id}'.",
                            node_id=node.id,
                            details={"condition": condition, "target_id": target_id},
                        )
                    )
            # Check Default
            if node.default not in valid_ids:
                errors.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_TOPOLOGY_BROKEN_SWITCH,
                        severity="violation",
                        message=f"Broken Switch Error: Node '{node.id}' default route points to missing ID "
                        f"'{node.default}'.",
                        node_id=node.id,
                        details={"target_id": node.default},
                    )
                )
    return errors


def _validate_orphan_nodes(flow: GraphFlow) -> list[ComplianceReport]:
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

    if flow.status != "published":
        return [
            ComplianceReport(
                code=ErrorCatalog.ERR_TOPOLOGY_ORPHAN_001,
                severity="info",
                message=f"Orphan Node Warning: Node '{oid}' has no incoming edges or implicit routes.",
                node_id=oid,
            )
            for oid in orphans
        ]

    return [
        ComplianceReport(
            code=ErrorCatalog.ERR_TOPOLOGY_ORPHAN_001,
            severity="warning",
            message=f"Orphan Node Warning: Node '{oid}' has no incoming edges or implicit routes.",
            node_id=oid,
            remediation=RemediationAction(
                type="update_field",
                description=f"Remove orphan node '{oid}'.",
                patch_data=[{"op": "remove", "path": f"/graph/nodes/{oid}"}],
            ),
        )
        for oid in orphans
    ]


def _validate_referential_integrity(
    nodes: list[AnyNode], definitions: FlowDefinitions | None
) -> list[ComplianceReport]:
    """
    Validates string references (e.g. resilience templates, profiles).
    """
    errors: list[ComplianceReport] = []

    # Check supervision templates
    templates = definitions.supervision_templates if definitions and definitions.supervision_templates else {}
    profile_ids = set(definitions.profiles.keys()) if definitions and definitions.profiles else set()

    for node in nodes:
        # Check resilience references
        if isinstance(node.resilience, str):
            ref = node.resilience
            if not ref.startswith("ref:"):
                errors.append(
                    ComplianceReport(
                        code=ErrorCatalog.ERR_RESILIENCE_INVALID_REF,
                        severity="violation",
                        message=f"Resilience Error: Node '{node.id}' has invalid resilience reference '{ref}'. "
                        "Must start with 'ref:'.",
                        node_id=node.id,
                        details={"reference": ref},
                    )
                )
            else:
                tmpl_id = ref.removeprefix("ref:")
                if tmpl_id not in templates:
                    errors.append(
                        ComplianceReport(
                            code=ErrorCatalog.ERR_RESILIENCE_MISSING_TEMPLATE,
                            severity="violation",
                            message=f"Resilience Error: Node '{node.id}' references undefined supervision template ID "
                            f"'{tmpl_id}'.",
                            node_id=node.id,
                            details={"template_id": tmpl_id},
                        )
                    )

        # Check profile references (AgentNode)
        if isinstance(node, AgentNode) and isinstance(node.profile, str) and node.profile not in profile_ids:
            errors.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_CAP_UNDEFINED_PROFILE_002,
                    severity="violation",
                    message=f"Integrity Error: AgentNode '{node.id}' references undefined profile ID '{node.profile}'.",
                    node_id=node.id,
                    details={"profile_id": node.profile},
                )
            )

        # Check worker profile references (SwarmNode)
        if isinstance(node, SwarmNode) and node.worker_profile not in profile_ids:
            errors.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_CAP_UNDEFINED_PROFILE_002,
                    severity="violation",
                    message=f"Integrity Error: SwarmNode '{node.id}' references undefined worker profile ID "
                    f"'{node.worker_profile}'.",
                    node_id=node.id,
                    details={"profile_id": node.worker_profile},
                )
            )

    return errors


def _validate_supervision(
    node: AnyNode, valid_ids: set[str], definitions: FlowDefinitions | None
) -> list[ComplianceReport]:
    errors: list[ComplianceReport] = []

    # Check unified resilience field on any node type
    policy = node.resilience
    if not policy:
        return errors

    resolved_policy = _resolve_resilience_policy(policy, definitions)
    if not resolved_policy:
        return errors

    # Collect strategies
    strategies = _extract_strategies(resolved_policy)

    for strategy in strategies:
        if isinstance(strategy, ReflexionStrategy) and node.type not in (
            "agent",
            "inspector",
            "emergence_inspector",
            "swarm",
            "planner",
        ):
            errors.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_RESILIENCE_MISMATCH,
                    severity="violation",
                    message=f"Resilience Error: Node '{node.id}' uses ReflexionStrategy but is of type '{node.type}'. "
                    "Only Agent/Inspector/Swarm/Planner nodes support reflexion.",
                    node_id=node.id,
                )
            )

        if isinstance(strategy, FallbackStrategy) and strategy.fallback_node_id not in valid_ids:
            errors.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_RESILIENCE_FALLBACK_MISSING,
                    severity="violation",
                    message=f"Resilience Error: Node '{node.id}' fallback points to missing ID "
                    f"'{strategy.fallback_node_id}'.",
                    node_id=node.id,
                    details={"fallback_node_id": strategy.fallback_node_id},
                )
            )

        if isinstance(strategy, EscalationStrategy) and not strategy.queue_name:
            errors.append(
                ComplianceReport(
                    code=ErrorCatalog.ERR_RESILIENCE_ESCALATION_INVALID,
                    severity="violation",
                    message=f"Resilience Error: Node '{node.id}' uses EscalationStrategy with empty queue_name.",
                    node_id=node.id,
                )
            )

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

    Args:
        policy: Can be ResilienceConfig (duck-typed with 'handlers'), a single Strategy,
               or SupervisionPolicy. We use Any here to avoid circular dependencies with
               complex Pydantic unions in the core spec.

    Returns:
        List of strategies extracted from the policy.
    """
    strategies: list[ResilienceStrategy] = []
    if hasattr(policy, "handlers"):
        strategies.extend([h.strategy for h in policy.handlers])
        if hasattr(policy, "default_strategy") and policy.default_strategy:
            strategies.append(policy.default_strategy)
    else:
        strategies.append(policy)
    return strategies


def _build_unified_adjacency_map(flow: LinearFlow | GraphFlow) -> dict[str, set[str]]:
    """
    Constructs a unified adjacency map for cycle detection.
    Includes sequential/graph edges, implicit SwitchNode routing, fallback routing, and global circuit breaker.
    """
    # 1. Initialize Map with strict type inference for node iteration
    nodes, edges_objs = get_unified_topology(flow)

    # SOTA Fix: Safe initialization without silent overwrites
    adj: dict[str, set[str]] = {}
    for node in nodes:
        if node.id not in adj:
            adj[node.id] = set()

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

        # SwitchNode routing
        if isinstance(node, SwitchNode):
            for target_id in node.cases.values():
                if target_id in adj:
                    adj[node.id].add(target_id)
            if node.default in adj:
                adj[node.id].add(node.default)

        # Local Fallback routing (Resolving templates to catch Trojan cycles)
        if node.resilience:
            resolved_policy = _resolve_resilience_policy(node.resilience, getattr(flow, "definitions", None))
            if resolved_policy:
                strategies = _extract_strategies(resolved_policy)
                for strategy in strategies:
                    if isinstance(strategy, FallbackStrategy) and strategy.fallback_node_id in adj:
                        adj[node.id].add(strategy.fallback_node_id)

    return adj


def _validate_budget_constraints(flow: LinearFlow | GraphFlow) -> list[ComplianceReport]:
    """
    Dynamically calculates the Maximum Cost Path using edge cost_weights to ensure
    the financial and latency limits are respected mathematically at compile-time.
    Uses Kahn's topological sort based dynamic programming algorithm.
    """
    errors: list[ComplianceReport] = []

    if not flow.governance or not flow.governance.operational_policy:
        return errors

    fin_limits = flow.governance.operational_policy.financial
    comp_limits = flow.governance.operational_policy.compute

    max_cost = fin_limits.max_cost_usd if fin_limits else None
    max_latency = comp_limits.max_execution_time_seconds if comp_limits else None

    if max_cost is None and max_latency is None:
        return errors

    # Only graph flows have explicitly weighted edges
    if not hasattr(flow, "graph"):
        return errors

    adj_map = _build_unified_adjacency_map(flow)

    # Need to handle explicitly weighted edges
    edge_weights: dict[tuple[str, str], tuple[float, float]] = {}
    if hasattr(flow, "graph"):
        for edge in flow.graph.edges:
            key = (edge.from_node, edge.to_node)
            existing_cost, existing_lat = edge_weights.get(key, (0.0, 0.0))

            # SOTA FinOps: If multiple conditional edges exist between two nodes,
            # enforce the mathematically safest worst-case upper bound.
            edge_weights[key] = (max(existing_cost, edge.cost_weight), max(existing_lat, edge.latency_weight_ms))

    from collections import defaultdict

    in_degree: dict[str, int] = defaultdict(int)
    for u in adj_map:
        for v in adj_map[u]:
            in_degree[v] += 1

    # Topological sort (Kahn's algorithm)
    dp_cost: dict[str, float] = defaultdict(float)
    dp_latency: dict[str, float] = defaultdict(float)

    topo_order = []
    zero_in = [u for u in adj_map if in_degree[u] == 0]

    while zero_in:
        u = zero_in.pop(0)
        topo_order.append(u)
        for v in adj_map[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                zero_in.append(v)

    # In case of cycles, length will not match. Fallback gracefully, as cycle detection handles cycles independently.
    if len(topo_order) != len(adj_map):
        errors.append(
            ComplianceReport(
                code="ERR_GOV_BUDGET_BYPASS",
                severity="warning",
                message="Budget Constraints Verification bypassed due to detected cycles in the DAG.",
            )
        )
        return errors

    for u in topo_order:
        for v in adj_map[u]:
            w_cost, w_latency = edge_weights.get((u, v), (0.0, 0.0))
            if dp_cost[u] + w_cost > dp_cost[v]:
                dp_cost[v] = dp_cost[u] + w_cost
            if dp_latency[u] + w_latency > dp_latency[v]:
                dp_latency[v] = dp_latency[u] + w_latency

    max_path_cost = max(dp_cost.values()) if dp_cost else 0.0
    max_path_latency_ms = max(dp_latency.values()) if dp_latency else 0.0

    if max_cost is not None and max_path_cost > max_cost:
        errors.append(
            ComplianceReport(
                code="ERR_GOV_INVALID_CONFIG",
                severity="violation",
                message=f"Budget Violation: Maximum possible path cost ({max_path_cost}) exceeds budget ({max_cost}).",
                details={"max_path_cost": max_path_cost, "max_cost_usd": max_cost},
            )
        )

    if max_latency is not None and (max_path_latency_ms / 1000.0) > max_latency:
        errors.append(
            ComplianceReport(
                code="ERR_GOV_INVALID_CONFIG",
                severity="violation",
                message=f"Budget Violation: Maximum possible path latency ({max_path_latency_ms / 1000.0}s) "
                f"exceeds budget ({max_latency}s).",
                details={"max_path_latency_ms": max_path_latency_ms, "max_latency_s": max_latency},
            )
        )

    nodes, _ = get_unified_topology(flow)
    for node in nodes:
        if node.type == "agent" and node.resilience:
            resolved_policy = _resolve_resilience_policy(node.resilience, getattr(flow, "definitions", None))
            if resolved_policy:
                strategies = _extract_strategies(resolved_policy)
                for strategy in strategies:
                    if getattr(strategy, "type", None) == "retry":
                        attempts = getattr(strategy, "max_attempts", 0)
                        if attempts > 5:
                            # Check for high cost model or RateCard
                            is_high_cost = False
                            if getattr(node, "profile", None) and getattr(node.profile, "reasoning", None):
                                primary_prof = getattr(node.profile.reasoning.models, "primary_profile", None)
                                if primary_prof and getattr(primary_prof, "pricing", None):
                                    is_high_cost = True

                            if is_high_cost:
                                errors.append(
                                    ComplianceReport(
                                        code="ERR_GOV_FINANCIAL_RISK",
                                        severity="warning",
                                        message=(
                                            f"Financial Risk: Agent node '{node.id}' has aggressive retry "
                                            "loop (max_attempts > 5) while using a cost-bearing model."
                                        ),
                                        details={"node_id": node.id, "max_attempts": attempts},
                                    )
                                )

    return errors


def _validate_kill_switch(flow: LinearFlow | GraphFlow) -> list[ComplianceReport]:
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


def _validate_middleware_refs(flow: LinearFlow | GraphFlow) -> list[ComplianceReport]:
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
