import winston from 'winston';
import path from 'path';

// 日志级别
const levels = {
  error: 0,
  warn: 1,
  info: 2,
  http: 3,
  debug: 4,
};

// 日志颜色
const colors = {
  error: 'red',
  warn: 'yellow',
  info: 'green',
  http: 'magenta',
  debug: 'white',
};

// 添加颜色到winston
winston.addColors(colors);

// 日志格式
const format = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss:ms' }),
  winston.format.colorize({ all: true }),
  winston.format.printf(
    (info) => `${info.timestamp} ${info.level}: ${info.message}`,
  ),
);

// 文件格式（不包含颜色）
const fileFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss:ms' }),
  winston.format.errors({ stack: true }),
  winston.format.json(),
);

// 传输器配置
const transports = [
  // 控制台输出
  new winston.transports.Console({
    format,
  }),

  // 错误日志文件
  new winston.transports.File({
    filename: 'logs/error.log',
    level: 'error',
    format: fileFormat,
    maxsize: 5242880, // 5MB
    maxFiles: 5,
  }),

  // 所有日志文件
  new winston.transports.File({
    filename: 'logs/combined.log',
    format: fileFormat,
    maxsize: 5242880, // 5MB
    maxFiles: 5,
  }),
];

// 创建logger实例
export const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  levels,
  format: fileFormat,
  transports,
  exitOnError: false,
});

// 开发环境下的额外配置
if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.combine(
      winston.format.colorize(),
      winston.format.simple()
    )
  }));
}

// 创建HTTP请求日志流
export const httpLogStream = {
  write: (message: string) => {
    logger.http(message.trim());
  },
};

// 游戏专用日志
export const gameLogger = {
  // 游戏开始
  gameStart: (sessionId: string, roomId: string, playerCount: number) => {
    logger.info(`Game Started - Session: ${sessionId}, Room: ${roomId}, Players: ${playerCount}`);
  },

  // 游戏结束
  gameEnd: (sessionId: string, winner: string, duration: number) => {
    logger.info(`Game Ended - Session: ${sessionId}, Winner: ${winner}, Duration: ${duration}s`);
  },

  // 阶段变化
  phaseChange: (sessionId: string, from: string, to: string, dayCount: number) => {
    logger.info(`Phase Change - Session: ${sessionId}, ${from} -> ${to}, Day: ${dayCount}`);
  },

  // 玩家行动
  playerAction: (sessionId: string, playerId: string, action: string, target?: string) => {
    logger.info(`Player Action - Session: ${sessionId}, Player: ${playerId}, Action: ${action}${target ? `, Target: ${target}` : ''}`);
  },

  // 角色技能使用
  roleAbility: (sessionId: string, playerId: string, role: string, ability: string, success: boolean) => {
    logger.info(`Role Ability - Session: ${sessionId}, Player: ${playerId}, Role: ${role}, Ability: ${ability}, Success: ${success}`);
  },

  // 投票
  voting: (sessionId: string, votingType: string, target: string, result: string) => {
    logger.info(`Voting - Session: ${sessionId}, Type: ${votingType}, Target: ${target}, Result: ${result}`);
  },

  // AI代理
  aiAgent: (agentId: string, action: string, processingTime: number, success: boolean) => {
    logger.info(`AI Agent - Agent: ${agentId}, Action: ${action}, Time: ${processingTime}ms, Success: ${success}`);
  },

  // WebSocket连接
  wsConnection: (type: 'connect' | 'disconnect', connectionId: string, playerId?: string) => {
    logger.info(`WebSocket ${type} - Connection: ${connectionId}${playerId ? `, Player: ${playerId}` : ''}`);
  },

  // 错误
  error: (message: string, error?: Error, context?: any) => {
    logger.error(`${message}${error ? ` - Error: ${error.message}` : ''}`, { error, context });
  },

  // 警告
  warn: (message: string, context?: any) => {
    logger.warn(message, context);
  },

  // 调试
  debug: (message: string, context?: any) => {
    logger.debug(message, context);
  }
};

// 性能监控日志
export const performanceLogger = {
  // 数据库查询
  dbQuery: (query: string, duration: number, success: boolean) => {
    logger.debug(`DB Query - Query: ${query.substring(0, 100)}..., Duration: ${duration}ms, Success: ${success}`);
  },

  // API请求
  apiRequest: (method: string, path: string, statusCode: number, duration: number) => {
    logger.http(`API Request - ${method} ${path}, Status: ${statusCode}, Duration: ${duration}ms`);
  },

  // 内存使用
  memoryUsage: (type: string, usage: NodeJS.MemoryUsage) => {
    logger.debug(`Memory Usage - ${type}: RSS: ${Math.round(usage.rss / 1024 / 1024)}MB, Heap: ${Math.round(usage.heapUsed / 1024 / 1024)}MB`);
  },

  // 系统负载
  systemLoad: (cpuUsage: number, memoryUsage: number) => {
    logger.info(`System Load - CPU: ${cpuUsage}%, Memory: ${memoryUsage}%`);
  }
};

// AgentScope专用日志
export const agentScopeLogger = {
  // 代理创建
  agentCreated: (agentId: string, agentType: string, playerName: string, role: string) => {
    logger.info(`AgentScope - Agent Created: ${agentId}, Type: ${agentType}, Player: ${playerName}, Role: ${role}`);
  },

  // 消息发送
  messageSent: (agentId: string, messageType: string, processingTime: number) => {
    logger.debug(`AgentScope - Message Sent: ${agentId}, Type: ${messageType}, Time: ${processingTime}ms`);
  },

  // 消息接收
  messageReceived: (agentId: string, messageType: string, success: boolean) => {
    logger.debug(`AgentScope - Message Received: ${agentId}, Type: ${messageType}, Success: ${success}`);
  },

  // 错误
  error: (agentId: string, error: string, context?: any) => {
    logger.error(`AgentScope Error - Agent: ${agentId}, Error: ${error}`, context);
  }
};

// 安全日志
export const securityLogger = {
  // 认证
  auth: (type: 'success' | 'failure', userId: string, ip: string, userAgent?: string) => {
    logger.info(`Auth ${type} - User: ${userId}, IP: ${ip}, UA: ${userAgent || 'Unknown'}`);
  },

  // 权限检查
  permission: (type: 'granted' | 'denied', userId: string, resource: string, action: string) => {
    logger.info(`Permission ${type} - User: ${userId}, Resource: ${resource}, Action: ${action}`);
  },

  // 速率限制
  rateLimit: (ip: string, endpoint: string, limit: number, current: number) => {
    logger.warn(`Rate Limit Exceeded - IP: ${ip}, Endpoint: ${endpoint}, Limit: ${limit}, Current: ${current}`);
  },

  // 可疑活动
  suspicious: (type: string, details: any) => {
    logger.warn(`Suspicious Activity - Type: ${type}, Details: ${details}`);
  }
};

// 导出默认logger
export default logger;