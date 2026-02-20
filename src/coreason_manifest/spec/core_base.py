from typing import Any, ClassVar, cast
import json

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

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """
        Override model_dump to ensure secrets are redacted.
        """
        data = super().model_dump(**kwargs)
        # Ensure the result is a dict before returning, _redact_secrets handles recursion
        result = self._redact_secrets(data)
        if isinstance(result, dict):
            return result
        # Fallback if model_dump somehow returned non-dict (unlikely for BaseModel unless custom root)
        return cast(dict[str, Any], result)

    def _redact_secrets(self, data: Any) -> Any:
        """
        Recursively redact secrets in the dictionary/list structure.
        """
        if isinstance(data, dict):
            return {k: self._redact_secrets(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self._redact_secrets(item) for item in data]
        if isinstance(data, SecretStr):
            return "***"
        return data

    def dump_for_telemetry(self) -> str:
        """Safely dumps state for OTEL attributes, masking all secrets."""
        # Pydantic v2 natively masks SecretStr if converted to JSON, but we ensure
        # it is a pure string payload to prevent OTEL primitive type crashes.
        dumped_dict = self.model_dump(
            mode="json",
            exclude_none=True,
            # Force serialization of secrets to '**********'
            round_trip=False
        )
        return json.dumps(dumped_dict)

    def model_copy(self, *, update: dict[str, Any] | None = None, deep: bool = False, **kwargs: Any) -> "ObservableModel":
        """Intercepts state cloning to emit an OTEL transition span."""

        # Get tracer again or rely on module level. Module level is fine.
        tracer = trace.get_tracer(__name__)

        with tracer.start_as_current_span(f"{self.__class__.__name__}.transition") as span:
            # Generate the new state
            new_instance = super().model_copy(update=update, deep=deep, **kwargs)

            # Record the exact diff in the span natively
            if update:
                span.set_attribute(
                    "state.transition.diff",
                    # Must stringify to JSON, OTEL attributes do not accept dicts natively
                    json.dumps({k: str(v) for k, v in update.items()}, default=str)
                )

            return new_instance

    def __init__(self, **data: Any):
        """
        Wraps initialization in an OTEL span.
        """
        tracer = trace.get_tracer(__name__)

        with tracer.start_as_current_span(
            f"{self.__class__.__name__}.__init__",
            attributes={
                "code.function": "__init__",
                "code.namespace": self.__class__.__module__,
            },
        ) as span:
            try:
                super().__init__(**data)
                # We record the state AFTER initialization
                # But we must be careful not to spam huge payloads.
                # Maybe just record the ID if available.
                if hasattr(self, "id"):
                    span.set_attribute("gen_ai.system", getattr(self, "id"))

            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                raise e
