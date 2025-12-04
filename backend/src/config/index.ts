import dotenv from 'dotenv';

dotenv.config();

export const config = {
  server: {
    port: parseInt(process.env.PORT || '3001'),
    host: process.env.HOST || '0.0.0.0'
  },

  cors: {
    origin: (process.env.CORS_ORIGIN || 'http://localhost:3000,http://localhost:3001').split(','),
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
  },

  database: {
    url: process.env.DATABASE_URL || 'postgresql://username:password@localhost:5432/werewolf',
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
    name: process.env.DB_NAME || 'werewolf',
    user: process.env.DB_USER || 'username',
    password: process.env.DB_PASSWORD || 'password',
    pool: {
      min: parseInt(process.env.DB_POOL_MIN || '2'),
      max: parseInt(process.env.DB_POOL_MAX || '10'),
      idleTimeoutMillis: parseInt(process.env.DB_IDLE_TIMEOUT || '30000'),
      connectionTimeoutMillis: parseInt(process.env.DB_CONNECTION_TIMEOUT || '2000')
    }
  },

  redis: {
    url: process.env.REDIS_URL || 'redis://localhost:6379',
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT || '6379'),
    password: process.env.REDIS_PASSWORD || undefined,
    keyPrefix: process.env.REDIS_KEY_PREFIX || 'werewolf:',
    retryDelayOnFailover: parseInt(process.env.REDIS_RETRY_DELAY || '100'),
    maxRetriesPerRequest: parseInt(process.env.REDIS_MAX_RETRIES || '3')
  },

  agentscope: {
    apiKey: process.env.AGENTSCOPE_API_KEY || '',
    baseUrl: process.env.AGENTSCOPE_BASE_URL || 'http://localhost:8080',
    timeout: parseInt(process.env.AGENTSCOPE_TIMEOUT || '30000'),
    maxRetries: parseInt(process.env.AGENTSCOPE_MAX_RETRIES || '3'),
    retryDelay: parseInt(process.env.AGENTSCOPE_RETRY_DELAY || '1000')
  },

  game: {
    maxDuration: parseInt(process.env.GAME_DURATION_LIMIT || '3600'), // 1小时
    maxConcurrentGames: parseInt(process.env.MAX_CONCURRENT_GAMES || '100'),
    maxPlayersPerGame: parseInt(process.env.MAX_PLAYERS_PER_GAME || '9'),
    aiResponseDelay: {
      min: parseInt(process.env.AI_RESPONSE_DELAY_MIN || '500'),
      max: parseInt(process.env.AI_RESPONSE_DELAY_MAX || '20000')
    },
    phaseTimeouts: {
      night: parseInt(process.env.PHASE_TIMEOUT_NIGHT || '30'),
      sheriffElection: parseInt(process.env.PHASE_TIMEOUT_SHERIFF_ELECTION || '120'),
      dayDiscussion: parseInt(process.env.PHASE_TIMEOUT_DAY_DISCUSSION || '180'),
      voting: parseInt(process.env.PHASE_TIMEOUT_VOTING || '60')
    }
  },

  ai: {
    openaiApiKey: process.env.OPENAI_API_KEY || '',
    claudeApiKey: process.env.CLAUDE_API_KEY || '',
    defaultTimeout: parseInt(process.env.AI_DEFAULT_TIMEOUT || '20000'),
    maxConcurrency: parseInt(process.env.AI_MAX_CONCURRENCY || '5'),
    defaultModel: process.env.AI_DEFAULT_MODEL || 'gpt-3.5-turbo',
    defaultTemperature: parseFloat(process.env.AI_DEFAULT_TEMPERATURE || '0.7'),
    defaultMaxTokens: parseInt(process.env.AI_DEFAULT_MAX_TOKENS || '500')
  },

  jwt: {
    secret: process.env.JWT_SECRET || 'your-secret-key',
    expiresIn: process.env.JWT_EXPIRES_IN || '24h',
    issuer: process.env.JWT_ISSUER || 'werewolf-server',
    audience: process.env.JWT_AUDIENCE || 'werewolf-client'
  },

  logging: {
    level: process.env.LOG_LEVEL || 'info',
    file: process.env.LOG_FILE || 'logs/app.log',
    maxSize: process.env.LOG_MAX_SIZE || '10m',
    maxFiles: parseInt(process.env.LOG_MAX_FILES || '5'),
    datePattern: process.env.LOG_DATE_PATTERN || 'YYYY-MM-DD'
  },

  security: {
    rateLimitWindow: parseInt(process.env.RATE_LIMIT_WINDOW || '15'), // 分钟
    rateLimitMax: parseInt(process.env.RATE_LIMIT_MAX || '100'),
    helmetEnabled: process.env.ENABLE_HELMET !== 'false',
    corsEnabled: process.env.ENABLE_CORS !== 'false'
  },

  development: {
    enableSwagger: process.env.ENABLE_SWAGGER === 'true',
    enablePlayground: process.env.ENABLE_PLAYGROUND === 'true',
    enableDebugRoutes: process.env.ENABLE_DEBUG_ROUTES === 'true',
    mockAgents: process.env.MOCK_AGENTS === 'true'
  },

  monitoring: {
    enableMetrics: process.env.ENABLE_METRICS !== 'false',
    metricsInterval: parseInt(process.env.METRICS_INTERVAL || '30000'),
    enableHealthChecks: process.env.ENABLE_HEALTH_CHECKS !== 'false',
    healthCheckInterval: parseInt(process.env.HEALTH_CHECK_INTERVAL || '60000')
  },

  websocket: {
    pingTimeout: parseInt(process.env.WS_PING_TIMEOUT || '60000'),
    pingInterval: parseInt(process.env.WS_PING_INTERVAL || '25000'),
    maxConnections: parseInt(process.env.WS_MAX_CONNECTIONS || '1000'),
    transports: (process.env.WS_TRANSPORTS || 'websocket,polling').split(',')
  }
};

// 验证必需的配置
export function validateConfig(): void {
  const requiredVars = [
    'JWT_SECRET'
  ];

  const missingVars = requiredVars.filter(varName => !process.env[varName]);

  if (missingVars.length > 0) {
    throw new Error(`Missing required environment variables: ${missingVars.join(', ')}`);
  }

  // 验证数值配置
  if (config.server.port < 1 || config.server.port > 65535) {
    throw new Error('Invalid server port');
  }

  if (config.game.maxPlayersPerGame < 4 || config.game.maxPlayersPerGame > 20) {
    throw new Error('Invalid max players per game');
  }

  if (config.ai.defaultTemperature < 0 || config.ai.defaultTemperature > 2) {
    throw new Error('Invalid AI temperature');
  }
}

// 获取配置摘要
export function getConfigSummary(): any {
  return {
    server: {
      port: config.server.port,
      environment: process.env.NODE_ENV || 'development'
    },
    database: {
      host: config.database.host,
      port: config.database.port,
      name: config.database.name,
      connected: !!config.database.url
    },
    redis: {
      host: config.redis.host,
      port: config.redis.port,
      connected: !!config.redis.url
    },
    agentscope: {
      baseUrl: config.agentscope.baseUrl,
      configured: !!config.agentscope.apiKey
    },
    game: {
      maxConcurrentGames: config.game.maxConcurrentGames,
      maxPlayersPerGame: config.game.maxPlayersPerGame
    },
    features: {
      mockAgents: config.development.mockAgents,
      enableSwagger: config.development.enableSwagger,
      enableMetrics: config.monitoring.enableMetrics
    }
  };
}

export default config;