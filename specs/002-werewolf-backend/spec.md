# Feature Specification: Werewolf Game Backend

**Feature Branch**: `002-werewolf-backend`
**Created**: 2025-12-01
**Status**: Draft
**Input**: User description: "基于已确认的狼人杀游戏规则（3狼3民1预言家1女巫1猎人9人局），使用AgentScope框架开发后端系统。需要包含：1. 游戏房间管理 2. 玩家匹配和身份分配 3. 游戏流程控制（夜晚/白天阶段）4. 角色技能系统（预言家查验、女巫解药毒药、猎人开枪）5. 警长竞选系统 6. 投票系统 7. 游戏胜负判定 8. 实时事件广播 9. 游戏回放功能 10. 与前端WebSocket通信"

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Game Session Management (Priority: P1)

As a player, I want to create or join a game room with 9 players, so that I can participate in a werewolf game with the correct role configuration.

**Why this priority**: Core functionality required for any game to start and manage player sessions

**Independent Test**: Users can successfully create a game room, other players can join, and the game starts when exactly 9 players are present

**Acceptance Scenarios**:

1. **Given** a player wants to start a game, **When** they create a room, **Then** a unique room ID is generated and the room shows in the lobby
2. **Given** other players want to join, **When** they enter the room ID, **Then** they are added to the player list and can see all joined players
3. **Given** 9 players are in the room, **When** the room creator starts the game, **Then** role assignment begins and the game transitions to night phase
4. **Given** a player disconnects during lobby, **When** connection is lost, **Then** the player is removed from the room and count updates

---

### User Story 2 - Role Assignment and Identity Management (Priority: P1)

As a game moderator, I want the system to automatically assign roles according to the 3-3-1-1-1 configuration, so that each game has the correct distribution and players receive their private roles.

**Why this priority**: Essential for game integrity and fair play mechanics

**Independent Test**: Starting a new game results in exactly 3 werewolves, 3 villagers, 1 seer, 1 witch, and 1 hunter being assigned with proper visibility controls

**Acceptance Scenarios**:

1. **Given** a game starts with 9 players, **When** role assignment occurs, **Then** exactly 3 players receive werewolf roles and can see their teammates
2. **Given** role assignment completes, **When** a werewolf player views their role, **Then** they can see the names of the other 2 werewolves
3. **Given** role assignment completes, **When** a good player views their role, **Then** they see only their specific role (seer, witch, hunter, or villager)
4. **Given** any player tries to access another player's role, **When** they make the request, **Then** the system denies access with appropriate error handling

---

### User Story 3 - Game Phase Control and Turn Management (Priority: P1)

As a game participant, I want the system to manage day/night cycles and turn order, so that the game progresses according to werewolf rules with proper timing and player actions.

**Why this priority**: Fundamental game flow management that enables all game mechanics to function correctly

**Independent Test**: A complete game can be played from start to finish with proper phase transitions and all role abilities activating at correct times

**Acceptance Scenarios**:

1. **Given** the game starts, **When** night phase begins, **Then** werewolves are prompted to select a victim and seer can check one player's identity
2. **Given** night actions complete, **When** witch phase activates, **Then** witch is notified of the victim and can choose to use antidote or poison
3. **Given** all night actions resolve, **When** day phase begins, **Then** all players are notified of deaths and discussion phase starts
4. **Given** discussion completes, **When** voting phase starts, **Then** all players can vote and results are tallied accurately with sheriff's 1.5 vote weight

---

### User Story 4 - Role Ability Execution System (Priority: P1)

As a player with a special role, I want to use my abilities through a clear interface, so that I can perform my role actions according to game rules.

**Why this priority**: Core game mechanics that enable strategic gameplay and role-specific interactions

**Independent Test**: Each special role (seer, witch, hunter) can successfully use their abilities at appropriate times with proper constraints and visibility

**Acceptance Scenarios**:

