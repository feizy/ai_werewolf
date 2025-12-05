# Data Model: Werewolf Game Frontend

**Date**: 2025-12-01
**Purpose**: Define data structures and interfaces for real-time multiplayer Werewolf game frontend
**Based on**: Research findings and feature specification requirements

## Core Game State Interfaces

### GameState
```typescript
interface GameState {
  readonly id: string;
  readonly day: number;
  readonly phase: GamePhase;
  readonly players: ReadonlyArray<Player>;
  readonly events: ReadonlyArray<GameEvent>;
  readonly sheriffElection: SheriffElection | null;
  readonly sheriffId: string | null;
  readonly createdAt: Date;
  readonly updatedAt: Date;
  readonly isReplayMode: boolean;
  readonly currentReplayDay?: number;
}
```

### GamePhase (Discriminated Union)
```typescript
type GamePhase =
  | { type: 'night'; round: number; timeRemaining: number }
  | { type: 'sheriff_election'; candidates: string[]; speechesCompleted: number }
  | { type: 'discussion'; timeRemaining: number }
  | { type: 'voting'; votes: VoteRecord[]; timeRemaining: number }
  | { type: 'game_over'; winner: 'werewolves' | 'villagers'; duration: number };
```

### Player Entity
```typescript
interface Player {
  readonly id: string;
  readonly name: string;
  readonly role: PlayerRole;
  readonly position: number; // 1-9 for circular seating
  readonly isAlive: boolean;
  readonly isSheriff: boolean;
  readonly hasVoted: boolean;
  readonly lastAction: GameAction | null;
  readonly connectedAt: Date;
  readonly updatedAt: Date;
}

type PlayerRole =
  | { type: 'werewolf'; teammates: ReadonlyArray<string> }
  | { type: 'villager' }
  | { type: 'seer'; investigationsLeft: number; lastInvestigated: string | null }
  | { type: 'witch'; hasAntidote: boolean; hasPoison: boolean }
  | { type: 'hunter'; hasGun: boolean };
```

### Role Status Tracking
```typescript
interface RoleStatus {
  readonly witch: {
    readonly hasAntidote: boolean;
    readonly hasPoison: boolean;
    readonly antitodeUsed: boolean;
    readonly poisonUsed: boolean;
    readonly lastUsed: Date | null;
  };
  readonly hunter: {
    readonly hasGun: boolean;
    readonly gunUsed: boolean;
    readonly lastUsed: Date | null;
    readonly target?: string;
  };
  readonly seer: {
    readonly investigationsLeft: number;
    readonly lastInvestigated: string | null;
    readonly investigationResults: Record<string, 'werewolf' | 'good'>;
  };
}
```

## Event System

### GameEvent (Base Interface)
```typescript
interface GameEvent {
  readonly id: string;
  readonly timestamp: Date;
  readonly day: number;
  readonly phase: GamePhase;
  readonly category: EventCategory;
  readonly description: string;
  readonly participants: ReadonlyArray<string>; // Player IDs
  readonly sequenceNumber: number;
  readonly metadata: EventMetadata;
}
```

### Event Categories
```typescript
type EventCategory =
  | 'MODERATOR'
  | 'SPEECH'
  | 'ACTION'
  | 'VOTE'
  | 'DEATH'
  | 'ELECTION'
  | 'SYSTEM';

type EventMetadata =
  | SpeechMetadata
  | ActionMetadata
  | VoteMetadata
  | DeathMetadata
  | ElectionMetadata
  | SystemMetadata;
```

