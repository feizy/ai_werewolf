import { v4 as uuidv4 } from 'uuid';
import {
  Player,
  PlayerType,
  PlayerStatus,
  ConnectionState,
  RoleType,
  Team,
  PersonalityType,
  SkillLevel,
  ResponseTime,
  StrategyType,
  AIPlayerConfig,
  RoleAbilities,
  CheckResult
} from '@/types';

export class PlayerModel implements Player {
  public readonly id: string;
  public name: string;
  public roomId: string;
  public type: PlayerType = PlayerType.AI;
  public role?: RoleType;
  public status: PlayerStatus;
  public position: number;
  public connectionState: ConnectionState;
  public joinedAt: Date;
  public lastActiveAt: Date;
  public aiConfig: AIPlayerConfig;
  public agentScopeId: string;
  public roleAbilities?: RoleAbilities;
  public votingWeight: number;

  constructor(data: Partial<Player>) {
    this.id = data.id || uuidv4();
    this.name = data.name || 'AI-Player';
    this.roomId = data.roomId || '';
    this.status = data.status || PlayerStatus.ALIVE;
    this.position = data.position || 0;
    this.connectionState = data.connectionState || ConnectionState.ACTIVE;
    this.joinedAt = data.joinedAt || new Date();
    this.lastActiveAt = data.lastActiveAt || new Date();
    this.aiConfig = data.aiConfig || this.getDefaultAIConfig();
    this.agentScopeId = data.agentScopeId || `agent-${this.id}`;
    this.votingWeight = data.votingWeight || 1.0;

    if (data.role) {
      this.role = data.role;
    }
    if (data.roleAbilities) {
      this.roleAbilities = data.roleAbilities;
    }
  }

  private getDefaultAIConfig(): AIPlayerConfig {
    return {
      agentType: 'werewolf_player',
      personality: PersonalityType.BALANCED,
      skillLevel: SkillLevel.INTERMEDIATE,
      responseTime: ResponseTime.NORMAL,
      strategy: StrategyType.LOGICAL,
      language: 'zh',
      creativityLevel: 0.5,
      aggressiveness: 0.5,
      cooperation: 0.5
    };
  }

  // 设置角色
  setRole(role: RoleType): void {
    this.role = role;
    this.initializeRoleAbilities(role);
  }

  // 初始化角色能力
  private initializeRoleAbilities(role: RoleType): void {
    this.roleAbilities = {};

    switch (role) {
      case RoleType.SEER:
        this.roleAbilities.seerInfo = {
          checksRemaining: 1,
          checkResults: []
        };
        break;

      case RoleType.WITCH:
        this.roleAbilities.witchInfo = {
          hasAntidote: true,
          hasPoison: true,
          antidoteUsed: false,
          poisonUsed: false
        };
        break;

      case RoleType.HUNTER:
        this.roleAbilities.hunterInfo = {
          canShoot: true,
          hasShot: false
        };
        break;
    }
  }

  // 检查是否存活
  isAlive(): boolean {
    return this.status === PlayerStatus.ALIVE;
  }

  // 获取所属阵营
  getTeam(): Team {
    if (!this.role) throw new Error('Role not assigned');

    switch (this.role) {
      case RoleType.WEREWOLF:
        return Team.WEREWOLF;
      case RoleType.SEER:
      case RoleType.WITCH:
      case RoleType.HUNTER:
      case RoleType.VILLAGER:
        return Team.GOOD;
      default:
        throw new Error(`Unknown role: ${this.role}`);
    }
  }

  // 设置死亡状态
  setDead(cause: string): void {
    this.status = PlayerStatus.DEAD;
    this.connectionState = ConnectionState.INACTIVE;

    if (this.roleAbilities?.hunterInfo) {
      this.roleAbilities.hunterInfo.deathCause = cause as any;
    }
  }

  // 预言家查验
  seerCheck(targetId: string, targetName: string, result: 'werewolf' | 'good'): void {
    if (!this.roleAbilities?.seerInfo) {
      throw new Error('Player is not a seer');
    }

    if (this.roleAbilities.seerInfo.checksRemaining <= 0) {
      throw new Error('No seer checks remaining');
    }

    this.roleAbilities.seerInfo.checksRemaining = 0;
    this.roleAbilities.seerInfo.lastCheckedPlayerId = targetId;
    this.roleAbilities.seerInfo.checkResults.push({
      targetPlayerId: targetId,
      targetName,
      result,
      nightNumber: 1, // 这个值需要从游戏状态获取
      timestamp: new Date()
    });
  }

