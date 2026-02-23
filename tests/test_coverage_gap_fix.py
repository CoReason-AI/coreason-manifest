from datetime import datetime
from typing import Any, cast

import pytest

from coreason_manifest.spec.core.flow import (
    DataSchema,
    Edge,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
    LinearFlow,
    VariableDef,
)
from coreason_manifest.spec.core.nodes import (
    AgentNode,
    HumanNode,
    InspectorNode,
    SwarmNode,
)
from coreason_manifest.spec.interop.antibody import AntibodyBase, _get_anomaly, _scan_and_quarantine
from coreason_manifest.spec.interop.exceptions import FaultSeverity, ManifestError, RecoveryAction, SemanticFault
from coreason_manifest.spec.interop.telemetry import NodeExecution, NodeState
from coreason_manifest.utils.gatekeeper import _is_guarded
from coreason_manifest.utils.integrity import compute_hash
from coreason_manifest.utils.validator import validate_flow

# --- flow.py coverage ---


def test_flow_compat_json_schema() -> None:
    ds = DataSchema.model_validate({"schema": {"type": "string"}})
    assert ds.json_schema == {"type": "string"}


def test_flow_compat_source_target() -> None:
    e = Edge.model_validate({"source": "a", "target": "b"})
    assert e.from_node == "a"
    assert e.to_node == "b"


def test_flow_compat_id_name() -> None:
    v = VariableDef.model_validate({"name": "var1", "type": "string"})
    assert v.id == "var1"


def test_flow_compat_blackboard() -> None:
    gf = GraphFlow.model_validate(
        {
            "type": "graph",
            "metadata": {"name": "test", "version": "1.0"},
            "interface": {},
            "graph": {"nodes": {}, "edges": []},
            "blackboard": None,
        }
    )
    assert gf.blackboard is not None


def test_flow_compat_sequence() -> None:
    # Ensure sequence is aliased to steps or handled by compat_sequence
    lf = LinearFlow.model_validate(
        {
            "type": "linear",
            "metadata": {"name": "test", "version": "1.0"},
            "interface": {},
            "sequence": [{"id": "n1", "type": "placeholder", "required_capabilities": []}],
        }
    )
    assert len(lf.steps) == 1
    assert lf.steps[0].id == "n1"


# --- antibody.py coverage ---


class Container(AntibodyBase):
    data: dict[str, Any] | list[Any]


def test_antibody_recursion_dict() -> None:
    c = Container(data={"nested": {"val": float("nan")}})
    d = cast("dict[str, Any]", c.data)
    assert isinstance(d["nested"]["val"], dict)
    assert d["nested"]["val"]["code"] == "CRSN-ANTIBODY-FLOAT"


def test_antibody_recursion_list() -> None:
    c = Container(data=[{"val": float("nan")}])
    data_list = cast("list[Any]", c.data)
    assert isinstance(data_list[0]["val"], dict)
    assert data_list[0]["val"]["code"] == "CRSN-ANTIBODY-FLOAT"


def test_antibody_float_nan_dict() -> None:
    data: dict[str, Any] = {"val": float("nan")}
    _scan_and_quarantine(data, "$")
    assert isinstance(data["val"], dict)
    assert data["val"]["code"] == "CRSN-ANTIBODY-FLOAT"


def test_antibody_float_nan_list() -> None:
    data: list[Any] = [float("nan")]
    _scan_and_quarantine(data, "$")
    assert isinstance(data[0], dict)
    assert data[0]["code"] == "CRSN-ANTIBODY-FLOAT"


def test_antibody_get_anomaly_direct() -> None:
    res = _get_anomaly(float("nan"), "$")
    assert res is not None
    assert res["code"] == "CRSN-ANTIBODY-FLOAT"

    res2 = _get_anomaly(object(), "$")
    assert res2 is not None
    assert res2["code"] == "CRSN-ANTIBODY-UNSERIALIZABLE"


# --- telemetry.py coverage ---


def test_telemetry_envelope_consistency() -> None:
    ts = datetime.now()
    data = {
        "node_id": "n1",
        "state": NodeState.COMPLETED,
        "inputs": {},
        "outputs": {},
        "timestamp": ts,
        "duration_ms": 1.0,
        "traceparent": None,
        "tracestate": None,
        "parent_hashes": [],
        "hash_version": "v2",
    }
    ne = NodeExecution.model_validate(data)
    assert ne.request_id is not None
    assert ne.root_request_id == ne.request_id

    # Test topology consistency
    data2 = {**data, "parent_hash": "abc"}
    ne2 = NodeExecution.model_validate(data2)
    assert ne2.parent_hashes == ["abc"]


def test_telemetry_trace_integrity() -> None:
    ts = datetime.now()
    # Test orphan trace validation
    with pytest.raises(ValueError, match="Orphaned trace detected"):
        NodeExecution(
            node_id="n1",
            state=NodeState.COMPLETED,
            inputs={},
            outputs={},
            timestamp=ts,
            duration_ms=1.0,
            parent_request_id="parent_id",
            root_request_id=None,
        )


# --- nodes.py coverage ---