### Specific Event Types
```typescript
interface SpeechMetadata {
  readonly type: 'speech';
  readonly speakerId: string;
  readonly content: string;
  readonly characterCount: number;
  readonly isSheriffSpeaking: boolean;
}

interface ActionMetadata {
  readonly type: 'action';
  readonly actionType: 'save' | 'poison' | 'shoot' | 'investigate';
  readonly actorId: string;
  readonly targetId?: string;
  readonly result: 'success' | 'failed' | 'blocked';
}

interface VoteMetadata {
  readonly type: 'vote';
  readonly voterId: string;
  readonly targetId: string;
  readonly weight: number; // Sheriff has 1.5 weight
  readonly round: number;
}

interface DeathMetadata {
  readonly type: 'death';
  readonly playerId: string;
  readonly role: PlayerRole;
  readonly causeOfDeath: 'werewolf_attack' | 'witch_poison' | 'voted_out' | 'hunter_revenge';
  readonly day: number;
}

interface ElectionMetadata {
  readonly type: 'election';
  readonly electionType: 'candidacy' | 'speech' | 'vote' | 'result';
  readonly candidateId?: string;
  readonly voterId?: string;
  readonly speechContent?: string;
  readonly winnerId?: string;
}
```

## Sheriff Election System

### SheriffElection
```typescript
interface SheriffElection {
  readonly id: string;
  readonly gameId: string;
  readonly day: number;
  readonly phase: 'nomination' | 'speeches' | 'voting' | 'completed';
  readonly candidates: ReadonlyArray<ElectionCandidate>;
  readonly votes: ReadonlyArray<ElectionVote>;
  readonly winnerId: string | null;
  readonly startedAt: Date;
  readonly completedAt: Date | null;
}

interface ElectionCandidate {
  readonly playerId: string;
  readonly playerName: string;
  readonly speech: string;
  readonly speechOrder: number;
  readonly hasSpoken: boolean;
  readonly withdrew: boolean;
}

interface ElectionVote {
  readonly voterId: string;
  readonly candidateId: string;
  readonly weight: number; // Regular players: 1.0, Sheriff: 1.5
  readonly timestamp: Date;
}
```

## Replay System

### DailySnapshot
```typescript
interface DailySnapshot {
  readonly id: string;
  readonly gameId: string;
  readonly day: number;
  readonly timestamp: Date;
  readonly playerStates: ReadonlyArray<PlayerSnapshot>;
  readonly sheriffId: string | null;
  readonly phaseAtSnapshot: GamePhase;
  readonly totalEvents: number;
  readonly eventIndex: number; // Index in full event array
}

interface PlayerSnapshot {
  readonly playerId: string;
  readonly player: Player;
  readonly roleStatus: RoleStatus;
  readonly position: number;
  readonly isAlive: boolean;
  readonly isSheriff: boolean;
}
```

### GameReplay
```typescript
interface GameReplay {
  readonly gameId: string;
  readonly snapshots: ReadonlyArray<DailySnapshot>;
  readonly events: ReadonlyArray<GameEvent>;
  readonly currentDay: number;
  readonly currentTime: Date;
  readonly isPlaying: boolean;
  readonly playbackSpeed: number; // 0.5x, 1x, 2x, 4x
  readonly currentEventIndex: number;
  readonly filters: ReplayFilters;
}

interface ReplayFilters {
  readonly eventCategories: ReadonlyArray<EventCategory>;
  readonly playerIds: ReadonlyArray<string>;
  readonly dayRange: { start: number; end: number } | null;
  readonly searchText: string;
}
```

## WebSocket Message Types

### WebSocket Messages
```typescript
interface WebSocketMessage {
  readonly type: MessageType;
  readonly gameId: string;
  readonly timestamp: Date;
  readonly payload: unknown;
}

type MessageType =
  | 'GAME_STATE_UPDATE'
  | 'PLAYER_EVENT'
  | 'PHASE_CHANGE'
  | 'SHERIFF_ELECTION_UPDATE'
  | 'REPLAY_SNAPSHOT'
  | 'CONNECTION_STATUS'
  | 'ERROR';
```

