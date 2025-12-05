"""Test AI agents functionality."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from src.werewolf.agents.agent_factory import AgentFactory
from src.werewolf.agents.werewolf_agent import WerewolfReactAgent, SeerReactAgent
from src.werewolf.agents.base_agent import BaseGameAgent, GameState, AgentAction
from src.werewolf.models.player import Player, Role, PersonalityType, SkillLevel
from src.werewolf.services.ai_game_engine import AIGameEngine
from src.werewolf.services.event_service import EventService


class TestAgentFactory:
    """Test AgentFactory."""

    def test_create_werewolf_agent(self):
        """Test creating werewolf agent."""
        player = Player.create_ai_player(
            name="TestWerewolf",
            room_id="test-room",
            role=Role.WEREWOLF,
            position=1
        )

        agent = AgentFactory.create_agent(player)

        assert agent is not None
        assert agent.player_id == player.id
        assert agent.role == Role.WEREWOLF
        assert isinstance(agent, WerewolfReactAgent)

    def test_create_seer_agent(self):
        """Test creating seer agent."""
        player = Player.create_ai_player(
            name="TestSeer",
            room_id="test-room",
            role=Role.SEER,
            position=2
        )

        agent = AgentFactory.create_agent(player)

        assert agent is not None
        assert agent.role == Role.SEER
        assert isinstance(agent, SeerReactAgent)

    def test_get_agent_info(self):
        """Test getting agent information."""
        info = AgentFactory.get_agent_info(Role.SEER)

        assert info["role"] == "seer"
        assert "agent_class" in info
        assert "capabilities" in info
        assert "recommended_personality" in info

    def test_create_all_agents(self):
        """Test creating agents for all players."""
        players = [
            Player(name="Wolf1", role=Role.WEREWOLF),
            Player(name="Seer", role=Role.SEER),
            Player(name="Villager1", role=Role.VILLAGER),
            Player(name="Villager2", role=Role.VILLAGER),
        ]

        agent_data = AgentFactory.create_all_agents(players)

        assert "agents" in agent_data
        assert "team_info" in agent_data
        assert len(agent_data["agents"]) == len(players)
        assert len(agent_data["team_info"]["werewolves"]) == 1
        assert len(agent_data["team_info"]["good_team"]) == 3


class TestBaseGameAgent:
    """Test BaseGameAgent."""

    @pytest.fixture
    def sample_agent(self):
        """Create sample agent."""
        player = Player.create_ai_player(
            name="TestAgent",
            room_id="test-room",
            role=Role.VILLAGER,
            position=1
        )

        with patch('werewolf.agents.base_agent.AGENTSCOPE_AVAILABLE', False):
            # Mock agent creation without actual AgentScope
            return BaseGameAgent(
                player_id=player.id,
                name=player.name,
                role=player.role,
                personality=player.ai_config.personality,
                skill_level=player.ai_config.skill_level
            )

    def test_agent_initialization(self, sample_agent):
        """Test agent initialization."""
        assert sample_agent.player_id is not None
        assert sample_agent.name == "TestAgent"
        assert sample_agent.role == Role.VILLAGER
        assert not sample_agent.is_initialized  # Should be false without AgentScope

    def test_temperature_calculation(self, sample_agent):
        """Test temperature calculation based on skill level."""
        temp = sample_agent._get_temperature()
        assert 0.1 <= temp <= 1.0

    def test_fallback_decision(self, sample_agent):
        """Test fallback decision making."""
        game_state = GameState(
            phase="day",
            day_count=1,
            alive_players=[],
            my_role="villager"
        )

        action = sample_agent._fallback_decision(game_state, ["speech"])

        assert action.action_type == "speech"
        assert action.confidence < 0.5

    @pytest.mark.asyncio
    async def test_make_decision_without_agentscope(self, sample_agent):
        """Test decision making without AgentScope."""
        game_state = GameState(
            phase="day",
            day_count=1,
            alive_players=[],
            my_role="villager"
        )

        action = await sample_agent.make_decision(game_state, ["speech"])

        assert action is not None
        assert action.action_type == "speech"

    def test_update_player_notes(self, sample_agent):
        """Test updating player notes."""
        sample_agent.update_player_notes("player123", "可疑行为")
        assert sample_agent.player_notes["player123"] == "可疑行为"

    def test_suspicion_update(self, sample_agent):
        """Test suspicion level updates."""
        game_state = GameState(
            phase="day",
            day_count=1,
            alive_players=[
                {"id": "player123", "name": "TestPlayer", "position": 1}
            ],
            recent_events=[
                {"type": "player_speech", "actor_id": "player123", "content": "我认为有狼人"}
            ]
        )

        # Should update suspicion based on speech
        asyncio.run(sample_agent._update_suspicion("player123", game_state))
        assert "player123" in sample_agent.suspicions


class TestWerewolfReactAgent:
    """Test WerewolfReactAgent."""

    @pytest.fixture
    def werewolf_agent(self):
        """Create werewolf agent."""
        player = Player.create_ai_player(
            name="TestWerewolf",
            room_id="test-room",
            role=Role.WEREWOLF,
            position=1
        )

        with patch('werewolf.agents.base_agent.AGENTSCOPE_AVAILABLE', False):
            return WerewolfReactAgent(
                player_id=player.id,
                name=player.name,
                role=player.role,
                personality=player.ai_config.personality,
                skill_level=player.ai_config.skill_level
            )

    def test_werewolf_system_prompt(self, werewolf_agent):
        """Test werewolf system prompt."""
        prompt = werewolf_agent._get_system_prompt()
        assert "狼人" in prompt
        assert "击杀" in prompt
        assert "隐藏身份" in prompt

    @pytest.mark.asyncio
    async def test_werewolf_decision_enhancement(self, werewolf_agent):
        """Test werewolf decision enhancement."""
        game_state = GameState(
            phase="night",
            day_count=1,
            alive_players=[
                {"id": "target1", "name": "Target1", "position": 2}
            ],
            my_role="werewolf"
        )

        action = AgentAction(
            action_type="werewolf_kill",
            target="target1",
            content="击杀目标"
        )

        enhanced_action = await werewolf_agent._enhance_kill_decision(action, game_state)

        assert enhanced_action.action_type == "werewolf_kill"
        assert "kill_priority" in enhanced_action.metadata


class TestAIGameEngine:
    """Test AIGameEngine."""

    @pytest.fixture
    def sample_room(self):
        """Create sample game room."""
        from werewolf.models.room import GameRoom

        room = GameRoom.create_room(
            creator_name="Creator",
            room_name="Test Room",
            max_players=6
        )

        # Add players
        players = [
            Player(name="Wolf1", role=Role.WEREWOLF),
            Player(name="Seer", role=Role.SEER),
            Player(name="Witch", role=Role.WITCH),
            Player(name="Hunter", role=Role.HUNTER),
            Player(name="Villager1", role=Role.VILLAGER),
            Player(name="Villager2", role=Role.VILLAGER),
        ]

        for player in players:
            room.add_player(player)

        return room

    @pytest.fixture
    def ai_game_engine(self, sample_room):
        """Create AI game engine."""
        event_service = Mock(spec=EventService)
        event_service.record_event = AsyncMock()

        with patch('werewolf.agents.base_agent.AGENTSCOPE_AVAILABLE', False):
            return AIGameEngine(
                room=sample_room,
                event_service=event_service,
                model_config={"model_name": "gpt-4"}
            )

    @pytest.mark.asyncio
    async def test_game_initialization(self, ai_game_engine):
        """Test game initialization."""
        await ai_game_engine.initialize_game()

        assert ai_game_engine.session is not None
        assert len(ai_game_engine.agents) == len(ai_game_engine.room.players)
        assert len(ai_game_engine.team_info["werewolves"]) == 1
        assert len(ai_game_engine.team_info["good_team"]) == 5

    @pytest.mark.asyncio
    async def test_start_game(self, ai_game_engine):
        """Test starting game."""
        with patch.object(ai_game_engine, '_start_night_phase') as mock_night:
            session = await ai_game_engine.start_game()

            assert session is not None
            assert ai_game_engine.is_running is True
            mock_night.assert_called_once()

    def test_get_night_agents(self, ai_game_engine):
        """Test getting night agents."""
        night_agents = ai_game_engine._get_night_agents()

        assert len(night_agents) == 3  # Werewolf, Seer, Witch
        roles = [agent["role"] for agent in night_agents]
        assert Role.WEREWOLF in roles
        assert Role.SEER in roles
        assert Role.WITCH in roles

    def test_night_actions_for_role(self, ai_game_engine):
        """Test getting night actions for roles."""
        werewolf_actions = ai_game_engine._get_night_actions_for_role(Role.WEREWOLF)
        seer_actions = ai_game_engine._get_night_actions_for_role(Role.SEER)
        villager_actions = ai_game_engine._get_night_actions_for_role(Role.VILLAGER)

        assert "werewolf_kill" in werewolf_actions
        assert "seer_check" in seer_actions
        assert "wait" in villager_actions

    @pytest.mark.asyncio
    async def test_create_game_state(self, ai_game_engine):
        """Test creating game state for agent."""
        await ai_game_engine.initialize_game()

        # Get a werewolf agent
        werewolf_agent = list(ai_game_engine.agents.values())[0]
        game_state = await ai_game_engine._create_game_state(werewolf_agent.player_id)

        assert game_state.phase in ["night", "day", "voting"]
        assert len(game_state.alive_players) == 6
        assert game_state.my_role is not None

    @pytest.mark.asyncio
    async def test_is_werewolf(self, ai_game_engine):
        """Test werewolf identification."""
        await ai_game_engine.initialize_game()

        # Find werewolf agent
        werewolf_agent = None
        for agent in ai_game_engine.agents.values():
            if agent.role == Role.WEREWOLF:
                werewolf_agent = agent
                break

        assert werewolf_agent is not None
        assert ai_game_engine._is_werewolf(werewolf_agent.player_id) is True

        # Test non-werewolf
        villager_agent = None
        for agent in ai_game_engine.agents.values():
            if agent.role == Role.VILLAGER:
                villager_agent = agent
                break

        if villager_agent:
            assert ai_game_engine._is_werewolf(villager_agent.player_id) is False

    @pytest.mark.asyncio
    async def test_victory_check(self, ai_game_engine):
        """Test victory condition checking."""
        await ai_game_engine.initialize_game()

        # Test ongoing game (no victory)
        result = await ai_game_engine._check_game_end()
        assert result is False

        # Test werewolf victory
        for player in ai_game_engine.room.players:
            if player.role != Role.WEREWOLF:
                player.status = PlayerStatus.DEATH

        result = await ai_game_engine._check_game_end()
        assert result is True
        assert ai_game_engine.session.winner.value == "werewolf"

    def test_game_summary(self, ai_game_engine):
        """Test getting game summary."""
        summary = ai_game_engine.get_game_summary()

        assert summary["status"] == "not_started"
        assert "session_id" not in summary

        # After initialization
        asyncio.run(ai_game_engine.initialize_game())
        summary = ai_game_engine.get_game_summary()

        assert "session_id" in summary
        assert "agent_info" in summary
        assert len(summary["agent_info"]) == len(ai_game_engine.agents)

    @pytest.mark.asyncio
    async def test_phase_transition(self, ai_game_engine):
        """Test phase transition."""
        await ai_game_engine.initialize_game()

        old_phase = ai_game_engine.session.current_phase
        await ai_game_engine._transition_to_phase(GamePhase.DAY)

        assert ai_game_engine.session.current_phase == GamePhase.DAY
        assert ai_game_engine.session.current_phase != old_phase

    def test_callback_setup(self, ai_game_engine):
        """Test setting up callbacks."""
        phase_callback = Mock()
        death_callback = Mock()
        end_callback = Mock()

        ai_game_engine.set_phase_change_callback(phase_callback)
        ai_game_engine.set_player_death_callback(death_callback)
        ai_game_engine.set_game_end_callback(end_callback)

        assert ai_game_engine.on_phase_change == phase_callback
        assert ai_game_engine.on_player_death == death_callback
        assert ai_game_engine.on_game_end == end_callback