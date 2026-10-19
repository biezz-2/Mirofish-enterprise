"""
MiroFish Enterprise - Real-time Simulation Event Streaming & Emitter
Subagent H: MCP Protocol Integration Specialist
Broadcasts real-time events across 7 canonical platforms (twitter, reddit,
instagram, tiktok, threads, linkedin, youtube) to SSE consumers (frontend)
and external MCP tools/webhooks.
"""

import time
import json
import uuid
import logging
import threading
from queue import Queue, Empty
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Generator, Set

logger = logging.getLogger("mirofish.simulation_events")

CANONICAL_PLATFORMS = (
    "instagram",
    "linkedin",
    "reddit",
    "threads",
    "tiktok",
    "twitter",
    "youtube",
)


class SimulationEvent:
    """Standardized event data structure for 7-platform simulation logs."""
    def __init__(
        self,
        event_type: str,
        simulation_id: str,
        platform: str,
        payload: Dict[str, Any],
        round_num: int = 0,
        event_id: Optional[str] = None,
        timestamp: Optional[str] = None
    ):
        self.event_id = event_id or f"evt_{uuid.uuid4().hex[:12]}"
        self.event_type = event_type  # "action", "round_end", "simulation_end", "state_change"
        self.simulation_id = simulation_id
        self.platform = platform
        self.payload = payload
        self.round_num = round_num
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "simulation_id": self.simulation_id,
            "platform": self.platform,
            "round": self.round_num,
            "timestamp": self.timestamp,
            "data": self.payload
        }

    def to_sse(self) -> str:
        """Format as Server-Sent Event string."""
        data_json = json.dumps(self.to_dict(), ensure_ascii=False)
        return f"id: {self.event_id}\nevent: {self.event_type}\ndata: {data_json}\n\n"