### Message Payloads
```typescript
interface GameStateUpdatePayload {
  readonly gameState: GameState;
  readonly changedPlayerIds?: ReadonlyArray<string>;
  readonly newEventIds?: ReadonlyArray<string>;
}

interface PlayerEventPayload {
  readonly event: GameEvent;
  readonly affectedPlayerIds: ReadonlyArray<string>;
}

interface PhaseChangePayload {
  readonly oldPhase: GamePhase;
  readonly newPhase: GamePhase;
  readonly transitionReason: string;
}

interface SheriffElectionUpdatePayload {
  readonly election: SheriffElection;
  readonly changeType: 'candidate_added' | 'speech_given' | 'vote_cast' | 'completed';
}
```

## UI State Interfaces

### GameUIState
```typescript
interface GameUIState {
  readonly selectedPlayerId: string | null;
  readonly hoveredPlayerId: string | null;
  readonly eventFilter: EventFilter;
  readonly sidebarOpen: boolean;
  readonly replayControlsOpen: boolean;
  readonly viewMode: 'live' | 'replay';
  readonly toastNotifications: ReadonlyArray<ToastNotification>;
}

interface EventFilter {
  readonly categories: ReadonlyArray<EventCategory>;
  readonly playerIds: ReadonlyArray<string>;
  readonly dayRange: { start: number; end: number } | null;
  readonly searchText: string;
  readonly timeRange: { start: Date; end: Date } | null;
}

interface ToastNotification {
  readonly id: string;
  readonly type: 'info' | 'success' | 'warning' | 'error';
  readonly title: string;
  readonly message: string;
  readonly duration: number;
  readonly timestamp: Date;
}
```

## Component Props Interfaces

### GameTable Props
```typescript
interface GameTableProps {
  readonly gameState: GameState;
  readonly currentPlayerId?: string;
  readonly onPlayerClick?: (playerId: string) => void;
  readonly onPlayerHover?: (playerId: string | null) => void;
  readonly selectedPlayerId?: string | null;
  readonly showRoles?: boolean; // For debugging/spectator mode
}

interface PlayerCircleProps {
  readonly players: ReadonlyArray<Player>;
  readonly gameState: GameState;
  readonly radius?: number;
  readonly centerOffset?: { x: number; y: number };
  readonly selectedPlayerId?: string | null;
  readonly hoveredPlayerId?: string | null;
  readonly onPlayerClick?: (playerId: string) => void;
  readonly onPlayerHover?: (playerId: string | null) => void;
}
```

### EventLog Props
```typescript
interface EventLogProps {
  readonly events: ReadonlyArray<GameEvent>;
  readonly filters: EventFilter;
  readonly onFilterChange: (filters: EventFilter) => void;
  readonly onEventClick?: (eventId: string) => void;
  readonly maxHeight?: number;
  readonly autoScroll?: boolean;
  readonly virtualized?: boolean;
}
```

### ReplayControls Props
```typescript
interface ReplayControlsProps {
  readonly replay: GameReplay;
  readonly onPlayPause: () => void;
  readonly onSpeedChange: (speed: number) => void;
  readonly onSeek: (eventIndex: number) => void;
  readonly onDaySelect: (day: number) => void;
  readonly onFilterChange: (filters: ReplayFilters) => void;
}
```

## Validation Rules

### Game State Validation
```typescript
interface GameStateValidator {
  validatePlayerCount(players: Player[]): boolean;
  validateRoleAssignment(players: Player[]): boolean;
  validatePhaseTransition(oldPhase: GamePhase, newPhase: GamePhase): boolean;
  validateSheriffElection(election: SheriffElection): boolean;
  validateReplayIntegrity(replay: GameReplay): boolean;
}

const validatePlayerCount = (players: Player[]): boolean => {
  return players.length === 9; // 3 werewolves, 3 villagers, 1 seer, 1 witch, 1 hunter
};

const validateRoleAssignment = (players: Player[]): boolean => {
  const roles = players.map(p => p.role.type);
  const counts = roles.reduce((acc, role) => {
    acc[role] = (acc[role] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    counts['werewolf'] === 3 &&
    counts['villager'] === 3 &&
    counts['seer'] === 1 &&
    counts['witch'] === 1 &&
    counts['hunter'] === 1
  );
};
```

