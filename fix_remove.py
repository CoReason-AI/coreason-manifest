with open("src/coreason_manifest/spec/ontology.py") as f:
    content = f.read()

# Replace `def trigger_rollback(self) -> Self:` state validator:

old_str = """
    @model_validator(mode="after")
    def trigger_rollback(self) -> Self:
        \"\"\"
        AGENT INSTRUCTION: State validator that actively purges memory associated with a SpeculativeExecutionBoundary
        when it is deemed falsified (e.g., commit_probability drops to 0.0 or a specific rollback flag is detected).
        For deterministic execution, we purge any boundary whose commit_probability is exactly 0.0.
        \"\"\"
        boundaries_to_rollback = [b for b in self.speculative_boundaries if b.commit_probability <= 0.0]
        if not boundaries_to_rollback:
            return self

        nodes_to_purge = set()
        for b in boundaries_to_rollback:
            for uuid_val in b.rollback_pointers:
                nodes_to_purge.add(str(uuid_val))

        # Purge nodes
        for node_id in nodes_to_purge:
            if node_id in self.nodes:
                del self.nodes[node_id]

        # Purge edges related to the purged nodes
        edges_to_keep = []
        for source, target in self.edges:
            if source not in nodes_to_purge and target not in nodes_to_purge:
                edges_to_keep.append((source, target))
        object.__setattr__(self, "edges", edges_to_keep)

        # Remove the boundaries themselves
        boundaries_to_keep = [b for b in self.speculative_boundaries if b.commit_probability > 0.0]
        object.__setattr__(self, "speculative_boundaries", boundaries_to_keep)

        return self
"""

content = content.replace(old_str, "")

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(content)
