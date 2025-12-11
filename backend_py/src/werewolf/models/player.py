"""Player models for werewolf game."""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid


class Team(str, Enum):
    """Team affiliation."""
    WEREWOLF = "werewolf"
    GOOD = "good"


class Role(str, Enum):
    """Player roles."""
    WEREWOLF = "werewolf"
    VILLAGER = "villager"
    SEER = "seer"
    WITCH = "witch"
    HUNTER = "hunter"


# 已移除 PersonalityType, SkillLevel, ResponseTime, StrategyType
# AI 玩家完全依赖 LLM 自身能力进行游戏


@dataclass
class RoleAbilities:
    """Role-specific abilities."""
    # Seer abilities
    seer_checks_remaining: int = 0
    seer_check_results: List[Dict[str, Any]] = field(default_factory=list)
    seer_last_checked_id: Optional[str] = None

    # Witch abilities
    witch_has_antidote: bool = False
    witch_has_poison: bool = False
    witch_antidote_used: bool = False
    witch_poison_used: bool = False
    witch_poison_target_id: Optional[str] = None
    witch_last_night_victim_id: Optional[str] = None

    # Hunter abilities
    hunter_can_shoot: bool = False
    hunter_has_shot: bool = False
    hunter_shot_target_id: Optional[str] = None
    hunter_death_cause: Optional[str] = None

class ModelProvider(str, Enum):
    """Supported model providers."""
    ANTHROPIC = "anthropic"  # Claude models / 智谱 GLM (Anthropic-compatible)
    OPENAI = "openai"        # GPT models
    DASHSCOPE = "dashscope"  # Qwen models (阿里通义)


@dataclass
class ModelConfig:
    """Model configuration for AgentScope.
    
    Compatible with AgentScope model initialization:
    - AnthropicChatModel(model_name, api_key=..., client_kwargs=...)
    - OpenAIChatModel(model_name, api_key=..., client_kwargs=...)
    - DashScopeChatModel(model_name, api_key=...)
    """
    # Required fields (no default) must come first
    model_name: str
    api_key: str
    # Optional fields with defaults
    provider: ModelProvider = ModelProvider.ANTHROPIC
    stream: bool = False
    enable_thinking: bool = False
    client_kwargs: Dict[str, Any] = field(default_factory=dict)  # For base_url etc.

@dataclass
class AIConfig:
    """AI player configuration - simplified, LLM handles everything."""
    model_config: Optional[ModelConfig] = None
    language: str = "zh"  # zh or en


class PlayerStatus(str, Enum):
    """Player status."""
    ALIVE = "alive"
    DEAD = "dead"
    PROCESSING = "processing"


