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

from coreason_manifest.core.common.highlighting import HighlightConfig, HighlightRule, HighlightStyle, MatchType


def test_highlight_rule_literal() -> None:
    """Test HighlightRule instantiates correctly with literal patterns."""
    rule = HighlightRule(pattern="hello", match_type=MatchType.LITERAL)
    assert rule.pattern == "hello"
    assert rule.match_type == MatchType.LITERAL
    assert rule.style == HighlightStyle.MARKER_YELLOW
    assert rule.case_sensitive is False


def test_highlight_rule_valid_static_regex() -> None:
    """Test HighlightRule instantiates correctly with a valid static regex."""
    rule = HighlightRule(pattern=r"\b\d{3}\b", match_type=MatchType.REGEX)
    assert rule.pattern == r"\b\d{3}\b"
    assert rule.match_type == MatchType.REGEX


def test_highlight_rule_bypass_re_compile() -> None:
    """Test HighlightRule safely bypasses re.compile if the regex pattern is a local pointer."""
    rule = HighlightRule(pattern="$local.regex_string", match_type=MatchType.REGEX)
    assert rule.pattern == "$local.regex_string"
    assert rule.match_type == MatchType.REGEX


def test_highlight_rule_invalid_static_regex() -> None:
    """Test HighlightRule successfully catches a malformed regex and raises a ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        HighlightRule(pattern="[unterminated", match_type=MatchType.REGEX)

    assert "Invalid Regex pattern: '[unterminated'." in str(exc_info.value)


def test_highlight_config() -> None:
    """Test HighlightConfig can be initialized with rules."""
    rule1 = HighlightRule(pattern="foo", match_type=MatchType.LITERAL)
    rule2 = HighlightRule(pattern=r"\d+", match_type=MatchType.REGEX)
    config = HighlightConfig(rules=[rule1, rule2])

    assert len(config.rules) == 2
    assert config.rules[0] == rule1
    assert config.rules[1] == rule2


def test_highlight_config_default() -> None:
    """Test HighlightConfig can be initialized without arguments and defaults to empty list."""
    config = HighlightConfig()

    assert config.rules == []
