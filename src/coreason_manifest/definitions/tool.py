# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator


import re
from typing import Any, Dict

from pydantic import ConfigDict, Field, field_validator

from .base import CoReasonBaseModel


class ToolCall(CoReasonBaseModel):
    """
    Defines the strict inputs for coreason-mcp.
    Ensures type strictness and prevents SQL injection.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    tool_name: str = Field(..., min_length=1, description="Name of the tool to call")
    arguments: Dict[str, Any] = Field(..., description="Dictionary of arguments for the tool")

    @field_validator("arguments")
    @classmethod
    def check_sql_injection(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scans all string values in arguments for SQL injection patterns.
        Uses regex to avoid false positives (e.g., 'update' in normal text).
        """
        # Regex patterns for dangerous SQL commands.
        # \b ensures word boundaries. \s+ allows multiple spaces/tabs/newlines.
        # (?i) makes it case-insensitive.
        patterns = [
            r"(?i)\bDROP\s+TABLE\b",
            r"(?i)\bDELETE\s+FROM\b",
            r"(?i)\bINSERT\s+INTO\b",
            r"(?i)\bUPDATE\s+\w+\s+SET\b",  # stricter UPDATE check: UPDATE table SET
            r"(?i)\bALTER\s+TABLE\b",
            r"(?i)\bUNION\s+SELECT\b",
            r"(?i)\s+OR\s+1=1\b",  # Classic bypass
            r"--",  # Comment: still aggressive, but -- is rare in standard inputs unless markdown
        ]

        compiled_patterns = [re.compile(p) for p in patterns]

        def scan_value(val: Any, key_path: str) -> None:
            if isinstance(val, str):
                # Normalize whitespace for pattern matching (optional, but helps with newlines)
                # But we want to preserve original value, so just scan raw or normalized?
                # Regex handles \s+, so raw is fine, but maybe replace newlines for single-line checks?
                # Let's trust the regex \s+.

                for pattern in compiled_patterns:
                    if pattern.search(val):
                        # Get the matched string for the error message
                        match = pattern.search(val)
                        found = match.group(0) if match else "SQL Pattern"
                        raise ValueError(f"Potential SQL injection detected in field '{key_path}': '{found}'")
            elif isinstance(val, dict):
                for k, sub_val in val.items():
                    scan_value(sub_val, f"{key_path}.{k}")
            elif isinstance(val, list):
                for i, item in enumerate(val):
                    scan_value(item, f"{key_path}[{i}]")

        for key, value in v.items():
            scan_value(value, key)

        return v
