"""AI manager for AgentScope integration."""

import asyncio
import json
import random
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import uuid

try:
    from agentscope import Agent, Msg, UserRequest
    from agentscope.message import Message
    from agentscope.models import OpenAIWrapper
    AGENTSCOPE_AVAILABLE = True
except ImportError:
    AGENTSCOPE_AVAILABLE = False
    Agent = None
    Msg = None
    UserRequest = None
    Message = None

from loguru import logger
from ..models.player import Player, Role, PersonalityType, SkillLevel, ResponseTime, StrategyType


class AgentType(str, Enum):
    """Agent types for different roles."""
    WEREWOLF = "werewolf_agent"
    SEER = "seer_agent"
    WITCH = "witch_agent"
    HUNTER = "hunter_agent"
    VILLAGER = "villager_agent"


@dataclass
class AgentConfig:
    """Agent configuration."""
    agent_type: AgentType
    name: str
    description: str
    personality: str
    system_prompt: str
    response_format: str = "json"
    capabilities: List[str] = None


@dataclass
class AIMessage:
    """AI message structure."""
    id: str
    type: str
    agent_id: str
    agent_type: str
    timestamp: float
    content: Any
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AIResponse:
    """AI response structure."""
    id: str
    request_id: str
    agent_id: str
    agent_type: str
    timestamp: float
    success: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, str]] = None
    processing_time: float = 0.0


