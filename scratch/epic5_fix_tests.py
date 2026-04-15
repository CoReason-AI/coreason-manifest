# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Fix remaining test files that reference deleted SSRF/CRLF validators."""

import re

# Files to patch
patches = {
    # test_browser_dom_state.py - delete SSRF test functions
    "tests/fuzzing/test_browser_dom_state.py": [
        # Delete the parametrized SSRF test functions but keep others
    ],
    # test_boundaries.py - delete the SSRF quarantine test
    "tests/fuzzing/test_boundaries.py": [],
    # test_ontology_validators.py - fix SSRF references
    "tests/contracts/test_ontology_validators.py": [],
    # test_coverage_gaps.py - delete CRLF injection tests
    "tests/contracts/test_coverage_gaps.py": [],
    # test_ontology_coverage.py - delete SSRF tests
    "tests/fuzzing/test_ontology_coverage.py": [],
    # test_protocols.py - delete SSRF/CRLF tests
    "tests/fuzzing/test_protocols.py": [],
}


def delete_function(content, func_name):
    """Delete a test function and its decorator (if parametrize)."""
    # Find the function definition
    pattern = rf"^def {func_name}\(.*?\n(?=\n(?:def |class |@|$))"
    match = re.search(pattern, content, flags=re.MULTILINE | re.DOTALL)
    if match:
        # Check for preceding decorator(s)
        start = match.start()
        # Walk backwards to find decorators
        lines = content[:start].split("\n")
        while lines and lines[-1].strip() == "":
            lines.pop()
        while lines and (
            lines[-1].strip().startswith("@")
            or lines[-1].strip().startswith('"')
            or lines[-1].strip().startswith("'")
            or lines[-1].strip() == "],"
            or lines[-1].strip() == "]"
            or lines[-1].strip() == ")"
        ):
            lines.pop()
        new_start = len("\n".join(lines)) + 1 if lines else 0
        content = content[:new_start] + content[match.end() :]
        print(f"  Deleted function: {func_name}")
    else:
        print(f"  WARNING: Could not find function: {func_name}")
    return content


def delete_class(content, class_name):
    """Delete a test class."""
    pattern = rf"^class {class_name}.*?\n(?=\n(?:def |class |@|$))"
    match = re.search(pattern, content, flags=re.MULTILINE | re.DOTALL)
    if match:
        content = content[: match.start()] + content[match.end() :]
        print(f"  Deleted class: {class_name}")
    else:
        print(f"  WARNING: Could not find class: {class_name}")
    return content


# ============================================================
# Fix test_browser_dom_state.py
# ============================================================
filepath = "tests/fuzzing/test_browser_dom_state.py"
with open(filepath, encoding="utf-8") as f:
    content = f.read()

# Remove all SSRF-specific parametrized test blocks
# These test BrowserDOMState with bogon IPs
tests_to_remove = [
    # Lines matching SSRF test functions
]

# Replace entire blocks that test SSRF
# Find and remove test_browser_dom_state_rejects_*, test_browser_dom_state_bogon_*
for func_name in [
    "test_browser_dom_state_rejects_private_ips",
    "test_browser_dom_state_rejects_loopback_ips",
    "test_browser_dom_state_rejects_reserved_ips",
]:
    content = delete_function(content, func_name)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print(f"Fixed: {filepath}")

# ============================================================
# Fix test_boundaries.py - delete SSRF quarantine test
# ============================================================
filepath = "tests/fuzzing/test_boundaries.py"
with open(filepath, encoding="utf-8") as f:
    content = f.read()

content = delete_function(content, "test_browser_dom_ssrf_quarantine")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print(f"Fixed: {filepath}")

# ============================================================
# Fix test_ontology_validators.py - remove SSRF expectations
# ============================================================
filepath = "tests/contracts/test_ontology_validators.py"
with open(filepath, encoding="utf-8") as f:
    content = f.read()

# Fix the comment reference
content = content.replace(
    "    # It might still trigger SSRF validation if hypothesis generates a local-looking domain,",
    "    # Hypothesis may generate domains that pass structural validation,",
)

# Remove the SSRF-related test assertions in test_browser_dom_state_fuzz
# These are pytest.raises blocks matching SSRF
content = content.replace(
    '    with pytest.raises(ValidationError, match=r"SSRF|validation error"):\n',
    "    with pytest.raises(ValidationError):\n",
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print(f"Fixed: {filepath}")

# ============================================================
# Fix test_coverage_gaps.py - delete CRLF injection tests
# ============================================================
filepath = "tests/contracts/test_coverage_gaps.py"
with open(filepath, encoding="utf-8") as f:
    content = f.read()

content = delete_class(content, "TestSSETransportCRLFInjection")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print(f"Fixed: {filepath}")

# ============================================================
# Fix test_ontology_coverage.py - delete SSRF tests
# ============================================================
filepath = "tests/fuzzing/test_ontology_coverage.py"
with open(filepath, encoding="utf-8") as f:
    content = f.read()

for func_name in [
    "test_browser_dom_state_ssrf_quarantine_hypothesis",
    "test_browser_dom_state_bogon_ssrf_strict",
    "test_browser_dom_state_invalid_hostname_ssrf",
]:
    content = delete_function(content, func_name)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print(f"Fixed: {filepath}")

# ============================================================
# Fix test_protocols.py - delete SSRF/CRLF tests
# ============================================================
filepath = "tests/fuzzing/test_protocols.py"
with open(filepath, encoding="utf-8") as f:
    content = f.read()

for func_name in ["test_fuzz_browser_dom_ssrf_ips", "test_fuzz_http_transport_profile_crlf"]:
    content = delete_function(content, func_name)

# Remove SSRF comment
content = content.replace("    # 2. BrowserDOMState SSRF Isolation\n", "")
content = content.replace("    # 3. HTTPTransportProfile CRLF\n", "")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print(f"Fixed: {filepath}")

print("\nAll test files fixed!")
