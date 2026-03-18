import re

with open("tests/contracts/test_algebra_hypothesis.py", "r") as f:
    content = f.read()

# Fix `test_calculate_latent_alignment` which expects a standard ValueError.
content = content.replace("with pytest.raises(Exception):", "with pytest.raises((ValueError, TamperFaultEvent), match=\"Latent alignment failed.\"):")
with open("tests/contracts/test_algebra_hypothesis.py", "w") as f:
    f.write(content)

with open("tests/contracts/test_algebra_coverage.py", "r") as f:
    content = f.read()

content = content.replace('match="Cannot replace at path /a/-: Cannot replace at path: Cannot extract from end of array"', 'match="Cannot replace at path /a/-: Cannot extract from end of array"')

with open("tests/contracts/test_algebra_coverage.py", "w") as f:
    f.write(content)
