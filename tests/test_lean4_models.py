from hypothesis import given
from hypothesis import strategies as st

from coreason_manifest.spec.ontology import (
    EpistemicLean4Premise,
    Lean4VerificationReceipt,
    TacticStateGoal,
)

# A simple strategy to generate valid CIDs for testing
valid_cid_strategy = st.from_regex(r"^did:[a-z0-9]+:[a-zA-Z0-9.\-_:]+$", fullmatch=True).filter(lambda x: len(x) >= 7)


@given(
    target_theorem=st.text(max_size=65536),
    tactics_script=st.text(max_size=100000),
    dependency_graph_cids=st.lists(valid_cid_strategy, max_size=10) | st.none(),
)
def test_epistemic_lean4_premise_sorting(
    target_theorem: str, tactics_script: str, dependency_graph_cids: list[str] | None
) -> None:
    premise = EpistemicLean4Premise(
        target_theorem=target_theorem,
        tactics_script=tactics_script,
        dependency_graph_cids=dependency_graph_cids,
    )
    if dependency_graph_cids is not None:
        assert premise.dependency_graph_cids == sorted(dependency_graph_cids)
    else:
        assert premise.dependency_graph_cids is None


@given(
    hypothesis_context=st.lists(st.text(max_size=2000), max_size=10),
    target_type=st.text(max_size=2000),
    complexity_score=st.floats(min_value=0.0, max_value=1.0) | st.none(),
)
def test_tactic_state_goal_sorting(
    hypothesis_context: list[str], target_type: str, complexity_score: float | None
) -> None:
    goal = TacticStateGoal(
        hypothesis_context=hypothesis_context,
        target_type=target_type,
        complexity_score=complexity_score,
    )
    assert goal.hypothesis_context == sorted(hypothesis_context)


@given(
    is_proved=st.booleans(),
    tactic_state_trees=st.lists(
        st.builds(
            TacticStateGoal,
            hypothesis_context=st.lists(st.text(max_size=10), max_size=5),
            target_type=st.text(max_size=10),
            complexity_score=st.none(),
        ),
        max_size=5,
    )
    | st.none(),
)
def test_lean4_verification_receipt_sorting(is_proved: bool, tactic_state_trees: list[TacticStateGoal] | None) -> None:
    receipt = Lean4VerificationReceipt(
        is_proved=is_proved,
        tactic_state_tree=tactic_state_trees,
    )
    if tactic_state_trees is not None:
        assert receipt.tactic_state_tree is not None
        sorted_trees = sorted(tactic_state_trees, key=lambda x: x.target_type)
        for expected, actual in zip(sorted_trees, receipt.tactic_state_tree, strict=True):
            assert expected.target_type == actual.target_type
    else:
        assert receipt.tactic_state_tree is None
