"""
Hospital Event Bus
Provides asynchronous event dispatching, persistent in-memory audit logs,
and real-time streaming listeners for the 3D visualization and dashboard.
"""

import asyncio
import logging
from typing import Callable, Coroutine, Dict, List, Set, Any
from .events import HospitalEvent, EventType

logger = logging.getLogger("HospitalEventBus")


class HospitalEventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[HospitalEvent], Coroutine[Any, Any, None]]]] = {}
        self._history: List[HospitalEvent] = []
        self._broadcast_queues: Set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()

    def subscribe(self, event_type: EventType | str, handler: Callable[[HospitalEvent], Coroutine[Any, Any, None]]):
        key = event_type.value if isinstance(event_type, EventType) else str(event_type)
        if key not in self._subscribers:
            self._subscribers[key] = []
        self._subscribers[key].append(handler)
        logger.info(f"Subscribed handler {handler.__name__} to event {key}")

    def register_broadcast_queue(self, queue: asyncio.Queue):
        self._broadcast_queues.add(queue)

    def unregister_broadcast_queue(self, queue: asyncio.Queue):
        self._broadcast_queues.discard(queue)

    async def publish(self, event: HospitalEvent):
        async with self._lock:
            self._history.append(event)
            # Limit in-memory history to last 5000 events
            if len(self._history) > 5000:
                self._history.pop(0)

        logger.info(f"[{event.event_type.value}] {event.summary} (Encounter: {event.encounter_id})")

        # Notify specific listeners
        handlers: List[Callable[[HospitalEvent], Coroutine[Any, Any, None]]] = []
        if event.event_type.value in self._subscribers:
            handlers.extend(self._subscribers[event.event_type.value])
        if "*" in self._subscribers:
            handlers.extend(self._subscribers["*"])

        for handler in handlers:
            try:
                asyncio.create_task(handler(event))
            except Exception as e:
                logger.error(f"Error invoking handler for {event.event_type}: {e}", exc_info=True)

        # Notify all real-time frontend streaming queues
        for queue in list(self._broadcast_queues):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning("Broadcast queue full, dropping frame for slow consumer")

    def get_encounter_events(self, encounter_id: str) -> List[HospitalEvent]:
        return [e for e in self._history if e.encounter_id == encounter_id]

    def get_recent_events(self, limit: int = 50) -> List[HospitalEvent]:
        return self._history[-limit:]

    def clear(self):
        self._history.clear()


# Global Singleton Event Bus Instance
event_bus = HospitalEventBus()
