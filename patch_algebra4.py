import re

with open("src/coreason_manifest/utils/algebra.py", "r") as f:
    content = f.read()

# Fix `test_generate_correction_prompt_missing_and_invalid`
content = content.replace("msg = err.get(\"msg\", \"Invalid structural payload.\")", "msg = err.get(\"msg\", \"Invalid structural payload.\")\n        if err_type == \"missing\":\n            msg = f\"The required semantic boundary at '{loc_path}' is completely missing. You must project this missing dimension to satisfy the StateContract.\"")


# Fix `test_calculate_latent_alignment` which expects a standard ValueError wrapped with 'TamperFaultEvent: ...' from the old implementation
# Wait, the instruction specifically said:
# "Change this to directly raise the properly typed exception: `raise TamperFaultEvent(\"Latent alignment failed.\")`"
# Let's check the test: it seems the test expects the exception type to be ValueError? No, the test failed because it raised TamperFaultEvent and the test was not updated? Wait, I shouldn't modify the tests if I can avoid it. But the issue specifically requested raising TamperFaultEvent. Wait, is TamperFaultEvent derived from ValueError? Yes, `class TamperFaultEvent(ValueError):`. But in the test it raises a plain ValueError or TamperFaultEvent?
# Let's look at the failing test:
# E           coreason_manifest.spec.ontology.TamperFaultEvent: Latent alignment failed.
# E           Falsifying example: test_calculate_latent_alignment(
# The Hypothesis test hit this. The issue says: "Change this to directly raise the properly typed exception: raise TamperFaultEvent("Latent alignment failed.")"
# Let me see `test_algebra_hypothesis.py` line 79.
pass
