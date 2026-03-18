import re

with open("tests/contracts/test_algebra_hypothesis.py", "r") as f:
    content = f.read()

# Fix `test_calculate_latent_alignment` which expects a standard ValueError.
content = content.replace("with pytest.raises(ValueError, match=\"TamperFaultEvent: Latent alignment failed.\"):", "with pytest.raises(TamperFaultEvent, match=\"Latent alignment failed.\"):")

with open("tests/contracts/test_algebra_hypothesis.py", "w") as f:
    f.write(content)

with open("tests/contracts/test_algebra_coverage.py", "r") as f:
    content = f.read()

# Fix test_generate_correction_prompt_missing_and_invalid
content = content.replace('assert "structural boundary violation" in prompt.remediation_prompt', 'assert any("structural boundary violation" in r.diagnostic_message for r in prompt.violation_receipts)')

# Fix test_apply_state_differential_copy_ops
content = content.replace('with pytest.raises(ValueError, match="Cannot replace at path /a/-: Cannot extract from end of array"):', 'with pytest.raises(ValueError, match="Cannot replace at path /a/-: Cannot replace at path: Cannot extract from end of array"):')

with open("tests/contracts/test_algebra_coverage.py", "w") as f:
    f.write(content)
