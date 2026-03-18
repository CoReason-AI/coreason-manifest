import re

with open("tests/contracts/test_algebra_hypothesis.py", "r") as f:
    content = f.read()

content = content.replace("with pytest.raises(Exception):", "with pytest.raises((ValueError, TamperFaultEvent)):")
with open("tests/contracts/test_algebra_hypothesis.py", "w") as f:
    f.write(content)
