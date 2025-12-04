"""
AI Werewolf Game Backend

A comprehensive backend system for AI-powered werewolf games using AgentScope framework.
"""

__version__ = "1.0.0"
__author__ = "AI Arena Team"
__email__ = "team@aiarena.dev"

from .core.game import WerewolfGame
from .models.player import Player, Role, Team
from .models.room import GameRoom
from .services.ai_manager import AIManager
from .services.game_engine import GameEngine

__all__ = [
    "WerewolfGame",
    "Player",
    "Role",
    "Team",
    "GameRoom",
    "AIManager",
    "GameEngine",
]