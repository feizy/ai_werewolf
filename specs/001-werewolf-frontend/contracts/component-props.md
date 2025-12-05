# Component Props Contracts

**Date**: 2025-12-01
**Purpose**: Define React component prop interfaces for Werewolf game frontend

## Core Game Components

### GameTable
```typescript
interface GameTableProps {
  readonly gameState: GameState;
  readonly currentPlayerId?: string;
  readonly selectedPlayerId?: string | null;
  readonly hoveredPlayerId?: string | null;
  readonly showRoles?: boolean; // For debugging/spectator mode
  readonly onPlayerClick?: (playerId: string) => void;
  readonly onPlayerHover?: (playerId: string | null) => void;
  readonly className?: string;
  readonly style?: React.CSSProperties;
}

interface PlayerCircleProps {
  readonly players: ReadonlyArray<Player>;
  readonly gameState: GameState;
  readonly radius?: number; // Default: 300
  readonly centerOffset?: { x: number; y: number }; // Default: {0, 0}
  readonly selectedPlayerId?: string | null;
  readonly hoveredPlayerId?: string | null;
  readonly onPlayerClick?: (playerId: string) => void;
  readonly onPlayerHover?: (playerId: string | null) => void;
  readonly showRoles?: boolean;
  readonly animated?: boolean; // Default: true
  readonly className?: string;
}

interface PlayerCardProps {
  readonly player: Player;
  readonly position: { x: number; y: number };
  readonly isSelected: boolean;
  readonly isHovered: boolean;
  readonly showRole: boolean;
  readonly isSheriff: boolean;
  readonly onClick: () => void;
  readonly onHover: (isHovered: boolean) => void;
  readonly disabled?: boolean;
  readonly size?: 'small' | 'medium' | 'large'; // Default: medium
  readonly className?: string;
}

interface GamePhaseBannerProps {
  readonly phase: GamePhase;
  readonly timeRemaining?: number;
  readonly isReplayMode?: boolean;
  readonly className?: string;
  readonly style?: React.CSSProperties;
}
```

### Event Log Components
```typescript
interface EventLogProps {
  readonly events: ReadonlyArray<GameEvent>;
  readonly filters: EventFilter;
  readonly onFilterChange: (filters: EventFilter) => void;
  readonly onEventClick?: (eventId: string) => void;
  readonly maxHeight?: number; // Default: 400
  readonly autoScroll?: boolean; // Default: true
  readonly virtualized?: boolean; // Default: true
  readonly className?: string;
}

interface EventListProps {
  readonly events: ReadonlyArray<GameEvent>;
  readonly filters: EventFilter;
  readonly onEventClick?: (eventId: string) => void;
  readonly onScrollEnd?: () => void;
  readonly itemHeight?: number; // Default: 60
  readonly overscan?: number; // Default: 5
  readonly className?: string;
}

interface EventItemProps {
  readonly event: GameEvent;
  readonly isSelected: boolean;
  readonly onClick: () => void;
  readonly showMetadata?: boolean; // Default: false
  readonly compact?: boolean; // Default: false
  readonly className?: string;
}

interface EventFiltersProps {
  readonly filters: EventFilter;
  readonly onFilterChange: (filters: EventFilter) => void;
  readonly availableCategories: ReadonlyArray<EventCategory>;
  readonly availablePlayers: ReadonlyArray<Player>;
  readonly className?: string;
}
```

### Sheriff Election Components
```typescript
interface SheriffElectionProps {
  readonly election: SheriffElection;
  readonly currentUserId?: string;
  readonly gameState: GameState;
  readonly onCandidateClick?: (playerId: string) => void;
  readonly onVoteCast?: (candidateId: string) => void;
  readonly className?: string;
}

interface ElectionPhaseProps {
  readonly election: SheriffElection;
  readonly currentUserId?: string;
  readonly onJoinElection: () => void;
  readonly onWithdraw: () => void;
  readonly className?: string;
}

interface CandidateCardProps {
  readonly candidate: ElectionCandidate;
  readonly currentUserId?: string;
  readonly isSelected: boolean;
  readonly canVote: boolean;
  readonly onSelect: () => void;
  readonly showSpeech: boolean;
  readonly className?: string;
}

interface VotingInterfaceProps {
  readonly election: SheriffElection;
  readonly currentUserId?: string;
  readonly candidates: ReadonlyArray<ElectionCandidate>;
  readonly voteWeight: number; // 1.0 for regular, 1.5 for sheriff
  readonly onVoteCast: (candidateId: string) => void;
  readonly onVoteChange?: (candidateId: string) => void;
  readonly timeRemaining?: number;
  readonly className?: string;
}
```

