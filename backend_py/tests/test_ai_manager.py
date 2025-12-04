"""Test AI manager functionality."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from werewolf.services.ai_manager import (
    AIManager, AgentType, AgentConfig, AIMessage, AIResponse,
    WerewolfAgent
)
from werewolf.models.player import Player, Role, PersonalityType, SkillLevel, ResponseTime


class TestAIManager:
    """Test AI Manager."""

    @pytest.fixture
    def ai_manager(self):
        """Create AI manager instance."""
        return AIManager()

    @pytest.fixture
    def sample_player(self):
        """Create sample player."""
        return Player.create_ai_player(
            name="TestPlayer",
            room_id="test-room",
            role=Role.SEER
        )

    def test_initialization(self, ai_manager: AIManager):
        """Test AI manager initialization."""
        assert not ai_manager.is_initialized
        assert len(ai_manager.agents) == 0
        assert len(ai_manager.agent_configs) > 0

    def test_agent_configs_exist(self, ai_manager: AIManager):
        """Test that agent configurations exist for all roles."""
        required_types = [
            AgentType.WEREWOLF,
            AgentType.SEER,
            AgentType.WITCH,
            AgentType.HUNTER,
            AgentType.VILLAGER
        ]

        for agent_type in required_types:
            assert agent_type in ai_manager.agent_configs
            config = ai_manager.agent_configs[agent_type]
            assert isinstance(config, AgentConfig)
            assert config.name is not None
            assert config.system_prompt is not None

    def test_role_to_agent_type_mapping(self, ai_manager: AIManager):
        """Test role to agent type mapping."""
        mappings = {
            Role.WEREWOLF: AgentType.WEREWOLF,
            Role.SEER: AgentType.SEER,
            Role.WITCH: AgentType.WITCH,
            Role.HUNTER: AgentType.HUNTER,
            Role.VILLAGER: AgentType.VILLAGER
        }

        for role, expected_type in mappings.items():
            assert ai_manager._role_to_agent_type(role) == expected_type

    @pytest.mark.asyncio
    async def test_initialize(self, ai_manager: AIManager):
        """Test AI manager initialization."""
        with patch('werewolf.services.ai_manager.AGENTSCOPE_AVAILABLE', True):
            await ai_manager.initialize()
            assert ai_manager.is_initialized

    @pytest.mark.asyncio
    async def test_initialize_without_agentscope(self, ai_manager: AIManager):
        """Test initialization without AgentScope."""
        with patch('werewolf.services.ai_manager.AGENTSCOPE_AVAILABLE', False):
            await ai_manager.initialize()
            assert ai_manager.is_initialized

    @pytest.mark.asyncio
    async def test_create_agent(self, ai_manager: AIManager, sample_player: Player):
        """Test creating AI agent."""
        ai_manager.is_initialized = True

        agent_id = await ai_manager.create_agent(sample_player)

        assert agent_id in ai_manager.agents
        assert agent_id in ai_manager.message_queues

        agent = ai_manager.agents[agent_id]
        assert isinstance(agent, WerewolfAgent)
        assert agent.name == sample_player.name

    @pytest.mark.asyncio
    async def test_create_agent_not_initialized(self, ai_manager: AIManager, sample_player: Player):
        """Test creating agent when manager not initialized."""
        with pytest.raises(RuntimeError, match="AI Manager not initialized"):
            await ai_manager.create_agent(sample_player)

    @pytest.mark.asyncio
    async def test_send_message(self, ai_manager: AIManager, sample_player: Player):
        """Test sending message to agent."""
        ai_manager.is_initialized = True

        # Create agent
        agent_id = await ai_manager.create_agent(sample_player)

        # Create message
        message = AIMessage(
            id="test-message-id",
            type="game_action",
            agent_id=agent_id,
            agent_type="seer_agent",
            timestamp=1234567890,
            content={"action": "seer_check", "targetId": "target-player"}
        )

        # Send message
        response = await ai_manager.send_message(agent_id, message)

        assert isinstance(response, AIResponse)
        assert response.request_id == message.id
        assert response.agent_id == agent_id

    @pytest.mark.asyncio
    async def test_send_message_nonexistent_agent(self, ai_manager: AIManager):
        """Test sending message to non-existent agent."""
        message = AIMessage(
            id="test-message-id",
            type="game_action",
            agent_id="nonexistent-agent",
            agent_type="seer_agent",
            timestamp=1234567890,
            content={}
        )

        with pytest.raises(ValueError, match="Agent not found"):
            await ai_manager.send_message("nonexistent-agent", message)

    def test_calculate_response_delay(self, ai_manager: AIManager):
        """Test response delay calculation."""
        # Test different response times
        delays = []

        for response_time in ResponseTime:
            delay = ai_manager._calculate_response_delay(response_time)
            delays.append(delay)
            assert isinstance(delay, int)
            assert delay > 0

        # Fast should be quicker than slow
        immediate_delay = ai_manager._calculate_response_delay(ResponseTime.IMMEDIATE)
        slow_delay = ai_manager._calculate_response_delay(ResponseTime.SLOW)
        assert immediate_delay < slow_delay

    def test_generate_reasoning(self, ai_manager: AIManager):
        """Test reasoning generation."""
        agent = WerewolfAgent(
            agent_id="test-agent",
            name="Test Agent",
            agent_type=AgentType.SEER,
            personality=PersonalityType.ANALYTICAL_CAUTIOUS_LEADERSHIP,
            skill_level=SkillLevel.INTERMEDIATE,
            response_time=ResponseTime.NORMAL
        )

        action_types = [
            "werewolf_kill",
            "seer_check",
            "witch_save",
            "witch_poison",
            "hunter_shoot",
            "vote_eliminate"
        ]

        for action_type in action_types:
            reasoning = ai_manager._generate_reasoning(agent, action_type)
            assert isinstance(reasoning, str)
            assert len(reasoning) > 0

    def test_calculate_confidence(self, ai_manager: AIManager):
        """Test confidence calculation."""
        confidences = []

        for skill_level in SkillLevel:
            confidence = ai_manager._calculate_confidence(skill_level)
            confidences.append(confidence)
            assert 0.5 <= confidence <= 1.0

        # Expert should have higher confidence than beginner
        beginner_confidence = ai_manager._calculate_confidence(SkillLevel.BEGINNER)
        expert_confidence = ai_manager._calculate_confidence(SkillLevel.EXPERT)
        assert expert_confidence > beginner_confidence

    def test_get_agent_info(self, ai_manager: AIManager):
        """Test getting agent information."""
        ai_manager.is_initialized = True

        # Create a sample agent directly
        agent = WerewolfAgent(
            agent_id="test-agent",
            name="Test Agent",
            agent_type=AgentType.SEER,
            personality=PersonalityType.ANALYTICAL_CAUTIOUS_LEADERSHIP,
            skill_level=SkillLevel.INTERMEDIATE,
            response_time=ResponseTime.NORMAL
        )

        ai_manager.agents["test-agent"] = agent

        agent_info = ai_manager.get_agent_info("test-agent")
        assert agent_info is not None
        assert agent_info["id"] == "test-agent"
        assert agent_info["name"] == "Test Agent"
        assert agent_info["agent_type"] == "seer_agent"

    def test_get_agent_info_nonexistent(self, ai_manager: AIManager):
        """Test getting info for non-existent agent."""
        agent_info = ai_manager.get_agent_info("nonexistent-agent")
        assert agent_info is None

    def test_get_all_agents(self, ai_manager: AIManager):
        """Test getting all agents."""
        ai_manager.is_initialized = True

        # Create sample agents
        for i in range(3):
            agent = WerewolfAgent(
                agent_id=f"agent-{i}",
                name=f"Agent {i}",
                agent_type=AgentType.VILLAGER,
                personality=PersonalityType.LOGICAL_ANALYTICAL_CAUTIOUS,
                skill_level=SkillLevel.INTERMEDIATE,
                response_time=ResponseTime.NORMAL
            )
            ai_manager.agents[f"agent-{i}"] = agent

        all_agents = ai_manager.get_all_agents()
        assert len(all_agents) == 3

        for agent_info in all_agents:
            assert "id" in agent_info
            assert "name" in agent_info

    def test_remove_agent(self, ai_manager: AIManager):
        """Test removing agent."""
        ai_manager.is_initialized = True

        # Create sample agent
        agent = WerewolfAgent(
            agent_id="test-agent",
            name="Test Agent",
            agent_type=AgentType.VILLAGER,
            personality=PersonalityType.LOGICAL_ANALYTICAL_CAUTIOUS,
            skill_level=SkillLevel.INTERMEDIATE,
            response_time=ResponseTime.NORMAL
        )

        ai_manager.agents["test-agent"] = agent
        ai_manager.message_queues["test-agent"] = []

        # Remove agent
        result = ai_manager.remove_agent("test-agent")
        assert result is True
        assert "test-agent" not in ai_manager.agents
        assert "test-agent" not in ai_manager.message_queues

        # Try to remove again
        result = ai_manager.remove_agent("test-agent")
        assert result is False

    def test_update_agent_status(self, ai_manager: AIManager):
        """Test updating agent status."""
        ai_manager.is_initialized = True

        # Create sample agent
        agent = WerewolfAgent(
            agent_id="test-agent",
            name="Test Agent",
            agent_type=AgentType.VILLAGER,
            personality=PersonalityType.LOGICAL_ANALYTICAL_CAUTIOUS,
            skill_level=SkillLevel.INTERMEDIATE,
            response_time=ResponseTime.NORMAL
        )

        ai_manager.agents["test-agent"] = agent

        # Update agent status
        status_updates = {
            "name": "Updated Agent",
            "skill_level": SkillLevel.EXPERT
        }

        ai_manager.update_agent_status("test-agent", status_updates)

        updated_agent = ai_manager.agents["test-agent"]
        assert updated_agent.name == "Updated Agent"
        assert updated_agent.skill_level == SkillLevel.EXPERT

    @pytest.mark.asyncio
    async def test_health_check(self, ai_manager: AIManager):
        """Test health check."""
        health = await ai_manager.health_check()
        assert "status" in health
        assert "agent_count" in health
        assert "agentscope_available" in health
        assert "last_check" in health

    @pytest.mark.asyncio
    async def test_shutdown(self, ai_manager: AIManager):
        """Test shutdown."""
        ai_manager.is_initialized = True

        # Create some agents
        for i in range(3):
            agent = WerewolfAgent(
                agent_id=f"agent-{i}",
                name=f"Agent {i}",
                agent_type=AgentType.VILLAGER,
                personality=PersonalityType.LOGICAL_ANALYTICAL_CAUTIOUS,
                skill_level=SkillLevel.INTERMEDIATE,
                response_time=ResponseTime.NORMAL
            )
            ai_manager.agents[f"agent-{i}"] = agent
            ai_manager.message_queues[f"agent-{i}"] = []

        assert len(ai_manager.agents) == 3
        assert len(ai_manager.message_queues) == 3

        await ai_manager.shutdown()

        assert len(ai_manager.agents) == 0
        assert len(ai_manager.message_queues) == 0


class TestWerewolfAgent:
    """Test WerewolfAgent."""

    def test_agent_creation(self):
        """Test agent creation."""
        agent = WerewolfAgent(
            agent_id="test-agent",
            name="Test Agent",
            agent_type=AgentType.SEER,
            personality=PersonalityType.ANALYTICAL_CAUTIOUS_LEADERSHIP,
            skill_level=SkillLevel.INTERMEDIATE,
            response_time=ResponseTime.NORMAL
        )

        assert agent.agent_id == "test-agent"
        assert agent.name == "Test Agent"
        assert agent.agent_type == AgentType.SEER
        assert agent.personality == PersonalityType.ANALYTICAL_CAUTIOUS_LEADERSHIP
        assert agent.skill_level == SkillLevel.INTERMEDIATE
        assert agent.response_time == ResponseTime.NORMAL

    def test_update_last_active(self):
        """Test updating last active timestamp."""
        agent = WerewolfAgent(
            agent_id="test-agent",
            name="Test Agent",
            agent_type=AgentType.VILLAGER,
            personality=PersonalityType.LOGICAL_ANALYTICAL_CAUTIOUS,
            skill_level=SkillLevel.INTERMEDIATE,
            response_time=ResponseTime.NORMAL
        )

        original_time = agent.last_active
        agent.update_last_active()
        assert agent.last_active > original_time

    def test_to_dict(self):
        """Test agent serialization."""
        agent = WerewolfAgent(
            agent_id="test-agent",
            name="Test Agent",
            agent_type=AgentType.SEER,
            personality=PersonalityType.ANALYTICAL_CAUTIOUS_LEADERSHIP,
            skill_level=SkillLevel.INTERMEDIATE,
            response_time=ResponseTime.NORMAL,
            language="zh"
        )

        agent_dict = agent.to_dict()
        assert agent_dict["agent_id"] == "test-agent"
        assert agent_dict["name"] == "Test Agent"
        assert agent_dict["agent_type"] == "seer_agent"
        assert agent_dict["personality"] == "analytical_cautious_leadership"
        assert agent_dict["skill_level"] == "intermediate"
        assert agent_dict["response_time"] == "normal"
        assert agent_dict["language"] == "zh"