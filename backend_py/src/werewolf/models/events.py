"""Event models for werewolf game."""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from .game import EventType, GamePhase


@dataclass
class EventVisibility:
    """Event visibility configuration."""
    public: bool = True
    visible_to_roles: List[str] = field(default_factory=list)
    visible_to_players: List[str] = field(default_factory=list)
    requires_role_reveal: bool = False


@dataclass
class EventDetails:
    """Event-specific details."""
    # Seer check details
    seer_check_result: Optional[str] = None

    # Witch action details
    witch_action: Optional[Dict[str, Any]] = None

    # Voting details
    voting_details: Optional[Dict[str, Any]] = None

    # Death details
    death_details: Optional[Dict[str, Any]] = None

    # Hunter shoot details
    hunter_details: Optional[Dict[str, Any]] = None


@dataclass
class GameEvent:
    """Complete game event."""
    id: str
    session_id: str
    event_type: EventType
    phase: GamePhase
    day_count: int
    timestamp: datetime
    actor_id: Optional[str]
    actor_name: Optional[str]
    target_id: Optional[str]
    target_name: Optional[str]
    content: str
    details: Optional[EventDetails]
    visibility: EventVisibility

    @property
    def type(self) -> EventType:
        """Get event type."""
        return self.event_type

    @property
    def is_public(self) -> bool:
        """Check if event is public."""
        return self.visibility.public

    @property
    def day_number(self) -> int:
        """Alias for day_count."""
        return self.day_count

    def is_visible_to_player(self, player_id: str, player_role: Optional[str] = None) -> bool:
        """Check if event is visible to a specific player."""
        # Public events are visible to all
        if self.visibility.public:
            return True

        # Check role visibility
        if player_role and self.visibility.visible_to_roles:
            if player_role in self.visibility.visible_to_roles:
                return True

        # Check player-specific visibility
        if self.visibility.visible_to_players:
            if player_id in self.visibility.visible_to_players:
                return True

        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "type": self.event_type.value,
            "phase": self.phase.value,
            "day_count": self.day_count,
            "timestamp": self.timestamp.isoformat(),
            "actor_id": self.actor_id,
            "actor_name": self.actor_name,
            "target_id": self.target_id,
            "target_name": self.target_name,
            "content": self.content,
            "details": self.details.__dict__ if self.details else None,
            "visibility": {
                "public": self.visibility.public,
                "visible_to_roles": self.visibility.visible_to_roles,
                "visible_to_players": self.visibility.visible_to_players,
                "requires_role_reveal": self.visibility.requires_role_reveal,
            }
        }


