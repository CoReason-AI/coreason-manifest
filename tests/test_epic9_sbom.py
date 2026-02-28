import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core.state.tools import Dependency


def test_dependency_valid_integrity_hash() -> None:
    # Valid sha256
    sha256 = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    dep = Dependency(name="requests", manager="pip", integrity_hash=sha256)
    assert dep.integrity_hash == sha256  # noqa: S101

    # Valid sha384
    sha384 = "sha384:38b060a751ac96384cd9327eb1b1e36a21fdb71114be07434c0cc7bf63f6e1da274edebfe76f65fbd51ad2f14898b95b"
    dep = Dependency(name="requests", manager="pip", integrity_hash=sha384)
    assert dep.integrity_hash.startswith("sha384:") if dep.integrity_hash else False  # noqa: S101

    # Valid sha512
    sha512 = (
        "sha512:cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d3"
        "6ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e"
    )
    dep = Dependency(name="requests", manager="pip", integrity_hash=sha512)
    assert dep.integrity_hash.startswith("sha512:") if dep.integrity_hash else False  # noqa: S101


def test_dependency_invalid_integrity_hash() -> None:
    invalid_hashes = [
        "md5:d41d8cd98f00b204e9800998ecf8427e",  # Invalid algorithm
        "sha256-e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",  # Invalid separator
        "sha256:E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",  # Uppercase not allowed
        "sha256:g3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",  # Invalid hex char
        "sha256:",  # Missing hex
    ]

    for h in invalid_hashes:
        with pytest.raises(ValidationError) as exc:
            Dependency(name="requests", manager="pip", integrity_hash=h)
        assert "String should match pattern" in str(exc.value)  # noqa: S101


def test_dependency_with_sbom_ref() -> None:
    dep = Dependency(name="pandas", manager="pip", sbom_ref="pkg:pypi/pandas@2.0.0?type=cyclonedx")
    assert dep.sbom_ref == "pkg:pypi/pandas@2.0.0?type=cyclonedx"  # noqa: S101
