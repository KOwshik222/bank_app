"""
Event bus abstraction — decouples banking services from transport.
In-memory implementation for development; Kafka implementation for production.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine
from uuid import uuid4

logger = logging.getLogger(__name__)

# Type alias for event handlers
EventHandler = Callable[["Event"], Coroutine[Any, Any, None]]


@dataclass
class Event:
    """Domain event published to the event bus."""

    topic: str
    payload: dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: str | None = None
    source_service: str | None = None


class EventBus(ABC):
    """Abstract event bus interface."""

    @abstractmethod
    async def publish(self, event: Event) -> None:
        """Publish an event to a topic."""
        ...

    @abstractmethod
    async def subscribe(self, topic: str, handler: EventHandler) -> None:
        """Subscribe a handler to a topic."""
        ...

    @abstractmethod
    async def start(self) -> None:
        """Start the event bus."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the event bus."""
        ...


class InMemoryEventBus(EventBus):
    """
    In-memory event bus for development.
    Handlers are called asynchronously in the background.
    Events are stored for replay/debugging.
    """

    def __init__(self, max_history: int = 10000):
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._history: list[Event] = []
        self._max_history = max_history
        self._running = False

    async def publish(self, event: Event) -> None:
        """Publish event — calls all subscribed handlers."""
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        handlers = self._handlers.get(event.topic, [])
        if handlers:
            logger.info(
                "Publishing event",
                extra={
                    "event_id": event.event_id,
                    "topic": event.topic,
                    "handler_count": len(handlers),
                    "correlation_id": event.correlation_id,
                },
            )
            # Fire handlers concurrently
            tasks = [asyncio.create_task(h(event)) for h in handlers]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(
                        f"Event handler failed: {result}",
                        extra={"event_id": event.event_id, "topic": event.topic},
                    )

    async def subscribe(self, topic: str, handler: EventHandler) -> None:
        """Register a handler for a topic."""
        self._handlers[topic].append(handler)
        logger.info(f"Subscribed handler to topic: {topic}")

    async def start(self) -> None:
        self._running = True
        logger.info("InMemoryEventBus started")

    async def stop(self) -> None:
        self._running = False
        logger.info("InMemoryEventBus stopped")

    def get_events(self, topic: str | None = None, limit: int = 100) -> list[Event]:
        """Retrieve recent events, optionally filtered by topic."""
        events = self._history
        if topic:
            events = [e for e in events if e.topic == topic]
        return events[-limit:]


# ── Singleton ────────────────────────────────────────────────────
_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = InMemoryEventBus()
    return _event_bus
