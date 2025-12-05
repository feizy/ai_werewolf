# WebSocket API Contracts

**Date**: 2025-12-01
**Purpose**: Define WebSocket communication contracts for real-time Werewolf game frontend

## Connection Establishment

### Connect to Game
```javascript
// Client initiates connection
const socket = io('/game', {
  auth: {
    gameId: 'uuid-string',
    playerId: 'player-uuid',
    token: 'jwt-token'
  },
  transports: ['websocket'],
  upgrade: false
});
```

### Connection Response
```json
{
  "type": "CONNECTION_ESTABLISHED",
  "gameId": "uuid-string",
  "playerId": "player-uuid",
  "timestamp": "2025-12-01T10:00:00.000Z",
  "payload": {
    "gameState": "GameState object",
    "connectionStatus": "connected",
    "serverTime": "2025-12-01T10:00:00.000Z"
  }
}
```

## Message Types

### Game State Updates

#### GAME_STATE_UPDATE
```json
{
  "type": "GAME_STATE_UPDATE",
  "gameId": "uuid-string",
  "timestamp": "2025-12-01T10:00:00.000Z",
  "payload": {
    "gameState": {
      "id": "game-uuid",
      "day": 1,
      "phase": {
        "type": "night",
        "round": 1,
        "timeRemaining": 30
      },
      "players": ["Player objects"],
      "sheriffElection": null,
      "sheriffId": null,
      "isReplayMode": false
    },
    "changedPlayerIds": ["player-uuid-1", "player-uuid-2"],
    "newEventIds": ["event-uuid-1"]
  }
}
```

#### PLAYER_EVENT
```json
{
  "type": "PLAYER_EVENT",
  "gameId": "uuid-string",
  "timestamp": "2025-12-01T10:00:00.000Z",
  "payload": {
    "event": {
      "id": "event-uuid",
      "timestamp": "2025-12-01T10:00:00.000Z",
      "day": 1,
      "phase": {
        "type": "discussion",
        "timeRemaining": 120
      },
      "category": "SPEECH",
      "description": "Player speaks during discussion",
      "participants": ["player-uuid-1"],
      "sequenceNumber": 1,
      "metadata": {
        "type": "speech",
        "speakerId": "player-uuid-1",
        "content": "I think player 3 is suspicious...",
        "characterCount": 42,
        "isSheriffSpeaking": false
      }
    },
    "affectedPlayerIds": ["player-uuid-1"]
  }
}
```

#### PHASE_CHANGE
```json
{
  "type": "PHASE_CHANGE",
  "gameId": "uuid-string",
  "timestamp": "2025-12-01T10:00:00.000Z",
  "payload": {
    "oldPhase": {
      "type": "night",
      "round": 1,
      "timeRemaining": 30
    },
    "newPhase": {
      "type": "sheriff_election",
      "candidates": ["player-uuid-1", "player-uuid-3"],
      "speechesCompleted": 0
    },
    "transitionReason": "Night phase completed, sheriff election begins"
  }
}
```

### Sheriff Election

#### SHERIFF_ELECTION_UPDATE
```json
{
  "type": "SHERIFF_ELECTION_UPDATE",
  "gameId": "uuid-string",
  "timestamp": "2025-12-01T10:00:00.000Z",
  "payload": {
    "election": {
      "id": "election-uuid",
      "gameId": "game-uuid",
      "day": 1,
      "phase": "speeches",
      "candidates": [
        {
          "playerId": "player-uuid-1",
          "playerName": "Player Name 1",
          "speech": "I nominate myself as sheriff...",
          "speechOrder": 1,
          "hasSpoken": true,
          "withdrew": false
        }
      ],
      "votes": [],
      "winnerId": null,
      "startedAt": "2025-12-01T10:00:00.000Z",
      "completedAt": null
    },
    "changeType": "candidate_added"
  }
}
```

### Replay System

