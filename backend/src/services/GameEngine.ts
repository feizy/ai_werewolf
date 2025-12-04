import { v4 as uuidv4 } from 'uuid';
import { GameSession, GameState, GamePhase, Team, RoleType, DeathCause, EventType } from '@/types';
import { PlayerModel } from '@/models/Player';
import { GameRoomModel } from '@/models/GameRoom';
import { AgentScopeService } from './AgentScopeService';
import { GameEventService } from './GameEventService';
import { logger } from '@/utils/logger';

export interface GameEngineConfig {
  maxDuration: number;          // 游戏最长持续时间（秒）
  phaseTimeouts: {             // 各阶段超时时间（秒）
    night: number;
    sheriffElection: number;
    dayDiscussion: number;
    voting: number;
  };
  autoProgress: boolean;       // 是否自动推进游戏
}

export class GameEngine {
  private config: GameEngineConfig;
  private session: GameSession;
  private agentScopeService: AgentScopeService;
  private eventService: GameEventService;
  private phaseTimer?: NodeJS.Timeout;
  private isRunning: boolean = false;

  constructor(
    room: GameRoomModel,
    agentScopeService: AgentScopeService,
    eventService: GameEventService,
    config?: Partial<GameEngineConfig>
  ) {
    this.config = {
      maxDuration: config?.maxDuration || 3600, // 1小时
      phaseTimeouts: {
        night: config?.phaseTimeouts?.night || 30,
        sheriffElection: config?.phaseTimeouts?.sheriffElection || 120,
        dayDiscussion: config?.phaseTimeouts?.dayDiscussion || 180,
        voting: config?.phaseTimeouts?.voting || 60
      },
      autoProgress: config?.autoProgress ?? true
    };

    this.agentScopeService = agentScopeService;
    this.eventService = eventService;
    this.session = this.createGameSession(room);
  }

  // 创建游戏会话
  private createGameSession(room: GameRoomModel): GameSession {
    const players = room.getPlayers();
    const roles = this.assignRoles(players);

    const gameState: GameState = {
      phase: GamePhase.NIGHT,
      dayCount: 1,
      players: players.map(p => ({
        playerId: p.id,
        playerName: p.name,
        role: p.role!,
        status: 'alive' as const,
        position: p.position,
        votingWeight: 1.0
      })),
      nightActions: {}
    };

    return {
      id: uuidv4(),
      roomId: room.id,
      players: players,
      gameState,
      dayCount: 1,
      currentPhase: GamePhase.NIGHT,
      phaseStartTime: new Date(),
      events: [],
      dailySnapshots: [],
      winner: undefined,
      endedAt: undefined
    };
  }

  // 分配角色
  private assignRoles(players: PlayerModel[]): RoleType[] {
    const roles: RoleType[] = [
      ...Array(3).fill(RoleType.WEREWOLF),
      ...Array(3).fill(RoleType.VILLAGER),
      RoleType.SEER,
      RoleType.WITCH,
      RoleType.HUNTER
    ];

    // 随机打乱角色
    for (let i = roles.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [roles[i], roles[j]] = [roles[j], roles[i]];
    }

    // 分配角色给玩家
    players.forEach((player, index) => {
      player.setRole(roles[index]);
    });

    return roles;
  }

  // 开始游戏
  async startGame(): Promise<void> {
    try {
      logger.info(`Starting game session ${this.session.id}`);

      this.isRunning = true;

      // 初始化AI代理
      await this.initializeAIAgents();

      // 创建每日快照
      await this.createDailySnapshot();

      // 游戏开始事件
      await this.eventService.createEvent({
        type: EventType.GAME_START,
        sessionId: this.session.id,
        phase: GamePhase.NIGHT,
        dayCount: 1,
        content: '游戏开始！',
        visibility: { public: true }
      });

      // 开始夜晚阶段
      await this.startNightPhase();

      logger.info(`Game ${this.session.id} started successfully`);
    } catch (error) {
      logger.error(`Failed to start game ${this.session.id}:`, error);
      throw error;
    }
  }

  // 初始化AI代理
  private async initializeAIAgents(): Promise<void> {
    logger.info('Initializing AI agents for all players');

    for (const player of this.session.players) {
      const agentId = await this.agentScopeService.createAgent(
        player.id,
        player.name,
        player.role!,
        player.aiConfig.personality,
        player.aiConfig.skillLevel,
        player.aiConfig.responseTime
      );

      player.agentScopeId = agentId;
      logger.info(`Created agent ${agentId} for player ${player.name} as ${player.role}`);
    }
  }

  // 开始夜晚阶段
  private async startNightPhase(): Promise<void> {
    logger.info(`Starting night phase, day ${this.session.dayCount}`);

    this.session.currentPhase = GamePhase.NIGHT;
    this.session.phaseStartTime = new Date();

    // 重置夜晚能力
    this.resetNightlyAbilities();

    // 阶段变化事件
    await this.eventService.createEvent({
      type: EventType.PHASE_CHANGE,
      sessionId: this.session.id,
      phase: GamePhase.NIGHT,
      dayCount: this.session.dayCount,
      content: `第${this.session.dayCount}夜降临`,
      visibility: { public: true }
    });

    // 获取夜晚行动者
    const nightActors = this.session.players.filter(p => p.isAlive() && this.canActAtNight(p.role!));

    // 按顺序处理夜晚行动
    await this.processNightActions(nightActors);
  }

  // 重置夜晚能力
  private resetNightlyAbilities(): void {
    this.session.players.forEach(player => {
      player.resetNightlyAbilities();
    });
  }

  // 检查角色是否可以在夜晚行动
  private canActAtNight(role: RoleType): boolean {
    return [RoleType.WEREWOLF, RoleType.SEER, RoleType.WITCH].includes(role);
  }

  // 处理夜晚行动
  private async processNightActions(nightActors: PlayerModel[]): Promise<void> {
    logger.info(`Processing night actions for ${nightActors.length} actors`);

    // 1. 狼人行动
    const werewolves = nightActors.filter(p => p.role === RoleType.WEREWOLF);
    if (werewolves.length > 0) {
      await this.processWerewolfActions(werewolves);
    }

    // 2. 预言家查验
    const seer = nightActors.find(p => p.role === RoleType.SEER);
    if (seer) {
      await this.processSeerAction(seer);
    }

    // 3. 女巫行动
    const witch = nightActors.find(p => p.role === RoleType.WITCH);
    if (witch) {
      await this.processWitchAction(witch);
    }

    // 处理夜晚死亡
    await this.resolveNightDeaths();

    // 检查胜利条件
    if (this.checkVictoryConditions()) {
      await this.endGame();
      return;
    }

    // 进入白天阶段
    await this.startDayPhase();
  }

  // 处理狼人行动
  private async processWerewolfActions(werewolves: PlayerModel[]): Promise<void> {
    logger.info(`Processing werewolf actions for ${werewolves.length} werewolves`);

    // 狼人团队讨论和决策
    const targets = this.session.players.filter(p => p.role !== RoleType.WEREWOLF && p.isAlive());

    if (targets.length === 0) {
      logger.warn('No valid targets for werewolves');
      return;
    }

    // 选择击杀目标（简化版本，实际需要更复杂的AI决策）
    const target = this.selectWerewolfTarget(werewolves, targets);

    this.session.gameState.nightActions!.werewolfTarget = {
      playerId: target.id,
      playerName: target.name,
      agreedBy: werewolves.map(w => w.id)
    };

    // 记录狼人击杀事件
    await this.eventService.createEvent({
      type: EventType.WEREWOLF_KILL,
      sessionId: this.session.id,
      phase: GamePhase.NIGHT,
      dayCount: this.session.dayCount,
      actorId: werewolves[0].id,
      actorName: '狼人团队',
      targetId: target.id,
      targetName: target.name,
      content: `狼人选择击杀${target.name}`,
      visibility: {
        public: false,
        visibleToRoles: [RoleType.WEREWOLF],
        visibleToPlayers: werewolves.map(w => w.id)
      }
    });

    logger.info(`Werewolves selected target: ${target.name}`);
  }