### Replay Components
```typescript
interface ReplayControlsProps {
  readonly replay: GameReplay;
  readonly onPlayPause: () => void;
  readonly onStop: () => void;
  readonly onSpeedChange: (speed: number) => void;
  readonly onSeek: (eventIndex: number) => void;
  readonly onDaySelect: (day: number) => void;
  readonly onFilterChange: (filters: ReplayFilters) => void;
  readonly className?: string;
}

interface DaySelectorProps {
  readonly replay: GameReplay;
  readonly availableDays: ReadonlyArray<number>;
  readonly onDaySelect: (day: number) => void;
  readonly disabled?: boolean;
  readonly className?: string;
}

interface PlaybackTimelineProps {
  readonly replay: GameReplay;
  readonly events: ReadonlyArray<GameEvent>;
  readonly onSeek: (eventIndex: number) => void;
  readonly onHover: (eventIndex: number) => void;
  readonly currentHoveredEvent?: number;
  readonly height?: number; // Default: 60
  readonly className?: string;
}

interface ReplayFiltersProps {
  readonly filters: ReplayFilters;
  readonly onFilterChange: (filters: ReplayFilters) => void;
  readonly availableCategories: ReadonlyArray<EventCategory>;
  readonly availablePlayers: ReadonlyArray<Player>;
  readonly totalEventCount: number;
  readonly filteredEventCount: number;
  readonly className?: string;
}
```

## Utility Components

### Loading States
```typescript
interface LoadingSpinnerProps {
  readonly size?: 'small' | 'medium' | 'large'; // Default: medium
  readonly color?: string; // Default: theme primary
  readonly text?: string;
  readonly overlay?: boolean; // Default: false
  readonly className?: string;
}

interface ConnectionStatusProps {
  readonly status: 'connected' | 'disconnected' | 'reconnecting' | 'error';
  readonly message?: string;
  readonly onReconnect?: () => void;
  readonly showRetryButton?: boolean; // Default: true
  readonly className?: string;
}
```

### Modal and Overlay Components
```typescript
interface ModalProps {
  readonly isOpen: boolean;
  readonly onClose: () => void;
  readonly title?: string;
  readonly children: React.ReactNode;
  readonly size?: 'small' | 'medium' | 'large' | 'fullscreen'; // Default: medium
  readonly closeOnOverlayClick?: boolean; // Default: true
  readonly closeOnEscape?: boolean; // Default: true
  readonly className?: string;
}

interface ToastNotificationProps {
  readonly notification: ToastNotification;
  readonly onClose: (id: string) => void;
  readonly autoHide?: boolean; // Default: true
  readonly duration?: number; // Default: 5000ms
  readonly position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left'; // Default: top-right
  readonly className?: string;
}
```

### Player Status Indicators
```typescript
interface RoleStatusProps {
  readonly player: Player;
  readonly gameState: GameState;
  readonly showRole?: boolean; // Default: false
  readonly compact?: boolean; // Default: false
  readonly className?: string;
}

interface SheriffBadgeProps {
  readonly isSheriff: boolean;
  readonly voteWeight: number; // 1.0 or 1.5
  readonly showWeight?: boolean; // Default: true
  readonly size?: 'small' | 'medium' | 'large'; // Default: medium
  readonly className?: string;
}

interface PlayerHealthProps {
  readonly isAlive: boolean;
  readonly role: PlayerRole;
  readonly showRole?: boolean; // Default: false
  readonly animated?: boolean; // Default: true
  readonly className?: string;
}
```

## Layout Components

### GameLayout
```typescript
interface GameLayoutProps {
  readonly children: React.ReactNode;
  readonly gameState: GameState;
  readonly currentPlayerId?: string;
  readonly sidebarContent?: React.ReactNode;
  readonly headerContent?: React.ReactNode;
  readonly footerContent?: React.ReactNode;
  readonly isReplayMode?: boolean;
  readonly className?: string;
}
```

### ResponsiveContainer
```typescript
interface ResponsiveContainerProps {
  readonly children: React.ReactNode;
  readonly breakpoint?: 'mobile' | 'tablet' | 'desktop'; // Default: desktop
  readonly padding?: number | string;
  readonly maxWidth?: number;
  readonly centerContent?: boolean; // Default: false
  readonly className?: string;
}
```

## Data Display Components

### CharacterCounter
```typescript
interface CharacterCounterProps {
  readonly current: number;
  readonly maximum: number;
  readonly showWarning?: boolean; // Default: true
  readonly warningThreshold?: number; // Default: 0.9
  readonly className?: string;
}
```

