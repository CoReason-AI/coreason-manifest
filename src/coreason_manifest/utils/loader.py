# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import asyncio
import importlib.util
import sys
import threading
from pathlib import Path

from coreason_manifest.builder import AgentBuilder
from coreason_manifest.spec.common.error import (
    AgentDefinitionError,
    AgentNotFoundError,
    InvalidReferenceError,
)
from coreason_manifest.spec.v2.definitions import ManifestV2
from coreason_manifest.spec.v2.recipe import RecipeDefinition

# Module-level lock to ensure thread safety during sys.path modification and import
_loader_lock = threading.Lock()


def load_agent_from_ref(reference: str) -> ManifestV2 | RecipeDefinition:
    """
    Dynamically loads an Agent Definition (ManifestV2) or RecipeDefinition from a python file reference.

    Args:
        reference: A string in the format "path/to/file.py:variable_name".

    Returns:
        ManifestV2 | RecipeDefinition: The loaded agent manifest or recipe.

    Raises:
        InvalidReferenceError: If the reference format is incorrect.
        AgentNotFoundError: If the file does not exist.
        AgentDefinitionError: If the object cannot be loaded or is not of the expected type.
    """
    if ":" not in reference:
        raise InvalidReferenceError(
            f"Invalid reference format: '{reference}'. Expected format 'path/to/file.py:variable_name'"
        )

    # Split on the *last* colon to support drive letters if absolutely necessary,
    # but simplest is strict split.
    file_path_str, var_name = reference.rsplit(":", 1)

    if not file_path_str or not var_name:
        raise InvalidReferenceError("Reference must contain both file path and variable name.")

    # Resolve file path
    file_path = Path(file_path_str).resolve()
    if not file_path.exists():
        raise AgentNotFoundError(f"File not found: {file_path}")

    # Use a lock to prevent race conditions when modifying sys.path and importing modules
    with _loader_lock:
        # Add directory to sys.path to allow relative imports within the module
        module_dir = str(file_path.parent)
        if module_dir not in sys.path:
            sys.path.insert(0, module_dir)

        module_name = file_path.stem

    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise AgentDefinitionError(f"Could not load spec for module: {file_path}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module

            # SECURITY WARNING: This executes arbitrary code from the file.
            sys.stderr.write(f"⚠️  SECURITY WARNING: Executing code from {file_path}\n")
            sys.stderr.flush()

        spec.loader.exec_module(module)
    except (ImportError, SyntaxError) as e:
        raise AgentDefinitionError(f"Failed to import module '{file_path}': {e}") from e
    except Exception as e:
        raise AgentDefinitionError(f"Error loading module {file_path}: {e}") from e

    # Extract variable
    try:
        agent_obj = getattr(module, var_name)
    except AttributeError as e:
        raise AgentDefinitionError(f"Variable '{var_name}' not found in {file_path}") from e

    # Handle Builder
    if isinstance(agent_obj, AgentBuilder):
        try:
            agent_obj = agent_obj.build()
        except Exception as e:
            raise AgentDefinitionError(f"Error building agent from builder: {e}") from e

    # Validate type
    if not isinstance(agent_obj, (ManifestV2, RecipeDefinition)):
        raise AgentDefinitionError(
            f"Object '{var_name}' is not a ManifestV2, RecipeDefinition, or AgentBuilder. "
            f"Got: {type(agent_obj).__name__}"
        )

    return agent_obj


async def load_agent_from_ref_async(reference: str) -> ManifestV2 | RecipeDefinition:
    """
    Asynchronously loads an Agent Definition (ManifestV2) or RecipeDefinition from a python file reference.
    Offloads the blocking file I/O and import operations to a thread pool.

    Args:
        reference: A string in the format "path/to/file.py:variable_name".

    Returns:
        ManifestV2 | RecipeDefinition: The loaded agent manifest or recipe.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, load_agent_from_ref, reference)
