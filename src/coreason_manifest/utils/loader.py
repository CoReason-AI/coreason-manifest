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
import sys
from pathlib import Path

from coreason_manifest.builder import AgentBuilder
from coreason_manifest.spec.v2.definitions import ManifestV2


def load_agent_from_ref(reference: str) -> ManifestV2:
    """
    Dynamically loads an Agent Definition (ManifestV2) from a python file reference.

    Args:
        reference: A string in the format "path/to/file.py:variable_name".
                   If ":variable_name" is omitted, defaults to "agent".

    Returns:
        ManifestV2: The loaded agent manifest.

    Raises:
        ValueError: If the file does not exist, the variable is missing,
                    or the object is not a valid AgentBuilder or ManifestV2.
    """
    if ":" in reference:
        file_path_str, var_name = reference.rsplit(":", 1)
    else:
        file_path_str, var_name = reference, "agent"

    # Resolve file path
    file_path = Path(file_path_str).resolve()
    if not file_path.exists():
        raise ValueError(f"File not found: {file_path}")

    # Add directory to sys.path to allow relative imports within the module
    module_dir = str(file_path.parent)
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)

    module_name = file_path.stem

    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Could not load spec for module: {file_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
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
    if not isinstance(agent_obj, ManifestV2):
        raise ValueError(f"Object '{var_name}' is not a ManifestV2 or AgentBuilder. Got: {type(agent_obj).__name__}")

    return agent_obj
