# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import tomllib
from pathlib import Path

import coreason_manifest


def test_version() -> None:
    """Verify that the package version matches pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)

    project_version = pyproject_data["project"]["version"]
    package_version = coreason_manifest.__version__

    assert project_version == package_version, (
        f"Project version {project_version} does not match package version {package_version}"
    )