  // 选择狼人击杀目标
  private selectWerewolfTarget(werewolves: PlayerModel[], targets: PlayerModel[]): PlayerModel {
    // 简化的选择逻辑：优先选择神职
    const priorityTargets = targets.filter(t =>
      [RoleType.SEER, RoleType.WITCH, RoleType.HUNTER].includes(t.role!)
    );

    const candidateTargets = priorityTargets.length > 0 ? priorityTargets : targets;
    return candidateTargets[Math.floor(Math.random() * candidateTargets.length)];
  }

  // 处理预言家查验
  private async processSeerAction(seer: PlayerModel): Promise<void> {
    logger.info(`Processing seer action for ${seer.name}`);

    const targets = this.session.players.filter(p => p.id !== seer.id && p.isAlive());

    if (targets.length === 0) {
      logger.warn('No valid targets for seer');
      return;
    }

    // 选择查验目标（简化逻辑）
    const target = targets[Math.floor(Math.random() * targets.length)];
    const result = target.getTeam() === Team.WEREWOLF ? 'werewolf' : 'good';

    seer.seerCheck(target.id, target.name, result);

    // 记录查验事件
    await this.eventService.createEvent({
      type: EventType.SEER_CHECK,
      sessionId: this.session.id,
      phase: GamePhase.NIGHT,
      dayCount: this.session.dayCount,
      actorId: seer.id,
      actorName: seer.name,
      targetId: target.id,
      targetName: target.name,
      content: `预言家查验了${target.name}`,
      visibility: {
        public: false,
        visibleToPlayers: [seer.id]
      },
      details: { seerCheckResult: result }
    });

    logger.info(`Seer ${seer.name} checked ${target.name}: ${result}`);
  }

  // 处理女巫行动
  private async processWitchAction(witch: PlayerModel): Promise<void> {
    logger.info(`Processing witch action for ${witch.name}`);

    const werewolfTarget = this.session.gameState.nightActions?.werewolfTarget;

    if (werewolfTarget) {
      // 女巫知晓狼人目标
      logger.info(`Witch ${witch.name} sees werewolf target: ${werewolfTarget.playerName}`);

      // 简化的决策逻辑：50%概率救人，30%概率毒人，20%概率什么都不做
      const random = Math.random();

      if (random < 0.5 && witch.roleAbilities?.witchInfo?.hasAntidote) {
        // 使用解药
        witch.useAntidote();
        this.session.gameState.nightActions!.witchAction = {
          action: 'antidote',
          targetId: werewolfTarget.playerId,
          targetName: werewolfTarget.playerName
        };

        await this.eventService.createEvent({
          type: EventType.WITCH_SAVE,
          sessionId: this.session.id,
          phase: GamePhase.NIGHT,
          dayCount: this.session.dayCount,
          actorId: witch.id,
          actorName: '女巫',
          targetId: werewolfTarget.playerId,
          targetName: werewolfTarget.playerName,
          content: `女巫使用解药救活了${werewolfTarget.playerName}`,
          visibility: {
            public: false,
            visibleToPlayers: [witch.id]
          }
        });

        logger.info(`Witch saved ${werewolfTarget.playerName}`);
      } else if (random < 0.8 && witch.roleAbilities?.witchInfo?.hasPoison) {
        // 使用毒药
        const poisonTargets = this.session.players.filter(p =>
          p.id !== witch.id && p.isAlive() && p.id !== werewolfTarget.playerId
        );

        if (poisonTargets.length > 0) {
          const poisonTarget = poisonTargets[Math.floor(Math.random() * poisonTargets.length)];
          witch.usePoison(poisonTarget.id);

          this.session.gameState.nightActions!.witchAction = {
            action: 'poison',
            targetId: poisonTarget.id,
            targetName: poisonTarget.name
          };

          await this.eventService.createEvent({
            type: EventType.WITCH_POISON,
            sessionId: this.session.id,
            phase: GamePhase.NIGHT,
            dayCount: this.session.dayCount,
            actorId: witch.id,
            actorName: '女巫',
            targetId: poisonTarget.id,
            targetName: poisonTarget.name,
            content: `女巫使用毒药毒死了${poisonTarget.name}`,
            visibility: {
              public: false,
              visibleToPlayers: [witch.id]
            }
          });

          logger.info(`Witch poisoned ${poisonTarget.name}`);
        }
      }
    }
  }

