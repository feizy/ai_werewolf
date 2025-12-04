"""SQLAlchemy database models for werewolf game."""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, JSON, Index, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property

from .connection import Base
from ..models.player import PlayerStatus, Role, PersonalityType, SkillLevel, ResponseTime
from ..models.room import RoomStatus
from ..models.game import GamePhase, Team, EventType


class PlayerDB(Base):
    """Database model for players."""

    __tablename__ = "players"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    room_id = Column(String, ForeignKey("game_rooms.id"), nullable=True)

    # Game state
    role = Column(SQLEnum(Role), nullable=True)
    status = Column(SQLEnum(PlayerStatus), default=PlayerStatus.ALIVE, nullable=False)
    position = Column(Integer, nullable=True)

    # AI configuration
    ai_config = Column(JSON, nullable=True)
    agent_scope_id = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_active = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    room = relationship("GameRoomDB", back_populates="players")
    events = relationship("GameEventDB", foreign_keys="GameEventDB.actor_id", back_populates="actor")
    target_events = relationship("GameEventDB", foreign_keys="GameEventDB.target_id", back_populates="target")

    __table_args__ = (
        Index("idx_players_room_id", "room_id"),
        Index("idx_players_status", "status"),
        Index("idx_players_created_at", "created_at"),
    )

    @hybrid_property
    def is_alive(self) -> bool:
        """Check if player is alive."""
        return self.status == PlayerStatus.ALIVE

    @hybrid_property
    def ai_config_dict(self) -> Dict[str, Any]:
        """Get AI configuration as dictionary."""
        return self.ai_config or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert player to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "room_id": self.room_id,
            "role": self.role.value if self.role else None,
            "status": self.status.value,
            "position": self.position,
            "ai_config": self.ai_config,
            "agent_scope_id": self.agent_scope_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_active": self.last_active.isoformat() if self.last_active else None,
        }