def test_nodes_human_magic_numbers() -> None:
    # Magic numbers are NO LONGER COERCED in V2.
    # Passing -1 should result in -1.
    hn = HumanNode.model_validate({"id": "h1", "type": "human", "prompt": "p", "timeout_seconds": -1})
    assert hn.timeout_seconds == -1

    hn2 = HumanNode.model_validate(
        {
            "id": "h2",
            "type": "human",
            "prompt": "p",
            # Removed timeout_seconds to avoid validation error for shadow mode
            "timeout_seconds": None,
            "interaction_mode": "shadow",
            "shadow_timeout_seconds": -1,
        }
    )
    assert hn2.shadow_timeout_seconds == -1


def test_nodes_human_validation() -> None:
    # Test interaction mode validation
    with pytest.raises(ManifestError) as exc:
        HumanNode(
            id="h3",
            type="human",
            prompt="p",
            interaction_mode="shadow",
            shadow_timeout_seconds=None,
            timeout_seconds=None,
        )
    assert exc.value.fault.error_code == "CRSN-VAL-HUMAN-SHADOW"

    with pytest.raises(ManifestError) as exc:
        HumanNode(
            id="h4",
            type="human",
            prompt="p",
            interaction_mode="shadow",
            shadow_timeout_seconds=300,
            timeout_seconds=100,
        )
    assert exc.value.fault.error_code == "CRSN-VAL-HUMAN-TIMEOUT"

    with pytest.raises(ManifestError) as exc:
        HumanNode(
            id="h5",
            type="human",
            prompt="p",
            interaction_mode="blocking",
            shadow_timeout_seconds=300,
            timeout_seconds=None,
        )
    assert exc.value.fault.error_code == "CRSN-VAL-HUMAN-BLOCKING"


def test_nodes_swarm_magic_numbers() -> None:
    sn = SwarmNode.model_validate(
        {
            "id": "s1",
            "type": "swarm",
            "worker_profile": "p1",
            "workload_variable": "w",
            "distribution_strategy": "sharded",
            "reducer_function": "concat",
            "output_variable": "o",
            "max_concurrency": -1,
        }
    )
    assert sn.max_concurrency == -1


def test_nodes_swarm_validation() -> None:
    with pytest.raises(ManifestError) as exc:
        SwarmNode(
            id="s2",
            type="swarm",
            worker_profile="p1",
            workload_variable="w",
            distribution_strategy="sharded",
            reducer_function="summarize",
            output_variable="o",
            aggregator_model=None,
            max_concurrency=10,
        )
    assert exc.value.fault.error_code == "CRSN-VAL-SWARM-REDUCER"


def test_nodes_inspector_property() -> None:
    insp = InspectorNode(id="i1", type="inspector", target_variable="t", output_variable="o", criteria="c")
    assert insp.to_node_variable == "t"


# --- exceptions.py coverage ---


def test_exceptions_manifest_error() -> None:
    fault = SemanticFault(
        error_code="TEST-001", message="msg", severity=FaultSeverity.CRITICAL, recovery_action=RecoveryAction.HALT
    )
    err = ManifestError(fault)
    # Match the new __str__ format
    assert str(err) == "[TEST-001] msg (Severity: CRITICAL)"
    assert err.fault == fault


# --- integrity.py coverage ---


def test_integrity_set_sorting() -> None:
    # Test mixed types in set sorting don't crash compute_hash
    data = {"s": {1, "a"}}
    h = compute_hash(data)
    assert len(h) == 64


# --- gatekeeper.py coverage ---


def test_gatekeeper_is_guarded() -> None:
    human = HumanNode(id="h1", type="human", prompt="p", timeout_seconds=100)
    agent = AgentNode(id="a1", type="agent", profile="p1")

    lf = LinearFlow(metadata=FlowMetadata(name="t", version="1"), steps=[human, agent])
    assert _is_guarded(agent, lf) is True

    lf2 = LinearFlow(metadata=FlowMetadata(name="t", version="1"), steps=[agent, human])
    assert _is_guarded(agent, lf2) is False


# --- validator.py coverage ---


def test_validator_symbol_table_sorting() -> None:
    schema = {"type": "object", "properties": {"p1": {"type": ["string", "null", "integer"]}}}
    gf = GraphFlow(
        metadata=FlowMetadata(name="t", version="1"),
        interface=FlowInterface(inputs=DataSchema(json_schema=schema)),
        graph=Graph(nodes={}, edges=[]),
    )
    validate_flow(gf)


def test_validator_inspector_attributes() -> None:
    insp = InspectorNode(
        id="insp1",
        type="inspector",
        target_variable="missing_target",
        output_variable="missing_output",
        criteria="c",
        judge_model="gpt-4",
    )

    gf = GraphFlow(
        metadata=FlowMetadata(name="t", version="1"),
        interface=FlowInterface(),
        graph=Graph(nodes={"insp1": insp}, edges=[]),
    )

    reports = validate_flow(gf)
    assert any("inspects missing variable 'missing_target'" in r for r in reports)


def test_integrity_type_error() -> None:
    # Trigger TypeError in _recursive_sort_and_sanitize
    class Unhashable:
        pass

    with pytest.raises(TypeError, match="is not deterministically serializable"):
        compute_hash(Unhashable())
