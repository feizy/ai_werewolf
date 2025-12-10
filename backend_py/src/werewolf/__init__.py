"""
AI Werewolf Game Backend

A comprehensive backend system for AI-powered werewolf games using AgentScope framework.
"""

__version__ = "1.0.0"
__author__ = "AI Arena Team"
__email__ = "team@aiarena.dev"

from .models.player import Player, Role, Team
from .models.room import GameRoom
from .models.game import GameSession, GamePhase, EventType
from .services.ai_game_engine import AIGameEngine
from .agents.agent_factory import AgentFactory

__all__ = [
    "Player",
    "Role",
    "Team",
    "GameRoom",
    "GameSession",
    "GamePhase",
    "EventType",
    "AIGameEngine",
    "AgentFactory",
]