class GameRoomDB(Base):
    """Database model for game rooms."""

    __tablename__ = "game_rooms"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=True)
    creator_id = Column(String, ForeignKey("players.id"), nullable=False)

    # Room configuration
    max_players = Column(Integer, default=9, nullable=False)
    min_players = Column(Integer, default=4, nullable=False)

    # Game configuration
    role_distribution = Column(JSON, nullable=True)
    phase_durations = Column(JSON, nullable=True)

    # Room state
    status = Column(SQLEnum(RoomStatus), default=RoomStatus.WAITING, nullable=False)
    current_players = Column(Integer, default=0, nullable=False)

    # Game session reference
    current_game_id = Column(String, ForeignKey("game_sessions.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    game_started_at = Column(DateTime, nullable=True)
    game_finished_at = Column(DateTime, nullable=True)

    # Relationships
    creator = relationship("PlayerDB", foreign_keys=[creator_id])
    players = relationship("PlayerDB", back_populates="room", foreign_keys="PlayerDB.room_id")
    current_game = relationship("GameSessionDB", foreign_keys=[current_game_id])

    __table_args__ = (
        Index("idx_game_rooms_status", "status"),
        Index("idx_game_rooms_created_at", "created_at"),
        Index("idx_game_rooms_creator_id", "creator_id"),
    )

    @hybrid_property
    def is_full(self) -> bool:
        """Check if room is full."""
        return self.current_players >= self.max_players

    @hybrid_property
    def can_start_game(self) -> bool:
        """Check if game can be started."""
        return (
            self.status == RoomStatus.WAITING and
            self.current_players >= self.min_players
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert room to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "creator_id": self.creator_id,
            "max_players": self.max_players,
            "min_players": self.min_players,
            "role_distribution": self.role_distribution,
            "phase_durations": self.phase_durations,
            "status": self.status.value,
            "current_players": self.current_players,
            "current_game_id": self.current_game_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "game_started_at": self.game_started_at.isoformat() if self.game_started_at else None,
            "game_finished_at": self.game_finished_at.isoformat() if self.game_finished_at else None,
        }


class GameSessionDB(Base):
    """Database model for game sessions."""

    __tablename__ = "game_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    room_id = Column(String, ForeignKey("game_rooms.id"), nullable=False)

    # Game state
    status = Column(String(50), default="night", nullable=False)
    current_phase = Column(SQLEnum(GamePhase), default=GamePhase.NIGHT, nullable=False)
    day_count = Column(Integer, default=1, nullable=False)

    # Game data
    game_state = Column(JSON, nullable=True)
    role_assignments = Column(JSON, nullable=True)

    # Game results
    winner = Column(SQLEnum(Team), nullable=True)
    end_reason = Column(String(200), nullable=True)

    # Sheriff information
    sheriff_id = Column(String, ForeignKey("players.id"), nullable=True)
    sheriff_name = Column(String(100), nullable=True)

    # Phase timing
    phase_start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    phase_end_time = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)

    # Relationships
    room = relationship("GameRoomDB", foreign_keys=[room_id])
    sheriff = relationship("PlayerDB", foreign_keys=[sheriff_id])
    events = relationship("GameEventDB", back_populates="game_session")

    __table_args__ = (
        Index("idx_game_sessions_room_id", "room_id"),
        Index("idx_game_sessions_status", "status"),
        Index("idx_game_sessions_phase", "current_phase"),
        Index("idx_game_sessions_created_at", "created_at"),
    )

    @hybrid_property
    def duration_minutes(self) -> Optional[float]:
        """Get game duration in minutes."""
        if self.started_at and self.ended_at:
            return (self.ended_at - self.started_at).total_seconds() / 60
        elif self.started_at:
            return (datetime.utcnow() - self.started_at).total_seconds() / 60
        return None

    @hybrid_property
    def is_active(self) -> bool:
        """Check if game is active."""
        return self.winner is None

    def to_dict(self) -> Dict[str, Any]:
        """Convert game session to dictionary."""
        return {
            "id": self.id,
            "room_id": self.room_id,
            "status": self.status,
            "current_phase": self.current_phase.value if self.current_phase else None,
            "day_count": self.day_count,
            "game_state": self.game_state,
            "role_assignments": self.role_assignments,
            "winner": self.winner.value if self.winner else None,
            "end_reason": self.end_reason,
            "sheriff_id": self.sheriff_id,
            "sheriff_name": self.sheriff_name,
            "phase_start_time": self.phase_start_time.isoformat() if self.phase_start_time else None,
            "phase_end_time": self.phase_end_time.isoformat() if self.phase_end_time else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_minutes": self.duration_minutes,
        }


class GameEventDB(Base):
    """Database model for game events."""

    __tablename__ = "game_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    game_session_id = Column(String, ForeignKey("game_sessions.id"), nullable=False)

    # Event information
    event_type = Column(SQLEnum(EventType), nullable=False)
    phase = Column(SQLEnum(GamePhase), nullable=False)
    day_number = Column(Integer, nullable=False)

    # Event participants
    actor_id = Column(String, ForeignKey("players.id"), nullable=True)
    target_id = Column(String, ForeignKey("players.id"), nullable=True)

    # Event data
    content = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)
    visibility = Column(JSON, nullable=True)  # Who can see this event

    # Event metadata
    event_order = Column(Integer, default=0, nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)

    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    game_session = relationship("GameSessionDB", back_populates="events")
    actor = relationship("PlayerDB", foreign_keys=[actor_id], back_populates="events")
    target = relationship("PlayerDB", foreign_keys=[target_id], back_populates="target_events")

    __table_args__ = (
        Index("idx_game_events_session_id", "game_session_id"),
        Index("idx_game_events_type", "event_type"),
        Index("idx_game_events_phase", "phase"),
        Index("idx_game_events_day", "day_number"),
        Index("idx_game_events_timestamp", "timestamp"),
        Index("idx_game_events_actor_id", "actor_id"),
        Index("idx_game_events_target_id", "target_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "id": self.id,
            "game_session_id": self.game_session_id,
            "event_type": self.event_type.value if self.event_type else None,
            "phase": self.phase.value if self.phase else None,
            "day_number": self.day_number,
            "actor_id": self.actor_id,
            "target_id": self.target_id,
            "content": self.content,
            "data": self.data,
            "visibility": self.visibility,
            "event_order": self.event_order,
            "is_public": self.is_public,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }