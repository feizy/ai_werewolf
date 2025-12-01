# WebSocket API Contracts: Werewolf Game Backend

**Created**: 2025-12-01
**Feature**: 002-werewolf-backend
**Purpose**: Define WebSocket events and message contracts for real-time game communication

## Connection Management

### Room Events

#### create_room
创建新游戏房间

```typescript
// Client → Server
interface CreateRoomRequest {
  type: 'create_room';
  payload: {
    playerName: string;        // 玩家名称（必填）
    roomName?: string;         // 可选房间名称
  };
}

// Server → Client
interface CreateRoomResponse {
  type: 'room_created';
  payload: {
    roomId: string;            // 房间ID
    playerId: string;          // 玩家ID
    roomName?: string;         // 房间名称
    creatorId: string;         // 创建者ID
  };
}
```

#### join_room
加入现有游戏房间

```typescript
// Client → Server
interface JoinRoomRequest {
  type: 'join_room';
  payload: {
    roomId: string;            // 房间ID
    playerName: string;        // 玩家名称
  };
}

// Server → Client (成功)
interface JoinRoomResponse {
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
    players: PlayerInfo[];      // 当前所有玩家
  };
}

// Server → Client (失败)
interface JoinRoomError {
  type: 'room_join_error';
  payload: {
    error: string;              // 错误信息
    code: 'ROOM_NOT_FOUND' | 'ROOM_FULL' | 'INVALID_NAME';
  };
}
```

#### leave_room
离开游戏房间

```typescript
// Client → Server
interface LeaveRoomRequest {
  type: 'leave_room';
  payload: {
    playerId: string;
  };
}

// Server → Client (广播给房间内其他玩家)
interface PlayerLeftEvent {
  type: 'player_left';
  payload: {
    playerId: string;
    playerName: string;
    playerCount: number;       // 剩余玩家数
  };
}
```

#### room_status_update
房间状态更新（广播）

```typescript
interface RoomStatusUpdate {
  type: 'room_status_update';
  payload: {
    roomId: string;
    status: 'waiting' | 'playing' | 'finished';
    currentPlayers: number;
    players: PlayerInfo[];
  };
}
```

### Player Events

#### player_joined
玩家加入房间（广播）

```typescript
interface PlayerJoinedEvent {
  type: 'player_joined';
  payload: {
    playerId: string;
    playerName: string;
    playerCount: number;
    players: PlayerInfo[];      // 更新后的玩家列表
  };
}
```

#### player_disconnected
玩家断线（广播）

```typescript
interface PlayerDisconnectedEvent {
  type: 'player_disconnected';
  payload: {
    playerId: string;
    playerName: string;
    reconnecting: boolean;      // 是否在重连中
  };
}
```

#### player_reconnected
玩家重连（广播）

```typescript
interface PlayerReconnectedEvent {
  type: 'player_reconnected';
  payload: {
    playerId: string;
    playerName: string;
  };
}
```

## Game Management

### Game Control Events

#### start_game
开始游戏（仅房主）

```typescript
// Client → Server
interface StartGameRequest {
  type: 'start_game';
  payload: {
    playerId: string;
  };
}

// Server → Client
interface GameStartedEvent {
  type: 'game_started';
  payload: {
    gameId: string;             // 游戏会话ID
    players: GamePlayerInfo[];   // 包含角色分配的玩家信息
    initialPhase: GamePhase;     // 初始游戏阶段
    dayCount: number;            // 当前天数（通常为1）
  };
}
```

#### phase_change
游戏阶段变化（广播）

```typescript
interface PhaseChangeEvent {
  type: 'phase_change';
  payload: {
    phase: GamePhase;
    dayCount: number;
    phaseStartTime: Date;
    // 阶段特定信息
    nightInfo?: NightPhaseInfo;
    dayInfo?: DayPhaseInfo;
    votingInfo?: VotingPhaseInfo;
  };
}
```

### Night Phase Events

#### werewolf_action
狼人夜晚行动

```typescript
// Client → Server (仅狼人玩家)
interface WerewolfActionRequest {
  type: 'werewolf_action';
  payload: {
    playerId: string;
    action: 'kill' | 'cancel';  // 行动类型
    targetId?: string;           // 击杀目标
  };
}

// Server → Client (狼人团队)
interface WerewolfTeamUpdate {
  type: 'werewolf_team_update';
  payload: {
    action: 'kill_selected' | 'kill_cancelled';
    targetId?: string;
    targetName?: string;
    actingPlayerId: string;
    remainingTime?: number;     // 剩余行动时间
  };
}
```

#### seer_check
预言家查验

