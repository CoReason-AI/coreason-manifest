import re

with open("src/coreason_manifest/spec/ontology.py") as f:
    c = f.read()

# 1. TheoryOfMindSnapshot
c = re.sub(
    r'(class TheoryOfMindSnapshot\(CoreasonBaseModel\):\n(?:[ \t]*""".*?"""\n)?[ \t]*.*?\n(?:[ \t]+.*?)*?)(?=\nclass |\n\nclass )',
    r'\1\n    @model_validator(mode="after")\n    def sort_arrays(self) -> Self:\n        object.__setattr__(self, "assumed_shared_beliefs", sorted(self.assumed_shared_beliefs))\n        object.__setattr__(self, "identified_knowledge_gaps", sorted(self.identified_knowledge_gaps))\n        return self\n',
    c,
    flags=re.MULTILINE | re.DOTALL,
)

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(c)
