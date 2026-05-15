"""In-process pub/sub event bus.

Subscribers receive every event. Fan-out is fire-and-forget (we don't wait
for slow subscribers). The WebSocket gateway is the primary consumer; the
SQLite event recorder is the secondary consumer.
"""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator

from .schema import Event

log = logging.getLogger(__name__)


class EventBus:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[Event]] = set()
        self._lock = asyncio.Lock()

    async def publish(self, event: Event) -> None:
        async with self._lock:
            subs = list(self._subscribers)
        for q in subs:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                log.warning("Dropped event for slow subscriber: %s", event.type)

    async def subscribe(self) -> "Subscription":
        q: asyncio.Queue[Event] = asyncio.Queue(maxsize=1024)
        async with self._lock:
            self._subscribers.add(q)
        return Subscription(self, q)

    async def _remove(self, q: asyncio.Queue[Event]) -> None:
        async with self._lock:
            self._subscribers.discard(q)

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)


class Subscription:
    def __init__(self, bus: EventBus, queue: asyncio.Queue[Event]) -> None:
        self._bus = bus
        self._queue = queue

    async def __aenter__(self) -> "Subscription":
        return self

    async def __aexit__(self, *_exc) -> None:
        await self.close()

    async def close(self) -> None:
        await self._bus._remove(self._queue)

    async def stream(self) -> AsyncIterator[Event]:
        while True:
            ev = await self._queue.get()
            yield ev


_bus: EventBus | None = None


def get_bus() -> EventBus:
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus
