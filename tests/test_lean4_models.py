from coreason_manifest.spec.ontology import (
    EpistemicLean4Premise,
    Lean4VerificationReceipt,
    TacticStateGoal,
)


def test_epistemic_lean4_premise_sorting():
    premise = EpistemicLean4Premise(
        target_theorem="theorem test : True",
        tactics_script="exact True.intro",
        dependency_graph_cids=[
            "did:example:3",
            "did:example:1",
            "did:example:2",
        ],
    )
    assert premise.dependency_graph_cids == [
        "did:example:1",
        "did:example:2",
        "did:example:3",
    ]


def test_tactic_state_goal_sorting():
    goal = TacticStateGoal(
        hypothesis_context=["h2 : B", "h1 : A"],
        target_type="C",
        complexity_score=0.5,
    )
    assert goal.hypothesis_context == ["h1 : A", "h2 : B"]


def test_lean4_verification_receipt_sorting():
    receipt = Lean4VerificationReceipt(
        is_proved=False,
        tactic_state_tree=[
            TacticStateGoal(hypothesis_context=["h : B"], target_type="C"),
            TacticStateGoal(hypothesis_context=["h : A"], target_type="B"),
        ],
    )

    assert receipt.tactic_state_tree is not None
    assert receipt.tactic_state_tree[0].target_type == "B"
    assert receipt.tactic_state_tree[1].target_type == "C"
