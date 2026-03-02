from coreason_manifest.adapters.system.dynamic_loader import LocalFileLoader
from coreason_manifest.core.workflow import GraphFlow, LinearFlow
from coreason_manifest.ports.system import ManifestLoader


class WorkspaceManager:
    """
    Application Service Orchestrator for managing workspace manifests.
    """

    def __init__(self, loader: ManifestLoader | None = None) -> None:
        if loader is None:
            # Default to LocalFileLoader
            self.loader: ManifestLoader = LocalFileLoader()
        else:
            self.loader = loader

    def load_flow(self, file_path: str) -> GraphFlow | LinearFlow:
        """
        Load a flow manifest using the injected loader.
        """
        return self.loader.load_flow(file_path)
