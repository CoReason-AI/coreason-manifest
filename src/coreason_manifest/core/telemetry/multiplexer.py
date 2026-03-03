import asyncio
from collections.abc import AsyncGenerator, Awaitable, Callable

from loguru import logger

from coreason_manifest.core.telemetry.custody import EpistemicEnvelope
from coreason_manifest.core.telemetry.stream import (
    StreamCloseEnvelope,
    StreamEpistemicEnvelope,
    StreamPacket,
    StreamUIEnvelope,
)

logger.disable("coreason_manifest")


class AsyncSSEMultiplexer:
    """
    A thread-safe buffer using asyncio.Queue to handle LLM backpressure
    and multiplex stream packets into Server-Sent Events (SSE).
    """

    def __init__(self, ui_observers: list[Callable[[StreamPacket], Awaitable[None]]] | None = None) -> None:
        """Initialize the multiplexer with a queue."""
        self._queue: asyncio.Queue[StreamPacket] | None = None
        self._background_tasks: set[asyncio.Task[None]] = set()
        self.ui_observers = ui_observers

    async def _get_queue(self) -> asyncio.Queue[StreamPacket]:
        if self._queue is None:
            self._queue = asyncio.Queue(maxsize=250)
        return self._queue

    async def push(self, packet: StreamPacket) -> None:
        """
        Push a stream packet into the buffer with a timeout to prevent deadlock.
        """

        if isinstance(packet, StreamUIEnvelope) and self.ui_observers:
            for observer in self.ui_observers:
                try:
                    await observer(packet)
                except Exception as e:
                    logger.error(
                        "ui_observer_failed", observer=getattr(observer, "__name__", str(observer)), error=str(e)
                    )

        queue = await self._get_queue()
        try:
            await asyncio.wait_for(queue.put(packet), timeout=1.0)
        except TimeoutError:
            logger.warning("telemetry_queue_full", action="dropped_stream_packet", reason="prevent_llm_stalling")

    async def broadcast_envelope(self, envelope: EpistemicEnvelope) -> None:
        """
        Broadcasts an EpistemicEnvelope asynchronously without blocking the GPU.
        The packet is pushed to the buffer via a background task.
        """

        async def _push_task() -> None:
            import time

            queue = await self._get_queue()
            await queue.put(StreamEpistemicEnvelope(op="epistemic", p=envelope, timestamp=time.time()))

        task = asyncio.create_task(_push_task())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def flush(self) -> None:
        """
        Awaits all background tasks to explicitly clear telemetry
        before a spot-instance shutdown.
        """
        if self._background_tasks:
            results = await asyncio.gather(*self._background_tasks, return_exceptions=True)
            exceptions = [r for r in results if isinstance(r, Exception)]

            if exceptions:
                eg = ExceptionGroup("Telemetry flush failures", exceptions)
                try:
                    raise eg
                except* asyncio.CancelledError:
                    pass
                except* (TimeoutError, ConnectionError) as eg_network:
                    for e_net in eg_network.exceptions:
                        logger.error("flush_network_error", error=str(e_net))
                except* Exception as eg_generic:
                    for e_gen in eg_generic.exceptions:
                        logger.error("flush_generic_error", error=str(e_gen))

    async def stream_sse(self) -> AsyncGenerator[str, None]:
        """
        Consume the queue and yield strings formatted as SSE.
        Terminates upon encountering a StreamCloseEnvelope.
        """
        queue = await self._get_queue()
        while True:
            packet = await queue.get()

            try:
                # Format as SSE, ensuring multi-line JSON has `data: ` prefix on every line.
                json_str = packet.model_dump_json()
                formatted_data = "\n".join(f"data: {line}" for line in json_str.split("\n"))
                yield f"{formatted_data}\n\n"
            finally:
                queue.task_done()

            if isinstance(packet, StreamCloseEnvelope):
                break
