package coreason.compliance

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