#### REPLAY_SNAPSHOT
```json
{
  "type": "REPLAY_SNAPSHOT",
  "gameId": "uuid-string",
  "timestamp": "2025-12-01T10:00:00.000Z",
  "payload": {
    "snapshot": {
      "id": "snapshot-uuid",
      "gameId": "game-uuid",
      "day": 2,
      "timestamp": "2025-12-01T10:05:00.000Z",
      "playerStates": [
        {
          "playerId": "player-uuid-1",
          "player": "Player object",
          "roleStatus": "RoleStatus object",
          "position": 1,
          "isAlive": true,
          "isSheriff": false
        }
      ],
      "sheriffId": "player-uuid-3",
      "phaseAtSnapshot": {
        "type": "discussion",
        "timeRemaining": 90
      },
      "totalEvents": 15,
      "eventIndex": 8
    }
  }
}
```

#### REPLAY_EVENTS
```json
{
  "type": "REPLAY_EVENTS",
  "gameId": "uuid-string",
  "timestamp": "2025-12-01T10:00:00.000Z",
  "payload": {
    "events": ["GameEvent objects"],
    "fromEventIndex": 0,
    "toEventIndex": 50,
    "replaySpeed": 1.0,
    "isPlaying": true
  }
}
```

## Client Actions

### Player Action Request
```javascript
// Client sends player action
socket.emit('PLAYER_ACTION', {
  gameId: 'game-uuid',
  playerId: 'player-uuid',
  action: {
    type: 'speech',
    content: 'I believe player 5 is the werewolf...',
    timestamp: '2025-12-01T10:00:00.000Z'
  },
  requestId: 'request-uuid'
});
```

### Vote Request
```javascript
// Client sends vote
socket.emit('CAST_VOTE', {
  gameId: 'game-uuid',
  playerId: 'player-uuid',
  vote: {
    targetPlayerId: 'player-uuid-5',
    round: 1,
    timestamp: '2025-12-01T10:00:00.000Z'
  },
  requestId: 'request-uuid'
});
```

### Sheriff Election Participation
```javascript
// Client joins sheriff election
socket.emit('JOIN_SHERIFF_ELECTION', {
  gameId: 'game-uuid',
  playerId: 'player-uuid',
  participate: true,
  requestId: 'request-uuid'
});

// Client submits sheriff vote
socket.emit('CAST_SHERIFF_VOTE', {
  gameId: 'game-uuid',
  playerId: 'player-uuid',
  vote: {
    candidateId: 'player-uuid-3',
    timestamp: '2025-12-01T10:00:00.000Z'
  },
  requestId: 'request-uuid'
});
```

### Replay Control
```javascript
// Client requests replay day
socket.emit('REQUEST_REPLAY_DAY', {
  gameId: 'game-uuid',
  day: 2,
  requestId: 'request-uuid'
});

// Client controls replay playback
socket.emit('REPLAY_CONTROL', {
  gameId: 'game-uuid',
  control: {
    action: 'play' | 'pause' | 'seek',
    speed: 1.0,
    targetEventIndex: 25
  },
  requestId: 'request-uuid'
});
```

## Response Types

### Success Response
```json
{
  "type": "ACTION_SUCCESS",
  "gameId": "uuid-string",
  "timestamp": "2025-12-01T10:00:00.000Z",
  "payload": {
    "requestId": "request-uuid",
    "action": "PLAYER_ACTION",
    "result": {
      "success": true,
      "message": "Action processed successfully",
      "newEvent": "GameEvent object"
    }
  }
}
```

### Error Response
```json
{
  "type": "ACTION_ERROR",
  "gameId": "uuid-string",
  "timestamp": "2025-12-01T10:00:00.000Z",
  "payload": {
    "requestId": "request-uuid",
    "action": "PLAYER_ACTION",
    "error": {
      "code": "SPEECH_TOO_LONG",
      "message": "Speech exceeds 500 character limit",
      "details": {
        "characterCount": 567,
        "maxAllowed": 500
      }
    }
  }
}
```

## Connection Management

### Heartbeat
```javascript
// Client sends periodic heartbeat
socket.emit('HEARTBEAT', {
  gameId: 'game-uuid',
  playerId: 'player-uuid',
  timestamp: '2025-12-01T10:00:00.000Z'
});

// Server responds
{
  "type": "HEARTBEAT_ACK",
  "gameId": "uuid-string",
  "timestamp": "2025-12-01T10:00:00.000Z",
  "payload": {
    "serverTime": "2025-12-01T10:00:00.000Z",
    "latency": 45
  }
}
```

