import { agentscopeConfig, agentTypeConfigs, roleToAgentType, aiResponseTimes } from '@/config/agentscope';
import {
  AgentScopeMessage,
  AgentScopeResponse,
  GameActionMessage,
  PlayerSpeechMessage,
  VoteDecisionMessage,
  RoleActionMessage,
  AIDecisionParams
} from '@/config/agentscope';
import { RoleType, PersonalityType, SkillLevel, ResponseTime, StrategyType } from '@/types';
import { logger } from '@/utils/logger';

export class AgentScopeService {
  private static instance: AgentScopeService;
  private agents: Map<string, any> = new Map();
  private messageQueue: Map<string, AgentScopeMessage[]> = new Map();

  private constructor() {}

  public static getInstance(): AgentScopeService {
    if (!AgentScopeService.instance) {
      AgentScopeService.instance = new AgentScopeService();
    }
    return AgentScopeService.instance;
  }

  // 初始化AgentScope服务
  async initialize(): Promise<void> {
    try {
      logger.info('Initializing AgentScope service...');

      // 这里应该连接到实际的AgentScope服务
      // 暂时使用模拟实现
      await this.connectToAgentScope();

      logger.info('AgentScope service initialized successfully');
    } catch (error) {
      logger.error('Failed to initialize AgentScope service:', error);
      throw error;
    }
  }

  // 连接到AgentScope服务
  private async connectToAgentScope(): Promise<void> {
    // 实际实现中这里会建立与AgentScope的连接
    logger.info(`Connecting to AgentScope at ${agentscopeConfig.baseUrl}`);

    // 模拟连接成功
    // await this.testConnection();
  }

  // 创建AI代理
  async createAgent(
    playerId: string,
    playerName: string,
    role: RoleType,
    personality: PersonalityType,
    skillLevel: SkillLevel,
    responseTime: ResponseTime
  ): Promise<string> {
    try {
      const agentType = roleToAgentType[role];
      if (!agentType) {
        throw new Error(`No agent type configured for role: ${role}`);
      }

      const agentConfig = agentTypeConfigs[agentType];
      if (!agentConfig) {
        throw new Error(`Agent type config not found: ${agentType}`);
      }

      const agentId = `agent-${playerId}`;

      // 创建AgentScope代理
      const agent = {
        id: agentId,
        name: `${playerName} (${role})`,
        type: agentType,
        personality,
        skillLevel,
        responseTime,
        config: agentConfig,
        createdAt: new Date(),
        lastActive: new Date()
      };

      this.agents.set(agentId, agent);
      this.messageQueue.set(agentId, []);

      logger.info(`Created AgentScope agent: ${agentId} for player ${playerName} as ${role}`);

      return agentId;
    } catch (error) {
      logger.error(`Failed to create agent for player ${playerId}:`, error);
      throw error;
    }
  }

  // 发送消息到代理
  async sendMessageToAgent(
    agentId: string,
    message: AgentScopeMessage
  ): Promise<AgentScopeResponse> {
    try {
      const agent = this.agents.get(agentId);
      if (!agent) {
        throw new Error(`Agent not found: ${agentId}`);
      }

      logger.debug(`Sending message to agent ${agentId}:`, message.type);

      // 模拟处理延迟
      const delay = this.calculateResponseDelay(agent.responseTime);
      await this.delay(delay);

      // 模拟AgentScope响应
      const response = await this.processAgentMessage(agent, message);

      // 更新代理活跃时间
      agent.lastActive = new Date();

      logger.debug(`Received response from agent ${agentId}:`, response.success ? 'success' : 'error');

      return response;
    } catch (error) {
      logger.error(`Failed to send message to agent ${agentId}:`, error);
      throw error;
    }
  }

