from coreason_manifest.core.workflow.nodes import Constraint, ConstraintOperator
from coreason_manifest.toolkit.builder import AgentBuilder
from coreason_manifest.toolkit.validator import _validate_data_flow


def test_constraint_schema() -> None:
    c = Constraint(variable="foo", operator=ConstraintOperator.EQ, value=42)
    assert c.variable == "foo"  # noqa: S101
    assert c.operator == ConstraintOperator.EQ  # noqa: S101
    assert c.value == 42  # noqa: S101
    assert c.required is True  # noqa: S101


def test_builder_with_constraint() -> None:
    builder = (
        AgentBuilder("test_agent")
        .with_identity("Analyst", "You analyze data.")
        .with_constraint("data.row_count", "gt", 100)
    )
    agent = builder.build()
    assert len(agent.constraints) == 1  # noqa: S101
    assert agent.constraints[0].variable == "data.row_count"  # noqa: S101
    assert agent.constraints[0].operator == ConstraintOperator.GT  # noqa: S101
    assert agent.constraints[0].value == 100  # noqa: S101


def test_validate_data_flow_missing_var() -> None:
    builder = (
        AgentBuilder("test_agent")
        .with_identity("Analyst", "You analyze data.")
        .with_constraint("data.row_count", "gt", 100)
    )
    agent = builder.build()

    # Empty symbol table -> "data" is missing
    reports = _validate_data_flow([agent], {}, None)

    assert len(reports) == 1  # noqa: S101
    assert reports[0].code == "ERR_CAP_MISSING_VAR"  # noqa: S101
    assert "Constraint Error" in reports[0].message  # noqa: S101
    assert "missing variable 'data.row_count'" in reports[0].message  # noqa: S101


def test_validate_data_flow_existing_var() -> None:
    builder = (
        AgentBuilder("test_agent")
        .with_identity("Analyst", "You analyze data.")
        .with_constraint("data.row_count", "gt", 100)
    )
    agent = builder.build()

    # "data" exists in symbol table
    reports = _validate_data_flow([agent], {"data": "object"}, None)

    assert len(reports) == 0  # noqa: S101
