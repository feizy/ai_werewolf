# Feature Specification: Werewolf Game Frontend

**Feature Branch**: `001-werewolf-frontend`
**Created**: 2025-12-01
**Status**: Draft
**Input**: User description: "1.前端页面包含一个玩家展示区和日志区。玩家展示区展示所有玩家（模拟成围坐的状态，玩家可用原点展示），展示玩家姓名、游戏身份、存活状态和能力状态（如女巫是否还有解药、毒药）。日志区展示所有事件（包含主持人发言、玩家发言、玩家动作等等所有事件）2.开发前需要好好查询狼人杀的规则（3狼3民预言家女巫猎人这个版本），形成文档，让我确认。3、使用agentscope框架进行开发。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Game State Visualization (Priority: P1)

As a game observer, I want to see all players displayed in a circular arrangement around a virtual table, so that I can understand the game dynamics and player relationships at a glance.

**Why this priority**: Core visualization requirement that enables users to understand game state and follow the gameplay

**Independent Test**: Users can open the game interface and see all 9 players correctly positioned in a circle with basic information visible, without any game actions required

**Acceptance Scenarios**:

1. **Given** a new game starts with 9 players, **When** the frontend loads, **Then** all players are displayed in circular formation around the game table
2. **Given** players have different roles, **When** the game begins, **Then** each player shows their name, role (if revealed), and survival status
3. **Given** the game is in progress, **When** viewing the player area, **Then** special role states (witch's potions, hunter's gun) are clearly indicated

---

### User Story 2 - Real-Time Event Logging (Priority: P1)

As a game participant or observer, I want to see a comprehensive log of all game events with timestamps, so that I can track game progression and understand player decisions.

**Why this priority**: Essential for transparency and game analysis, supports the constitution's auditability requirements

**Independent Test**: Users can observe any game action and immediately see corresponding entries in the log area with proper categorization and formatting

**Acceptance Scenarios**:

1. **Given** the game moderator makes an announcement, **When** the announcement occurs, **Then** it appears in the log with "MODERATOR" category and timestamp
2. **Given** an LLM player makes a statement during discussion, **When** they speak, **Then** their message appears in the log with their name and "SPEECH" category
3. **Given** a player uses their special ability (witch saves, hunter shoots), **When** the action resolves, **Then** it appears in the log with "ACTION" category and detailed description
4. **Given** voting occurs, **When** votes are cast, **Then** all voting actions appear in the log with "VOTE" category
5. **Given** a player dies during night phase, **When** death is announced, **Then** it appears in the log with "DEATH" category and timestamp

---

### User Story 3 - Role Status Management (Priority: P2)

As a player or observer, I want to see real-time status updates for special role abilities, so that I can track game progression and make informed decisions.

**Why this priority**: Critical for game strategy and understanding available options during gameplay

**Independent Test**: Users can observe the status indicators for special roles and verify they update correctly when abilities are used

**Acceptance Scenarios**:

1. **Given** the witch has both potions available, **When** viewing the witch's player info, **Then** both "解药" (antidote) and "毒药" (poison) show as "可用" (available)
2. **Given** the witch uses the antidote to save someone, **When** the action completes, **Then** the antidote status changes to "已使用" (used)
3. **Given** the hunter is still alive, **When** viewing the hunter's player info, **Then** their gun status shows as "可开枪" (can shoot)
4. **Given** the hunter dies without shooting, **When** their death is processed, **Then** their gun status shows as "未使用" (unused)

---

### User Story 4 - Sheriff Election (Priority: P1)

As a game participant, I want to participate in sheriff election on day 1, so that I can help establish game leadership and order.

**Why this priority**: Critical game phase that establishes leadership and voting mechanics for the entire game

**Independent Test**: Users can observe sheriff election phase with candidate declarations, speeches, and voting process completing successfully

**Acceptance Scenarios**:

1. **Given** it's day 1 and sheriff election phase starts, **When** election begins, **Then** the phase banner shows "竞选警长" and players can choose to participate
2. **Given** players are running for sheriff, **When** candidates speak, **Then** each candidate's speech appears in log with "SPEECH" category and respects 500-character limit
3. **Given** sheriff election voting is in progress, **When** votes are cast, **Then** voting results appear in log with "VOTE" category and winner is announced
4. **Given** sheriff is elected, **When** election completes, **Then** sheriff badge appears on elected player and phase changes to discussion

---

### User Story 5 - Game Replay and Daily Snapshots (Priority: P2)

As a game analyst or player, I want to review daily snapshots of player states and replay the complete game, so that I can analyze game progression and understand key decisions.

**Why this priority**: Essential for game analysis, learning, and satisfying the constitution's auditability requirements

**Independent Test**: Users can select any day from a completed game and view the exact player state snapshot at the beginning of that day, with all game events replayable

**Acceptance Scenarios**:

