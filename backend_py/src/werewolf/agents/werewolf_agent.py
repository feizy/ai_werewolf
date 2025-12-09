"""Werewolf agent implementation using AgentScope ReactAgent."""

import json
from typing import Dict, List, Any

from .base_agent import BaseGameAgent, GameState, AgentAction
from ..models.player import Role
from loguru import logger


class WerewolfReactAgent(BaseGameAgent):
    """Werewolf agent - LLM handles all strategic decisions."""

    def _get_system_prompt(self) -> str:
        """Get system prompt for werewolf agent."""
        return """你是狼人杀游戏中的狼人。你的目标是与狼人队友合作，隐藏身份，消灭所有好人。

游戏规则：
1. 狼人在夜晚阶段可以击杀一名玩家
2. 你需要隐藏自己的狼人身份，在白天伪装成好人
3. 与狼人队友配合，制定最佳策略
4. 观察其他玩家的行为，识别神职角色（预言家、女巫、猎人）

决策原则：
- 优先击杀神职角色：预言家 > 女巫 > 猎人 > 平民
- 分析每个玩家的发言和行为
- 白天发言时要避免暴露身份
- 在投票时误导好人

你的回应必须是JSON格式。"""

    async def make_decision(
        self,
        game_state: GameState,
        available_actions: List[str]
    ) -> AgentAction:
        """Make werewolf-specific decision."""
        # Update werewolf-specific analysis
        # await self._analyze_werewolf_situation(game_state)

        # Call parent decision making
        action = await super().make_decision(game_state, available_actions)

        return action

    async def _analyze_werewolf_situation(self, game_state: GameState) -> None:
        """Analyze current situation from werewolf perspective."""
        # Count werewolves vs good players
        werewolf_count = sum(1 for p in game_state.alive_players
                            if self.player_notes.get(p["id"], "").startswith("队友"))

        good_count = len(game_state.alive_players) - werewolf_count - 1  # -1 for self

        # Identify high-value targets
        for player in game_state.alive_players:
            if player["id"] == self.player_id:
                continue

            # Behavioral analysis from speeches
            recent_speeches = [event for event in game_state.recent_events
                             if event.get("actor_id") == player["id"] and
                             event.get("type") == "player_speech"]

            threat_level = 0.0
            for speech in recent_speeches:
                content = speech.get("content", "").lower()
                if any(word in content for word in ["预言家", "查验"]):
                    threat_level += 0.3
                elif any(word in content for word in ["狼人", "击杀"]):
                    threat_level += 0.2

            if threat_level > 0.5:
                current_notes = self.player_notes.get(player["id"], "")
                if "高威胁" not in current_notes:
                    self.update_player_notes(player["id"], f"{current_notes} [高威胁目标]")


class SeerReactAgent(BaseGameAgent):
    """Seer agent - LLM handles prophecy and deduction."""

    def _get_system_prompt(self) -> str:
        """Get system prompt for seer agent."""
        return """你是狼人杀游戏中的预言家。你的目标是找出所有狼人，引导好人阵营获胜。

游戏能力：
- 每晚可以查验一名玩家的真实身份（好人/狼人）
- 查验结果会在你的 known_info 中显示

预言家策略：
- 谨慎选择查验目标，优先查验可疑玩家
- 在适当时机公布查验结果
- 保护自己的身份安全
- 引导好人正确投票

决策原则：
- 分析玩家发言和行为模式
- 根据游戏局势调整查验策略
- 在关键时刻挺身而出公布身份

你的回应必须是JSON格式。"""

    async def make_decision(
        self,
        game_state: GameState,
        available_actions: List[str]
    ) -> AgentAction:
        """Make seer-specific decision."""
        # Update seer analysis - use check results
        for player_id, info in self.player_notes.items():
            if "查验结果" in info:
                if "狼人" in info:
                    self.suspicions[player_id] = 1.0
                elif "好人" in info:
                    self.suspicions[player_id] = 0.0

        return await super().make_decision(game_state, available_actions)


class WitchReactAgent(BaseGameAgent):
    """Witch agent - LLM handles potion decisions."""

    def _get_system_prompt(self) -> str:
        """Get system prompt for witch agent."""
        return """你是狼人杀游戏中的女巫。你拥有一瓶解药和一瓶毒药。

游戏能力：
- 解药：每晚可以救活被狼人击杀的玩家（整局游戏只能用一次）
- 毒药：可以毒死一名玩家（整局游戏只能用一次）
- 不能在同一晚同时使用解药和毒药
- 被狼人击杀的玩家信息会在 known_info 中告诉你

女巫策略：
- 谨慎使用解药，救活重要的神职或关键玩家
- 毒药要有确凿证据，避免误伤好人
- 根据局势判断何时使用药剂

决策原则：
- 分析击杀目标的身份价值
- 评估使用药剂的风险和收益
- 考虑剩余玩家数量

你的回应必须是JSON格式。"""


class HunterReactAgent(BaseGameAgent):
    """Hunter agent - LLM handles final shot decision."""

    def _get_system_prompt(self) -> str:
        """Get system prompt for hunter agent."""
        return """你是狼人杀游戏中的猎人。你在死亡时可以开枪带走一名玩家。

游戏能力：
- 死亡时可以开枪带走一名玩家
- 被投票出局或被狼人杀死时可以开枪
- 被女巫毒死时不能开枪

猎人策略：
- 在游戏过程中观察和分析可疑玩家
- 死亡时要有充分的判断依据
- 优先带走最可疑的玩家

决策原则：
- 基于整局游戏的观察判断
- 选择最具威胁的目标
- 为好人阵营做最后贡献

你的回应必须是JSON格式。"""


class VillagerReactAgent(BaseGameAgent):
    """Villager agent - LLM handles logical reasoning."""

    def _get_system_prompt(self) -> str:
        """Get system prompt for villager agent."""
        return """你是狼人杀游戏中的平民。你的目标是通过观察和推理找出狼人。

游戏能力：
- 白天参与讨论，分析发言
- 投票放逐可疑玩家
- 没有特殊能力，依靠逻辑推理

平民策略：
- 仔细观察每个玩家的发言和行为
- 识别发言中的矛盾和疑点
- 保护神职玩家，支持正确判断

决策原则：
- 基于逻辑推理而非情绪
- 分析证据和线索
- 与好人阵营团结一致

你的回应必须是JSON格式。"""
