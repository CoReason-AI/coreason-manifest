import json
from typing import Any, ClassVar

from opentelemetry import trace
from pydantic import BaseModel, ConfigDict, SecretStr

tracer = trace.get_tracer(__name__)


class ObservableModel(BaseModel):
    """
    Base class for all manifest models.

    Features:
    - Native OpenTelemetry tracing for lifecycle events.
    - Automatic secret redaction in dumps.
    """
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    # Class-level exclusion list for fields that shouldn't be traced (if any)
    _trace_exclude: ClassVar[list[str]] = []

    def model_dump(self, **kwargs) -> dict[str, Any]:
        """
        Override model_dump to ensure secrets are redacted.
        """
        data = super().model_dump(**kwargs)
        return self._redact_secrets(data)

    def _redact_secrets(self, data: Any) -> Any:
        """
        Recursively redact secrets in the dictionary/list structure.
        """
        if isinstance(data, dict):
            return {k: self._redact_secrets(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._redact_secrets(item) for item in data]
        elif isinstance(data, SecretStr):
            return "***"
        return data

    def __init__(self, **data: Any):
        """
        Wraps initialization in an OTEL span.
        """
        with tracer.start_as_current_span(
            f"{self.__class__.__name__}.__init__",
            attributes={
                "code.function": "__init__",
                "code.namespace": self.__class__.__module__,
            }
        ) as span:
            try:
                super().__init__(**data)
                # We record the state AFTER initialization
                # But we must be careful not to spam huge payloads.
                # Maybe just record the ID if available.
                if hasattr(self, "id"):
                    span.set_attribute("gen_ai.system", getattr(self, "id"))

                # Optional: Record the full state diff (redacted)
                # serialized_state = json.dumps(self.model_dump(), default=str)
                # span.set_attribute("gen_ai.state", serialized_state)

            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                raise e
