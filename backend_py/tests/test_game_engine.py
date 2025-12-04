"""Test game engine functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from werewolf.services.game_engine import GameEngine
from werewolf.models.player import Player, Role, PlayerStatus
from werewolf.models.room import GameRoom, RoomStatus
from werewolf.models.game import GameSession, GamePhase, EventType
from werewolf.services.event_service import EventService
from werewolf.services.ai_manager import AIManager


class TestGameEngine:
    """Test GameEngine."""

    @pytest.fixture
    def sample_room(self):
        """Create sample game room."""
        room = GameRoom.create_room(
            creator_name="Creator",
            room_name="Test Room",
            max_players=6
        )

        # Add players
        players = [
            Player(name="Wolf1", role=Role.WEREWOLF),
            Player(name="Wolf2", role=Role.WEREWOLF),
            Player(name="Wolf3", role=Role.WEREWOLF),
            Player(name="Seer", role=Role.SEER),
            Player(name="Witch", role=Role.WITCH),
            Player(name="Hunter", role=Role.HUNTER),
        ]

        for player in players:
            room.add_player(player)

        return room

    @pytest.fixture
    def mock_ai_manager(self):
        """Create mock AI manager."""
        mock = Mock(spec=AIManager)
        mock.is_initialized = True
        mock.create_agent = AsyncMock(return_value="agent-id")
        mock.send_message = AsyncMock(return_value=Mock(
            success=True,
            data={"action": "test_action", "result": "success"}
        ))
        return mock

    @pytest.fixture
    def mock_event_service(self):
        """Create mock event service."""
        mock = Mock(spec=EventService)
        mock.record_event = AsyncMock()
        mock.broadcast_event = AsyncMock()
        return mock

    @pytest.fixture
    def game_engine(self, sample_room: GameRoom, mock_ai_manager, mock_event_service):
        """Create game engine instance."""
        return GameEngine(
            room=sample_room,
            ai_manager=mock_ai_manager,
            event_service=mock_event_service
        )

    def test_engine_initialization(self, game_engine: GameEngine, sample_room: GameRoom):
        """Test game engine initialization."""
        assert game_engine.room == sample_room
        assert game_engine.ai_manager is not None
        assert game_engine.event_service is not None
        assert game_engine.session is None

    @pytest.mark.asyncio
    async def test_start_game(self, game_engine: GameEngine, mock_ai_manager):
        """Test starting game."""
        # Mock role assignment
        with patch.object(game_engine.room, 'assign_roles') as mock_assign:
            mock_assign.return_value = {
                Role.WEREWOLF: 3,
                Role.SEER: 1,
                Role.WITCH: 1,
                Role.HUNTER: 1
            }

            session = await game_engine.start_game()

            assert session is not None
            assert session.room_id == game_engine.room.id
            assert session.current_phase == GamePhase.NIGHT
            assert len(session.players) == len(game_engine.room.players)

            # Check that AI agents were created
            assert mock_ai_manager.create_agent.call_count == len(game_engine.room.players)

    @pytest.mark.asyncio
    async def test_start_game_insufficient_players(self, mock_ai_manager, mock_event_service):
        """Test starting game with insufficient players."""
        room = GameRoom.create_room("Creator", max_players=6)
        # Only add creator (1 player)
        engine = GameEngine(room, mock_ai_manager, mock_event_service)

        with pytest.raises(ValueError, match="Not enough players"):
            await engine.start_game()

    @pytest.mark.asyncio
    async def test_night_phase_werewolf_action(self, game_engine: GameEngine):
        """Test werewolf action during night phase."""
        # Start game first
        game_engine.session = GameSession(game_engine.room)

        # Get werewolf players
        werewolves = [p for p in game_engine.session.players if p.role == Role.WEREWOLF]
        if werewolves:
            werewolf = werewolves[0]

            # Mock AI response
            game_engine.ai_manager.send_message.return_value = Mock(
                success=True,
                data={
                    "action": "werewolf_kill",
                    "targetPlayer": "victim-id",
                    "reasoning": "Test reasoning"
                }
            )

            await game_engine.process_night_phase()

            # Check that AI was asked for action
            game_engine.ai_manager.send_message.assert_called()

    @pytest.mark.asyncio
    async def test_night_phase_seer_action(self, game_engine: GameEngine):
        """Test seer action during night phase."""
        # Start game first
        game_engine.session = GameSession(game_engine.room)

        # Get seer player
        seers = [p for p in game_engine.session.players if p.role == Role.SEER]
        if seers:
            seer = seers[0]

            # Mock AI response
            game_engine.ai_manager.send_message.return_value = Mock(
                success=True,
                data={
                    "action": "seer_check",
                    "targetPlayer": "target-id",
                    "result": "werewolf"
                }
            )

            await game_engine.process_night_phase()

            # Check that AI was asked for action
            game_engine.ai_manager.send_message.assert_called()

    @pytest.mark.asyncio
    async def test_day_phase_discussion(self, game_engine: GameEngine):
        """Test day phase discussion."""
        # Start game first
        game_engine.session = GameSession(game_engine.room)
        game_engine.session.transition_to_phase(GamePhase.DAY)

        # Mock AI responses
        game_engine.ai_manager.send_message.return_value = Mock(
            success=True,
            data={
                "speechContent": "I think someone is suspicious",
                "reasoning": "Based on behavior analysis"
            }
        )

        await game_engine.process_day_phase()

        # Check that AI was asked for speeches
        assert game_engine.ai_manager.send_message.call_count > 0

    @pytest.mark.asyncio
    async def test_voting_phase(self, game_engine: GameEngine):
        """Test voting phase."""
        # Start game first
        game_engine.session = GameSession(game_engine.room)
        game_engine.session.transition_to_phase(GamePhase.DAY)

        # Mock AI responses
        game_engine.ai_manager.send_message.return_value = Mock(
            success=True,
            data={
                "targetPlayerId": "target-id",
                "targetPlayerName": "Target Player",
                "reasoning": "Most suspicious behavior"
            }
        )

        await game_engine.process_voting_phase()

        # Check that AI was asked for votes
        assert game_engine.ai_manager.send_message.call_count > 0

    def test_check_victory_werewolves_win(self):
        """Test werewolf victory condition."""
        room = GameRoom.create_room("Creator", max_players=6)
        engine = GameEngine(room, Mock(), Mock())

        # Create scenario where werewolves equal villagers
        players = [
            Player(name="Wolf1", role=Role.WEREWOLF, status=PlayerStatus.ALIVE),
            Player(name="Wolf2", role=Role.WEREWOLF, status=PlayerStatus.ALIVE),
            Player(name="Villager1", role=Role.VILLAGER, status=PlayerStatus.ALIVE),
            Player(name="Villager2", role=Role.VILLAGER, status=PlayerStatus.DEAD),
        ]

        engine.session = GameSession(room)
        engine.session.players = players

        winner = engine.check_victory()
        assert winner.value == "werewolf"

    def test_check_victory_villagers_win(self):
        """Test villager victory condition."""
        room = GameRoom.create_room("Creator", max_players=6)
        engine = GameEngine(room, Mock(), Mock())

        # Create scenario where all werewolves are dead
        players = [
            Player(name="Wolf1", role=Role.WEREWOLF, status=PlayerStatus.DEAD),
            Player(name="Wolf2", role=Role.WEREWOLF, status=PlayerStatus.DEAD),
            Player(name="Villager1", role=Role.VILLAGER, status=PlayerStatus.ALIVE),
            Player(name="Villager2", role=Role.VILLAGER, status=PlayerStatus.ALIVE),
        ]

        engine.session = GameSession(room)
        engine.session.players = players

        winner = engine.check_victory()
        assert winner.value == "villager"

    def test_check_victory_no_winner_yet(self):
        """Test no victory condition yet."""
        room = GameRoom.create_room("Creator", max_players=6)
        engine = GameEngine(room, Mock(), Mock())

        # Create balanced scenario
        players = [
            Player(name="Wolf1", role=Role.WEREWOLF, status=PlayerStatus.ALIVE),
            Player(name="Villager1", role=Role.VILLAGER, status=PlayerStatus.ALIVE),
            Player(name="Villager2", role=Role.VILLAGER, status=PlayerStatus.ALIVE),
            Player(name="Villager3", role=Role.VILLAGER, status=PlayerStatus.ALIVE),
        ]

        engine.session = GameSession(room)
        engine.session.players = players

        winner = engine.check_victory()
        assert winner is None

    @pytest.mark.asyncio
    async def test_end_game(self, game_engine: GameEngine):
        """Test ending game."""
        # Start game first
        game_engine.session = GameSession(game_engine.room)

        # Set up callbacks
        phase_change_callback = AsyncMock()
        player_death_callback = AsyncMock()
        game_end_callback = AsyncMock()

        game_engine.set_phase_change_callback(phase_change_callback)
        game_engine.set_player_death_callback(player_death_callback)
        game_engine.set_game_end_callback(game_end_callback)

        await game_engine.end_game("werewolf", "All villagers eliminated")

        assert game_engine.session.winner.value == "werewolf"
        assert game_engine.session.end_reason == "All villagers eliminated"
        assert game_engine.session.ended_at is not None

        # Check that game end callback was called
        game_end_callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_player_death_hunter(self, game_engine: GameEngine):
        """Test hunter death shooting ability."""
        # Start game first
        game_engine.session = GameSession(game_engine.room)

        # Create hunter who dies
        hunter = Player(name="Hunter", role=Role.HUNTER, status=PlayerStatus.ALIVE)
        victim = Player(name="Victim", role=Role.VILLAGER, status=PlayerStatus.ALIVE)

        game_engine.session.players = [hunter, victim]

        # Mock AI response for hunter shot
        game_engine.ai_manager.send_message.return_value = Mock(
            success=True,
            data={
                "action": "hunter_shoot",
                "targetPlayer": victim.id,
                "reasoning": "Most suspicious"
            }
        )

        await game_engine.process_player_death(hunter, "vote_eliminate")

        # Check that hunter shot was processed
        assert victim.status == PlayerStatus.DEAD

    def test_get_current_state(self, game_engine: GameEngine):
        """Test getting current game state."""
        # Start game first
        game_engine.session = GameSession(game_engine.room)

        state = game_engine.get_current_state()

        assert "session_id" in state
        assert "room_id" in state
        assert "current_phase" in state
        assert "day_count" in state
        assert "players" in state

    def test_get_game_summary(self, game_engine: GameEngine):
        """Test getting game summary."""
        # Start game first
        game_engine.session = GameSession(game_engine.room)

        summary = game_engine.get_game_summary()

        assert "session_id" in summary
        assert "status" in summary
        assert "current_phase" in summary
        assert "day_count" in summary
        assert "players" in summary

    def test_set_callbacks(self, game_engine: GameEngine):
        """Test setting event callbacks."""
        phase_callback = AsyncMock()
        death_callback = AsyncMock()
        end_callback = AsyncMock()

        game_engine.set_phase_change_callback(phase_callback)
        game_engine.set_player_death_callback(death_callback)
        game_engine.set_game_end_callback(end_callback)

        assert game_engine.phase_change_callback == phase_callback
        assert game_engine.player_death_callback == death_callback
        assert game_engine.game_end_callback == end_callback

    @pytest.mark.asyncio
    async def test_phase_transition(self, game_engine: GameEngine):
        """Test phase transition with callbacks."""
        # Start game first
        game_engine.session = GameSession(game_engine.room)

        # Set up callback
        phase_callback = AsyncMock()
        game_engine.set_phase_change_callback(phase_callback)

        # Transition phase
        await game_engine.transition_phase(GamePhase.DAY)

        assert game_engine.session.current_phase == GamePhase.DAY
        phase_callback.assert_called_once_with(GamePhase.NIGHT, GamePhase.DAY)

    @pytest.mark.asyncio
    async def test_ai_agent_interaction(self, game_engine: GameEngine):
        """Test AI agent interaction during game."""
        # Start game first
        game_engine.session = GameSession(game_engine.room)

        # Get a player
        player = game_engine.session.players[0]

        # Mock AI response
        game_engine.ai_manager.send_message.return_value = Mock(
            success=True,
            data={
                "action": "game_action",
                "result": "success"
            }
        )

        # Send message to agent
        response = await game_engine.send_message_to_agent(
            player.id,
            "game_action",
            {"action": "test_action"}
        )

        assert response is not None
        assert response.success is True

    def test_role_ability_validation(self, game_engine: GameEngine):
        """Test role ability validation."""
        # Test seer ability
        seer = Player(name="Seer", role=Role.SEER)
        assert game_engine.can_use_role_ability(seer, "seer_check") is True
        assert game_engine.can_use_role_ability(seer, "invalid_ability") is False

        # Test witch ability
        witch = Player(name="Witch", role=Role.WITCH)
        witch.has_save = True
        witch.has_poison = True
        assert game_engine.can_use_role_ability(witch, "witch_save") is True
        assert game_engine.can_use_role_ability(witch, "witch_poison") is True

        witch.has_save = False
        witch.has_poison = False
        assert game_engine.can_use_role_ability(witch, "witch_save") is False
        assert game_engine.can_use_role_ability(witch, "witch_poison") is False

    @pytest.mark.asyncio
    async def test_timeout_handling(self, game_engine: GameEngine):
        """Test handling of timeouts during phases."""
        # Start game first
        game_engine.session = GameSession(game_engine.room)

        # Mock AI to timeout
        import asyncio
        game_engine.ai_manager.send_message = AsyncMock(
            side_effect=asyncio.TimeoutError("AI response timeout")
        )

        # Should handle timeout gracefully
        await game_engine.process_night_phase()

        # Should not crash
        assert game_engine.session is not None