1. **Given** a game has completed, **When** accessing replay mode, **Then** day selector shows all days (Day 1, Day 2, etc.) with current selection highlighted
2. **Given** user selects Day N from selector, **When** day loads, **Then** interface shows exact player state snapshot at beginning of that day (roles, survival, special abilities)
3. **Given** viewing daily snapshot, **When** user starts replay, **Then** all game events from that day play back in chronological order with original timestamps
4. **Given** replay is in progress, **When** user pauses/stops replay, **Then** they can continue from any point or select different day

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Frontend MUST display all 9 players in circular formation around virtual table
- **FR-002**: System MUST show player name, role (when revealed), and survival status for each player
- **FR-003**: Frontend MUST maintain a comprehensive event log with categorization (MODERATOR, SPEECH, ACTION, VOTE)
- **FR-004**: System MUST display real-time updates for special role abilities (witch's potions, hunter's gun)
- **FR-005**: Event log MUST include timestamps for all entries
- **FR-006**: Player display MUST update immediately when survival status changes
- **FR-007**: Log area MUST support filtering by basic event categories (MODERATOR, SPEECH, ACTION, VOTE, DEATH)
- **FR-008**: System MUST support scrolling through historical log entries
- **FR-009**: Frontend MUST display game phase information with prominent banner at top showing current phase (夜晚/竞选警长/讨论/投票)
- **FR-010**: System MUST handle real-time updates via WebSocket or similar technology
- **FR-011**: Frontend MUST support sheriff election phase on day 1 with candidate declarations and voting
- **FR-012**: System MUST display sheriff badge on current sheriff player with 1.5 voting power indication
- **FR-013**: Frontend MUST indicate when sheriff has last speaking privilege during discussions
- **FR-014**: System MUST enforce 500-character limit for all player speech entries
- **FR-015**: Event log MUST include DEATH category for player elimination events
- **FR-016**: System MUST capture daily player state snapshots at beginning of each game day
- **FR-017**: Frontend MUST provide day selector for replay mode with all game days available
- **FR-018**: System MUST display player state snapshot when specific day is selected in replay
- **FR-019**: Frontend MUST support chronological replay of all events within selected day
- **FR-020**: Replay controls MUST allow pause, play, and seek within selected day's events

### Key Entities

- **Player**: Represents a game participant with name, role, survival status, sheriff status, and special ability states
- **GameEvent**: Represents any game occurrence with timestamp, category, description, and participant
- **GamePhase**: Represents current game state (night, sheriff election, discussion, voting, etc.)
- **RoleStatus**: Tracks availability of special abilities for witch (antidote/poison) and hunter (gun)
- **SheriffElection**: Represents election process with candidates, speeches, voting results, and current sheriff
- **DailySnapshot**: Captures complete player state at beginning of each game day for replay functionality
- **GameReplay**: Represents replay session with day selection, playback controls, and event timeline

## Assumptions

- **A001**: Backend provides real-time game state via WebSocket or similar connection
- **A002**: Player data includes Chinese language names and role descriptions
- **A003**: Event log supports both Chinese and English content from LLM players
- **A004**: AgentScope framework provides necessary backend integration capabilities
- **A005**: Game follows standard 3-3-1-1-1 Werewolf rules as researched
- **A006**: Werewolf players know their teammates' identities from game start; good players can only infer others' identities through observation
- **A007**: All player speech limited to maximum 500 characters per message
- **A008**: Sheriff election occurs on day 1 before discussion phase, with candidates giving speeches and voting

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can identify game state and player status within 5 seconds of opening the interface
- **SC-002**: Event log displays new game events within 1 second of backend notification
- **SC-003**: Users can review complete game history through scrolling and filtering functionality
- **SC-004**: Player visualization accurately reflects all 9 roles and their current states with 100% accuracy
- **SC-005**: Interface supports concurrent viewing by multiple observers without performance degradation
- **SC-006**: Users can distinguish between different event types through visual categorization and formatting
- **SC-007**: Users can select any day from completed game and view accurate player state snapshot within 2 seconds
- **SC-008**: Game replay functionality supports chronological event playback with original timestamps preserved
- **SC-009**: Replay controls provide responsive play/pause/seek functionality within 100ms of user input

## Edge Cases

- What happens when WebSocket connection is lost during active game?
- How does the interface handle malformed game state data from backend?
- What occurs when multiple events happen simultaneously?
- How does the system display conflicting role states during sync issues?
- What happens when the log exceeds display capacity - auto-scroll behavior?
- How are special Unicode characters and emojis from LLM responses handled?
- What occurs when game is interrupted and needs to be resumed from saved state?
- How does replay system handle corrupted or incomplete game data?
- What happens when user selects day during replay but backend fails to load snapshot?
- How does interface handle replay of very long games with many events?
- What occurs when replay controls are used during live game playback?
- How does system manage memory usage when loading multiple daily snapshots?

## Dependencies

- **Backend Integration**: Requires AgentScope-based backend with real-time game state broadcasting
- **WebSocket Infrastructure**: Real-time communication channel for game updates
- **Authentication System**: User authentication for accessing game sessions
- **Game Logic Engine**: Backend implementation of Werewolf rules and game flow management
- **Data Storage**: Persistent storage for daily snapshots and complete game event history
- **Replay Engine**: Backend service for retrieving daily snapshots and chronological event sequences
- **State Management**: Frontend state management for handling live games vs replay mode
