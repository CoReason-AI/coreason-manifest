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
from pydantic import TypeAdapter

from coreason_manifest import (
    GraphEventNodeStream,
    GraphEventStreamStart,
    GraphEventStreamEnd,
    IStreamEmitter,
    GraphEvent,
)


class TestStreamLifecycle:
    def test_default_stream_compatibility(self):
        """
        Verify that creating a GraphEventNodeStream without a stream_id
        defaults to "default".
        """
        event = GraphEventNodeStream(
            run_id="run-1",
            trace_id="trace-1",
            node_id="node-1",
            timestamp=12345.0,
            chunk="Hello World"
        )
        assert event.stream_id == "default"
        assert event.chunk == "Hello World"

    def test_multiplexing_serialization(self):
        """
        Verify that we can serialize a list of events with different stream IDs.
        """
        events = [
            GraphEventStreamStart(
                run_id="run-1", trace_id="trace-1", node_id="node-1", timestamp=1.0,
                stream_id="A", content_type="text/plain"
            ),
            GraphEventStreamStart(
                run_id="run-1", trace_id="trace-1", node_id="node-1", timestamp=2.0,
                stream_id="B", content_type="application/json"
            ),
            GraphEventNodeStream(
                run_id="run-1", trace_id="trace-1", node_id="node-1", timestamp=3.0,
                stream_id="A", chunk="Text"
            ),
            GraphEventNodeStream(
                run_id="run-1", trace_id="trace-1", node_id="node-1", timestamp=4.0,
                stream_id="B", chunk="Code"
            ),
             GraphEventStreamEnd(
                run_id="run-1", trace_id="trace-1", node_id="node-1", timestamp=5.0,
                stream_id="A"
            ),
        ]

        adapter = TypeAdapter(list[GraphEvent])
        json_output = adapter.dump_json(events).decode("utf-8")

        # Verify JSON contains the stream IDs
        assert '"stream_id":"A"' in json_output
        assert '"stream_id":"B"' in json_output
        assert '"chunk":"Text"' in json_output
        assert '"chunk":"Code"' in json_output

        # Round trip
        loaded_events = adapter.validate_json(json_output)
        assert len(loaded_events) == 5
        assert loaded_events[0].stream_id == "A"
        assert loaded_events[1].stream_id == "B"
        assert loaded_events[2].stream_id == "A"
        assert loaded_events[3].stream_id == "B"

    def test_protocol_verification(self):
        """
        Verify that the IStreamEmitter protocol is runtime checkable.
        """
        class MyEmitter:
            async def emit_chunk(self, content: str) -> None:
                pass

            async def close(self) -> None:
                pass

        class BadEmitter:
            def emit_chunk(self, content: str) -> None:
                pass

        assert isinstance(MyEmitter(), IStreamEmitter)
        # BadEmitter is missing close(), so it should fail check
        assert not isinstance(BadEmitter(), IStreamEmitter)
