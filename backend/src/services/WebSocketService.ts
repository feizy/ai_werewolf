import { Server as SocketIOServer } from 'socket.io';
import { Server as HTTPServer } from 'http';
import { Server as HTTPSServer } from 'https';
import jwt from 'jsonwebtoken';
import { logger, wsConnection, gameLogger } from '@/utils/logger';
import { GameRoomModel } from '@/models/GameRoom';
import { GameEngine } from './GameEngine';
import { AgentScopeService } from './AgentScopeService';
import { GameEventService } from './GameEventService';
import {
  WSMessage,
  CreateRoomRequest,
  JoinRoomRequest,
  StartGameRequest,
  // 添加其他消息类型...
} from '@/types/websocket';
import { ErrorCode } from '@/types/websocket';

export interface WebSocketConfig {
  cors?: {
    origin: string[];
    methods: string[];
  };
  pingTimeout: number;
  pingInterval: number;
  transports: string[];
  allowEIO3: boolean;
}

export interface ConnectedClient {
  socketId: string;
  playerId?: string;
  roomId?: string;
  joinedAt: Date;
  lastActive: Date;
  userAgent?: string;
  ip: string;
}

export class WebSocketService {
  private static instance: WebSocketService;
  private io: SocketIOServer;
  private connectedClients: Map<string, ConnectedClient> = new Map();
  private gameRooms: Map<string, GameRoomModel> = new Map();
  private gameEngines: Map<string, GameEngine> = new Map();
  private agentScopeService: AgentScopeService;
  private eventService: GameEventService;

  private constructor(
    private server: HTTPServer | HTTPSServer,
    private config?: WebSocketConfig
  ) {
    this.io = new SocketIOServer(server, {
      cors: {
        origin: config?.cors?.origin || ['http://localhost:3000', 'http://localhost:3001'],
        methods: config?.cors?.methods || ['GET', 'POST'],
        credentials: true
      },
      pingTimeout: config?.pingTimeout || 60000,
      pingInterval: config?.pingInterval || 25000,
      transports: config?.transports || ['websocket', 'polling'],
      allowEIO3: config?.allowEIO3 || true
    });

    this.agentScopeService = AgentScopeService.getInstance();
    this.eventService = GameEventService.getInstance();

    this.setupEventHandlers();
  }

  public static getInstance(
    server: HTTPServer | HTTPSServer,
    config?: WebSocketConfig
  ): WebSocketService {
    if (!WebSocketService.instance) {
      WebSocketService.instance = new WebSocketService(server, config);
    }
    return WebSocketService.instance;
  }

  private setupEventHandlers(): void {
    this.io.on('connection', (socket) => {
      this.handleConnection(socket);
    });

    logger.info('WebSocket service initialized');
  }

  private handleConnection(socket: any): void {
    const clientInfo: ConnectedClient = {
      socketId: socket.id,
      joinedAt: new Date(),
      lastActive: new Date(),
      ip: socket.handshake.address,
      userAgent: socket.handshake.headers['user-agent']
    };

    this.connectedClients.set(socket.id, clientInfo);
    wsConnection('connect', socket.id);

    logger.info(`Client connected: ${socket.id} from ${clientInfo.ip}`);

    // 发送连接确认
    this.sendToSocket(socket, 'connection_established', {
      connectionId: socket.id,
      timestamp: new Date(),
      serverTime: new Date()
    });

    // 设置事件处理器
    this.setupSocketEventHandlers(socket);

    // 处理断开连接
    socket.on('disconnect', (reason: string) => {
      this.handleDisconnection(socket, reason);
    });

    // 处理错误
    socket.on('error', (error: Error) => {
      logger.error(`Socket error for ${socket.id}:`, error);
    });
  }

  private setupSocketEventHandlers(socket: any): void {
    // 房间管理
    socket.on('create_room', (data: CreateRoomRequest) => {
      this.handleCreateRoom(socket, data);
    });

    socket.on('join_room', (data: JoinRoomRequest) => {
      this.handleJoinRoom(socket, data);
    });

    socket.on('leave_room', () => {
      this.handleLeaveRoom(socket);
    });

    // 游戏控制
    socket.on('start_game', (data: StartGameRequest) => {
      this.handleStartGame(socket, data);
    });

    // 心跳
    socket.on('heartbeat', (data) => {
      this.handleHeartbeat(socket, data);
    });

    // 重连
    socket.on('reconnect', (data) => {
      this.handleReconnect(socket, data);
    });
  }