1. **Given** a player is the seer, **When** night phase begins, **Then** they can select any alive player and receive accurate "werewolf" or "good" result
2. **Given** the witch has both potions available, **When** someone is killed by werewolves, **Then** witch can choose to save them with antidote or poison someone else
3. **Given** the witch uses a potion, **When** the action completes, **Then** the potion becomes permanently unavailable for the rest of the game
4. **Given** the hunter dies (except by witch poison), **When** death is announced, **Then** they can immediately select any player to eliminate before leaving the game

---

### User Story 5 - Sheriff Election System (Priority: P1)

As a day 1 participant, I want to participate in sheriff election, so that the game can establish leadership and voting mechanics for the remainder of the game.

**Why this priority**: Critical first-day phase that establishes game governance and voting structure

**Independent Test**: Sheriff election on day 1 proceeds with candidate declarations, speeches, voting, and proper sheriff badge assignment

**Acceptance Scenarios**:

1. **Given** it's day 1, **When** the game starts, **Then** sheriff election phase begins and all players can declare candidacy
2. **Given** multiple players are running for sheriff, **When** election speeches occur, **Then** each candidate can speak and other players can listen
3. **Given** speech phase completes, **When** voting occurs, **Then** all non-candidates vote and the candidate with most votes becomes sheriff
4. **Given** a sheriff is elected, **When** the next voting phase occurs, **Then** the sheriff's vote counts as 1.5 votes and they can break ties

---

### User Story 6 - Real-time Event Broadcasting (Priority: P1)

As a game participant, I want to receive real-time updates about all game events, so that I can follow the game progression and make informed decisions.

**Why this priority**: Essential for live game experience and maintaining player engagement with current game state

**Independent Test**: All players receive immediate notifications for game events relevant to them with proper visibility controls

**Acceptance Scenarios**:

1. **Given** any player action occurs, **When** the action resolves, **Then** all relevant players receive immediate WebSocket notifications
2. **Given** werewolves select a victim, **When** the choice is made, **Then** all werewolves receive notification of the target
3. **Given** a player is eliminated, **When** death occurs, **Then** all players receive notification with appropriate death cause
4. **Given** voting results are calculated, **When** voting completes, **Then** all players receive the results with vote counts and sheriff influence

---

### User Story 7 - Game Victory Detection and Resolution (Priority: P2)

As a game participant, I want the system to detect victory conditions and end the game appropriately, so that games conclude correctly with clear winner announcement.

**Why this priority**: Essential for game completion and providing clear outcomes to players

**Independent Test**: Games end immediately when victory conditions are met with correct winner announcement and role reveals

**Acceptance Scenarios**:

1. **Given** all werewolves are eliminated, **When** the last werewolf dies, **Then** the game immediately ends and announces "Good Team Victory"
2. **Given** werewolves equal or outnumber good players, **When** this condition is met, **Then** the game immediately ends and announces "Werewolf Team Victory"
3. **Given** the game ends, **When** victory is announced, **Then** all player roles are revealed and final statistics are displayed
4. **Given** victory detection occurs, **When** game ends, **Then** all players receive complete game summary with progression timeline

---

### User Story 8 - Game Replay and Historical Analysis (Priority: P2)

As a player who wants to review past games, I want to access complete game replays with daily snapshots, so that I can analyze gameplay, learn strategies, and understand key decisions.

**Why this priority**: Valuable for player improvement, game analysis, and understanding game progression patterns

**Independent Test**: Completed games can be replayed with accurate daily state restoration and chronological event playback

**Acceptance Scenarios**:

1. **Given** a game has completed, **When** accessing replay mode, **Then** all game days are available for selection with beginning-of-day player states
2. **Given** a player selects day N, **When** the day loads, **Then** the interface shows exact player states (roles, survival, abilities) at the start of that day
3. **Given** viewing daily snapshot, **When** replay starts, **Then** all events from that day play back in chronological order with original timestamps
4. **Given** replay is active, **When** using playback controls, **Then** users can pause, play, and seek within the selected day's events

### Edge Cases

