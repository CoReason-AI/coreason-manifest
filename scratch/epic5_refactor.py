# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Epic 5: Protocol & Security Purge - Line-based refactoring."""

ONTOLOGY = "src/coreason_manifest/spec/ontology.py"

with open(ONTOLOGY, encoding="utf-8") as f:
    lines = f.readlines()

original_count = len(lines)
print(f"Original line count: {original_count}")


def find_line(pattern, start=0):
    """Find first line containing pattern from start index."""
    for i in range(start, len(lines)):
        if pattern in lines[i]:
            return i
    return -1


def delete_range(start, end):
    """Delete lines from start to end (exclusive)."""
    del lines[start:end]
    return end - start


def find_method_end(start_idx):
    """Find the end of a method (next line at class indent level or blank + class/field)."""
    indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
    i = start_idx + 1
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        # End on: blank line followed by non-indented-more content, or dedent
        if stripped and not line.startswith(" " * (indent + 1)) and not stripped.startswith("#"):
            # This line is at same or lesser indent - method is over
            return i
        if stripped == "" and i + 1 < len(lines):
            next_line = lines[i + 1]
            next_stripped = next_line.strip()
            if next_stripped and not next_line.startswith(" " * (indent + 1)):
                return i + 1
        i += 1
    return i


def delete_method(method_name, field_decorator_text=None):
    """Delete a method including its decorator and docstring."""
    # Find the @field_validator or @model_validator decorator
    if field_decorator_text:
        idx = find_line(field_decorator_text)
    else:
        idx = find_line(f"def {method_name}")
        # Go back to find the decorator
        while idx > 0 and ("@field_validator" in lines[idx - 1] or "@classmethod" in lines[idx - 1]):
            idx -= 1

    if idx == -1:
        print(f"  WARNING: Could not find method {method_name}")
        return 0

    # Find the end of the method
    def_idx = idx
    while def_idx < len(lines) and f"def {method_name}" not in lines[def_idx]:
        def_idx += 1

    end = find_method_end(def_idx)

    # Also eat trailing blank lines
    while end < len(lines) and lines[end].strip() == "":
        end += 1
    # But leave one blank line
    if end > 0:
        end -= 1

    deleted = delete_range(idx, end)
    print(f"  Deleted {method_name}: {deleted} lines (was at line {idx + 1})")
    return deleted


# ============================================================
# Step 1: Delete imports
# ============================================================

for imp in [
    "import nh3\n",
    "import nh3\r\n",
    "import ipaddress\n",
    "import ipaddress\r\n",
    "import urllib.parse\n",
    "import urllib.parse\r\n",
]:
    idx = find_line(imp.strip())
    if idx >= 0:
        del lines[idx]
        print(f"  Deleted import: {imp.strip()}")

# ============================================================
# Step 2: Delete _validate_ssrf_safety function
# ============================================================

idx = find_line("def _validate_ssrf_safety(url: str)")
if idx >= 0:
    # Find function end (next top-level definition)
    end = idx + 1
    while end < len(lines):
        stripped = lines[end].strip()
        if (
            stripped
            and not lines[end].startswith(" ")
            and not lines[end].startswith("#")
            and stripped.startswith(("type ", "class ", "def "))
        ):
            break
        end += 1
    deleted = delete_range(idx, end)
    print(f"  Deleted _validate_ssrf_safety: {deleted} lines")

# ============================================================
# Step 3: Delete sanitize_markdown validator
# ============================================================

idx = find_line("def sanitize_markdown")
if idx >= 0:
    # Go back to @field_validator decorator
    dec_idx = idx
    while dec_idx > 0 and "@field_validator" not in lines[dec_idx]:
        dec_idx -= 1
    # Find end of method
    end = find_method_end(idx)
    # Eat trailing blank lines but keep one
    while end < len(lines) and lines[end].strip() == "":
        end += 1
    if end > dec_idx:
        end -= 1
    deleted = delete_range(dec_idx, end)
    print(f"  Deleted sanitize_markdown: {deleted} lines")

# ============================================================
# Step 4: Delete _enforce_spatial_safety (BrowserDOMState)
# ============================================================

idx = find_line("def _enforce_spatial_safety")
if idx >= 0:
    dec_idx = idx
    while dec_idx > 0 and "@field_validator" not in lines[dec_idx]:
        dec_idx -= 1
    end = find_method_end(idx)
    while end < len(lines) and lines[end].strip() == "":
        end += 1
    if end > dec_idx:
        end -= 1
    deleted = delete_range(dec_idx, end)
    print(f"  Deleted _enforce_spatial_safety: {deleted} lines")