### TimerDisplay
```typescript
interface TimerDisplayProps {
  readonly timeRemaining: number; // in seconds
  readonly totalTime?: number; // for progress bar
  readonly format?: 'mm:ss' | 'ss' | 'custom'; // Default: mm:ss
  readonly showProgress?: boolean; // Default: true
  readonly warningThreshold?: number; // Default: 10 seconds
  readonly className?: string;
}
```

### EventTimestamp
```typescript
interface EventTimestampProps {
  readonly timestamp: Date;
  readonly format?: 'relative' | 'absolute' | 'both'; // Default: relative
  readonly showDate?: boolean; // Default: false
  readonly className?: string;
}
```

## Form Components

### SpeechInput
```typescript
interface SpeechInputProps {
  readonly value: string;
  readonly onChange: (value: string) => void;
  readonly onSubmit: (content: string) => void;
  readonly maxLength?: number; // Default: 500
  readonly placeholder?: string;
  readonly disabled?: boolean;
  readonly showCounter?: boolean; // Default: true
  readonly autoResize?: boolean; // Default: true
  readonly className?: string;
}
```

### VotingButtons
```typescript
interface VotingButtonsProps {
  readonly candidates: ReadonlyArray<{ id: string; name: string }>;
  readonly selectedCandidate?: string;
  readonly onVoteSelect: (candidateId: string) => void;
  readonly onVoteSubmit: () => void;
  readonly disabled?: boolean;
  readonly voteWeight?: number; // Display sheriff vote weight
  readonly timeRemaining?: number;
  readonly className?: string;
}
```

## Type Definitions for Props

### EventFilter
```typescript
interface EventFilter {
  readonly categories: ReadonlyArray<EventCategory>;
  readonly playerIds: ReadonlyArray<string>;
  readonly dayRange: { start: number; end: number } | null;
  readonly searchText: string;
  readonly timeRange: { start: Date; end: Date } | null;
}
```

### ReplayFilters
```typescript
interface ReplayFilters extends EventFilter {
  readonly speed: number;
  readonly autoPlay?: boolean;
  readonly showOnlyKeyEvents?: boolean;
}
```

### ToastNotification
```typescript
interface ToastNotification {
  readonly id: string;
  readonly type: 'info' | 'success' | 'warning' | 'error';
  readonly title: string;
  readonly message: string;
  readonly duration: number;
  readonly timestamp: Date;
  readonly actions?: ReadonlyArray<{
    readonly label: string;
    readonly action: () => void;
    readonly style?: 'primary' | 'secondary';
  }>;
}
```

## Prop Validation Rules

### Required Props
- All `gameState` props must be valid `GameState` objects
- All `player` props must be valid `Player` objects
- All `id` props must be non-empty strings
- All `onClick` and `onChange` props must be functions

### Optional Props with Defaults
- `className`: string | undefined
- `style`: React.CSSProperties | undefined
- `disabled`: boolean | false
- `size`: 'small' | 'medium' | 'large' | 'medium'
- `animated`: boolean | true

### Validation Examples
```typescript
// Validate GameTable props
const validateGameTableProps = (props: GameTableProps): boolean => {
  return (
    props.gameState !== undefined &&
    typeof props.gameState.id === 'string' &&
    Array.isArray(props.gameState.players) &&
    props.gameState.players.length === 9
  );
};

// Validate EventLog props
const validateEventLogProps = (props: EventLogProps): boolean => {
  return (
    Array.isArray(props.events) &&
    props.filters !== undefined &&
    typeof props.onFilterChange === 'function'
  );
};
```

## Accessibility Props

### ARIA Support
```typescript
interface AccessibleComponentProps {
  readonly 'aria-label'?: string;
  readonly 'aria-labelledby'?: string;
  readonly 'aria-describedby'?: string;
  readonly 'aria-expanded'?: boolean;
  readonly 'aria-selected'?: boolean;
  readonly 'aria-disabled'?: boolean;
  readonly role?: string;
  readonly tabIndex?: number;
}
```

### Keyboard Navigation
```typescript
interface KeyboardNavigationProps {
  readonly onKeyDown?: (event: React.KeyboardEvent) => void;
  readonly onFocus?: (event: React.FocusEvent) => void;
  readonly onBlur?: (event: React.FocusEvent) => void;
  readonly focusable?: boolean; // Default: false
}
```

This prop interface specification ensures type safety, consistency, and maintainability across all React components in the Werewolf game frontend.