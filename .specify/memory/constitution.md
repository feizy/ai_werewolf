<!-- Sync Impact Report -->
<!-- Version change: 0.0.0 → 1.0.0 (initial constitution) -->
<!-- Modified principles: None (new constitution) -->
<!-- Added sections: All sections (new constitution) -->
<!-- Removed sections: None (new constitution) -->
<!-- Templates requiring updates: ✅ All templates updated and aligned -->
<!-- Follow-up TODOs: None -->

# AI Arena Constitution

## Core Principles

### I. Multi-LLM API Abstraction
All LLM interactions MUST go through a unified API abstraction layer. This ensures seamless switching between providers (OpenAI, Anthropic, Chinese LLMs, etc.) without game logic changes. API providers MUST be configurable via tokens only.

### II. Real-Time Game State Transparency
All game actions, conversations, and state changes MUST be logged with timestamps and player attribution. The frontend MUST display real-time updates of LLM reasoning, speech acts, and voting patterns. No hidden game state is permitted.

### III. Modular Game Architecture
Game logic, LLM interfaces, and frontend presentation MUST be separate modules. Werewolf game mechanics (role validation, phase transitions, win conditions) MUST be independently testable from LLM behavior.

### IV. Provider-Agnostic Testing
Integration tests MUST validate game mechanics independent of specific LLM providers. Mock LLM responses MUST be used for deterministic testing of game flows and edge cases.

### V. Fair Play & Auditability
All LLM decisions MUST be traceable to specific game context and prompts. The system MUST prevent cheating by enforcing turn-based actions and logging all API interactions. Complete game replays MUST be reconstructible from logs.

## Technical Requirements

### LLM Provider Integration
- Support token-based authentication for all major LLM APIs
- Implement retry logic and fallback mechanisms for provider failures
- Enforce rate limiting and cost controls per game/session
- Standardize prompt/response formats across providers

### Real-Time Frontend
- WebSocket or similar real-time communication for live game updates
- Responsive UI showing all player actions and conversation history
- Game state visualization (roles revealed as appropriate, voting results)
- Comprehensive filtering and search of game logs

### Game Logic Requirements
- Support 3 werewolves, 3 villagers, 1 hunter, 1 witch, 1 seer configuration
- Enforce standard Werewolf game rules and phase transitions
- Handle LLM communication failures gracefully
- Support game replay and analysis features

## Development Workflow

### Game-First Development
1. Implement core Werewolf game mechanics without LLM integration
2. Create deterministic test scenarios for all game phases
3. Add LLM integration with mock providers for testing
4. Implement real-time frontend with mock game data
5. Connect all components and validate end-to-end functionality

### Quality Gates
- All game mechanics MUST have 100% test coverage
- Integration tests MUST validate complete game scenarios
- Frontend MUST handle network disconnections and provider failures
- Security review required for API token handling and storage

## Governance

### Constitution Supremacy
This constitution supersedes all other development practices and templates. All feature implementations MUST comply with these principles.

### Amendment Process
- Amendments require documented rationale and impact analysis
- Major version bump for breaking changes to core principles
- Minor version bump for adding new principles or sections
- Patch version for clarifications and wording improvements

### Compliance Review
- All pull requests MUST verify constitution compliance
- Complexity beyond core principles requires explicit justification
- Use `.specify/templates/` for runtime development guidance
- Performance and security reviews for provider integrations

**Version**: 1.0.0 | **Ratified**: 2025-12-01 | **Last Amended**: 2025-12-01
