import pytest
from unittest.mock import patch
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from coreason_manifest.utils.loader import Loader

@pytest.mark.asyncio
async def test_loader_trace() -> None:
    # Setup OTEL
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    processor = SimpleSpanProcessor(exporter)
    provider.add_span_processor(processor)

    tracer = provider.get_tracer("coreason_manifest.utils.loader")

    manifest_str = """
    {
        "manifest_version": "v1",
        "flow": {
            "kind": "LinearFlow",
            "metadata": {
                "name": "trace-test",
                "version": "1.0",
                "description": "trace",
                "tags": []
            },
            "sequence": []
        }
    }
    """

    with patch("opentelemetry.trace.get_tracer", return_value=tracer):
        await Loader.load(manifest_str, auto_heal=True)

    spans = exporter.get_finished_spans()
    loader_span = next((s for s in spans if s.name == "Loader.load"), None)
    assert loader_span is not None
    assert loader_span.status.is_ok

@pytest.mark.asyncio
async def test_loader_trace_with_auto_heal_event() -> None:
    # Setup OTEL
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    processor = SimpleSpanProcessor(exporter)
    provider.add_span_processor(processor)

    tracer = provider.get_tracer("coreason_manifest.utils.loader")

    manifest_md = """
    ```json
    {
        "manifest_version": "v1",
        "flow": {
            "kind": "LinearFlow",
            "metadata": {
                "name": "heal-test",
                "version": "1.0",
                "description": "heal",
                "tags": []
            },
            "sequence": []
        }
    }
    ```
    """

    with patch("opentelemetry.trace.get_tracer", return_value=tracer):
        await Loader.load(manifest_md, auto_heal=True)

    spans = exporter.get_finished_spans()
    loader_span = next((s for s in spans if s.name == "Loader.load"), None)
    assert loader_span is not None

    # Check for event
    events = loader_span.events
    assert len(events) > 0
    event = next((e for e in events if e.name == "auto_heal_applied"), None)
    assert event is not None
    assert "mutations" in event.attributes
    assert "Stripped markdown code blocks" in event.attributes["mutations"]
