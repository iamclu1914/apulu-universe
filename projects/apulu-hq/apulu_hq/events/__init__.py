"""Events package — pub/sub bus and versioned WS event schema."""

from .schema import Event, EventType, SCHEMA_VERSION
from .bus import EventBus, get_bus

__all__ = ["Event", "EventType", "SCHEMA_VERSION", "EventBus", "get_bus"]
