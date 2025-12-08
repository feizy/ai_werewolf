"""CRUD operations for werewolf game database."""

from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from loguru import logger

from .models import PlayerDB, GameRoomDB, GameSessionDB, GameEventDB
from ..models.player import PlayerStatus, Role
from ..models.room import RoomStatus
from ..models.game import GamePhase, EventType


class BaseCRUD:
    """Base CRUD operations."""

    def __init__(self, model):
        self.model = model

    def get(self, db: Session, id: str) -> Optional[Any]:
        """Get record by ID."""
        try:
            return db.query(self.model).filter(self.model.id == id).first()
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by ID: {e}")
            return None

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """Get multiple records with pagination."""
        try:
            query = db.query(self.model)

            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        query = query.filter(getattr(self.model, key) == value)

            return query.offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting multiple {self.model.__name__}: {e}")
            return []

    def create(self, db: Session, obj_in: Dict[str, Any]) -> Optional[Any]:
        """Create new record."""
        try:
            db_obj = self.model(**obj_in)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            logger.error(f"Error creating {self.model.__name__}: {e}")
            db.rollback()
            return None

    def update(
        self,
        db: Session,
        db_obj: Any,
        obj_in: Dict[str, Any]
    ) -> Optional[Any]:
        """Update record."""
        try:
            for field, value in obj_in.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)

            db_obj.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            logger.error(f"Error updating {self.model.__name__}: {e}")
            db.rollback()
            return None

    def delete(self, db: Session, id: str) -> bool:
        """Delete record by ID."""
        try:
            obj = db.query(self.model).filter(self.model.id == id).first()
            if obj:
                db.delete(obj)
                db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting {self.model.__name__}: {e}")
            db.rollback()
            return False


class PlayerCRUD(BaseCRUD):
    """CRUD operations for players."""

    def __init__(self):
        super().__init__(PlayerDB)

    def get_by_name(self, db: Session, name: str) -> Optional[PlayerDB]:
        """Get player by name."""
        try:
            return db.query(PlayerDB).filter(PlayerDB.name == name).first()
        except Exception as e:
            logger.error(f"Error getting player by name: {e}")
            return None

    def get_by_room(self, db: Session, room_id: str) -> List[PlayerDB]:
        """Get all players in a room."""
        try:
            return db.query(PlayerDB).filter(PlayerDB.room_id == room_id).all()
        except Exception as e:
            logger.error(f"Error getting players by room: {e}")
            return []

    def get_alive_players(self, db: Session, room_id: str) -> List[PlayerDB]:
        """Get all alive players in a room."""
        try:
            return db.query(PlayerDB).filter(
                and_(
                    PlayerDB.room_id == room_id,
                    PlayerDB.status == PlayerStatus.ALIVE
                )
            ).all()
        except Exception as e:
            logger.error(f"Error getting alive players: {e}")
            return []

    def get_by_role(self, db: Session, room_id: str, role: Role) -> List[PlayerDB]:
        """Get players by role in a room."""
        try:
            return db.query(PlayerDB).filter(
                and_(
                    PlayerDB.room_id == room_id,
                    PlayerDB.role == role
                )
            ).all()
        except Exception as e:
            logger.error(f"Error getting players by role: {e}")
            return []

    def update_status(self, db: Session, player_id: str, status: PlayerStatus) -> bool:
        """Update player status."""
        try:
            player = db.query(PlayerDB).filter(PlayerDB.id == player_id).first()
            if player:
                player.status = status
                player.updated_at = datetime.utcnow()
                db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating player status: {e}")
            db.rollback()
            return False

    def update_last_active(self, db: Session, player_id: str) -> bool:
        """Update player last active timestamp."""
        try:
            player = db.query(PlayerDB).filter(PlayerDB.id == player_id).first()
            if player:
                player.last_active = datetime.utcnow()
                db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating player last active: {e}")
            db.rollback()
            return False

    def count_by_room(self, db: Session, room_id: str) -> int:
        """Count players in a room."""
        try:
            return db.query(PlayerDB).filter(PlayerDB.room_id == room_id).count()
        except Exception as e:
            logger.error(f"Error counting players by room: {e}")
            return 0


