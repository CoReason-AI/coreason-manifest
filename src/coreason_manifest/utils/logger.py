from loguru import logger

# THE SUPREME LAW (AGENTS.md): Disable the logger by default so the library is 100% passive.
# Only the consuming Builder/Engine application will attach sinks and enable it.
logger.disable("coreason_manifest")

__all__ = ["logger"]
