"""AI-powered game engine using AgentScope ReactAgents."""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Callable, TYPE_CHECKING
from datetime import datetime

from loguru import logger

from ..models.player import Player, Role, PlayerStatus
from ..models.room import GameRoom
from ..models.game import GameSession, GamePhase, EventType, Team
from ..models.events import EventService
from ..agents.agent_factory import AgentFactory
from ..agents.base_agent import GameState, AgentAction
from agentscope.message import Msg



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

    def create_event(
        self,
        event_type: EventType,
        content: str,
        actor_id: Optional[str] = None,
        actor_name: Optional[str] = None,
        target_id: Optional[str] = None,
        target_name: Optional[str] = None,
        is_public: bool = True,
        visible_to_roles: Optional[List[Role]] = None,
        visible_to_players: Optional[List[str]] = None
    ) -> None:
        """Create and store event using EventService."""
        if not self.session:
            logger.warning("Cannot create event: no session available")
            return

        # Create event using EventService
        from ..models.events import EventVisibility
        self.event_service.create_event(
            session_id=self.session.id,
            event_type=event_type,
            phase=self.current_phase,
            day_count=self.day_count,
            content=content,
            actor_id=actor_id,
            actor_name=actor_name,
            target_id=target_id,
            target_name=target_name,
            visibility=EventVisibility(
                public=is_public,
                visible_to_roles=[r.value for r in visible_to_roles] if visible_to_roles else [],
                visible_to_players=visible_to_players or []
            )
        )

        # Also add to session for compatibility (optional)
        self.session.add_event(
            event_type=event_type,
            content=content,
            actor_id=actor_id,
            actor_name=actor_name,
            target_id=target_id,
            target_name=target_name,
            is_public=is_public,
            visible_to_roles=visible_to_roles,
            visible_to_players=visible_to_players
        )

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

            # Initialize all agents (create AgentScope ReactAgent instances)
            logger.info("Initializing AgentScope agents...")
            for agent_id, agent in self.agents.items():
                try:
                    await agent.initialize()
                    logger.debug(f"Initialized agent for {agent.name}")
                except Exception as e:
                    logger.error(f"Failed to initialize agent for {agent.name}: {e}")

            # Create game session
            self.session = GameSession(self.room.id, self.room.players)
            self.session.current_phase = GamePhase.INIT
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
            content="Players are ready, game starts!",
            phase=GamePhase.INIT,
            day_number=1
        )

        # Start first night phase
        await self._start_night_phase()

        return self.session

    async def _start_night_phase(self) -> None:
        """Start night phase."""
        logger.info(f"Starting night phase, day {self.day_count}")
        if self.day_count > 1:
            #总结上一日发言，存入event_service
            daily_summary = await self._get_daily_summary()
            await self.event_service.record_event(
                session_id=self.session.id,
                event_type=EventType.DAILY_SUMMARY,
                content=daily_summary,
                phase=GamePhase.DAY_DISCUSSION,
                day_number=self.day_count-1
            )
            #clear all players' memory
            for agent_id, agent in self.agents.items():
                await agent.agent.memory.clear()
            #取出所有之前日的summary，存入所有玩家memory
            for event in self.event_service.get_session_events(self.session.id):
                if event.event_type == EventType.DAILY_SUMMARY:
                    msg = Msg(role="system", content=event.content, name="system")
                    for agent_id, agent in self.agents.items():
                        if agent.agent:
                            try:
                                await agent.agent.memory.add(msg)
                            except Exception as e:
                                logger.warning(f"Failed to add memory to agent {agent.name}: {e}")

        await self._transition_to_phase(GamePhase.NIGHT)

        # Night actions in order:
        # 1. Werewolves discuss and vote on kill target
        await self._process_werewolf_night()
        
        # 2. Seer checks one player
        await self._process_seer_night()
        
        # 3. Witch decides to save/poison (knows werewolf target)
        await self._process_witch_night()

        # Transition to day phase
        await self._start_day_phase()

    async def _process_werewolf_night(self) -> None:
        """Process werewolf night phase - brief discussion, leader decides."""
        werewolf_agents = [
                agent for agent_id, agent in self.agents.items()
            if agent.role == Role.WEREWOLF and self._is_player_alive(agent_id)
            ]

        if not werewolf_agents:
            return
        
        # logger.info("🐺 狼人睁眼，开始商议击杀目标")
        print("[狼人夜晚] 狼人睁眼，开始商议")
        await self.event_service.record_event(
            session_id=self.session.id,
            event_type=EventType.WEREWOLF_DISCUSS,
            content="狼人睁眼，开始商议击杀目标",
            phase=GamePhase.NIGHT,
            day_number=self.day_count
        )
        # Get non-werewolf alive players as potential targets
        potential_targets = [
            p for p in self.room.players 
            if p.status == PlayerStatus.ALIVE and p.role != Role.WEREWOLF
        ]
        
        # Each werewolf shares: 1. target suggestion, 2. brief reason
        # All wolves can see previous wolves' messages
        wolf_messages = []  # List of {"wolf": name, "target": target_name, "reason": reason}
        for i, agent in enumerate(werewolf_agents):
            try:
                game_state = await self._create_game_state(agent.player_id)
                game_state.known_info["potential_targets"] = [
                    {"position": p.position, "name": p.name}
                    for p in potential_targets
                ]
                # Share all previous wolves' messages
                game_state.known_info["wolf_discussion"] = wolf_messages.copy()
                action = await agent.make_decision(game_state, ["werewolf_discuss"])
                if action and action.target:
                    target_player = self._get_player_by_id(action.target)
                    if target_player:
                        # Extract brief reason from content or reasoning
                        reason = action.reasoning or action.content or "无理由"
                        if len(reason) > 50:
                            reason = reason[:50] + "..."

                        wolf_messages.append({
                            "wolf": agent.name,
                            "target": target_player.name,
                            "reason": reason
                        })

                        print(f"[调试] 记录 {agent.name} 的建议击杀事件")
                        await self.event_service.record_event(
                            session_id=self.session.id,
                            event_type=EventType.WEREWOLF_DISCUSS,
                            content=f"{agent.name} 建议击杀 {target_player.name}，理由: {reason}",
                            phase=GamePhase.NIGHT,
                            day_number=self.day_count,
                            actor_id=agent.player_id,
                            actor_name=agent.name,
                            target_id=target_player.id,
                            target_name=target_player.name)
                        # logger.info(f"🐺 {agent.name}: 建议击杀 {target_player.name}，理由: {reason}")
                        print(f"[狼人] {agent.name}: 建议击杀 {target_player.name}，理由: {reason}")
                    
            except Exception as e:
                logger.error(f"Error in werewolf discussion for {agent.name}: {e}")
        
        # First werewolf (leader) makes final decision based on all discussion
        leader = werewolf_agents[0]
        try:
            game_state = await self._create_game_state(leader.player_id)
            game_state.known_info["wolf_discussion"] = wolf_messages  # All wolves' messages with reasons
            game_state.known_info["potential_targets"] = [
                {"position": p.position, "name": p.name} 
                for p in potential_targets
            ]
            
            action = await leader.make_decision(game_state, ["werewolf_kill"])
            
            if action.target:
                target_player = self._get_player_by_id(action.target)
                if target_player and target_player.role != Role.WEREWOLF:
                    # logger.info(f"🐺 狼人决定击杀: {target_player.name}")
                    print(f"[狼人击杀] 狼人决定击杀: {target_player.name}")
                    
                    self.session.night_actions.werewolf_target = {
                        "player_id": target_player.id,
                        "player_name": target_player.name
                    }
                    #添加到event_service
                    await self.event_service.record_event(
                        session_id=self.session.id,
                        event_type=EventType.WEREWOLF_KILL,
                        content=f"狼人决定击杀: {target_player.name}",
                        phase=GamePhase.NIGHT,
                        day_number=self.day_count,
                        actor_id=leader.player_id,
                        actor_name=leader.name,
                        target_id=target_player.id,
                        target_name=target_player.name
                    )
        except Exception as e:
            logger.error(f"Error in werewolf kill decision: {e}")
    
    async def _process_seer_night(self) -> None:
        """Process seer night action."""
        seer_agents = [
            agent for agent_id, agent in self.agents.items()
            if agent.role == Role.SEER and self._is_player_alive(agent_id)
        ]
        
        for agent in seer_agents:
            try:
                # logger.info(f"🔮 预言家 {agent.name} 睁眼查验")
                print(f"[预言家] {agent.name} 睁眼查验")
                
                game_state = await self._create_game_state(agent.player_id)
                action = await agent.make_decision(game_state, ["seer_check"])
                
                if action.target:
                    await self._execute_seer_check(agent.player_id, action.target)
            except Exception as e:
                logger.error(f"Error in seer check for {agent.name}: {e}")
    
    async def _process_witch_night(self) -> None:
        """Process witch night action."""
        witch_agents = [
            agent for agent_id, agent in self.agents.items()
            if agent.role == Role.WITCH and self._is_player_alive(agent_id)
        ]
        
        for agent in witch_agents:
            try:
                # logger.info(f"🧪 女巫 {agent.name} 睁眼")
                print(f"[女巫] {agent.name} 睁眼")
                
                game_state = await self._create_game_state(agent.player_id)
                
                # Witch knows who was killed by werewolves
                werewolf_target = self.session.night_actions.werewolf_target
                if werewolf_target:
                    game_state.known_info["werewolf_kill_target"] = {
                        "player_id": werewolf_target["player_id"],
                        "player_name": werewolf_target["player_name"]
                    }
                    # logger.info(f"🧪 女巫得知 {werewolf_target['player_name']} 被狼人击杀")
                    print(f"[女巫] 得知 {werewolf_target['player_name']} 被狼人击杀")
                    await self.event_service.record_event(
                        session_id=self.session.id,
                        event_type=EventType.WITCH_SAVE,
                        content=f"女巫得知 {werewolf_target['player_name']} 被狼人击杀",
                        phase=GamePhase.NIGHT,
                        day_number=self.day_count,
                        actor_id=agent.player_id,
                        actor_name=agent.name,
                        target_id=werewolf_target["player_id"],
                        target_name=werewolf_target["player_name"])
                # Check witch abilities
                player = self._get_player_by_id(agent.player_id)
                game_state.known_info["has_antidote"] = player.role_abilities.witch_has_antidote if player else False
                game_state.known_info["has_poison"] = player.role_abilities.witch_has_poison if player else False
                
                # Can self-save only on first night
                can_self_save = self.day_count == 1 and werewolf_target and werewolf_target["player_id"] == agent.player_id
                game_state.known_info["can_self_save"] = can_self_save
                
                action = await agent.make_decision(game_state, ["witch_save", "witch_poison", "wait"])
                
                if action.action_type == "witch_save" and game_state.known_info.get("has_antidote"):
                    # Save the werewolf target
                    if werewolf_target:
                        await self._execute_witch_save(agent.player_id, werewolf_target)
                        await self.event_service.record_event(
                            session_id=self.session.id,
                            event_type=EventType.WITCH_SAVE,
                            content=f"女巫使用解药救活了{werewolf_target['player_name']}.内心活动：{action.reasoning}",
                            actor_id=agent.player_id,
                            target_id=werewolf_target['player_id'],
                            actor_name=agent.name,
                            target_name=werewolf_target['player_name'],
                            phase=GamePhase.NIGHT,
                            day_number=self.day_count,
                            data={"action": "save"}
                        )
                elif action.action_type == "witch_poison" and action.target and game_state.known_info.get("has_poison"):
                    # Poison someone - delegate to execution method
                    target_player = self._get_player_by_id(action.target)
                    if target_player:
                        await self._execute_witch_poison(agent.player_id, target_player.id)
                        await self.event_service.record_event(
                            session_id=self.session.id,
                            event_type=EventType.WITCH_POISON,
                            content=f"女巫使用毒药击杀了{target_player.name}.内心活动：{action.reasoning}",
                            actor_id=agent.player_id,
                            target_id=target_player.id,
                            actor_name=agent.name,
                            target_name=target_player.name,
                            phase=GamePhase.NIGHT,
                            day_number=self.day_count,
                            data={"action": "poison"}
                        )
                else:
                    # logger.info(f"🧪 女巫选择不使用药水")
                    print(f"[女巫] 女巫选择不使用药水")
                    await self.event_service.record_event(
                        session_id=self.session.id,
                        event_type=EventType.WITCH_SAVE,
                        content=f"女巫选择不使用药水.内心活动：{action.reasoning}",
                        phase=GamePhase.NIGHT,
                        day_number=self.day_count,
                        actor_id=agent.player_id,
                        actor_name=agent.name
                    )

            except Exception as e:
                    logger.error(f"Error in witch action for {agent.name}: {e}")

    async def _start_day_phase(self) -> None:
        """Start day phase."""
        logger.info(f"Starting day phase, day {self.day_count}")

        # Process night results first (determine who died)
        night_deaths = await self._process_night_results()

        # Check for game end
        if await self._check_game_end():
            return

        # Announce night deaths
        await self._announce_night_deaths(night_deaths)

        # Dead players give last words
        for death in night_deaths:
            await self._process_last_words(death["player_id"], "夜晚死亡")

        # Sheriff election (only on day 1)
        if self.day_count == 1:
            await self._process_sheriff_election()

        await self._transition_to_phase(GamePhase.DAY_DISCUSSION)

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

        # Standard werewolf rules: 1 round of discussion per day
        discussion_rounds = 1

        for round_num in range(discussion_rounds):
            logger.info(f"Discussion round {round_num + 1}")

            for agent in alive_agents:
                try:
                    game_state = await self._create_game_state(agent.player_id)
                    action = await agent.make_decision(game_state, ["speech"])

                    if action.action_type == "speech" and action.content:
                        await self._process_speech(agent.player_id, action.content)

                        # Small delay between speeches
                        await asyncio.sleep(0.5)

                except Exception as e:
                    logger.error(f"Error in speech for {agent.name}: {e}")

    async def _process_speech(self, player_id: str, content: str) -> None:
        """Process player speech."""
        player = self._get_player_by_id(player_id)
        if not player:
            return

        # Log speech to console with enhanced formatting
        role_info = f"({player.role.value})" if player.role else "(Unknown)"
        # logger.info(f"💬 {player.name} {role_info} 发言: {content}")
        print(f"[发言] {player.name} {role_info}: {content}")

        # Record speech event
        await self.event_service.record_event(
            session_id=self.session.id,
            event_type=EventType.PLAYER_SPEECH,
            content=f"{player.name}: {content}",
            actor_id=player_id,
            phase=GamePhase.DAY_DISCUSSION,
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
        speaker_name = self._get_player_by_id(speaker_id).name
        content = f"{speaker_name}发言：{content}"
        msg = Msg(role="system", name=speaker_name, content=content)
        try:
            if listener_agent.agent and getattr(listener_agent.agent, "memory", None):
                await listener_agent.agent.memory.add(msg)
        except Exception as e:
            logger.warning(f"Failed to add speech to memory for {listener_id}: {e}")

        # Simple speech analysis - this would be enhanced with the agent's own analysis
        # if "狼人" in content or "werewolf" in content.lower():
        #     # Player is actively looking for werewolves
        #     current_suspicion = listener_agent.suspicions.get(speaker_id, 0.1)
        #     listener_agent.suspicions[speaker_id] = max(0.0, current_suspicion - 0.1)

        # # Update notes
        # current_notes = listener_agent.player_notes.get(speaker_id, "")
        # new_note = f"发言记录: {content[:50]}..."
        # if new_note not in current_notes:
        #     listener_agent.update_player_notes(speaker_id, f"{current_notes} | {new_note}")

    async def _start_voting_phase(self) -> None:
        """Start voting phase."""
        logger.info("Starting voting phase")
        voting_record={}
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
                    voting_record[agent.name] = self._get_player_by_id(action.target).name
                    await self.event_service.record_event(
                            session_id=self.session.id,
                            event_type=EventType.PLAYER_VOTE,
                            content=f"{agent.name} 投票给 {action.target}",
                            phase=GamePhase.VOTING,
                            day_number=self.day_count,
                            actor_id=agent.player_id,
                            actor_name=agent.name,
                            target_id=action.target,
                            target_name=self._get_player_by_id(action.target).name
                    )
            except Exception as e:
                logger.error(f"Error getting vote from {agent.name}: {e}")
        voting_name = f"第{self.day_count}天白天放逐投票"
        for agent in alive_agents:
            agent.update_voting_history(voting_name, voting_record)

        # Process voting results
        await self._process_voting_results(votes)

    async def _process_voting_results(self, votes: Dict[str, str]) -> None:
        """Process voting results and eliminate player."""
        if not votes:
            # logger.info("⚖️ 无人投票，无人被放逐")
            print("[投票结果] 无人投票，无人被放逐")
            # Continue to next night
            if not await self._check_game_end():
                self.day_count += 1
                await self._start_night_phase()
            return

        # Count votes
        vote_counts = {}
        for target_id in votes.values():
            # Resolve target to player ID
            target_player = self._get_player_by_id(target_id)
            if target_player:
                actual_id = target_player.id
                vote_counts[actual_id] = vote_counts.get(actual_id, 0) + 1

        if not vote_counts:
            if not await self._check_game_end():
                self.day_count += 1
                await self._start_night_phase()
            return

        # Display vote counts
        # logger.info("⚖️ 投票统计:")
        print("[投票统计]")
        for player_id, count in vote_counts.items():
            player = self._get_player_by_id(player_id)
            if player:
                logger.info(f"  {player.name}: {count} 票")
                print(f"  {player.name}: {count} 票")

        # Find player with most votes
        eliminated_id = max(vote_counts.keys(), key=lambda k: vote_counts[k])
        eliminated_player = self._get_player_by_id(eliminated_id)
        max_votes = vote_counts[eliminated_id]

        # Check for tie
        tied_players = [pid for pid, count in vote_counts.items() if count == max_votes]
        if len(tied_players) > 1:
            # logger.info("⚖️ 平票，无人被放逐")
            print("[投票结果] 平票，无人被放逐")
            # TODO: Could add PK round here
        elif eliminated_player and max_votes > 0:
            # logger.info(f"⚖️ {eliminated_player.name} 被放逐出局")
            print(f"[投票结果] {eliminated_player.name} 被放逐出局")
            
            # Last words before elimination
            await self._process_last_words(eliminated_id, "投票放逐")
            
            await self._eliminate_player(eliminated_id, "投票出局")

            # Check for hunter ability (hunter can shoot when voted out)
            if eliminated_player.role == Role.HUNTER:
                await self._process_hunter_shot(eliminated_id)

        # Check for game end
        if not await self._check_game_end():
            # Continue to next night
            self.day_count += 1
            await self._start_night_phase()

    # async def _execute_agent_action(self, agent_id: str, action: AgentAction, phase: GamePhase) -> None:
    #     """Execute agent action."""
    #     logger.info(f"Executing {action.action_type} for agent {agent_id}")

    #     if action.action_type == "werewolf_kill" and action.target:
    #         await self._execute_werewolf_kill(agent_id, action.target)

    #     elif action.action_type == "seer_check" and action.target:
    #         await self._execute_seer_check(agent_id, action.target)

    #     elif action.action_type == "witch_save" and action.target:
    #         await self._execute_witch_save(agent_id, action.target)

    #     elif action.action_type == "witch_poison" and action.target:
    #         await self._execute_witch_poison(agent_id, action.target)

    #     elif action.action_type == "hunter_shoot" and action.target:
    #         await self._execute_hunter_shot(agent_id, action.target)

    # async def _execute_werewolf_kill(self, werewolf_id: str, target_id: str) -> None:
    #     """Execute werewolf kill action."""
    #     target_player = self._get_player_by_id(target_id)
    #     if target_player:
    #         # Log werewolf kill to console
    #         logger.info(f"🌙 狼人击杀目标: {target_player.name}")
    #         print(f"[狼人击杀] 目标: {target_player.name}")

    #         # Mark for death (will be processed in day phase)
    #         self.session.night_actions.werewolf_target = {
    #             "player_id": target_id,
    #             "player_name": target_player.name,
    #             "action_by": werewolf_id
    #         }

    async def _execute_seer_check(self, seer_id: str, target_id: str) -> None:
        """Execute seer check action."""
        target_player = self._get_player_by_id(target_id)
        seer_agent = self.agents[seer_id]

        if target_player:
            result = "werewolf" if target_player.role == Role.WEREWOLF else "good"
            result_text = "狼人" if result == "werewolf" else "好人"

            # Log seer check to console
            # logger.info(f"🔮 预言家查验了 {target_player.name}，结果是: {result_text}")
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

    async def _execute_witch_save(self, witch_id: str, werewolf_target: dict) -> None:
        """Execute witch save action."""
        target_name = werewolf_target['player_name']

        # Update night actions
        self.session.night_actions.witch_save = True

        # Update witch's ability status
        witch_player = self._get_player_by_id(witch_id)
        if witch_player:
            witch_player.role_abilities.witch_has_antidote = False

        # Log to console
        # logger.info(f"🧪 女巫使用解药救了 {target_name}")
        print(f"[女巫解药] 女巫救了 {target_name}")

        # Update witch's knowledge
        witch_agent = self.agents[witch_id]
        witch_agent.update_player_notes(
            werewolf_target['player_id'],
            "使用解药拯救"
        )

        

    async def _execute_witch_poison(self, witch_id: str, target_id: str) -> None:
        """Execute witch poison action."""
        target_player = self._get_player_by_id(target_id)
        witch_agent = self.agents[witch_id]

        if target_player:
            # Update night actions (use witch_poison_target for consistency)
            self.session.night_actions.witch_poison_target = {
                "player_id": target_player.id,
                "player_name": target_player.name
            }

            # Update witch's ability status
            witch_player = self._get_player_by_id(witch_id)
            if witch_player:
                witch_player.role_abilities.witch_has_poison = False

            # Log to console
            # logger.info(f"🧪 女巫使用毒药毒死 {target_player.name}")
            print(f"[女巫毒药] 女巫毒死 {target_player.name}")

            # Update witch's knowledge
            witch_agent.update_player_notes(
                target_id,
                "使用毒药击杀"
            )

           

    async def _execute_hunter_shot(self, hunter_id: str, target_id: str) -> None:
        """Execute hunter shot action."""
        target_player = self._get_player_by_id(target_id)
        hunter_agent = self.agents[hunter_id]

        if target_player:
            # Log hunter shot to console
            # logger.info(f"🔫 猎人开枪: {target_player.name}")
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

    async def _process_night_results(self) -> List[Dict[str, Any]]:
        """Process night phase results. Returns list of deaths."""
        night_deaths = []
        
        # Check werewolf kill
        werewolf_target = self.session.night_actions.werewolf_target
        if werewolf_target:
            target_id = werewolf_target["player_id"]
            target_name = werewolf_target["player_name"]

            # Check if witch saved the target
            if self.session.night_actions.witch_save:
                logger.info(f"🧪 女巫使用解药救活了 {target_name}")
                print(f"[女巫解药] {target_name} 被救活")
                
            else:
                await self._eliminate_player(target_id, "狼人击杀")
                night_deaths.append({
                    "player_id": target_id,
                    "player_name": target_name,
                    "cause": "狼人击杀"
                })
      
        # Check witch poison
        if hasattr(self.session.night_actions, 'witch_poison_target') and self.session.night_actions.witch_poison_target:
            poison_target = self.session.night_actions.witch_poison_target
            await self._eliminate_player(poison_target["player_id"], "女巫毒杀")
            night_deaths.append({
                "player_id": poison_target["player_id"],
                "player_name": poison_target["player_name"],
                "cause": "女巫毒杀"
            })
        
        # Reset night actions for next night
        self.session.night_actions.werewolf_target = None
        self.session.night_actions.witch_save = False
        if hasattr(self.session.night_actions, 'witch_poison_target'):
            self.session.night_actions.witch_poison_target = None
        
        return night_deaths
    
    async def _announce_night_deaths(self, deaths: List[Dict[str, Any]]) -> None:
        """Announce night deaths."""
        if not deaths:
            result = "昨晚是平安夜，无人死亡"
            logger.info("☀️ 昨晚是平安夜，无人死亡")
            print("[天亮] 昨晚是平安夜，无人死亡")
            await self.event_service.record_event(
                session_id=self.session.id,
                event_type=EventType.DEATH_ANNOUNCE,
                content=result,
                phase=GamePhase.DAY_DISCUSSION,
                day_number=self.day_count
            )
        else:
            names = ", ".join([d["player_name"] for d in deaths])
            result = f"昨晚死亡: {names}"
            logger.info(f"☀️ 天亮了，昨晚死亡: {names}")
            print(f"[天亮] 昨晚死亡: {names}")
            await self.event_service.record_event(
                session_id=self.session.id,
                event_type=EventType.DEATH_ANNOUNCE,
                content=f"昨晚死亡: {names}",
                phase=GamePhase.DAY_DISCUSSION,
                day_number=self.day_count
            )
        #加入memory
        msg = Msg(role="system", content=result, name="system")
        for agent_id, agent in self.agents.items():
            if self._is_player_alive(agent_id) and agent.agent:
                try:
                    await agent.agent.memory.add(msg)
                except Exception as e:
                    logger.warning(f"Failed to add memory to agent {agent.name}: {e}")

    async def _process_last_words(self, player_id: str, death_reason: str) -> None:
        """Process last words for a dead player."""
        player = self._get_player_by_id(player_id)
        if not player:
            return
        
        agent = self.agents.get(player_id)
        if not agent:
            return
        #若果是猎人
        if player.role == Role.HUNTER:
            await self._process_hunter_shot(player_id)
        else:    
            try:
                # Get last words from agent
                game_state = await self._create_game_state(player_id)
                game_state.my_status = "dead"
                action = await agent.make_decision(game_state, ["last_words"])
                
                if action.content:
                    logger.info(f"💀 {player.name} 的遗言: {action.content}")
                    print(f"[遗言] {player.name}: {action.content}")
                    #加入玩家memory
                    msg = Msg(role="system", content=f"{player.name} 遗言: {action.content}", name="system")
                    for agent_id, agent in self.agents.items():
                        if self._is_player_alive(agent_id) and agent.agent:
                            try:
                                await agent.agent.memory.add(msg)
                            except Exception as e:
                                logger.warning(f"Failed to add memory to agent {agent.name}: {e}")
                    await self.event_service.record_event(
                        session_id=self.session.id,
                        event_type=EventType.PLAYER_SPEECH,
                        content=f"{player.name} 遗言: {action.content}",
                        actor_id=player_id,
                        phase=GamePhase.DAY_DISCUSSION,
                        day_number=self.day_count
                    )
            except Exception as e:
                logger.error(f"Error getting last words from {player.name}: {e}")
    
    async def _process_sheriff_election(self) -> None:
        """Process sheriff election (day 1 only)."""
        logger.info("🎖️ 开始警长竞选")
        print("[警长竞选] 开始警长竞选环节")
        
        await self._transition_to_phase(GamePhase.SHERIFF_ELECTION)
        
        # Step 1: Each player decides whether to run (no speech required for declining)
        candidates = []
        for agent_id, agent in self.agents.items():
            if self._is_player_alive(agent_id):
                # Retry up to 2 times on connection errors
                for attempt in range(2):
                    try:
                        game_state = await self._create_game_state(agent_id)
                        action = await agent.make_decision(game_state, ["run_for_sheriff", "decline_sheriff"])
                        
                        if action.action_type == "run_for_sheriff":
                            candidates.append({"id": agent_id, "agent": agent})
                            player = self._get_player_by_id(agent_id)
                            logger.info(f"🎖️ {player.name} 参与竞选警长")
                            print(f"[竞选] {player.name} 参与竞选警长")
                            await self.event_service.record_event(
                                session_id=self.session.id,
                                event_type=EventType.SHERIFF_CANDIDACY,
                                content=f"{player.name} 决定参与竞选警长",
                                phase=GamePhase.SHERIFF_ELECTION,
                                day_number=self.day_count,
                                actor_id=player.id,
                                actor_name=player.name)
                        else:
                            logger.info(f"🎖️ {player.name} 决定不参与竞选警长")
                            print(f"[竞选] {player.name} 决定不参与竞选警长")
                            await self.event_service.record_event(
                                session_id=self.session.id,
                                event_type=EventType.SHERIFF_CANDIDACY,
                                content=f"{player.name} 决定不参与竞选警长",
                                phase=GamePhase.SHERIFF_ELECTION,
                                day_number=self.day_count,
                                actor_id=player.id,
                                actor_name=player.name)
                        # Players who decline don't need to say anything
                        break  # Success, exit retry loop
                    except Exception as e:
                        if attempt == 0 and "connection" in str(e).lower():
                            logger.warning(f"Connection error for {agent.name}, retrying...")
                            await asyncio.sleep(1)  # Wait before retry
                        else:
                            logger.error(f"Error in sheriff election for {agent.name}: {e}")
                            break
        
        if not candidates:
            logger.info("🎖️ 无人参与竞选，本局无警长")
            print("[警长竞选] 无人参与竞选，本局无警长")
            return
        
        # Step 2: Only candidates give campaign speeches
        logger.info("📢 竞选者发表竞选演说")
        print("[竞选发言] 竞选者发表竞选演说")
        for candidate in candidates:
            try:
                game_state = await self._create_game_state(candidate["id"])
                game_state.known_info["is_campaign_speech"] = True
                action = await candidate["agent"].make_decision(game_state, ["campaign_speech"])
                
                player = self._get_player_by_id(candidate["id"])
                if action.content and player:
                    # logger.info(f"📢 {player.name}: {action.content[:100]}...")
                    print(f"[竞选发言] {player.name}: {action.content}")
                    #添加到event_service
                    await self.event_service.record_event(
                        session_id=self.session.id,
                        event_type=EventType.SHERIFF_SPEECH,
                        content=f"{player.name} 竞选发言: {action.content}",
                        phase=GamePhase.DAY_DISCUSSION,
                        day_number=self.day_count,
                        actor_id=player.id,
                        actor_name=player.name
                    )
            except Exception as e:
                logger.error(f"Error in campaign speech for {candidate['agent'].name}: {e}")
        
        # Step 3: Non-candidates vote (they don't need to speak, just vote)
        candidate_ids = [c["id"] for c in candidates]
        votes = {}
        voting_record={}
        for agent_id, agent in self.agents.items():
            if self._is_player_alive(agent_id) and agent_id not in candidate_ids:
                try:
                    game_state = await self._create_game_state(agent_id)
                    game_state.known_info["candidates"] = [
                        {"id": c["id"], "name": self._get_player_by_id(c["id"]).name}
                        for c in candidates
                    ]
                    action = await agent.make_decision(game_state, ["vote_sheriff"])
                    
                    if action.target:
                        target_player = self._get_player_by_id(action.target)
                        if target_player and target_player.id in candidate_ids:
                            votes[agent_id] = target_player.id
                            voter = self._get_player_by_id(agent_id)
                            logger.info(f"🗳️ {voter.name} 投票给 {target_player.name}")
                            voting_record[voter.name] = target_player.name
                            await self.event_service.record_event(
                                session_id=self.session.id,
                                event_type=EventType.PLAYER_VOTE,
                                content=f"{voter.name} 投票给 {target_player.name}。内心活动：{action.reasoning}",
                                phase=GamePhase.VOTING,
                                day_number=self.day_count,
                                actor_id=voter.id,
                                actor_name=voter.name,
                                target_id=target_player.id,
                                target_name=target_player.name)
                except Exception as e:
                    logger.error(f"Error in sheriff vote from {agent.name}: {e}")
        voting_name = "警长竞选投票"
        for agent_id, agent in self.agents.items():
            if self._is_player_alive(agent_id):
                agent.update_voting_history(voting_name, voting_record)
        # Step 4: Count votes and elect sheriff
        if votes:
            vote_counts = {}
            for target_id in votes.values():
                vote_counts[target_id] = vote_counts.get(target_id, 0) + 1
            
            sheriff_id = max(vote_counts.keys(), key=lambda k: vote_counts[k])
            sheriff = self._get_player_by_id(sheriff_id)
            
            if sheriff:
                self.session.sheriff = {"player_id": sheriff_id, "player_name": sheriff.name}
                sheriff.set_as_sheriff()  # Set sheriff status and voting weight
                logger.info(f"🎖️ {sheriff.name} 当选警长！")
                print(f"[警长竞选] {sheriff.name} 当选警长！")
                await self.event_service.record_event(
                    session_id=self.session.id,
                    event_type=EventType.SHERIFF_ELECTED,
                    content=f"{sheriff.name} 当选警长！",
                    phase=GamePhase.DAY_DISCUSSION,
                    day_number=self.day_count,
                    actor_id=sheriff.id,
                    actor_name=sheriff.name)
        elif len(candidates) == 1:
            # Only one candidate, auto-elect
            sheriff_id = candidates[0]["id"]
            sheriff = self._get_player_by_id(sheriff_id)
            if sheriff:
                self.session.sheriff = {"player_id": sheriff_id, "player_name": sheriff.name}
                sheriff.set_as_sheriff()  # Set sheriff status and voting weight
                logger.info(f"🎖️ {sheriff.name} 自动当选警长！")
                print(f"[警长竞选] {sheriff.name} 自动当选警长（唯一竞选者）")
                await self.event_service.record_event(
                    session_id=self.session.id,
                    event_type=EventType.SHERIFF_ELECTED,
                    content=f"{sheriff.name} 自动当选警长！",
                    phase=GamePhase.DAY_DISCUSSION,
                    day_number=self.day_count,
                    actor_id=sheriff.id,
                    actor_name=sheriff.name)

    async def _eliminate_player(self, player_id: str, reason: str) -> None:
        """Eliminate a player from the game."""
        player = self._get_player_by_id(player_id)
        if not player or player.status != PlayerStatus.ALIVE:
            return

        player.status = PlayerStatus.DEAD
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
            actor_name=player.name,
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
        else:
            await self.event_service.record_event(
                session_id=self.session.id,
                event_type=EventType.HUNTER_SHOOT,
                content=f"猎人选择不开枪",
                phase=GamePhase.DAY_DISCUSSION,
                day_number=self.day_count,
                actor_id=hunter_id,
                actor_name=hunter_agent.name)
    def _get_night_actions_for_role(self, role: Role) -> List[str]:
        """Get available actions for a role during night."""
        actions = {
            Role.WEREWOLF: ["werewolf_discuss", "werewolf_kill"],
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
        elif self.session.current_phase == GamePhase.DAY_DISCUSSION:
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
        alive_village = [
            p for p in self.room.players
            if p.role == Role.VILLAGER and p.status == PlayerStatus.ALIVE
        ]
        alive_special = [
            p for p in self.room.players
            if p.role in [Role.SEER, Role.WITCH, Role.HUNTER] and p.status == PlayerStatus.ALIVE
        ]

        if len(alive_werewolves) == 0:
            await self._end_game(Team.GOOD, "所有狼人被消灭")
            return True
        elif len(alive_village) == 0:
            await self._end_game(Team.WEREWOLF, "村民全灭")
            return True
        elif len(alive_special) == 0:
            await self._end_game(Team.WEREWOLF, "神全灭")
            return True

        return False

    async def _end_game(self, winner: Team, reason: str) -> None:
        """End the game."""
        logger.info(f"Game ended. Winner: {winner.value}, Reason: {reason}")
        #打印获胜玩家
        winner_players = [p.name for p in self.room.players if p.team == winner]
        logger.info(f"获胜玩家: {winner_players}")
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
        """Get player by ID or position number."""
        # First try by UUID
        player = next((p for p in self.room.players if p.id == player_id), None)
        if player:
            return player
        
        # Try by position number (AI might return "2" instead of UUID)
        try:
            position = int(player_id)
            player = next((p for p in self.room.players if p.position == position), None)
            if player:
                return player
        except (ValueError, TypeError):
            pass
        
        # Try by player name
        player = next((p for p in self.room.players if p.name == player_id), None)
        return player

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

        # Calculate duration
        start_time = self.session.phase_start_time
        end_time = self.session.ended_at or datetime.now()
        duration = (end_time - start_time).total_seconds()

        return {
            "session_id": self.session.id,
            "room_id": self.session.room_id,
            "status": "running" if self.is_running else "ended",
            "current_phase": self.session.current_phase.value,
            "day_count": self.session.day_count,
            "is_running": self.is_running,
            "players": [p.get_private_info() for p in self.room.players],
            "events": [
                {
                    "id": str(e.id),
                    "timestamp": e.timestamp.isoformat(),
                    "day_count": e.day_count,
                    "phase": e.phase.value if hasattr(e.phase, 'value') else str(e.phase),
                    "type": e.type.value if hasattr(e.type, 'value') else str(e.type),
                    "content": e.content,
                    "actor_id": e.actor_id,
                    "actor_name": e.actor_name,
                    "target_id": e.target_id,
                    "target_name": e.target_name,
                }
                for e in self.event_service.get_visible_events(self.session.id)
            ],
            "winner": self.session.winner.value if self.session.winner else None,
            "start_time": start_time.isoformat(),
            "end_time": self.session.ended_at.isoformat() if self.session.ended_at else None,
            "duration": duration,
            "agent_info": {
                player_id: agent.get_agent_info()
                for player_id, agent in self.agents.items()
            }
        }

    def stop_game(self) -> None:
        """Stop the game immediately."""
        logger.info(f"Stopping game for room {self.room.id}")

        # Set game as not running
        self.is_running = False

        # Mark session as ended if it exists
        if self.session:
            self.session.end_game("游戏被手动停止")

        # Record stop event if session exists
        if self.session:
            asyncio.create_task(self.event_service.record_event(
                session_id=self.session.id,
                event_type=EventType.GAME_END,
                content="游戏被手动停止",
                phase=self.session.current_phase,
                day_number=self.day_count
            ))

    async def cleanup(self) -> None:
        """Clean up resources."""
        logger.info(f"Cleaning up game resources for room {self.room.id}")

        try:
            # Clean up all AI agents
            if self.agents:
                for player_id, agent in self.agents.items():
                    try:
                        if hasattr(agent, 'cleanup'):
                            await agent.cleanup()
                        elif hasattr(agent, 'close'):
                            await agent.close()
                        logger.debug(f"Cleaned up agent for player {player_id}")
                    except Exception as e:
                        logger.error(f"Error cleaning up agent {player_id}: {e}")

                self.agents.clear()

            # Clean up event service
            if self.event_service and hasattr(self.event_service, 'cleanup'):
                await self.event_service.cleanup()

            # Clear session
            self.session = None
            self.is_running = False

            # Clear team info
            self.team_info.clear()

            logger.info(f"Game resources cleaned up for room {self.room.id}")

        except Exception as e:
            logger.error(f"Error during cleanup for room {self.room.id}: {e}")

    async def _get_daily_summary(self) -> str:
        """Get daily summary of speeches for the current day."""
        if not self.session:
            return ""

        # 从 EventService 获取当前对局的事件，过滤当日的总结
        all_events = self.event_service.get_session_events(self.session.id)
        daily_summary_events = [
            e for e in all_events
            if e.event_type == EventType.PLAYER_SPEECH or e.event_type == EventType.SHERIFF_SPEECH or e.event_type == EventType.DEATH_ANNOUNCE or e.event_type == EventType.SEER_CHECK or e.event_type == EventType.WITCH_SAVE or e.event_type == EventType.WITCH_POISON or e.event_type == EventType.HUNTER_SHOOT and e.day_count == self.day_count
        ]

        daily_summary = ""
        for event in daily_summary_events:
            daily_summary += f"{event.actor_name}（{event.actor_id}）：{event.content}\n"


        # 调用 LLM 总结发言，重点关注“保谁 / 踩谁”
        prompt = f"总结第{self.day_count}天的所有事件，重点关注发言中谁保了谁、谁踩了谁，不要漏掉死亡事件：\n{daily_summary}"
        msg = Msg(role="user", content=prompt, name="user")
        summary = await self.room.summary_agent(msg)
        logger.info(f"第{self.day_count}天事件总结：{summary.content}")
        return summary.content

