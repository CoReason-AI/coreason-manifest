import tomllib
from pathlib import Path

import coreason_manifest


def test_version() -> None:
    """Verify that the package version matches pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)

    poetry_version = pyproject_data["tool"]["poetry"]["version"]
    project_version = pyproject_data["project"]["version"]
    package_version = coreason_manifest.__version__

    assert poetry_version == package_version, (
        f"Poetry version {poetry_version} does not match package version {package_version}"
    )
    assert project_version == package_version, (
        f"Project version {project_version} does not match package version {package_version}"
    )