  // 创建房间
  private async handleCreateRoom(socket: any, data: CreateRoomRequest): Promise<void> {
    try {
      const { playerName, roomName } = data.payload;

      // 验证玩家名称
      if (!playerName || playerName.trim().length === 0 || playerName.length > 20) {
        this.sendError(socket, 'INVALID_PLAYER_NAME', 'Player name is required and must be 1-20 characters');
        return;
      }

      // 创建房间
      const room = GameRoomModel.createRoom(
        `creator-${socket.id}`,
        playerName.trim(),
        roomName?.trim()
      );

      // 存储房间
      this.gameRooms.set(room.id, room);

      // 更新客户端信息
      const clientInfo = this.connectedClients.get(socket.id);
      if (clientInfo) {
        clientInfo.playerId = room.creatorId;
        clientInfo.roomId = room.id;
      }

      // 加入Socket.IO房间
      socket.join(room.id);

      // 发送响应
      this.sendToSocket(socket, 'room_created', {
        roomId: room.id,
        playerId: room.creatorId,
        roomName: room.name,
        creatorId: room.creatorId
      });

      logger.info(`Room created: ${room.id} by ${playerName}`);
    } catch (error) {
      logger.error('Error creating room:', error);
      this.sendError(socket, 'INTERNAL_ERROR', 'Failed to create room');
    }
  }

  // 加入房间
  private async handleJoinRoom(socket: any, data: JoinRoomRequest): Promise<void> {
    try {
      const { roomId, playerName } = data.payload;

      // 验证输入
      if (!roomId || !playerName || playerName.trim().length === 0 || playerName.length > 20) {
        this.sendError(socket, 'INVALID_PLAYER_NAME', 'Invalid room ID or player name');
        return;
      }

      // 查找房间
      const room = this.gameRooms.get(roomId);
      if (!room) {
        this.sendError(socket, 'ROOM_NOT_FOUND', 'Room not found');
        return;
      }

      // 检查房间是否已满
      if (room.isFull()) {
        this.sendError(socket, 'ROOM_FULL', 'Room is full');
        return;
      }

      // 检查房间状态
      if (room.status !== 'waiting') {
        this.sendError(socket, 'GAME_NOT_STARTED', 'Game is already in progress');
        return;
      }

      // 创建新玩家
      const player = PlayerModel.createAIPlayer(
        playerName.trim(),
        roomId,
        room.currentPlayers + 1
      );

      // 添加到房间
      if (!room.addPlayer(player)) {
        this.sendError(socket, 'ROOM_FULL', 'Failed to join room');
        return;
      }

      // 更新客户端信息
      const clientInfo = this.connectedClients.get(socket.id);
      if (clientInfo) {
        clientInfo.playerId = player.id;
        clientInfo.roomId = roomId;
      }

      // 加入Socket.IO房间
      socket.join(roomId);

      // 发送给加入者
      this.sendToSocket(socket, 'room_joined', {
        roomId: room.id,
        playerId: player.id,
        roomInfo: {
          name: room.name,
          creatorName: room.getPlayer(room.creatorId)?.name || 'Unknown',
          currentPlayers: room.currentPlayers,
          maxPlayers: room.maxPlayers
        },
        players: room.getPlayersInfo()
      });

      // 广播给房间内其他玩家
      this.broadcastToRoom(roomId, 'player_joined', {
        playerId: player.id,
        playerName: player.name,
        playerCount: room.currentPlayers,
        players: room.getPlayersInfo()
      }, socket.id);

      logger.info(`Player ${playerName} joined room ${roomId}`);
    } catch (error) {
      logger.error('Error joining room:', error);
      this.sendError(socket, 'INTERNAL_ERROR', 'Failed to join room');
    }
  }

  // 开始游戏
  private async handleStartGame(socket: any, data: StartGameRequest): Promise<void> {
    try {
      const { playerId } = data.payload;
      const clientInfo = this.connectedClients.get(socket.id);

      if (!clientInfo || clientInfo.playerId !== playerId) {
        this.sendError(socket, 'INSUFFICIENT_PERMISSIONS', 'Invalid player ID');
        return;
      }

      const room = this.gameRooms.get(clientInfo.roomId!);
      if (!room) {
        this.sendError(socket, 'ROOM_NOT_FOUND', 'Room not found');
        return;
      }

      // 检查是否是房主
      if (room.creatorId !== playerId) {
        this.sendError(socket, 'INSUFFICIENT_PERMISSIONS', 'Only room creator can start the game');
        return;
      }

      // 检查房间状态
      if (!room.canStartGame()) {
        this.sendError(socket, 'GAME_NOT_STARTED', 'Cannot start game: room not ready');
        return;
      }

      // 开始游戏
      room.startGame();

      // 创建游戏引擎
      const gameEngine = new GameEngine(
        room,
        this.agentScopeService,
        this.eventService
      );

      this.gameEngines.set(room.id, gameEngine);

      // 启动游戏
      await gameEngine.startGame();

      // 获取玩家信息
      const gamePlayers = room.getPlayers().map(p => ({
        playerId: p.id,
        playerName: p.name,
        type: 'ai' as const,
        role: p.role!,
        status: p.isAlive() ? 'alive' as const : 'dead' as const,
        votingWeight: p.votingWeight
      }));

      // 广播游戏开始
      this.broadcastToRoom(room.id, 'game_started', {
        gameId: gameEngine.getSession().id,
        players: gamePlayers,
        initialPhase: 'night',
        dayCount: 1
      });

      gameLogger.gameStart(gameEngine.getSession().id, room.id, room.currentPlayers);

      logger.info(`Game started in room ${room.id}`);
    } catch (error) {
      logger.error('Error starting game:', error);
      this.sendError(socket, 'INTERNAL_ERROR', 'Failed to start game');
    }
  }

