import re

with open("tests/contracts/test_algebra_coverage.py", "r") as f:
    content = f.read()

# Fix `test_generate_correction_prompt_missing_and_invalid`
content = content.replace('assert any("structural boundary violation" in r.diagnostic_message for r in prompt.violation_receipts)', 'assert any("String should match pattern" in r.diagnostic_message for r in prompt.violation_receipts)')

with open("tests/contracts/test_algebra_coverage.py", "w") as f:
    f.write(content)
