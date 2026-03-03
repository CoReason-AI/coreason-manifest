from opentelemetry.trace import Span


class ObservabilityTelemetry:
    """Wrapper for OpenTelemetry to add Agentic UX semantic conventions."""

    @staticmethod
    def record_genui_milestone(span: Span | None, event_type: str, timestamp: float) -> None:
        """
        Logs a GenUI milestone, specifically designed to log "Time to First Component" (TTFC).

        Args:
            span: The OpenTelemetry span object to add the event to.
            event_type: A string identifier for the event (e.g., 'ttfc', 'component_emitted').
            timestamp: The exact timestamp (float) of the emission.
        """
        if not span:
            return

        from typing import cast
        from opentelemetry.util.types import Attributes

        attributes = {
            "genui.event.type": event_type,
            "genui.event.timestamp": timestamp,
        }

        # Add semantic convention events to the span
        span.add_event(
            name=f"genui.milestone.{event_type}",
            attributes=cast(Attributes, attributes),
            timestamp=int(timestamp * 1e9),  # OpenTelemetry expects nanoseconds
        )