  // 处理代理消息
  private async processAgentMessage(
    agent: any,
    message: AgentScopeMessage
  ): Promise<AgentScopeResponse> {
    const startTime = Date.now();

    try {
      let responseData: any;

      switch (message.type) {
        case 'game_action':
          responseData = await this.processGameAction(agent, message as GameActionMessage);
          break;
        case 'player_speech':
          responseData = await this.processPlayerSpeech(agent, message as PlayerSpeechMessage);
          break;
        case 'vote_decision':
          responseData = await this.processVoteDecision(agent, message as VoteDecisionMessage);
          break;
        case 'role_action':
          responseData = await this.processRoleAction(agent, message as RoleActionMessage);
          break;
        default:
          throw new Error(`Unknown message type: ${message.type}`);
      }

      const processingTime = Date.now() - startTime;

      return {
        id: this.generateId(),
        requestId: message.id,
        agentId: agent.id,
        agentType: agent.type,
        timestamp: new Date(),
        success: true,
        data: responseData,
        processingTime
      };
    } catch (error) {
      const processingTime = Date.now() - startTime;

      return {
        id: this.generateId(),
        requestId: message.id,
        agentId: agent.id,
        agentType: agent.type,
        timestamp: new Date(),
        success: false,
        error: {
          code: 'PROCESSING_ERROR',
          message: error instanceof Error ? error.message : 'Unknown error',
          details: error
        },
        processingTime
      };
    }
  }

  // 处理游戏动作
  private async processGameAction(
    agent: any,
    message: GameActionMessage
  ): Promise<any> {
    const { actionType, actionData } = message.content;

    logger.debug(`Processing game action ${actionType} for agent ${agent.id}`);

    // 这里应该调用实际的AgentScope API
    // 暂时返回模拟响应
    const response = {
      action: actionType,
      result: 'success',
      target: actionData.targetId,
      reasoning: this.generateReasoning(agent, actionType),
      confidence: this.calculateConfidence(agent.skillLevel)
    };

    return response;
  }

  // 处理玩家发言
  private async processPlayerSpeech(
    agent: any,
    message: PlayerSpeechMessage
  ): Promise<any> {
    const { speechContent, reasoning, tone, targetPlayer } = message.content;

    logger.debug(`Processing speech for agent ${agent.id}: ${speechContent.substring(0, 50)}...`);

    // 模拟AI发言生成
    const response = {
      speechContent: speechContent,
      reasoning: reasoning || this.generateSpeechReasoning(agent),
      tone: tone || 'neutral',
      targetPlayer: targetPlayer,
      confidence: this.calculateConfidence(agent.skillLevel),
      characterCount: speechContent.length
    };

    return response;
  }

  // 处理投票决策
  private async processVoteDecision(
    agent: any,
    message: VoteDecisionMessage
  ): Promise<any> {
    const { targetPlayerId, targetPlayerName, reasoning, alternatives } = message.content;

    logger.debug(`Processing vote decision for agent ${agent.id}: voting for ${targetPlayerName}`);

    const response = {
      targetPlayerId,
      targetPlayerName,
      reasoning: reasoning || this.generateVoteReasoning(agent, targetPlayerName),
      confidence: this.calculateConfidence(agent.skillLevel),
      alternatives: alternatives || this.generateVoteAlternatives(agent, targetPlayerId)
    };

    return response;
  }

  // 处理角色行动
  private async processRoleAction(
    agent: any,
    message: RoleActionMessage
  ): Promise<any> {
    const { action, targetPlayer, reasoning, priority, riskAssessment } = message.content;

    logger.debug(`Processing role action ${action} for agent ${agent.id}`);

    const response = {
      action,
      targetPlayer: targetPlayer,
      reasoning: reasoning || this.generateRoleActionReasoning(agent, action),
      priority: priority || 5,
      riskAssessment: riskAssessment || this.calculateRiskAssessment(agent, action),
      success: Math.random() > 0.1 // 90%成功率
    };

    return response;
  }

  // 计算响应延迟
  private calculateResponseDelay(responseTime: string): number {
    const config = aiResponseTimes[responseTime as keyof typeof aiResponseTimes];
    if (!config) {
      return aiResponseTimes.normal.min;
    }

    const range = config.max - config.min;
    return config.min + Math.random() * range;
  }

