# Prosperity-3.0
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from coreason_manifest.models import (
    AgentMetadata,
    AgentTopology,
    Step,
)


def test_unique_step_ids_validation() -> None:
    """Test that duplicate step IDs raise a ValidationError."""
    steps = (
        Step(id="step1", description="desc"),
        Step(id="step1", description="desc2"),  # Duplicate
    )

    with pytest.raises(ValidationError) as e:
        AgentTopology(steps=steps, model_config={"model": "gpt-4", "temperature": 0.5})
    assert "Duplicate step IDs found: step1" in str(e.value)


def test_unique_step_ids_valid() -> None:
    """Test that unique step IDs are accepted."""
    steps = (
        Step(id="step1", description="desc"),
        Step(id="step2", description="desc2"),
    )
    topo = AgentTopology(steps=steps, model_config={"model": "gpt-4", "temperature": 0.5})
    assert len(topo.steps) == 2


def test_empty_step_id_rejected() -> None:
    """Test that empty step ID is rejected."""
    with pytest.raises(ValidationError) as e:
        Step(id="", description="desc")
    assert "String should have at least 1 character" in str(e.value)


def test_empty_name_author_rejected() -> None:
    """Test that empty name and author are rejected."""
    # Test Name
    with pytest.raises(ValidationError) as e:
        AgentMetadata(
            id=uuid4(),
            version="1.0.0",
            name="",
            author="Valid",
            created_at=datetime.now(timezone.utc),
        )
    assert "String should have at least 1 character" in str(e.value)

    # Test Author
    with pytest.raises(ValidationError) as e:
        AgentMetadata(
            id=uuid4(),
            version="1.0.0",
            name="Valid",
            author="",
            created_at=datetime.now(timezone.utc),
        )
    assert "String should have at least 1 character" in str(e.value)


def test_created_at_validation() -> None:
    """Test created_at datetime parsing."""
    # Valid ISO string
    meta = AgentMetadata(
        id=uuid4(),
        version="1.0.0",
        name="Valid",
        author="Valid",
        created_at="2023-01-01T12:00:00Z",
    )
    assert isinstance(meta.created_at, datetime)
    assert meta.created_at.year == 2023

    # Invalid string
    with pytest.raises(ValidationError) as e:
        AgentMetadata(
            id=uuid4(),
            version="1.0.0",
            name="Valid",
            author="Valid",
            created_at="not-a-date",
        )
    assert "Input should be a valid datetime" in str(e.value)