class GameRoomCRUD(BaseCRUD):
    """CRUD operations for game rooms."""

    def __init__(self):
        super().__init__(GameRoomDB)

    def get_by_status(self, db: Session, status: RoomStatus) -> List[GameRoomDB]:
        """Get rooms by status."""
        try:
            return db.query(GameRoomDB).filter(GameRoomDB.status == status).all()
        except Exception as e:
            logger.error(f"Error getting rooms by status: {e}")
            return []

    def get_active_rooms(self, db: Session) -> List[GameRoomDB]:
        """Get active rooms (waiting or playing)."""
        try:
            return db.query(GameRoomDB).filter(
                or_(
                    GameRoomDB.status == RoomStatus.WAITING,
                    GameRoomDB.status == RoomStatus.PLAYING
                )
            ).all()
        except Exception as e:
            logger.error(f"Error getting active rooms: {e}")
            return []

    def update_status(self, db: Session, room_id: str, status: RoomStatus) -> bool:
        """Update room status."""
        try:
            room = db.query(GameRoomDB).filter(GameRoomDB.id == room_id).first()
            if room:
                room.status = status
                room.updated_at = datetime.utcnow()

                if status == RoomStatus.PLAYING and not room.game_started_at:
                    room.game_started_at = datetime.utcnow()
                elif status == RoomStatus.FINISHED:
                    room.game_finished_at = datetime.utcnow()

                db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating room status: {e}")
            db.rollback()
            return False

    def update_player_count(self, db: Session, room_id: str, count: int) -> bool:
        """Update room player count."""
        try:
            room = db.query(GameRoomDB).filter(GameRoomDB.id == room_id).first()
            if room:
                room.current_players = count
                room.updated_at = datetime.utcnow()
                db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating player count: {e}")
            db.rollback()
            return False

    def set_current_game(self, db: Session, room_id: str, game_id: str) -> bool:
        """Set current game for room."""
        try:
            room = db.query(GameRoomDB).filter(GameRoomDB.id == room_id).first()
            if room:
                room.current_game_id = game_id
                room.updated_at = datetime.utcnow()
                db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error setting current game: {e}")
            db.rollback()
            return False


class GameSessionCRUD(BaseCRUD):
    """CRUD operations for game sessions."""

    def __init__(self):
        super().__init__(GameSessionDB)

    def get_by_room(self, db: Session, room_id: str) -> Optional[GameSessionDB]:
        """Get current game session for room."""
        try:
            return db.query(GameSessionDB).filter(
                GameSessionDB.room_id == room_id
            ).order_by(desc(GameSessionDB.created_at)).first()
        except Exception as e:
            logger.error(f"Error getting game session by room: {e}")
            return None

    def get_active_sessions(self, db: Session) -> List[GameSessionDB]:
        """Get all active game sessions."""
        try:
            return db.query(GameSessionDB).filter(GameSessionDB.winner.is_(None)).all()
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return []

    def update_phase(self, db: Session, session_id: str, phase: GamePhase) -> bool:
        """Update game session phase."""
        try:
            session = db.query(GameSessionDB).filter(GameSessionDB.id == session_id).first()
            if session:
                session.current_phase = phase
                session.phase_start_time = datetime.utcnow()
                session.updated_at = datetime.utcnow()

                if phase == GamePhase.DAY_DISCUSSION and session.day_count == 1:
                    session.started_at = datetime.utcnow()

                db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating game phase: {e}")
            db.rollback()
            return False

    def increment_day(self, db: Session, session_id: str) -> bool:
        """Increment day count."""
        try:
            session = db.query(GameSessionDB).filter(GameSessionDB.id == session_id).first()
            if session:
                session.day_count += 1
                session.updated_at = datetime.utcnow()
                db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error incrementing day: {e}")
            db.rollback()
            return False

    def end_game(self, db: Session, session_id: str, winner, end_reason: str) -> bool:
        """End game session."""
        try:
            session = db.query(GameSessionDB).filter(GameSessionDB.id == session_id).first()
            if session:
                session.winner = winner
                session.end_reason = end_reason
                session.ended_at = datetime.utcnow()
                session.updated_at = datetime.utcnow()
                db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error ending game: {e}")
            db.rollback()
            return False

    def update_game_state(self, db: Session, session_id: str, game_state: Dict[str, Any]) -> bool:
        """Update game state."""
        try:
            session = db.query(GameSessionDB).filter(GameSessionDB.id == session_id).first()
            if session:
                session.game_state = game_state
                session.updated_at = datetime.utcnow()
                db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating game state: {e}")
            db.rollback()
            return False


