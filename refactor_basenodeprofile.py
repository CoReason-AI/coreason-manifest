import re

with open('src/coreason_manifest/spec/ontology.py', 'r') as f:
    content = f.read()

fields = """    description: str = Field(
        max_length=2000,
        description="The semantic boundary defining the objective function or computational perimeter of the execution node.",
    )
    architectural_intent: str | None = Field(
        max_length=2000, default=None, description="The AI's declarative rationale for selecting this node."
    )
    justification: str | None = Field(
        max_length=2000,
        default=None,
        description="Cryptographic/audit justification for this node's existence in the graph.",
    )
    intervention_policies: list[InterventionPolicy] = Field(
        default_factory=list,
        description="The declarative array of proactive oversight hooks bound to this node's lifecycle.",
    )
    domain_extensions: dict[Annotated[str, StringConstraints(max_length=255)], JsonPrimitiveState] | None = Field(
        default=None,
        description="Passive, untyped extension point for vertical domain context. Strictly bounded to prevent JSON-bomb memory leaks. AGENT INSTRUCTION: Payload volume is strictly limited to an absolute $O(N)$ limit of 10,000 nodes and a maximum recursion depth of 10 to prevent VRAM exhaustion.",
    )
    semantic_zoom: SemanticZoomProfile | None = Field(
        default=None,
        description="The mathematical Information Bottleneck thresholds dictating the semantic degradation of this specific node.",
    )
    markov_blanket: MarkovBlanketRenderingPolicy | None = Field(
        default=None, description="The epistemic isolation boundary guarding this agent's internal generative states."
    )
    optical_physics: PhysicallyBasedRenderingProfile | None = Field(
        default=None, description="The strict microfacet BRDF physics governing the visual representation of this node."
    )\n"""

field_validator = """    @field_validator("domain_extensions", mode="before")
    @classmethod
    def enforce_payload_topology(cls, v: Any) -> Any:
        \"\"\"AGENT INSTRUCTION: Mathematically bound recursive dictionary payloads to prevent OOM/CPU exhaustion during EpistemicLedgerState hashing.\"\"\"
        return _validate_payload_bounds(v)\n"""

# BaseNodeProfile sorting function:
#     @model_validator(mode="after")
#     def _enforce_canonical_sort_intervention_policies(self) -> Self:
#         object.__setattr__(
#             self, "intervention_policies", sorted(self.intervention_policies, key=operator.attrgetter("trigger"))
#         )
#         return self

children = [
    'HumanNodeProfile', 'MemoizedNodeProfile', 'SystemNodeProfile', 'CompositeNodeProfile', 'AgentNodeProfile'
]

for child in children:
    # 1. Replace inheritance
    pattern = r'(class ' + child + r'\(BaseNodeProfile\):(?:\s*(?:r?"""[\s\S]*?"""|r?\'\'\'[\s\S]*?\'\'\'))?)'

    def repl(m):
        base = m.group(1).replace('BaseNodeProfile', 'CoreasonBaseState')
        return base + '\n\n' + fields

    content = re.sub(pattern, repl, content)

    # 2. Inject field_validator
    # We can inject field_validator right after the last Field definition of the class or simply at the bottom of the class block.
    # To be safe, we'll find the last method or field of the class, or just inject it right after fields
    # Wait, it's easier to inject both fields and field_validator into the same spot at the top. Let's adjust repl to include field_validator.

# Redo:
with open('src/coreason_manifest/spec/ontology.py', 'r') as f:
    content = f.read()

for child in children:
    pattern = r'(class ' + child + r'\(BaseNodeProfile\):(?:\s*(?:r?"""[\s\S]*?"""|r?\'\'\'[\s\S]*?\'\'\'))?)'

    def repl(m):
        base = m.group(1).replace('BaseNodeProfile', 'CoreasonBaseState')
        return base + '\n\n' + fields + '\n' + field_validator

    content = re.sub(pattern, repl, content)

    # 3. Handle sorting logic.
    # Let's see if the child already has a `_enforce_canonical_sort_...` or similar.
    # AgentNodeProfile has `_enforce_canonical_sort_peft_adapters`.
    # Let's just find any @model_validator(mode="after") def _enforce_canonical_sort...

    # Actually, we can just look for the class block.
    class_idx = content.find(f"class {child}(CoreasonBaseState):")
    next_class_idx = content.find("class ", class_idx + 1)
    if next_class_idx == -1: next_class_idx = len(content)

    class_block = content[class_idx:next_class_idx]

    # If the class has a sorting validator, we merge. If not, we add a new one.
    sort_pattern = r'(@model_validator\(mode="after"\)\s+def _enforce_canonical_sort[a-zA-Z0-9_]*\(self\) -> Self:\s+(?:[^\n]+\n)*?\s+return self)'
    sort_match = re.search(sort_pattern, class_block)

    sort_logic = '        object.__setattr__(self, "intervention_policies", sorted(self.intervention_policies, key=operator.attrgetter("trigger")))\n'

    if sort_match:
        # Merge
        old_sort = sort_match.group(1)
        # Rename the function to `_enforce_canonical_sort` to be clean.
        # Find where the `return self` is
        new_sort = re.sub(r'def _enforce_canonical_sort[a-zA-Z0-9_]*\(self\) -> Self:', 'def _enforce_canonical_sort(self) -> Self:', old_sort)
        new_sort = new_sort.replace('return self', sort_logic.strip() + '\n        return self')
        class_block = class_block.replace(old_sort, new_sort)
    else:
        # Add new one at the end of the class block
        new_sort = f'\n    @model_validator(mode="after")\n    def _enforce_canonical_sort_intervention_policies(self) -> Self:\n{sort_logic}        return self\n\n'
        class_block = class_block.rstrip() + new_sort

    content = content[:class_idx] + class_block + content[next_class_idx:]


# Remove BaseNodeProfile definition completely
base_pattern = r'class BaseNodeProfile\(CoreasonBaseState\):\s*(?:r?"""[\s\S]*?"""|r?\'\'\'[\s\S]*?\'\'\')?[\s\S]*?return _validate_payload_bounds\(v\)\n'
content = re.sub(base_pattern, '', content)

with open('src/coreason_manifest/spec/ontology.py', 'w') as f:
    f.write(content)
