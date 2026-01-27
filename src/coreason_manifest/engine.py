# Prosperity-3.0
"""Engine for the Coreason Manifest system.

This module provides the main entry point for verifying and loading Agent Manifests.
It coordinates schema validation, policy enforcement, and integrity checking.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional, Union, cast

import anyio
import anyio.to_thread

from coreason_manifest.integrity import IntegrityChecker
from coreason_manifest.loader import ManifestLoader
from coreason_manifest.models import AgentDefinition
from coreason_manifest.policy import PolicyEnforcer
from coreason_manifest.utils.logger import logger
from coreason_manifest.validator import SchemaValidator


@dataclass
class ManifestConfig:
    """Configuration for the ManifestEngine.

    Attributes:
        policy_path: Path to the Rego policy file.
        opa_path: Path to the OPA executable. Defaults to "opa".
        tbom_path: Optional path to the Trusted Bill of Materials.
        extra_data_paths: Additional data paths to load into OPA.
    """

    policy_path: Union[str, Path]
    opa_path: str = "opa"
    tbom_path: Optional[Union[str, Path]] = None
    extra_data_paths: List[Union[str, Path]] = field(default_factory=list)


class ManifestEngineAsync:
    """The async core for verifying and loading Agent Manifests.

    This class coordinates the validation process, including:
    1.  Loading raw YAML.
    2.  Validating against JSON Schema.
    3.  Converting to AgentDefinition Pydantic model (Normalization).
    4.  Enforcing Policy (Rego).
    5.  Verifying Integrity (Hash check).
    """

    def __init__(self, config: ManifestConfig) -> None:
        """Initialize the ManifestEngineAsync.

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

    async def __aenter__(self) -> ManifestEngineAsync:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        # Clean up resources if necessary.
        pass

    async def validate_manifest_dict(self, raw_data: dict[str, Any]) -> AgentDefinition:
        """Validates an Agent Manifest dictionary in memory.

        Performs:
        1. Normalization (stripping version prefixes)
        2. Schema Validation
        3. Model Conversion
        4. Policy Enforcement

        Does NOT perform Integrity Check (hashing).

        Args:
            raw_data: The raw dictionary of the manifest.

        Returns:
            AgentDefinition: The fully validated agent definition.

        Raises:
            ManifestSyntaxError: If structure or schema is invalid.
            PolicyViolationError: If business rules are violated.
        """
        # 1. Normalization (ensure version string is clean before schema/model validation)
        # We access the static method on ManifestLoader.
        ManifestLoader._normalize_data(raw_data)

        # 2. Schema Validation
        logger.debug("Running Schema Validation...")
        self.schema_validator.validate(raw_data)

        # 3. Model Conversion (Normalization) (CPU bound)
        logger.debug("Converting to AgentDefinition...")
        agent_def = await anyio.to_thread.run_sync(ManifestLoader.load_from_dict, raw_data)
        logger.info(f"Validating Agent {agent_def.metadata.id} v{agent_def.metadata.version}")

        # 4. Policy Enforcement (Subprocess / Blocking)
        logger.debug("Enforcing Policies...")
        # We assume policy is checked against the Normalized data (model dumped back to dict)
        normalized_data = agent_def.model_dump(mode="json")
        start_time = time.perf_counter()
        try:
            # PolicyEnforcer.evaluate is synchronous and runs subprocess.run, so we wrap it.
            await anyio.to_thread.run_sync(self.policy_enforcer.evaluate, normalized_data)
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.info(f"Policy Check: Pass - {duration_ms:.2f}ms")
        except Exception:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.info(f"Policy Check: Fail - {duration_ms:.2f}ms")
            raise

        return cast(AgentDefinition, agent_def)

    async def load_and_validate(self, manifest_path: Union[str, Path], source_dir: Union[str, Path]) -> AgentDefinition:
        """Loads, validates, and verifies an Agent Manifest asynchronously.

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

        # 1. Load Raw YAML (I/O)
        raw_data = await ManifestLoader.load_raw_from_file_async(manifest_path)

        # 2. Validate Manifest Dict (Schema, Model, Policy)
        agent_def = await self.validate_manifest_dict(raw_data)

        # 5. Integrity Check (Heavy I/O and CPU)
        logger.debug("Verifying Integrity...")
        # IntegrityChecker.verify is synchronous and does heavy IO, so we wrap it.
        await anyio.to_thread.run_sync(IntegrityChecker.verify, agent_def, source_dir, manifest_path)

        logger.info("Agent validation successful.")
        return agent_def


class ManifestEngine:
    """The Sync Facade for ManifestEngineAsync.

    Allows synchronous usage of the async core via anyio.run.
    """

    def __init__(self, config: ManifestConfig) -> None:
        """Initialize the ManifestEngine facade.

        Args:
            config: Configuration including policy path and OPA path.
        """
        self._async = ManifestEngineAsync(config)

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the async engine instance.

        This ensures backward compatibility for accessing attributes like
        'config', 'schema_validator', and 'policy_enforcer'.
        """
        return getattr(self._async, name)

    def __enter__(self) -> ManifestEngine:
        """Context manager entry."""
        anyio.run(self._async.__aenter__)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        anyio.run(self._async.__aexit__, exc_type, exc_val, exc_tb)

    def load_and_validate(self, manifest_path: Union[str, Path], source_dir: Union[str, Path]) -> AgentDefinition:
        """Loads, validates, and verifies an Agent Manifest synchronously.

        Args:
            manifest_path: Path to the agent.yaml file.
            source_dir: Path to the source code directory.

        Returns:
            AgentDefinition: The fully validated and verified agent definition.
        """
        return cast(AgentDefinition, anyio.run(self._async.load_and_validate, manifest_path, source_dir))

    def validate_manifest_dict(self, raw_data: dict[str, Any]) -> AgentDefinition:
        """Validates an Agent Manifest dictionary synchronously.

        Args:
            raw_data: The raw dictionary of the manifest.

        Returns:
            AgentDefinition: The fully validated agent definition.
        """
        return cast(AgentDefinition, anyio.run(self._async.validate_manifest_dict, raw_data))