  // 解决夜晚死亡
  private async resolveNightDeaths(): Promise<void> {
    const deaths: { playerId: string; playerName: string; cause: DeathCause }[] = [];

    // 检查狼人击杀
    const werewolfTarget = this.session.gameState.nightActions?.werewolfTarget;
    const witchAction = this.session.gameState.nightActions?.witchAction;

    if (werewolfTarget && witchAction?.action !== 'antidote') {
      deaths.push({
        playerId: werewolfTarget.playerId,
        playerName: werewolfTarget.playerName,
        cause: DeathCause.WEREWOLF_KILL
      });
    }

    // 检查女巫毒药
    if (witchAction?.action === 'poison' && witchAction.targetId) {
      deaths.push({
        playerId: witchAction.targetId,
        playerName: witchAction.targetName!,
        cause: DeathCause.WITCH_POISON
      });
    }

    // 处理死亡
    for (const death of deaths) {
      const player = this.session.players.find(p => p.id === death.playerId);
      if (player) {
        player.setDead(death.cause);

        await this.eventService.createEvent({
          type: EventType.PLAYER_DEATH,
          sessionId: this.session.id,
          phase: GamePhase.NIGHT,
          dayCount: this.session.dayCount,
          targetId: death.playerId,
          targetName: death.playerName,
          content: `${death.playerName}在夜里死亡了`,
          visibility: { public: true },
          details: { deathDetails: { cause: death.cause } }
        });

        logger.info(`${death.playerName} died from ${death.cause}`);
      }
    }
  }

  // 开始白天阶段
  private async startDayPhase(): Promise<void> {
    logger.info(`Starting day phase, day ${this.session.dayCount}`);

    this.session.currentPhase = this.session.dayCount === 1 ?
      GamePhase.SHERIFF_ELECTION :
      GamePhase.DAY_DISCUSSION;

    this.session.phaseStartTime = new Date();

    if (this.session.dayCount === 1) {
      await this.startSheriffElection();
    } else {
      await this.startDayDiscussion();
    }
  }

  // 开始警长竞选
  private async startSheriffElection(): Promise<void> {
    logger.info('Starting sheriff election');

    // 记录警长竞选开始事件
    await this.eventService.createEvent({
      type: EventType.SHERIFF_ELECTION_START,
      sessionId: this.session.id,
      phase: GamePhase.SHERIFF_ELECTION,
      dayCount: this.session.dayCount,
      content: '第一天警长竞选开始',
      visibility: { public: true }
    });

    // 简化处理：随机选择警长
    const alivePlayers = this.session.players.filter(p => p.isAlive());
    const sheriff = alivePlayers[Math.floor(Math.random() * alivePlayers.length)];

    sheriff.setAsSheriff();

    await this.eventService.createEvent({
      type: EventType.SHERIFF_ELECTED,
      sessionId: this.session.id,
      phase: GamePhase.SHERIFF_ELECTION,
      dayCount: this.session.dayCount,
      targetId: sheriff.id,
      targetName: sheriff.name,
      content: `${sheriff.name}当选为警长`,
      visibility: { public: true }
    });

    logger.info(`${sheriff.name} was elected as sheriff`);

    // 进入讨论阶段
    await this.startDayDiscussion();
  }

  // 开始白天讨论
  private async startDayDiscussion(): Promise<void> {
    logger.info(`Starting day discussion, day ${this.session.dayCount}`);

    this.session.currentPhase = GamePhase.DAY_DISCUSSION;

    await this.eventService.createEvent({
      type: EventType.PHASE_CHANGE,
      sessionId: this.session.id,
      phase: GamePhase.DAY_DISCUSSION,
      dayCount: this.session.dayCount,
      content: `第${this.session.dayCount}天讨论开始`,
      visibility: { public: true }
    });

    // 简化处理：直接进入投票阶段
    await this.startVoting();
  }

