import { GamePhase, RoleType, EventType } from './index';
import { PlayerInfo, GamePlayerInfo } from './player';
import { VotingCandidate } from './game';

// WebSocket消息基础类型
export interface WSMessage {
  type: string;
  timestamp: Date;
  payload?: any;
}

// 房间管理事件
export interface CreateRoomRequest {
  type: 'create_room';
  payload: {
    playerName: string;
    roomName?: string;
  };
}

export interface CreateRoomResponse {
  type: 'room_created';
  payload: {
    roomId: string;
    playerId: string;
    roomName?: string;
    creatorId: string;
  };
}

export interface JoinRoomRequest {
  type: 'join_room';
  payload: {
    roomId: string;
    playerName: string;
  };
}

export interface JoinRoomResponse {
  type: 'room_joined';
  payload: {
    roomId: string;
    playerId: string;
    roomInfo: {
      name?: string;
      creatorName: string;
      currentPlayers: number;
      maxPlayers: number;
    };
    players: PlayerInfo[];
  };
}

export interface JoinRoomError {
  type: 'room_join_error';
  payload: {
    error: string;
    code: 'ROOM_NOT_FOUND' | 'ROOM_FULL' | 'INVALID_NAME';
  };
}

export interface PlayerJoinedEvent {
  type: 'player_joined';
  payload: {
    playerId: string;
    playerName: string;
    playerCount: number;
    players: PlayerInfo[];
  };
}

export interface PlayerLeftEvent {
  type: 'player_left';
  payload: {
    playerId: string;
    playerName: string;
    playerCount: number;
  };
}

export interface RoomStatusUpdate {
  type: 'room_status_update';
  payload: {
    roomId: string;
    status: 'waiting' | 'playing' | 'finished';
    currentPlayers: number;
    players: PlayerInfo[];
  };
}

// 游戏管理事件
export interface StartGameRequest {
  type: 'start_game';
  payload: {
    playerId: string;
  };
}

export interface GameStartedEvent {
  type: 'game_started';
  payload: {
    gameId: string;
    players: GamePlayerInfo[];
    initialPhase: GamePhase;
    dayCount: number;
  };
}

export interface PhaseChangeEvent {
  type: 'phase_change';
  payload: {
    phase: GamePhase;
    dayCount: number;
    phaseStartTime: Date;
    nightInfo?: NightPhaseInfo;
    dayInfo?: DayPhaseInfo;
    votingInfo?: VotingPhaseInfo;
  };
}

// 夜晚阶段事件
export interface WerewolfActionRequest {
  type: 'werewolf_action';
  payload: {
    playerId: string;
    action: 'kill' | 'cancel';
    targetId?: string;
  };
}

export interface WerewolfTeamUpdate {
  type: 'werewolf_team_update';
  payload: {
    action: 'kill_selected' | 'kill_cancelled';
    targetId?: string;
    targetName?: string;
    actingPlayerId: string;
    remainingTime?: number;
  };
}

export interface SeerCheckRequest {
  type: 'seer_check';
  payload: {
    playerId: string;
    targetId: string;
  };
}

export interface SeerCheckResult {
  type: 'seer_check_result';
  payload: {
    targetId: string;
    targetName: string;
    result: 'werewolf' | 'good';
    nightNumber: number;
  };
}

export interface WitchActionRequest {
  type: 'witch_action';
  payload: {
    playerId: string;
    action: 'use_antidote' | 'use_poison' | 'skip';
    targetId?: string;
  };
}

export interface WitchInfoUpdate {
  type: 'witch_info_update';
  payload: {
    victimId?: string;
    victimName?: string;
    hasAntidote: boolean;
    hasPoison: boolean;
    remainingTime?: number;
  };
}

export interface WitchActionResult {
  type: 'witch_action_result';
  payload: {
    action: 'antidote_used' | 'poison_used' | 'skipped';
    targetId?: string;
    targetName?: string;
    success: boolean;
  };
}

// 白天阶段事件
export interface SheriffElectionStartEvent {
  type: 'sheriff_election_start';
  payload: {
    electionId: string;
    candidates: CandidateInfo[];
    speakingOrder: string[];
    speakingTimeLimit: number;
  };
}

export interface CandidateInfo {
  playerId: string;
  playerName: string;
  role?: RoleType;
  voteCount: number;
}

export interface SheriffCandidacyRequest {
  type: 'sheriff_candidacy';
  payload: {
    playerId: string;
    action: 'declare' | 'withdraw';
  };
}

export interface SheriffCandidateUpdate {
  type: 'sheriff_candidate_update';
  payload: {
    playerId: string;
    playerName: string;
    action: 'declared' | 'withdrew';
    currentCandidates: CandidateInfo[];
  };
}

export interface SheriffSpeechRequest {
  type: 'sheriff_speech';
  payload: {
    playerId: string;
    content: string;
  };
}

export interface SheriffSpeechEvent {
  type: 'sheriff_speech';
  payload: {
    playerId: string;
    playerName: string;
    content: string;
    timestamp: Date;
  };
}

export interface DiscussionSpeakRequest {
  type: 'discussion_speak';
  payload: {
    playerId: string;
    content: string;
  };
}

export interface DiscussionSpeakEvent {
  type: 'discussion_speak';
  payload: {
    playerId: string;
    playerName: string;
    content: string;
    timestamp: Date;
    speakingOrder: string[];
    currentSpeaker?: string;
  };
}

