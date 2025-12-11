// 游戏角色
export type RoleType = 'werewolf' | 'villager' | 'seer' | 'witch' | 'hunter';

// 游戏阶段
export type GamePhaseType = 'night' | 'sheriff_election' | 'day_discussion' | 'voting' | 'game_over';

// 玩家状态
export type PlayerStatus = 'alive' | 'dead';

// 事件类别
export type EventCategory = 'MODERATOR' | 'SPEECH' | 'ACTION' | 'VOTE' | 'DEATH' | 'SYSTEM';

// 角色信息
export interface RoleInfo {
  type: RoleType;
  name: string;
  team: 'werewolf' | 'villager';
  icon: string;
  color: string;
}

// 角色能力状态
export interface RoleAbilities {
  witchHasAntidote?: boolean;
  witchHasPoison?: boolean;
  hunterCanShoot?: boolean;
}

// LLM 配置
export interface LLMConfig {
  provider: 'anthropic' | 'openai' | 'dashscope';
  apiKey: string;
  modelName: string;
  temperature?: number;
  stream?: boolean;
  enableThinking?: boolean;
  clientKwargs?: Record<string, any>;
}

// 房间状态
export type RoomStatus = 'waiting' | 'ready' | 'playing' | 'finished';

// 视图状态
export type ViewType = 'home' | 'create-room' | 'room-setup' | 'game';

// 房间信息
export interface Room {
  id: string;
  name: string;
  currentPlayers: number;
  maxPlayers: number;
  isFull: boolean;
  canStartGame: boolean;
  status: RoomStatus;
  players: RoomPlayer[];
}

// 房间玩家
export interface RoomPlayer {
  id: string;
  name: string;
  position: number;
  isAI: boolean;
  llmConfig?: LLMConfig;
  role?: string;
  status?: string;
}

// 玩家
export interface Player {
  id: string;
  name: string;
  position: number;
  role?: RoleType;
  status: PlayerStatus;
  isSheriff: boolean;
  votingWeight: number;
  abilities?: RoleAbilities;
}

// 游戏事件
export interface GameEvent {
  id: string;
  timestamp: string;
  day: number;
  phase: GamePhaseType;
  category: EventCategory;
  content: string;
  actorId?: string;
  actorName?: string;
  targetId?: string;
  targetName?: string;
}

// 游戏状态
export interface GameState {
  id: string;
  roomId: string;
  day: number;
  phase: GamePhaseType;
  players: Player[];
  events: GameEvent[];
  sheriffId?: string;
  winner?: 'werewolf' | 'villager';
  isRunning: boolean;
}

// 角色配置
export const ROLE_CONFIG: Record<RoleType, RoleInfo> = {
  werewolf: {
    type: 'werewolf',
    name: '狼人',
    team: 'werewolf',
    icon: '🐺',
    color: '#dc2626'
  },
  villager: {
    type: 'villager', 
    name: '平民',
    team: 'villager',
    icon: '👤',
    color: '#059669'
  },
  seer: {
    type: 'seer',
    name: '预言家',
    team: 'villager',
    icon: '🔮',
    color: '#7c3aed'
  },
  witch: {
    type: 'witch',
    name: '女巫',
    team: 'villager',
    icon: '🧪',
    color: '#0891b2'
  },
  hunter: {
    type: 'hunter',
    name: '猎人',
    team: 'villager',
    icon: '🎯',
    color: '#ca8a04'
  }
};

// 阶段配置
export const PHASE_CONFIG: Record<GamePhaseType, { name: string; icon: string; color: string }> = {
  night: { name: '夜晚', icon: '🌙', color: '#1e3a5f' },
  sheriff_election: { name: '警长竞选', icon: '🎖️', color: '#7c3aed' },
  day_discussion: { name: '白天讨论', icon: '☀️', color: '#f59e0b' },
  voting: { name: '投票放逐', icon: '🗳️', color: '#ef4444' },
  game_over: { name: '游戏结束', icon: '🏆', color: '#10b981' }
};

// 事件类别配置
export const EVENT_CATEGORY_CONFIG: Record<EventCategory, { name: string; color: string; icon: string }> = {
  MODERATOR: { name: '主持人', color: '#f59e0b', icon: '📢' },
  SPEECH: { name: '发言', color: '#3b82f6', icon: '💬' },
  ACTION: { name: '行动', color: '#8b5cf6', icon: '⚡' },
  VOTE: { name: '投票', color: '#ef4444', icon: '🗳️' },
  DEATH: { name: '死亡', color: '#6b7280', icon: '💀' },
  SYSTEM: { name: '系统', color: '#6b7280', icon: '⚙️' }
};


