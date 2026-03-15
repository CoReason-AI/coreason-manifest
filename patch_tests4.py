with open("tests/contracts/test_domain_extensions.py", "r") as f:
    content = f.read()

test_extension = """
def test_taxonomic_routing_policy_dict_validation_key() -> None:
    with pytest.raises(ValidationError):
        TaxonomicRoutingPolicy.model_validate(
            {
                "policy_id": "p5",
                "intent_to_heuristic_matrix": {"ext:custom_intent": "chronological"},
                "fallback_heuristic": "chronological",
                "some_other_dict": {"ext:invalid_key": "v"}
            },
            context={"allowed_ext_intents": {"ext:custom_intent"}}
        )
"""

if "test_taxonomic_routing_policy_dict_validation_key" not in content:
    content += "\n" + test_extension
    with open("tests/contracts/test_domain_extensions.py", "w") as f:
        f.write(content)
