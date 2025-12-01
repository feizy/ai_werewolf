# Data Model: Werewolf Game Backend

**Created**: 2025-12-01
**Feature**: 002-werewolf-backend
**Purpose**: Define core entities and relationships for werewolf game system

## Core Entities

### GameRoom
游戏房间实体，管理游戏会话和玩家连接

```typescript
interface GameRoom {
  id: string;                    // 唯一房间ID
  name?: string;                  // 可选房间名称
  creatorId: string;              // 创建者玩家ID
  maxPlayers: number;             // 最大玩家数（固定为9）
  currentPlayers: number;          // 当前玩家数
  status: RoomStatus;             // 房间状态
  gameConfig: GameConfiguration;   // 游戏配置
  createdAt: Date;                // 创建时间
  startedAt?: Date;               // 游戏开始时间
  endedAt?: Date;                 // 游戏结束时间
}

enum RoomStatus {
  WAITING = 'waiting',           // 等待玩家加入
  PLAYING = 'playing',           // 游戏进行中
  FINISHED = 'finished'          // 游戏已结束
}
```

### Player
玩家实体，包含身份信息和游戏状态

```typescript
interface Player {
  id: string;                    // 玩家唯一标识
  name: string;                  // 玩家名称（前端显示用）
  roomId: string;                 // 所属房间ID
  type: PlayerType;               // 玩家类型（全为AI）
  role?: Role;                   // 分配的角色（游戏开始后分配）
  status: PlayerStatus;           // 玩家状态
  position: number;               // 座位位置（1-9）
  connectionState: ConnectionState; // AI连接状态
  joinedAt: Date;                // 加入房间时间
  lastActiveAt: Date;             // 最后活跃时间
  // AI特有属性
  aiConfig: AIPlayerConfig;       // AI配置
  agentScopeId: string;          // AgentScope代理ID
  // 角色特有属性
  roleAbilities?: RoleAbilities;  // 角色能力状态
  // 投票相关
  votingWeight: number;           // 投票权重（普通1.0，警长1.5）
}

interface AIPlayerConfig {
  agentType: string;             // AI代理类型
  personality: PersonalityType;    // AI性格类型
  skillLevel: SkillLevel;          // 技能等级
  responseTime: ResponseTime;     // 响应时间配置
  strategy: StrategyType;         // 策略类型
  language: 'zh' | 'en';         // 语言偏好
  creativityLevel: number;        // 创造力等级（0-1）
  aggressiveness: number;          // 攻击性等级（0-1）
  cooperation: number;            // 合作性等级（0-1）
}

enum PersonalityType {
  AGGRESSIVE = 'aggressive',     // 攻击型
  ANALYTICAL = 'analytical',     // 分析型
  DECEPTIVE = 'deceptive',      // 欺骗型
  CAUTIOUS = 'cautious',       // 谨慎型
  LEADER = 'leader',            // 领导型
  FOLLOWER = 'follower'         // 跟随型
}

enum SkillLevel {
  BEGINNER = 'beginner',         // 初学者
  INTERMEDIATE = 'intermediate', // 中级
  ADVANCED = 'advanced',        // 高级
  EXPERT = 'expert'             // 专家
}

enum ResponseTime {
  IMMEDIATE = 'immediate',       // 立即响应（0.5-2秒）
  FAST = 'fast',                // 快速响应（2-5秒）
  NORMAL = 'normal',            // 正常响应（5-10秒）
  SLOW = 'slow'                 // 慢速响应（10-20秒）
}

enum StrategyType {
  LOGICAL = 'logical',          // 逻辑型策略
  EMOTIONAL = 'emotional',      // 情感型策略
  BALANCED = 'balanced',        // 平衡型策略
  RANDOM = 'random'            // 随机型策略
}

enum PlayerType {
  AI = 'ai'                     // AI玩家（所有玩家都是AI）
}

enum PlayerStatus {
  ALIVE = 'alive',               // 存活
  DEAD = 'dead',                 // 死亡
  PROCESSING = 'processing'      // AI正在处理行动
}

enum ConnectionState {
  ACTIVE = 'active',              // AI活跃状态
  INACTIVE = 'inactive',          // AI非活跃状态
  PROCESSING = 'processing'        // AI正在处理决策
}
```

### Role
角色实体，定义游戏中的不同角色

```typescript
interface Role {
  type: RoleType;                 // 角色类型
  team: Team;                    // 所属阵营
  abilities: RoleAbility[];       // 角色能力
  visibility: VisibilityRules;    // 可见性规则
}

enum RoleType {
  WEREWOLF = 'werewolf',         // 狼人
  VILLAGER = 'villager',         // 平民
  SEER = 'seer',                 // 预言家
  WITCH = 'witch',               // 女巫
  HUNTER = 'hunter'              // 猎人
}

enum Team {
  WEREWOLF = 'werewolf',         // 狼人阵营
  GOOD = 'good'                  // 好人阵营
}
```

