# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Any

import pytest
from pydantic import ValidationError

from coreason_manifest.compute.symbolic import NeuroSymbolicHandoff


def test_neuro_symbolic_handoff_valid() -> None:
    handoff = NeuroSymbolicHandoff(
        handoff_id="test_id",
        solver_protocol="z3",
        formal_grammar_payload="x > 5",
        expected_proof_schema={"type": "boolean"},
        timeout_ms=1000,
    )
    assert handoff.handoff_id == "test_id"


def test_neuro_symbolic_handoff_invalid_solver() -> None:
    # We use a trick to bypass type checking for invalid literal testing
    invalid_protocol: Any = "invalid_solver"
    with pytest.raises(ValidationError):
        NeuroSymbolicHandoff(
            handoff_id="test_id",
            solver_protocol=invalid_protocol,
            formal_grammar_payload="x > 5",
            expected_proof_schema={"type": "boolean"},
            timeout_ms=1000,
        )


def test_neuro_symbolic_handoff_invalid_timeout() -> None:
    with pytest.raises(ValidationError):
        NeuroSymbolicHandoff(
            handoff_id="test_id",
            solver_protocol="z3",
            formal_grammar_payload="x > 5",
            expected_proof_schema={"type": "boolean"},
            timeout_ms=0,
        )


def test_neuro_symbolic_handoff_invalid_id() -> None:
    with pytest.raises(ValidationError):
        NeuroSymbolicHandoff(
            handoff_id="",
            solver_protocol="z3",
            formal_grammar_payload="x > 5",
            expected_proof_schema={"type": "boolean"},
            timeout_ms=1000,
        )
