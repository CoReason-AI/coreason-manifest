# Prosperity-3.0
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from coreason_manifest.errors import ManifestError
from coreason_manifest.integrity import IntegrityChecker
from coreason_manifest.loader import ManifestLoader
from coreason_manifest.models import AgentDefinition
from coreason_manifest.policy import PolicyEnforcer
from coreason_manifest.utils.logger import logger
from coreason_manifest.validator import SchemaValidator


@dataclass
class ManifestConfig:
    """Configuration for the ManifestEngine."""

    policy_path: str | Path
    schema_path: str | Path | None = None
    opa_path: str | Path = "opa"
    verify_integrity: bool = True
    enforce_policy: bool = True


class ManifestEngine:
    """
    The orchestrator for validating CoReason Agent Manifests.

    Usage:
        config = ManifestConfig(policy_path="policies/compliance.rego")
        engine = ManifestEngine(config)
        agent_def = engine.load_and_validate("agent.yaml", "src")
    """

    def __init__(self, config: ManifestConfig) -> None:
        self.config = config
        self.validator = SchemaValidator(schema_path=config.schema_path)
        self.policy_enforcer: Optional[PolicyEnforcer] = None

        if self.config.enforce_policy:
            self.policy_enforcer = PolicyEnforcer(policy_path=config.policy_path, opa_path=config.opa_path)

    def load_and_validate(
        self,
        manifest_path: Union[str, Path],
        source_dir: Union[str, Path],
    ) -> AgentDefinition:
        """
        Loads, validates, and verifies the agent manifest and source code.

        Args:
            manifest_path: Path to the agent.yaml file.
            source_dir: Path to the agent's source code directory.

        Returns:
            AgentDefinition: The validated and verified agent definition.

        Raises:
            ManifestSyntaxError: If YAML is invalid or schema validation fails.
            PolicyViolationError: If compliance policy is violated.
            IntegrityCompromisedError: If source code integrity check fails.
            FileNotFoundError: If files or directories are missing.
        """
        manifest_path = Path(manifest_path)
        source_dir = Path(source_dir)

        logger.info(f"Validating Agent Manifest: {manifest_path}")

        # 1. Load and Schema Validation
        import yaml

        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

        with open(manifest_path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)

        if isinstance(raw_data, dict):
            # 2. Schema Validation
            logger.info("Running Schema Validation...")
            self.validator.validate(raw_data)

        # 3. Load into Pydantic Model (Normalization)
        # We use ManifestLoader.load_from_dict which returns AgentDefinition
        # Type ignore explanation: load_from_dict expects dict[str, Any], but raw_data can be any YAML type.
        # ManifestLoader handles validation internally.
        agent_def = ManifestLoader.load_from_dict(raw_data)  # type: ignore[unused-ignore]

        logger.info(f"Loaded Agent: {agent_def.metadata.name} v{agent_def.metadata.version}")

        # 4. Policy Enforcement
        if self.config.enforce_policy and self.policy_enforcer:
            logger.info("Running Policy Check...")
            try:
                self.policy_enforcer.evaluate(agent_def)
                logger.info("Policy Check: Pass")
            except ManifestError as e:
                logger.error(f"Policy Check: Fail - {str(e)}")
                raise

        # 5. Integrity Check
        if self.config.verify_integrity:
            logger.info("Running Integrity Check...")
            try:
                IntegrityChecker.verify(agent_def, source_dir)
                logger.info("Integrity Check: Pass")
            except ManifestError as e:
                logger.error(f"Integrity Check: Fail - {str(e)}")
                raise

        logger.info("Agent validation successful.")
        return agent_def
