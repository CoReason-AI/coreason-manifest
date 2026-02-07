import sys
from pathlib import Path
from unittest.mock import patch

from _pytest.capture import CaptureFixture

from coreason_manifest.cli import main


# Helper to create an agent file manually
def create_complex_agent_file(path: Path, code: str) -> Path:
    path.write_text(code, encoding="utf-8")
    return path


def test_hash_minimal_agent(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    """Test hashing an agent with only required fields."""
    code = """
from coreason_manifest.spec.v2.definitions import ManifestV2, ManifestMetadata, Workflow, AgentStep, InterfaceDefinition

agent = ManifestV2(
    kind="Agent",
    metadata=ManifestMetadata(name="MinimalAgent", version="1.0.0"),
    workflow=Workflow(start="step1", steps={"step1": AgentStep(id="step1", agent="self")})
)
"""
    agent_file = tmp_path / "minimal.py"
    create_complex_agent_file(agent_file, code)

    with patch.object(sys, "argv", ["coreason", "hash", str(agent_file)]):
        main()

    hash_val = capsys.readouterr().out.strip()
    assert hash_val.startswith("sha256:")
    assert len(hash_val) > 10


def test_hash_unicode_agent(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    """Test hashing an agent with Unicode characters to ensure consistent encoding."""
    # Using characters that might be problematic if not handled correctly (e.g., emojis, non-latin scripts)
    unicode_name = "Agent 🤖 - Dêfînîtîøn"
    code = f"""
from coreason_manifest.builder import AgentBuilder
builder = AgentBuilder(name="{unicode_name}")
agent = builder.build()
"""
    agent_file = tmp_path / "unicode.py"
    create_complex_agent_file(agent_file, code)

    with patch.object(sys, "argv", ["coreason", "hash", str(agent_file)]):
        main()

    hash_val = capsys.readouterr().out.strip()
    assert hash_val.startswith("sha256:")

    # Verify determinism with unicode
    with patch.object(sys, "argv", ["coreason", "hash", str(agent_file)]):
        main()
    hash_val_2 = capsys.readouterr().out.strip()
    assert hash_val == hash_val_2


def test_hash_large_agent(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    """Test hashing a large agent definition with many steps."""
    # Construct a large workflow
    steps_code = "{"
    for i in range(100):
        steps_code += f"'s{i}': AgentStep(id='s{i}', agent='worker', next='s{i + 1}' if {i} < 99 else None),"
    steps_code += "}"

    code = f"""
from coreason_manifest.spec.v2.definitions import ManifestV2, ManifestMetadata, Workflow, AgentStep, InterfaceDefinition

agent = ManifestV2(
    kind="Agent",
    metadata=ManifestMetadata(name="LargeAgent", version="1.0.0"),
    workflow=Workflow(start="s0", steps={steps_code})
)
"""
    agent_file = tmp_path / "large.py"
    create_complex_agent_file(agent_file, code)

    with patch.object(sys, "argv", ["coreason", "hash", str(agent_file)]):
        main()

    hash_val = capsys.readouterr().out.strip()
    assert hash_val.startswith("sha256:")


def test_hash_field_ordering_stability(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    """Test that defining fields in different order in Python source results in the same hash (Pydantic stability)."""
    # File 1: Standard order
    code1 = """
from coreason_manifest.builder import AgentBuilder
builder = AgentBuilder(name="OrderTest")
builder.with_model("gpt-4")
builder.with_system_prompt("Do work")
agent = builder.build()
"""
    file1 = tmp_path / "order1.py"
    create_complex_agent_file(file1, code1)

    # File 2: Different calls order (affecting internal list/dict construction order potentially,
    # but final object should be canonical)
    code2 = """
from coreason_manifest.builder import AgentBuilder
builder = AgentBuilder(name="OrderTest")
# Swap these calls
builder.with_system_prompt("Do work")
builder.with_model("gpt-4")
agent = builder.build()
"""
    file2 = tmp_path / "order2.py"
    create_complex_agent_file(file2, code2)

    with patch.object(sys, "argv", ["coreason", "hash", str(file1)]):
        main()
    hash1 = capsys.readouterr().out.strip()

    with patch.object(sys, "argv", ["coreason", "hash", str(file2)]):
        main()
    hash2 = capsys.readouterr().out.strip()

    assert hash1 == hash2
