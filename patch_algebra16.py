import re

with open("tests/contracts/test_algebra_hypothesis.py", "r") as f:
    content = f.read()

# Fix `test_calculate_latent_alignment`
content = content.replace("with pytest.raises((ValueError, TamperFaultEvent), match=\"Latent alignment failed.\"):", "with pytest.raises(TamperFaultEvent, match=\"Latent alignment failed.\"):")

with open("tests/contracts/test_algebra_hypothesis.py", "w") as f:
    f.write(content)
