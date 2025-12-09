"""AI manager for AgentScope integration."""

import asyncio
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# AgentScope imports
from agentscope.agent import ReActAgent
from agentscope.message import Msg
from agentscope.model import AnthropicChatModel, OpenAIChatModel, DashScopeChatModel
from agentscope.formatter import AnthropicChatFormatter, OpenAIChatFormatter, DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from loguru import logger

# Import from player.py (single source of truth)
from ..models.player import Player, Role, ModelProvider, ModelConfig


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
    system_prompt: str
    response_format: str = "json"
    capabilities: List[str] = None


class AIManager:
    """Manages AI agents for the werewolf game.
    
    Supports lazy initialization - agents are created per-player with individual model configs.
    """

    def __init__(self):
        self.agents: Dict[str, ReActAgent] = {}
        self.agent_configs: Dict[str, AgentConfig] = {}
        self.player_models: Dict[str, Any] = {}  # player_id -> model instance

    def _get_default_model_config(self) -> Dict[str, Any]:
        """Get default model configuration from environment."""
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check for API keys in order of preference
        if os.getenv("ANTHROPIC_API_KEY"):
            return {
                "provider": ModelProvider.ANTHROPIC,
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
                "model_name": os.getenv("MODEL_NAME", "glm-4"),
            }
        elif os.getenv("OPENAI_API_KEY"):
            return {
                "provider": ModelProvider.OPENAI,
                "api_key": os.getenv("OPENAI_API_KEY"),
                "model_name": os.getenv("MODEL_NAME", "gpt-4"),
            }
        elif os.getenv("DASHSCOPE_API_KEY"):
            return {
                "provider": ModelProvider.DASHSCOPE,
                "api_key": os.getenv("DASHSCOPE_API_KEY"),
                "model_name": os.getenv("MODEL_NAME", "qwen-max"),
            }
        
        return {}

    def _create_model_for_player(self, model_config: Dict[str, Any]) -> Any:
        """Create model instance for a specific player based on their config.
        
        Supports ModelConfig dataclass or dict with same fields:
        - model_name: str (required)
        - api_key: str (required)
        - provider: ModelProvider (default: ANTHROPIC)
        - client_kwargs: Dict (for base_url, etc.)
        """
        # Handle ModelConfig dataclass
        if hasattr(model_config, '__dataclass_fields__'):
            config_dict = {
                "provider": model_config.provider,
                "model_name": model_config.model_name,
                "api_key": model_config.api_key,
                "stream": model_config.stream,
                "client_kwargs": model_config.client_kwargs,
            }
            model_config = config_dict
        
        # Merge with defaults if no config provided
        if not model_config:
            model_config = self._get_default_model_config()
        
        if not model_config.get("api_key"):
            raise ValueError("No API key provided for AI player")
        
        provider = model_config.get("provider", ModelProvider.ANTHROPIC)
        api_key = model_config["api_key"]
        model_name = model_config.get("model_name", "glm-4")
        stream = model_config.get("stream", False)
        enable_thinking = model_config.get("enable_thinking", False)
        client_kwargs = model_config.get("client_kwargs", {})
        
        logger.info(f"Creating model: provider={provider}, model={model_name}")
        
        # Create model based on provider
        if provider == ModelProvider.ANTHROPIC:
            # AnthropicChatModel for Claude / 智谱 GLM (Anthropic-compatible API)
            model = AnthropicChatModel(model_name, api_key=api_key, stream=stream, client_kwargs=client_kwargs)
        elif provider == ModelProvider.OPENAI:
            # OpenAIChatModel for GPT / vLLM / compatible endpoints
            model = OpenAIChatModel(model_name, api_key=api_key, stream=stream, enable_thinking=enable_thinking, client_kwargs=client_kwargs)
        elif provider == ModelProvider.DASHSCOPE:
            # DashScopeChatModel for Qwen (阿里通义)
            model = DashScopeChatModel(model_name, api_key=api_key, stream=stream, enable_thinking=enable_thinking)
        else:
            raise ValueError(f"Unsupported model provider: {provider}")
        
        return model

    async def create_agent(
        self,
        player: Player,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create AI agent for player with player-specific model config."""
        agent_id = f"agent-{player.id}"
        agent_type = self._role_to_agent_type(player.role)
        
        # Get model config from player's ai_config or use custom_config
        player_model_config = {}
        if player.ai_config and player.ai_config.model_config:
            player_model_config = player.ai_config.model_config
        if custom_config:
            player_model_config.update(custom_config)
        
        # Create model for this specific player
        try:
            model = self._create_model_for_player(player_model_config)
            self.player_models[player.id] = model
            logger.info(f"Created model for player {player.name}: {player_model_config.get('model_name', 'default')}")
        except Exception as e:
            logger.error(f"Failed to create model for player {player.name}: {e}")
            raise

        # Create AgentScope agent with player's model
        agent = await self._create_agentscope_agent(
            agent_id,
            player.name,
            agent_type,
            player.ai_config,
            model
        )

        self.agents[agent_id] = agent
        return agent_id

    def _role_to_agent_type(self, role: Optional[Role]) -> AgentType:
        """Convert player role to agent type."""
        role_mapping = {
            Role.WEREWOLF: AgentType.WEREWOLF,
            Role.SEER: AgentType.SEER,
            Role.WITCH: AgentType.WITCH,
            Role.HUNTER: AgentType.HUNTER,
            Role.VILLAGER: AgentType.VILLAGER,
        }
        return role_mapping.get(role, AgentType.VILLAGER)

    async def _create_agentscope_agent(
        self,
        agent_id: str,
        player_name: str,
        agent_type: AgentType,
        ai_config: Any,
        model: Any
    ) -> ReActAgent:
        """Create AgentScope ReAct agent with player-specific model."""
        # Convert ai_config to dict if needed
        ai_config_dict = {}
        if ai_config:
            if hasattr(ai_config, '__dict__'):
                ai_config_dict = {k: v.value if hasattr(v, 'value') else v 
                                  for k, v in ai_config.__dict__.items()}
            elif isinstance(ai_config, dict):
                ai_config_dict = ai_config

        # Get system prompt based on role and personality
        system_prompt = self._get_system_prompt(agent_type, ai_config_dict)

        # Create the ReAct agent using player's specific model
        #不同类型的model使用不同类型的formatter
        if model.provider == ModelProvider.ANTHROPIC or model.provider ==ModelProvider.ZHIPU:
            formatter = AnthropicChatFormatter()
        elif model.provider == ModelProvider.OPENAI:
            formatter = OpenAIChatFormatter()
        elif model.provider == ModelProvider.DASHSCOPE:
            formatter = DashScopeChatFormatter()
        else:
            raise ValueError(f"Unsupported model provider: {model.provider}")
        agent = ReActAgent(
            name=f"{player_name}_{agent_type}",
            sys_prompt=system_prompt,
            model=model,
            formatter=formatter,
            max_iters=3,
            parallel_tool_calls=False,
            memory=InMemoryMemory()  
        )

        logger.info(f"Created AgentScope ReAct agent: {player_name} ({agent_type})")
        return agent

    def _get_system_prompt(self, agent_type: AgentType, ai_config: Dict[str, Any]) -> str:
        """Get system prompt for agent based on role only. LLM decides its own style."""
        prompts = {
            AgentType.WEREWOLF: self._get_werewolf_prompt(),
            AgentType.SEER: self._get_seer_prompt(),
            AgentType.WITCH: self._get_witch_prompt(),
            AgentType.HUNTER: self._get_hunter_prompt(),
            AgentType.VILLAGER: self._get_villager_prompt(),
        }
        return prompts.get(agent_type, prompts[AgentType.VILLAGER])

    def _get_werewolf_prompt(self) -> str:
        """Get werewolf system prompt."""
        return """你是狼人杀游戏中的【狼人】。

你的阵营：狼人阵营
你的目标：隐藏身份，消灭好人阵营，让狼人存活到最后。

你的能力：
- 夜晚与其他狼人一起讨论并选择击杀一名玩家
- 你知道谁是你的狼人队友

游戏规则：
- 优先击杀神职角色（预言家、女巫、猎人）对狼人有利
- 白天要伪装成好人，避免暴露身份
- 与狼人队友配合，必要时可以互相掩护

请根据游戏局势做出最优决策。"""

    def _get_seer_prompt(self) -> str:
        """Get seer system prompt."""
        return """你是狼人杀游戏中的【预言家】。

你的阵营：好人阵营
你的目标：利用查验能力找出狼人，帮助好人阵营获胜。

你的能力：
- 每晚可以查验一名玩家，得知其是狼人还是好人

游戏规则：
- 查验结果只有你自己知道
- 需要判断何时公开身份和查验结果
- 公开身份会成为狼人的首要目标
- 你的信息对好人阵营至关重要

请根据游戏局势做出最优决策。"""

    def _get_witch_prompt(self) -> str:
        """Get witch system prompt."""
        return """你是狼人杀游戏中的【女巫】。

你的阵营：好人阵营
你的目标：合理使用药剂，帮助好人阵营获胜。

你的能力：
- 解药：整局游戏只有一瓶，可以在夜间救活被狼人击杀的玩家
- 毒药：整局游戏只有一瓶，可以在夜间毒杀一名玩家
- 第一晚可以自救（如果你被狼人杀）

游戏规则：
- 每晚你会得知谁被狼人击杀
- 解药和毒药各只能使用一次
- 同一晚不能同时使用解药和毒药
- 药剂使用需谨慎，错误使用可能导致好人失败

请根据游戏局势做出最优决策。"""

    def _get_hunter_prompt(self) -> str:
        """Get hunter system prompt."""
        return """你是狼人杀游戏中的【猎人】。

你的阵营：好人阵营
你的目标：利用开枪技能带走狼人，帮助好人阵营获胜。

你的能力：
- 当你被投票出局或被狼人击杀时，可以开枪带走一名玩家
- 如果你被女巫毒死，则无法开枪

游戏规则：
- 开枪只有一次机会，需要选择最可疑的目标
- 可以适当暗示身份获得信任，但要注意不被狼人先手击杀
- 你的开枪可以在关键时刻扭转局势

请根据游戏局势做出最优决策。"""

    def _get_villager_prompt(self) -> str:
        """Get villager system prompt."""
        return """你是狼人杀游戏中的【平民】。

你的阵营：好人阵营
你的目标：通过观察和分析找出狼人，帮助好人阵营获胜。

你的能力：
- 没有特殊能力，但拥有一票投票权

游戏规则：
- 通过玩家的发言、行为、逻辑漏洞来判断身份
- 积极参与讨论，分享你的推理和观察
- 保护可能的神职玩家
- 你的投票和判断对好人阵营的胜利至关重要

请根据游戏局势做出最优决策。"""

    async def send_message(self, agent_id: str, message: str) -> Any:
        """Send message to agent and get response."""
        agent = self.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        try:
            # Create message
            msg = Msg(role="user", content=message)

            # Send message to agent
            response = agent(msg)

            return response
        except Exception as e:
            logger.error(f"Error sending message to agent {agent_id}: {e}")
            raise

    async def get_agent(self, agent_id: str) -> Optional[ReActAgent]:
        """Get agent by ID."""
        return self.agents.get(agent_id)

    def list_agents(self) -> List[str]:
        """List all agent IDs."""
        return list(self.agents.keys())

    def has_agent(self, player_id: str) -> bool:
        """Check if agent exists for player."""
        agent_id = f"agent-{player_id}"
        return agent_id in self.agents

    async def remove_agent(self, player_id: str) -> None:
        """Remove agent for a specific player."""
        agent_id = f"agent-{player_id}"
        if agent_id in self.agents:
            agent = self.agents.pop(agent_id)
            try:
                if hasattr(agent, 'close'):
                    await agent.close()
                logger.info(f"Removed agent for player: {player_id}")
            except Exception as e:
                logger.warning(f"Error closing agent {agent_id}: {e}")
        
        # Also remove the model
        if player_id in self.player_models:
            del self.player_models[player_id]

    async def shutdown(self) -> None:
        """Shutdown AI manager and cleanup all agents."""
        try:
            # Close all agents
            for agent_id, agent in self.agents.items():
                try:
                    if hasattr(agent, 'close'):
                        await agent.close()
                    logger.info(f"Closed agent: {agent_id}")
                except Exception as e:
                    logger.warning(f"Error closing agent {agent_id}: {e}")

            self.agents.clear()
            self.player_models.clear()
            logger.info("AI Manager shutdown successfully")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")