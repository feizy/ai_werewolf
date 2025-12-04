import { v4 as uuidv4 } from 'uuid';
import { GameRoom, RoomStatus, GameConfiguration } from '@/types';
import { PlayerModel } from './Player';

export class GameRoomModel implements GameRoom {
  public readonly id: string;
  public name?: string;
  public creatorId: string;
  public maxPlayers: number;
  public currentPlayers: number;
  public status: RoomStatus;
  public gameConfig: GameConfiguration;
  public createdAt: Date;
  public startedAt?: Date;
  public endedAt?: Date;

  private players: PlayerModel[] = [];

  constructor(data: Partial<GameRoom>) {
    this.id = data.id || uuidv4();
    this.name = data.name;
    this.creatorId = data.creatorId || '';
    this.maxPlayers = data.maxPlayers || 9;
    this.currentPlayers = data.currentPlayers || 0;
    this.status = data.status || RoomStatus.WAITING;
    this.gameConfig = data.gameConfig || this.getDefaultGameConfig();
    this.createdAt = data.createdAt || new Date();
    this.startedAt = data.startedAt;
    this.endedAt = data.endedAt;
  }

  private getDefaultGameConfig(): GameConfiguration {
    return {
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
      gameMode: 'classic'
    };
  }

  // 添加玩家
  addPlayer(player: PlayerModel): boolean {
    if (this.currentPlayers >= this.maxPlayers) {
      return false;
    }

    // 检查玩家名称是否重复
    if (this.players.some(p => p.name === player.name)) {
      throw new Error(`Player name "${player.name}" already exists in room`);
    }

    this.players.push(player);
    player.roomId = this.id;
    this.currentPlayers = this.players.length;
    return true;
  }

  // 移除玩家
  removePlayer(playerId: string): PlayerModel | null {
    const playerIndex = this.players.findIndex(p => p.id === playerId);
    if (playerIndex === -1) {
      return null;
    }

    const player = this.players.splice(playerIndex, 1)[0];
    this.currentPlayers = this.players.length;
    return player;
  }

  // 根据ID获取玩家
  getPlayer(playerId: string): PlayerModel | null {
    return this.players.find(p => p.id === playerId) || null;
  }

  // 根据名称获取玩家
  getPlayerByName(name: string): PlayerModel | null {
    return this.players.find(p => p.name === name) || null;
  }

  // 获取所有玩家
  getPlayers(): PlayerModel[] {
    return [...this.players];
  }

  // 获取存活的玩家
  getAlivePlayers(): PlayerModel[] {
    return this.players.filter(p => p.isAlive());
  }

  // 检查房间是否已满
  isFull(): boolean {
    return this.currentPlayers >= this.maxPlayers;
  }

  // 检查房间是否可以开始游戏
  canStartGame(): boolean {
    return this.status === RoomStatus.WAITING && this.currentPlayers === this.maxPlayers;
  }

  // 开始游戏
  startGame(): boolean {
    if (!this.canStartGame()) {
      return false;
    }

    this.status = RoomStatus.PLAYING;
    this.startedAt = new Date();
    return true;
  }

  // 结束游戏
  endGame(): void {
    this.status = RoomStatus.FINISHED;
    this.endedAt = new Date();
  }

  // 分配座位
  assignPositions(): void {
    this.players.forEach((player, index) => {
      player.position = index + 1;
    });
  }

  // 随机打乱玩家顺序
  shufflePlayers(): void {
    for (let i = this.players.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [this.players[i], this.players[j]] = [this.players[j], this.players[i]];
    }
    this.assignPositions();
  }

  // 获取房间摘要信息
  getSummary() {
    return {
      id: this.id,
      name: this.name,
      creatorId: this.creatorId,
      maxPlayers: this.maxPlayers,
      currentPlayers: this.currentPlayers,
      status: this.status,
      createdAt: this.createdAt,
      startedAt: this.startedAt,
      endedAt: this.endedAt,
      isFull: this.isFull(),
      canStartGame: this.canStartGame(),
      players: this.players.map(p => p.getSummary())
    };
  }

  // 获取玩家信息（用于API响应）
  getPlayersInfo() {
    return this.players.map(p => ({
      playerId: p.id,
      playerName: p.name,
      type: 'ai' as const,
      position: p.position,
      joinedAt: p.joinedAt
    }));
  }

  // 获取房间状态信息
  getStatusInfo() {
    return {
      id: this.id,
      name: this.name,
      creatorName: this.getPlayer(this.creatorId)?.name || 'Unknown',
      currentPlayers: this.currentPlayers,
      maxPlayers: this.maxPlayers,
      status: this.status,
      players: this.getPlayersInfo()
    };
  }

  // 静态方法：创建新房间
  static createRoom(
    creatorId: string,
    creatorName: string,
    roomName?: string,
    config?: Partial<GameConfiguration>
  ): GameRoomModel {
    const room = new GameRoomModel({
      creatorId,
      name: roomName,
      gameConfig: config
    });

    // 自动创建房主玩家
    const creator = PlayerModel.createAIPlayer(creatorName, room.id, 0);
    room.addPlayer(creator);

    return room;
  }

  // 静态方法：创建测试房间
  static createTestRoom(playerCount: number = 9): GameRoomModel {
    const room = new GameRoomModel({
      creatorId: 'test-creator',
      name: 'Test Room'
    });

    // 创建测试玩家
    for (let i = 0; i < playerCount; i++) {
      const player = PlayerModel.createAIPlayer(`AI Player ${i + 1}`, room.id, i);
      room.addPlayer(player);
    }

    return room;
  }

  // 验证房间状态
  validateState(): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (!this.creatorId) {
      errors.push('Room must have a creator');
    }

    if (this.players.length !== this.currentPlayers) {
      errors.push('Player count mismatch');
    }

    const creatorExists = this.players.some(p => p.id === this.creatorId);
    if (!creatorExists) {
      errors.push('Creator not found in players');
    }

    const duplicateNames = this.players
      .map(p => p.name)
      .filter((name, index, arr) => arr.indexOf(name) !== index);
    if (duplicateNames.length > 0) {
      errors.push(`Duplicate player names: ${duplicateNames.join(', ')}`);
    }

    const duplicatePositions = this.players
      .map(p => p.position)
      .filter((pos, index, arr) => arr.indexOf(pos) !== index && pos !== 0);
    if (duplicatePositions.length > 0) {
      errors.push(`Duplicate positions: ${duplicatePositions.join(', ')}`);
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }
}