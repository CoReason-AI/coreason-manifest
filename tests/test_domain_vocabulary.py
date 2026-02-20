import pytest
from pydantic import BaseModel, ValidationError

from coreason_manifest.spec.core.types import GitSHA, NodeID, SemanticVersion


class VocabularyTestModel(BaseModel):
    version: SemanticVersion | None = None
    sha: GitSHA | None = None
    node: NodeID | None = None


def test_semantic_version_valid() -> None:
    m = VocabularyTestModel(version="1.0.0")
    assert m.version == "1.0.0"

    m = VocabularyTestModel(version="0.1.2")
    assert m.version == "0.1.2"


def test_semantic_version_invalid() -> None:
    with pytest.raises(ValidationError) as excinfo:
        VocabularyTestModel(version="v1.0")
    assert "String should match pattern" in str(excinfo.value)

    with pytest.raises(ValidationError):
        VocabularyTestModel(version="1.0")  # Missing patch

    with pytest.raises(ValidationError):
        VocabularyTestModel(version="1.a.2")


def test_git_sha_valid() -> None:
    valid_sha = "a" * 40
    m = VocabularyTestModel(sha=valid_sha)
    assert m.sha == valid_sha


def test_git_sha_invalid() -> None:
    with pytest.raises(ValidationError):
        VocabularyTestModel(sha="bad")  # Too short

    with pytest.raises(ValidationError):
        VocabularyTestModel(sha="z" * 40)  # Invalid hex

    with pytest.raises(ValidationError):
        VocabularyTestModel(sha="a" * 41)  # Too long


def test_node_id_valid() -> None:
    m = VocabularyTestModel(node="valid_node_1")
    assert m.node == "valid_node_1"


def test_node_id_invalid() -> None:
    with pytest.raises(ValidationError):
        VocabularyTestModel(node="invalid node")  # Space not allowed

    with pytest.raises(ValidationError):
        VocabularyTestModel(node="")  # Empty
