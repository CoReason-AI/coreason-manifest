with open("src/coreason_manifest/telemetry/schemas.py", "r") as f:
    content = f.read()

target = """    @model_validator(mode="after")
    def sort_events(self) -> Any:"""

replacement = """    @model_validator(mode="after")
    def validate_temporal_bounds(self) -> Any:
        if self.end_time_unix_nano is not None and self.end_time_unix_nano < self.start_time_unix_nano:
            raise ValueError("end_time_unix_nano cannot be before start_time_unix_nano")
        return self

    @model_validator(mode="after")
    def sort_events(self) -> Any:"""

content = content.replace(target, replacement)

with open("src/coreason_manifest/telemetry/schemas.py", "w") as f:
    f.write(content)