class GameEventCRUD(BaseCRUD):
    """CRUD operations for game events."""

    def __init__(self):
        super().__init__(GameEventDB)

    def get_by_session(self, db: Session, session_id: str) -> List[GameEventDB]:
        """Get all events for a game session."""
        try:
            return db.query(GameEventDB).filter(
                GameEventDB.game_session_id == session_id
            ).order_by(asc(GameEventDB.timestamp)).all()
        except Exception as e:
            logger.error(f"Error getting events by session: {e}")
            return []

    def get_by_day(self, db: Session, session_id: str, day_number: int) -> List[GameEventDB]:
        """Get events for a specific day."""
        try:
            return db.query(GameEventDB).filter(
                and_(
                    GameEventDB.game_session_id == session_id,
                    GameEventDB.day_number == day_number
                )
            ).order_by(asc(GameEventDB.timestamp)).all()
        except Exception as e:
            logger.error(f"Error getting events by day: {e}")
            return []

    def get_by_phase(self, db: Session, session_id: str, phase: GamePhase) -> List[GameEventDB]:
        """Get events for a specific phase."""
        try:
            return db.query(GameEventDB).filter(
                and_(
                    GameEventDB.game_session_id == session_id,
                    GameEventDB.phase == phase
                )
            ).order_by(asc(GameEventDB.timestamp)).all()
        except Exception as e:
            logger.error(f"Error getting events by phase: {e}")
            return []

    def get_public_events(self, db: Session, session_id: str) -> List[GameEventDB]:
        """Get public events."""
        try:
            return db.query(GameEventDB).filter(
                and_(
                    GameEventDB.game_session_id == session_id,
                    GameEventDB.is_public == True
                )
            ).order_by(asc(GameEventDB.timestamp)).all()
        except Exception as e:
            logger.error(f"Error getting public events: {e}")
            return []

    def get_events_by_actor(self, db: Session, session_id: str, actor_id: str) -> List[GameEventDB]:
        """Get events by actor."""
        try:
            return db.query(GameEventDB).filter(
                and_(
                    GameEventDB.game_session_id == session_id,
                    GameEventDB.actor_id == actor_id
                )
            ).order_by(asc(GameEventDB.timestamp)).all()
        except Exception as e:
            logger.error(f"Error getting events by actor: {e}")
            return []

    def get_recent_events(self, db: Session, session_id: str, limit: int = 10) -> List[GameEventDB]:
        """Get recent events."""
        try:
            return db.query(GameEventDB).filter(
                GameEventDB.game_session_id == session_id
            ).order_by(desc(GameEventDB.timestamp)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting recent events: {e}")
            return []

    def create_event(
        self,
        db: Session,
        session_id: str,
        event_type: EventType,
        phase: GamePhase,
        day_number: int,
        content: str,
        actor_id: Optional[str] = None,
        target_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        visibility: Optional[Dict[str, Any]] = None,
        is_public: bool = True
    ) -> Optional[GameEventDB]:
        """Create new game event."""
        try:
            event_data = {
                "game_session_id": session_id,
                "event_type": event_type,
                "phase": phase,
                "day_number": day_number,
                "content": content,
                "actor_id": actor_id,
                "target_id": target_id,
                "data": data,
                "visibility": visibility,
                "is_public": is_public,
                "timestamp": datetime.utcnow()
            }

            event = GameEventDB(**event_data)
            db.add(event)
            db.commit()
            db.refresh(event)
            return event
        except Exception as e:
            logger.error(f"Error creating game event: {e}")
            db.rollback()
            return None