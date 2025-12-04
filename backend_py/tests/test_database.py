"""Test database models and CRUD operations."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from werewolf.database.models import PlayerDB, GameRoomDB, GameSessionDB, GameEventDB
from werewolf.database.crud import PlayerCRUD, GameRoomCRUD, GameSessionCRUD, GameEventCRUD
from werewolf.database.manager import DatabaseManager
from werewolf.models.player import PlayerStatus, Role
from werewolf.models.room import RoomStatus
from werewolf.models.game import GamePhase, Team, EventType


class TestPlayerDB:
    """Test Player database model."""

    def test_player_creation(self, test_db_session: Session):
        """Test player creation in database."""
        player_data = {
            "name": "TestPlayer",
            "role": Role.VILLAGER,
            "status": PlayerStatus.ALIVE,
            "position": 1,
            "ai_config": {
                "personality": "logical_analytical_cautious",
                "skill_level": "intermediate",
                "response_time": "normal"
            }
        }

        player = PlayerDB(**player_data)
        test_db_session.add(player)
        test_db_session.commit()
        test_db_session.refresh(player)

        assert player.id is not None
        assert player.name == "TestPlayer"
        assert player.role == Role.VILLAGER
        assert player.status == PlayerStatus.ALIVE

    def test_player_hybrid_properties(self, test_db_session: Session):
        """Test player hybrid properties."""
        player = PlayerDB(
            name="TestPlayer",
            status=PlayerStatus.ALIVE
        )
        test_db_session.add(player)
        test_db_session.commit()

        assert player.is_alive is True

        player.status = PlayerStatus.DEAD
        test_db_session.commit()
        assert player.is_alive is False


class TestGameRoomDB:
    """Test GameRoom database model."""

    def test_room_creation(self, test_db_session: Session):
        """Test room creation in database."""
        room_data = {
            "name": "Test Room",
            "creator_id": "creator-id",
            "max_players": 9,
            "min_players": 4,
            "current_players": 1,
            "status": RoomStatus.WAITING
        }

        room = GameRoomDB(**room_data)
        test_db_session.add(room)
        test_db_session.commit()
        test_db_session.refresh(room)

        assert room.id is not None
        assert room.name == "Test Room"
        assert room.status == RoomStatus.WAITING

    def test_room_hybrid_properties(self, test_db_session: Session):
        """Test room hybrid properties."""
        room = GameRoomDB(
            name="Test Room",
            creator_id="creator-id",
            max_players=2,
            min_players=2,
            current_players=2,
            status=RoomStatus.WAITING
        )
        test_db_session.add(room)
        test_db_session.commit()

        assert room.is_full is True
        assert room.can_start_game is True

        room.current_players = 1
        test_db_session.commit()
        assert room.is_full is False
        assert room.can_start_game is False


class TestGameSessionDB:
    """Test GameSession database model."""

    def test_session_creation(self, test_db_session: Session, sample_game_room: GameRoomDB):
        """Test session creation in database."""
        session_data = {
            "room_id": sample_game_room.id,
            "current_phase": GamePhase.NIGHT,
            "day_count": 1,
            "game_state": {
                "players": [],
                "events": []
            }
        }

        session = GameSessionDB(**session_data)
        test_db_session.add(session)
        test_db_session.commit()
        test_db_session.refresh(session)

        assert session.id is not None
        assert session.room_id == sample_game_room.id
        assert session.current_phase == GamePhase.NIGHT
        assert session.day_count == 1

    def test_session_duration(self, test_db_session: Session, sample_game_room: GameRoomDB):
        """Test session duration calculation."""
        session = GameSessionDB(
            room_id=sample_game_room.id,
            started_at=datetime.utcnow() - timedelta(minutes=30)
        )
        test_db_session.add(session)
        test_db_session.commit()

        assert session.duration_minutes is not None
        assert session.duration_minutes >= 29  # Allow for some time difference

    def test_session_active_status(self, test_db_session: Session, sample_game_room: GameRoomDB):
        """Test session active status."""
        session = GameSessionDB(room_id=sample_game_room.id)
        test_db_session.add(session)
        test_db_session.commit()

        assert session.is_active is True

        session.winner = Team.VILLAGER
        test_db_session.commit()
        assert session.is_active is False


class TestGameEventDB:
    """Test GameEvent database model."""

    def test_event_creation(self, test_db_session: Session, sample_game_session: GameSessionDB):
        """Test event creation in database."""
        event_data = {
            "game_session_id": sample_game_session.id,
            "event_type": EventType.PLAYER_SPEECH,
            "phase": GamePhase.DAY,
            "day_number": 1,
            "actor_id": "player-id",
            "content": "Test speech content",
            "data": {"speech_type": "accusation"},
            "is_public": True
        }

        event = GameEventDB(**event_data)
        test_db_session.add(event)
        test_db_session.commit()
        test_db_session.refresh(event)

        assert event.id is not None
        assert event.game_session_id == sample_game_session.id
        assert event.event_type == EventType.PLAYER_SPEECH
        assert event.content == "Test speech content"


class TestPlayerCRUD:
    """Test Player CRUD operations."""

    def test_create_player(self, test_db_session: Session):
        """Test creating player."""
        player_data = {
            "name": "TestPlayer",
            "role": Role.SEER,
            "status": PlayerStatus.ALIVE,
            "position": 1
        }

        crud = PlayerCRUD()
        player = crud.create(test_db_session, player_data)

        assert player is not None
        assert player.name == "TestPlayer"
        assert player.role == Role.SEER

    def test_get_player_by_id(self, test_db_session: Session, sample_player: PlayerDB):
        """Test getting player by ID."""
        crud = PlayerCRUD()
        player = crud.get(test_db_session, sample_player.id)

        assert player is not None
        assert player.id == sample_player.id

    def test_get_player_by_name(self, test_db_session: Session, sample_player: PlayerDB):
        """Test getting player by name."""
        crud = PlayerCRUD()
        player = crud.get_by_name(test_db_session, sample_player.name)

        assert player is not None
        assert player.name == sample_player.name

    def test_get_players_by_room(self, test_db_session: Session, sample_game_room: GameRoomDB):
        """Test getting players by room."""
        # Create multiple players in the room
        for i in range(3):
            player = PlayerDB(
                name=f"Player{i}",
                room_id=sample_game_room.id,
                role=Role.VILLAGER,
                status=PlayerStatus.ALIVE,
                position=i + 1
            )
            test_db_session.add(player)
        test_db_session.commit()

        crud = PlayerCRUD()
        players = crud.get_by_room(test_db_session, sample_game_room.id)

        assert len(players) == 3

    def test_get_alive_players(self, test_db_session: Session, sample_game_room: GameRoomDB):
        """Test getting alive players."""
        # Create players with different statuses
        alive_player = PlayerDB(
            name="AlivePlayer",
            room_id=sample_game_room.id,
            status=PlayerStatus.ALIVE
        )
        dead_player = PlayerDB(
            name="DeadPlayer",
            room_id=sample_game_room.id,
            status=PlayerStatus.DEAD
        )

        test_db_session.add_all([alive_player, dead_player])
        test_db_session.commit()

        crud = PlayerCRUD()
        alive_players = crud.get_alive_players(test_db_session, sample_game_room.id)

        assert len(alive_players) == 1
        assert alive_players[0].name == "AlivePlayer"

    def test_update_player_status(self, test_db_session: Session, sample_player: PlayerDB):
        """Test updating player status."""
        crud = PlayerCRUD()
        result = crud.update_status(test_db_session, sample_player.id, PlayerStatus.DEAD)

        assert result is True

        updated_player = crud.get(test_db_session, sample_player.id)
        assert updated_player.status == PlayerStatus.DEAD


class TestGameRoomCRUD:
    """Test GameRoom CRUD operations."""

    def test_create_room(self, test_db_session: Session):
        """Test creating room."""
        room_data = {
            "name": "Test Room",
            "creator_id": "creator-id",
            "max_players": 9,
            "current_players": 1,
            "status": RoomStatus.WAITING
        }

        crud = GameRoomCRUD()
        room = crud.create(test_db_session, room_data)

        assert room is not None
        assert room.name == "Test Room"

    def test_get_rooms_by_status(self, test_db_session: Session):
        """Test getting rooms by status."""
        # Create rooms with different statuses
        waiting_room = GameRoomDB(
            name="Waiting Room",
            creator_id="creator1",
            status=RoomStatus.WAITING
        )
        playing_room = GameRoomDB(
            name="Playing Room",
            creator_id="creator2",
            status=RoomStatus.PLAYING
        )

        test_db_session.add_all([waiting_room, playing_room])
        test_db_session.commit()

        crud = GameRoomCRUD()
        waiting_rooms = crud.get_by_status(test_db_session, RoomStatus.WAITING)

        assert len(waiting_rooms) == 1
        assert waiting_rooms[0].name == "Waiting Room"

    def test_update_room_status(self, test_db_session: Session, sample_game_room: GameRoomDB):
        """Test updating room status."""
        crud = GameRoomCRUD()
        result = crud.update_status(test_db_session, sample_game_room.id, RoomStatus.PLAYING)

        assert result is True

        updated_room = crud.get(test_db_session, sample_game_room.id)
        assert updated_room.status == RoomStatus.PLAYING
        assert updated_room.game_started_at is not None


class TestGameSessionCRUD:
    """Test GameSession CRUD operations."""

    def test_create_session(self, test_db_session: Session, sample_game_room: GameRoomDB):
        """Test creating session."""
        session_data = {
            "room_id": sample_game_room.id,
            "current_phase": GamePhase.NIGHT,
            "day_count": 1
        }

        crud = GameSessionCRUD()
        session = crud.create(test_db_session, session_data)

        assert session is not None
        assert session.room_id == sample_game_room.id

    def test_get_session_by_room(self, test_db_session: Session, sample_game_room: GameRoomDB):
        """Test getting session by room."""
        session_data = {
            "room_id": sample_game_room.id,
            "current_phase": GamePhase.NIGHT
        }

        crud = GameSessionCRUD()
        crud.create(test_db_session, session_data)

        session = crud.get_by_room(test_db_session, sample_game_room.id)
        assert session is not None
        assert session.room_id == sample_game_room.id

    def test_update_session_phase(self, test_db_session: Session, sample_game_session: GameSessionDB):
        """Test updating session phase."""
        crud = GameSessionCRUD()
        result = crud.update_phase(
            test_db_session,
            sample_game_session.id,
            GamePhase.DAY
        )

        assert result is True

        updated_session = crud.get(test_db_session, sample_game_session.id)
        assert updated_session.current_phase == GamePhase.DAY

    def test_increment_day(self, test_db_session: Session, sample_game_session: GameSessionDB):
        """Test incrementing day count."""
        original_day = sample_game_session.day_count

        crud = GameSessionCRUD()
        result = crud.increment_day(test_db_session, sample_game_session.id)

        assert result is True

        updated_session = crud.get(test_db_session, sample_game_session.id)
        assert updated_session.day_count == original_day + 1


class TestGameEventCRUD:
    """Test GameEvent CRUD operations."""

    def test_create_event(self, test_db_session: Session, sample_game_session: GameSessionDB):
        """Test creating event."""
        crud = GameEventCRUD()
        event = crud.create_event(
            db=test_db_session,
            session_id=sample_game_session.id,
            event_type=EventType.PLAYER_SPEECH,
            phase=GamePhase.DAY,
            day_number=1,
            content="Test speech",
            actor_id="player-id"
        )

        assert event is not None
        assert event.content == "Test speech"
        assert event.actor_id == "player-id"

    def test_get_events_by_session(self, test_db_session: Session, sample_game_session: GameSessionDB):
        """Test getting events by session."""
        crud = GameEventCRUD()

        # Create multiple events
        for i in range(3):
            crud.create_event(
                db=test_db_session,
                session_id=sample_game_session.id,
                event_type=EventType.PLAYER_SPEECH,
                phase=GamePhase.DAY,
                day_number=1,
                content=f"Speech {i}",
                actor_id=f"player-{i}"
            )

        events = crud.get_by_session(test_db_session, sample_game_session.id)
        assert len(events) == 3

    def test_get_events_by_day(self, test_db_session: Session, sample_game_session: GameSessionDB):
        """Test getting events by day."""
        crud = GameEventCRUD()

        # Create events for different days
        crud.create_event(
            db=test_db_session,
            session_id=sample_game_session.id,
            event_type=EventType.GAME_PHASE_CHANGE,
            phase=GamePhase.NIGHT,
            day_number=1,
            content="Night phase started"
        )

        crud.create_event(
            db=test_db_session,
            session_id=sample_game_session.id,
            event_type=EventType.GAME_PHASE_CHANGE,
            phase=GamePhase.DAY,
            day_number=2,
            content="Day phase started"
        )

        day1_events = crud.get_by_day(test_db_session, sample_game_session.id, 1)
        day2_events = crud.get_by_day(test_db_session, sample_game_session.id, 2)

        assert len(day1_events) == 1
        assert len(day2_events) == 1
        assert day1_events[0].content == "Night phase started"
        assert day2_events[0].content == "Day phase started"

    def test_get_public_events(self, test_db_session: Session, sample_game_session: GameSessionDB):
        """Test getting public events."""
        crud = GameEventCRUD()

        # Create public and private events
        crud.create_event(
            db=test_db_session,
            session_id=sample_game_session.id,
            event_type=EventType.GAME_PHASE_CHANGE,
            phase=GamePhase.DAY,
            day_number=1,
            content="Phase change",
            is_public=True
        )

        crud.create_event(
            db=test_db_session,
            session_id=sample_game_session.id,
            event_type=EventType.WEREWOLF_KILL,
            phase=GamePhase.NIGHT,
            day_number=1,
            content="Kill target",
            is_public=False
        )

        public_events = crud.get_public_events(test_db_session, sample_game_session.id)
        assert len(public_events) == 1
        assert public_events[0].event_type == EventType.GAME_PHASE_CHANGE


class TestDatabaseManager:
    """Test DatabaseManager."""

    def test_manager_initialization(self):
        """Test database manager initialization."""
        manager = DatabaseManager()
        assert manager.engine is not None
        assert manager.SessionLocal is not None
        assert manager.player_crud is not None
        assert manager.room_crud is not None
        assert manager.session_crud is not None
        assert manager.event_crud is not None

    def test_get_session(self):
        """Test getting database session."""
        manager = DatabaseManager()
        session = manager.get_session()
        assert session is not None
        session.close()

    @pytest.mark.asyncio
    async def test_health_check(self, temp_db: str):
        """Test health check with temporary database."""
        from werewolf.database.connection import engine, Base, SessionLocal
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        # Create temporary database manager
        test_engine = create_engine(f"sqlite:///{temp_db}")
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        Base.metadata.create_all(bind=test_engine)

        class TestDatabaseManager(DatabaseManager):
            def __init__(self):
                self.engine = test_engine
                self.SessionLocal = TestingSessionLocal
                self.player_crud = PlayerCRUD()
                self.room_crud = GameRoomCRUD()
                self.session_crud = GameSessionCRUD()
                self.event_crud = GameEventCRUD()

        manager = TestDatabaseManager()
        health = manager.health_check()

        assert health["status"] == "healthy"
        assert "connection" in health
        assert "stats" in health