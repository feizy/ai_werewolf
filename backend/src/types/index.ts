// 基础类型定义
export enum PlayerType {
  AI = 'ai'
}

export enum PlayerStatus {
  ALIVE = 'alive',
  DEAD = 'dead',
  PROCESSING = 'processing'
}

export enum ConnectionState {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  PROCESSING = 'processing'
}

export enum RoleType {
  WEREWOLF = 'werewolf',
  VILLAGER = 'villager',
  SEER = 'seer',
  WITCH = 'witch',
  HUNTER = 'hunter'
}

export enum Team {
  WEREWOLF = 'werewolf',
  GOOD = 'good'
}

export enum GamePhase {
  NIGHT = 'night',
  SHERIFF_ELECTION = 'sheriff_election',
  DAY_DISCUSSION = 'day_discussion',
  VOTING = 'voting',
  GAME_OVER = 'game_over'
}

export enum RoomStatus {
  WAITING = 'waiting',
  PLAYING = 'playing',
  FINISHED = 'finished'
}

export enum PersonalityType {
  AGGRESSIVE = 'aggressive',
  ANALYTICAL = 'analytical',
  DECEPTIVE = 'deceptive',
  CAUTIOUS = 'cautious',
  LEADER = 'leader',
  FOLLOWER = 'follower'
}

export enum SkillLevel {
  BEGINNER = 'beginner',
  INTERMEDIATE = 'intermediate',
  ADVANCED = 'advanced',
  EXPERT = 'expert'
}

export enum ResponseTime {
  IMMEDIATE = 'immediate',
  FAST = 'fast',
  NORMAL = 'normal',
  SLOW = 'slow'
}

export enum StrategyType {
  LOGICAL = 'logical',
  EMOTIONAL = 'emotional',
  BALANCED = 'balanced',
  RANDOM = 'random'
}

export enum DeathCause {
  WEREWOLF_KILL = 'werewolf_kill',
  VOTE_OUT = 'vote_out',
  WITCH_POISON = 'witch_poison',
  HUNTER_SHOOT = 'hunter_shoot'
}

export enum EventType {
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

export enum VotingType {
  SHERIFF_ELECTION = 'sheriff_election',
  PLAYER_ELIMINATION = 'player_elimination'
}