```typescript
// Client → Server (仅预言家)
interface SeerCheckRequest {
  type: 'seer_check';
  payload: {
    playerId: string;
    targetId: string;           // 查验目标
  };
}

// Server → Client (仅预言家)
interface SeerCheckResult {
  type: 'seer_check_result';
  payload: {
    targetId: string;
    targetName: string;
    result: 'werewolf' | 'good'; // 查验结果
    nightNumber: number;
  };
}
```

#### witch_action
女巫行动

```typescript
// Client → Server (仅女巫)
interface WitchActionRequest {
  type: 'witch_action';
  payload: {
    playerId: string;
    action: 'use_antidote' | 'use_poison' | 'skip';
    targetId?: string;           // 使用毒药时的目标
  };
}

// Server → Client (仅女巫)
interface WitchInfoUpdate {
  type: 'witch_info_update';
  payload: {
    victimId?: string;           // 今晚被狼人杀死的玩家
    victimName?: string;
    hasAntidote: boolean;       // 是否还有解药
    hasPoison: boolean;         // 是否还有毒药
    remainingTime?: number;
  };
}

// Server → Client (行动结果)
interface WitchActionResult {
  type: 'witch_action_result';
  payload: {
    action: 'antidote_used' | 'poison_used' | 'skipped';
    targetId?: string;
    targetName?: string;
    success: boolean;
  };
}
```

### Day Phase Events

#### sheriff_election_start
警长竞选开始（仅第一天）

```typescript
interface SheriffElectionStartEvent {
  type: 'sheriff_election_start';
  payload: {
    electionId: string;
    candidates: CandidateInfo[];  // 当前候选人
    speakingOrder: string[];      // 发言顺序
    speakingTimeLimit: number;    // 单人发言时间限制（秒）
  };
}
```

#### sheriff_candidacy
警长竞选报名

```typescript
// Client → Server
interface SheriffCandidacyRequest {
  type: 'sheriff_candidacy';
  payload: {
    playerId: string;
    action: 'declare' | 'withdraw'; // 声明参选或退选
  };
}

// Server → Client (广播)
interface SheriffCandidateUpdate {
  type: 'sheriff_candidate_update';
  payload: {
    playerId: string;
    playerName: string;
    action: 'declared' | 'withdrew';
    currentCandidates: CandidateInfo[];
  };
}
```

#### sheriff_speech
警长竞选发言

```typescript
// Client → Server
interface SheriffSpeechRequest {
  type: 'sheriff_speech';
  payload: {
    playerId: string;
    content: string;              // 发言内容（最大500字符）
  };
}

// Server → Client (广播)
interface SheriffSpeechEvent {
  type: 'sheriff_speech';
  payload: {
    playerId: string;
    playerName: string;
    content: string;
    timestamp: Date;
  };
}
```

#### sheriff_vote
警长投票

```typescript
// Client → Server
interface SheriffVoteRequest {
  type: 'sheriff_vote';
  payload: {
    playerId: string;
    candidateId: string;         // 候选人ID
  };
}

// Server → Client (投票进度）
interface SheriffVoteProgress {
  type: 'sheriff_vote_progress';
  payload: {
    totalVotes: number;
    candidateVotes: Array<{
      candidateId: string;
      candidateName: string;
      voteCount: number;
    }>;
    remainingVoters: string[];
  };
}

// Server → Client (结果）
interface SheriffElectionResult {
  type: 'sheriff_election_result';
  payload: {
    winner?: {
      playerId: string;
      playerName: string;
      voteCount: number;
    };
    tieCandidates?: Array<{
      playerId: string;
      playerName: string;
      voteCount: number;
    }>;
    totalVotes: number;
  };
}
```

#### day_discussion
白天讨论

```typescript
// Client → Server
interface DiscussionSpeakRequest {
  type: 'discussion_speak';
  payload: {
    playerId: string;
    content: string;              // 发言内容（最大500字符）
  };
}

// Server → Client (广播)
interface DiscussionSpeakEvent {
  type: 'discussion_speak';
  payload: {
    playerId: string;
    playerName: string;
    content: string;
    timestamp: Date;
    speakingOrder: string[];     // 当前发言顺序
    currentSpeaker?: string;     // 当前发言人
  };
}
```

### Voting Events

#### voting_start
投票开始

```typescript
interface VotingStartEvent {
  type: 'voting_start';
  payload: {
    votingId: string;
    votingType: 'sheriff_election' | 'player_elimination';
    candidates: VotingCandidate[];
    votingTimeLimit: number;     // 投票时间限制（秒）
    alivePlayers: string[];      // 可投票玩家
  };
}
```

#### player_vote
玩家投票