// 投票事件
export interface VotingStartEvent {
  type: 'voting_start';
  payload: {
    votingId: string;
    votingType: 'sheriff_election' | 'player_elimination';
    candidates: VotingCandidate[];
    votingTimeLimit: number;
    alivePlayers: string[];
  };
}

export interface PlayerVoteRequest {
  type: 'player_vote';
  payload: {
    playerId: string;
    targetId: string;
  };
}

export interface VotingProgress {
  type: 'voting_progress';
  payload: {
    votingId: string;
    totalVotes: number;
    candidateVotes: Array<{
      targetId: string;
      targetName: string;
      voteCount: number;
      voteWeight: number;
    }>;
    remainingVoters: string[];
  };
}

export interface VotingResultEvent {
  type: 'voting_result';
  payload: {
    votingId: string;
    winner?: {
      playerId: string;
      playerName: string;
      voteCount: number;
      voteWeight: number;
    };
    eliminated?: {
      playerId: string;
      playerName: string;
      role?: RoleType;
    };
    sheriffInfluence?: boolean;
    totalVotes: number;
  };
}

// 死亡事件
export interface PlayerDeathEvent {
  type: 'player_death';
  payload: {
    playerId: string;
    playerName: string;
    role?: RoleType;
    deathCause: DeathCause;
    dayCount: number;
    timestamp: Date;
  };
}

export interface HunterShootRequest {
  type: 'hunter_shoot';
  payload: {
    playerId: string;
    targetId: string;
  };
}

export interface HunterShootEvent {
  type: 'hunter_shoot';
  payload: {
    hunterId: string;
    hunterName: string;
    targetId: string;
    targetName: string;
    timestamp: Date;
  };
}

// 游戏结束事件
export interface GameOverEvent {
  type: 'game_over';
  payload: {
    winner: Team;
    gameDuration: number;
    totalDays: number;
    finalRoles: Array<{
      playerId: string;
      playerName: string;
      role: RoleType;
      survived: boolean;
    }>;
    gameId: string;
    canReplay: boolean;
  };
}

// 回放系统事件
export interface ReplayAccessRequest {
  type: 'replay_access';
  payload: {
    gameId: string;
  };
}

export interface ReplayAccessResponse {
  type: 'replay_access_response';
  payload: {
    success: boolean;
    gameInfo?: {
      gameId: string;
      duration: number;
      totalDays: number;
      winner: Team;
      playerCount: number;
    };
    error?: string;
  };
}

export interface ReplayDaySelectRequest {
  type: 'replay_day_select';
  payload: {
    gameId: string;
    dayNumber: number;
  };
}

export interface ReplayDaySnapshot {
  type: 'replay_day_snapshot';
  payload: {
    dayNumber: number;
    playerStates: any[];
    gameState: any;
    availableEvents: any[];
  };
}

export interface ReplayPlaybackRequest {
  type: 'replay_playback';
  payload: {
    gameId: string;
    action: 'play' | 'pause' | 'stop' | 'seek';
    timestamp?: number;
    speed?: number;
  };
}

export interface ReplayEventPlayback {
  type: 'replay_event_playback';
  payload: {
    event: GameEvent;
    playbackTime: number;
    speed: number;
    isPlaying: boolean;
  };
}

// 错误事件
export interface ErrorEvent {
  type: 'error';
  payload: {
    code: ErrorCode;
    message: string;
    details?: any;
    timestamp: Date;
  };
}

export enum ErrorCode {
  CONNECTION_FAILED = 'connection_failed',
  ROOM_NOT_FOUND = 'room_not_found',
  ROOM_FULL = 'room_full',
  INVALID_PLAYER_NAME = 'invalid_player_name',
  GAME_NOT_STARTED = 'game_not_started',
  INVALID_PHASE = 'invalid_phase',
  ACTION_NOT_ALLOWED = 'action_not_allowed',
  INVALID_VOTE_TARGET = 'invalid_vote_target',
  ALREADY_VOTED = 'already_voted',
  INSUFFICIENT_PERMISSIONS = 'insufficient_permissions',
  ROLE_REQUIRED = 'role_required',
  INTERNAL_ERROR = 'internal_error',
  TIMEOUT = 'timeout'
}

// 连接管理事件
export interface ConnectionEstablishedEvent {
  type: 'connection_established';
  payload: {
    connectionId: string;
    timestamp: Date;
    serverTime: Date;
  };
}

export interface HeartbeatRequest {
  type: 'heartbeat';
  payload: {
    timestamp: Date;
  };
}

export interface HeartbeatResponse {
  type: 'heartbeat_response';
  payload: {
    timestamp: Date;
    serverTime: Date;
  };
}

export interface ReconnectRequest {
  type: 'reconnect';
  payload: {
    playerId: string;
    roomId: string;
    lastEventId?: string;
  };
}

export interface ReconnectResponse {
  type: 'reconnect_response';
  payload: {
    success: boolean;
    missedEvents?: GameEvent[];
    currentGameState?: GameState;
  };
}

// 辅助接口
export interface NightPhaseInfo {
  duration: number;
  werewolves: string[];
  seer?: string;
  witch?: string;
}

export interface DayPhaseInfo {
  duration: number;
  speakingOrder: string[];
  currentSpeaker?: string;
}

export interface VotingPhaseInfo {
  duration: number;
  candidates: VotingCandidate[];
  sheriffId?: string;
}