  // 开始投票
  private async startVoting(): Promise<void> {
    logger.info(`Starting voting phase, day ${this.session.dayCount}`);

    this.session.currentPhase = GamePhase.VOTING;

    const alivePlayers = this.session.players.filter(p => p.isAlive());

    // 简化投票：随机投票
    const votes = new Map<string, { playerId: string; playerName: string; votes: number; weight: number }>();

    alivePlayers.forEach(voter => {
      const targets = alivePlayers.filter(p => p.id !== voter.id);
      if (targets.length > 0) {
        const target = targets[Math.floor(Math.random() * targets.length)];
        const existing = votes.get(target.id);

        if (existing) {
          existing.votes += voter.votingWeight;
          existing.weight += voter.votingWeight;
        } else {
          votes.set(target.id, {
            playerId: target.id,
            playerName: target.name,
            votes: voter.votingWeight,
            weight: voter.votingWeight
          });
        }
      }
    });

    // 找出得票最多的玩家
    let maxVotes = 0;
    let eliminated: any = null;

    for (const vote of votes.values()) {
      if (vote.votes > maxVotes) {
        maxVotes = vote.votes;
        eliminated = vote;
      }
    }

    // 处理投票结果
    if (eliminated) {
      const player = this.session.players.find(p => p.id === eliminated.playerId);
      if (player) {
        player.setDead(DeathCause.VOTE_OUT);

        await this.eventService.createEvent({
          type: EventType.VOTE_RESULT,
          sessionId: this.session.id,
          phase: GamePhase.VOTING,
          dayCount: this.session.dayCount,
          targetId: eliminated.playerId,
          targetName: eliminated.playerName,
          content: `${eliminated.playerName}被投票出局`,
          visibility: { public: true },
          details: {
            votingDetails: {
              candidateId: eliminated.playerId,
              voteCount: eliminated.votes,
              sheriffInfluence: false
            }
          }
        });

        logger.info(`${eliminated.playerName} was eliminated by vote`);

        // 检查是否是猎人
        if (player.role === RoleType.HUNTER) {
          await this.processHunterShoot(player);
        }
      }
    }

    // 检查胜利条件
    if (this.checkVictoryConditions()) {
      await this.endGame();
      return;
    }

    // 进入下一个夜晚
    this.session.dayCount++;
    await this.startNightPhase();
  }

  // 处理猎人开枪
  private async processHunterShoot(hunter: PlayerModel): Promise<void> {
    logger.info(`Processing hunter shoot for ${hunter.name}`);

    const alivePlayers = this.session.players.filter(p => p.isAlive() && p.id !== hunter.id);

    if (alivePlayers.length === 0) {
      logger.warn('No valid targets for hunter');
      return;
    }

    // 随机选择目标
    const target = alivePlayers[Math.floor(Math.random() * alivePlayers.length)];

    hunter.hunterShoot(target.id);
    target.setDead(DeathCause.HUNTER_SHOOT);

    await this.eventService.createEvent({
      type: EventType.HUNTER_SHOOT,
      sessionId: this.session.id,
      phase: GamePhase.VOTING,
      dayCount: this.session.dayCount,
      actorId: hunter.id,
      actorName: hunter.name,
      targetId: target.id,
      targetName: target.name,
      content: `猎人${hunter.name}开枪带走了${target.name}`,
      visibility: { public: true }
    });

    logger.info(`Hunter ${hunter.name} shot ${target.name}`);
  }

  // 检查胜利条件
  private checkVictoryConditions(): boolean {
    const alivePlayers = this.session.players.filter(p => p.isAlive());
    const aliveWerewolves = alivePlayers.filter(p => p.role === RoleType.WEREWOLF);
    const aliveGood = alivePlayers.filter(p => p.role !== RoleType.WEREWOLF);
    const aliveVillagers = alivePlayers.filter(p => p.role === RoleType.VILLAGER);
    const aliveSpecial = alivePlayers.filter(p => [RoleType.SEER, RoleType.WITCH, RoleType.HUNTER].includes(p.role!));

    // 检查狼人胜利条件
    if (aliveWerewolves.length >= aliveGood.length ||
        aliveVillagers.length === 0 ||
        aliveSpecial.length === 0) {
      this.session.winner = Team.WEREWOLF;
      return true;
    }

    // 检查好人胜利条件
    if (aliveWerewolves.length === 0) {
      this.session.winner = Team.GOOD;
      return true;
    }

    return false;
  }