class SimulationEventBroadcaster:
    """
    Central event broadcaster for MiroFish multi-platform simulation streams.
    Manages subscriber queues for SSE endpoints and triggers webhook dispatchers.
    """
    def __init__(self, max_buffer_size: int = 500):
        self.max_buffer_size = max_buffer_size
        self._subscribers: Dict[str, Set[Queue]] = {}  # simulation_id -> set of Queues
        self._global_subscribers: Set[Queue] = set()
        self._event_buffers: Dict[str, List[SimulationEvent]] = {}  # simulation_id -> list
        self._lock = threading.Lock()

    def subscribe(self, simulation_id: str) -> Queue:
        """Subscribe to events for a specific simulation."""
        q: Queue = Queue(maxsize=1000)
        with self._lock:
            if simulation_id not in self._subscribers:
                self._subscribers[simulation_id] = set()
            self._subscribers[simulation_id].add(q)
            logger.debug(f"[SimulationEventBroadcaster] Subscriber added for {simulation_id}. Total: {len(self._subscribers[simulation_id])}")
        return q

    def unsubscribe(self, simulation_id: str, q: Queue):
        """Unsubscribe queue."""
        with self._lock:
            if simulation_id in self._subscribers:
                self._subscribers[simulation_id].discard(q)
                if not self._subscribers[simulation_id]:
                    del self._subscribers[simulation_id]

    def subscribe_global(self) -> Queue:
        """Subscribe to events across all simulations."""
        q: Queue = Queue(maxsize=1000)
        with self._lock:
            self._global_subscribers.add(q)
        return q

    def unsubscribe_global(self, q: Queue):
        """Unsubscribe global queue."""
        with self._lock:
            self._global_subscribers.discard(q)

    def publish_event(self, event: SimulationEvent):
        """Publish event to all subscribers and buffer it."""
        with self._lock:
            # 1. Add to buffer
            buf = self._event_buffers.setdefault(event.simulation_id, [])
            buf.append(event)
            if len(buf) > self.max_buffer_size:
                self._event_buffers[event.simulation_id] = buf[-self.max_buffer_size:]

            # 2. Distribute to specific subscribers
            subscribers = list(self._subscribers.get(event.simulation_id, set()))
            global_subs = list(self._global_subscribers)

        for q in subscribers:
            try:
                q.put_nowait(event)
            except Exception:
                pass

        for q in global_subs:
            try:
                q.put_nowait(event)
            except Exception:
                pass

        # 3. Optional async webhook broadcast
        self._broadcast_to_webhooks(event)

    def _broadcast_to_webhooks(self, event: SimulationEvent):
        try:
            from .webhook_service import webhook_dispatcher
            webhook_type = "SIMULATION_ACTION_EMITTED" if event.event_type == "action" else (
                "SIMULATION_ROUND_COMPLETED" if event.event_type == "round_end" else "SIMULATION_STATE_CHANGED"
            )
            webhook_dispatcher.broadcast(
                event_type=webhook_type,
                payload=event.to_dict(),
                async_mode=True
            )
        except Exception as e:
            logger.debug(f"Webhook broadcast skipped/failed: {e}")

    def emit_action(
        self,
        simulation_id: str,
        platform: str,
        round_num: int,
        agent_id: Any,
        agent_name: str,
        action_type: str,
        action_args: Optional[Dict[str, Any]] = None,
        result: Optional[str] = None,
        success: bool = True
    ) -> SimulationEvent:
        """Emit action event for an agent on one of the 7 platforms."""
        payload = {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "action_type": action_type,
            "action_args": action_args or {},
            "result": result,
            "success": success,
            "platform": platform
        }
        event = SimulationEvent(
            event_type="action",
            simulation_id=simulation_id,
            platform=platform,
            payload=payload,
            round_num=round_num
        )
        self.publish_event(event)
        return event

    def emit_round_end(
        self,
        simulation_id: str,
        platform: str,
        round_num: int,
        simulated_hours: int = 0,
        actions_count: int = 0
    ) -> SimulationEvent:
        """Emit round_end event for a platform."""
        payload = {
            "round": round_num,
            "simulated_hours": simulated_hours,
            "actions_count": actions_count,
            "platform": platform
        }
        event = SimulationEvent(
            event_type="round_end",
            simulation_id=simulation_id,
            platform=platform,
            payload=payload,
            round_num=round_num
        )
        self.publish_event(event)
        return event

    def emit_simulation_end(
        self,
        simulation_id: str,
        platform: str,
        total_rounds: int,
        total_actions: int
    ) -> SimulationEvent:
        """Emit simulation_end event."""
        payload = {
            "total_rounds": total_rounds,
            "total_actions": total_actions,
            "platform": platform
        }
        event = SimulationEvent(
            event_type="simulation_end",
            simulation_id=simulation_id,
            platform=platform,
            payload=payload,
            round_num=total_rounds
        )
        self.publish_event(event)
        return event

    def get_events(
        self,
        simulation_id: str,
        from_round: int = 0,
        platform: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get buffered events for replay or polling."""
        with self._lock:
            buf = self._event_buffers.get(simulation_id, [])
            filtered = [
                e.to_dict() for e in buf
                if e.round_num >= from_round and (platform is None or e.platform == platform)
            ]
            return filtered[:limit]

    def generate_sse_stream(
        self,
        simulation_id: str,
        from_round: int = 0,
        timeout: float = 30.0,
        heartbeat_interval: float = 5.0
    ) -> Generator[str, None, None]:
        """
        Yield SSE formatted strings for streaming to clients.
        First replays buffered events >= from_round, then streams live events.
        """
        # Replay backlog
        buffered = self.get_events(simulation_id, from_round=from_round, limit=200)
        for ev_dict in buffered:
            data_json = json.dumps(ev_dict, ensure_ascii=False)
            yield f"id: {ev_dict.get('event_id')}\nevent: {ev_dict.get('event_type')}\ndata: {data_json}\n\n"

        q = self.subscribe(simulation_id)
        start_time = time.time()
        last_heartbeat = time.time()
        try:
            while True:
                now = time.time()
                if timeout and (now - start_time > timeout):
                    break
                try:
                    event: SimulationEvent = q.get(timeout=1.0)
                    yield event.to_sse()
                    last_heartbeat = time.time()
                except Empty:
                    if now - last_heartbeat >= heartbeat_interval:
                        yield f": heartbeat {int(now)}\n\n"
                        last_heartbeat = now
        finally:
            self.unsubscribe(simulation_id, q)


# Global singleton broadcaster
simulation_broadcaster = SimulationEventBroadcaster()
