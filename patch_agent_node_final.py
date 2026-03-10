import re

with open("src/coreason_manifest/spec/ontology.py") as f:
    c = f.read()

# Make absolutely sure we find AgentNode
match = re.search(r"(class AgentNode\(BaseNode\):.*?)(?=\n\nclass |\n\nAnyNode )", c, re.DOTALL)
if match:
    block = match.group(1)
    if "def sort_adapters" not in block:
        new_block = (
            block
            + """

    @model_validator(mode="after")
    def sort_adapters(self) -> Self:
        object.__setattr__(self, "peft_adapters", sorted(self.peft_adapters, key=lambda x: x.adapter_id))
        return self"""
        )
        c = c.replace(block, new_block)
        print("Patched AgentNode!")
    else:
        print("Already has sort_adapters")
else:
    print("AgentNode not found")

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(c)
