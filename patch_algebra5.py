import re

with open("src/coreason_manifest/utils/algebra.py", "r") as f:
    content = f.read()

# Update test_generate_correction_prompt_missing_and_invalid
content = content.replace('msg = err.get("msg", "Invalid structural payload.")', 'msg = err.get("msg", "Invalid structural payload.")\n        if err_type == "missing":\n            msg = f"The required semantic boundary at \'{loc_path}\' is completely missing. You must project this missing dimension to satisfy the StateContract."')


# Update apply_state_differential to properly catch KeyError/IndexError inside _extract_from_target for replace ops
content = content.replace("raise ValueError(\"Key not found\")", "raise ValueError(f\"Key not found\")")

with open("src/coreason_manifest/utils/algebra.py", "w") as f:
    f.write(content)
