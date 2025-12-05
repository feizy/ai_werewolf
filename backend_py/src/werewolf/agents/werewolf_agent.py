"""Werewolf agent implementation using AgentScope ReactAgent."""

import json
from typing import Dict, List, Any

from .base_agent import BaseGameAgent, GameState, AgentAction
from ..models.player import Role, PersonalityType, SkillLevel
from loguru import logger


class WerewolfReactAgent(BaseGameAgent):
    """Werewolf agent with sophisticated decision making."""

    def _get_system_prompt(self) -> str:
        """Get system prompt for werewolf agent."""
        return f"""你是一个狼人杀游戏中的狼人玩家。你的目标是与狼人队友合作，隐藏身份，消灭所有好人。

你的身份：狼人
性格特点：{self.personality.value}
技能等级：{self.skill_level.value}

游戏规则：
1. 狼人在夜晚阶段可以击杀一名玩家
2. 你需要隐藏自己的狼人身份，在白天伪装成好人
3. 与狼人队友配合，制定最佳策略
4. 观察其他玩家的行为，识别神职角色（预言家、女巫、猎人）
5. 根据局势调整策略，必要时牺牲队友保全团队

狼人策略：
- 优先击杀神职角色：预言家 > 女巫 > 猎人 > 平民
- 避免在白天暴露自己的身份
- 制造混乱，误导好人投票
- 保护重要的狼人队友
- 在关键时刻采取冒险行动

决策原则：
- 分析每个玩家的威胁等级
- 考虑击杀目标对游戏局势的影响
- 平衡短期收益和长期策略
- 根据剩余玩家数量调整策略

你的回应必须是基于当前游戏局势的理性分析。"""

    async def make_decision(
        self,
        game_state: GameState,
        available_actions: List[str]
    ) -> AgentAction:
        """Make werewolf-specific decision."""
        # Update werewolf-specific analysis
        await self._analyze_werewolf_situation(game_state)

        # Call parent decision making
        action = await super().make_decision(game_state, available_actions)

        # Enhance werewolf decisions
        if action.action_type == "werewolf_kill":
            action = await self._enhance_kill_decision(action, game_state)

        return action

    async def _analyze_werewolf_situation(self, game_state: GameState) -> None:
        """Analyze current situation from werewolf perspective."""
        # Count werewolves vs good players
        werewolf_count = sum(1 for p in game_state.alive_players
                            if self.player_notes.get(p["id"], "").startswith("队友"))

        good_count = len(game_state.alive_players) - werewolf_count

        # Update strategic priorities
        if good_count <= werewolf_count + 1:
            self.strategic_priority = "aggressive"  # Need to eliminate quickly
        elif good_count > werewolf_count * 2:
            self.strategic_priority = "careful"    # Need to be stealthy
        else:
            self.strategic_priority = "balanced"  # Balanced approach

        # Identify high-value targets
        await self._identify_high_value_targets(game_state)

    async def _identify_high_value_targets(self, game_state: GameState) -> None:
        """Identify high priority targets for elimination."""
        for player in game_state.alive_players:
            if player["id"] == self.player_id:
                continue

            threat_level = 0.0
            reasoning = []

            # Known enemies (from team knowledge)
            if self.player_notes.get(player["id"], "").startswith("敌人"):
                threat_level += 0.8
                reasoning.append("已知敌人")

            # Behavioral analysis
            recent_speeches = [event for event in game_state.recent_events
                             if event.get("actor_id") == player["id"] and
                             event.get("type") == "player_speech"]

            for speech in recent_speeches:
                content = speech.get("content", "").lower()
                if any(word in content for word in ["预言家", "查验", "好人"]):
                    threat_level += 0.3
                    reasoning.append("神职行为模式")
                elif any(word in content for word in ["狼人", "击杀", "黑夜"]):
                    threat_level += 0.2
                    reasoning.append("可能识破狼人")

            # Update notes with analysis
            if threat_level > 0.6:
                current_notes = self.player_notes.get(player["id"], "")
                if "高价值目标" not in current_notes:
                    new_notes = f"{current_notes} [高价值目标: {', '.join(reasoning)}]"
                    self.update_player_notes(player["id"], new_notes)

    async def _enhance_kill_decision(self, action: AgentAction, game_state: GameState) -> AgentAction:
        """Enhance werewolf kill decision with strategic analysis."""
        if not action.target:
            return action

        target_player = next((p for p in game_state.alive_players if p["id"] == action.target), None)
        if not target_player:
            return action

        # Calculate kill priority
        kill_priority = self._calculate_kill_priority(target_player, game_state)

        # Add strategic reasoning
        strategic_reasoning = f"""
击杀优先级分析：
- 威胁等级：{kill_priority['threat_level']:.2f}
- 战略价值：{kill_priority['strategic_value']:.2f}
- 风险评估：{kill_priority['risk_assessment']:.2f}

当前局势：{self.strategic_priority}
剩余好人：{len([p for p in game_state.alive_players if p['id'] != self.player_id and not self.player_notes.get(p['id'], '').startswith('队友')])}
剩余狼人：{len([p for p in game_state.alive_players if self.player_notes.get(p['id'], '').startswith('队友')]) + 1}  # +1 for self

决策理由：{self._generate_kill_reasoning(target_player, kill_priority)}
"""

        action.metadata = {
            "kill_priority": kill_priority,
            "strategic_analysis": strategic_reasoning,
            "target_notes": self.player_notes.get(action.target, "无记录")
        }

        return action

    def _calculate_kill_priority(self, target: Dict[str, Any], game_state: GameState) -> Dict[str, float]:
        """Calculate priority for killing a target."""
        priority = {
            "threat_level": 0.0,
            "strategic_value": 0.0,
            "risk_assessment": 0.0
        }

        # Threat level based on known role or behavior
        notes = self.player_notes.get(target["id"], "")
        if "预言家" in notes or "seer" in notes.lower():
            priority["threat_level"] = 0.95
        elif "女巫" in notes or "witch" in notes.lower():
            priority["threat_level"] = 0.85
        elif "猎人" in notes or "hunter" in notes.lower():
            priority["threat_level"] = 0.75
        elif "神职" in notes:
            priority["threat_level"] = 0.8
        else:
            # Estimate based on behavior
            suspicion = self.suspicions.get(target["id"], 0.1)
            priority["threat_level"] = min(0.6, suspicion * 2)

        # Strategic value based on player position and influence
        if target.get("position", 0) <= 3:  # Early positions often more influential
            priority["strategic_value"] += 0.2

        # Risk assessment - killing suspicious players might be risky
        if self.suspicions.get(target["id"], 0.1) > 0.7:
            priority["risk_assessment"] = 0.8  # Risky - might confirm werewolf existence
        else:
            priority["risk_assessment"] = 0.3

        return priority

    def _generate_kill_reasoning(self, target: Dict[str, Any], priority: Dict[str, float]) -> str:
        """Generate reasoning for kill decision."""
        reasons = []

        if priority["threat_level"] > 0.8:
            reasons.append("高威胁目标，优先清除")
        elif priority["strategic_value"] > 0.6:
            reasons.append("具有重要战略价值")

        if self.strategic_priority == "aggressive":
            reasons.append("当前需要采取激进策略")
        elif self.strategic_priority == "careful":
            reasons.append("选择相对安全的目标")

        target_name = target.get("name", "未知玩家")
        return f"选择击杀{target_name}：" + "，".join(reasons)


