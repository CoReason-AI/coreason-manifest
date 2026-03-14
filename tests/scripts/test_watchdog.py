# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at [https://prosperitylicense.com/versions/3.0.0](https://prosperitylicense.com/versions/3.0.0)
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: [https://github.com/CoReason-AI/coreason-manifest](https://github.com/CoReason-AI/coreason-manifest)

import os
import sys

# Ensure the root directory is on the path so 'scripts' can be imported in CI
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import json
from unittest.mock import MagicMock, patch

import pytest

from scripts.swarm_watchdog import extract_descriptions, main, scan_schema


def test_extract_descriptions() -> None:
    schema = {
        "description": "Top-level description",
        "properties": {
            "field1": {"description": "Field 1 description"},
            "field2": {"type": "array", "items": [{"description": "Item description"}]},
        },
    }
    descriptions = extract_descriptions(schema)
    assert len(descriptions) == 3
    assert "Top-level description" in descriptions
    assert "Field 1 description" in descriptions
    assert "Item description" in descriptions


def test_watchdog_detects_stolen_schema() -> None:
    stolen_schema = {
        "title": "My Copied Schema",
        "description": "A totally original schema.",
        "properties": {
            "prop1": {
                "description": "Some normal description [SITD-Alpha: Non-Monotonic Epistemic Quarantine Isometry]"
            },
            "prop2": {"description": "Another description. Topologically Bounded Latent Spaces"},
            "prop3": {"description": "Buried description [SITD-Gamma: Neurosymbolic Substrate Alignment]"},
        },
    }

    score = scan_schema(stolen_schema)
    # 3 matches out of 5 registry items = 0.6
    assert score >= 0.6


def test_watchdog_clears_clean_schema() -> None:
    clean_schema = {
        "title": "Clean Schema",
        "description": "The user ID",
        "properties": {"prop1": {"description": "Updates the data"}},
    }

    score = scan_schema(clean_schema)
    assert score == 0.0


@patch("sys.argv", ["swarm_watchdog.py"])
def test_main_missing_args(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
    assert "Usage" in capsys.readouterr().out


@patch("sys.argv", ["swarm_watchdog.py", "http://example.com/schema.json"])
@patch("urllib.request.urlopen")
def test_main_http_success(mock_urlopen: MagicMock, capsys: pytest.CaptureFixture[str]) -> None:
    mock_response = MagicMock()
    mock_response.read.return_dict = {"description": "Clean"}
    mock_response.read.return_value = b'{"description": "Clean Schema"}'
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response

    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 0
    assert "Schema clear. No epistemic contamination found." in capsys.readouterr().out


@patch("sys.argv", ["swarm_watchdog.py", "local_file.json"])
@patch("builtins.open", new_callable=MagicMock)
def test_main_file_stolen(mock_open: MagicMock, capsys: pytest.CaptureFixture[str]) -> None:
    mock_file = MagicMock()
    stolen_schema = {
        "description": "[SITD-Alpha: Non-Monotonic Epistemic Quarantine Isometry]",
        "prop": {"description": "Topologically Bounded Latent Spaces"},
        "prop2": {"description": "[SITD-Gamma: Neurosymbolic Substrate Alignment]"},
    }
    mock_file.read.return_value = json.dumps(stolen_schema)
    mock_file.__enter__.return_value = mock_file
    mock_open.return_value = mock_file

    with patch("json.load", return_value=stolen_schema), pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 1
    assert "CRITICAL: PPL 3.0 VIOLATION DETECTED" in capsys.readouterr().out


@patch("sys.argv", ["swarm_watchdog.py", "nonexistent.json"])
@patch("builtins.open", side_effect=FileNotFoundError("No file"))
def test_main_file_error(mock_open: MagicMock, capsys: pytest.CaptureFixture[str]) -> None:
    _ = mock_open

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
    assert "Error loading schema" in capsys.readouterr().out