- What happens when a player disconnects during an active game phase?
- How does system handle timeout when players don't make required actions?
- What occurs when WebSocket connections are lost during critical moments?
- How does system handle simultaneous actions from multiple players?
- What happens when game state becomes corrupted or inconsistent?
- How are tie votes handled when sheriff is dead or disconnected?
- What occurs when multiple players have special abilities that conflict?
- How does system handle players rejoining after accidental disconnection?
- What happens when AgentScope agents become unresponsive?
- How are edge cases in role ability interactions resolved?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support game room creation with unique room IDs and lobby management
- **FR-002**: System MUST support up to 9 players per game room with real-time player list updates
- **FR-003**: System MUST automatically assign roles according to 3 werewolves, 3 villagers, 1 seer, 1 witch, 1 hunter configuration
- **FR-004**: Werewolves MUST see their teammates' identities while good roles see only their own role
- **FR-005**: System MUST manage night/day phase transitions with proper timing and player notification
- **FR-006**: Seer MUST be able to check one player's identity each night and receive accurate results
- **FR-007**: Witch MUST receive werewolf target information each night and can use antidote or poison once per game
- **FR-008**: Hunter MUST be able to shoot one player upon death (except when poisoned by witch)
- **FR-009**: System MUST implement sheriff election on day 1 with candidate speeches and voting
- **FR-010**: Sheriff MUST receive 1.5 vote weight and tie-breaking authority in voting phases
- **FR-011**: System MUST handle voting phases with proper vote counting, sheriff influence, and tie resolution
- **FR-012**: System MUST detect victory conditions immediately and end games with appropriate winner announcement
- **FR-013**: Werewolf victory condition: werewolves equal or outnumber good players, OR all villagers die, OR all special roles die
- **FR-014**: Good team victory condition: all werewolves eliminated
- **FR-015**: System MUST provide real-time WebSocket communication for all game events with proper visibility controls
- **FR-016**: System MUST capture daily player state snapshots at beginning of each game day
- **FR-017**: System MUST support game replay functionality with day selection and chronological event playback
- **FR-018**: System MUST integrate with AgentScope framework for AI player management and game logic
- **FR-019**: System MUST handle player disconnection and reconnection gracefully during active games
- **FR-020**: System MUST persist complete game history with all events, votes, and role reveals for replay functionality

### Key Entities *(include if feature involves data)*

- **GameRoom**: Represents a game session with room ID, player list, game state, and configuration
- **Player**: Represents a game participant with role, survival status, special abilities, and connection state
- **GamePhase**: Represents current game state (night, day, voting, sheriff election) with associated timers
- **Role**: Represents player roles (werewolf, villager, seer, witch, hunter) with specific abilities and visibility rules
- **GameEvent**: Represents any game occurrence with timestamp, type, participants, and visibility rules
- **Vote**: Represents player voting actions with targets, weights, and sheriff influence calculations
- **DailySnapshot**: Captures complete game state at beginning of each day for replay functionality
- **GameSession**: Represents complete game with all events, snapshots, and final outcome for historical access

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Games can be created and joined by 9 players within 30 seconds of room creation
- **SC-002**: Role assignment completes within 5 seconds and provides accurate identity distribution
- **SC-003**: All game phase transitions occur within 2 seconds with proper player notifications
- **SC-004**: Real-time game events are delivered to relevant players within 500ms of occurrence
- **SC-005**: System maintains 99%+ uptime for active game sessions with automatic failover
- **SC-006**: Victory detection occurs instantly upon condition fulfillment with zero delay
- **SC-007**: Game replay functionality provides instant access to any day's snapshot within 1 second
- **SC-008**: System supports 100+ concurrent game rooms without performance degradation
- **SC-009**: Player disconnection/reconnection completes within 10 seconds without game disruption
- **SC-010**: All role abilities execute correctly according to game rules with 100% accuracy
- **SC-011**: Sheriff election completes within 2 minutes with accurate vote counting and winner determination
- **SC-012**: Game state remains consistent across all players with zero synchronization errors
- **SC-013**: WebSocket connections maintain 99.9% reliability with automatic reconnection for interrupted sessions
- **SC-014**: Complete game history is preserved accurately with all events, votes, and role information for replay
- **SC-015**: System processes voting calculations including sheriff weights and tie-breaking within 1 second
