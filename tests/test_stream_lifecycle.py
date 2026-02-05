# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import cast

from pydantic import TypeAdapter

from coreason_manifest import (
    GraphEvent,
    GraphEventNodeStream,
    GraphEventStreamEnd,
    GraphEventStreamStart,
    IStreamEmitter,
)


class TestStreamLifecycle:
    def test_default_stream_compatibility(self) -> None:
        """
        Verify that creating a GraphEventNodeStream without a stream_id
        defaults to "default".
        """
        event = GraphEventNodeStream(
            run_id="run-1", trace_id="trace-1", node_id="node-1", timestamp=12345.0, chunk="Hello World"
        )
        assert event.stream_id == "default"
        assert event.chunk == "Hello World"

    def test_multiplexing_serialization(self) -> None:
        """
        Verify that we can serialize a list of events with different stream IDs.
        """
        events: list[GraphEvent] = [
            GraphEventStreamStart(
                run_id="run-1",
                trace_id="trace-1",
                node_id="node-1",
                timestamp=1.0,
                stream_id="A",
                content_type="text/plain",
            ),
            GraphEventStreamStart(
                run_id="run-1",
                trace_id="trace-1",
                node_id="node-1",
                timestamp=2.0,
                stream_id="B",
                content_type="application/json",
            ),
            GraphEventNodeStream(
                run_id="run-1", trace_id="trace-1", node_id="node-1", timestamp=3.0, stream_id="A", chunk="Text"
            ),
            GraphEventNodeStream(
                run_id="run-1", trace_id="trace-1", node_id="node-1", timestamp=4.0, stream_id="B", chunk="Code"
            ),
            GraphEventStreamEnd(run_id="run-1", trace_id="trace-1", node_id="node-1", timestamp=5.0, stream_id="A"),
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

        # Use cast for strict typing in tests to avoid union-attr errors
        # In a real application, one would likely use isinstance()
        e0 = cast("GraphEventStreamStart", loaded_events[0])
        assert e0.stream_id == "A"

        e1 = cast("GraphEventStreamStart", loaded_events[1])
        assert e1.stream_id == "B"

        e2 = cast("GraphEventNodeStream", loaded_events[2])
        assert e2.stream_id == "A"

        e3 = cast("GraphEventNodeStream", loaded_events[3])
        assert e3.stream_id == "B"

    def test_protocol_verification(self) -> None:
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
