with open("src/coreason_manifest/spec/ontology.py") as f:
    c = f.read()

target = """    @model_validator(mode="after")
    def verify_unique_tool_namespaces(self) -> Any:
        tool_names = {t.tool_name for t in self.native_tools}
        if len(tool_names) < len(self.native_tools):
            raise ValueError("Tool names within an ActionSpace must be strictly unique.")
        return self"""

replacement = """    @model_validator(mode="after")
    def verify_unique_tool_namespaces_and_sort(self) -> Self:
        tool_names = {t.tool_name for t in self.native_tools}
        if len(tool_names) < len(self.native_tools):
            raise ValueError("Tool names within an ActionSpace must be strictly unique.")

        object.__setattr__(self, "native_tools", sorted(self.native_tools, key=lambda x: x.tool_name))
        object.__setattr__(self, "mcp_servers", sorted(self.mcp_servers, key=lambda x: x.server_uri))
        object.__setattr__(self, "ephemeral_partitions", sorted(self.ephemeral_partitions, key=lambda x: x.partition_id))
        return self"""

c = c.replace(target, replacement)

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(c)