  // 女巫使用解药
  useAntidote(): void {
    if (!this.roleAbilities?.witchInfo) {
      throw new Error('Player is not a witch');
    }

    if (!this.roleAbilities.witchInfo.hasAntidote) {
      throw new Error('No antidote available');
    }

    this.roleAbilities.witchInfo.hasAntidote = false;
    this.roleAbilities.witchInfo.antidoteUsed = true;
  }

  // 女巫使用毒药
  usePoison(targetId: string): void {
    if (!this.roleAbilities?.witchInfo) {
      throw new Error('Player is not a witch');
    }

    if (!this.roleAbilities.witchInfo.hasPoison) {
      throw new Error('No poison available');
    }

    this.roleAbilities.witchInfo.hasPoison = false;
    this.roleAbilities.witchInfo.poisonUsed = true;
    this.roleAbilities.witchInfo.poisonTargetId = targetId;
  }

  // 猎人开枪
  hunterShoot(targetId: string): void {
    if (!this.roleAbilities?.hunterInfo) {
      throw new Error('Player is not a hunter');
    }

    if (!this.roleAbilities.hunterInfo.canShoot || this.roleAbilities.hunterInfo.hasShot) {
      throw new Error('Hunter cannot shoot');
    }

    this.roleAbilities.hunterInfo.canShoot = false;
    this.roleAbilities.hunterInfo.hasShot = true;
    this.roleAbilities.hunterInfo.shotTargetId = targetId;
  }

  // 重置夜晚能力（每天夜晚开始时调用）
  resetNightlyAbilities(): void {
    if (this.role === RoleType.SEER && this.roleAbilities?.seerInfo) {
      this.roleAbilities.seerInfo.checksRemaining = 1;
    }

    if (this.role === RoleType.WITCH && this.roleAbilities?.witchInfo) {
      this.roleAbilities.witchInfo.lastNightVictimId = undefined;
    }
  }

  // 获取当前状态摘要
  getSummary() {
    return {
      id: this.id,
      name: this.name,
      role: this.role,
      status: this.status,
      position: this.position,
      isAlive: this.isAlive(),
      team: this.role ? this.getTeam() : undefined,
      votingWeight: this.votingWeight,
      connectionState: this.connectionState
    };
  }

  // 更新最后活跃时间
  updateLastActive(): void {
    this.lastActiveAt = new Date();
  }

  // 设置处理状态（AI决策中）
  setProcessing(): void {
    this.status = PlayerStatus.PROCESSING;
    this.connectionState = ConnectionState.PROCESSING;
  }

  // 设置活跃状态
  setActive(): void {
    if (this.isAlive()) {
      this.status = PlayerStatus.ALIVE;
    }
    this.connectionState = ConnectionState.ACTIVE;
    this.updateLastActive();
  }

  // 设置为警长
  setAsSheriff(): void {
    this.votingWeight = 1.5;
  }

  // 取消警长身份
  removeSheriff(): void {
    this.votingWeight = 1.0;
  }

  // 转换为JSON对象
  toJSON(): Partial<Player> {
    return {
      id: this.id,
      name: this.name,
      roomId: this.roomId,
      type: this.type,
      role: this.role,
      status: this.status,
      position: this.position,
      connectionState: this.connectionState,
      joinedAt: this.joinedAt,
      lastActiveAt: this.lastActiveAt,
      votingWeight: this.votingWeight
    };
  }

  // 静态方法：创建AI玩家
  static createAIPlayer(name: string, roomId: string, position: number, config?: Partial<AIPlayerConfig>): PlayerModel {
    return new PlayerModel({
      name,
      roomId,
      position,
      type: PlayerType.AI,
      aiConfig: config
    });
  }

  // 静态方法：创建角色特定的AI玩家
  static createAIPlayerWithRole(
    name: string,
    roomId: string,
    position: number,
    role: RoleType,
    config?: Partial<AIPlayerConfig>
  ): PlayerModel {
    const player = PlayerModel.createAIPlayer(name, roomId, position, config);
    player.setRole(role);
    return player;
  }
}