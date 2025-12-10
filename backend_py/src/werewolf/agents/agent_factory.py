"""Factory for creating game agents."""

import os
from typing import Dict, Any, Optional, List
from ..models.player import Player, Role, ModelProvider
from .werewolf_agent import (
    WerewolfReactAgent, SeerReactAgent, WitchReactAgent,
    HunterReactAgent, VillagerReactAgent
)
from loguru import logger

# AgentScope imports for model creation
from agentscope.model import AnthropicChatModel, OpenAIChatModel, DashScopeChatModel


class AgentFactory:
    """Factory for creating game agents based on player roles.

    Handles model creation and caching directly.
    """

    _agent_classes = {
        Role.WEREWOLF: WerewolfReactAgent,
        Role.SEER: SeerReactAgent,
        Role.WITCH: WitchReactAgent,
        Role.HUNTER: HunterReactAgent,
        Role.VILLAGER: VillagerReactAgent
    }

    # Cache models per player to avoid recreation
    _player_models: Dict[str, Any] = {}

    @classmethod
    def create_agent(cls, player: Player, model: Any = None):
        """Create an agent for a player with optional pre-created model."""
        # Get model_config from player's ai_config
        model_config = None
        if player.ai_config and player.ai_config.model_config:
            mc = player.ai_config.model_config
            model_config = {
                "model_name": mc.model_name,
                "api_key": mc.api_key,
                "provider": mc.provider.value if hasattr(mc.provider, 'value') else mc.provider,
                "stream": mc.stream,
                "enable_thinking": mc.enable_thinking,
                "client_kwargs": mc.client_kwargs
            }

        try:
            agent_class = cls._agent_classes.get(player.role, VillagerReactAgent)

            agent = agent_class(
                player_id=player.id,
                name=player.name,
                role=player.role,
                model_config=model_config,
                model=model  # Pass pre-created model
            )

            logger.info(f"Created {player.role.value} agent for player {player.name}")
            return agent

        except Exception as e:
            logger.error(f"Failed to create agent for player {player.name}: {e}")
            # Fallback to villager agent
            return VillagerReactAgent(
                player_id=player.id,
                name=player.name,
                role=player.role,
                model_config=model_config,
                model=model
            )

    @classmethod
    def get_agent_info(cls, role: Role) -> Dict[str, Any]:
        """Get information about an agent type."""
        agent_class = cls._agent_classes.get(role, VillagerReactAgent)

        return {
            "role": role.value,
            "agent_class": agent_class.__name__,
            "capabilities": cls._get_role_capabilities(role)
        }

    @classmethod
    def _get_role_capabilities(cls, role: Role) -> List[str]:
        """Get capabilities for a role."""
        capabilities = {
            Role.WEREWOLF: ["夜间击杀", "团队合作", "身份伪装", "局势分析"],
            Role.SEER: ["身份查验", "逻辑推理", "团队引导", "信息管理"],
            Role.WITCH: ["使用解药", "使用毒药", "局势判断", "药剂管理"],
            Role.HUNTER: ["死亡开枪", "威胁分析", "时机把握", "最终判断"],
            Role.VILLAGER: ["逻辑推理", "观察分析", "团队协作", "投票判断"]
        }
        return capabilities.get(role, ["基础游戏能力"])

    @classmethod
    def create_all_agents(cls, players: list[Player]) -> Dict[str, Any]:
        """Create agents for all players in a game.

        Args:
            players: List of players to create agents for
        """
        agents = {}
        team_info = {
            "werewolves": [],
            "good_team": []
        }

        for player in players:
            # Get/create model for this player
            model = None
            model_config = cls._get_model_config_dict(player)
            if model_config:
                try:
                    model = cls.get_model_for_player(player.id, model_config)
                    logger.info(f"Got model for {player.name}")
                except Exception as e:
                    logger.warning(f"Failed to create model for {player.name}: {e}")

            agent = cls.create_agent(player, model=model)
            agents[player.id] = agent

            if player.role == Role.WEREWOLF:
                team_info["werewolves"].append({
                    "id": player.id,
                    "name": player.name,
                    "agent": agent
                })
            else:
                team_info["good_team"].append({
                    "id": player.id,
                    "name": player.name,
                    "role": player.role.value,
                    "agent": agent
                })

        # Setup team knowledge for werewolves
        cls._setup_team_knowledge(team_info["werewolves"])

        logger.info(f"Created {len(agents)} agents for game")
        return {
            "agents": agents,
            "team_info": team_info
        }
    
    @classmethod
    def _get_model_config_dict(cls, player: Player) -> Optional[Dict[str, Any]]:
        """Extract model config dict from player."""
        if not player.ai_config or not player.ai_config.model_config:
            return None

        mc = player.ai_config.model_config
        return {
            "model_name": mc.model_name,
            "api_key": mc.api_key,
            "provider": mc.provider.value if hasattr(mc.provider, 'value') else mc.provider,
            "stream": mc.stream,
            "enable_thinking": mc.enable_thinking,
            "client_kwargs": mc.client_kwargs
        }

    @classmethod
    def _create_model_for_player(cls, model_config: Dict[str, Any]) -> Any:
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
            model_config = cls._get_default_model_config()

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
            model = AnthropicChatModel(model_name, api_key=api_key, stream=stream)
        elif provider == ModelProvider.OPENAI:
            # OpenAIChatModel for GPT / vLLM / compatible endpoints
            model = OpenAIChatModel(model_name, api_key=api_key, stream=stream, enable_thinking=enable_thinking, client_kwargs=client_kwargs)
        elif provider == ModelProvider.DASHSCOPE:
            # DashScopeChatModel for Qwen (阿里通义)
            model = DashScopeChatModel(model_name, api_key=api_key, stream=stream, enable_thinking=enable_thinking)
        else:
            raise ValueError(f"Unsupported model provider: {provider}")

        return model

    @classmethod
    def _get_default_model_config(cls) -> Dict[str, Any]:
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

    @classmethod
    def get_model_for_player(cls, player_id: str, model_config: Optional[Dict[str, Any]] = None) -> Any:
        """Return cached model for player or create one.

        Args:
            player_id: player id, used as cache key
            model_config: dict or ModelConfig; if None, fallback to env defaults
        """
        if player_id in cls._player_models:
            return cls._player_models[player_id]

        model = cls._create_model_for_player(model_config or {})
        cls._player_models[player_id] = model
        return model

    @classmethod
    def _setup_team_knowledge(cls, werewolves: list[Dict[str, Any]]) -> None:
        """Setup team knowledge for werewolves."""
        for werewolf in werewolves:
            agent = werewolf["agent"]
            # Add teammates to notes
            for teammate in werewolves:
                if teammate["id"] != werewolf["id"]:
                    agent.update_player_notes(
                        teammate["id"],
                        "队友 - 需要配合和保护"
                    )
