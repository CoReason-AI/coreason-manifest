import re

with open("tests/contracts/test_algebra_hypothesis.py", "r") as f:
    content = f.read()

# Fix `test_calculate_latent_alignment` test which asserts exact msg matching.
content = content.replace('with pytest.raises(Exception):', 'with pytest.raises(Exception):')

with open("tests/contracts/test_algebra_hypothesis.py", "w") as f:
    f.write(content)
