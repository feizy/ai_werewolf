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
from ..models.player import Player, Role, PersonalityType, SkillLevel, ModelProvider, ModelConfig


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
                "temperature": model_config.temperature,
                "stream": model_config.stream,
                "enable_thinking": model_config.enable_thinking,
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
        temperature = model_config.get("temperature", 0.7)
        stream = model_config.get("stream", False)
        enable_thinking = model_config.get("enable_thinking", False)
        client_kwargs = model_config.get("client_kwargs", {})
        
        logger.info(f"Creating model: provider={provider}, model={model_name}")
        
        # Create model based on provider
        if provider == ModelProvider.ANTHROPIC:
            # AnthropicChatModel for Claude / 智谱 GLM (Anthropic-compatible API)
            model = AnthropicChatModel(model_name, api_key=api_key, temperature=temperature, stream=stream, enable_thinking=enable_thinking, client_kwargs=client_kwargs)
        elif provider == ModelProvider.OPENAI:
            # OpenAIChatModel for GPT / vLLM / compatible endpoints
            model = OpenAIChatModel(model_name, api_key=api_key, temperature=temperature, stream=stream, enable_thinking=enable_thinking, client_kwargs=client_kwargs)
        elif provider == ModelProvider.DASHSCOPE:
            # DashScopeChatModel for Qwen (阿里通义)
            model = DashScopeChatModel(model_name, api_key=api_key, temperature=temperature, stream=stream, enable_thinking=enable_thinking)
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
        """Get system prompt for agent based on role and personality."""
        personality = ai_config.get("personality", "analytical")

        base_prompts = {
            AgentType.WEREWOLF: self._get_werewolf_prompt(personality),
            AgentType.SEER: self._get_seer_prompt(personality),
            AgentType.WITCH: self._get_witch_prompt(personality),
            AgentType.HUNTER: self._get_hunter_prompt(personality),
            AgentType.VILLAGER: self._get_villager_prompt(personality),
        }

        return base_prompts.get(agent_type, base_prompts[AgentType.VILLAGER])

    def _get_werewolf_prompt(self, personality: str) -> str:
        """Get werewolf system prompt."""
        personality_traits = {
            "aggressive": "你是狼人团队的攻击型玩家，喜欢主动出击和混淆视听。",
            "deceptive": "你是狼人团队的策略型玩家，擅长伪装和误导好人。",
            "analytical": "你是狼人团队的分析型玩家，会仔细分析局势并做出最优决策。"
        }

        trait_desc = personality_traits.get(personality, "你是一个理性的狼人玩家。")

        return f"""{trait_desc}

作为狼人，你的任务是隐藏身份并消灭好人阵营。

游戏策略：
- 夜晚选择击杀目标：优先击杀神职角色（预言家、女巫、猎人）
- 白天伪装成好人：积极参与讨论，避免暴露
- 制造混乱：转移注意力，陷害其他玩家
- 团队合作：与其他狼人协调行动

当前你的目标是存活到最后，让狼人团队获胜。"""

    def _get_seer_prompt(self, personality: str) -> str:
        """Get seer system prompt."""
        personality_traits = {
            "logical": "你是预言家，逻辑清晰，善于推理和分析。",
            "analytical": "你是预言家，注重细节和证据的收集。",
            "cautious": "你是预言家，行事谨慎，避免过早暴露身份。"
        }

        trait_desc = personality_traits.get(personality, "你是一个智慧的预言家。")

        return f"""{trait_desc}

作为预言家，你的职责是查验玩家身份，帮助好人阵营找出狼人。

你的能力：
- 每晚可以查验一名玩家，得知其是狼人还是好人

游戏策略：
- 合理使用查验次数：优先查验可疑玩家
- 保护身份：不要过早暴露预言家身份
- 引导讨论：在不暴露身份的情况下引导好人投票
- 记录信息：管理查验结果，建立身份档案

你的查验结果对好人阵营至关重要。"""

    def _get_witch_prompt(self, personality: str) -> str:
        """Get witch system prompt."""
        personality_traits = {
            "cautious": "你是女巫，非常谨慎，会仔细考虑每次用药。",
            "strategic": "你是女巫，擅长策略思考，懂得时机把握。",
            "analytical": "你是女巫，善于分析局势和玩家行为。"
        }

        trait_desc = personality_traits.get(personality, "你是一个智慧的女巫。")

        return f"""{trait_desc}

作为女巫，你拥有一瓶解药和一瓶毒药，是好人阵营的重要力量。

你的能力：
- 解药：可以在夜间救活被狼人击杀的玩家
- 毒药：可以在夜间毒杀一名玩家

游戏策略：
- 合理使用解药：判断被击杀者是否值得拯救
- 谨慎使用毒药：确保击杀狼人或可疑玩家
- 身份管理：平衡神职身份暴露的风险
- 观察分析：结合发言和行为判断玩家身份

你的药剂使用可以改变游戏局势。"""

    def _get_hunter_prompt(self, personality: str) -> str:
        """Get hunter system prompt."""
        personality_traits = {
            "aggressive": "你是猎人，性格直接，会果断使用开枪技能。",
            "strategic": "你是猎人，懂得战术配合，会选择最佳开枪时机。",
            "analytical": "你是猎人，会理性分析局势再决定行动。"
        }

        trait_desc = personality_traits.get(personality, "你是一个勇敢的猎人。")

        return f"""{trait_desc}

作为猎人，你拥有死亡时开枪的能力，是好人阵营的最后防线。

你的能力：
- 当你被投票出局或被狼人击杀时，可以开枪击杀一名玩家
- 开枪时机：死亡时立即选择目标并开枪

游戏策略：
- 身份保护：适当暗示身份获得信任
- 目标选择：优先选择狼人或高度可疑的玩家
- 最后一搏：确保开枪击中对好人威胁最大的玩家
- 证据收集：在存活时收集信息指导开枪决策

你的开枪可以为好人阵营翻盘。"""

    def _get_villager_prompt(self, personality: str) -> str:
        """Get villager system prompt."""
        personality_traits = {
            "logical": "你是平民，逻辑思维强，善于分析发言和行为。",
            "analytical": "你是平民，观察细致，注重细节和推理。",
            "cautious": "你是平民，行事稳健，避免被误导。"
        }

        trait_desc = personality_traits.get(personality, "你是一个热心的平民。")

        return f"""{trait_desc}

作为平民，虽然没有特殊能力，但你是好人阵营的重要力量。

你的任务：
- 积极参与讨论：分享观察和推理
- 逻辑分析：通过发言漏洞识别狼人
- 投票决策：支持可疑度低的玩家
- 团结合作：与其他好人共同对抗狼人

游戏策略：
- 仔细观察：记录玩家的言行模式
- 理性判断：避免被情绪或谣言影响
- 信息整合：结合多方信息做出判断
- 保护神职：在不确定时保护可能的神职玩家

你的投票和判断对好人阵营的胜利至关重要。"""

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