### GameSession
游戏会话实体，记录完整的游戏过程

```typescript
interface GameSession {
  id: string;                    // 游戏会话ID
  roomId: string;                // 房间ID
  players: Player[];              // 所有玩家
  gameState: GameState;           // 当前游戏状态
  dayCount: number;               // 游戏天数
  currentPhase: GamePhase;        // 当前阶段
  phaseStartTime: Date;           // 阶段开始时间
  events: GameEvent[];            // 游戏事件历史
  dailySnapshots: DailySnapshot[]; // 每日快照
  winner?: Team;                  // 获胜阵营
  endedAt?: Date;                 // 结束时间
}
```

### GameState
游戏状态实体，跟踪当前游戏进展

```typescript
interface GameState {
  phase: GamePhase;               // 当前游戏阶段
  dayCount: number;               // 当前天数
  players: PlayerState[];         // 玩家状态
  sheriff?: SheriffState;          // 警长状态
  // 夜晚阶段特有状态
  nightActions?: NightActions;      // 夜晚行动
  // 白天阶段特有状态
  dayPhase?: DayPhaseState;        // 白天阶段状态
  // 投票阶段特有状态
  voting?: VotingState;           // 投票状态
}

enum GamePhase {
  NIGHT = 'night',               // 夜晚阶段
  SHERIFF_ELECTION = 'sheriff_election', // 警长竞选
  DAY_DISCUSSION = 'day_discussion',     // 白天讨论
  VOTING = 'voting',              // 投票阶段
  GAME_OVER = 'game_over'       // 游戏结束
}
```

### RoleAbilities
角色能力状态，特指有特殊技能的角色

```typescript
interface RoleAbilities {
  // 预言家能力
  seerInfo?: {
    checksRemaining: number;        // 剩余查验次数（每夜1次）
    lastCheckedPlayerId?: string;  // 上次查验的玩家ID
    checkResults: CheckResult[];   // 查验结果历史
  };

  // 女巫能力
  witchInfo?: {
    hasAntidote: boolean;         // 是否有解药
    hasPoison: boolean;            // 是否有毒药
    antidoteUsed: boolean;        // 解药是否已使用
    poisonUsed: boolean;          // 毒药是否已使用
    poisonTargetId?: string;      // 毒药目标ID
    lastNightVictimId?: string;   // 昨晚死亡者ID
  };

  // 猎人能力
  hunterInfo?: {
    canShoot: boolean;             // 是否可以开枪
    hasShot: boolean;             // 是否已开枪
    shotTargetId?: string;         // 开枪目标ID
    deathCause?: DeathCause;       // 死亡原因（判断是否能开枪）
  };
}

interface CheckResult {
  targetPlayerId: string;         // 目标玩家ID
  targetName: string;             // 目标玩家姓名
  result: 'werewolf' | 'good';  // 查验结果
  nightNumber: number;            // 查验夜晚
  timestamp: Date;                // 查验时间
}

enum DeathCause {
  WEREWOLF_KILL = 'werewolf_kill', // 狼人击杀
  VOTE_OUT = 'vote_out',          // 投票出局
  WITCH_POISON = 'witch_poison',  // 女巫毒杀
  HUNTER_SHOOT = 'hunter_shoot'   // 猎人开枪
}
```

### GameEvent
游戏事件实体，记录所有游戏行为

```typescript
interface GameEvent {
  id: string;                    // 事件唯一ID
  sessionId: string;              // 游戏会话ID
  type: EventType;                // 事件类型
  phase: GamePhase;               // 发生阶段
  dayCount: number;               // 发生天数
  timestamp: Date;                // 事件时间
  // 事件参与者
  actorId?: string;               // 行动者ID
  actorName?: string;             // 行动者姓名
  targetId?: string;             // 目标ID
  targetName?: string;            // 目标姓名
  // 事件内容
  content: string;                // 事件描述（前端显示用）
  details?: EventDetails;         // 事件详细信息
  // 可见性控制
  visibility: EventVisibility;     // 谁能看到此事件
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

interface EventVisibility {
  public: boolean;                // 是否公开
  visibleToRoles?: RoleType[];    // 可见的角色类型
  visibleToPlayers?: string[];    // 可见的玩家ID
  requiresRoleReveal?: boolean;   // 是否需要角色揭露
}
```

### VotingState
投票状态实体

