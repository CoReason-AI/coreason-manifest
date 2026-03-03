import asyncio
from collections.abc import AsyncGenerator

from coreason_manifest.core.telemetry.custody import EpistemicEnvelope
from coreason_manifest.core.telemetry.stream import StreamCloseEnvelope, StreamPacket


class AsyncSSEMultiplexer:
    """
    A thread-safe buffer using asyncio.Queue to handle LLM backpressure
    and multiplex stream packets into Server-Sent Events (SSE).
    """

    def __init__(self) -> None:
        """Initialize the multiplexer with a queue."""
        self._queue: asyncio.Queue[StreamPacket] | None = None
        self._background_tasks: set[asyncio.Task[None]] = set()

    async def _get_queue(self) -> asyncio.Queue[StreamPacket]:
        if self._queue is None:
            self._queue = asyncio.Queue(maxsize=250)
        return self._queue

    async def push(self, packet: StreamPacket) -> None:
        """
        Push a stream packet into the buffer.
        """
        queue = await self._get_queue()
        await queue.put(packet)

    async def broadcast_envelope(self, envelope: EpistemicEnvelope) -> None:
        """
        Broadcasts an EpistemicEnvelope asynchronously without blocking the GPU.
        The packet is pushed to the buffer via a background task.
        """

        async def _push_task() -> None:
            # Note: We assume the queue consumer can handle raw EpistemicEnvelopes.
            # We push the envelope itself, ignoring the strict StreamPacket type.
            queue = await self._get_queue()
            await queue.put(envelope)  # type: ignore[arg-type]

        task = asyncio.create_task(_push_task())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def flush(self) -> None:
        """
        Awaits all background tasks to explicitly clear telemetry
        before a spot-instance shutdown.
        """
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)

    async def stream_sse(self) -> AsyncGenerator[str, None]:
        """
        Consume the queue and yield strings formatted as SSE.
        Terminates upon encountering a StreamCloseEnvelope.
        """
        queue = await self._get_queue()
        while True:
            packet = await queue.get()

            try:
                # Use model_dump_json directly, formatting as SSE
                yield f"data: {packet.model_dump_json()}\n\n"
            finally:
                queue.task_done()

            if isinstance(packet, StreamCloseEnvelope):
                break
