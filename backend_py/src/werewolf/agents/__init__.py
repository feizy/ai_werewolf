"""AgentScope agents for werewolf game."""

from .werewolf_agent import WerewolfReactAgent
from .base_agent import BaseGameAgent
from .agent_factory import AgentFactory

__all__ = [
    "WerewolfReactAgent",
    "BaseGameAgent",
    "AgentFactory"
]