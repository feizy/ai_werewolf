"""Game session and state models."""

from enum import Enum
from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from .player import Player, Role, Team, PlayerStatus


class GamePhase(str, Enum):
    """Game phases."""
    NIGHT = "night"
    SHERIFF_ELECTION = "sheriff_election"
    DAY_DISCUSSION = "day_discussion"
    VOTING = "voting"
    GAME_OVER = "game_over"


class DeathCause(str, Enum):
    """Death causes."""
    WEREWOLF_KILL = "werewolf_kill"
    VOTE_OUT = "vote_out"
    WITCH_POISON = "witch_poison"
    HUNTER_SHOOT = "hunter_shoot"


class EventType(str, Enum):
    """Event types."""
    # System events
    GAME_START = "game_start"
    GAME_END = "game_end"
    PHASE_CHANGE = "phase_change"
    DAILY_SUMMARY = "daily_summary"
    # Night events
    WEREWOLF_KILL = "werewolf_kill"
    SEER_CHECK = "seer_check"
    WITCH_SAVE = "witch_save"
    WITCH_POISON = "witch_poison"

    # Day events
    SHERIFF_ELECTION_START = "sheriff_election_start"
    SHERIFF_CANDIDACY = "sheriff_candidacy"
    SHERIFF_SPEECH = "sheriff_speech"
    SHERIFF_ELECTED = "sheriff_elected"

    # Discussion events
    PLAYER_SPEAK = "player_speak"
    PLAYER_SPEECH = "player_speech"  # Alias for compatibility

    # Voting events
    VOTE_START = "vote_start"
    PLAYER_VOTE = "player_vote"
    VOTE_RESULT = "vote_result"

    # Death events
    PLAYER_DEATH = "player_death"
    DEATH_ANNOUNCE = "death_announce"  # Announce deaths at day start

    # Hunter events
    HUNTER_SHOOT = "hunter_shoot"

    # Role action events
    ROLE_ACTION = "role_action"


@dataclass
class SheriffState:
    """Sheriff state."""
    player_id: str
    player_name: str
    has_last_word: bool = True
    can_transfer: bool = True
    transferred_to_id: Optional[str] = None


@dataclass
class NightActions:
    """Night phase actions."""
    werewolf_target: Optional[Dict[str, str]] = None  # {player_id, player_name}
    seer_check: Optional[Dict[str, str]] = None       # {target_id, target_name, result}
    witch_action: Optional[Dict[str, Any]] = None      # {action, target_id, target_name}
    witch_save: bool = False                           # Whether witch used antidote
    witch_poison_target: Optional[Dict[str, str]] = None  # {player_id, player_name}


@dataclass
class DayPhaseState:
    """Day phase state."""
    speaker_queue: List[str] = field(default_factory=list)
    current_speaker: Optional[str] = None
    speaking_time_limit: int = 180  # seconds
    messages: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Vote:
    """Vote record."""
    voter_id: str
    voter_name: str
    candidate_id: str
    weight: float
    timestamp: datetime


@dataclass
class VotingCandidate:
    """Voting candidate."""
    player_id: str
    player_name: str
    role: Optional[Role] = None
    vote_count: float = 0.0
    vote_weight: float = 1.0


@dataclass
class VotingResult:
    """Voting result."""
    winner: Optional[VotingCandidate] = None
    eliminated: Optional[VotingCandidate] = None
    tied_candidates: List[VotingCandidate] = field(default_factory=list)
    total_votes: int = 0
    sheriff_influence: bool = False


@dataclass
class VotingState:
    """Voting state."""
    voting_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    voting_type: str = "player_elimination"  # "sheriff_election" or "player_elimination"
    candidates: List[VotingCandidate] = field(default_factory=list)
    votes: List[Vote] = field(default_factory=list)
    status: Literal["active", "completed"] = "active"
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    result: Optional[VotingResult] = None


@dataclass
class GameState:
    """Current game state."""
    phase: GamePhase
    day_count: int
    players: List[Dict[str, Any]]  # Player state dictionaries
    sheriff: Optional[SheriffState] = None
    night_actions: Optional[NightActions] = None
    day_phase: Optional[DayPhaseState] = None
    voting: Optional[VotingState] = None


@dataclass
class EventVisibility:
    """Event visibility rules."""
    public: bool
    visible_to_roles: List[Role] = field(default_factory=list)
    visible_to_players: List[str] = field(default_factory=list)
    requires_role_reveal: bool = False


