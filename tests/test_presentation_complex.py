# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any, cast

from pydantic import TypeAdapter

from coreason_manifest import (
    CitationBlock,
    CitationItem,
    MarkdownBlock,
    PresentationEvent,
    PresentationEventType,
    ProgressUpdate,
)


def test_mixed_polymorphic_list() -> None:
    """Test a list containing various types of PresentationEvents."""
    events = [
        PresentationEvent(
            type=PresentationEventType.MARKDOWN_BLOCK,
            data=MarkdownBlock(content="# Header"),
        ),
        PresentationEvent(
            type=PresentationEventType.CITATION_BLOCK,
            data=CitationBlock(
                items=[
                    CitationItem(source_id="1", uri="http://a.com", title="A"),
                ]
            ),
        ),
        PresentationEvent(
            type=PresentationEventType.PROGRESS_INDICATOR,
            data=ProgressUpdate(label="Loading", status="running", progress_percent=0.5),
        ),
        PresentationEvent(
            type=PresentationEventType.USER_ERROR,
            data={"error": "Something went wrong"},
        ),
    ]

    # Serialize list
    adapter = TypeAdapter(list[PresentationEvent])
    json_output = adapter.dump_json(events)

    # Deserialize back
    restored_events = adapter.validate_json(json_output)

    assert len(restored_events) == 4

    # Verify individual types
    assert restored_events[0].type == PresentationEventType.MARKDOWN_BLOCK
    assert isinstance(restored_events[0].data, MarkdownBlock)

    assert restored_events[1].type == PresentationEventType.CITATION_BLOCK
    assert isinstance(restored_events[1].data, CitationBlock)

    assert restored_events[2].type == PresentationEventType.PROGRESS_INDICATOR
    assert isinstance(restored_events[2].data, ProgressUpdate)

    assert restored_events[3].type == PresentationEventType.USER_ERROR
    assert isinstance(restored_events[3].data, dict)
    assert restored_events[3].data["error"] == "Something went wrong"


def test_nested_complex_structure() -> None:
    """Test deeply nested structure in USER_ERROR."""
    complex_data = {
        "level1": {
            "level2": {
                "level3": [
                    {"id": 1, "val": "a"},
                    {"id": 2, "val": "b"},
                ]
            }
        },
        "meta": [1, 2, 3],
    }

    event = PresentationEvent(type=PresentationEventType.USER_ERROR, data=complex_data)

    dumped = event.model_dump(mode="json")
    restored = PresentationEvent.model_validate(dumped)

    # Use explicit casting to satisfy MyPy
    data = cast("dict[str, Any]", restored.data)
    assert data["level1"]["level2"]["level3"][1]["val"] == "b"