  // 结束游戏
  private async endGame(): Promise<void> {
    logger.info(`Game ${this.session.id} ended. Winner: ${this.session.winner}`);

    this.isRunning = false;
    this.session.endedAt = new Date();
    this.session.currentPhase = GamePhase.GAME_OVER;

    // 揭露所有角色
    const finalRoles = this.session.players.map(p => ({
      playerId: p.id,
      playerName: p.name,
      role: p.role!,
      survived: p.isAlive()
    }));

    // 记录游戏结束事件
    await this.eventService.createEvent({
      type: EventType.GAME_END,
      sessionId: this.session.id,
      phase: GamePhase.GAME_OVER,
      dayCount: this.session.dayCount,
      content: `游戏结束！${this.session.winner === Team.WEREWOLF ? '狼人阵营' : '好人阵营'}获胜！`,
      visibility: { public: true }
    });

    // 创建最终的每日快照
    await this.createDailySnapshot();

    // 清理定时器
    if (this.phaseTimer) {
      clearTimeout(this.phaseTimer);
      this.phaseTimer = undefined;
    }

    logger.info(`Game ${this.session.id} completed successfully`);
  }

  // 创建每日快照
  private async createDailySnapshot(): Promise<void> {
    const snapshot = {
      id: uuidv4(),
      sessionId: this.session.id,
      dayNumber: this.session.dayCount,
      timestamp: new Date(),
      playerStates: this.session.players.map(p => ({
        playerId: p.id,
        playerName: p.name,
        role: p.role!,
        status: p.isAlive() ? 'alive' as const : 'dead' as const,
        position: p.position,
        abilities: p.roleAbilities ? {
          witchAntidote: p.roleAbilities.witchInfo?.hasAntidote || false,
          witchPoison: p.roleAbilities.witchInfo?.hasPoison || false,
          hunterCanShoot: p.roleAbilities.hunterInfo?.canShoot || false
        } : undefined,
        votingWeight: p.votingWeight
      })),
      gameState: {
        phase: this.session.currentPhase,
        sheriff: this.session.players.find(p => p.votingWeight > 1) ? {
          playerId: this.session.players.find(p => p.votingWeight > 1)!.id,
          playerName: this.session.players.find(p => p.votingWeight > 1)!.name
        } : undefined,
        alivePlayers: this.session.players.filter(p => p.isAlive()).length
      },
      availableEvents: this.session.events.map(e => ({
        eventId: e.id,
        type: e.type,
        timestamp: e.timestamp,
        description: e.content,
        participants: [e.actorId, e.targetId].filter(Boolean) as string[]
      }))
    };

    this.session.dailySnapshots.push(snapshot);
    logger.info(`Created daily snapshot for day ${this.session.dayCount}`);
  }

  // 获取游戏会话
  getSession(): GameSession {
    return this.session;
  }

  // 获取当前游戏状态
  getCurrentState(): GameState {
    return this.session.gameState;
  }

  // 停止游戏
  async stopGame(): Promise<void> {
    logger.info(`Stopping game ${this.session.id}`);

    this.isRunning = false;

    if (this.phaseTimer) {
      clearTimeout(this.phaseTimer);
      this.phaseTimer = undefined;
    }

    if (!this.session.endedAt) {
      await this.endGame();
    }

    logger.info(`Game ${this.session.id} stopped`);
  }

  // 获取游戏状态摘要
  getGameSummary() {
    return {
      sessionId: this.session.id,
      roomId: this.session.roomId,
      status: this.isRunning ? 'running' : 'ended',
      currentPhase: this.session.currentPhase,
      dayCount: this.session.dayCount,
      players: this.session.players.map(p => ({
        id: p.id,
        name: p.name,
        role: p.role!,
        status: p.isAlive() ? 'alive' : 'dead',
        position: p.position,
        votingWeight: p.votingWeight
      })),
      winner: this.session.winner,
      startTime: this.session.phaseStartTime,
      endTime: this.session.endedAt,
      duration: this.session.endedAt ?
        Math.floor((this.session.endedAt.getTime() - this.session.phaseStartTime.getTime()) / 1000) :
        Math.floor((new Date().getTime() - this.session.phaseStartTime.getTime()) / 1000)
    };
  }
}