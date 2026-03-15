with open("src/coreason_manifest/spec/ontology.py", "r") as f:
    content = f.read()

target = "class TaxonomicRoutingPolicy(CoreasonBaseState):"

intent_class = """class IntentClassificationReceipt(CoreasonBaseState):
    \"\"\"The mathematical output of the routing LLM supporting superposition.\"\"\"
    primary_intent: ValidRoutingIntent = Field(description="The argmax intent with highest probability.")
    concurrent_intents: dict[ValidRoutingIntent, float] = Field(
        default_factory=dict,
        description="Dictionary of adjacent intents and confidence scores (0.0 to 1.0). Used for superposition branching."
    )

    @model_validator(mode="after")
    def sort_concurrent_intents(self) -> Self:
        if self.concurrent_intents:
            object.__setattr__(self, "concurrent_intents", dict(sorted(self.concurrent_intents.items())))
        return self

"""

if target in content:
    content = content.replace(target, intent_class + target)
    print("Injected IntentClassificationReceipt")

# Append to model_rebuild
rebuild_target = "EpistemicAxiomState.model_rebuild()"
if rebuild_target in content:
    content = content.replace(rebuild_target, rebuild_target + "\nIntentClassificationReceipt.model_rebuild()")
    print("Injected IntentClassificationReceipt.model_rebuild()")

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(content)
