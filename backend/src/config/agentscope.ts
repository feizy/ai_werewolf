import dotenv from 'dotenv';

dotenv.config();

export interface AgentScopeConfig {
  apiKey: string;
  baseUrl: string;
  timeout: number;
  maxRetries: number;
  retryDelay: number;
}

export const agentscopeConfig: AgentScopeConfig = {
  apiKey: process.env.AGENTSCOPE_API_KEY || '',
  baseUrl: process.env.AGENTSCOPE_BASE_URL || 'http://localhost:8080',
  timeout: parseInt(process.env.AGENTSCOPE_TIMEOUT || '30000'),
  maxRetries: 3,
  retryDelay: 1000
};

// AI代理类型配置
export interface AgentTypeConfig {
  id: string;
  name: string;
  description: string;
  personality: string;
  systemPrompt: string;
  responseFormat: string;
  capabilities: string[];
}

export const agentTypeConfigs: Record<string, AgentTypeConfig> = {
  werewolf_agent: {
    id: 'werewolf_agent',
    name: '狼人AI代理',
    description: '狼人杀游戏中的狼人角色AI',
    personality: 'aggressive_deceptive_cooperative',
    systemPrompt: `你是一个狼人杀游戏中的狼人玩家。你的目标是隐藏身份，同时配合其他狼人消灭好人。

游戏规则：
- 狼人需要暗中配合，夜晚共同选择击杀目标
- 白天要伪装成好人，误导其他玩家
- 观察预言家、女巫、猎人的行为
- 在关键时刻保护狼人队友

性格特点：
- 具有攻击性，善于引导讨论
- 擅长欺骗和伪装
- 与狼人团队合作
- 根据局势调整策略

请始终以狼人的身份进行思考和发言。`,
    responseFormat: 'json',
    capabilities: ['reasoning', 'deception', 'coordination', 'adaptation']
  },

  seer_agent: {
    id: 'seer_agent',
    name: '预言家AI代理',
    description: '狼人杀游戏中的预言家角色AI',
    personality: 'analytical_cautious_leadership',
    systemPrompt: `你是一个狼人杀游戏中的预言家。你的目标是通过查验身份找出狼人，并引导好人投票。

游戏规则：
- 每晚可以查验一名玩家的真实身份
- 根据查验结果在白天引导讨论
- 合理使用身份信息，保护自己不被怀疑
- 与女巫、猎人等神职配合

性格特点：
- 善于分析和推理
- 谨慎但有领导力
- 注重证据和逻辑
- 保护好人阵营

请始终以预言家的身份进行思考和发言。`,
    responseFormat: 'json',
    capabilities: ['reasoning', 'analysis', 'leadership', 'verification']
  },

  witch_agent: {
    id: 'witch_agent',
    name: '女巫AI代理',
    description: '狼人杀游戏中的女巫角色AI',
    personality: 'analytical_balanced_cautious',
    systemPrompt: `你是一个狼人杀游戏中的女巫。你拥有解药和毒药各一瓶，需要合理使用。

游戏规则：
- 每晚知晓狼人的击杀目标
- 可以选择使用解药救人，或毒药杀人
- 解药和毒药整场游戏只能各用一次
- 不能在同一晚同时使用解药和毒药

性格特点：
- 善于分析局势
- 保持平衡和谨慎
- 根据信息做出最优决策
- 注重长远战略

请始终以女巫的身份进行思考和发言。`,
    responseFormat: 'json',
    capabilities: ['analysis', 'strategy', 'decision_making', 'adaptation']
  },

  hunter_agent: {
    id: 'hunter_agent',
    name: '猎人AI代理',
    description: '狼人杀游戏中的猎人角色AI',
    personality: 'aggressive_just_reactive',
    systemPrompt: `你是一个狼人杀游戏中的猎人。你在死亡时可以开枪带走一名玩家。

游戏规则：
- 被投票出局或被狼人杀死时可以开枪
- 被女巫毒死时不能开枪
- 开枪选择要基于对游戏的判断
- 为好人阵营做最后贡献

性格特点：
- 具有攻击性和正义感
- 反应迅速，善于判断
- 注重公平和正义
- 在关键时刻发挥作用

请始终以猎人的身份进行思考和发言。`,
    responseFormat: 'json',
    capabilities: ['reasoning', 'justice', 'reactive', 'adaptation']
  },

  villager_agent: {
    id: 'villager_agent',
    name: '平民AI代理',
    description: '狼人杀游戏中的平民角色AI',
    personality: 'logical_analytical_cautious',
    systemPrompt: `你是一个狼人杀游戏中的平民。你的目标是通过观察和推理找出狼人。

游戏规则：
- 白天参与讨论，分析发言
- 投票放逐可疑玩家
- 没有特殊能力，依靠逻辑推理
- 保护神职玩家，找出狼人

性格特点：
- 善于逻辑分析
- 谨慎但有判断力
- 注重证据和推理
- 与好人阵营合作

请始终以平民的身份进行思考和发言。`,
    responseFormat: 'json',
    capabilities: ['reasoning', 'analysis', 'observation', 'adaptation']
  }
};

// 角色到代理类型的映射
export const roleToAgentType: Record<string, string> = {
  werewolf: 'werewolf_agent',
  seer: 'seer_agent',
  witch: 'witch_agent',
  hunter: 'hunter_agent',
  villager: 'villager_agent'
};

// AI响应时间配置（毫秒）
export const aiResponseTimes = {
  immediate: { min: 500, max: 2000 },      // 0.5-2秒
  fast: { min: 2000, max: 5000 },          // 2-5秒
  normal: { min: 5000, max: 10000 },       // 5-10秒
  slow: { min: 10000, max: 20000 }         // 10-20秒
};

// AI决策参数
export interface AIDecisionParams {
  context: any;
  gameState: any;
  role: string;
  personality: string;
  skillLevel: string;
  responseTime: string;
  language: string;
  creativityLevel: number;
  aggressiveness: number;
  cooperation: number;
}

// AgentScope消息格式
export interface AgentScopeMessage {
  id: string;
  type: 'request' | 'response';
  agentId: string;
  agentType: string;
  timestamp: Date;
  content: any;
  metadata?: {
    sessionId?: string;
    playerId?: string;
    gameId?: string;
    phase?: string;
    priority?: number;
  };
}

// AgentScope响应格式
export interface AgentScopeResponse {
  id: string;
  requestId: string;
  agentId: string;
  agentType: string;
  timestamp: Date;
  success: boolean;
  data?: any;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  processingTime: number;
}

// 游戏特定的AgentScope消息类型
export interface GameActionMessage extends AgentScopeMessage {
  content: {
    actionType: string;
    actionData: any;
    reasoning?: string;
    confidence?: number;
    alternatives?: any[];
  };
}

export interface PlayerSpeechMessage extends AgentScopeMessage {
  content: {
    speechContent: string;
    reasoning: string;
    tone: 'aggressive' | 'friendly' | 'neutral' | 'suspicious';
    targetPlayer?: string;
    confidence: number;
  };
}

export interface VoteDecisionMessage extends AgentScopeMessage {
  content: {
    targetPlayerId: string;
    targetPlayerName: string;
    reasoning: string;
    confidence: number;
    alternatives: Array<{
      playerId: string;
      playerName: string;
      score: number;
    }>;
  };
}

export interface RoleActionMessage extends AgentScopeMessage {
  content: {
    action: string;
    targetPlayer?: string;
    reasoning: string;
    priority: number;
    riskAssessment: number;
  };
}