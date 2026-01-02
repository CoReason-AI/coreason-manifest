package coreason.compliance

import data.tbom

default allow = false

# Deny if 'pickle' is in libraries
deny[msg] {
    some i
    input.dependencies.libraries[i] == "pickle"
    msg := "Security Risk: 'pickle' library is strictly forbidden."
}

# Deny if 'os' is in libraries (just another example)
deny[msg] {
    some i
    input.dependencies.libraries[i] == "os"
    msg := "Security Risk: 'os' library is strictly forbidden."
}

# Deny if description is too short (Business Rule example)
deny[msg] {
    count(input.topology.steps) > 0
    count(input.topology.steps[0].description) < 5
    msg := "Step description is too short."
}

# Rule 1 (Dependency Pinning): All library dependencies must have explicit version pins
deny[msg] {
    some i
    lib := input.dependencies.libraries[i]
    # Check if '==' exists in the string
    # We use regex matching.
    # Logic: If it does NOT match pinned format, deny.
    not regex.match(".*==.*", lib)
    msg := sprintf("Compliance Violation: Library '%v' must be pinned with '=='.", [lib])
}

# Rule 2 (Allowlist Enforcement): Libraries must be in TBOM
deny[msg] {
    some i
    lib_str := input.dependencies.libraries[i]

    # Extract library name using regex (matches characters before any '==' or other version specifiers)
    # We assume the name is at the start.
    # Pattern: ^([a-zA-Z0-9_\-]+)
    # Note: Regex parsing in Rego returns an array of matches.
    # regex.find_all_string_submatch_n(pattern, value, number)
    parts := regex.find_all_string_submatch_n("^[a-zA-Z0-9_\\-]+", lib_str, 1)
    count(parts) > 0
    lib_name := parts[0][0]

    # Check if lib_name is in tbom
    not array_contains(tbom, lib_name)

    msg := sprintf("Compliance Violation: Library '%v' is not in the Trusted Bill of Materials (TBOM).", [lib_name])
}

array_contains(arr, elem) {
  arr[_] == elem
}