class ConnectionState(str, Enum):
    """Connection state."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PROCESSING = "processing"


@dataclass
class Player:
    """Player model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    room_id: str = ""
    role: Optional[Role] = None
    status: PlayerStatus = PlayerStatus.ALIVE
    position: int = 0
    connection_state: ConnectionState = ConnectionState.ACTIVE
    joined_at: datetime = field(default_factory=datetime.now)
    last_active_at: datetime = field(default_factory=datetime.now)

    # AI specific attributes
    ai_config: AIConfig = field(default_factory=AIConfig)
    agent_scope_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Game specific attributes
    role_abilities: RoleAbilities = field(default_factory=RoleAbilities)
    voting_weight: float = 1.0
    is_sheriff: bool = False

    def __post_init__(self):
        """Initialize role abilities after role is set."""
        if self.role:
            self._initialize_role_abilities()

    @property
    def is_alive(self) -> bool:
        """Check if player is alive."""
        return self.status == PlayerStatus.ALIVE

    @property
    def team(self) -> Optional[Team]:
        """Get player's team based on role. Returns None if role not assigned yet."""
        if not self.role:
            return None

        if self.role == Role.WEREWOLF:
            return Team.WEREWOLF
        return Team.GOOD

    def set_role(self, role: Role) -> None:
        """Set player role and initialize abilities."""
        self.role = role
        self._initialize_role_abilities()

    def _initialize_role_abilities(self) -> None:
        """Initialize role-specific abilities."""
        if not self.role:
            return

        if self.role == Role.SEER:
            self.role_abilities.seer_checks_remaining = 1
            self.role_abilities.seer_check_results = []

        elif self.role == Role.WITCH:
            self.role_abilities.witch_has_antidote = True
            self.role_abilities.witch_has_poison = True
            self.role_abilities.witch_antidote_used = False
            self.role_abilities.witch_poison_used = False

        elif self.role == Role.HUNTER:
            self.role_abilities.hunter_can_shoot = True
            self.role_abilities.hunter_has_shot = False

    def set_dead(self, cause: str) -> None:
        """Mark player as dead."""
        self.status = PlayerStatus.DEAD
        self.connection_state = ConnectionState.INACTIVE

        if self.role == Role.HUNTER:
            self.role_abilities.hunter_death_cause = cause

    def reset_nightly_abilities(self) -> None:
        """Reset abilities that refresh each night."""
        if self.role == Role.SEER:
            self.role_abilities.seer_checks_remaining = 1

        if self.role == Role.WITCH:
            self.role_abilities.witch_last_night_victim_id = None

    # Seer methods
    def seer_check(self, target_id: str, target_name: str, result: str) -> None:
        """Perform seer check on target player."""
        if self.role != Role.SEER:
            raise ValueError("Player is not a seer")

        if self.role_abilities.seer_checks_remaining <= 0:
            raise ValueError("No seer checks remaining")

        self.role_abilities.seer_checks_remaining -= 1
        self.role_abilities.seer_last_checked_id = target_id

        self.role_abilities.seer_check_results.append({
            "target_player_id": target_id,
            "target_name": target_name,
            "result": result,  # "werewolf" or "good"
            "night_number": 1,  # This should come from game state
            "timestamp": datetime.now().isoformat()
        })

    # Witch methods
    def use_antidote(self) -> None:
        """Use witch antidote."""
        if self.role != Role.WITCH:
            raise ValueError("Player is not a witch")

        if not self.role_abilities.witch_has_antidote:
            raise ValueError("No antidote available")

        self.role_abilities.witch_has_antidote = False
        self.role_abilities.witch_antidote_used = True

    def use_poison(self, target_id: str) -> None:
        """Use witch poison on target."""
        if self.role != Role.WITCH:
            raise ValueError("Player is not a witch")

        if not self.role_abilities.witch_has_poison:
            raise ValueError("No poison available")

        self.role_abilities.witch_has_poison = False
        self.role_abilities.witch_poison_used = True
        self.role_abilities.witch_poison_target_id = target_id

    # Hunter methods
    def hunter_shoot(self, target_id: str) -> None:
        """Hunter shoots target player."""
        if self.role != Role.HUNTER:
            raise ValueError("Player is not a hunter")

        if not self.role_abilities.hunter_can_shoot or self.role_abilities.hunter_has_shot:
            raise ValueError("Hunter cannot shoot")

        self.role_abilities.hunter_can_shoot = False
        self.role_abilities.hunter_has_shot = True
        self.role_abilities.hunter_shot_target_id = target_id

    # Sheriff methods
    def set_as_sheriff(self) -> None:
        """Set player as sheriff."""
        self.is_sheriff = True
        self.voting_weight = 1.5

    def remove_sheriff(self) -> None:
        """Remove sheriff status."""
        self.is_sheriff = False
        self.voting_weight = 1.0

    # Utility methods
    def update_last_active(self) -> None:
        """Update last active timestamp."""
        self.last_active_at = datetime.now()

    def set_processing(self) -> None:
        """Set player to processing state."""
        self.status = PlayerStatus.PROCESSING
        self.connection_state = ConnectionState.PROCESSING

    def set_active(self) -> None:
        """Set player to active state."""
        if self.is_alive:
            self.status = PlayerStatus.ALIVE
        self.connection_state = ConnectionState.ACTIVE
        self.update_last_active()

    def to_dict(self) -> Dict[str, Any]:
        """Convert player to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "room_id": self.room_id,
            "role": self.role.value if self.role else None,
            "status": self.status.value,
            "position": self.position,
            "connection_state": self.connection_state.value,
            "joined_at": self.joined_at.isoformat(),
            "last_active_at": self.last_active_at.isoformat(),
            "voting_weight": self.voting_weight,
            "is_alive": self.is_alive,
            "team": self.team.value if self.team else None,
            "is_sheriff": self.is_sheriff,
            "role_abilities": {
                "witch_has_antidote": self.role_abilities.witch_has_antidote,
                "witch_has_poison": self.role_abilities.witch_has_poison,
                "hunter_can_shoot": self.role_abilities.hunter_can_shoot,
            } if self.role else None,
        }

    def get_public_info(self) -> Dict[str, Any]:
        """Get public player information (hides role)."""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "position": self.position,
            "voting_weight": self.voting_weight,
            "is_alive": self.is_alive,
        }

    def get_private_info(self) -> Dict[str, Any]:
        """Get private player information (includes role)."""
        return self.to_dict()

    @classmethod
    def create_ai_player(
        cls,
        name: str,
        room_id: str,
        position: int,
        role: Optional[Role] = None,
        ai_config: Optional[Dict[str, Any]] = None,
        model_config: Optional[Dict[str, Any]] = None
    ) -> "Player":
        """Create AI player with model config. LLM handles all gameplay decisions."""
        # Build model_config if provided
        model_cfg = None
        if model_config and model_config.get("model_name") and model_config.get("api_key"):
            model_cfg = ModelConfig(
                model_name=model_config["model_name"],
                api_key=model_config["api_key"],
                provider=ModelProvider(model_config.get("provider", "anthropic")),
                stream=model_config.get("stream", False),
                enable_thinking=model_config.get("enable_thinking", False),
                client_kwargs=model_config.get("client_kwargs", {})
            )

        # Build ai_config
        language = ai_config.get("language", "zh") if ai_config else "zh"

        player = cls(
            name=name,
            room_id=room_id,
            position=position,
            ai_config=AIConfig(model_config=model_cfg, language=language)
        )

        if role:
            player.set_role(role)

        return player

    def __str__(self) -> str:
        """String representation."""
        return f"Player({self.name}, role={self.role}, status={self.status.value})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"Player(id={self.id}, name={self.name}, role={self.role}, "
                f"status={self.status.value}, position={self.position}, "
                f"voting_weight={self.voting_weight})")