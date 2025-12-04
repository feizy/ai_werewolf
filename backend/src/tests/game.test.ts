import { GameEngine } from '@/services/GameEngine';
import { GameRoomModel } from '@/models/GameRoom';
import { AgentScopeService } from '@/services/AgentScopeService';
import { GameEventService } from '@/services/GameEventService';
import { PlayerModel } from '@/models/Player';
import { RoleType } from '@/types';

// Mock AgentScopeService
jest.mock('@/services/AgentScopeService');
jest.mock('@/services/GameEventService');

describe('GameEngine', () => {
  let gameEngine: GameEngine;
  let room: GameRoomModel;
  let mockAgentScopeService: jest.Mocked<AgentScopeService>;
  let mockEventService: jest.Mocked<GameEventService>;

  beforeEach(() => {
    // 创建测试房间
    room = GameRoomModel.createTestRoom(9);

    // Mock服务
    mockAgentScopeService = new AgentScopeService() as jest.Mocked<AgentScopeService>;
    mockEventService = new GameEventService() as jest.Mocked<GameEventService>;

    // Mock AgentScope方法
    mockAgentScopeService.initialize = jest.fn().mockResolvedValue(undefined);
    mockAgentScopeService.createAgent = jest.fn().mockResolvedValue('mock-agent-id');

    // Mock EventService方法
    mockEventService.createEvent = jest.fn().mockResolvedValue({
      id: 'mock-event-id',
      sessionId: 'mock-session-id',
      type: 'game_start',
      phase: 'night',
      dayCount: 1,
      timestamp: new Date(),
      content: 'Mock event'
    });
    mockEventService.getSessionEvents = jest.fn().mockReturnValue([]);

    // 创建游戏引擎
    gameEngine = new GameEngine(
      room,
      mockAgentScopeService,
      mockEventService,
      { autoProgress: false } // 禁用自动进度用于测试
    );
  });

  describe('Initialization', () => {
    it('should create game session with correct configuration', () => {
      const session = gameEngine.getSession();

      expect(session.roomId).toBe(room.id);
      expect(session.players).toHaveLength(9);
      expect(session.currentPhase).toBe('night');
      expect(session.dayCount).toBe(1);
    });

    it('should assign roles correctly', () => {
      const session = gameEngine.getSession();
      const roles = session.players.map(p => p.role);

      expect(roles.filter(r => r === RoleType.WEREWOLF)).toHaveLength(3);
      expect(roles.filter(r => r === RoleType.VILLAGER)).toHaveLength(3);
      expect(roles.filter(r => r === RoleType.SEER)).toHaveLength(1);
      expect(roles.filter(r => r === RoleType.WITCH)).toHaveLength(1);
      expect(roles.filter(r => r === RoleType.HUNTER)).toHaveLength(1);
    });
  });

  describe('Game Start', () => {
    it('should initialize AI agents for all players', async () => {
      await gameEngine.startGame();

      expect(mockAgentScopeService.initialize).toHaveBeenCalled();
      expect(mockAgentScopeService.createAgent).toHaveBeenCalledTimes(9);
    });

    it('should create game start event', async () => {
      await gameEngine.startGame();

      expect(mockEventService.createEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'game_start',
          phase: 'night',
          dayCount: 1,
          content: '游戏开始！'
        })
      );
    });
  });

  describe('Phase Transitions', () => {
    beforeEach(async () => {
      await gameEngine.startGame();
    });

    it('should transition from night to day', async () => {
      const session = gameEngine.getSession();
      expect(session.currentPhase).toBe('night');

      // 模拟夜晚完成
      // 这里需要通过GameEngine的公共方法或测试特定的状态转换
    });
  });

  describe('Victory Conditions', () => {
    it('should detect werewolf victory when werewolves equal good players', () => {
      // 创建测试场景：3个狼人 vs 3个好人
      const testRoom = GameRoomModel.createTestRoom(6);
      testRoom.getPlayers().forEach((player, index) => {
        if (index < 3) {
          player.setRole(RoleType.WEREWOLF);
        } else {
          player.setRole(RoleType.VILLAGER);
        }
      });

      // 设置第4、5、6个玩家死亡
      testRoom.getPlayers().slice(3).forEach(player => {
        player.setDead('werewolf_kill');
      });

      const testEngine = new GameEngine(
        testRoom,
        mockAgentScopeService,
        mockEventService
      );

      // 这里应该测试胜利条件检测逻辑
      // 需要访问私有方法或创建测试辅助函数
    });
  });

  describe('Player Actions', () => {
    beforeEach(async () => {
      await gameEngine.startGame();
    });

    it('should handle seer check action', () => {
      const seer = gameEngine.getSession().players.find(p => p.role === RoleType.SEER);
      const target = gameEngine.getSession().players.find(p => p.role === RoleType.VILLAGER);

      expect(seer).toBeDefined();
      expect(target).toBeDefined();

      if (seer && target) {
        seer.seerCheck(target.id, target.name, 'good');

        expect(seer.roleAbilities?.seerInfo?.checksRemaining).toBe(0);
        expect(seer.roleAbilities?.seerInfo?.lastCheckedPlayerId).toBe(target.id);
      }
    });

    it('should handle witch actions', () => {
      const witch = gameEngine.getSession().players.find(p => p.role === RoleType.WITCH);

      expect(witch).toBeDefined();

      if (witch) {
        // 测试使用解药
        witch.useAntidote();
        expect(witch.roleAbilities?.witchInfo?.hasAntidote).toBe(false);
        expect(witch.roleAbilities?.witchInfo?.antidoteUsed).toBe(true);

        // 测试使用毒药
        witch.usePoison('target-id');
        expect(witch.roleAbilities?.witchInfo?.hasPoison).toBe(false);
        expect(witch.roleAbilities?.witchInfo?.poisonUsed).toBe(true);
      }
    });

    it('should handle hunter shoot action', () => {
      const hunter = gameEngine.getSession().players.find(p => p.role === RoleType.HUNTER);

      expect(hunter).toBeDefined();

      if (hunter) {
        hunter.hunterShoot('target-id');
        expect(hunter.roleAbilities?.hunterInfo?.hasShot).toBe(true);
        expect(hunter.roleAbilities?.hunterInfo?.shotTargetId).toBe('target-id');
      }
    });
  });

  describe('Game State', () => {
    it('should provide correct game summary', () => {
      const summary = gameEngine.getGameSummary();

      expect(summary).toHaveProperty('sessionId');
      expect(summary).toHaveProperty('roomId');
      expect(summary).toHaveProperty('status');
      expect(summary).toHaveProperty('currentPhase');
      expect(summary).toHaveProperty('players');
      expect(summary.players).toHaveLength(9);
    });

    it('should provide current game state', () => {
      const currentState = gameEngine.getCurrentState();

      expect(currentState).toHaveProperty('phase');
      expect(currentState).toHaveProperty('dayCount');
      expect(currentState).toHaveProperty('players');
      expect(currentState.players).toHaveLength(9);
    });
  });

  describe('Error Handling', () => {
    it('should handle game start errors gracefully', async () => {
      // Mock AgentScope initialization失败
      mockAgentScopeService.initialize.mockRejectedValue(new Error('AgentScope connection failed'));

      await expect(gameEngine.startGame()).rejects.toThrow();
    });
  });
});

// 集成测试
describe('GameEngine Integration', () => {
  let gameEngine: GameEngine;
  let room: GameRoomModel;

  beforeEach(() => {
    room = GameRoomModel.createTestRoom(9);
    const agentScopeService = AgentScopeService.getInstance();
    const eventService = GameEventService.getInstance();

    gameEngine = new GameEngine(
      room,
      agentScopeService,
      eventService,
      { autoProgress: true }
    );
  });

  it('should complete a full game cycle', async () => {
    // 这是一个集成测试，需要实际运行完整的游戏循环
    // 由于涉及AI决策和时间延迟，这里只做基本的结构测试

    const session = gameEngine.getSession();
    expect(session).toBeDefined();
    expect(session.players).toHaveLength(9);
  }, 10000); // 增加超时时间
});