import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from pydantic import ConfigDict, SecretStr

from coreason_manifest.spec.core_base import ObservableModel

class SensitiveModel(ObservableModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    name: str
    api_key: SecretStr

def test_observable_init_trace() -> None:
    # Setup OTEL
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    processor = SimpleSpanProcessor(exporter)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    # Instantiate model
    model = SensitiveModel(name="test", api_key=SecretStr("sk-12345"))

    # Check spans
    spans = exporter.get_finished_spans()

    # Find the init span
    span = next((s for s in spans if s.name == "SensitiveModel.__init__"), None)
    assert span is not None, "Init span not found"
    assert span.status.is_ok
    assert span.attributes.get("code.function") == "__init__"

    # Check redaction in dump
    dump = model.model_dump()
    assert dump["api_key"] == "***"
    assert dump["name"] == "test"

    # Ensure api_key IS stored internally (not redacted in memory)
    assert model.api_key.get_secret_value() == "sk-12345"
