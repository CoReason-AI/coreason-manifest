with open("tests/contracts/test_epistemic_zero_trust.py") as f:
    content = f.read()

new_content = (
    content
    + """
def test_epistemic_constraint_policy_invalid_type():
    with pytest.raises(ValidationError):
        EpistemicConstraintPolicy(
            assertion_ast=123,
            remediation_prompt="test"
        )
"""
)
with open("tests/contracts/test_epistemic_zero_trust.py", "w") as f:
    f.write(new_content)