@dataclass
class GameEvent:
    """Game event."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    type: EventType = EventType.GAME_START
    phase: GamePhase = GamePhase.NIGHT
    day_count: int = 1
    timestamp: datetime = field(default_factory=datetime.now)
    actor_id: Optional[str] = None
    actor_name: Optional[str] = None
    target_id: Optional[str] = None
    target_name: Optional[str] = None
    content: str = ""
    details: Optional[Dict[str, Any]] = None
    visibility: EventVisibility = field(default_factory=lambda: EventVisibility(public=True))

    @property
    def is_public(self) -> bool:
        """Check if event is public."""
        return self.visibility.public

    @property
    def day_number(self) -> int:
        """Alias for day_count."""
        return self.day_count

    @property
    def event_type(self) -> EventType:
        """Alias for type."""
        return self.type

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "type": self.type.value,
            "event_type": self.type.value,  # For compatibility with frontend
            "phase": self.phase.value,
            "day_count": self.day_count,
            "timestamp": self.timestamp.isoformat(),
            "actor_id": self.actor_id,
            "actor_name": self.actor_name,
            "target_id": self.target_id,
            "target_name": self.target_name,
            "content": self.content,
            "details": self.details,
        }


@dataclass
class DailySnapshot:
    """Daily game state snapshot."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    day_number: int = 1
    timestamp: datetime = field(default_factory=datetime.now)
    player_states: List[Dict[str, Any]] = field(default_factory=list)
    game_state: Optional[Dict[str, Any]] = None
    events: List[GameEvent] = field(default_factory=list)