class AIManager:
    """Manager for AI agents using AgentScope."""

    def __init__(self):
        self.agents: Dict[str, "WerewolfAgent"] = {}
        self.agent_configs: Dict[AgentType, AgentConfig] = {}
        self.message_queues: Dict[str, List[AIMessage]] = {}
        self.is_initialized = False

        # Response time configurations (in milliseconds)
        self.response_times = {
            ResponseTime.IMMEDIATE: (500, 2000),
            ResponseTime.FAST: (2000, 5000),
            ResponseTime.NORMAL: (5000, 10000),
            ResponseTime.SLOW: (10000, 20000)
        }

        # Initialize agent configurations
        self._initialize_agent_configs()

    def _initialize_agent_configs(self) -> None:
        """Initialize configurations for different agent types."""
        self.agent_configs = {
            AgentType.WEREWOLF: AgentConfig(
                agent_type=AgentType.WEREWOLF,
                name="狼人AI代理",
                description="狼人杀游戏中的狼人角色AI",
                personality="aggressive_deceptive_cooperative",
                system_prompt=self._get_werewolf_prompt(),
                capabilities=["reasoning", "deception", "coordination", "adaptation"]
            ),

            AgentType.SEER: AgentConfig(
                agent_type=AgentType.SEER,
                name="预言家AI代理",
                description="狼人杀游戏中的预言家角色AI",
                personality="analytical_cautious_leadership",
                system_prompt=self._get_seer_prompt(),
                capabilities=["reasoning", "analysis", "leadership", "verification"]
            ),

            AgentType.WITCH: AgentConfig(
                agent_type=AgentType.WITCH,
                name="女巫AI代理",
                description="狼人杀游戏中的女巫角色AI",
                personality="analytical_balanced_cautious",
                system_prompt=self._get_witch_prompt(),
                capabilities=["analysis", "strategy", "decision_making", "adaptation"]
            ),

            AgentType.HUNTER: AgentConfig(
                agent_type=AgentType.HUNTER,
                name="猎人AI代理",
                description="狼人杀游戏中的猎人角色AI",
                personality="aggressive_just_reactive",
                system_prompt=self._get_hunter_prompt(),
                capabilities=["reasoning", "justice", "reactive", "adaptation"]
            ),

            AgentType.VILLAGER: AgentConfig(
                agent_type=AgentType.VILLAGER,
                name="平民AI代理",
                description="狼人杀游戏中的平民角色AI",
                personality="logical_analytical_cautious",
                system_prompt=self._get_villager_prompt(),
                capabilities=["reasoning", "analysis", "observation", "adaptation"]
            )
        }

    def _get_werewolf_prompt(self) -> str:
        """Get werewolf agent system prompt."""
        return """你是一个狼人杀游戏中的狼人玩家。你的目标是隐藏身份，同时配合其他狼人消灭好人。

游戏规则：
- 狼人需要暗中配合，夜晚共同选择击杀目标
- 白天要伪装成好人，误导其他玩家
- 观察预言家、女巫、猎人的行为
- 在关键时刻保护狼人队友

性格特点：
- 具有攻击性，善于引导讨论
- 擅长欺骗和伪装
- 与狼人团队合作
- 根据局势调整策略

请始终以狼人的身份进行思考和发言。你必须隐藏你的身份，同时寻找机会消灭好人阵营。"""

    def _get_seer_prompt(self) -> str:
        """Get seer agent system prompt."""
        return """你是一个狼人杀游戏中的预言家。你的目标是通过查验身份找出狼人，并引导好人投票。

游戏规则：
- 每晚可以查验一名玩家的真实身份
- 根据查验结果在白天引导讨论
- 合理使用身份信息，保护自己不被怀疑
- 与女巫、猎人等神职配合

性格特点：
- 善于分析和推理
- 谨慎但有领导力
- 注重证据和逻辑
- 保护好人阵营

请始终以预言家的身份进行思考和发言。你的查验结果是准确的，但要注意保护自己的安全。"""

    def _get_witch_prompt(self) -> str:
        """Get witch agent system prompt."""
        return """你是一个狼人杀游戏中的女巫。你拥有解药和毒药各一瓶，需要合理使用。

游戏规则：
- 每晚知晓狼人的击杀目标
- 可以选择使用解药救人，或毒药杀人
- 解药和毒药整场游戏只能各用一次
- 不能在同一晚同时使用解药和毒药

性格特点：
- 善于分析局势
- 保持平衡和谨慎
- 根据信息做出最优决策
- 注重长远战略

请始终以女巫的身份进行思考和发言。你的决策会影响游戏走向，要权衡利弊。"""

    def _get_hunter_prompt(self) -> str:
        """Get hunter agent system prompt."""
        return """你是一个狼人杀游戏中的猎人。你在死亡时可以开枪带走一名玩家。

游戏规则：
- 被投票出局或被狼人杀死时可以开枪
- 被女巫毒死时不能开枪
- 开枪选择要基于对游戏的判断
- 为好人阵营做最后贡献

性格特点：
- 具有攻击性和正义感
- 反应迅速，善于判断
- 注重公平和正义
- 在关键时刻发挥作用

请始终以猎人的身份进行思考和发言。你的开枪机会很珍贵，要确保打中最可疑的目标。"""

    def _get_villager_prompt(self) -> str:
        """Get villager agent system prompt."""
        return """你是一个狼人杀游戏中的平民。你的目标是通过观察和推理找出狼人。

游戏规则：
- 白天参与讨论，分析发言
- 投票放逐可疑玩家
- 没有特殊能力，依靠逻辑推理
- 保护神职玩家，找出狼人

性格特点：
- 善于逻辑分析
- 谨慎但有判断力
- 注重证据和推理
- 与好人阵营合作

请始终以平民的身份进行思考和发言。虽然你没有什么特殊能力，但你的观察和推理对好人阵营很重要。"""

    async def initialize(self) -> None:
        """Initialize AI manager."""
        if not AGENTSCOPE_AVAILABLE:
            logger.warning("AgentScope not available, using mock AI implementation")
            self.is_initialized = True
            return

        try:
            # Initialize AgentScope connection
            logger.info("Initializing AgentScope connection")
            self.is_initialized = True
            logger.info("AI Manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI Manager: {e}")
            raise

    async def create_agent(
        self,
        player: Player,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create AI agent for player."""
        if not self.is_initialized:
            raise RuntimeError("AI Manager not initialized")

        agent_id = f"agent-{player.id}"
        agent_type = self._role_to_agent_type(player.role)

        if AGENTSCOPE_AVAILABLE:
            # Create real AgentScope agent
            agent = await self._create_agentscope_agent(
                agent_id,
                player.name,
                agent_type,
                player.ai_config
            )
        else:
            # Create mock agent for testing
            agent = WerewolfAgent(
                agent_id=agent_id,
                name=f"{player.name} ({player.role})",
                agent_type=agent_type,
                personality=player.ai_config.personality,
                skill_level=player.ai_config.skill_level,
                response_time=player.ai_config.response_time,
                language=player.ai_config.language
            )

        self.agents[agent_id] = agent
        self.message_queues[agent_id] = []

        logger.info(f"Created AI agent {agent_id} for player {player.name} as {player.role}")
        return agent_id

    def _role_to_agent_type(self, role: Role) -> AgentType:
        """Convert role to agent type."""
        role_mapping = {
            Role.WEREWOLF: AgentType.WEREWOLF,
            Role.SEER: AgentType.SEER,
            Role.WITCH: AgentType.WITCH,
            Role.HUNTER: AgentType.HUNTER,
            Role.VILLAGER: AgentType.VILLAGER
        }

        return role_mapping.get(role, AgentType.VILLAGER)

    async def _create_agentscope_agent(
        self,
        agent_id: str,
        name: str,
        agent_type: AgentType,
        ai_config: Any
    ) -> "WerewolfAgent":
        """Create AgentScope agent."""
        config = self.agent_configs[agent_type]

        # Create AgentScope agent
        # This is a simplified implementation
        # In actual implementation, you would use AgentScope's agent creation APIs
        agent = WerewolfAgent(
            agent_id=agent_id,
            name=name,
            agent_type=agent_type,
            personality=config.personality,
            skill_level=ai_config.skill_level,
            response_time=ai_config.response_time,
            language=ai_config.language
        )

        return agent

    async def send_message(
        self,
        agent_id: str,
        message: AIMessage
    ) -> AIResponse:
        """Send message to agent and get response."""
        if agent_id not in self.agents:
            raise ValueError(f"Agent not found: {agent_id}")

        agent = self.agents[agent_id]
        start_time = time.time()

        try:
            # Simulate processing delay
            delay = self._calculate_response_delay(agent.response_time)
            await asyncio.sleep(delay / 1000)

            # Process message and get response
            response_data = await self._process_message(agent, message)

            processing_time = (time.time() - start_time) * 1000

            response = AIResponse(
                id=str(uuid.uuid4()),
                request_id=message.id,
                agent_id=agent_id,
                agent_type=agent.agent_type,
                timestamp=time.time(),
                success=True,
                data=response_data,
                processing_time=processing_time
            )

            logger.debug(f"Agent {agent_id} responded in {processing_time:.2f}ms")
            return response

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000

            logger.error(f"Error processing message for agent {agent_id}: {e}")

            return AIResponse(
                id=str(uuid.uuid4()),
                request_id=message.id,
                agent_id=agent_id,
                agent_type=agent.agent_type,
                timestamp=time.time(),
                success=False,
                error={
                    "code": "PROCESSING_ERROR",
                    "message": str(e)
                },
                processing_time=processing_time
            )

    async def _process_message(self, agent: "WerewolfAgent", message: AIMessage) -> Any:
        """Process message and generate response."""
        message_type = message.type
        content = message.content

        if AGENTSCOPE_AVAILABLE:
            # Use real AgentScope processing
            return await self._agentscope_process_message(agent, message)
        else:
            # Use mock processing
            return await self._mock_process_message(agent, message)

    async def _agentscope_process_message(self, agent: "WerewolfAgent", message: AIMessage) -> Any:
        """Process message using AgentScope."""
        # This would integrate with actual AgentScope APIs
        # For now, return a mock response
        return {
            "action": "processed",
            "reasoning": f"Processed {message_type} as {agent.agent_type}",
            "confidence": 0.8
        }

    async def _mock_process_message(self, agent: "WerewolfAgent", message: AIMessage) -> Any:
        """Mock message processing for testing."""
        message_type = message.type
        content = message.content

        # Generate mock responses based on message type
        if message_type == "game_action":
            action = content.get("action", "unknown")
            return {
                "action": action,
                "result": "success",
                "target": content.get("targetId"),
                "reasoning": self._generate_reasoning(agent, action),
                "confidence": self._calculate_confidence(agent.skill_level)
            }

        elif message_type == "player_speech":
            speech_content = content.get("content", "")
            return {
                "speechContent": speech_content,
                "reasoning": "基于当前局势分析",
                "tone": "neutral",
                "confidence": self._calculate_confidence(agent.skill_level),
                "characterCount": len(speech_content)
            }

        elif message_type == "vote_decision":
            target_id = content.get("targetId")
            target_name = content.get("targetName", "Unknown")
            return {
                "targetPlayerId": target_id,
                "targetPlayerName": target_name,
                "reasoning": f"基于分析，我认为{target_name}最可疑",
                "confidence": self._calculate_confidence(agent.skill_level),
                "alternatives": self._generate_vote_alternatives(target_id)
            }

        elif message_type == "role_action":
            action = content.get("action", "unknown")
            return {
                "action": action,
                "targetPlayer": content.get("targetPlayer"),
                "reasoning": self._generate_role_action_reasoning(agent, action),
                "priority": 5,
                "riskAssessment": 0.5,
                "success": random.random() > 0.1
            }

        else:
            return {
                "message": f"Processed {message_type}",
                "agent": agent.name
            }

    def _calculate_response_delay(self, response_time: ResponseTime) -> int:
        """Calculate response delay in milliseconds."""
        min_time, max_time = self.response_times.get(response_time, (5000, 10000))
        return random.randint(min_time, max_time)

    def _generate_reasoning(self, agent: "WerewolfAgent", action_type: str) -> str:
        """Generate reasoning for action."""
        reasoning_map = {
            "werewolf_kill": "基于当前局势，我认为击杀目标是最优选择",
            "seer_check": "根据玩家行为分析，我需要查验此人来获取更多信息",
            "witch_save": "考虑到游戏平衡，救活这个玩家对好人阵营更有利",
            "witch_poison": "根据我的判断，这个玩家很可能是狼人，应该毒死",
            "hunter_shoot": "基于我的观察，这个玩家是最可疑的目标",
            "vote_eliminate": "通过分析所有发言，我认为应该投票给这个玩家"
        }

        return reasoning_map.get(action_type, "基于当前游戏状态和我的角色分析")

    def _generate_role_action_reasoning(self, agent: "WerewolfAgent", action: str) -> str:
        """Generate reasoning for role action."""
        reasoning_map = {
            "seer_check": "查验这个玩家可以获得关键的阵营信息",
            "witch_save": "救活这个玩家可以维持人数优势",
            "witch_poison": "毒死这个玩家可以减少威胁",
            "hunter_shoot": "带走这个可疑玩家可以为好人阵营做贡献"
        }

        return reasoning_map.get(action, "基于我的角色能力和当前局势判断")

    def _calculate_confidence(self, skill_level: SkillLevel) -> float:
        """Calculate confidence level based on skill."""
        confidence_map = {
            SkillLevel.BEGINNER: 0.6,
            SkillLevel.INTERMEDIATE: 0.75,
            SkillLevel.ADVANCED: 0.85,
            SkillLevel.EXPERT: 0.95
        }

        base_confidence = confidence_map.get(skill_level, 0.75)
        # Add some randomness
        return max(0.5, min(1.0, base_confidence + (random.random() - 0.5) * 0.2))

    def _generate_vote_alternatives(self, excluded_id: str) -> List[Dict[str, Any]]:
        """Generate vote alternatives."""
        return [
            {"playerId": "alt-1", "playerName": "Alternative Player 1", "score": 0.7},
            {"playerId": "alt-2", "playerName": "Alternative Player 2", "score": 0.5}
        ]

    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent information."""
        agent = self.agents.get(agent_id)
        if not agent:
            return None

        return {
            "id": agent.agent_id,
            "name": agent.name,
            "agent_type": agent.agent_type,
            "personality": agent.personality,
            "skill_level": agent.skill_level,
            "response_time": agent.response_time,
            "language": agent.language,
            "created_at": time.time()
        }

    def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get all agents information."""
        return [self.get_agent_info(agent_id) for agent_id in self.agents]

    def remove_agent(self, agent_id: str) -> bool:
        """Remove agent."""
        removed = agent_id in self.agents
        if removed:
            del self.agents[agent_id]
            if agent_id in self.message_queues:
                del self.message_queues[agent_id]
            logger.info(f"Removed agent: {agent_id}")
        return removed

    def update_agent_status(self, agent_id: str, status: Dict[str, Any]) -> None:
        """Update agent status."""
        agent = self.agents.get(agent_id)
        if agent:
            for key, value in status.items():
                if hasattr(agent, key):
                    setattr(agent, key, value)
            logger.debug(f"Updated agent {agent_id} status: {status}")

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        return {
            "status": "healthy",
            "agent_count": len(self.agents),
            "agentscope_available": AGENTSCOPE_AVAILABLE,
            "last_check": time.time()
        }

    async def shutdown(self) -> None:
        """Shutdown AI manager."""
        logger.info("Shutting down AI Manager")

        # Clear all agents
        self.agents.clear()
        self.message_queues.clear()

        logger.info("AI Manager shutdown complete")


class WerewolfAgent:
    """Werewolf AI agent."""

    def __init__(
        self,
        agent_id: str,
        name: str,
        agent_type: AgentType,
        personality: PersonalityType,
        skill_level: SkillLevel,
        response_time: ResponseTime,
        language: str = "zh"
    ):
        self.agent_id = agent_id
        self.name = name
        self.agent_type = agent_type
        self.personality = personality
        self.skill_level = skill_level
        self.response_time = response_time
        self.language = language
        self.created_at = time.time()
        self.last_active = time.time()

    def update_last_active(self) -> None:
        """Update last active timestamp."""
        self.last_active = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "agent_type": self.agent_type.value,
            "personality": self.personality.value,
            "skill_level": self.skill_level.value,
            "response_time": self.response_time.value,
            "language": self.language,
            "created_at": self.created_at,
            "last_active": self.last_active
        }