class SeerReactAgent(BaseGameAgent):
    """Seer agent with prophecy and deduction abilities."""

    def _get_system_prompt(self) -> str:
        """Get system prompt for seer agent."""
        return f"""你是一个狼人杀游戏中的预言家。你的目标是找出所有狼人，引导好人阵营获胜。

你的身份：预言家
性格特点：{self.personality.value}
技能等级：{self.skill_level.value}

游戏能力：
- 每晚可以查验一名玩家的真实身份（好人/狼人）
- 在白天根据查验结果引导讨论和投票
- 需要合理使用身份信息，避免过早暴露
- 与其他神职角色配合

预言家策略：
- 谨慎选择查验目标，优先查验可疑玩家
- 在适当时机公布查验结果
- 保护自己的身份安全
- 引导好人正确投票

决策原则：
- 分析玩家发言和行为模式
- 根据游戏局势调整查验策略
- 平衡风险和收益
- 在关键时刻挺身而出

你的每个决策都应该基于逻辑推理和证据分析。"""

    async def make_decision(
        self,
        game_state: GameState,
        available_actions: List[str]
    ) -> AgentAction:
        """Make seer-specific decision."""
        # Update seer analysis
        await self._analyze_seer_knowledge(game_state)

        # Call parent decision making
        action = await super().make_decision(game_state, available_actions)

        # Enhance seer decisions
        if action.action_type == "seer_check":
            action = await self._enhance_check_decision(action, game_state)

        return action

    async def _analyze_seer_knowledge(self, game_state: GameState) -> None:
        """Analyze knowledge from seer perspective."""
        # Update knowledge based on previous checks
        for player_id, info in self.player_notes.items():
            if "查验结果" in info:
                # Extract knowledge from previous checks
                if "狼人" in info:
                    self.suspicions[player_id] = 1.0
                elif "好人" in info:
                    self.suspicions[player_id] = 0.0

    async def _enhance_check_decision(self, action: AgentAction, game_state: GameState) -> AgentAction:
        """Enhance seer check decision."""
        if not action.target:
            return action

        target_notes = self.player_notes.get(action.target, "")
        check_reasoning = f"查验理由："

        if "未查验" in target_notes:
            # New target analysis
            suspicion_level = self.suspicions.get(action.target, 0.1)
            check_reasoning += f"疑似度{suspicion_level:.2f}，需要确认身份"
        else:
            check_reasoning += "重新分析该玩家的行为模式"

        action.metadata = {
            "check_priority": self._calculate_check_priority(action.target, game_state),
            "target_suspicion": self.suspicions.get(action.target, 0.1),
            "previous_checks": [p for p in self.player_notes.keys() if "查验结果" in self.player_notes[p]]
        }

        action.reasoning = check_reasoning
        return action

    def _calculate_check_priority(self, target_id: str, game_state: GameState) -> float:
        """Calculate priority for checking a target."""
        base_priority = self.suspicions.get(target_id, 0.1)

        # Increase priority for influential players
        target = next((p for p in game_state.alive_players if p["id"] == target_id), None)
        if target and target.get("position", 0) <= 3:
            base_priority += 0.2

        return min(1.0, base_priority)


