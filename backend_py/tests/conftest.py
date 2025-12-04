"""Pytest configuration and fixtures."""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
import tempfile
import os

from werewolf.database.connection import get_db, Base
from werewolf.database.models import PlayerDB, GameRoomDB, GameSessionDB, GameEventDB
from werewolf.web.api import create_app
from werewolf.config import settings


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    """Create temporary database."""
    # Create temporary SQLite database
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    yield path

    # Cleanup
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def test_db_session(temp_db: str) -> Generator[Session, None, None]:
    """Create test database session."""
    # Override database URL for testing
    test_db_url = f"sqlite:///{temp_db}"

    engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False}
    )

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_client(test_db_session: Session) -> Generator[TestClient, None, None]:
    """Create test client with database dependency override."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    # Remove dependency override
    app.dependency_overrides.clear()


@pytest.fixture
def sample_player_data() -> dict:
    """Sample player data for testing."""
    return {
        "name": "TestPlayer",
        "role": "villager",
        "ai_config": {
            "personality": "logical_analytical_cautious",
            "skill_level": "intermediate",
            "response_time": "normal",
            "language": "zh"
        }
    }


@pytest.fixture
def sample_room_data() -> dict:
    """Sample room data for testing."""
    return {
        "player_name": "TestCreator",
        "room_name": "Test Room",
        "max_players": 9
    }


@pytest.fixture
def sample_game_room(test_db_session: Session) -> GameRoomDB:
    """Create sample game room for testing."""
    room_data = {
        "name": "Test Room",
        "creator_id": "test-creator-id",
        "max_players": 9,
        "min_players": 4,
        "current_players": 1,
        "status": "waiting"
    }

    room = GameRoomDB(**room_data)
    test_db_session.add(room)
    test_db_session.commit()
    test_db_session.refresh(room)

    return room


@pytest.fixture
def sample_player(test_db_session: Session, sample_game_room: GameRoomDB) -> PlayerDB:
    """Create sample player for testing."""
    player_data = {
        "name": "TestPlayer",
        "room_id": sample_game_room.id,
        "role": "villager",
        "status": "alive",
        "position": 1,
        "ai_config": {
            "personality": "logical_analytical_cautious",
            "skill_level": "intermediate",
            "response_time": "normal",
            "language": "zh"
        }
    }

    player = PlayerDB(**player_data)
    test_db_session.add(player)
    test_db_session.commit()
    test_db_session.refresh(player)

    return player


@pytest.fixture
def mock_ai_manager():
    """Mock AI manager for testing."""
    from unittest.mock import Mock
    from werewolf.services.ai_manager import AIManager

    mock = Mock(spec=AIManager)
    mock.is_initialized = True
    mock.agents = {}
    mock.create_agent.return_value = "test-agent-id"
    mock.send_message.return_value = Mock(
        success=True,
        data={"action": "test_action", "result": "success"}
    )
    mock.health_check.return_value = {
        "status": "healthy",
        "agent_count": 0
    }

    return mock


@pytest.fixture
def mock_game_engine():
    """Mock game engine for testing."""
    from unittest.mock import Mock
    from werewolf.services.game_engine import GameEngine

    mock = Mock(spec=GameEngine)
    mock.get_session.return_value = Mock(
        id="test-session-id",
        room_id="test-room-id",
        current_phase="night",
        day_count=1
    )
    mock.start_game.return_value = Mock(
        id="test-session-id",
        status="started"
    )
    mock.get_game_summary.return_value = {
        "session_id": "test-session-id",
        "status": "active",
        "current_phase": "night",
        "day_count": 1
    }

    return mock


@pytest.fixture
def websocket_test_client():
    """Create WebSocket test client."""
    from unittest.mock import Mock
    from werewolf.web.websocket import WebSocketManager
    from werewolf.web.api import create_app

    app = create_app()
    mock_manager = Mock(spec=WebSocketManager)
    mock_manager.connected_clients = {}
    mock_manager.room_clients = {}

    return {
        "app": app,
        "manager": mock_manager
    }


@pytest.fixture(scope="function", autouse=True)
async def cleanup_test_data():
    """Cleanup test data after each test."""
    yield
    # Cleanup can be done here if needed
    pass