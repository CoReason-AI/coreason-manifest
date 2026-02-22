import pytest
from typing import Any, cast
from coreason_manifest.spec.core.flow import (
    DataSchema, Edge, VariableDef, GraphFlow, FlowInterface, Graph, FlowMetadata
)
from coreason_manifest.spec.interop.antibody import AntibodyBase, _scan_and_quarantine
from coreason_manifest.utils.validator import validate_flow
from coreason_manifest.spec.core.nodes import InspectorNode


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
    gf = GraphFlow.model_validate({
        "type": "graph",
        "metadata": {"name": "test", "version": "1.0"},
        "interface": {},
        "graph": {"nodes": {}, "edges": []},
        "blackboard": None
    })
    assert gf.blackboard is not None

# --- antibody.py coverage ---

class Container(AntibodyBase):
    data: dict[str, Any] | list[Any]

def test_antibody_recursion_dict() -> None:
    c = Container(data={"nested": {"val": float("nan")}})
    d = cast(dict[str, Any], c.data)
    assert isinstance(d["nested"]["val"], dict)
    assert d["nested"]["val"]["code"] == "CRSN-ANTIBODY-FLOAT"

def test_antibody_recursion_list() -> None:
    c = Container(data=[{"val": float("nan")}])
    l = cast(list[Any], c.data)
    assert isinstance(l[0]["val"], dict)
    assert l[0]["val"]["code"] == "CRSN-ANTIBODY-FLOAT"

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

# --- validator.py coverage ---

def test_validator_symbol_table_sorting() -> None:
    schema = {
        "type": "object",
        "properties": {
            "p1": {"type": ["string", "null", "integer"]}
        }
    }
    gf = GraphFlow(
        metadata=FlowMetadata(name="t", version="1"),
        interface=FlowInterface(inputs=DataSchema(json_schema=schema)),
        graph=Graph(nodes={}, edges=[])
    )
    validate_flow(gf)

def test_validator_inspector_attributes() -> None:
    insp = InspectorNode(
        id="insp1", type="inspector",
        target_variable="missing_target",
        output_variable="missing_output",
        criteria="c",
        judge_model="gpt-4"
    )

    gf = GraphFlow(
        metadata=FlowMetadata(name="t", version="1"),
        interface=FlowInterface(),
        graph=Graph(nodes={"insp1": insp}, edges=[])
    )

    reports = validate_flow(gf)
    assert any("inspects missing variable 'missing_target'" in r for r in reports)