class WitchReactAgent(BaseGameAgent):
    """Witch agent with potion management and healing/poisoning."""

    def _get_system_prompt(self) -> str:
        """Get system prompt for witch agent."""
        return f"""你是一个狼人杀游戏中的女巫。你拥有一瓶解药和一瓶毒药，需要明智使用。

你的身份：女巫
性格特点：{self.personality.value}
技能等级：{self.skill_level.value}

游戏能力：
- 解药：每晚可以救活被狼人击杀的玩家（整局游戏只能用一次）
- 毒药：可以毒死一名玩家（整局游戏只能用一次）
- 不能在同一晚同时使用解药和毒药

女巫策略：
- 谨慎使用解药，救活重要的神职或关键玩家
- 毒药要有确凿证据，避免误伤好人
- 根据局势判断何时使用药剂
- 在关键时刻发挥作用

决策原则：
- 分析击杀目标的身份价值
- 评估使用药剂的风险和收益
- 考虑剩余玩家数量和阵营平衡
- 保持隐秘，避免过早暴露

你的每个决策都直接影响游戏走向。"""


class HunterReactAgent(BaseGameAgent):
    """Hunter agent with final shot ability."""

    def _get_system_prompt(self) -> str:
        """Get system prompt for hunter agent."""
        return f"""你是一个狼人杀游戏中的猎人。你在死亡时可以开枪带走一名玩家。

你的身份：猎人
性格特点：{self.personality.value}
技能等级：{self.skill_level.value}

游戏能力：
- 死亡时可以开枪带走一名玩家
- 被投票出局或被狼人杀死时可以开枪
- 被女巫毒死时不能开枪

猎人策略：
- 在游戏过程中观察和分析可疑玩家
- 死亡时要有充分的判断依据
- 优先带走最可疑的玩家
- 为好人阵营做最后贡献

决策原则：
- 基于整局游戏的观察判断
- 选择最具威胁的目标
- 考虑剩余玩家的阵营平衡
- 在关键时刻做出正确选择

你的开枪机会很珍贵，务必谨慎使用。"""


class VillagerReactAgent(BaseGameAgent):
    """Villager agent with logical reasoning."""

    def _get_system_prompt(self) -> str:
        """Get system prompt for villager agent."""
        return f"""你是一个狼人杀游戏中的平民。你的目标是通过观察和推理找出狼人。

你的身份：平民
性格特点：{self.personality.value}
技能等级：{self.skill_level.value}

游戏能力：
- 白天参与讨论，分析发言
- 投票放逐可疑玩家
- 没有特殊能力，依靠逻辑推理

平民策略：
- 仔细观察每个玩家的发言和行为
- 识别发言中的矛盾和疑点
- 保护神职玩家，支持正确判断
- 在关键时刻发挥团队作用

决策原则：
- 基于逻辑推理而非情绪
- 分析证据和线索
- 考虑多种可能性
- 与好人阵营团结一致

虽然你是平民，但你的观察和推理对好人阵营很重要。"""