with open("tests/contracts/test_domain_extensions.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "TaxonomicRoutingPolicy's intent_to_heuristic_matrix" in line:
        new_lines.append("    # intent_to_heuristic_matrix has keys as ValidRoutingIntent\n")
    elif "and values as Literals. Values cannot be extensions, but let's test if the validator catches it anyway (even if pydantic catches it first)." in line:
        new_lines.append("    # Values are Literals. Values cannot be extensions.\n")
    elif "Therefore, the `if isinstance(dv, str) and dv.startswith(\"ext:\")` branch is technically unreachable for TaxonomicRoutingPolicy via normal validation." in line:
        new_lines.append("    # The dv check branch is technically unreachable for normal validation.\n")
    elif "We can hit it by explicitly calling the validator or by modifying the class `__dict__` and then calling the validator method." in line:
        new_lines.append("    # We can hit it by modifying the class __dict__.\n")
    elif "with pytest.raises(ValueError) as exc:" in line:
        new_lines.append("    with pytest.raises(ValueError, match=\"Unauthorized extension string in dict value\") as exc:\n")
    elif "assert \"Unauthorized extension string in dict value\" in str(exc.value)" in line:
        continue # we matched it
    else:
        new_lines.append(line)

with open("tests/contracts/test_domain_extensions.py", "w") as f:
    f.writelines(new_lines)
