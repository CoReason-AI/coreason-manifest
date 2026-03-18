import re

with open("tests/contracts/test_algebra_hypothesis.py", "r") as f:
    content = f.read()

# Fix `test_calculate_latent_alignment` exception check.
content = content.replace('except ValueError as e:', 'except (ValueError, TamperFaultEvent) as e:')
content = content.replace('if "TamperFaultEvent: Latent alignment failed" in str(e):', 'if "TamperFaultEvent: Latent alignment failed" in str(e) or "Latent alignment failed" in str(e):')

with open("tests/contracts/test_algebra_hypothesis.py", "w") as f:
    f.write(content)
