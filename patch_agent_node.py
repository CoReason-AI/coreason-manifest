with open("src/coreason_manifest/spec/ontology.py") as f:
    c = f.read()

target = """class AgentNode(BaseNode):
    \"\"\"
    A computational node powered by a large language model.
    \"\"\"

    type: Literal["agent"] = Field(default="agent", description="Discriminator for an Agent node.")
    model_profile: ModelProfile | None = Field(
        default=None, description="The structural performance and boundary definition of the underlying LLM."
    )
    system_prompt: str | None = Field(
        default=None,
        description="The strictly bounded system instructions to enforce behavioral alignment.",
    )
    action_space: OntologicalSurfaceProjection | None = Field(
        default=None,
        description="The strictly typed, dynamically projected surface of Tools and MCP Servers accessible to this agent.",  # noqa: E501
    )
    peft_adapters: list[PeftAdapterContract] = Field(
        default_factory=list,
        description="A declarative list of ephemeral PEFT/LoRA weights required to be hot-swapped during this agent's execution.",  # noqa: E501
    )
    agent_attestation: AgentAttestation | None = Field(
        default=None, description="A verifiable credential proving the agent's identity, clearance, and parameters."
    )"""

replacement = (
    target
    + """

    @model_validator(mode="after")
    def sort_adapters(self) -> Self:
        object.__setattr__(self, "peft_adapters", sorted(self.peft_adapters, key=lambda x: x.adapter_id))
        return self"""
)

c = c.replace(target, replacement)
with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(c)
