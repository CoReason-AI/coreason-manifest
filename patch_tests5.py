with open("tests/contracts/test_domain_extensions.py", "r") as f:
    content = f.read()

test_extension = """
def test_all_extension_cases() -> None:
    # Just extra test for coverage of DifferentiableLogicConstraint with invalid dict
    with pytest.raises(ValidationError):
        DifferentiableLogicConstraint.model_validate(
            {
                "constraint_id": "c1",
                "formal_syntax_smt": "(assert (= x y))",
                "relaxation_epsilon": 0.1,
                "anomaly_classification": "logic_flaw",
                "solver_status": "sat",
                "some_dict": {"ext:invalid_key": "v"}
            },
            context={"allowed_ext_intents": set()}
        )

    with pytest.raises(ValidationError):
        DifferentiableLogicConstraint.model_validate(
            {
                "constraint_id": "c1",
                "formal_syntax_smt": "(assert (= x y))",
                "relaxation_epsilon": 0.1,
                "anomaly_classification": "logic_flaw",
                "solver_status": "sat",
                "some_dict": {"k": "ext:invalid_val"}
            },
            context={"allowed_ext_intents": set()}
        )

    # Same for BargeInInterruptEvent
    with pytest.raises(ValidationError):
        BargeInInterruptEvent.model_validate(
            {
                "event_id": "e2",
                "timestamp": 100.0,
                "target_event_id": "t2",
                "epistemic_disposition": "discard",
                "disfluency_type": "repair",
                "evicted_token_count": 5,
                "some_dict": {"ext:invalid_key": "v"}
            },
            context={"allowed_ext_intents": set()}
        )

    with pytest.raises(ValidationError):
        BargeInInterruptEvent.model_validate(
            {
                "event_id": "e2",
                "timestamp": 100.0,
                "target_event_id": "t2",
                "epistemic_disposition": "discard",
                "disfluency_type": "repair",
                "evicted_token_count": 5,
                "some_dict": {"k": "ext:invalid_val"}
            },
            context={"allowed_ext_intents": set()}
        )

    # Same for EpistemicAxiomState
    with pytest.raises(ValidationError):
        EpistemicAxiomState.model_validate(
            {
                "source_concept_id": "s2",
                "directed_edge_type": "is_a",
                "target_concept_id": "t2",
                "some_dict": {"ext:invalid_key": "v"}
            },
            context={"allowed_ext_intents": set()}
        )

    with pytest.raises(ValidationError):
        EpistemicAxiomState.model_validate(
            {
                "source_concept_id": "s2",
                "directed_edge_type": "is_a",
                "target_concept_id": "t2",
                "some_dict": {"k": "ext:invalid_val"}
            },
            context={"allowed_ext_intents": set()}
        )

"""

if "test_all_extension_cases" not in content:
    content += "\n" + test_extension
    with open("tests/contracts/test_domain_extensions.py", "w") as f:
        f.write(content)
