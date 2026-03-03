from loguru import logger

# Architectural Constraint (per AGENTS.md): Disable the logger by default to ensure
# the library remains strictly passive.
# Only the consuming Builder/Engine application will attach sinks and enable it.
logger.disable("coreason_manifest")

__all__ = ["logger"]
