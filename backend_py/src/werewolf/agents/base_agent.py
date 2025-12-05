"""Base game agent using AgentScope."""

import json
import time
from typing import Dict, List, Any, Optional, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass

from agentscope.agent import ReActAgent
from agentscope.message import Msg
from agentscope.model import AnthropicChatModel
from agentscope.formatter import AnthropicChatFormatter
from loguru import logger
from ..models.player import Role, PersonalityType, SkillLevel


@dataclass
class GameState:
    """Game state information for agents."""
    phase: str  # "night", "day", "voting"
    day_count: int
    alive_players: List[Dict[str, Any]]
    my_role: Optional[str] = None
    my_status: str = "alive"  # "alive", "dead"
    known_info: Dict[str, Any] = None
    recent_events: List[Dict[str, Any]] = None
    available_actions: List[str] = None

    def __post_init__(self):
        if self.known_info is None:
            self.known_info = {}
        if self.recent_events is None:
            self.recent_events = []
        if self.available_actions is None:
            self.available_actions = []


@dataclass
class AgentAction:
    """Agent action structure."""
    action_type: str
    target: Optional[str] = None  # Target player ID
    content: Optional[str] = None  # Speech content or action details
    reasoning: Optional[str] = None
    confidence: float = 0.8
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseGameAgent(ReActAgent):
    """Base class for game agents using AgentScope."""

    def __init__(
        self,
        player_id: str,
        name: str,
        role: Role,
        personality: PersonalityType,
        skill_level: SkillLevel,
        model_config: Optional[Dict[str, Any]] = None
    ):
        self.player_id = player_id
        self.name = name
        self.role = role
        self.personality = personality
        self.skill_level = skill_level
        self.model_config = model_config or {}

        # AgentScope agent instance
        self.agent = None
        self.is_initialized = False

        # Agent memory
        self.game_history: List[Dict[str, Any]] = []
        self.player_notes: Dict[str, str] = {}
        self.suspicions: Dict[str, float] = {}  # player_id -> suspicion_level

    async def initialize(self, model: Optional[AnthropicChatModel] = None) -> None:
        """Initialize the AgentScope agent."""
        try:
            if self.is_initialized:
                return

            system_prompt = self._get_system_prompt()

            # Use provided model or create default one
            if not model:
                model = AnthropicChatModel(
                    **self.model_config
                )

            # Create the AgentScope agent
            self.agent = ReActAgent(
                name=f"{self.name}_{self.role.value}",
                sys_prompt=system_prompt,
                model=model,
                formatter=AnthropicChatFormatter(),
                max_iters=3,
                parallel_tool_calls=False,
                memory=True,
                enable_monitor=True
            )

            self.is_initialized = True
            logger.info(f"Initialized AgentScope agent {self.name} with role {self.role}")

        except Exception as e:
            logger.error(f"Failed to initialize AgentScope agent {self.name}: {e}")
            raise

    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Get system prompt for the agent."""
        pass

    def _get_temperature(self) -> float:
        """Get temperature based on skill level and personality."""
        # More skilled agents have lower temperature for more consistent responses
        skill_temps = {
            SkillLevel.BEGINNER: 0.9,
            SkillLevel.INTERMEDIATE: 0.7,
            SkillLevel.ADVANCED: 0.5,
            SkillLevel.EXPERT: 0.3
        }

        base_temp = skill_temps.get(self.skill_level, 0.7)

        # Adjust based on personality
        if "aggressive" in self.personality.value:
            base_temp += 0.1
        elif "cautious" in self.personality.value:
            base_temp -= 0.1

        return max(0.1, min(1.0, base_temp))

    async def make_decision(
        self,
        game_state: GameState,
        available_actions: List[str]
    ) -> AgentAction:
        """Make a game decision using AgentScope agent."""
        if not self.is_initialized:
            await self.initialize()

        if not self.agent:
            raise RuntimeError(f"Agent {self.name} not initialized")

        try:
            # Update internal state
            await self._update_internal_state(game_state)

            # Prepare decision prompt
            decision_prompt = self._prepare_decision_prompt(game_state, available_actions)

            # Get decision from AgentScope agent
            response = await self._query_agent(decision_prompt)

            # Parse response
            action = self._parse_agent_response(response)

            # Record decision
            self._record_decision(game_state, action)

            return action

        except Exception as e:
            logger.error(f"Error making decision for agent {self.name}: {e}")
            raise

    async def _update_internal_state(self, game_state: GameState) -> None:
        """Update agent's internal state based on game state."""
        # Update suspicions based on new information
        for player in game_state.alive_players:
            if player["id"] != self.player_id:
                await self._update_suspicion(player["id"], game_state)

        # Update recent events
        self.game_history.extend(game_state.recent_events)

        # Keep only recent history (last 50 events)
        if len(self.game_history) > 50:
            self.game_history = self.game_history[-50:]

    async def _update_suspicion(self, player_id: str, game_state: GameState) -> None:
        """Update suspicion level for a player."""
        # Base suspicion logic - will be overridden by specific agents
        current_suspicion = self.suspicions.get(player_id, 0.1)

        # Analyze recent events for this player
        relevant_events = [
            event for event in game_state.recent_events
            if event.get("actor_id") == player_id
        ]

        # Simple suspicion update logic
        for event in relevant_events:
            if event.get("type") == "player_speech":
                # Analyze speech content
                speech_content = event.get("content", "").lower()
                if any(word in speech_content for word in ["怀疑", "狼人", "坏人"]):
                    current_suspicion -= 0.1  # Player is actively looking for werewolves
                elif any(word in speech_content for word in ["无辜", "好人", "清白"]):
                    current_suspicion += 0.05  # Might be defensive

        self.suspicions[player_id] = max(0.0, min(1.0, current_suspicion))

    def _prepare_decision_prompt(self, game_state: GameState, available_actions: List[str]) -> str:
        """Prepare prompt for agent decision making."""
        prompt = f"""
现在是狼人杀游戏第{game_state.day_count}天，当前阶段：{game_state.phase}

你的信息：
- 身份：{game_state.my_role if game_state.my_role else self.role.value}
- 状态：{game_state.my_status}
- 技能等级：{self.skill_level.value}
- 性格特点：{self.personality.value}

存活玩家：
"""

        for i, player in enumerate(game_state.alive_players, 1):
            if player["id"] != self.player_id:
                suspicion = self.suspicions.get(player["id"], 0.1)
                notes = self.player_notes.get(player["id"], "暂无信息")
                prompt += f"{i}. {player['name']} (位置{player['position']}) - 疑似度: {suspicion:.2f} - 备注: {notes}\n"

        prompt += f"""
近期事件：
{chr(10).join(f"- {event}" for event in game_state.recent_events[-5:])}

可用行动：
{chr(10).join(f"- {action}" for action in available_actions)}

已知信息：
{json.dumps(game_state.known_info, ensure_ascii=False, indent=2)}

请分析当前局势，选择最佳行动。你需要以JSON格式回应，包含以下字段：
{{
    "action_type": "选择的行动类型",
    "target": "目标玩家ID（如果适用）",
    "content": "发言内容或行动详情",
    "reasoning": "决策理由",
    "confidence": 0.8,
    "strategic_analysis": "战略分析"
}}

请确保你的决策符合你的身份特点和当前局势。
"""
        return prompt

    async def _query_agent(self, prompt: str) -> str:
        """Query the AgentScope agent for a decision."""
        try:
            # Create message for agent
            msg = Msg(
                name="game_master",
                role="user",
                content=prompt
            )

            # Get response from AgentScope agent
            response = self.agent(msg)

            return response.text if hasattr(response, 'text') else str(response)

        except Exception as e:
            logger.error(f"Error querying AgentScope agent {self.name}: {e}")
            raise

    def _parse_agent_response(self, response: str) -> AgentAction:
        """Parse agent response into AgentAction."""
        try:
            # Try to parse as JSON
            if response.strip().startswith('{'):
                data = json.loads(response)

                return AgentAction(
                    action_type=data.get("action_type", "unknown"),
                    target=data.get("target"),
                    content=data.get("content"),
                    reasoning=data.get("reasoning", "No reasoning provided"),
                    confidence=float(data.get("confidence", 0.8)),
                    metadata=data.get("strategic_analysis", {})
                )
            else:
                # Parse as text response
                return self._parse_text_response(response)

        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON response from {self.name}, trying text parsing")
            return self._parse_text_response(response)

    def _parse_text_response(self, response: str) -> AgentAction:
        """Parse text response into AgentAction."""
        # Simple text parsing - this would be enhanced with better NLP
        content = response.strip()

        # Try to extract action type
        action_type = "speech"  # Default
        target = None

        if "击杀" in content or "kill" in content.lower():
            action_type = "werewolf_kill"
        elif "查验" in content or "check" in content.lower():
            action_type = "seer_check"
        elif "毒" in content or "poison" in content.lower():
            action_type = "witch_poison"
        elif "救" in content or "save" in content.lower():
            action_type = "witch_save"
        elif "开枪" in content or "shoot" in content.lower():
            action_type = "hunter_shoot"
        elif "投票" in content or "vote" in content.lower():
            action_type = "vote"

        return AgentAction(
            action_type=action_type,
            target=target,
            content=content,
            reasoning=f"Text response: {content[:100]}...",
            confidence=0.6
        )

    def _record_decision(self, game_state: GameState, action: AgentAction) -> None:
        """Record agent decision for learning."""
        decision_record = {
            "timestamp": time.time(),
            "game_state": {
                "phase": game_state.phase,
                "day_count": game_state.day_count
            },
            "action": {
                "type": action.action_type,
                "target": action.target,
                "reasoning": action.reasoning
            }
        }

        self.game_history.append(decision_record)

    async def send_message(self, message: str) -> str:
        """Send a message to the agent and get response."""
        if not self.is_initialized:
            await self.initialize()

        if not self.agent:
            raise RuntimeError(f"Agent {self.name} not initialized")

        try:
            msg = Msg(role="user", content=message)
            response = self.agent(msg)
            return response.text if hasattr(response, 'text') else str(response)
        except Exception as e:
            logger.error(f"Error sending message to agent {self.name}: {e}")
            raise

    def update_player_notes(self, player_id: str, notes: str) -> None:
        """Update notes about a player."""
        self.player_notes[player_id] = notes
        logger.debug(f"Agent {self.name} updated notes for player {player_id}: {notes}")

    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information."""
        return {
            "player_id": self.player_id,
            "name": self.name,
            "role": self.role.value,
            "personality": self.personality.value,
            "skill_level": self.skill_level.value,
            "is_initialized": self.is_initialized,
            "suspicions": self.suspicions,
            "player_notes": self.player_notes
        }

    async def close(self) -> None:
        """Close the agent and clean up resources."""
        try:
            if self.agent and hasattr(self.agent, 'close'):
                await self.agent.close()
            self.is_initialized = False
            logger.info(f"Closed agent {self.name}")
        except Exception as e:
            logger.warning(f"Error closing agent {self.name}: {e}")