  // 生成推理
  private generateReasoning(agent: any, actionType: string): string {
    const reasonings = {
      werewolf_kill: `基于当前局势，我认为击杀目标是最优选择`,
      seer_check: `根据玩家行为分析，我需要查验此人来获取更多信息`,
      witch_antidote: `考虑到游戏平衡，救活这个玩家对好人阵营更有利`,
      witch_poison: `根据我的判断，这个玩家很可能是狼人，应该毒死`,
      hunter_shoot: `基于我的观察，这个玩家是最可疑的目标`,
      vote_eliminate: `通过分析所有发言，我认为应该投票给这个玩家`
    };

    return reasonings[actionType] || `基于当前游戏状态和我的角色分析`;
  }

  // 生成发言推理
  private generateSpeechReasoning(agent: any): string {
    return `根据当前的游戏进展和获得的信息，我需要表达我的观点并引导讨论方向`;
  }

  // 生成投票推理
  private generateVoteReasoning(agent: any, targetName: string): string {
    return `通过分析${targetName}的发言和行为，我认为他最可能是狼人`;
  }

  // 生成投票备选项
  private generateVoteAlternatives(agent: any, excludedId: string): any[] {
    // 模拟生成其他投票选项
    return [
      { playerId: 'alt-1', playerName: 'Alternative Player 1', score: 0.7 },
      { playerId: 'alt-2', playerName: 'Alternative Player 2', score: 0.5 }
    ];
  }

  // 生成角色行动推理
  private generateRoleActionReasoning(agent: any, action: string): string {
    const reasonings = {
      seer_check: `查验这个玩家可以获得关键的阵营信息`,
      witch_save: `救活这个玩家可以维持人数优势`,
      witch_poison: `毒死这个玩家可以减少威胁`,
      hunter_shoot: `带走这个可疑玩家可以为好人阵营做贡献`
    };

    return reasonings[action] || `基于我的角色能力和当前局势判断`;
  }

  // 计算信心度
  private calculateConfidence(skillLevel: string): number {
    const baseConfidence = {
      beginner: 0.6,
      intermediate: 0.75,
      advanced: 0.85,
      expert: 0.95
    };

    const confidence = baseConfidence[skillLevel as keyof typeof baseConfidence] || 0.75;
    return confidence + (Math.random() - 0.5) * 0.2; // 添加一些随机性
  }

  // 计算风险评估
  private calculateRiskAssessment(agent: any, action: string): number {
    // 根据代理技能级别和行动类型评估风险
    const skillRiskFactor = {
      beginner: 0.8,
      intermediate: 0.6,
      advanced: 0.4,
      expert: 0.2
    };

    const actionRiskFactor = {
      safe: 0.2,
      moderate: 0.5,
      risky: 0.8
    };

    const baseRisk = skillRiskFactor[agent.skillLevel as keyof typeof skillRiskFactor] || 0.5;
    const actionRisk = actionRiskFactor.risky; // 默认风险

    return Math.min(1.0, baseRisk + actionRisk);
  }

  // 生成唯一ID
  private generateId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // 延迟函数
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // 获取代理信息
  getAgentInfo(agentId: string): any | null {
    return this.agents.get(agentId) || null;
  }

  // 获取所有代理
  getAllAgents(): any[] {
    return Array.from(this.agents.values());
  }

  // 移除代理
  removeAgent(agentId: string): boolean {
    const removed = this.agents.delete(agentId);
    this.messageQueue.delete(agentId);

    if (removed) {
      logger.info(`Removed agent: ${agentId}`);
    }

    return removed;
  }

  // 更新代理状态
  updateAgentStatus(agentId: string, status: any): void {
    const agent = this.agents.get(agentId);
    if (agent) {
      Object.assign(agent, status);
      agent.lastActive = new Date();
      logger.debug(`Updated agent ${agentId} status:`, status);
    }
  }

  // 健康检查
  async healthCheck(): Promise<{ status: string; agentCount: number; lastCheck: Date }> {
    return {
      status: 'healthy',
      agentCount: this.agents.size,
      lastCheck: new Date()
    };
  }

  // 关闭服务
  async shutdown(): Promise<void> {
    logger.info('Shutting down AgentScope service...');

    // 清理所有代理
    this.agents.clear();
    this.messageQueue.clear();

    logger.info('AgentScope service shutdown complete');
  }
}