class EventService:
    """Service for managing game events."""

    def __init__(self):
        self.events: Dict[str, List[GameEvent]] = {}  # session_id -> events

    async def record_event(
        self,
        session_id: str,
        event_type: EventType,
        content: str,
        phase: GamePhase,
        day_number: int,
        actor_id: Optional[str] = None,
        target_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        visible_to_players: Optional[List[str]] = None
    ) -> GameEvent:
        """Record a game event (async wrapper for create_event)."""
        # Create visibility configuration
        visibility = EventVisibility(
            public=visible_to_players is None,
            visible_to_players=visible_to_players or []
        )
        
        # Create event details if data provided
        details = None
        if data:
            details = EventDetails()
            if "result" in data:
                details.seer_check_result = data.get("result")
            if "action" in data:
                details.witch_action = data
        
        return self.create_event(
            session_id=session_id,
            event_type=event_type,
            phase=phase,
            day_count=day_number,
            content=content,
            actor_id=actor_id,
            target_id=target_id,
            details=details,
            visibility=visibility
        )

    def create_event(
        self,
        session_id: str,
        event_type: EventType,
        phase: GamePhase,
        day_count: int,
        content: str,
        actor_id: Optional[str] = None,
        actor_name: Optional[str] = None,
        target_id: Optional[str] = None,
        target_name: Optional[str] = None,
        details: Optional[EventDetails] = None,
        visibility: Optional[EventVisibility] = None
    ) -> GameEvent:
        """Create and store a new game event."""
        event = GameEvent(
            id=str(uuid.uuid4()),
            session_id=session_id,
            event_type=event_type,
            phase=phase,
            day_count=day_count,
            timestamp=datetime.now(),
            actor_id=actor_id,
            actor_name=actor_name,
            target_id=target_id,
            target_name=target_name,
            content=content,
            details=details,
            visibility=visibility or EventVisibility(public=True)
        )

        # Store event
        if session_id not in self.events:
            self.events[session_id] = []
        self.events[session_id].append(event)

        return event

    def get_session_events(self, session_id: str) -> List[GameEvent]:
        """Get all events for a session."""
        return self.events.get(session_id, [])

    def get_visible_events(
        self,
        session_id: str,
        player_id: Optional[str] = None,
        player_role: Optional[str] = None
    ) -> List[GameEvent]:
        """Get events visible to a specific player."""
        session_events = self.get_session_events(session_id)
        return [
            event for event in session_events
            if event.is_visible_to_player(player_id, player_role)
        ]

    def get_events_by_phase(self, session_id: str, phase: GamePhase) -> List[GameEvent]:
        """Get events from a specific phase."""
        session_events = self.get_session_events(session_id)
        return [event for event in session_events if event.phase == phase]

    def get_events_by_day(self, session_id: str, day_count: int) -> List[GameEvent]:
        """Get events from a specific day."""
        session_events = self.get_session_events(session_id)
        return [event for event in session_events if event.day_count == day_count]

    def get_events_by_type(
        self,
        session_id: str,
        event_type: EventType
    ) -> List[GameEvent]:
        """Get events of a specific type."""
        session_events = self.get_session_events(session_id)
        return [event for event in session_events if event.event_type == event_type]

    def get_recent_events(self, session_id: str, limit: int = 10) -> List[GameEvent]:
        """Get most recent events."""
        session_events = self.get_session_events(session_id)
        return sorted(session_events, key=lambda e: e.timestamp, reverse=True)[:limit]

    def search_events(
        self,
        session_id: str,
        query: Dict[str, Any]
    ) -> List[GameEvent]:
        """Search events based on criteria."""
        session_events = self.get_session_events(session_id)
        filtered_events = session_events

        if "event_type" in query:
            filtered_events = [
                e for e in filtered_events
                if e.event_type == query["event_type"]
            ]

        if "phase" in query:
            filtered_events = [
                e for e in filtered_events
                if e.phase == query["phase"]
            ]

        if "day_count" in query:
            filtered_events = [
                e for e in filtered_events
                if e.day_count == query["day_count"]
            ]

        if "actor_id" in query:
            filtered_events = [
                e for e in filtered_events
                if e.actor_id == query["actor_id"]
            ]

        if "target_id" in query:
            filtered_events = [
                e for e in filtered_events
                if e.target_id == query["target_id"]
            ]

        if "content" in query:
            search_content = query["content"].lower()
            filtered_events = [
                e for e in filtered_events
                if search_content in e.content.lower()
            ]

        return filtered_events

    def export_events(
        self,
        session_id: str,
        format_type: str = "json"
    ) -> str:
        """Export events in specified format."""
        session_events = self.get_session_events(session_id)

        if format_type == "json":
            import json
            return json.dumps([event.to_dict() for event in session_events], indent=2)
        elif format_type == "csv":
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Header
            writer.writerow([
                "id", "session_id", "type", "phase", "day_count",
                "timestamp", "actor_id", "actor_name", "target_id",
                "target_name", "content"
            ])

            # Rows
            for event in session_events:
                writer.writerow([
                    event.id,
                    event.session_id,
                    event.event_type.value,
                    event.phase.value,
                    event.day_count,
                    event.timestamp.isoformat(),
                    event.actor_id or "",
                    event.actor_name or "",
                    event.target_id or "",
                    event.target_name or "",
                    event.content
                ])

            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    def clear_session_events(self, session_id: str) -> None:
        """Clear all events for a session."""
        if session_id in self.events:
            del self.events[session_id]

    def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session."""
        session_events = self.get_session_events(session_id)

        stats = {
            "total_events": len(session_events),
            "events_by_type": {},
            "events_by_phase": {},
            "events_by_day": {},
            "public_events": 0,
            "private_events": 0,
            "time_span": None
        }

        for event in session_events:
            # Count by type
            event_type = event.event_type.value
            stats["events_by_type"][event_type] = stats["events_by_type"].get(event_type, 0) + 1

            # Count by phase
            phase = event.phase.value
            stats["events_by_phase"][phase] = stats["events_by_phase"].get(phase, 0) + 1

            # Count by day
            day = event.day_count
            stats["events_by_day"][day] = stats["events_by_day"].get(day, 0) + 1

            # Count public vs private
            if event.visibility.public:
                stats["public_events"] += 1
            else:
                stats["private_events"] += 1

        # Calculate time span
        if session_events:
            timestamps = [e.timestamp for e in session_events]
            time_span = max(timestamps) - min(timestamps)
            stats["time_span"] = {
                "seconds": int(time_span.total_seconds()),
                "minutes": int(time_span.total_seconds() / 60),
                "hours": int(time_span.total_seconds() / 3600)
            }

        return stats

    def get_service_status(self) -> Dict[str, Any]:
        """Get overall service status."""
        total_sessions = len(self.events)
        total_events = sum(len(events) for events in self.events.values())

        return {
            "total_sessions": total_sessions,
            "total_events": total_events,
            "memory_usage": len(self.events),
            "average_events_per_session": (
                total_events / total_sessions if total_sessions > 0 else 0
            )
        }

    def cleanup_expired_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up sessions older than max_age_hours."""
        import time
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)
        removed_events = 0

        expired_sessions = []
        for session_id, events in self.events.items():
            if not events:
                continue

            # Convert latest timestamp to seconds since epoch
            latest_timestamp = max(e.timestamp for e in events)
            session_age = latest_timestamp.timestamp()

            if session_age < cutoff_time:
                expired_sessions.append(session_id)
                removed_events += len(events)

        for session_id in expired_sessions:
            del self.events[session_id]

        return removed_events