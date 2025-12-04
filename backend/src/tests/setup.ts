import 'dotenv/config';

// 设置测试环境变量
process.env.NODE_ENV = 'test';
process.env.JWT_SECRET = 'test-secret-key';
process.env.LOG_LEVEL = 'error'; // 减少测试时的日志输出

// Mock console方法以减少测试输出
global.console = {
  ...console,
  log: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
};

// 设置测试超时
jest.setTimeout(10000);

// 全局测试工具
global.testUtils = {
  // 创建测试用的玩家
  createTestPlayer: (overrides: any = {}) => ({
    id: 'test-player-id',
    name: 'Test Player',
    roomId: 'test-room-id',
    type: 'ai' as const,
    role: undefined,
    status: 'alive' as const,
    position: 1,
    connectionState: 'active' as const,
    joinedAt: new Date(),
    lastActiveAt: new Date(),
    aiConfig: {
      agentType: 'test_agent',
      personality: 'balanced' as const,
      skillLevel: 'intermediate' as const,
      responseTime: 'normal' as const,
      strategy: 'logical' as const,
      language: 'zh' as const,
      creativityLevel: 0.5,
      aggressiveness: 0.5,
      cooperation: 0.5
    },
    agentScopeId: 'test-agent-id',
    votingWeight: 1.0,
    ...overrides
  }),

  // 创建测试用的房间
  createTestRoom: (overrides: any = {}) => ({
    id: 'test-room-id',
    creatorId: 'test-creator-id',
    maxPlayers: 9,
    currentPlayers: 0,
    status: 'waiting' as const,
    gameConfig: {
      roleDistribution: {
        werewolf: 3,
        villager: 3,
        seer: 1,
        witch: 1,
        hunter: 1
      },
      phaseDurations: {
        night: 30,
        sheriffElection: 120,
        dayDiscussion: 180,
        voting: 60
      },
      aiConfigurations: [],
      maxPlayers: 9,
      gameMode: 'classic' as const
    },
    createdAt: new Date(),
    ...overrides
  }),

  // 等待指定时间
  delay: (ms: number) => new Promise(resolve => setTimeout(resolve, ms)),

  // 生成随机字符串
  randomString: (length: number = 10) => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  }
};

// 在所有测试后清理
afterAll(() => {
  // 清理资源
});