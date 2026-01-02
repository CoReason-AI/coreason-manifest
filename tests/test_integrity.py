# Prosperity-3.0

import pytest

from coreason_manifest.errors import IntegrityCompromisedError
from coreason_manifest.integrity import IntegrityChecker
from coreason_manifest.models import (
    AgentDefinition,
    AgentDependencies,
    AgentInterface,
    AgentMetadata,
    AgentTopology,
    ModelConfig,
    Step,
)


# Helper to create a dummy agent definition
def create_agent_def(integrity_hash=None):
    return AgentDefinition(
        metadata=AgentMetadata(
            id="123e4567-e89b-12d3-a456-426614174000",
            version="1.0.0",
            name="Test Agent",
            author="Tester",
            created_at="2023-10-27T10:00:00Z",
        ),
        interface=AgentInterface(inputs={}, outputs={}),
        topology=AgentTopology(steps=[Step(id="step1")], model_config=ModelConfig(model="gpt-4", temperature=0.7)),
        dependencies=AgentDependencies(),
        integrity_hash=integrity_hash,
    )


@pytest.fixture
def source_dir(tmp_path):
    d = tmp_path / "src"
    d.mkdir()
    (d / "main.py").write_text("print('hello')")
    (d / "utils.py").write_text("def foo(): pass")
    subdir = d / "subdir"
    subdir.mkdir()
    (subdir / "helper.py").write_text("x = 1")
    return d


def test_calculate_directory_hash(source_dir):
    # Calculate hash manually to verify
    # Files sorted: main.py, subdir/helper.py, utils.py (based on standard sort)
    # Wait, simple string sort: 'main.py', 'subdir/helper.py', 'utils.py'

    # Let's verify deterministic behavior first
    hash1 = IntegrityChecker.calculate_directory_hash(source_dir)
    hash2 = IntegrityChecker.calculate_directory_hash(source_dir)
    assert hash1 == hash2


def test_calculate_directory_hash_changes_on_content(source_dir):
    hash1 = IntegrityChecker.calculate_directory_hash(source_dir)

    # Modify a file
    (source_dir / "main.py").write_text("print('world')")

    hash2 = IntegrityChecker.calculate_directory_hash(source_dir)
    assert hash1 != hash2


def test_calculate_directory_hash_changes_on_filename(source_dir):
    hash1 = IntegrityChecker.calculate_directory_hash(source_dir)

    # Rename a file
    (source_dir / "main.py").rename(source_dir / "main2.py")

    hash2 = IntegrityChecker.calculate_directory_hash(source_dir)
    assert hash1 != hash2


def test_calculate_directory_hash_not_found():
    with pytest.raises(FileNotFoundError):
        IntegrityChecker.calculate_directory_hash("non_existent_dir")


def test_verify_success(source_dir):
    calculated_hash = IntegrityChecker.calculate_directory_hash(source_dir)
    agent = create_agent_def(integrity_hash=calculated_hash)

    # Should not raise
    IntegrityChecker.verify(agent, source_dir)


def test_verify_mismatch(source_dir):
    agent = create_agent_def(integrity_hash="wrong_hash")

    with pytest.raises(IntegrityCompromisedError, match="Integrity check failed"):
        IntegrityChecker.verify(agent, source_dir)


def test_verify_missing_hash(source_dir):
    agent = create_agent_def(integrity_hash=None)

    with pytest.raises(IntegrityCompromisedError, match="Manifest is missing 'integrity_hash'"):
        IntegrityChecker.verify(agent, source_dir)
