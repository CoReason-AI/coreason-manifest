package coreason.compliance

import rego.v1

# Do not import data.tbom to avoid namespace confusion, access via data.tbom directly if needed or via helper.

default allow := false

# Deny if 'pickle' is in libraries (matches "pickle", "pickle==1.0", "pickle>=2.0")
deny contains msg if {
    some i
    lib_str := input.dependencies.libraries[i]
    # Check if the library name starts with 'pickle' followed by end of string or version specifier
    regex.match("^pickle([<>=!@\\[].*)?$", lib_str)
    msg := "Security Risk: 'pickle' library is strictly forbidden."
}

# Deny if 'os' is in libraries
deny contains msg if {
    some i
    lib_str := input.dependencies.libraries[i]
    regex.match("^os([<>=!@\\[].*)?$", lib_str)
    msg := "Security Risk: 'os' library is strictly forbidden."
}

# Deny if description is too short (Business Rule example)
deny contains msg if {
    count(input.topology.steps) > 0
    count(input.topology.steps[0].description) < 5
    msg := "Step description is too short."
}

# Rule 1 (Dependency Pinning): All library dependencies must have explicit version pins
deny contains msg if {
    some i
    lib := input.dependencies.libraries[i]
    # Check if '==' exists in the string
    # We use regex matching.
    # Logic: If it does NOT match pinned format, deny.
    not regex.match(".*==.*", lib)
    msg := sprintf("Compliance Violation: Library '%v' must be pinned with '=='.", [lib])
}

# Rule 2 (Allowlist Enforcement): Libraries must be in TBOM
deny contains msg if {
    some i
    lib_str := input.dependencies.libraries[i]

    # Extract library name using regex (matches characters before any '==' or other version specifiers)
    # Pattern must support dots (for namespace packages) and stop before extras brackets or version specifiers.
    # Updated Pattern: ^([a-zA-Z0-9_\-\.]+)
    # Note: Regex parsing in Rego returns an array of matches.
    # regex.find_all_string_submatch_n(pattern, value, number)
    parts := regex.find_all_string_submatch_n("^[a-zA-Z0-9_\\-\\.]+", lib_str, 1)
    count(parts) > 0
    lib_name := parts[0][0]

    # Check if lib_name is in tbom
    not is_in_tbom(lib_name)

    msg := sprintf("Compliance Violation: Library '%v' is not in the Trusted Bill of Materials (TBOM).", [lib_name])
}

# Helper to safely check if lib is in TBOM
# Returns true if data.tbom exists AND contains the lib
is_in_tbom(lib) if {
    # Check if data.tbom exists and is array (implicitly handled by iteration)
    # If data.tbom is undefined, this rule body is undefined (false).
    data.tbom[_] == lib
}
