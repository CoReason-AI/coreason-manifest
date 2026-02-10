# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import importlib.util
import os
import stat
import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from coreason_manifest.builder import AgentBuilder
from coreason_manifest.spec.v2.definitions import ManifestV2
from coreason_manifest.spec.v2.recipe import RecipeDefinition


@contextmanager
def _temporary_sys_path(path: str) -> Generator[None, None, None]:
    """Context manager to temporarily add a path to sys.path."""
    sys.path.insert(0, path)
    try:
        yield
    finally:
        if sys.path and sys.path[0] == path:
            sys.path.pop(0)


def load_agent_from_ref(reference: str, allowed_root_dir: str | Path | None = None) -> ManifestV2 | RecipeDefinition:
    """
    Dynamically loads an Agent Definition (ManifestV2) or RecipeDefinition from a python file reference.

    Args:
        reference: A string in the format "path/to/file.py:variable_name".
        allowed_root_dir: The root directory that the file must reside within.
                          Defaults to current working directory if None.

    Returns:
        ManifestV2 | RecipeDefinition: The loaded agent manifest or recipe.

    Raises:
        ValueError: If the file does not exist, the variable is missing,
                    or the object is not a valid AgentBuilder, ManifestV2, or RecipeDefinition.
                    Also raises ValueError for security violations (path traversal, world-writable files).
    """
    if ":" not in reference:
        raise ValueError(f"Invalid reference format: '{reference}'. Expected format 'path/to/file.py:variable_name'")

    # Split on the *last* colon to support drive letters if absolutely necessary,
    # but simplest is strict split.
    file_path_str, var_name = reference.rsplit(":", 1)

    if not file_path_str or not var_name:
        raise ValueError("Reference must contain both file path and variable name.")

    # Resolve file path
    file_path = Path(file_path_str).resolve()

    # Security Check: Path Allowlisting
    allowed_root_dir = Path.cwd() if allowed_root_dir is None else Path(allowed_root_dir).resolve()

    if not file_path.is_relative_to(allowed_root_dir):
        raise ValueError(f"Security Violation: File {file_path} is outside allowed root {allowed_root_dir}")

    if not file_path.exists():
        raise ValueError(f"File not found: {file_path}")

    # Security Check: File Permissions (POSIX)
    if os.name == "posix":
        mode = file_path.stat().st_mode
        if mode & stat.S_IWOTH:
            raise ValueError(f"Security Violation: File {file_path} is world-writable.")

    # Add directory to sys.path to allow relative imports within the module
    module_dir = str(file_path.parent)

    module_name = file_path.stem

    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Could not load spec for module: {file_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        # SECURITY WARNING: This executes arbitrary code from the file.
        sys.stderr.write(f"⚠️  SECURITY WARNING: Executing code from {file_path}\n")
        sys.stderr.flush()

        with _temporary_sys_path(module_dir):
            spec.loader.exec_module(module)
    except Exception as e:
        raise ValueError(f"Error loading module {file_path}: {e}") from e

    # Extract variable
    try:
        agent_obj = getattr(module, var_name)
    except AttributeError as e:
        raise ValueError(f"Variable '{var_name}' not found in {file_path}") from e

    # Handle Builder
    if isinstance(agent_obj, AgentBuilder):
        try:
            agent_obj = agent_obj.build()
        except Exception as e:
            raise ValueError(f"Error building agent from builder: {e}") from e

    # Validate type
    if not isinstance(agent_obj, (ManifestV2, RecipeDefinition)):
        raise ValueError(
            f"Object '{var_name}' is not a ManifestV2, RecipeDefinition, or AgentBuilder. "
            f"Got: {type(agent_obj).__name__}"
        )

    return agent_obj
