with open("tests/contracts/test_domain_extensions.py", "r") as f:
    content = f.read()

test_extension = """
def test_taxonomic_routing_policy_dict_validation() -> None:
    # Test valid extension dictionary value with context
    with pytest.raises(ValidationError):
        TaxonomicRoutingPolicy.model_validate(
            {
                "policy_id": "p4",
                "intent_to_heuristic_matrix": {"ext:custom_intent": "chronological"},
                "fallback_heuristic": "chronological",
                "some_other_dict": {"k": "ext:invalid_value"}
            },
            context={"allowed_ext_intents": {"ext:custom_intent"}}
        )
"""

if "test_taxonomic_routing_policy_dict_validation" not in content:
    content += "\n" + test_extension
    with open("tests/contracts/test_domain_extensions.py", "w") as f:
        f.write(content)
