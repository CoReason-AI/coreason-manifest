# Prosperity-3.0
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union

from coreason_manifest.integrity import IntegrityChecker
from coreason_manifest.loader import ManifestLoader
from coreason_manifest.models import AgentDefinition
from coreason_manifest.policy import PolicyEnforcer

# Import logger from utils to ensure configuration is applied
from coreason_manifest.utils.logger import logger
from coreason_manifest.validator import SchemaValidator


@dataclass
class ManifestConfig:
    """Configuration for the ManifestEngine."""

    policy_path: Union[str, Path]
    opa_path: str = "opa"
    tbom_path: Optional[Union[str, Path]] = None
    extra_data_paths: List[Union[str, Path]] = field(default_factory=list)


class ManifestEngine:
    """
    The main entry point for verifying and loading Agent Manifests.
    """

    def __init__(self, config: ManifestConfig) -> None:
        """
        Initialize the ManifestEngine.

        Args:
            config: Configuration including policy path and OPA path.
        """
        self.config = config
        self.schema_validator = SchemaValidator()

        # Collect data paths
        data_paths = list(config.extra_data_paths)
        if config.tbom_path:
            data_paths.append(config.tbom_path)

        self.policy_enforcer = PolicyEnforcer(
            policy_path=config.policy_path,
            opa_path=config.opa_path,
            data_paths=data_paths,
        )

    def load_and_validate(self, manifest_path: Union[str, Path], source_dir: Union[str, Path]) -> AgentDefinition:
        """
        Loads, validates, and verifies an Agent Manifest.

        Steps:
        1. Load raw YAML.
        2. Validate against JSON Schema.
        3. Convert to AgentDefinition Pydantic model (Normalization).
        4. Enforce Policy (Rego).
        5. Verify Integrity (Hash check).

        Args:
            manifest_path: Path to the agent.yaml file.
            source_dir: Path to the source code directory.

        Returns:
            AgentDefinition: The fully validated and verified agent definition.

        Raises:
            ManifestSyntaxError: If structure or schema is invalid.
            PolicyViolationError: If business rules are violated.
            IntegrityCompromisedError: If source code hash does not match.
            FileNotFoundError: If files are missing.
        """
        manifest_path = Path(manifest_path)
        source_dir = Path(source_dir)

        logger.info(f"Validating Agent Manifest: {manifest_path}")

        # 1. Load Raw YAML
        raw_data = ManifestLoader.load_raw_from_file(manifest_path)

        # 2. Schema Validation
        logger.debug("Running Schema Validation...")
        self.schema_validator.validate(raw_data)

        # 3. Model Conversion (Normalization)
        logger.debug("Converting to AgentDefinition...")
        agent_def = ManifestLoader.load_from_dict(raw_data)
        logger.info(f"Validating Agent {agent_def.metadata.id} v{agent_def.metadata.version}")

        # 4. Policy Enforcement
        logger.debug("Enforcing Policies...")
        # We assume policy is checked against the Normalized data (model dumped back to dict)
        # or raw data? Standard practice: Check against normalized data to prevent bypasses.
        # dump mode='json' converts UUIDs/Dates to strings which is what OPA expects usually.
        normalized_data = agent_def.model_dump(mode="json")
        start_time = time.perf_counter()
        try:
            self.policy_enforcer.evaluate(normalized_data)
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.info(f"Policy Check: Pass - {duration_ms:.2f}ms")
        except Exception:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.info(f"Policy Check: Fail - {duration_ms:.2f}ms")
            raise

        # 5. Integrity Check
        logger.debug("Verifying Integrity...")
        IntegrityChecker.verify(agent_def, source_dir, manifest_path=manifest_path)

        logger.info("Agent validation successful.")
        return agent_def
