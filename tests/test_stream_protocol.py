from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union
from uuid import uuid4

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.events import CloudEvent, GraphEvent
from coreason_manifest.definitions.interfaces import ResponseHandler, StreamHandle
from coreason_manifest.definitions.presentation import (
    ErrorSeverity,
    PresentationEvent,
    PresentationEventType,
    ProgressUpdate,
    StreamError,
    StreamOpCode,
    StreamPacket,
)


class MockStreamHandle:
    def __init__(self, stream_id: str) -> None:
        self._stream_id = stream_id
        self._active = True

    @property
    def stream_id(self) -> str:
        return self._stream_id

    @property
    def is_active(self) -> bool:
        return self._active

    async def write(self, chunk: str) -> None:
        if not self._active:
            raise RuntimeError("Stream is closed")

    async def close(self) -> None:
        self._active = False

    async def abort(self, reason: str) -> None:
        self._active = False


class MockResponseHandler:
    async def emit(self, event: Union[CloudEvent[Any], GraphEvent]) -> None:
        pass

    async def log(self, level: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        pass

    async def audit(self, actor: str, action: str, resource: str, success: bool) -> None:
        pass

    async def thought(self, content: str, status: str = "IN_PROGRESS") -> None:
        pass

    async def markdown(self, content: str) -> None:
        pass

    async def data(
        self,
        data: Dict[str, Any],
        title: Optional[str] = None,
        view_hint: str = "JSON",
    ) -> None:
        pass

    async def error(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = False,
    ) -> None:
        pass

    async def create_stream(
        self, title: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None
    ) -> StreamHandle:
        return MockStreamHandle("test-stream-id")


@pytest.mark.asyncio
async def test_stream_handle_protocol() -> None:
    handle = MockStreamHandle("id")
    # Runtime checkable
    assert isinstance(handle, StreamHandle)
    assert handle.stream_id == "id"
    assert handle.is_active
    await handle.write("chunk")
    await handle.close()
    assert not handle.is_active
    with pytest.raises(RuntimeError):
        await handle.write("chunk")


@pytest.mark.asyncio
async def test_response_handler_protocol() -> None:
    handler = MockResponseHandler()
    # Runtime checkable
    assert isinstance(handler, ResponseHandler)

    stream = await handler.create_stream()
    assert isinstance(stream, StreamHandle)
    await stream.write("hello")
    await stream.close()


def test_stream_packet_error_serialization() -> None:
    """Test Case 1: Create a StreamPacket with op=ERROR and a valid StreamError object."""
    stream_id = uuid4()
    now = datetime.now(timezone.utc)

    error = StreamError(
        code="rate_limit_exceeded",
        message="Too many requests",
        severity=ErrorSeverity.TRANSIENT,
        details={"limit": 100},
    )

    packet = StreamPacket(
        stream_id=stream_id,
        seq=1,
        op=StreamOpCode.ERROR,
        t=now,
        p=error,
    )

    dump = packet.dump()
    assert dump["op"] == "ERROR"
    assert dump["p"]["code"] == "rate_limit_exceeded"
    assert dump["p"]["severity"] == "TRANSIENT"


def test_stream_packet_error_validation_string() -> None:
    """Test Case 2 (Validation): Attempt to create a StreamPacket with op=ERROR and a raw string."""
    stream_id = uuid4()
    now = datetime.now(timezone.utc)

    with pytest.raises(
        ValueError, match="Payload must be a StreamError or Dict for ERROR op"
    ):
        StreamPacket(
            stream_id=stream_id,
            seq=1,
            op=StreamOpCode.ERROR,
            t=now,
            p="Something went wrong",
        )


def test_stream_error_severity_serialization() -> None:
    """Test Case 3 (Severity): Verify that ErrorSeverity serializes to its string value."""
    assert ErrorSeverity.FATAL == "FATAL"
    assert ErrorSeverity.TRANSIENT == "TRANSIENT"
    assert ErrorSeverity.WARNING == "WARNING"

    error = StreamError(
        code="test_code",
        message="test_msg",
        severity=ErrorSeverity.FATAL,
    )
    dump = error.dump()
    assert dump["severity"] == "FATAL"


def test_stream_packet_error_dict_coercion() -> None:
    """Test Case 4 (Coercion): Verify that a valid dict payload becomes a StreamError object."""
    stream_id = uuid4()
    now = datetime.now(timezone.utc)

    error_dict = {
        "code": "coercion_test",
        "message": "This should be coerced",
        "severity": "WARNING",
    }

    packet = StreamPacket(
        stream_id=stream_id,
        seq=1,
        op=StreamOpCode.ERROR,
        t=now,
        p=error_dict,
    )

    # Assert p became a StreamError instance
    assert isinstance(packet.p, StreamError)
    assert packet.p.code == "coercion_test"
    assert packet.p.severity == ErrorSeverity.WARNING


def test_stream_packet_error_invalid_dict() -> None:
    """Test Case 5 (Validation): Verify that an invalid dict raises ValidationError."""
    stream_id = uuid4()
    now = datetime.now(timezone.utc)

    invalid_dict = {
        "code": "missing_severity",
        "message": "Oops"
        # severity missing
    }

    # Expect ValidationError from StreamError.model_validate
    with pytest.raises(ValidationError):
        StreamPacket(
            stream_id=stream_id,
            seq=1,
            op=StreamOpCode.ERROR,
            t=now,
            p=invalid_dict,
        )


def test_stream_packet_error_wrong_type() -> None:
    """Test Case 6: Verify that a non-StreamError object raises ValueError for ERROR op."""
    stream_id = uuid4()
    now = datetime.now(timezone.utc)

    update = ProgressUpdate(label="test", status="running")
    event = PresentationEvent(
        id=uuid4(),
        timestamp=now,
        type=PresentationEventType.PROGRESS_INDICATOR,
        data=update,
    )

    with pytest.raises(ValueError, match="Payload must be a StreamError for ERROR op"):
        StreamPacket(
            stream_id=stream_id,
            seq=1,
            op=StreamOpCode.ERROR,
            t=now,
            p=event,
        )