```typescript
// Client → Server
interface PlayerVoteRequest {
  type: 'player_vote';
  payload: {
    playerId: string;
    targetId: string;            // 投票目标
  };
}

// Server → Client (投票进度）
interface VotingProgress {
  type: 'voting_progress';
  payload: {
    votingId: string;
    totalVotes: number;
    candidateVotes: Array<{
      targetId: string;
      targetName: string;
      voteCount: number;
      voteWeight: number;        // 考虑警长1.5票权重
    }>;
    remainingVoters: string[];
  };
}
```

#### voting_result
投票结果

```typescript
interface VotingResultEvent {
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
      role?: RoleType;           // 死亡后揭露角色
    };
    sheriffInfluence?: boolean;  // 是否使用了警长影响力
    totalVotes: number;
  };
}
```

### Death Events

#### player_death
玩家死亡

```typescript
interface PlayerDeathEvent {
  type: 'player_death';
  payload: {
    playerId: string;
    playerName: string;
    role?: RoleType;             // 死亡后揭露（游戏结束后才揭露）
    deathCause: DeathCause;
    dayCount: number;
    timestamp: Date;
  };
}
```

#### hunter_shoot
猎人开枪

```typescript
// Client → Server (仅猎人死亡时)
interface HunterShootRequest {
  type: 'hunter_shoot';
  payload: {
    playerId: string;
    targetId: string;            // 开枪目标
  };
}

// Server → Client (广播)
interface HunterShootEvent {
  type: 'hunter_shoot';
  payload: {
    hunterId: string;
    hunterName: string;
    targetId: string;
    targetName: string;
    timestamp: Date;
  };
}
```

### Game End Events

#### game_over
游戏结束

```typescript
interface GameOverEvent {
  type: 'game_over';
  payload: {
    winner: Team;                // 获胜阵营
    gameDuration: number;         // 游戏时长（秒）
    totalDays: number;            // 总天数
    finalRoles: Array<{
      playerId: string;
      playerName: string;
      role: RoleType;            // 最终角色揭露
      survived: boolean;
    }>;
    gameId: string;              // 游戏会话ID
    canReplay: boolean;          // 是否可以回放
  };
}
```

## Replay System Events

#### replay_access
访问游戏回放

```typescript
// Client → Server
interface ReplayAccessRequest {
  type: 'replay_access';
  payload: {
    gameId: string;              // 游戏会话ID
  };
}

// Server → Client
interface ReplayAccessResponse {
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
```

#### replay_day_select
选择回放天数

```typescript
// Client → Server
interface ReplayDaySelectRequest {
  type: 'replay_day_select';
  payload: {
    gameId: string;
    dayNumber: number;           // 选择的天数
  };
}

// Server → Client
interface ReplayDaySnapshot {
  type: 'replay_day_snapshot';
  payload: {
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
  };
}
```

#### replay_playback
回放控制

```typescript
// Client → Server
interface ReplayPlaybackRequest {
  type: 'replay_playback';
  payload: {
    gameId: string;
    action: 'play' | 'pause' | 'stop' | 'seek';
    timestamp?: number;           // 快进到指定时间戳
    speed?: number;               // 播放速度（0.5x, 1x, 2x）
  };
}

// Server → Client (事件回放）
interface ReplayEventPlayback {
  type: 'replay_event_playback';
  payload: {
    event: GameEvent;
    playbackTime: number;        // 回放时间戳
    speed: number;               // 当前播放速度
    isPlaying: boolean;
  };
}
```

## Error Handling

### Error Events

#### error
通用错误事件

```typescript
interface ErrorEvent {
  type: 'error';
  payload: {
    code: ErrorCode;
    message: string;
    details?: any;
    timestamp: Date;
  };
}

enum ErrorCode {
  // 连接错误
  CONNECTION_FAILED = 'connection_failed',
  ROOM_NOT_FOUND = 'room_not_found',
  ROOM_FULL = 'room_full',
  INVALID_PLAYER_NAME = 'invalid_player_name',

  // 游戏状态错误
  GAME_NOT_STARTED = 'game_not_started',
  INVALID_PHASE = 'invalid_phase',
  ACTION_NOT_ALLOWED = 'action_not_allowed',

  // 投票错误
  INVALID_VOTE_TARGET = 'invalid_vote_target',
  ALREADY_VOTED = 'already_voted',

  // 权限错误
  INSUFFICIENT_PERMISSIONS = 'insufficient_permissions',
  ROLE_REQUIRED = 'role_required',

  // 系统错误
  INTERNAL_ERROR = 'internal_error',
  TIMEOUT = 'timeout'
}
```

#### validation_error
验证错误

```typescript
interface ValidationError {
  type: 'validation_error';
  payload: {
    field: string;               // 错误字段
    value: any;                   // 错误值
    message: string;              // 错误信息
    code: string;
  };
}
```

## Common Types

