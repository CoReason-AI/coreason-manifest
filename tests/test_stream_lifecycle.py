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

    def test_implicit_default_stream(self) -> None:
        """
        Edge Case: Verify that emitting a chunk without a preceding START event
        is valid and defaults to 'default'. This supports legacy behavior.
        """
        event = GraphEventNodeStream(
            run_id="run-X", trace_id="trace-X", node_id="node-X", timestamp=100.0, chunk="Implicit Chunk"
        )
        assert event.stream_id == "default"

        # Even if we explicitly name it "default", it works same way
        event_explicit = GraphEventNodeStream(
            run_id="run-X",
            trace_id="trace-X",
            node_id="node-X",
            timestamp=100.0,
            chunk="Explicit Default",
            stream_id="default",
        )
        assert event_explicit.stream_id == "default"

    def test_stream_id_constraints(self) -> None:
        """
        Edge Case: Verify behavior with unusual stream IDs (empty string, special chars).
        While the system doesn't enforce regex, it should serialize them correctly.
        """
        weird_ids = ["", "   ", "stream-123", "stream/with/slashes", "😊"]

        for sid in weird_ids:
            event = GraphEventStreamStart(
                run_id="r", trace_id="t", node_id="n", timestamp=0.0, stream_id=sid, content_type="text/plain"
            )
            adapter: TypeAdapter[Any] = TypeAdapter(GraphEvent)
            dumped = adapter.dump_json(event)
            loaded = cast("GraphEventStreamStart", adapter.validate_json(dumped))
            assert loaded.stream_id == sid

    def test_lifecycle_violations_structure(self) -> None:
        """
        Edge Case: Verify that structurally, END without START is permitted by the model.
        The Pydantic model is a data structure, not a state machine, so this should pass.
        The runtime engine is responsible for logical validation.
        """
        event = GraphEventStreamEnd(run_id="r", trace_id="t", node_id="n", timestamp=0.0, stream_id="ghost_stream")
        assert event.stream_id == "ghost_stream"

    def test_complex_multiplexing(self) -> None:
        """
        Complex Case: Simulate a realistic interleaved stream of Thought, Code, and User Message.
        """
        # Timeline:
        # T=1: Start Thinking (A)
        # T=2: Start Code (B)
        # T=3: Chunk A "Thinking..."
        # T=4: Chunk B "print('hello')"
        # T=5: Chunk A "Still thinking..."
        # T=6: End B
        # T=7: Chunk A "Done."
        # T=8: End A

        timeline: list[GraphEvent] = [
            GraphEventStreamStart(
                run_id="r",
                trace_id="t",
                node_id="n",
                timestamp=1,
                stream_id="thought",
                name="Thinking",
                content_type="text/markdown",
            ),
            GraphEventStreamStart(
                run_id="r",
                trace_id="t",
                node_id="n",
                timestamp=2,
                stream_id="code",
                name="Terminal",
                content_type="text/x-python",
            ),
            GraphEventNodeStream(run_id="r", trace_id="t", node_id="n", timestamp=3, stream_id="thought", chunk="..."),
            GraphEventNodeStream(
                run_id="r", trace_id="t", node_id="n", timestamp=4, stream_id="code", chunk="print('hello')"
            ),
            GraphEventNodeStream(
                run_id="r", trace_id="t", node_id="n", timestamp=5, stream_id="thought", chunk="Still..."
            ),
            GraphEventStreamEnd(run_id="r", trace_id="t", node_id="n", timestamp=6, stream_id="code"),
            GraphEventNodeStream(run_id="r", trace_id="t", node_id="n", timestamp=7, stream_id="thought", chunk="Done"),
            GraphEventStreamEnd(run_id="r", trace_id="t", node_id="n", timestamp=8, stream_id="thought"),
        ]

        adapter = TypeAdapter(list[GraphEvent])
        json_payload = adapter.dump_json(timeline)

        # Verify integrity
        reloaded = adapter.validate_json(json_payload)
        assert len(reloaded) == 8

        # Verify filtering logic (simulation of a client subscriber)
        thought_events = [e for e in reloaded if getattr(e, "stream_id", None) == "thought"]
        code_events = [e for e in reloaded if getattr(e, "stream_id", None) == "code"]

        # 1. Start Thought
        # 3. Chunk Thought
        # 5. Chunk Thought
        # 7. Chunk Thought
        # 8. End Thought
        # Total = 5
        assert len(thought_events) == 5

        # 2. Start Code
        # 4. Chunk Code
        # 6. End Code
        # Total = 3
        assert len(code_events) == 3

    def test_stream_error_propagation(self) -> None:
        """
        Complex Case: Ensure that standard GraphEventError can co-exist with streams,
        even though it doesn't carry a stream ID (it fails the node).
        """
        # Use Pydantic to validate the dict injection above works as a proper class
        adapter: TypeAdapter[Any] = TypeAdapter(list[GraphEvent])
        # We need to pass actual objects or dicts. Let's pass objects.

        from coreason_manifest import GraphEventError

        events_obj: list[GraphEvent] = [
            GraphEventStreamStart(
                run_id="r", trace_id="t", node_id="n", timestamp=1, stream_id="A", content_type="text/plain"
            ),
            GraphEventNodeStream(run_id="r", trace_id="t", node_id="n", timestamp=2, stream_id="A", chunk="ok"),
            GraphEventError(run_id="r", trace_id="t", node_id="n", timestamp=3, error_message="Fatal Error"),
        ]

        json_output = adapter.dump_json(events_obj)
        loaded = adapter.validate_json(json_output)

        assert len(loaded) == 3
        assert isinstance(loaded[2], GraphEventError)