### Event Validation
```typescript
interface EventValidator {
  validateEventSequence(events: GameEvent[]): boolean;
  validateSpeechEvent(event: GameEvent): boolean;
  validateVoteEvent(event: GameEvent, gameState: GameState): boolean;
  validateActionEvent(event: GameEvent, gameState: GameState): boolean;
}

const validateSpeechEvent = (event: GameEvent): boolean => {
  if (event.category !== 'SPEECH') return false;
  const metadata = event.metadata as SpeechMetadata;
  return metadata.characterCount <= 500; // Character limit enforced
};
```

## Performance Optimizations

### Memoization Structures
```typescript
interface MemoizedGameCalculations {
  readonly alivePlayers: ReadonlyArray<Player>;
  readonly deadPlayers: ReadonlyArray<Player>;
  readonly werewolfPlayers: ReadonlyArray<Player>;
  readonly sheriffPlayer: Player | null;
  readonly playerPositions: Map<string, { x: number; y: number }>;
  readonly filteredEvents: ReadonlyArray<GameEvent>;
  readonly eventStats: {
    totalEvents: number;
    eventsByCategory: Record<EventCategory, number>;
    eventsByPlayer: Record<string, number>;
  };
}
```

### Virtual Scrolling Data
```typescript
interface VirtualizedEventListData {
  readonly itemCount: number;
  readonly itemHeight: number;
  readonly containerHeight: number;
  readonly overscan: number;
  readonly items: ReadonlyArray<VirtualizedEventItem>;
}

interface VirtualizedEventItem {
  readonly index: number;
  readonly event: GameEvent;
  readonly top: number;
  readonly height: number;
  readonly key: string;
}
```

## Error Types

### Game Errors
```typescript
interface GameError {
  readonly code: ErrorCode;
  readonly message: string;
  readonly details?: unknown;
  readonly timestamp: Date;
  readonly gameId?: string;
  readonly playerId?: string;
}

type ErrorCode =
  | 'WEBSOCKET_CONNECTION_FAILED'
  | 'GAME_STATE_CORRUPTION'
  | 'REPLAY_DATA_MISSING'
  | 'INVALID_PHASE_TRANSITION'
  | 'PLAYER_ACTION_INVALID'
  | 'SHERIFF_ELECTION_ERROR'
  | 'ROLE_VALIDATION_FAILED';
```

## Integration Points

### AgentScope Integration
```typescript
interface AgentScopeIntegration {
  readonly gameId: string;
  readonly agentType: 'moderator' | 'narrator' | 'ai_player';
  readonly connectionStatus: 'connected' | 'disconnected' | 'error';
  readonly lastHeartbeat: Date;
  readonly messageQueue: ReadonlyArray<AgentScopeMessage>;
}

interface AgentScopeMessage {
  readonly id: string;
  readonly type: 'action_request' | 'state_update' | 'notification';
  readonly gameId: string;
  readonly payload: unknown;
  readonly timestamp: Date;
  readonly responseRequired: boolean;
}
```

## Data Flow Patterns

### State Update Pattern
```typescript
type StateUpdateAction =
  | { type: 'GAME_EVENT_RECEIVED'; payload: GameEvent }
  | { type: 'PLAYER_STATE_CHANGED'; payload: { playerId: string; changes: Partial<Player> } }
  | { type: 'PHASE_CHANGED'; payload: GamePhase }
  | { type: 'SHERIFF_ELECTED'; payload: { sheriffId: string } }
  | { type: 'REPLAY_SELECT_DAY'; payload: { day: number } }
  | { type: 'REPLAY_PLAY_PAUSE'; payload: { isPlaying: boolean } }
  | { type: 'REPLAY_SEEK'; payload: { eventIndex: number } }
  | { type: 'EVENT_FILTER_CHANGED'; payload: EventFilter };
```

This data model provides comprehensive type safety, supports real-time updates, enables replay functionality, and maintains clear separation of concerns while optimizing for performance in a multiplayer gaming environment.