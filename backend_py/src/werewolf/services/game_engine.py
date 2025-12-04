"""Game engine for werewolf game."""

import asyncio
import random
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta

from loguru import logger

from ..models.player import Player, Role, Team, PlayerStatus, DeathCause
from ..models.room import GameRoom
from ..models.game import GameSession, GamePhase, EventType
from ..models.events import EventService, EventVisibility
from .ai_manager import AIManager, AIMessage


class GameEngine:
    """Main game engine for werewolf game."""

    def __init__(
        self,
        room: GameRoom,
        ai_manager: AIManager,
        event_service: EventService,
        config: Optional[Dict[str, Any]] = None
    ):
        self.room = room
        self.ai_manager = ai_manager
        self.event_service = event_service
        self.config = config or self._get_default_config()

        self.session: Optional[GameSession] = None
        self.is_running = False
        self.phase_timer: Optional[asyncio.Task] = None

        # Game state callbacks
        self.on_phase_change: Optional[Callable[[GamePhase, GamePhase], None]] = None
        self.on_player_death: Optional[Callable[[Player, DeathCause], None]] = None
        self.on_game_end: Optional[Callable[[Team], None]] = None

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "max_duration": 3600,  # 1 hour in seconds
            "phase_timeouts": {
                "night": 30,
                "sheriff_election": 120,
                "day_discussion": 180,
                "voting": 60
            },
            "auto_progress": True,
            "enable_ai_delay": True
        }

    async def start_game(self) -> GameSession:
        """Start the game."""
        if self.is_running:
            raise RuntimeError("Game is already running")

        logger.info(f"Starting game in room {self.room.id}")

        try:
            # Create game session
            self.session = GameSession(self.room.id, self.room.players)

            # Initialize AI agents
            await self._initialize_ai_agents()

            # Assign roles
            self._assign_roles()

            # Shuffle and assign positions
            self.room.shuffle_players()

            # Create initial daily snapshot
            self.session.create_daily_snapshot()

            # Start game loop
            self.is_running = True

            # Start with night phase
            await self._start_night_phase()

            logger.info(f"Game {self.session.id} started successfully")
            return self.session

        except Exception as e:
            logger.error(f"Failed to start game: {e}")
            self.is_running = False
            raise

    async def _initialize_ai_agents(self) -> None:
        """Initialize AI agents for all players."""
        logger.info("Initializing AI agents for all players")

        for player in self.room.players:
            try:
                agent_id = await self.ai_manager.create_agent(player)
                player.agent_scope_id = agent_id
                logger.info(f"Created agent {agent_id} for player {player.name} as {player.role}")
            except Exception as e:
                logger.error(f"Failed to create agent for player {player.name}: {e}")
                raise

    def _assign_roles(self) -> None:
        """Assign roles to all players."""
        roles = self.room.game_config.role_distribution.roles_list
        random.shuffle(roles)

        for player, role in zip(self.room.players, roles):
            player.set_role(role)

        logger.info(f"Assigned roles: {len([r for r in roles if r == Role.WEREWOLF])} werewolves")

    async def _start_night_phase(self) -> None:
        """Start night phase."""
        logger.info(f"Starting night phase, day {self.session.day_count}")

        self.session.transition_to_phase(GamePhase.NIGHT)

        # Reset nightly abilities
        self._reset_nightly_abilities()

        # Get night actors
        night_actors = self._get_night_actors()

        # Process night actions sequentially
        await self._process_werewolf_actions(night_actors)
        await self._process_seer_action(night_actors)
        await self._process_witch_action(night_actors)

        # Resolve night deaths
        await self._resolve_night_deaths()

        # Check victory conditions
        if self._check_victory_conditions():
            await self._end_game()
            return

        # Move to day phase
        await self._start_day_phase()

    def _get_night_actors(self) -> List[Player]:
        """Get players who can act at night."""
        night_roles = [Role.WEREWOLF, Role.SEER, Role.WITCH]
        return [p for p in self.session.players if p.role in night_roles and p.is_alive]

    def _reset_nightly_abilities(self) -> None:
        """Reset abilities that refresh each night."""
        for player in self.session.players:
            player.reset_nightly_abilities()

    async def _process_werewolf_actions(self, night_actors: List[Player]) -> None:
        """Process werewolf actions."""
        werewolves = [p for p in night_actors if p.role == Role.WEREWOLF]
        if not werewolves:
            return

        logger.info(f"Processing werewolf actions for {len(werewolves)} werewolves")

        # Get potential targets
        targets = [p for p in self.session.players if p.role != Role.WEREWOLF and p.is_alive]
        if not targets:
            return

        # Select target (simplified logic)
        target = self._select_werewolf_target(werewolves, targets)

        # Update night actions
        self.session.night_actions.werewolf_target = {
            "player_id": target.id,
            "player_name": target.name,
            "agreed_by": [w.id for w in werewolves]
        }

        # Create event
        self.session.add_event(
            EventType.WEREWOLF_KILL,
            f"狼人选择击杀{target.name}",
            actor_name="狼人团队",
            target_id=target.id,
            target_name=target.name,
            is_public=False,
            visible_to_players=[w.id for w in werewolves]
        )

        logger.info(f"Werewolves selected target: {target.name}")

    def _select_werewolf_target(self, werewolves: List[Player], targets: List[Player]) -> Player:
        """Select werewolf target."""
        # Prioritize special roles
        priority_roles = [Role.SEER, Role.WITCH, Role.HUNTER]
        priority_targets = [t for t in targets if t.role in priority_roles]

        candidate_targets = priority_targets if priority_targets else targets
        return random.choice(candidate_targets)

    async def _process_seer_action(self, night_actors: List[Player]) -> None:
        """Process seer action."""
        seers = [p for p in night_actors if p.role == Role.SEER]
        if not seers:
            return

        seer = seers[0]
        targets = [p for p in self.session.players if p.id != seer.id and p.is_alive]
        if not targets:
            return

        target = random.choice(targets)
        result = "werewolf" if target.team == Team.WEREWOLF else "good"

        seer.seer_check(target.id, target.name, result)

        # Create event
        self.session.add_event(
            EventType.SEER_CHECK,
            f"预言家查验了{target.name}",
            actor_id=seer.id,
            actor_name=seer.name,
            target_id=target.id,
            target_name=target.name,
            details={"seer_check_result": result},
            is_public=False,
            visible_to_players=[seer.id]
        )

        logger.info(f"Seer {seer.name} checked {target.name}: {result}")

    async def _process_witch_action(self, night_actors: List[Player]) -> None:
        """Process witch action."""
        witches = [p for p in night_actors if p.role == Role.WITCH]
        if not witches:
            return

        witch = witches[0]
        werewolf_target = self.session.night_actions.werewolf_target

        if werewolf_target:
            logger.info(f"Witch {witch.name} sees werewolf target: {werewolf_target['player_name']}")

            # Simulate witch decision (50% save, 30% poison, 20% nothing)
            decision = random.random()

            if decision < 0.5 and witch.role_abilities.witch_has_antidote:
                # Use antidote
                witch.use_antidote()
                self.session.night_actions.witch_action = {
                    "action": "antidote",
                    "target_id": werewolf_target["player_id"],
                    "target_name": werewolf_target["player_name"]
                }

                self.session.add_event(
                    EventType.WITCH_SAVE,
                    f"女巫使用解药救活了{werewolf_target['player_name']}",
                    actor_id=witch.id,
                    actor_name="女巫",
                    target_id=werewolf_target["player_id"],
                    target_name=werewolf_target["player_name"],
                    is_public=False,
                    visible_to_players=[witch.id]
                )

                logger.info(f"Witch saved {werewolf_target['player_name']}")

            elif decision < 0.8 and witch.role_abilities.witch_has_poison:
                # Use poison
                poison_targets = [
                    p for p in self.session.players
                    if p.id != witch.id and p.is_alive() and
                    p.id != werewolf_target["player_id"]
                ]

                if poison_targets:
                    poison_target = random.choice(poison_targets)
                    witch.use_poison(poison_target.id)

                    self.session.night_actions.witch_action = {
                        "action": "poison",
                        "target_id": poison_target.id,
                        "target_name": poison_target.name
                    }

                    self.session.add_event(
                        EventType.WITCH_POISON,
                        f"女巫使用毒药毒死了{poison_target.name}",
                        actor_id=witch.id,
                        actor_name="女巫",
                        target_id=poison_target.id,
                        target_name=poison_target.name,
                        is_public=False,
                        visible_to_players=[witch.id]
                    )

                    logger.info(f"Witch poisoned {poison_target.name}")

    async def _resolve_night_deaths(self) -> None:
        """Resolve deaths from night actions."""
        deaths = []

        # Check werewolf kill
        werewolf_target = self.session.night_actions.werewolf_target
        witch_action = self.session.night_actions.witch_action

        if werewolf_target and witch_action and witch_action.get("action") != "antidote":
            deaths.append({
                "player_id": werewolf_target["player_id"],
                "player_name": werewolf_target["player_name"],
                "cause": DeathCause.WEREWOLF_KILL
            })

        # Check witch poison
        if witch_action and witch_action.get("action") == "poison":
            deaths.append({
                "player_id": witch_action["target_id"],
                "player_name": witch_action["target_name"],
                "cause": DeathCause.WITCH_POISON
            })

        # Process deaths
        for death in deaths:
            player = next((p for p in self.session.players if p.id == death["player_id"]), None)
            if player:
                player.set_dead(death["cause"])

                self.session.add_event(
                    EventType.PLAYER_DEATH,
                    f"{death['player_name']}在夜里死亡了",
                    target_id=death["player_id"],
                    target_name=death["player_name"],
                    details={"death_details": {"cause": death["cause"]}},
                    is_public=True
                )

                logger.info(f"{death['player_name']} died from {death['cause']}")

    async def _start_day_phase(self) -> None:
        """Start day phase."""
        logger.info(f"Starting day phase, day {self.session.day_count}")

        if self.session.day_count == 1:
            await self._start_sheriff_election()
        else:
            await self._start_day_discussion()

    async def _start_sheriff_election(self) -> None:
        """Start sheriff election."""
        logger.info("Starting sheriff election")

        self.session.transition_to_phase(GamePhase.SHERIFF_ELECTION)

        self.session.add_event(
            EventType.SHERIFF_ELECTION_START,
            "第一天警长竞选开始",
            is_public=True
        )

        # Simplified sheriff election: random selection
        alive_players = self.session.get_alive_players()
        sheriff = random.choice(alive_players)
        sheriff.set_as_sheriff()

        self.session.sheriff = {
            "player_id": sheriff.id,
            "player_name": sheriff.name,
            "has_last_word": True,
            "can_transfer": True
        }

        self.session.add_event(
            EventType.SHERIFF_ELECTED,
            f"{sheriff.name}当选为警长",
            target_id=sheriff.id,
            target_name=sheriff.name,
            is_public=True
        )

        logger.info(f"{sheriff.name} was elected as sheriff")

        # Move to discussion phase
        await self._start_day_discussion()

    async def _start_day_discussion(self) -> None:
        """Start day discussion."""
        logger.info(f"Starting day discussion, day {self.session.day_count}")

        self.session.transition_to_phase(GamePhase.DAY_DISCUSSION)

        # Simulate discussion with AI speeches
        await self._simulate_discussion()

        # Move to voting
        await self._start_voting()

    async def _simulate_discussion(self) -> None:
        """Simulate AI discussion (simplified)."""
        alive_players = self.session.get_alive_players()

        for player in alive_players:
            if self.config.get("enable_ai_delay", True):
                # Add delay based on AI response time
                await asyncio.sleep(random.uniform(1, 3))

            # Simulate speech generation
            speech = await self._generate_ai_speech(player)

            self.session.add_event(
                EventType.PLAYER_SPEAK,
                f"{player.name}: {speech}",
                actor_id=player.id,
                actor_name=player.name,
                is_public=True
            )

            logger.debug(f"{player.name} spoke: {speech[:50]}...")

    async def _generate_ai_speech(self, player: Player) -> str:
        """Generate AI speech content."""
        try:
            message = AIMessage(
                id=str(time.time()),
                type="player_speech",
                agent_id=player.agent_scope_id,
                agent_type="",  # Will be filled by AI manager
                timestamp=time.time(),
                content={
                    "content": "我分析了当前局势...",
                    "reasoning": "基于观察和行为分析",
                    "tone": "neutral",
                    "confidence": 0.8
                }
            )

            response = await self.ai_manager.send_message(player.agent_scope_id, message)

            if response.success and response.data:
                return response.data.get("speechContent", "我有一些想法...")
            else:
                return "我有一些想法需要分享..."

        except Exception as e:
            logger.error(f"Error generating speech for {player.name}: {e}")
            return "我有一些想法需要分享..."

    async def _start_voting(self) -> None:
        """Start voting phase."""
        logger.info(f"Starting voting phase, day {self.session.day_count}")

        self.session.transition_to_phase(GamePhase.VOTING)

        # Simulate voting
        await self._simulate_voting()

        # Check for hunter death
        await self._check_hunter_death()

        # Check victory conditions
        if self._check_victory_conditions():
            await self._end_game()
            return

        # Move to next night
        self.session.day_count += 1
        await self._start_night_phase()

    async def _simulate_voting(self) -> None:
        """Simulate AI voting."""
        alive_players = self.session.get_alive_players()
        votes = {}  # player_id -> (target_id, target_name, weight)

        for voter in alive_players:
            if self.config.get("enable_ai_delay", True):
                await asyncio.sleep(random.uniform(0.5, 2))

            # Generate vote decision
            vote = await self._generate_ai_vote(voter, alive_players)
            if vote:
                votes[voter.id] = vote

        # Count votes
        vote_counts = {}
        for voter_id, (target_id, target_name, weight) in votes.items():
            if target_id not in vote_counts:
                vote_counts[target_id] = {"name": target_name, "count": 0, "weight": 0}
            vote_counts[target_id]["count"] += 1
            vote_counts[target_id]["weight"] += weight

        # Find winner
        if vote_counts:
            eliminated_id = max(vote_counts.keys(), key=lambda k: vote_counts[k]["weight"])
            eliminated_data = vote_counts[eliminated_id]

            # Eliminate player
            eliminated_player = next(
                (p for p in self.session.players if p.id == eliminated_id),
                None
            )
            if eliminated_player:
                eliminated_player.set_dead(DeathCause.VOTE_OUT)

                self.session.add_event(
                    EventType.VOTE_RESULT,
                    f"{eliminated_data['name']}被投票出局",
                    target_id=eliminated_id,
                    target_name=eliminated_data['name'],
                    details={
                        "voting_details": {
                            "candidate_id": eliminated_id,
                            "vote_count": eliminated_data['weight'],
                            "sheriff_influence": False
                        }
                    },
                    is_public=True
                )

                logger.info(f"{eliminated_data['name']} was eliminated by vote")

    async def _generate_ai_vote(self, voter: Player, candidates: List[Player]) -> Optional[tuple]:
        """Generate AI vote decision."""
        try:
            targets = [p for p in candidates if p.id != voter.id]
            if not targets:
                return None

            target = random.choice(targets)
            confidence = 0.7 + (random.random() - 0.5) * 0.3

            return (target.id, target.name, voter.voting_weight)

        except Exception as e:
            logger.error(f"Error generating vote for {voter.name}: {e}")
            return None

    async def _check_hunter_death(self) -> None:
        """Check if hunter died and process shoot."""
        dead_players = [p for p in self.session.players if not p.is_alive]
        hunter = next((p for p in dead_players if p.role == Role.HUNTER), None)

        if hunter and hunter.role_abilities.hunter_death_cause != DeathCause.WITCH_POISON:
            await self._process_hunter_shoot(hunter)

    async def _process_hunter_shoot(self, hunter: Player) -> None:
        """Process hunter shoot action."""
        logger.info(f"Processing hunter shoot for {hunter.name}")

        alive_players = self.session.get_alive_players()
        if not alive_players:
            return

        # Generate shoot decision
        shoot_target = await self._generate_hunter_target(hunter, alive_players)
        if shoot_target:
            hunter.hunter_shoot(shoot_target.id)
            shoot_target.set_dead(DeathCause.HUNTER_SHOOT)

            self.session.add_event(
                EventType.HUNTER_SHOOT,
                f"猎人{hunter.name}开枪带走了{shoot_target.name}",
                actor_id=hunter.id,
                actor_name=hunter.name,
                target_id=shoot_target.id,
                target_name=shoot_target.name,
                is_public=True
            )

            logger.info(f"Hunter {hunter.name} shot {shoot_target.name}")

    async def _generate_hunter_target(self, hunter: Player, candidates: List[Player]) -> Optional[Player]:
        """Generate hunter target decision."""
        # Simplified: random target, real implementation would be more strategic
        return random.choice(candidates) if candidates else None

    def _check_victory_conditions(self) -> bool:
        """Check if victory conditions are met."""
        if not self.session:
            return False

        alive_players = self.session.get_alive_players()
        alive_werewolves = [p for p in alive_players if p.role == Role.WEREWOLF]
        alive_good = [p for p in alive_players if p.role != Role.WEREWOLF]
        alive_villagers = [p for p in alive_players if p.role == Role.VILLAGER]
        alive_special = [p for p in alive_players if p.role in [Role.SEER, Role.WITCH, Role.HUNTER]]

        # Werewolf victory conditions
        if (len(alive_werewolves) >= len(alive_good) or
            len(alive_villagers) == 0 or
            len(alive_special) == 0):
            self.session.winner = Team.WEREWOLF
            return True

        # Good team victory condition
        if len(alive_werewolves) == 0:
            self.session.winner = Team.GOOD
            return True

        return False

    async def _end_game(self) -> None:
        """End the game."""
        if not self.session:
            return

        logger.info(f"Game {self.session.id} ended. Winner: {self.session.winner}")

        self.is_running = False
        self.session.end_game()

        # Call callback
        if self.on_game_end:
            await self.on_game_end(self.session.winner)

    async def stop_game(self) -> None:
        """Stop the game."""
        logger.info(f"Stopping game {self.session.id if self.session else 'unknown'}")

        self.is_running = False

        if self.phase_timer:
            self.phase_timer.cancel()
            self.phase_timer = None

        if not self.session or self.session.ended_at:
            await self._end_game()

    def get_session(self) -> Optional[GameSession]:
        """Get current game session."""
        return self.session

    def get_current_state(self) -> Optional[dict]:
        """Get current game state."""
        if not self.session:
            return None

        return self.session.game_state.__dict__

    def get_game_summary(self) -> dict:
        """Get game summary."""
        if not self.session:
            return {"status": "not_started"}

        return {
            "session_id": self.session.id,
            "room_id": self.session.room_id,
            "status": "running" if self.is_running else "ended",
            "current_phase": self.session.current_phase,
            "day_count": self.session.day_count,
            "players": [p.get_private_info() for p in self.session.players],
            "winner": self.session.winner.value if self.session.winner else None,
            "start_time": self.session.phase_start_time.isoformat(),
            "end_time": self.session.ended_at.isoformat() if self.session.ended_at else None,
            "duration": (
                (self.session.ended_at - self.session.phase_start_time).total_seconds()
                if self.session.ended_at
                else (datetime.now() - self.session.phase_start_time).total_seconds()
            )
        }

    # Callback setters
    def set_phase_change_callback(self, callback: Callable[[GamePhase, GamePhase], None]) -> None:
        """Set phase change callback."""
        self.on_phase_change = callback

    def set_player_death_callback(self, callback: Callable[[Player, DeathCause], None]) -> None:
        """Set player death callback."""
        self.on_player_death = callback

    def set_game_end_callback(self, callback: Callable[[Team], None]) -> None:
        """Set game end callback."""
        self.on_game_end = callback