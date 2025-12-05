"""Factory for creating game agents."""

from typing import Dict, Any, Optional, List
from ..models.player import Player, Role, PersonalityType, SkillLevel
from .werewolf_agent import (
    WerewolfReactAgent, SeerReactAgent, WitchReactAgent,
    HunterReactAgent, VillagerReactAgent
)
from loguru import logger


class AgentFactory:
    """Factory for creating game agents based on player roles."""

    _agent_classes = {
        Role.WEREWOLF: WerewolfReactAgent,
        Role.SEER: SeerReactAgent,
        Role.WITCH: WitchReactAgent,
        Role.HUNTER: HunterReactAgent,
        Role.VILLAGER: VillagerReactAgent
    }

    @classmethod
    def create_agent(
        cls,
        player: Player,
    ):
        """Create an agent for a player."""
        # Convert string personality to enum
        personality = PersonalityType(player.ai_config.personality) if isinstance(player.ai_config.personality, str) else player.ai_config.personality
        skill_level = SkillLevel(player.ai_config.skill_level) if isinstance(player.ai_config.skill_level, str) else player.ai_config.skill_level

        # Get model_config from player's ai_config
        model_config = getattr(player.ai_config, 'model_config', {})

        try:
            agent_class = cls._agent_classes.get(player.role, VillagerReactAgent)

            agent = agent_class(
                player_id=player.id,
                name=player.name,
                role=player.role,
                personality=personality,
                skill_level=skill_level,
                model_config=model_config
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
                personality=personality,
                skill_level=skill_level,
                model_config=model_config
            )

    @classmethod
    def get_agent_info(cls, role: Role) -> Dict[str, Any]:
        """Get information about an agent type."""
        agent_class = cls._agent_classes.get(role, VillagerReactAgent)

        return {
            "role": role.value,
            "agent_class": agent_class.__name__,
            "capabilities": cls._get_role_capabilities(role),
            "recommended_personality": cls._get_recommended_personality(role)
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
    def _get_recommended_personality(cls, role: Role) -> PersonalityType:
        """Get recommended personality for a role."""
        recommendations = {
            Role.WEREWOLF: PersonalityType.AGGRESSIVE,
            Role.SEER: PersonalityType.ANALYTICAL,
            Role.WITCH: PersonalityType.CAUTIOUS,
            Role.HUNTER: PersonalityType.AGGRESSIVE,
            Role.VILLAGER: PersonalityType.ANALYTICAL
        }
        return recommendations.get(role, PersonalityType.ANALYTICAL)

    @classmethod
    def create_all_agents(
        cls,
        players: list[Player],
    ) -> Dict[str, Any]:
        """Create agents for all players in a game."""
        agents = {}
        team_info = {
            "werewolves": [],
            "good_team": []
        }

        for player in players:
            agent = cls.create_agent(player)
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