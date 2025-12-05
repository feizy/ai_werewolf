"""AI-powered game engine using AgentScope ReactAgents."""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from loguru import logger

from ..models.player import Player, Role, PlayerStatus
from ..models.room import GameRoom
from ..models.game import GameSession, GamePhase, EventType, Team
from ..models.events import EventService
from ..agents.agent_factory import AgentFactory
from ..agents.base_agent import GameState, AgentAction


class AIGameEngine:
    """AI-powered game engine that uses ReactAgents for all decisions."""

    def __init__(
        self,
        room: GameRoom,
        event_service: EventService
    ):
        self.room = room
        self.event_service = event_service

        # Game state
        self.session: Optional[GameSession] = None
        self.is_running = False
        self.phase_timer = None

        # AI agents
        self.agents: Dict[str, Any] = {}
        self.team_info: Dict[str, Any] = {}

        # Callbacks
        self.on_phase_change: Optional[Callable] = None
        self.on_player_death: Optional[Callable] = None
        self.on_game_end: Optional[Callable] = None

        # Game state tracking
        self.current_phase = GamePhase.NIGHT
        self.day_count = 1
        self.phase_start_time = datetime.now()

    async def initialize_game(self) -> None:
        """Initialize the game and create AI agents."""
        logger.info(f"Initializing AI-powered game for room {self.room.id}")

        try:
            # Assign roles to players
            self.room.assign_roles()

            # Create AI agents for all players
            agent_data = AgentFactory.create_all_agents(self.room.players)
            self.agents = agent_data["agents"]
            self.team_info = agent_data["team_info"]

            # Create game session
            self.session = GameSession(self.room.id, self.room.players)
            self.session.current_phase = GamePhase.NIGHT
            self.session.day_count = 1

            logger.info(f"Game initialized with {len(self.agents)} AI agents")

        except Exception as e:
            logger.error(f"Failed to initialize game: {e}")
            raise

    async def start_game(self) -> GameSession:
        """Start the game."""
        if not self.session:
            await self.initialize_game()

        logger.info(f"Starting AI-powered game {self.session.id}")

        self.is_running = True
        self.session.start_game()

        # Record game start event
        await self.event_service.record_event(
            session_id=self.session.id,
            event_type=EventType.GAME_START,
            content="游戏开始，所有玩家就位",
            phase=GamePhase.NIGHT,
            day_number=1
        )

        # Start first night phase
        await self._start_night_phase()

        return self.session

    async def _start_night_phase(self) -> None:
        """Start night phase."""
        logger.info(f"Starting night phase, day {self.day_count}")

        await self._transition_to_phase(GamePhase.NIGHT)

        # Get agents who act at night
        night_agents = self._get_night_agents()

        # Process night actions in order
        for agent_info in night_agents:
            await self._process_night_action(agent_info)

        # Transition to day phase
        await self._start_day_phase()

    def _get_night_agents(self) -> List[Dict[str, Any]]:
        """Get agents who act during night phase in order."""
        night_order = [Role.WEREWOLF, Role.SEER, Role.WITCH]
        night_agents = []

        for role in night_order:
            role_agents = [
                agent for agent_id, agent in self.agents.items()
                if agent.role == role and self._is_player_alive(agent_id)
            ]

            for agent in role_agents:
                night_agents.append({
                    "id": agent.player_id,
                    "agent": agent,
                    "role": role,
                    "available_actions": self._get_night_actions_for_role(role)
                })

        return night_agents

    async def _process_night_action(self, agent_info: Dict[str, Any]) -> None:
        """Process night action for an agent."""
        agent_id = agent_info["id"]
        agent = agent_info["agent"]
        role = agent_info["role"]
        available_actions = agent_info["available_actions"]

        try:
            logger.info(f"Processing night action for {role.value}: {agent.name}")

            # Create game state for agent
            game_state = await self._create_game_state(agent_id)

            # Get AI decision
            action = await agent.make_decision(game_state, available_actions)

            # Execute action
            await self._execute_agent_action(agent_id, action, GamePhase.NIGHT)

            # Record action event
            await self._record_agent_action(agent_id, action, GamePhase.NIGHT)

        except Exception as e:
            logger.error(f"Error processing night action for {agent.name}: {e}")

    async def _start_day_phase(self) -> None:
        """Start day phase."""
        logger.info(f"Starting day phase, day {self.day_count}")

        await self._transition_to_phase(GamePhase.DAY)

        # Process night results
        await self._process_night_results()

        # Check for game end
        if await self._check_game_end():
            return

        # Day discussion phase
        await self._process_day_discussion()

        # Start voting phase
        await self._start_voting_phase()

    async def _process_day_discussion(self) -> None:
        """Process day discussion with AI agents."""
        logger.info("Starting day discussion")

        alive_agents = [
            agent for agent_id, agent in self.agents.items()
            if self._is_player_alive(agent_id)
        ]

        discussion_rounds = 3  # Each agent speaks 3 times

        for round_num in range(discussion_rounds):
            logger.info(f"Discussion round {round_num + 1}")

            for agent in alive_agents:
                try:
                    game_state = await self._create_game_state(agent.player_id)
                    action = await agent.make_decision(game_state, ["speech"])

                    if action.action_type == "speech" and action.content:
                        await self._process_speech(agent.player_id, action.content)

                        # Small delay between speeches
                        await asyncio.sleep(1)

                except Exception as e:
                    logger.error(f"Error in speech for {agent.name}: {e}")

    async def _process_speech(self, player_id: str, content: str) -> None:
        """Process player speech."""
        player = self._get_player_by_id(player_id)
        if not player:
            return

        # Log speech to console with enhanced formatting
        role_info = f"({player.role.value})" if player.role else "(Unknown)"
        logger.info(f"💬 {player.name} {role_info} 发言: {content}")
        print(f"[发言] {player.name} {role_info}: {content}")

        # Record speech event
        await self.event_service.record_event(
            session_id=self.session.id,
            event_type=EventType.PLAYER_SPEECH,
            content=f"{player.name}: {content}",
            actor_id=player_id,
            phase=GamePhase.DAY,
            day_number=self.day_count,
            data={"speech_content": content}
        )

        # Broadcast speech to other agents for analysis
        await self._broadcast_speech_to_agents(player_id, content)

    async def _broadcast_speech_to_agents(self, speaker_id: str, content: str) -> None:
        """Broadcast speech to other agents for analysis."""
        for agent_id, agent in self.agents.items():
            if agent_id != speaker_id and self._is_player_alive(agent_id):
                # Agents can update their suspicions based on speeches
                await self._analyze_speech_for_agent(agent_id, speaker_id, content)

    async def _analyze_speech_for_agent(self, listener_id: str, speaker_id: str, content: str) -> None:
        """Agent analyzes speech from another player."""
        listener_agent = self.agents[listener_id]

        # Simple speech analysis - this would be enhanced with the agent's own analysis
        if "狼人" in content or "werewolf" in content.lower():
            # Player is actively looking for werewolves
            current_suspicion = listener_agent.suspicions.get(speaker_id, 0.1)
            listener_agent.suspicions[speaker_id] = max(0.0, current_suspicion - 0.1)

        # Update notes
        current_notes = listener_agent.player_notes.get(speaker_id, "")
        new_note = f"发言记录: {content[:50]}..."
        if new_note not in current_notes:
            listener_agent.update_player_notes(speaker_id, f"{current_notes} | {new_note}")

    async def _start_voting_phase(self) -> None:
        """Start voting phase."""
        logger.info("Starting voting phase")

        await self._transition_to_phase(GamePhase.VOTING)

        # Get votes from all alive agents
        votes = {}
        alive_agents = [
            agent for agent_id, agent in self.agents.items()
            if self._is_player_alive(agent_id)
        ]

        for agent in alive_agents:
            try:
                game_state = await self._create_game_state(agent.player_id)
                action = await agent.make_decision(game_state, ["vote"])

                if action.action_type == "vote" and action.target:
                    votes[agent.player_id] = action.target
                    logger.info(f"{agent.name} votes for {action.target}")

            except Exception as e:
                logger.error(f"Error getting vote from {agent.name}: {e}")

        # Process voting results
        await self._process_voting_results(votes)

    async def _process_voting_results(self, votes: Dict[str, str]) -> None:
        """Process voting results and eliminate player."""
        if not votes:
            return

        # Count votes
        vote_counts = {}
        for target_id in votes.values():
            vote_counts[target_id] = vote_counts.get(target_id, 0) + 1

        if not vote_counts:
            return

        # Find player with most votes
        eliminated_id = max(vote_counts.keys(), key=lambda k: vote_counts[k])
        eliminated_player = self._get_player_by_id(eliminated_id)

        if eliminated_player and vote_counts[eliminated_id] > len(votes) // 2:
            await self._eliminate_player(eliminated_id, "投票出局")

            # Check for hunter ability
            if eliminated_player.role == Role.HUNTER:
                await self._process_hunter_shot(eliminated_id)

        # Check for game end
        if not await self._check_game_end():
            # Continue to next night
            self.day_count += 1
            await self._start_night_phase()

    async def _execute_agent_action(self, agent_id: str, action: AgentAction, phase: GamePhase) -> None:
        """Execute agent action."""
        logger.info(f"Executing {action.action_type} for agent {agent_id}")

        if action.action_type == "werewolf_kill" and action.target:
            await self._execute_werewolf_kill(agent_id, action.target)

        elif action.action_type == "seer_check" and action.target:
            await self._execute_seer_check(agent_id, action.target)

        elif action.action_type == "witch_save" and action.target:
            await self._execute_witch_save(agent_id, action.target)

        elif action.action_type == "witch_poison" and action.target:
            await self._execute_witch_poison(agent_id, action.target)

        elif action.action_type == "hunter_shoot" and action.target:
            await self._execute_hunter_shot(agent_id, action.target)

    async def _execute_werewolf_kill(self, werewolf_id: str, target_id: str) -> None:
        """Execute werewolf kill action."""
        target_player = self._get_player_by_id(target_id)
        if target_player:
            # Log werewolf kill to console
            logger.info(f"🌙 狼人击杀目标: {target_player.name}")
            print(f"[狼人击杀] 目标: {target_player.name}")

            # Mark for death (will be processed in day phase)
            self.session.night_actions.werewolf_target = {
                "player_id": target_id,
                "player_name": target_player.name,
                "action_by": werewolf_id
            }

    async def _execute_seer_check(self, seer_id: str, target_id: str) -> None:
        """Execute seer check action."""
        target_player = self._get_player_by_id(target_id)
        seer_agent = self.agents[seer_id]

        if target_player:
            result = "werewolf" if target_player.role == Role.WEREWOLF else "good"
            result_text = "狼人" if result == "werewolf" else "好人"

            # Log seer check to console
            logger.info(f"🔮 预言家查验了 {target_player.name}，结果是: {result_text}")
            print(f"[预言家查验] 查验目标: {target_player.name} → 结果: {result_text}")

            # Update seer's knowledge
            seer_agent.update_player_notes(
                target_id,
                f"查验结果: {result}"
            )
            seer_agent.suspicions[target_id] = 1.0 if result == "werewolf" else 0.0

            # Record check event
            await self.event_service.record_event(
                session_id=self.session.id,
                event_type=EventType.SEER_CHECK,
                content=f"预言家查验了{target_player.name}，结果是{result}",
                actor_id=seer_id,
                target_id=target_id,
                phase=GamePhase.NIGHT,
                day_number=self.day_count,
                data={"result": result},
                visible_to_players=[seer_id]
            )

    async def _execute_witch_poison(self, witch_id: str, target_id: str) -> None:
        """Execute witch poison action."""
        target_player = self._get_player_by_id(target_id)
        witch_agent = self.agents[witch_id]

        if target_player:
            # Log witch poison to console
            logger.info(f"🧪 女巫使用毒药: {target_player.name}")
            print(f"[女巫毒药] 目标: {target_player.name}")

            # Mark for death
            self.session.night_actions.witch_action = {
                "action": "poison",
                "target_id": target_id,
                "target_name": target_player.name
            }

            # Update witch's knowledge
            witch_agent.update_player_notes(
                target_id,
                "使用毒药击杀"
            )

            # Record poison event
            await self.event_service.record_event(
                session_id=self.session.id,
                event_type=EventType.WITCH_POISON,
                content=f"女巫使用毒药击杀了{target_player.name}",
                actor_id=witch_id,
                target_id=target_id,
                phase=GamePhase.NIGHT,
                day_number=self.day_count,
                data={"action": "poison"}
            )

    async def _execute_hunter_shot(self, hunter_id: str, target_id: str) -> None:
        """Execute hunter shot action."""
        target_player = self._get_player_by_id(target_id)
        hunter_agent = self.agents[hunter_id]

        if target_player:
            # Log hunter shot to console
            logger.info(f"🔫 猎人开枪: {target_player.name}")
            print(f"[猎人开枪] 目标: {target_player.name}")

            # Kill target immediately
            target_player.set_dead("hunter_shot")

            # Update hunter's knowledge
            hunter_agent.update_player_notes(
                target_id,
                "开枪击杀"
            )

            # Record shot event
            await self.event_service.record_event(
                session_id=self.session.id,
                event_type=EventType.HUNTER_SHOOT,
                content=f"猎人开枪击杀了{target_player.name}",
                actor_id=hunter_id,
                target_id=target_id,
                phase=GamePhase.NIGHT,
                day_number=self.day_count,
                data={"action": "shoot"}
            )

    async def _process_night_results(self) -> None:
        """Process night phase results."""
        # Check werewolf kill
        werewolf_target = self.session.night_actions.werewolf_target
        if werewolf_target:
            target_id = werewolf_target["player_id"]

            # Check if witch saved the target
            if not self.session.night_actions.witch_save:
                await self._eliminate_player(target_id, "狼人击杀")

    async def _eliminate_player(self, player_id: str, reason: str) -> None:
        """Eliminate a player from the game."""
        player = self._get_player_by_id(player_id)
        if not player or player.status != PlayerStatus.ALIVE:
            return

        player.status = PlayerStatus.DEATH
        player.death_cause = reason

        # Enhanced elimination log
        role_info = f"({player.role.value})" if player.role else "(Unknown)"
        logger.info(f"💀 玩家淘汰: {player.name} {role_info} - {reason}")
        print(f"[玩家淘汰] {player.name} {role_info} - {reason}")

        # Record elimination event
        await self.event_service.record_event(
            session_id=self.session.id,
            event_type=EventType.PLAYER_DEATH,
            content=f"{player.name} 被淘汰：{reason}",
            actor_id=player_id,
            phase=self.session.current_phase,
            day_number=self.day_count
        )

        # Call death callback
        if self.on_player_death:
            await self.on_player_death(player, reason)

    async def _process_hunter_shot(self, hunter_id: str) -> None:
        """Process hunter's final shot."""
        hunter_agent = self.agents[hunter_id]

        # Get hunter's decision for final shot
        game_state = await self._create_game_state(hunter_id)
        action = await hunter_agent.make_decision(game_state, ["hunter_shoot"])

        if action.action_type == "hunter_shoot" and action.target:
            await self._eliminate_player(action.target, "猎人开枪")

    def _get_night_actions_for_role(self, role: Role) -> List[str]:
        """Get available actions for a role during night."""
        actions = {
            Role.WEREWOLF: ["werewolf_kill"],
            Role.SEER: ["seer_check"],
            Role.WITCH: ["witch_save", "witch_poison", "wait"],
            Role.HUNTER: ["wait"],
            Role.VILLAGER: ["wait"]
        }
        return actions.get(role, ["wait"])

    async def _create_game_state(self, agent_id: str) -> GameState:
        """Create game state for an agent."""
        alive_players = []
        for player in self.room.players:
            if player.status == PlayerStatus.ALIVE:
                player_info = {
                    "id": player.id,
                    "name": player.name,
                    "position": player.position
                }

                # Add role info for same team members
                if player.id == agent_id:
                    player_info["my_role"] = player.role.value
                elif (self._is_werewolf(agent_id) and player.role == Role.WEREWOLF):
                    player_info["my_role"] = "队友"

                alive_players.append(player_info)

        return GameState(
            phase=self.session.current_phase.value,
            day_count=self.day_count,
            alive_players=alive_players,
            my_role=self._get_agent_role(agent_id),
            my_status="alive",
            known_info=self.agents[agent_id].player_notes,
            recent_events=self._get_recent_events(),
            available_actions=self._get_available_actions(agent_id)
        )

    def _is_werewolf(self, agent_id: str) -> bool:
        """Check if agent is a werewolf."""
        agent = self.agents.get(agent_id)
        return agent.role == Role.WEREWOLF if agent else False

    def _get_agent_role(self, agent_id: str) -> Optional[str]:
        """Get role for agent."""
        agent = self.agents.get(agent_id)
        return agent.role.value if agent else None

    def _get_recent_events(self) -> List[Dict[str, Any]]:
        """Get recent game events."""
        # Return recent events from session
        if not self.session:
            return []

        recent_events = []
        for event in self.session.events[-10:]:  # Last 10 events
            if event.is_public:  # Only include public events
                recent_events.append({
                    "type": event.event_type.value,
                    "content": event.content,
                    "day": event.day_number
                })

        return recent_events

    def _get_available_actions(self, agent_id: str) -> List[str]:
        """Get available actions for an agent."""
        agent = self.agents.get(agent_id)
        if not agent:
            return []

        if self.session.current_phase == GamePhase.NIGHT:
            return self._get_night_actions_for_role(agent.role)
        elif self.session.current_phase == GamePhase.DAY:
            return ["speech"]
        elif self.session.current_phase == GamePhase.VOTING:
            return ["vote"]

        return ["wait"]

    async def _transition_to_phase(self, new_phase: GamePhase) -> None:
        """Transition to a new phase."""
        old_phase = self.session.current_phase
        self.session.current_phase = new_phase
        self.phase_start_time = datetime.now()

        # Enhanced phase transition log
        phase_names = {
            GamePhase.NIGHT: "夜晚",
            GamePhase.SHERIFF_ELECTION: "警长竞选",
            GamePhase.DAY_DISCUSSION: "白天讨论",
            GamePhase.VOTING: "投票",
            GamePhase.GAME_OVER: "游戏结束"
        }

        old_phase_name = phase_names.get(old_phase, old_phase.value)
        new_phase_name = phase_names.get(new_phase, new_phase.value)

        logger.info(f"🔄 阶段转换: {old_phase_name} → {new_phase_name} (第{self.day_count}天)")
        print(f"[阶段转换] {old_phase_name} → {new_phase_name} (第{self.day_count}天)")

        # Call phase change callback
        if self.on_phase_change:
            await self.on_phase_change(old_phase, new_phase)

        # Record phase change event
        await self.event_service.record_event(
            session_id=self.session.id,
            event_type=EventType.PHASE_CHANGE,
            content=f"阶段变化: {old_phase.value} -> {new_phase.value}",
            phase=new_phase,
            day_number=self.day_count
        )

    async def _check_game_end(self) -> bool:
        """Check if the game has ended."""
        if not self.session:
            return False

        alive_werewolves = [
            p for p in self.room.players
            if p.role == Role.WEREWOLF and p.status == PlayerStatus.ALIVE
        ]
        alive_others = [
            p for p in self.room.players
            if p.role != Role.WEREWOLF and p.status == PlayerStatus.ALIVE
        ]

        if len(alive_werewolves) == 0:
            await self._end_game(Team.VILLAGER, "所有狼人被消灭")
            return True
        elif len(alive_werewolves) >= len(alive_others):
            await self._end_game(Team.WEREWOLF, "狼人数量大于等于好人")
            return True

        return False

    async def _end_game(self, winner: Team, reason: str) -> None:
        """End the game."""
        logger.info(f"Game ended. Winner: {winner.value}, Reason: {reason}")

        self.session.winner = winner
        self.session.end_reason = reason
        self.session.ended_at = datetime.now()
        self.is_running = False

        # Record game end event
        await self.event_service.record_event(
            session_id=self.session.id,
            event_type=EventType.GAME_END,
            content=f"游戏结束！{winner.value}阵营获胜！原因：{reason}",
            phase=self.session.current_phase,
            day_number=self.day_count
        )

        # Call game end callback
        if self.on_game_end:
            await self.on_game_end(winner)

    def _is_player_alive(self, player_id: str) -> bool:
        """Check if a player is alive."""
        player = self._get_player_by_id(player_id)
        return player and player.status == PlayerStatus.ALIVE

    def _get_player_by_id(self, player_id: str) -> Optional[Player]:
        """Get player by ID."""
        return next((p for p in self.room.players if p.id == player_id), None)

    async def _record_agent_action(self, agent_id: str, action: AgentAction, phase: GamePhase) -> None:
        """Record agent action in event log."""
        player = self._get_player_by_id(agent_id)
        if not player:
            return

        content = f"{player.name} 执行行动: {action.action_type}"
        if action.target:
            target_player = self._get_player_by_id(action.target)
            content += f" -> {target_player.name if target_player else '未知'}"

        await self.event_service.record_event(
            session_id=self.session.id,
            event_type=EventType.ROLE_ACTION,
            content=content,
            actor_id=agent_id,
            target_id=action.target,
            phase=phase,
            day_number=self.day_count,
            data={
                "action_type": action.action_type,
                "reasoning": action.reasoning,
                "confidence": action.confidence,
                "metadata": action.metadata
            }
        )

    # Callback setters
    def set_phase_change_callback(self, callback: Callable[[GamePhase, GamePhase], None]) -> None:
        """Set phase change callback."""
        self.on_phase_change = callback

    def set_player_death_callback(self, callback: Callable[[Player, str], None]) -> None:
        """Set player death callback."""
        self.on_player_death = callback

    def set_game_end_callback(self, callback: Callable[[Team], None]) -> None:
        """Set game end callback."""
        self.on_game_end = callback

    def get_session(self) -> Optional[GameSession]:
        """Get current game session."""
        return self.session

    def get_game_summary(self) -> Dict[str, Any]:
        """Get game summary."""
        if not self.session:
            return {"status": "not_started"}

        return {
            "session_id": self.session.id,
            "room_id": self.session.room_id,
            "status": "running" if self.is_running else "ended",
            "current_phase": self.session.current_phase.value,
            "day_count": self.session.day_count,
            "players": [p.get_private_info() for p in self.room.players],
            "winner": self.session.winner.value if self.session.winner else None,
            "start_time": self.session.phase_start_time.isoformat(),
            "end_time": self.session.ended_at.isoformat() if self.session.ended_at else None,
            "agent_info": {
                player_id: agent.get_agent_info()
                for player_id, agent in self.agents.items()
            }
        }