### Reconnection
```json
{
  "type": "RECONNECTION_SYNC",
  "gameId": "uuid-string",
  "timestamp": "2025-12-01T10:00:00.000Z",
  "payload": {
    "gameState": "GameState object",
    "missedEvents": ["GameEvent objects"],
    "sequenceNumber": 42,
    "reconnectedAt": "2025-12-01T10:00:00.000Z"
  }
}
```

## Event Categories and Metadata

### SPEECH Events
```json
{
  "id": "event-uuid",
  "category": "SPEECH",
  "metadata": {
    "type": "speech",
    "speakerId": "player-uuid",
    "content": "I think we need to be more careful...",
    "characterCount": 47,
    "isSheriffSpeaking": false,
    "phase": "discussion",
    "timeRemaining": 95
  }
}
```

### ACTION Events
```json
{
  "id": "event-uuid",
  "category": "ACTION",
  "metadata": {
    "type": "action",
    "actionType": "save",
    "actorId": "player-uuid-7", // witch
    "targetId": "player-uuid-3",
    "result": "success",
    "phase": "night",
    "round": 2
  }
}
```

### VOTE Events
```json
{
  "id": "event-uuid",
  "category": "VOTE",
  "metadata": {
    "type": "vote",
    "voterId": "player-uuid-1",
    "targetId": "player-uuid-5",
    "weight": 1.5, // sheriff vote weight
    "round": 1,
    "votingPhase": "elimination"
  }
}
```

### DEATH Events
```json
{
  "id": "event-uuid",
  "category": "DEATH",
  "metadata": {
    "type": "death",
    "playerId": "player-uuid-4",
    "role": "werewolf",
    "causeOfDeath": "werewolf_attack",
    "day": 1,
    "phase": "night"
  }
}
```

### ELECTION Events
```json
{
  "id": "event-uuid",
  "category": "ELECTION",
  "metadata": {
    "type": "election",
    "electionType": "candidate_nomination",
    "candidateId": "player-uuid-2",
    "speechContent": "I nominate myself as sheriff...",
    "speechOrder": 2
  }
}
```

## Error Codes

### Connection Errors
- `WEBSOCKET_CONNECTION_FAILED`: Unable to establish WebSocket connection
- `AUTHENTICATION_FAILED`: Invalid authentication token
- `GAME_NOT_FOUND`: Game ID does not exist
- `PLAYER_NOT_IN_GAME`: Player ID not associated with game

### Game State Errors
- `GAME_STATE_CORRUPTION`: Invalid game state received
- `INVALID_PHASE_TRANSITION`: Illegal phase transition attempted
- `PLAYER_ACTION_INVALID`: Action not allowed in current phase

### Action Errors
- `SPEECH_TOO_LONG`: Speech exceeds 500 character limit
- `VOTE_INVALID`: Invalid vote target
- `ROLE_ACTION_INVALID`: Role-specific action not available
- `SHERIFF_ELECTION_ERROR`: Sheriff election action invalid

### Replay Errors
- `REPLAY_DATA_MISSING`: No replay data available for requested day
- `INVALID_REPLAY_REQUEST`: Invalid replay control request
- `REPLAY_OUT_OF_SYNC`: Replay state out of sync

## Rate Limits

### Client Actions
- Speech: Max 1 per 10 seconds
- Votes: Max 1 per voting round
- Sheriff election: Max 1 nomination per election
- Replay requests: Max 5 per minute

### Server Messages
- Game state updates: As needed, batched if < 100ms apart
- Event notifications: Immediate
- Heartbeat: Every 30 seconds
- Sync messages: On reconnection

## Data Validation

### Message Structure
```typescript
interface WebSocketMessage {
  type: MessageType;
  gameId: string;
  timestamp: string; // ISO 8601
  payload: unknown;
  requestId?: string;
}
```

### Required Fields
- `type`: Must be valid MessageType
- `gameId`: Valid UUID string
- `timestamp`: Valid ISO 8601 date string
- `payload`: Valid structure for message type

### Validation Rules
- All IDs must be valid UUIDs
- All timestamps must be ISO 8601 format
- All player actions must reference valid players in current game state
- Speech content must not exceed 500 characters
- Vote weights must respect sheriff status (1.5 vs 1.0)

This WebSocket API provides comprehensive real-time communication for the Werewolf game frontend with robust error handling, replay support, and clear separation of concerns.