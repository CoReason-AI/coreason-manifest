from coreason_manifest.core.workflow.nodes import Constraint, ConstraintOperator
from coreason_manifest.toolkit.builder import AgentBuilder
from coreason_manifest.toolkit.validator import _validate_data_flow


def test_constraint_schema() -> None:
    c = Constraint(variable="foo", operator=ConstraintOperator.EQ, value=42)
    assert c.variable == "foo"
    assert c.operator == ConstraintOperator.EQ
    assert c.value == 42
    assert c.required is True


def test_builder_with_constraint() -> None:
    builder = (
        AgentBuilder("test_agent")
        .with_identity("Analyst", "You analyze data.")
        .with_constraint("data.row_count", "gt", 100)
    )
    agent = builder.build()
    assert len(agent.constraints) == 1
    assert agent.constraints[0].variable == "data.row_count"
    assert agent.constraints[0].operator == ConstraintOperator.GT
    assert agent.constraints[0].value == 100


def test_validate_data_flow_missing_var() -> None:
    builder = (
        AgentBuilder("test_agent")
        .with_identity("Analyst", "You analyze data.")
        .with_constraint("data.row_count", "gt", 100)
    )
    agent = builder.build()

    # Empty symbol table -> "data" is missing
    reports = _validate_data_flow([agent], {}, None)

    assert len(reports) == 1
    assert reports[0].code == "ERR_CAP_MISSING_VAR"
    assert "Constraint Error" in reports[0].message
    assert "missing variable 'data.row_count'" in reports[0].message


def test_validate_data_flow_existing_var() -> None:
    builder = (
        AgentBuilder("test_agent")
        .with_identity("Analyst", "You analyze data.")
        .with_constraint("data.row_count", "gt", 100)
    )
    agent = builder.build()

    # "data" exists in symbol table
    reports = _validate_data_flow([agent], {"data": "object"}, None)

    assert len(reports) == 0
