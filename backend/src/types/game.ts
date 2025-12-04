import { GamePhase, RoomStatus, VotingType, DeathCause, EventType, Team } from './index';
import { Player, GamePlayerInfo } from './player';

// 游戏房间
export interface GameRoom {
  id: string;
  name?: string;
  creatorId: string;
  maxPlayers: number;
  currentPlayers: number;
  status: RoomStatus;
  gameConfig: GameConfiguration;
  createdAt: Date;
  startedAt?: Date;
  endedAt?: Date;
}

export interface GameConfiguration {
  roleDistribution: RoleDistribution;
  phaseDurations: PhaseDurations;
  aiConfigurations: AIConfigurationTemplate[];
  maxPlayers: number;
  gameMode: 'classic' | 'custom';
}

export interface RoleDistribution {
  werewolf: number;
  villager: number;
  seer: number;
  witch: number;
  hunter: number;
}

export interface PhaseDurations {
  night: number;                    // 秒
  sheriffElection: number;          // 秒
  dayDiscussion: number;            // 秒
  voting: number;                   // 秒
}

export interface AIConfigurationTemplate {
  roleType: RoleType;
  personality: PersonalityType;
  skillLevel: SkillLevel;
  responseTime: ResponseTime;
  strategy: StrategyType;
}

// 游戏会话
export interface GameSession {
  id: string;
  roomId: string;
  players: Player[];
  gameState: GameState;
  dayCount: number;
  currentPhase: GamePhase;
  phaseStartTime: Date;
  events: GameEvent[];
  dailySnapshots: DailySnapshot[];
  winner?: Team;
  endedAt?: Date;
}

// 游戏状态
export interface GameState {
  phase: GamePhase;
  dayCount: number;
  players: PlayerState[];
  sheriff?: SheriffState;
  // 夜晚阶段特有状态
  nightActions?: NightActions;
  // 白天阶段特有状态
  dayPhase?: DayPhaseState;
  // 投票阶段特有状态
  voting?: VotingState;
}

export interface PlayerState {
  playerId: string;
  playerName: string;
  role: RoleType;
  status: PlayerStatus;
  position: number;
  abilities?: RoleAbilities;
  votingWeight: number;
}

export interface SheriffState {
  playerId: string;
  playerName: string;
  hasLastWord: boolean;
  canTransfer: boolean;
  transferredToId?: string;
}

// 夜晚行动状态
export interface NightActions {
  werewolfTarget?: {
    playerId: string;
    playerName: string;
    agreedBy: string[];             // 同意的狼人ID
  };
  seerCheck?: {
    targetId: string;
    targetName: string;
    result?: 'werewolf' | 'good';
  };
  witchAction?: {
    action: 'antidote' | 'poison' | 'skip';
    targetId?: string;
    targetName?: string;
  };
}

// 白天阶段状态
export interface DayPhaseState {
  speakerQueue: string[];
  currentSpeaker?: string;
  speakingTimeLimit: number;
  messages: DiscussionMessage[];
}

export interface DiscussionMessage {
  playerId: string;
  playerName: string;
  content: string;
  timestamp: Date;
  characterCount: number;
}

// 投票状态
export interface VotingState {
  id: string;
  type: VotingType;
  candidates: VotingCandidate[];
  votes: Vote[];
  status: 'active' | 'completed';
  startTime: Date;
  endTime?: Date;
  result?: VotingResult;
}

export interface VotingCandidate {
  playerId: string;
  playerName: string;
  role?: RoleType;
  voteCount: number;
  voteWeight: number;
}

export interface Vote {
  voterId: string;
  voterName: string;
  candidateId: string;
  weight: number;
  timestamp: Date;
}

export interface VotingResult {
  winner?: VotingCandidate;
  eliminated?: VotingCandidate;
  tiedCandidates?: VotingCandidate[];
  totalVotes: number;
  sheriffInfluence?: boolean;
}

// 游戏事件
export interface GameEvent {
  id: string;
  sessionId: string;
  type: EventType;
  phase: GamePhase;
  dayCount: number;
  timestamp: Date;
  // 事件参与者
  actorId?: string;
  actorName?: string;
  targetId?: string;
  targetName?: string;
  // 事件内容
  content: string;
  details?: EventDetails;
  // 可见性控制
  visibility: EventVisibility;
}

export interface EventDetails {
  [key: string]: any;
  // 预言家查验详情
  seerCheckResult?: 'werewolf' | 'good';
  // 女巫行动详情
  witchAction?: {
    action: 'antidote' | 'poison';
    success: boolean;
  };
  // 投票详情
  votingDetails?: {
    candidateId: string;
    voteCount: number;
    sheriffInfluence: boolean;
  };
  // 死亡详情
  deathDetails?: {
    cause: DeathCause;
    killer?: string;
  };
}

export interface EventVisibility {
  public: boolean;
  visibleToRoles?: RoleType[];
  visibleToPlayers?: string[];
  requiresRoleReveal?: boolean;
}

// 每日快照
export interface DailySnapshot {
  id: string;
  sessionId: string;
  dayNumber: number;
  timestamp: Date;
  playerStates: PlayerState[];
  gameState: Partial<GameState>;
  events: GameEvent[];
}

// 回放相关
export interface ReplayEventInfo {
  eventId: string;
  type: EventType;
  timestamp: Date;
  description: string;
  participants: string[];
}

export interface ReplayDaySnapshot {
  dayNumber: number;
  playerStates: ReplayPlayerState[];
  gameState: {
    phase: GamePhase;
    sheriff?: {
      playerId: string;
      playerName: string;
    };
    alivePlayers: number;
  };
  availableEvents: ReplayEventInfo[];
}