import pytest
from pydantic import ValidationError

from coreason_manifest.core.workflow.contracts import ActionNode, AtomicSkill, StrategyNode
from coreason_manifest.core.workflow.nodes import PlannerNode


def test_htn_immutability() -> None:
    skill = AtomicSkill(id="s1", description="skill")
    action = ActionNode(id="a1", description="action", skill=skill)
    strategy = StrategyNode(id="str1", goal="goal", strategy_name="ReAct", children=[])

    with pytest.raises(ValidationError):
        setattr(skill, "id", "s2")  # noqa: B010

    with pytest.raises(ValidationError):
        setattr(action, "id", "a2")  # noqa: B010

    with pytest.raises(ValidationError):
        setattr(strategy, "id", "str2")  # noqa: B010


def test_planner_node_output_schema_validation() -> None:
    # Valid output_schema
    PlannerNode(id="p1", type="planner", goal="goal", output_schema={"type": "object"})
    PlannerNode(id="p2", type="planner", goal="goal", output_schema={"type": "array"})

    # Invalid output_schema
    with pytest.raises(
        ValidationError, match=r"PlannerNode output_schema must define an object or array representing the PlanTree\."
    ):
        PlannerNode(id="p3", type="planner", goal="goal", output_schema={"type": "string"})

    with pytest.raises(
        ValidationError, match=r"PlannerNode output_schema must define an object or array representing the PlanTree\."
    ):
        PlannerNode(id="p4", type="planner", goal="goal", output_schema={"type": "integer"})
