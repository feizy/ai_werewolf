"""Factory for creating game agents."""

from typing import Dict, Any, Optional, List, TYPE_CHECKING
from ..models.player import Player, Role
from .werewolf_agent import (
    WerewolfReactAgent, SeerReactAgent, WitchReactAgent,
    HunterReactAgent, VillagerReactAgent
)
from loguru import logger

if TYPE_CHECKING:
    from ..services.ai_manager import AIManager


class AgentFactory:
    """Factory for creating game agents based on player roles.
    
    Uses AIManager for unified model creation.
    """

    _agent_classes = {
        Role.WEREWOLF: WerewolfReactAgent,
        Role.SEER: SeerReactAgent,
        Role.WITCH: WitchReactAgent,
        Role.HUNTER: HunterReactAgent,
        Role.VILLAGER: VillagerReactAgent
    }

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
    def create_all_agents(cls, players: list[Player], ai_manager: "AIManager" = None) -> Dict[str, Any]:
        """Create agents for all players in a game.
        
        Args:
            players: List of players to create agents for
            ai_manager: Optional AIManager for unified model creation
        """
        agents = {}
        team_info = {
            "werewolves": [],
            "good_team": []
        }

        for player in players:
            # Use AIManager to create model if provided
            model = None
            if ai_manager:
                model_config = cls._get_model_config_dict(player)
                if model_config:
                    try:
                        model = ai_manager._create_model_for_player(model_config)
                        logger.info(f"Created model via AIManager for {player.name}")
                    except Exception as e:
                        logger.warning(f"Failed to create model via AIManager for {player.name}: {e}")
            
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