# ============================================================
# Step 5: Delete all _enforce_ssrf_quarantine validators (loop until none left)
# ============================================================

while True:
    idx = find_line("def _enforce_ssrf_quarantine")
    if idx == -1:
        break
    dec_idx = idx
    while dec_idx > 0 and "@field_validator" not in lines[dec_idx]:
        dec_idx -= 1
    end = find_method_end(idx)
    while end < len(lines) and lines[end].strip() == "":
        end += 1
    if end > dec_idx:
        end -= 1
    deleted = delete_range(dec_idx, end)
    print(f"  Deleted _enforce_ssrf_quarantine: {deleted} lines (was at line {dec_idx + 1})")

# ============================================================
# Step 6: Delete _enforce_ssrf_safety (SPARQLQueryIntent)
# ============================================================

idx = find_line("def _enforce_ssrf_safety")
if idx >= 0:
    dec_idx = idx
    while dec_idx > 0 and "@field_validator" not in lines[dec_idx]:
        dec_idx -= 1
    end = find_method_end(idx)
    while end < len(lines) and lines[end].strip() == "":
        end += 1
    if end > dec_idx:
        end -= 1
    deleted = delete_range(dec_idx, end)
    print(f"  Deleted _enforce_ssrf_safety: {deleted} lines")

# ============================================================
# Step 7: Delete _prevent_crlf_injection validators (loop)
# ============================================================

while True:
    idx = find_line("def _prevent_crlf_injection")
    if idx == -1:
        break
    dec_idx = idx
    while dec_idx > 0 and "@field_validator" not in lines[dec_idx]:
        dec_idx -= 1
    end = find_method_end(idx)
    while end < len(lines) and lines[end].strip() == "":
        end += 1
    if end > dec_idx:
        end -= 1
    deleted = delete_range(dec_idx, end)
    print(f"  Deleted _prevent_crlf_injection: {deleted} lines")

# ============================================================
# Step 8: Update docstrings
# ============================================================

for i in range(len(lines)):
    line = lines[i]
    # BrowserDOMState EPISTEMIC BOUNDS
    if "Enforces strict Server-Side Request Forgery (SSRF) quarantine via" in line:
        lines[i] = line.replace(
            "Enforces strict Server-Side Request Forgery (SSRF) quarantine via the `@field_validator` `_enforce_spatial_safety`, mathematically isolating the agent from Bogon/private IP space. `dom_hash` rigidly locked to SHA-256 pattern.",
            "`dom_hash` rigidly locked to SHA-256 pattern.",
        )
    # BrowserDOMState MCP ROUTING TRIGGERS
    if "SSRF Quarantine, Spatial Execution Bound" in line:
        lines[i] = line.replace("SSRF Quarantine, ", "")
    # HTTPTransportProfile EPISTEMIC BOUNDS
    if "explicitly trapped by the `@field_validator` `_prevent_crlf_injection`" in line:
        lines[i] = line.replace(
            "mathematically bounded (`max_length=2000`) and explicitly trapped by the `@field_validator` `_prevent_crlf_injection` to physically block HTTP Request Smuggling.",
            "mathematically bounded (`max_length=2000`).",
        )
    # SSETransportProfile EPISTEMIC BOUNDS
    if "mathematically sanitized against CRLF injection via" in line:
        lines[i] = line.replace(
            "strictly limited via `StringConstraints` (`max_length=255/2000`) and mathematically sanitized against CRLF injection via `@field_validator` `_prevent_crlf_injection` to preserve protocol boundary integrity.",
            "strictly limited via `StringConstraints` (`max_length=255/2000`).",
        )
    # EvidentiaryCitationState EPISTEMIC BOUNDS
    if "Network resolution is strictly gated by the `_enforce_ssrf_quarantine` hook" in line:
        lines[i] = line.replace(
            "Network resolution is strictly gated by the `_enforce_ssrf_quarantine` hook to prevent Bogon/loopback execution. The textual premise",
            "The textual premise",
        )
    # SPARQLQueryIntent EPISTEMIC BOUNDS
    if "The target_endpoint implements an SSRF protection hook" in line:
        lines[i] = line.replace(
            "The target_endpoint implements an SSRF protection hook to mathematically reject lateral movement.",
            "The target_endpoint is a strictly typed HttpUrl.",
        )

print(f"\nFinal line count: {len(lines)} (deleted {original_count - len(lines)} lines)")

with open(ONTOLOGY, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Epic 5 ontology refactoring complete!")
