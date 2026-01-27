# Prosperity-3.0
"""Manifest Loader.

This module is responsible for loading the agent manifest from YAML files or
dictionaries, normalizing the data, and converting it into Pydantic models.
"""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Callable, Dict, List, Union, get_type_hints

try:
    from typing import get_args, get_origin
except ImportError:  # pragma: no cover
    # For Python < 3.8, though project requires 3.12+
    from typing_extensions import get_args, get_origin  # type: ignore

import aiofiles
import yaml
from coreason_identity import UserContext
from pydantic import ValidationError, create_model

from coreason_manifest.errors import ManifestSyntaxError
from coreason_manifest.models import AgentDefinition, AgentInterface


class ManifestLoader:
    """Component A: ManifestLoader (The Parser).

    Responsibility:
      - Load YAML safely.
      - Convert raw data into a Pydantic AgentDefinition model.
      - Normalization: Ensure all version strings follow SemVer and all IDs are canonical UUIDs.
    """

    @staticmethod
    def load_raw_from_file(path: Union[str, Path]) -> dict[str, Any]:
        """Loads the raw dict from a YAML file.

        Args:
            path: The path to the agent.yaml file.

        Returns:
            dict: The raw dictionary content.

        Raises:
            ManifestSyntaxError: If YAML is invalid.
            FileNotFoundError: If the file does not exist.
        """
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                raise FileNotFoundError(f"Manifest file not found: {path}")

            with open(path_obj, "r", encoding="utf-8") as f:
                # safe_load is recommended for untrusted input
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                raise ManifestSyntaxError(f"Invalid YAML content in {path}: must be a dictionary.")

            ManifestLoader._normalize_data(data)

            return data

        except yaml.YAMLError as e:
            raise ManifestSyntaxError(f"Failed to parse YAML file {path}: {str(e)}") from e
        except OSError as e:
            if isinstance(e, FileNotFoundError):
                raise
            raise ManifestSyntaxError(f"Error reading file {path}: {str(e)}") from e

    @staticmethod
    async def load_raw_from_file_async(path: Union[str, Path]) -> dict[str, Any]:
        """Loads the raw dict from a YAML file asynchronously.

        Args:
            path: The path to the agent.yaml file.

        Returns:
            dict: The raw dictionary content.

        Raises:
            ManifestSyntaxError: If YAML is invalid.
            FileNotFoundError: If the file does not exist.
        """
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                raise FileNotFoundError(f"Manifest file not found: {path}")

            async with aiofiles.open(path_obj, "r", encoding="utf-8") as f:
                content = await f.read()
                data = yaml.safe_load(content)

            if not isinstance(data, dict):
                raise ManifestSyntaxError(f"Invalid YAML content in {path}: must be a dictionary.")

            ManifestLoader._normalize_data(data)

            return data

        except yaml.YAMLError as e:
            raise ManifestSyntaxError(f"Failed to parse YAML file {path}: {str(e)}") from e
        except OSError as e:
            if isinstance(e, FileNotFoundError):
                raise
            raise ManifestSyntaxError(f"Error reading file {path}: {str(e)}") from e

    @staticmethod
    def load_from_file(path: Union[str, Path]) -> AgentDefinition:
        """Loads the agent manifest from a YAML file.

        Args:
            path: The path to the agent.yaml file.

        Returns:
            AgentDefinition: The validated Pydantic model.

        Raises:
            ManifestSyntaxError: If YAML is invalid or Pydantic validation fails.
            FileNotFoundError: If the file does not exist.
        """
        data = ManifestLoader.load_raw_from_file(path)
        return ManifestLoader.load_from_dict(data)

    @staticmethod
    def load_from_dict(data: dict[str, Any]) -> AgentDefinition:
        """Converts a dictionary into an AgentDefinition model.

        Args:
            data: The raw dictionary.

        Returns:
            AgentDefinition: The validated Pydantic model.

        Raises:
            ManifestSyntaxError: If Pydantic validation fails.
        """
        try:
            # Ensure normalization happens before Pydantic validation
            # We work on a copy to avoid side effects if possible, but deep copy is expensive.
            # The input 'data' might be modified in place.
            ManifestLoader._normalize_data(data)

            return AgentDefinition.model_validate(data)
        except ValidationError as e:
            # Convert Pydantic ValidationError to ManifestSyntaxError
            # We assume "normalization" happens via Pydantic validators (e.g. UUID, SemVer checks)
            raise ManifestSyntaxError(f"Manifest validation failed: {str(e)}") from e

    @staticmethod
    def _normalize_data(data: dict[str, Any]) -> None:
        """Normalizes the data dictionary in place.

        Specifically strips 'v' or 'V' from version strings recursively until clean.
        """
        if "metadata" in data and isinstance(data["metadata"], dict):
            version = data["metadata"].get("version")
            if isinstance(version, str):
                # Recursively strip leading 'v' or 'V'
                while version and version[0] in ("v", "V"):
                    version = version[1:]
                data["metadata"]["version"] = version

    @staticmethod
    def inspect_function(func: Callable[..., Any]) -> AgentInterface:
        """Generates an AgentInterface from a Python function.

        Scans the function signature. If `user_context` (by name) or UserContext (by type)
        is found, it is marked as injected and excluded from the public schema.

        Args:
            func: The function to inspect.

        Returns:
            AgentInterface: The generated interface definition.

        Raises:
            ManifestSyntaxError: If forbidden arguments are found.
        """
        sig = inspect.signature(func)
        try:
            type_hints = get_type_hints(func)
        except Exception:
            # Fallback if get_type_hints fails (e.g. forward refs issues)
            type_hints = {}

        field_definitions: Dict[str, Any] = {}
        injected: List[str] = []

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue

            # Determine type annotation
            annotation = type_hints.get(param_name, param.annotation)
            if annotation is inspect.Parameter.empty:
                annotation = Any

            # Check for forbidden arguments
            if param_name in ("api_key", "token"):
                raise ManifestSyntaxError(f"Function argument '{param_name}' is forbidden. Use UserContext for auth.")

            # Check for injection
            is_injected = False
            if param_name == "user_context":
                is_injected = True
            else:
                # Check direct type
                if annotation is UserContext:
                    is_injected = True
                else:
                    # Check for Optional[UserContext], Annotated[UserContext, ...], Union[UserContext, ...]
                    origin = get_origin(annotation)
                    args = get_args(annotation)
                    if origin is not None:
                        # Recursively check if UserContext is in args (handles Optional/Union)
                        # or if this is Annotated (UserContext might be the first arg)
                        # We do a shallow check on args.
                        for arg in args:
                            if arg is UserContext:
                                is_injected = True
                                break

            if is_injected:
                if "user_context" not in injected:
                    injected.append("user_context")
                continue

            # Prepare for Pydantic model creation
            default = param.default
            if default is inspect.Parameter.empty:
                default = ...

            field_definitions[param_name] = (annotation, default)

        # Create dynamic model to generate JSON Schema for inputs
        # We assume strict mode or similar is handled by the consumer, here we just describe it.
        try:
            InputsModel = create_model("Inputs", **field_definitions)
            inputs_schema = InputsModel.model_json_schema()
        except Exception as e:
            raise ManifestSyntaxError(f"Failed to generate schema from function signature: {e}") from e

        # Handle return type for outputs
        return_annotation = type_hints.get("return", sig.return_annotation)
        outputs_schema = {}
        if (
            return_annotation is not inspect.Parameter.empty
            and return_annotation is not None
            and return_annotation is not type(None)
        ):
            try:
                # If return annotation is a Pydantic model, use its schema
                if hasattr(return_annotation, "model_json_schema"):
                    outputs_schema = return_annotation.model_json_schema()
                else:
                    # Wrap in a model
                    OutputsModel = create_model("Outputs", result=(return_annotation, ...))
                    outputs_schema = OutputsModel.model_json_schema()
            except Exception:
                pass

        return AgentInterface(
            inputs=inputs_schema,
            outputs=outputs_schema,
            injected_params=injected,
        )
