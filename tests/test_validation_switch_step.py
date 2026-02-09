# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.definitions import SwitchStep


def test_switch_step_empty_condition() -> None:
    """Test that SwitchStep raises ValueError when a case condition is empty."""
    with pytest.raises(ValidationError) as exc:
        SwitchStep(
            id="switch1",
            cases={
                "": "step2",  # Empty condition
            },
        )
    assert "Switch condition cannot be empty" in str(exc.value)


def test_switch_step_whitespace_condition() -> None:
    """Test that SwitchStep raises ValueError when a case condition is whitespace."""
    with pytest.raises(ValidationError) as exc:
        SwitchStep(
            id="switch1",
            cases={
                "   ": "step2",  # Whitespace condition
            },
        )
    assert "Switch condition cannot be empty" in str(exc.value)
