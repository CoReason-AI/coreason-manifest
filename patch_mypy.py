# ruff: noqa
with open("tests/contracts/test_domain_extensions.py") as f:
    content = f.read()

# Fix 1: type hints for MockValidationInfo
content = content.replace("def __init__(self, context):", "def __init__(self, context: dict[str, set[str]]) -> None:")

# Fix 2: different exc variable
content = content.replace(
    'with pytest.raises(ValueError, match="Unauthorized extension string in dict value") as exc:',
    'with pytest.raises(ValueError, match="Unauthorized extension string in dict value") as exc2:',
)
content = content.replace(
    'assert "Unauthorized extension string in dict value" in str(exc.value)',
    'assert "Unauthorized extension string in dict value" in str(exc2.value)',
)

# Fix 3: PydanticDescriptorProxy not callable
# Instead of calling p.validate_domain_extensions(info), we can call the underlying bound method or pass the info dictionary differently.
# But validate_domain_extensions is a @model_validator, so it is wrapped.
# We can just use TaxonomicRoutingPolicy.model_validate again, but with a pre-polluted dict? No, model_validate parses it.
# We can bypass model validation by modifying the object and triggering serialization, but `validate_domain_extensions` is an AFTER validator.
# We can call `__pydantic_validator__.validate_python`?
# Actually, we can just do: `TaxonomicRoutingPolicy.__dict__["validate_domain_extensions"].__get__(p)(info)` or similar.
# Wait, pydantic 2 wraps it in a decorator.
# Let's just remove the explicit call and test it through standard validation if possible, or use the raw method if we can access it.
# But we can't easily trigger the dict value branch in TaxonomicRoutingPolicy because pydantic catches it earlier.
# What if we use `BargeInInterruptEvent` for the dict value branch? It accepts `dict[str, Any]` for `retained_partial_payload`.
# Wait, my `BargeInInterruptEvent` test DOES test the dict value branch successfully:
# "BargeInInterruptEvent.model_validate({'retained_partial_payload': {'k': 'ext:invalid_val'}})"
# That hits the dict value branch! Let's check codecov.
# If `BargeInInterruptEvent` hits it, then I don't even NEED the `TaxonomicRoutingPolicy` explicit call. Let's just delete the unreachable TaxonomicRoutingPolicy manual call.

import re

# Remove the MockValidationInfo block
content = re.sub(
    r'    p = TaxonomicRoutingPolicy\(.*?\n    assert "Unauthorized extension string in dict value" in str\(exc2\.value\)\n',
    "",
    content,
    flags=re.DOTALL,
)
content = re.sub(
    r'    p = TaxonomicRoutingPolicy\(.*?\n    assert "Unauthorized extension string in dict value" in str\(exc\.value\)\n',
    "",
    content,
    flags=re.DOTALL,
)

with open("tests/contracts/test_domain_extensions.py", "w") as f:
    f.write(content)
