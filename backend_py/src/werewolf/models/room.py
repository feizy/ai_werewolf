"""Game room models for werewolf game."""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from .player import Player, Role, Team


class RoomStatus(str, Enum):
    """Room status."""
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"


@dataclass
class RoleDistribution:
    """Role distribution configuration."""
    werewolf: int = 3
    villager: int = 3
    seer: int = 1
    witch: int = 1
    hunter: int = 1

    @property
    def total_players(self) -> int:
        """Get total players required."""
        return (self.werewolf + self.villager + self.seer + self.witch + self.hunter)

    @property
    def roles_list(self) -> List[Role]:
        """Get list of all roles."""
        roles = []
        roles.extend([Role.WEREWOLF] * self.werewolf)
        roles.extend([Role.VILLAGER] * self.villager)
        roles.extend([Role.SEER] * self.seer)
        roles.extend([Role.WITCH] * self.witch)
        roles.extend([Role.HUNTER] * self.hunter)
        return roles


@dataclass
class PhaseDurations:
    """Phase duration configuration (in seconds)."""
    night: int = 30
    sheriff_election: int = 120
    day_discussion: int = 180
    voting: int = 60


@dataclass
class GameConfiguration:
    """Game configuration."""
    role_distribution: RoleDistribution = field(default_factory=RoleDistribution)
    phase_durations: PhaseDurations = field(default_factory=PhaseDurations)
    max_players: int = 9
    game_mode: str = "classic"