  // 处理心跳
  private handleHeartbeat(socket: any, data: any): void {
    const clientInfo = this.connectedClients.get(socket.id);
    if (clientInfo) {
      clientInfo.lastActive = new Date();
    }

    this.sendToSocket(socket, 'heartbeat_response', {
      timestamp: new Date(),
      serverTime: new Date()
    });
  }

  // 处理重连
  private async handleReconnect(socket: any, data: any): Promise<void> {
    try {
      const { playerId, roomId, lastEventId } = data.payload;

      // 验证房间和玩家
      const room = this.gameRooms.get(roomId);
      if (!room) {
        this.sendError(socket, 'ROOM_NOT_FOUND', 'Room not found');
        return;
      }

      const player = room.getPlayer(playerId);
      if (!player) {
        this.sendError(socket, 'INVALID_PLAYER_NAME', 'Player not found in room');
        return;
      }

      // 更新客户端信息
      const clientInfo = this.connectedClients.get(socket.id);
      if (clientInfo) {
        clientInfo.playerId = playerId;
        clientInfo.roomId = roomId;
      }

      // 重新加入Socket.IO房间
      socket.join(roomId);

      // 获取错过的事件
      const missedEvents = this.eventService.getEventsAfter(
        this.gameEngines.get(roomId)?.getSession().id || '',
        new Date()
      );

      const currentGameState = this.gameEngines.get(roomId)?.getCurrentState();

      this.sendToSocket(socket, 'reconnect_response', {
        success: true,
        missedEvents: missedEvents.slice(0, 10), // 限制返回的事件数量
        currentGameState
      });

      logger.info(`Player ${playerId} reconnected to room ${roomId}`);
    } catch (error) {
      logger.error('Error handling reconnect:', error);
      this.sendError(socket, 'INTERNAL_ERROR', 'Failed to reconnect');
    }
  }

  // 处理离开房间
  private handleLeaveRoom(socket: any): void {
    const clientInfo = this.connectedClients.get(socket.id);
    if (!clientInfo || !clientInfo.roomId) {
      return;
    }

    const room = this.gameRooms.get(clientInfo.roomId);
    if (!room) {
      return;
    }

    const player = room.getPlayer(clientInfo.playerId!);
    if (player) {
      room.removePlayer(player.id);
      socket.leave(clientInfo.roomId);

      // 广播玩家离开
      this.broadcastToRoom(clientInfo.roomId, 'player_left', {
        playerId: player.id,
        playerName: player.name,
        playerCount: room.currentPlayers
      });
    }

    // 清理客户端信息
    clientInfo.playerId = undefined;
    clientInfo.roomId = undefined;

    logger.info(`Player left room ${clientInfo.roomId}`);
  }

  // 处理断开连接
  private handleDisconnection(socket: any, reason: string): void {
    const clientInfo = this.connectedClients.get(socket.id);
    if (!clientInfo) {
      return;
    }

    this.handleLeaveRoom(socket);
    this.connectedClients.delete(socket.id);

    wsConnection('disconnect', socket.id, clientInfo.playerId);
    logger.info(`Client disconnected: ${socket.id}, reason: ${reason}`);
  }

  // 发送消息到Socket
  private sendToSocket(socket: any, type: string, payload: any): void {
    try {
      socket.emit(type, {
        type,
        timestamp: new Date(),
        payload
      });
    } catch (error) {
      logger.error(`Error sending message to socket ${socket.id}:`, error);
    }
  }

  // 广播消息到房间
  private broadcastToRoom(roomId: string, type: string, payload: any, excludeSocketId?: string): void {
    try {
      const message = {
        type,
        timestamp: new Date(),
        payload
      };

      if (excludeSocketId) {
        this.io.to(roomId).except(excludeSocketId).emit(type, message);
      } else {
        this.io.to(roomId).emit(type, message);
      }
    } catch (error) {
      logger.error(`Error broadcasting to room ${roomId}:`, error);
    }
  }

  // 发送错误消息
  private sendError(socket: any, code: ErrorCode, message: string, details?: any): void {
    this.sendToSocket(socket, 'error', {
      code,
      message,
      details,
      timestamp: new Date()
    });
  }

  // 获取服务状态
  getServiceStatus() {
    return {
      connectedClients: this.connectedClients.size,
      activeRooms: this.gameRooms.size,
      activeGames: this.gameEngines.size,
      uptime: process.uptime()
    };
  }

  // 清理资源
  async cleanup(): Promise<void> {
    logger.info('Cleaning up WebSocket service...');

    // 停止所有游戏引擎
    for (const [roomId, engine] of this.gameEngines) {
      try {
        await engine.stopGame();
      } catch (error) {
        logger.error(`Error stopping game ${roomId}:`, error);
      }
    }

    // 断开所有连接
    this.io.close();

    // 清理数据
    this.connectedClients.clear();
    this.gameRooms.clear();
    this.gameEngines.clear();

    logger.info('WebSocket service cleanup completed');
  }
}