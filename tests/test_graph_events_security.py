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

from coreason_manifest import (
    GraphEventNodeStart,
)


def test_red_team_type_confusion() -> None:
    """Type Confusion: Pass list instead of dict for payload."""
    with pytest.raises(ValidationError):
        GraphEventNodeStart(
            run_id="r1",
            trace_id="t1",
            node_id="n1",
            timestamp=100.0,
            payload=["not", "a", "dict"],
        )
