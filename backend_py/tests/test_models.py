"""Test data models."""

import pytest
from datetime import datetime
from werewolf.models.player import Player, Role, PlayerStatus, AIConfig
from werewolf.models.room import GameRoom, RoomStatus
from werewolf.models.game import GameSession, GamePhase, GameEvent, Team, EventType


class TestPlayer:
    """Test Player model."""

    def test_player_creation(self):
        """Test player creation."""
        player = Player.create_ai_player(
            name="TestPlayer",
            room_id="test-room",
            position=1
        )

        assert player.name == "TestPlayer"
        assert player.room_id == "test-room"
        assert player.position == 1
        assert player.status == PlayerStatus.ALIVE
        assert player.ai_config is not None

    def test_player_death(self):
        """Test player death."""
        player = Player(name="TestPlayer")
        player.die("werewolf_kill")

        assert player.status == PlayerStatus.DEAD
        assert player.death_cause == "werewolf_kill"

    def test_player_revival(self):
        """Test player revival."""
        player = Player(name="TestPlayer", status=PlayerStatus.DEAD)
        player.revive()

        assert player.status == PlayerStatus.ALIVE
        assert player.death_cause is None

    def test_seer_ability(self):
        """Test seer ability."""
        player = Player(name="Seer", role=Role.SEER)

        # Test seer check
        result = player.seer_check("target-id")
        assert result["success"] is True
        assert result["action"] == "seer_check"
        assert result["targetPlayer"] == "target-id"

    def test_witch_ability(self):
        """Test witch ability."""
        player = Player(name="Witch", role=Role.WITCH)

        # Test witch save
        assert player.can_use_save() is True
        player.use_save()
        assert player.can_use_save() is False

        # Test witch poison
        assert player.can_use_poison() is True
        player.use_poison()
        assert player.can_use_poison() is False

    def test_hunter_ability(self):
        """Test hunter ability."""
        player = Player(name="Hunter", role=Role.HUNTER)

        # Test hunter shoot
        result = player.hunter_shoot("target-id")
        assert result["success"] is True
        assert result["action"] == "hunter_shoot"
        assert result["targetPlayer"] == "target-id"

    def test_get_private_info(self):
        """Test getting private player info."""
        player = Player(
            name="TestPlayer",
            role=Role.WEREWOLF,
            status=PlayerStatus.ALIVE
        )

        info = player.get_private_info()
        assert info["name"] == "TestPlayer"
        assert info["role"] == "werewolf"
        assert info["isAlive"] is True

    def test_get_public_info(self):
        """Test getting public player info."""
        player = Player(
            name="TestPlayer",
            role=Role.WEREWOLF,  # Role should be hidden in public info
            status=PlayerStatus.ALIVE
        )

        info = player.get_public_info()
        assert info["name"] == "TestPlayer"
        assert "role" not in info  # Role should not be in public info
        assert info["isAlive"] is True


class TestGameRoom:
    """Test GameRoom model."""

    def test_room_creation(self):
        """Test room creation."""
        room = GameRoom.create_room(
            creator_name="Creator",
            room_name="Test Room",
            max_players=9
        )

        assert room.name == "Test Room"
        assert room.max_players == 9
        assert room.current_players == 1
        assert room.status == RoomStatus.WAITING

    def test_add_player(self):
        """Test adding player to room."""
        room = GameRoom.create_room("Creator", max_players=3)

        player = Player(name="Player1")
        assert room.add_player(player) is True
        assert room.current_players == 2

    def test_room_full(self):
        """Test room full condition."""
        room = GameRoom.create_room("Creator", max_players=2)

        player1 = Player(name="Player1")
        player2 = Player(name="Player2")

        room.add_player(player1)
        room.add_player(player2)

        assert room.is_full() is True

    def test_can_start_game(self):
        """Test game start condition."""
        room = GameRoom.create_room("Creator", max_players=4)

        # Add minimum players
        for i in range(3):  # Creator + 3 more = 4 players
            player = Player(name=f"Player{i}")
            room.add_player(player)

        assert room.can_start_game() is True

    def test_start_game(self):
        """Test starting game."""
        room = GameRoom.create_room("Creator", max_players=4)

        # Add minimum players
        for i in range(3):
            player = Player(name=f"Player{i}")
            room.add_player(player)

        room.start_game()
        assert room.status == RoomStatus.PLAYING

    def test_assign_roles(self):
        """Test role assignment."""
        room = GameRoom.create_room("Creator", max_players=6)

        # Add players
        for i in range(5):
            player = Player(name=f"Player{i}")
            room.add_player(player)

        role_counts = room.assign_roles()

        # Check that all players have roles
        for player in room.players:
            assert player.role is not None

        # Check role counts
        assert sum(role_counts.values()) == len(room.players)

    def test_get_players_info(self):
        """Test getting players info."""
        room = GameRoom.create_room("Creator", max_players=3)

        players_info = room.get_players_info()
        assert len(players_info) == 1
        assert players_info[0]["name"] == "Creator"