class GameSession:
    """Game session model."""

    def __init__(self, room_id: str, players: List[Player]):
        self.id = str(uuid.uuid4())
        self.room_id = room_id
        self.players = players
        self.day_count = 1
        self.current_phase = GamePhase.NIGHT
        self.phase_start_time = datetime.now()
        self.events: List[GameEvent] = []
        self.daily_snapshots: List[DailySnapshot] = []
        self.winner: Optional[Team] = None
        self.ended_at: Optional[datetime] = None

        # Sheriff state
        self.sheriff: Optional[SheriffState] = None

        # Phase-specific states
        self.night_actions: NightActions = NightActions()
        self.day_phase: Optional[DayPhaseState] = None
        self.voting: Optional[VotingState] = None

        self._create_initial_state()

    def _create_initial_state(self) -> None:
        """Create initial game state."""
        # Create daily snapshot
        self.create_daily_snapshot()

        # Add game start event
        self.add_event(EventType.GAME_START, "游戏开始！", is_public=True)

    @property
    def game_state(self) -> GameState:
        """Get current game state."""
        return GameState(
            phase=self.current_phase,
            day_count=self.day_count,
            players=[self._get_player_state(p) for p in self.players],
            sheriff=self.sheriff,
            night_actions=self.night_actions,
            day_phase=self.day_phase,
            voting=self.voting
        )

    def _get_player_state(self, player: Player) -> Dict[str, Any]:
        """Get player state dictionary."""
        return {
            "player_id": player.id,
            "player_name": player.name,
            "role": player.role.value if player.role else None,
            "status": player.status.value,
            "position": player.position,
            "abilities": {
                "witch_antidote": player.role_abilities.witch_has_antidote,
                "witch_poison": player.role_abilities.witch_has_poison,
                "hunter_can_shoot": player.role_abilities.hunter_can_shoot,
            } if player.role else None,
            "voting_weight": player.voting_weight
        }

    def get_alive_players(self) -> List[Player]:
        """Get all alive players."""
        return [p for p in self.players if p.is_alive]

    def get_players_by_role(self, role: Role) -> List[Player]:
        """Get players by role."""
        return [p for p in self.players if p.role == role]

    def get_players_by_team(self, team: Team) -> List[Player]:
        """Get players by team."""
        return [p for p in self.players if p.role and p.team == team]

    def transition_to_phase(self, phase: GamePhase) -> None:
        """Transition to new game phase."""
        self.current_phase = phase
        self.phase_start_time = datetime.now()

        phase_messages = {
            GamePhase.NIGHT: f"第{self.day_count}夜降临",
            GamePhase.SHERIFF_ELECTION: "警长竞选开始",
            GamePhase.DAY_DISCUSSION: f"第{self.day_count}天讨论开始",
            GamePhase.VOTING: "投票阶段开始",
            GamePhase.GAME_OVER: "游戏结束"
        }

        message = phase_messages.get(phase, f"进入{phase.value}阶段")
        self.add_event(EventType.PHASE_CHANGE, message, is_public=True)

    def add_event(
        self,
        event_type: EventType,
        content: str,
        actor_id: Optional[str] = None,
        actor_name: Optional[str] = None,
        target_id: Optional[str] = None,
        target_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        is_public: bool = True,
        visible_to_roles: Optional[List[Role]] = None,
        visible_to_players: Optional[List[str]] = None
    ) -> GameEvent:
        """Add game event."""
        event = GameEvent(
            session_id=self.id,
            type=event_type,
            phase=self.current_phase,
            day_count=self.day_count,
            actor_id=actor_id,
            actor_name=actor_name,
            target_id=target_id,
            target_name=target_name,
            content=content,
            details=details,
            visibility=EventVisibility(
                public=is_public,
                visible_to_roles=visible_to_roles or [],
                visible_to_players=visible_to_players or []
            )
        )

        self.events.append(event)
        return event

    def get_visible_events(
        self,
        player_id: Optional[str] = None,
        player_role: Optional[Role] = None
    ) -> List[GameEvent]:
        """Get events visible to a player."""
        visible_events = []

        for event in self.events:
            # Public events
            if event.visibility.public:
                visible_events.append(event)
                continue

            # Role-specific visibility
            if player_role and event.visibility.visible_to_roles:
                if player_role in event.visibility.visible_to_roles:
                    visible_events.append(event)
                continue

            # Player-specific visibility
            if player_id and event.visibility.visible_to_players:
                if player_id in event.visibility.visible_to_players:
                    visible_events.append(event)
                continue

        return visible_events

    def create_daily_snapshot(self) -> None:
        """Create daily snapshot."""
        snapshot = DailySnapshot(
            session_id=self.id,
            day_number=self.day_count,
            player_states=[self._get_player_state(p) for p in self.players],
            game_state={
                "phase": self.current_phase,
                "sheriff": {
                    "player_id": self.sheriff.player_id,
                    "player_name": self.sheriff.player_name
                } if self.sheriff else None,
                "alive_players": len(self.get_alive_players())
            },
            events=self.events.copy()
        )

        self.daily_snapshots.append(snapshot)

    def check_victory_conditions(self) -> Optional[Team]:
        """Check if victory conditions are met."""
        alive_players = self.get_alive_players()
        alive_werewolves = [p for p in alive_players if p.role == Role.WEREWOLF]
        alive_good = [p for p in alive_players if p.role != Role.WEREWOLF]
        alive_villagers = [p for p in alive_players if p.role == Role.VILLAGER]
        alive_special = [p for p in alive_players if p.role in [Role.SEER, Role.WITCH, Role.HUNTER]]

        # Werewolf victory conditions
        if (len(alive_werewolves) >= len(alive_good) or
            len(alive_villagers) == 0 or
            len(alive_special) == 0):
            self.winner = Team.WEREWOLF
            return Team.WEREWOLF

        # Good team victory condition
        if len(alive_werewolves) == 0:
            self.winner = Team.GOOD
            return Team.GOOD

        return None

    def start_game(self) -> None:
        """Start the game."""
        # Add game start event
        # self.add_event(
        #     EventType.GAME_START,
        #     "游戏开始，所有玩家就位",
        #     is_public=True
        # )

        # Create initial daily snapshot
        self.create_daily_snapshot()

    def end_game(self) -> None:
        """End the game."""
        self.current_phase = GamePhase.GAME_OVER
        self.ended_at = datetime.now()

        # Create final snapshot
        self.create_daily_snapshot()

        # Add game end event
        winner_text = "狼人阵营" if self.winner == Team.WEREWOLF else "好人阵营"
        self.add_event(
            EventType.GAME_END,
            f"游戏结束！{winner_text}获胜！",
            is_public=True
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get game session summary."""
        return {
            "id": self.id,
            "room_id": self.room_id,
            "status": "ended" if self.ended_at else "running",
            "current_phase": self.current_phase,
            "day_count": self.day_count,
            "players": [p.get_private_info() for p in self.players],
            "winner": self.winner.value if self.winner else None,
            "start_time": self.phase_start_time.isoformat(),
            "end_time": self.ended_at.isoformat() if self.ended_at else None,
            "duration": (
                (self.ended_at - self.phase_start_time).total_seconds()
                if self.ended_at
                else (datetime.now() - self.phase_start_time).total_seconds()
            )
        }

    def get_events_by_day(self, day_number: int) -> List[GameEvent]:
        """Get events for specific day."""
        return [e for e in self.events if e.day_count == day_number]

    def get_events_by_phase(self, phase: GamePhase) -> List[GameEvent]:
        """Get events for specific phase."""
        return [e for e in self.events if e.phase == phase]

    def get_events_by_type(self, event_type: EventType) -> List[GameEvent]:
        """Get events of specific type."""
        return [e for e in self.events if e.type == event_type]

    def to_dict(self) -> Dict[str, Any]:
        """Convert game session to dictionary."""
        # Try to get events from EventService if available
        events = self.events  # fallback to internal events

        # Note: EventService is not available in this context,
        # so we use internal events. The API handles EventService integration.

        return {
            "id": self.id,
            "room_id": self.room_id,
            "day_count": self.day_count,
            "current_phase": self.current_phase,
            "phase_start_time": self.phase_start_time.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "winner": self.winner.value if self.winner else None,
            "events_count": len(events),
            "snapshots_count": len(self.daily_snapshots),
            "players": [p.get_private_info() for p in self.players],
            "events": [event.to_dict() for event in events],
            "is_running": self.ended_at is None,
        }