class GameRoom:
    """Game room model."""

    def __init__(
        self,
        name: Optional[str] = None,
        creator_id: Optional[str] = None,
        max_players: int = 9,
        game_config: Optional[GameConfiguration] = None
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.creator_id = creator_id or str(uuid.uuid4())
        self.max_players = max_players
        self.status = RoomStatus.WAITING
        self.game_config = game_config or GameConfiguration()
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.ended_at: Optional[datetime] = None

        self._players: List[Player] = []

    @property
    def players(self) -> List[Player]:
        """Get all players in room."""
        return self._players.copy()

    @property
    def current_players(self) -> int:
        """Get current number of players."""
        return len(self._players)

    @property
    def is_full(self) -> bool:
        """Check if room is full."""
        return self.current_players >= self.max_players

    @property
    def can_start_game(self) -> bool:
        """Check if game can start."""
        return (
            self.status == RoomStatus.WAITING and
            self.current_players == self.max_players
        )

    def add_player(self, player: Player) -> bool:
        """Add player to room."""
        if self.is_full:
            return False

        # Check for duplicate names
        if any(p.name == player.name for p in self._players):
            raise ValueError(f"Player name '{player.name}' already exists in room")

        self._players.append(player)
        player.room_id = self.id
        return True

    def remove_player(self, player_id: str) -> Optional[Player]:
        """Remove player from room."""
        for i, player in enumerate(self._players):
            if player.id == player_id:
                removed_player = self._players.pop(i)
                removed_player.room_id = ""
                return removed_player
        return None

    def get_player(self, player_id: str) -> Optional[Player]:
        """Get player by ID."""
        for player in self._players:
            if player.id == player_id:
                return player
        return None

    def get_player_by_name(self, name: str) -> Optional[Player]:
        """Get player by name."""
        for player in self._players:
            if player.name == name:
                return player
        return None

    def get_alive_players(self) -> List[Player]:
        """Get all alive players."""
        return [p for p in self._players if p.is_alive]

    def get_players_by_role(self, role: Role) -> List[Player]:
        """Get players by role."""
        return [p for p in self._players if p.role == role]

    def get_players_by_team(self, team: Team) -> List[Player]:
        """Get players by team."""
        return [p for p in self._players if p.role and p.team == team]

    def assign_positions(self) -> None:
        """Assign seat positions to players."""
        for i, player in enumerate(self._players):
            player.position = i + 1

    def shuffle_players(self) -> None:
        """Shuffle player order and assign positions."""
        import random
        random.shuffle(self._players)
        self.assign_positions()

    def assign_roles(self) -> None:
        """Assign roles to all players."""
        if self.current_players != self.max_players:
            raise ValueError(f"Need {self.max_players} players to assign roles")

        roles = self.game_config.role_distribution.roles_list
        import random
        random.shuffle(roles)

        for player, role in zip(self._players, roles):
            player.set_role(role)

    def start_game(self) -> bool:
        """Start the game."""
        if not self.can_start_game:
            return False

        self.status = RoomStatus.PLAYING
        self.started_at = datetime.now()
        return True

    def end_game(self) -> None:
        """End the game."""
        self.status = RoomStatus.FINISHED
        self.ended_at = datetime.now()

    def get_summary(self) -> Dict[str, Any]:
        """Get room summary."""
        return {
            "id": self.id,
            "name": self.name,
            "creator_id": self.creator_id,
            "max_players": self.max_players,
            "current_players": self.current_players,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "is_full": self.is_full,
            "can_start_game": self.can_start_game,
            "players": [p.to_dict() for p in self._players],
        }

    def get_status_info(self) -> Dict[str, Any]:
        """Get room status information for API responses."""
        creator = self.get_player(self.creator_id)
        return {
            "id": self.id,
            "name": self.name,
            "creator_name": creator.name if creator else "Unknown",
            "max_players": self.max_players,
            "current_players": self.current_players,
            "status": self.status.value,
            "players": [p.get_public_info() for p in self._players],
        }

    def validate_state(self) -> Dict[str, Any]:
        """Validate room state."""
        errors = []

        # Check creator exists
        if not self.get_player(self.creator_id):
            errors.append("Creator not found in players")

        # Check player count
        if len(self._players) != self.current_players:
            errors.append("Player count mismatch")

        # Check for duplicate names
        names = [p.name for p in self._players]
        if len(names) != len(set(names)):
            errors.append("Duplicate player names found")

        # Check duplicate positions
        positions = [p.position for p in self._players if p.position > 0]
        if len(positions) != len(set(positions)):
            errors.append("Duplicate positions found")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert room to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "creator_id": self.creator_id,
            "max_players": self.max_players,
            "current_players": self.current_players,
            "status": self.status.value,
            "game_config": {
                "role_distribution": {
                    "werewolf": self.game_config.role_distribution.werewolf,
                    "villager": self.game_config.role_distribution.villager,
                    "seer": self.game_config.role_distribution.seer,
                    "witch": self.game_config.role_distribution.witch,
                    "hunter": self.game_config.role_distribution.hunter,
                },
                "phase_durations": {
                    "night": self.game_config.phase_durations.night,
                    "sheriff_election": self.game_config.phase_durations.sheriff_election,
                    "day_discussion": self.game_config.phase_durations.day_discussion,
                    "voting": self.game_config.phase_durations.voting,
                },
                "max_players": self.game_config.max_players,
                "game_mode": self.game_config.game_mode,
            },
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "players": [p.get_public_info() for p in self._players],
        }

    @classmethod
    def create_room(
        cls,
        room_name: Optional[str] = None,
        max_players: int = 9
    ) -> "GameRoom":
        """Create new empty room. Players join via add_player()."""
        room = cls(
            name=room_name,
            max_players=max_players
        )
        return room

    @classmethod
    def create_test_room(cls, player_count: int = 9) -> "GameRoom":
        """Create test room with AI players."""
        room = cls(name="Test Room", max_players=player_count)

        # Create test players
        for i in range(player_count):
            player = Player.create_ai_player(
                name=f"AI Player {i + 1}",
                room_id=room.id,
                position=i
            )
            room.add_player(player)

        return room

    def __str__(self) -> str:
        """String representation."""
        return f"GameRoom(id={self.id}, name={self.name}, players={self.current_players}/{self.max_players})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"GameRoom(id={self.id}, name={self.name}, status={self.status.value}, "
                f"creator_id={self.creator_id}, players={self.current_players}/{self.max_players})")