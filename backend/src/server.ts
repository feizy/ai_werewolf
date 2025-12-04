import express from 'express';
import { createServer } from 'http';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import dotenv from 'dotenv';
import { logger, gameLogger, performanceLogger } from '@/utils/logger';
import { WebSocketService } from '@/services/WebSocketService';
import { AgentScopeService } from '@/services/AgentScopeService';
import { GameEventService } from '@/services/GameEventService';
import { config } from '@/config';

// 加载环境变量
dotenv.config();

class WerewolfServer {
  private app: express.Application;
  private server: any;
  private wsService: WebSocketService;
  private agentScopeService: AgentScopeService;
  private eventService: GameEventService;
  private isShuttingDown: boolean = false;

  constructor() {
    this.app = express();
    this.server = createServer(this.app);
    this.setupMiddleware();
    this.setupRoutes();
    this.setupErrorHandling();
  }

  private setupMiddleware(): void {
    // 安全中间件
    this.app.use(helmet({
      contentSecurityPolicy: false, // WebSocket需要
      crossOriginEmbedderPolicy: false
    }));

    // CORS配置
    this.app.use(cors({
      origin: config.cors.origin,
      methods: ['GET', 'POST', 'PUT', 'DELETE'],
      credentials: true,
      optionsSuccessStatus: 200
    }));

    // 压缩中间件
    this.app.use(compression());

    // 请求解析
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true, limit: '10mb' }));

    // 请求日志
    this.app.use((req, res, next) => {
      const startTime = Date.now();

      res.on('finish', () => {
        const duration = Date.now() - startTime;
        performanceLogger.apiRequest(req.method, req.path, res.statusCode, duration);
      });

      next();
    });

    // 健康检查端点
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        memory: process.memoryUsage(),
        version: process.env.npm_package_version || '1.0.0'
      });
    });

    logger.info('Middleware configured');
  }

  private setupRoutes(): void {
    // API路由前缀
    const apiRouter = express.Router();

    // 房间管理API
    apiRouter.get('/rooms', this.getRooms.bind(this));
    apiRouter.get('/rooms/:roomId', this.getRoom.bind(this));
    apiRouter.post('/rooms', this.createRoom.bind(this));

    // 游戏管理API
    apiRouter.get('/games/:gameId', this.getGame.bind(this));
    apiRouter.get('/games/:gameId/state', this.getGameState.bind(this));
    apiRouter.post('/games/:gameId/replay', this.accessReplay.bind(this));

    // 系统状态API
    apiRouter.get('/status', this.getSystemStatus.bind(this));
    apiRouter.get('/metrics', this.getMetrics.bind(this));

    // 回放系统API
    apiRouter.get('/replays/:gameId/days', this.getReplayDays.bind(this));
    apiRouter.get('/replays/:gameId/day/:dayNumber', this.getReplayDay.bind(this));
    apiRouter.get('/replays/:gameId/events', this.getReplayEvents.bind(this));

    this.app.use('/api', apiRouter);

    logger.info('API routes configured');
  }

  private setupErrorHandling(): void {
    // 404处理
    this.app.use('*', (req, res) => {
      res.status(404).json({
        error: 'Not Found',
        message: `Route ${req.method} ${req.originalUrl} not found`,
        timestamp: new Date().toISOString()
      });
    });

    // 全局错误处理
    this.app.use((error: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
      logger.error('Unhandled error:', error);

      res.status(error.status || 500).json({
        error: error.name || 'Internal Server Error',
        message: error.message || 'An unexpected error occurred',
        timestamp: new Date().toISOString(),
        ...(process.env.NODE_ENV === 'development' && { stack: error.stack })
      });
    });

    // 未捕获的异常处理
    process.on('uncaughtException', (error) => {
      logger.error('Uncaught Exception:', error);
      this.gracefulShutdown('SIGTERM');
    });

    process.on('unhandledRejection', (reason, promise) => {
      logger.error('Unhandled Rejection at:', promise, 'reason:', reason);
    });

    // 优雅关闭信号处理
    process.on('SIGTERM', () => this.gracefulShutdown('SIGTERM'));
    process.on('SIGINT', () => this.gracefulShutdown('SIGINT'));

    logger.info('Error handling configured');
  }

  // API处理方法
  private async getRooms(req: express.Request, res: express.Response): Promise<void> {
    try {
      // 这里应该从数据库获取房间列表
      // 暂时返回模拟数据
      res.json({
        rooms: [],
        total: 0,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      logger.error('Error getting rooms:', error);
      res.status(500).json({ error: 'Failed to get rooms' });
    }
  }

  private async getRoom(req: express.Request, res: express.Response): Promise<void> {
    try {
      const { roomId } = req.params;

      // 这里应该从数据库获取房间信息
      res.json({
        roomId,
        status: 'not_found',
        message: 'Room not found'
      });
    } catch (error) {
      logger.error('Error getting room:', error);
      res.status(500).json({ error: 'Failed to get room' });
    }
  }

  private async createRoom(req: express.Request, res: express.Response): Promise<void> {
    try {
      const { playerName, roomName } = req.body;

      if (!playerName) {
        return res.status(400).json({ error: 'Player name is required' });
      }

      // 这里应该创建房间并保存到数据库
      res.json({
        message: 'Room created successfully',
        roomId: 'mock-room-id',
        playerId: 'mock-player-id'
      });
    } catch (error) {
      logger.error('Error creating room:', error);
      res.status(500).json({ error: 'Failed to create room' });
    }
  }

  private async getGame(req: express.Request, res: express.Response): Promise<void> {
    try {
      const { gameId } = req.params;

      // 这里应该从数据库获取游戏信息
      res.json({
        gameId,
        status: 'not_found',
        message: 'Game not found'
      });
    } catch (error) {
      logger.error('Error getting game:', error);
      res.status(500).json({ error: 'Failed to get game' });
    }
  }

  private async getGameState(req: express.Request, res: express.Response): Promise<void> {
    try {
      const { gameId } = req.params;

      // 这里应该从游戏引擎获取当前状态
      res.json({
        gameId,
        phase: 'waiting',
        dayCount: 0,
        players: [],
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      logger.error('Error getting game state:', error);
      res.status(500).json({ error: 'Failed to get game state' });
    }
  }

  private async accessReplay(req: express.Request, res: express.Response): Promise<void> {
    try {
      const { gameId } = req.params;

      // 这里应该访问回放系统
      res.json({
        gameId,
        canReplay: false,
        message: 'Replay not available'
      });
    } catch (error) {
      logger.error('Error accessing replay:', error);
      res.status(500).json({ error: 'Failed to access replay' });
    }
  }

  private async getSystemStatus(req: express.Request, res: express.Response): Promise<void> {
    try {
      const status = {
        server: {
          status: 'healthy',
          uptime: process.uptime(),
          version: process.env.npm_package_version || '1.0.0',
          environment: process.env.NODE_ENV || 'development'
        },
        websocket: this.wsService?.getServiceStatus() || { connectedClients: 0, activeRooms: 0, activeGames: 0 },
        agentscope: this.agentScopeService?.healthCheck() || { status: 'not_initialized' },
        memory: process.memoryUsage(),
        timestamp: new Date().toISOString()
      };

      res.json(status);
    } catch (error) {
      logger.error('Error getting system status:', error);
      res.status(500).json({ error: 'Failed to get system status' });
    }
  }

  private async getMetrics(req: express.Request, res: express.Response): Promise<void> {
    try {
      const metrics = {
        performance: {
          uptime: process.uptime(),
          memoryUsage: process.memoryUsage(),
          cpuUsage: process.cpuUsage()
        },
        services: {
          websocket: this.wsService?.getServiceStatus(),
          agentscope: this.agentScopeService?.healthCheck(),
          eventService: this.eventService?.getServiceStatus()
        },
        timestamp: new Date().toISOString()
      };

      res.json(metrics);
    } catch (error) {
      logger.error('Error getting metrics:', error);
      res.status(500).json({ error: 'Failed to get metrics' });
    }
  }

  private async getReplayDays(req: express.Request, res: express.Response): Promise<void> {
    try {
      const { gameId } = req.params;

      // 这里应该获取回放天数列表
      res.json({
        gameId,
        days: [],
        totalDays: 0
      });
    } catch (error) {
      logger.error('Error getting replay days:', error);
      res.status(500).json({ error: 'Failed to get replay days' });
    }
  }

  private async getReplayDay(req: express.Request, res: express.Response): Promise<void> {
    try {
      const { gameId, dayNumber } = req.params;

      // 这里应该获取指定天的回放数据
      res.json({
        gameId,
        dayNumber: parseInt(dayNumber),
        playerStates: [],
        gameState: {},
        events: []
      });
    } catch (error) {
      logger.error('Error getting replay day:', error);
      res.status(500).json({ error: 'Failed to get replay day' });
    }
  }

  private async getReplayEvents(req: express.Request, res: express.Response): Promise<void> {
    try {
      const { gameId } = req.params;
      const { fromDay, toDay } = req.query;

      // 这里应该获取事件列表
      res.json({
        gameId,
        events: [],
        total: 0
      });
    } catch (error) {
      logger.error('Error getting replay events:', error);
      res.status(500).json({ error: 'Failed to get replay events' });
    }
  }

  // 启动服务器
  public async start(): Promise<void> {
    try {
      // 初始化服务
      await this.initializeServices();

      // 启动HTTP服务器
      const port = config.server.port || 3001;
      this.server.listen(port, () => {
        logger.info(`Werewolf Game Server started on port ${port}`);
        logger.info(`Environment: ${process.env.NODE_ENV || 'development'}`);
        logger.info(`WebSocket service available`);
        logger.info(`API documentation: http://localhost:${port}/api/status`);
      });

      // 启动性能监控
      this.startPerformanceMonitoring();

    } catch (error) {
      logger.error('Failed to start server:', error);
      process.exit(1);
    }
  }

  // 初始化服务
  private async initializeServices(): Promise<void> {
    logger.info('Initializing services...');

    try {
      // 初始化AgentScope服务
      this.agentScopeService = AgentScopeService.getInstance();
      await this.agentScopeService.initialize();

      // 初始化事件服务
      this.eventService = GameEventService.getInstance();

      // 初始化WebSocket服务
      this.wsService = WebSocketService.getInstance(this.server, {
        cors: {
          origin: config.cors.origin,
          methods: ['GET', 'POST']
        },
        pingTimeout: 60000,
        pingInterval: 25000
      });

      logger.info('All services initialized successfully');
    } catch (error) {
      logger.error('Failed to initialize services:', error);
      throw error;
    }
  }

  // 启动性能监控
  private startPerformanceMonitoring(): void {
    setInterval(() => {
      const memUsage = process.memoryUsage();
      performanceLogger.memoryUsage('server', memUsage);

      // 检查内存使用率
      const heapUsedMB = memUsage.heapUsed / 1024 / 1024;
      if (heapUsedMB > 500) { // 超过500MB时警告
        logger.warn(`High memory usage: ${heapUsedMB.toFixed(2)}MB`);
      }
    }, 30000); // 每30秒检查一次

    logger.info('Performance monitoring started');
  }

  // 优雅关闭
  private async gracefulShutdown(signal: string): Promise<void> {
    if (this.isShuttingDown) {
      logger.info('Shutdown already in progress');
      return;
    }

    this.isShuttingDown = true;
    logger.info(`Received ${signal}, starting graceful shutdown...`);

    try {
      // 停止接受新连接
      this.server.close(async () => {
        logger.info('HTTP server closed');

        try {
          // 清理WebSocket服务
          if (this.wsService) {
            await this.wsService.cleanup();
          }

          // 清理AgentScope服务
          if (this.agentScopeService) {
            await this.agentScopeService.shutdown();
          }

          // 清理事件服务
          if (this.eventService) {
            this.eventService.cleanupExpiredData();
          }

          logger.info('All services cleaned up');
          process.exit(0);
        } catch (error) {
          logger.error('Error during cleanup:', error);
          process.exit(1);
        }
      });

      // 强制关闭超时
      setTimeout(() => {
        logger.error('Forced shutdown due to timeout');
        process.exit(1);
      }, 10000); // 10秒超时

    } catch (error) {
      logger.error('Error during graceful shutdown:', error);
      process.exit(1);
    }
  }
}

// 创建并启动服务器
const server = new WerewolfServer();
server.start().catch((error) => {
  logger.error('Failed to start server:', error);
  process.exit(1);
});