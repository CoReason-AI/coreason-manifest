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
# Iterates over ALL steps to ensure compliance.
deny contains msg if {
    some step in input.topology.steps
    count(step.description) < 5
    msg := "Step description is too short."
}

# Rule 1 (Dependency Pinning): All library dependencies must have explicit version pins.
# Strictly enforces "name==version" (with optional extras).
# Rejects "name>=version", "name==version,>=other", etc.
deny contains msg if {
    some i
    lib := input.dependencies.libraries[i]

    # Regex Explanation:
    # ^                         Start
    # [a-zA-Z0-9_\-\.]+         Package name (alphanum, _, -, .)
    # (\[[a-zA-Z0-9_\-\.,]+\])? Optional extras in brackets (e.g. [security,fast])
    # ==                        Must be strictly '=='
    # [a-zA-Z0-9_\-\.\+]+       Version string (alphanum, _, -, ., + for metadata)
    # $                         End (No trailing constraints like ,>=2.0)

    not regex.match("^[a-zA-Z0-9_\\-\\.]+(\\[[a-zA-Z0-9_\\-\\.,]+\\])?==[a-zA-Z0-9_\\-\\.\\+]+$", lib)
    msg := sprintf("Compliance Violation: Library '%v' must be strictly pinned with '==' (e.g., 'pandas==2.0.1').", [lib])
}

# Rule 2 (Allowlist Enforcement): Libraries must be in TBOM
deny contains msg if {
    some i
    lib_str := input.dependencies.libraries[i]

    # Extract library name using regex
    # Pattern must support dots (for namespace packages) and stop before extras brackets or version specifiers.
    parts := regex.find_all_string_submatch_n("^[a-zA-Z0-9_\\-\\.]+", lib_str, 1)
    count(parts) > 0
    lib_name := parts[0][0]

    # Check if lib_name is in tbom (case-insensitive)
    not is_in_tbom(lib_name)

    msg := sprintf("Compliance Violation: Library '%v' is not in the Trusted Bill of Materials (TBOM).", [lib_name])
}

# Helper to safely check if lib is in TBOM
# Returns true if data.tbom exists AND contains the lib (case-insensitive)
is_in_tbom(lib) if {
    # Lowercase the input library name
    lower_lib := lower(lib)

    # Check against TBOM
    # If data.tbom is undefined, this rule body is undefined (false).
    # Iterate through TBOM and compare lowercased versions
    some tbom_lib in data.tbom
    lower(tbom_lib) == lower_lib
}