class TestGameSession:
    """Test GameSession model."""

    def test_session_creation(self):
        """Test session creation."""
        room = GameRoom.create_room("Creator", max_players=4)
        session = GameSession(room=room)

        assert session.room_id == room.id
        assert session.current_phase == GamePhase.NIGHT
        assert session.day_count == 1

    def test_phase_transition(self):
        """Test phase transition."""
        room = GameRoom.create_room("Creator", max_players=4)
        session = GameSession(room=room)

        session.transition_to_phase(GamePhase.DAY)
        assert session.current_phase == GamePhase.DAY

    def test_add_event(self):
        """Test adding event."""
        room = GameRoom.create_room("Creator", max_players=4)
        session = GameSession(room=room)

        event = session.add_event(
            event_type=EventType.PLAYER_SPEECH,
            actor_id="player1",
            content="Test speech"
        )

        assert event is not None
        assert event.content == "Test speech"
        assert len(session.events) == 1

    def test_get_alive_players(self):
        """Test getting alive players."""
        room = GameRoom.create_room("Creator", max_players=4)
        session = GameSession(room=room)

        # Create players with different statuses
        player1 = Player(name="Player1", status=PlayerStatus.ALIVE)
        player2 = Player(name="Player2", status=PlayerStatus.DEAD)

        session.players = [player1, player2]

        alive_players = session.get_alive_players()
        assert len(alive_players) == 1
        assert alive_players[0] == player1

    def test_victory_check(self):
        """Test victory condition checking."""
        room = GameRoom.create_room("Creator", max_players=6)
        session = GameSession(room=room)

        # Create players
        players = [
            Player(name="Wolf1", role=Role.WEREWOLF, status=PlayerStatus.ALIVE),
            Player(name="Wolf2", role=Role.WEREWOLF, status=PlayerStatus.ALIVE),
            Player(name="Villager1", role=Role.VILLAGER, status=PlayerStatus.ALIVE),
            Player(name="Villager2", role=Role.VILLAGER, status=PlayerStatus.ALIVE),
        ]

        session.players = players

        # Test no winner yet
        winner = session.check_victory()
        assert winner is None

        # Test werewolf victory
        players[2].status = PlayerStatus.DEAD
        players[3].status = PlayerStatus.DEAD
        winner = session.check_victory()
        assert winner == Team.WEREWOLF

        # Test villager victory
        players[0].status = PlayerStatus.DEAD
        players[1].status = PlayerStatus.DEAD
        players[2].status = PlayerStatus.ALIVE
        players[3].status = PlayerStatus.ALIVE
        winner = session.check_victory()
        assert winner == Team.VILLAGER


class TestGameEvent:
    """Test GameEvent model."""

    def test_event_creation(self):
        """Test event creation."""
        event = GameEvent(
            session_id="test-session",
            event_type=EventType.PLAYER_SPEECH,
            actor_id="player1",
            content="Test speech"
        )

        assert event.session_id == "test-session"
        assert event.event_type == EventType.PLAYER_SPEECH
        assert event.actor_id == "player1"
        assert event.content == "Test speech"

    def test_event_visibility(self):
        """Test event visibility."""
        event = GameEvent(
            session_id="test-session",
            event_type=EventType.WEREWOLF_KILL,
            actor_id="wolf1",
            target_id="villager1",
            content="Kill villager",
            visibility={"roles": ["werewolf"]}
        )

        # Check if werewolf can see event
        assert event.is_visible_to_player(Player(role=Role.WEREWOLF)) is True

        # Check if villager cannot see event
        assert event.is_visible_to_player(Player(role=Role.VILLAGER)) is False

    def test_public_event(self):
        """Test public event."""
        event = GameEvent(
            session_id="test-session",
            event_type=EventType.GAME_PHASE_CHANGE,
            content="Phase changed to day"
        )

        # Public events should be visible to everyone
        assert event.is_visible_to_player(Player(role=Role.WEREWOLF)) is True
        assert event.is_visible_to_player(Player(role=Role.VILLAGER)) is True

    def test_to_dict(self):
        """Test event serialization."""
        event = GameEvent(
            session_id="test-session",
            event_type=EventType.PLAYER_SPEECH,
            actor_id="player1",
            content="Test speech"
        )

        event_dict = event.to_dict()
        assert event_dict["sessionId"] == "test-session"
        assert event_dict["type"] == "player_speech"
        assert event_dict["actorId"] == "player1"
        assert event_dict["content"] == "Test speech"