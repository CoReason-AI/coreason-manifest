# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator


from typing import Any, Dict, List, Literal, Optional

from pydantic import ConfigDict, Field

from .base import CoReasonBaseModel


class BECTestCase(CoReasonBaseModel):
    """
    Represents a single benchmark test case.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(..., min_length=1, description="Unique identifier for the test case")
    prompt: str = Field(..., min_length=1, description="The input prompt for the agent")
    context_files: List[str] = Field(default_factory=list, description="List of file paths providing context")
    expected_output_structure: Optional[Dict[str, Any]] = Field(
        default=None, description="JSON Schema defining the expected output structure"
    )


class BECManifest(CoReasonBaseModel):
    """
    Defines the Benchmark Evaluation Corpus (Test Data).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"] = "1.0"
    corpus_id: str = Field(..., min_length=1, description="Unique identifier for the corpus")
    cases: List[BECTestCase] = Field(..., min_length=1, description="List of test cases")
