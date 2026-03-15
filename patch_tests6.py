with open("tests/contracts/test_domain_extensions.py", "r") as f:
    content = f.read()

# Replace the previous bad dict validation tests with correct ones for TaxonomicRoutingPolicy and BargeInInterruptEvent

good_test_cases = """
def test_dict_validation_in_barge_in_event() -> None:
    # Invalid key
    with pytest.raises(ValidationError) as exc:
        BargeInInterruptEvent.model_validate(
            {
                "event_id": "e3",
                "timestamp": 100.0,
                "target_event_id": "t3",
                "epistemic_disposition": "discard",
                "disfluency_type": "repair",
                "retained_partial_payload": {"ext:invalid_key": "v"}
            },
            context={"allowed_ext_intents": set()}
        )
    assert "Unauthorized extension string in dict key" in str(exc.value)

    # Invalid value
    with pytest.raises(ValidationError) as exc:
        BargeInInterruptEvent.model_validate(
            {
                "event_id": "e4",
                "timestamp": 100.0,
                "target_event_id": "t4",
                "epistemic_disposition": "discard",
                "disfluency_type": "repair",
                "retained_partial_payload": {"k": "ext:invalid_val"}
            },
            context={"allowed_ext_intents": set()}
        )
    assert "Unauthorized extension string in dict value" in str(exc.value)

def test_dict_validation_in_taxonomic_routing_policy() -> None:
    # TaxonomicRoutingPolicy's intent_to_heuristic_matrix has keys as ValidRoutingIntent (which can be extension strings)
    # and values as Literals. Values cannot be extensions, but let's test if the validator catches it anyway (even if pydantic catches it first).
    # Wait, if pydantic catches it first, the custom validator won't run for the value.
    # But it WILL run for the key because the key is ValidRoutingIntent.

    with pytest.raises(ValidationError) as exc:
        TaxonomicRoutingPolicy.model_validate(
            {
                "policy_id": "p6",
                "intent_to_heuristic_matrix": {"ext:invalid_key": "chronological"},
                "fallback_heuristic": "chronological"
            },
            context={"allowed_ext_intents": set()}
        )
    assert "Unauthorized extension string in dict key" in str(exc.value)

    # To test an invalid value in dict, we'd need to bypass pydantic's typing or use a field that allows it.
    # intent_to_heuristic_matrix values are Literal, so passing "ext:invalid" fails pydantic typing.
    # Is there another dict in TaxonomicRoutingPolicy? No.
    # Therefore, the `if isinstance(dv, str) and dv.startswith("ext:")` branch is technically unreachable for TaxonomicRoutingPolicy via normal validation.
    # We can hit it by explicitly calling the validator or by modifying the class `__dict__` and then calling the validator method.

    p = TaxonomicRoutingPolicy(
        policy_id="p7",
        intent_to_heuristic_matrix={"informational_inform": "chronological"},
        fallback_heuristic="chronological"
    )
    # forcefully insert a bad value into __dict__
    p.__dict__["intent_to_heuristic_matrix"] = {"informational_inform": "ext:bad_value"}

    from pydantic_core.core_schema import ValidationInfo
    # Create a mock ValidationInfo
    class MockValidationInfo:
        def __init__(self, context):
            self.context = context
            self.config = None
            self.mode = 'python'
            self.data = {}
            self.field_name = None

    info = MockValidationInfo(context={"allowed_ext_intents": set()})

    with pytest.raises(ValueError) as exc:
        p.validate_domain_extensions(info)
    assert "Unauthorized extension string in dict value" in str(exc.value)

"""

# Remove old test_all_extension_cases, test_taxonomic_routing_policy_dict_validation, test_taxonomic_routing_policy_dict_validation_key
import re
content = re.sub(r'def test_taxonomic_routing_policy_dict_validation\(\) -> None:.*?context={"allowed_ext_intents": {"ext:custom_intent"}}\n        \)\n', '', content, flags=re.DOTALL)
content = re.sub(r'def test_taxonomic_routing_policy_dict_validation_key\(\) -> None:.*?context={"allowed_ext_intents": {"ext:custom_intent"}}\n        \)\n', '', content, flags=re.DOTALL)
content = re.sub(r'def test_all_extension_cases\(\) -> None:.*', '', content, flags=re.DOTALL)

content += "\n" + good_test_cases

with open("tests/contracts/test_domain_extensions.py", "w") as f:
    f.write(content)

print("Updated tests to correctly hit dictionary extension validation.")