```typescript
interface PlayerInfo {
  playerId: string;
  playerName: string;
  type: 'human' | 'ai';
  position?: number;             // 座位号（游戏开始后分配）
  joinedAt: Date;
}

interface GamePlayerInfo extends PlayerInfo {
  role: RoleType;                // 分配的角色
  status: 'alive' | 'dead';
  votingWeight: number;          // 投票权重
}

interface CandidateInfo {
  playerId: string;
  playerName: string;
  role?: RoleType;                // 死亡后揭露
  voteCount: number;
}

interface VotingCandidate {
  playerId: string;
  playerName: string;
  voteCount: number;
  voteWeight: number;            // 投票权重
}

interface ReplayPlayerState {
  playerId: string;
  playerName: string;
  role: RoleType;                // 回放时揭露所有角色
  status: 'alive' | 'dead';
  position: number;
  abilities?: {
    witchAntidote: boolean;
    witchPoison: boolean;
    hunterCanShoot: boolean;
  };
}

interface ReplayEventInfo {
  eventId: string;
  type: EventType;
  timestamp: Date;
  description: string;
  participants: string[];        // 参与玩家ID
}

enum GamePhase {
  NIGHT = 'night',
  SHERIFF_ELECTION = 'sheriff_election',
  DAY_DISCUSSION = 'day_discussion',
  VOTING = 'voting',
  GAME_OVER = 'game_over'
}

enum RoleType {
  WEREWOLF = 'werewolf',
  VILLAGER = 'villager',
  SEER = 'seer',
  WITCH = 'witch',
  HUNTER = 'hunter'
}

enum Team {
  WEREWOLF = 'werewolf',
  GOOD = 'good'
}

enum DeathCause {
  WEREWOLF_KILL = 'werewolf_kill',
  VOTE_OUT = 'vote_out',
  WITCH_POISON = 'witch_poison',
  HUNTER_SHOOT = 'hunter_shoot'
}

enum EventType {
  // 系统事件
  GAME_START = 'game_start',
  GAME_END = 'game_end',
  PHASE_CHANGE = 'phase_change',

  // 夜晚事件
  WEREWOLF_KILL = 'werewolf_kill',
  SEER_CHECK = 'seer_check',
  WITCH_SAVE = 'witch_save',
  WITCH_POISON = 'witch_poison',

  // 白天事件
  SHERIFF_ELECTION_START = 'sheriff_election_start',
  SHERIFF_CANDIDACY = 'sheriff_candidacy',
  SHERIFF_SPEECH = 'sheriff_speech',
  SHERIFF_ELECTED = 'sheriff_elected',

  // 讨论事件
  PLAYER_SPEAK = 'player_speak',

  // 投票事件
  VOTE_START = 'vote_start',
  PLAYER_VOTE = 'player_vote',
  VOTE_RESULT = 'vote_result',

  // 死亡事件
  PLAYER_DEATH = 'player_death',

  // 猎人事件
  HUNTER_SHOOT = 'hunter_shoot'
}
```

## Connection Events

#### connection_established
连接建立

```typescript
interface ConnectionEstablishedEvent {
  type: 'connection_established';
  payload: {
    connectionId: string;
    timestamp: Date;
    serverTime: Date;
  };
}
```

#### heartbeat
心跳事件

```typescript
// Client → Server
interface HeartbeatRequest {
  type: 'heartbeat';
  payload: {
    timestamp: Date;
  };
}

// Server → Client
interface HeartbeatResponse {
  type: 'heartbeat_response';
  payload: {
    timestamp: Date;
    serverTime: Date;
  };
}
```

#### reconnect
重连事件

```typescript
// Client → Server
interface ReconnectRequest {
  type: 'reconnect';
  payload: {
    playerId: string;
    roomId: string;
    lastEventId?: string;        // 最后收到的事件ID
  };
}

// Server → Client
interface ReconnectResponse {
  type: 'reconnect_response';
  payload: {
    success: boolean;
    missedEvents?: GameEvent[];   // 错过的事件
    currentGameState?: GameState;  // 当前游戏状态
  };
}
```

## Rate Limiting and Security

### Message Limits

- **发言消息**: 最大500字符
- **连接限制**: 每IP最多10个并发连接
- **房间限制**: 每个房间最多9个玩家
- **重连限制**: 断线后5分钟内可重连

### Authentication

```typescript
interface AuthToken {
  playerId: string;
  roomId: string;
  expiresAt: Date;
  signature: string;
}
```

### Permission System

- **房间创建**: 无需认证，自动分配房主权限
- **游戏开始**: 仅房主权限
- **警长竞选**: 仅存活玩家
- **投票**: 仅存活玩家
- **角色技能**: 仅对应角色在正确阶段
- **查看回放**: 游戏参与者