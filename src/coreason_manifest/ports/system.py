from typing import Protocol

from coreason_manifest.core.workflow import GraphFlow, LinearFlow


class ManifestLoader(Protocol):
    def load_flow(self, file_path: str) -> GraphFlow | LinearFlow: ...
