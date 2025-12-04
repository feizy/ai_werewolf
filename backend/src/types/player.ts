import {
  PlayerType,
  PlayerStatus,
  ConnectionState,
  RoleType,
  PersonalityType,
  SkillLevel,
  ResponseTime,
  StrategyType
} from './index';

// AI玩家配置
export interface AIPlayerConfig {
  agentType: string;
  personality: PersonalityType;
  skillLevel: SkillLevel;
  responseTime: ResponseTime;
  strategy: StrategyType;
  language: 'zh' | 'en';
  creativityLevel: number;      // 0-1
  aggressiveness: number;      // 0-1
  cooperation: number;         // 0-1
}

// 角色能力状态
export interface RoleAbilities {
  // 预言家能力
  seerInfo?: {
    checksRemaining: number;
    lastCheckedPlayerId?: string;
    checkResults: CheckResult[];
  };

  // 女巫能力
  witchInfo?: {
    hasAntidote: boolean;
    hasPoison: boolean;
    antidoteUsed: boolean;
    poisonUsed: boolean;
    poisonTargetId?: string;
    lastNightVictimId?: string;
  };

  // 猎人能力
  hunterInfo?: {
    canShoot: boolean;
    hasShot: boolean;
    shotTargetId?: string;
    deathCause?: DeathCause;
  };
}

export interface CheckResult {
  targetPlayerId: string;
  targetName: string;
  result: 'werewolf' | 'good';
  nightNumber: number;
  timestamp: Date;
}

// 玩家实体
export interface Player {
  id: string;
  name: string;
  roomId: string;
  type: PlayerType;
  role?: RoleType;
  status: PlayerStatus;
  position: number;
  connectionState: ConnectionState;
  joinedAt: Date;
  lastActiveAt: Date;
  // AI特有属性
  aiConfig: AIPlayerConfig;
  agentScopeId: string;
  // 角色特有属性
  roleAbilities?: RoleAbilities;
  // 投票相关
  votingWeight: number;
}

// 角色定义
export interface Role {
  type: RoleType;
  team: Team;
  abilities: RoleAbility[];
  visibility: VisibilityRules;
}

export interface RoleAbility {
  name: string;
  description: string;
  usageLimit?: number;
  activeDuring: GamePhase[];
}

export interface VisibilityRules {
  teamVisibility: boolean;      // 是否能看到队友
  roleReveal: RoleType[];       // 在哪些条件下揭露角色
  eventVisibility: EventType[]; // 能看到哪些事件类型
}

// 玩家信息（用于API响应）
export interface PlayerInfo {
  playerId: string;
  playerName: string;
  type: 'human' | 'ai';
  position?: number;
  joinedAt: Date;
}

export interface GamePlayerInfo extends PlayerInfo {
  role: RoleType;
  status: 'alive' | 'dead';
  votingWeight: number;
}

export interface ReplayPlayerState {
  playerId: string;
  playerName: string;
  role: RoleType;
  status: 'alive' | 'dead';
  position: number;
  abilities?: {
    witchAntidote: boolean;
    witchPoison: boolean;
    hunterCanShoot: boolean;
  };
}