```typescript
interface VotingState {
  id: string;                    // 投票会话ID
  type: VotingType;               // 投票类型
  candidates: VotingCandidate[];   // 候选人列表
  votes: Vote[];                  // 投票记录
  status: VotingStatus;            // 投票状态
  startTime: Date;                // 开始时间
  endTime?: Date;                 // 结束时间
  result?: VotingResult;           // 投票结果
}

enum VotingType {
  SHERIFF_ELECTION = 'sheriff_election', // 警长竞选
  PLAYER_ELIMINATION = 'player_elimination' // 放逐投票
}

interface VotingCandidate {
  playerId: string;               // 玩家ID
  playerName: string;             // 玩家姓名
  role?: RoleType;                // 角色（已死亡后揭露）
  voteCount: number;              // 得票数
  voteWeight: number;             // 投票权重
}

interface Vote {
  voterId: string;                // 投票者ID
  voterName: string;              // 投票者姓名
  candidateId: string;            // 候选人ID
  weight: number;                 // 投票权重
  timestamp: Date;                // 投票时间
}

interface VotingResult {
  winner?: VotingCandidate;       // 获胜者
  tiedCandidates?: VotingCandidate[]; // 平票候选者
  totalVotes: number;             // 总票数
  sheriffInfluence?: boolean;     // 是否使用了警长影响力
}
```

### DailySnapshot
每日快照实体，用于游戏回放

```typescript
interface DailySnapshot {
  id: string;                    // 快照ID
  sessionId: string;              // 游戏会话ID
  dayNumber: number;              // 天数
  timestamp: Date;                // 快照时间（该天开始时）
  playerStates: PlayerState[];     // 该天开始时的玩家状态
  gameState: Partial<GameState>;  // 该天开始时的游戏状态
  events: GameEvent[];            // 当天所有事件
}

interface PlayerState {
  playerId: string;               // 玩家ID
  playerName: string;             // 玩家姓名
  role: RoleType;                 // 角色（回放时揭露）
  status: PlayerStatus;           // 状态
  position: number;               // 座位
  abilities?: RoleAbilities;       // 能力状态
  votingWeight: number;           // 投票权重
}
```

## Validation Rules

### Game Room Validation
- 房间ID必须唯一
- 最大玩家数固定为9
- 房间创建者自动成为第一个玩家
- 游戏开始后不允许新玩家加入

### Player Validation
- 玩家名称不能为空，长度1-20字符
- 同一房间内玩家名称不能重复
- 座位位置必须在1-9范围内且不重复
- AI玩家必须有有效的AgentScope配置

### Role Assignment Validation
- 9人局必须严格分配：3狼人、3平民、1预言家、1女巫、1猎人
- 狼人玩家必须能相互识别身份
- 好人玩家只能看到自己的具体角色
- 角色分配必须是随机的但符合配置规则

### Game Phase Validation
- 夜晚阶段：只有狼人、预言家、女巫可以行动
- 白天讨论阶段：所有存活玩家可以发言
- 投票阶段：只有存活玩家可以投票
- 警长只在第一天选举

### Role Ability Validation
- 预言家每夜只能查验一名玩家
- 女巫解药和毒药整个游戏只能使用一次
- 女巫不能在同晚同时使用解药和毒药
- 猎人只能在被投票出局或被狼人杀死时开枪
- 被女巫毒死的猎人不能开枪

### Voting Validation
- 警长投票权重为1.5，普通玩家为1.0
- 投票平票时由警长决定结果
- 警长竞选只有第一天进行
- 死亡玩家不能参与投票

## State Transitions

### Game Phase Flow
1. **NIGHT** → **SHERIFF_ELECTION** (仅第一天) → **DAY_DISCUSSION** → **VOTING** → **NIGHT**
2. 游戏在任意时刻检测胜利条件，如满足直接进入 **GAME_OVER**

### Player Status Flow
1. **ALIVE** → **DEAD** (被杀死、被投票出局、被毒死)
2. **CONNECTED** → **DISCONNECTED** → **RECONNECTING** → **CONNECTED**

### Role Ability Usage Flow
1. 预言家：每夜可用一次查验能力
2. 女巫：夜晚可使用解药救活被杀玩家，或使用毒药毒杀玩家
3. 猎人：死亡时（非被毒死）可立即开枪带走一人

## Relationships

- **GameRoom** 1:n **Player** (一个房间多个玩家)
- **GameRoom** 1:1 **GameSession** (一个房间一个游戏会话)
- **Player** 1:1 **Role** (每个玩家一个角色)
- **GameSession** 1:n **GameEvent** (一个会话多个事件)
- **GameSession** 1:n **DailySnapshot** (一个会话多个每日快照)
- **VotingState** 1:n **Vote** (一个投票会话多张选票)

## Performance Considerations

### Indexing Strategy
- **GameRoom.id**: 主键索引，房间查询
- **Player.roomId + playerId**: 复合索引，房间内玩家查询
- **GameSession.roomId**: 外键索引，关联房间
- **GameEvent.sessionId + timestamp**: 复合索引，事件时间序列查询
- **DailySnapshot.sessionId + dayNumber**: 复合索引，快照查询

### Caching Strategy
- 活跃游戏状态缓存在内存中
- 房间列表使用Redis缓存支持快速查询
- 玩家连接状态缓存在内存中支持实时更新
- 每日快照定期持久化到数据库

### Data Retention
- 完成的游戏数据保留至少30天用于回放
- 事件日志用于分析和调试，定期归档
- 玩家断线重连数据保留24小时