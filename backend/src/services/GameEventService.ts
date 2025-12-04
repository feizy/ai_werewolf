import { v4 as uuidv4 } from 'uuid';
import { GameEvent, EventType, GamePhase } from '@/types';
import { logger } from '@/utils/logger';

export interface CreateEventData {
  type: EventType;
  sessionId: string;
  phase: GamePhase;
  dayCount: number;
  actorId?: string;
  actorName?: string;
  targetId?: string;
  targetName?: string;
  content: string;
  visibility: {
    public: boolean;
    visibleToRoles?: string[];
    visibleToPlayers?: string[];
    requiresRoleReveal?: boolean;
  };
  details?: any;
}

export class GameEventService {
  private static instance: GameEventService;
  private events: Map<string, GameEvent[]> = new Map();

  private constructor() {}

  public static getInstance(): GameEventService {
    if (!GameEventService.instance) {
      GameEventService.instance = new GameEventService();
    }
    return GameEventService.instance;
  }

  // 创建游戏事件
  async createEvent(data: CreateEventData): Promise<GameEvent> {
    const event: GameEvent = {
      id: uuidv4(),
      sessionId: data.sessionId,
      type: data.type,
      phase: data.phase,
      dayCount: data.dayCount,
      timestamp: new Date(),
      actorId: data.actorId,
      actorName: data.actorName,
      targetId: data.targetId,
      targetName: data.targetName,
      content: data.content,
      details: data.details,
      visibility: data.visibility
    };

    // 存储事件
    const sessionEvents = this.events.get(data.sessionId) || [];
    sessionEvents.push(event);
    this.events.set(data.sessionId, sessionEvents);

    logger.debug(`Created event ${event.id} for session ${data.sessionId}: ${event.content}`);

    return event;
  }

  // 获取游戏的所有事件
  getSessionEvents(sessionId: string): GameEvent[] {
    return this.events.get(sessionId) || [];
  }

  // 获取指定阶段的事件
  getPhaseEvents(sessionId: string, phase: GamePhase): GameEvent[] {
    const events = this.getSessionEvents(sessionId);
    return events.filter(e => e.phase === phase);
  }

  // 获取指定天数的事件
  getDayEvents(sessionId: string, dayCount: number): GameEvent[] {
    const events = this.getSessionEvents(sessionId);
    return events.filter(e => e.dayCount === dayCount);
  }

  // 获取玩家可见的事件
  getVisibleEvents(
    sessionId: string,
    playerId?: string,
    playerRole?: string
  ): GameEvent[] {
    const events = this.getSessionEvents(sessionId);

    return events.filter(event => {
      // 公开事件所有人可见
      if (event.visibility.public) {
        return true;
      }

      // 检查角色可见性
      if (playerRole && event.visibility.visibleToRoles?.includes(playerRole)) {
        return true;
      }

      // 检查玩家可见性
      if (playerId && event.visibility.visibleToPlayers?.includes(playerId)) {
        return true;
      }

      return false;
    });
  }

  // 获取事件详情（用于回放）
  getEventById(sessionId: string, eventId: string): GameEvent | null {
    const events = this.getSessionEvents(sessionId);
    return events.find(e => e.id === eventId) || null;
  }

  // 获取最近的事件
  getRecentEvents(sessionId: string, limit: number = 10): GameEvent[] {
    const events = this.getSessionEvents(sessionId);
    return events
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
      .slice(0, limit);
  }

  // 获取指定事件之后的事件
  getEventsAfter(sessionId: string, timestamp: Date): GameEvent[] {
    const events = this.getSessionEvents(sessionId);
    return events.filter(e => e.timestamp > timestamp);
  }

  // 清理游戏事件
  clearSessionEvents(sessionId: string): void {
    this.events.delete(sessionId);
    logger.debug(`Cleared events for session ${sessionId}`);
  }

  // 获取事件统计信息
  getEventStats(sessionId: string) {
    const events = this.getSessionEvents(sessionId);

    const stats = {
      totalEvents: events.length,
      eventsByType: {} as Record<EventType, number>,
      eventsByPhase: {} as Record<GamePhase, number>,
      eventsByDay: {} as Record<number, number>,
      publicEvents: 0,
      privateEvents: 0
    };

    events.forEach(event => {
      // 按类型统计
      stats.eventsByType[event.type] = (stats.eventsByType[event.type] || 0) + 1;

      // 按阶段统计
      stats.eventsByPhase[event.phase] = (stats.eventsByPhase[event.phase] || 0) + 1;

      // 按天数统计
      stats.eventsByDay[event.dayCount] = (stats.eventsByDay[event.dayCount] || 0) + 1;

      // 公开/私有统计
      if (event.visibility.public) {
        stats.publicEvents++;
      } else {
        stats.privateEvents++;
      }
    });

    return stats;
  }

  // 搜索事件
  searchEvents(
    sessionId: string,
    query: {
      type?: EventType;
      phase?: GamePhase;
      dayCount?: number;
      actorId?: string;
      targetId?: string;
      content?: string;
      startDate?: Date;
      endDate?: Date;
    }
  ): GameEvent[] {
    let events = this.getSessionEvents(sessionId);

    if (query.type) {
      events = events.filter(e => e.type === query.type);
    }

    if (query.phase) {
      events = events.filter(e => e.phase === query.phase);
    }

    if (query.dayCount) {
      events = events.filter(e => e.dayCount === query.dayCount);
    }

    if (query.actorId) {
      events = events.filter(e => e.actorId === query.actorId);
    }

    if (query.targetId) {
      events = events.filter(e => e.targetId === query.targetId);
    }

    if (query.content) {
      events = events.filter(e =>
        e.content.toLowerCase().includes(query.content!.toLowerCase())
      );
    }

    if (query.startDate) {
      events = events.filter(e => e.timestamp >= query.startDate!);
    }

    if (query.endDate) {
      events = events.filter(e => e.timestamp <= query.endDate!);
    }

    return events;
  }

  // 获取玩家事件历史
  getPlayerEventHistory(sessionId: string, playerId: string): {
    asActor: GameEvent[];
    asTarget: GameEvent[];
    mentioned: GameEvent[];
  } {
    const events = this.getSessionEvents(sessionId);

    return {
      asActor: events.filter(e => e.actorId === playerId),
      asTarget: events.filter(e => e.targetId === playerId),
      mentioned: events.filter(e =>
        e.content.includes(playerId) ||
        (e.actorId !== playerId && e.targetId !== playerId)
      )
    };
  }

  // 创建事件序列（用于回放）
  createEventSequence(sessionId: string, fromDay?: number, toDay?: number): GameEvent[] {
    let events = this.getSessionEvents(sessionId);

    if (fromDay !== undefined) {
      events = events.filter(e => e.dayCount >= fromDay);
    }

    if (toDay !== undefined) {
      events = events.filter(e => e.dayCount <= toDay);
    }

    return events.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
  }

  // 验证事件可见性
  validateEventVisibility(event: GameEvent, playerId?: string, playerRole?: string): boolean {
    // 公开事件
    if (event.visibility.public) {
      return true;
    }

    // 角色可见性
    if (playerRole && event.visibility.visibleToRoles?.includes(playerRole)) {
      return true;
    }

    // 玩家可见性
    if (playerId && event.visibility.visibleToPlayers?.includes(playerId)) {
      return true;
    }

    return false;
  }

  // 导出事件数据
  exportEvents(sessionId: string, format: 'json' | 'csv' = 'json'): string {
    const events = this.getSessionEvents(sessionId);

    if (format === 'json') {
      return JSON.stringify(events, null, 2);
    } else {
      // CSV格式
      const headers = [
        'id', 'sessionId', 'type', 'phase', 'dayCount', 'timestamp',
        'actorId', 'actorName', 'targetId', 'targetName', 'content'
      ];

      const rows = events.map(event => [
        event.id,
        event.sessionId,
        event.type,
        event.phase,
        event.dayCount,
        event.timestamp.toISOString(),
        event.actorId || '',
        event.actorName || '',
        event.targetId || '',
        event.targetName || '',
        event.content
      ]);

      return [headers, ...rows].map(row => row.join(',')).join('\n');
    }
  }

  // 获取服务状态
  getServiceStatus() {
    return {
      sessionCount: this.events.size,
      totalEvents: Array.from(this.events.values()).reduce((sum, events) => sum + events.length, 0),
      memoryUsage: process.memoryUsage()
    };
  }

  // 清理过期数据
  cleanupExpiredData(maxAge: number = 7 * 24 * 60 * 60 * 1000): number {
    let cleanedCount = 0;
    const cutoffTime = new Date(Date.now() - maxAge);

    for (const [sessionId, events] of this.events.entries()) {
      const filteredEvents = events.filter(event => event.timestamp > cutoffTime);
      const removedCount = events.length - filteredEvents.length;

      if (removedCount > 0) {
        this.events.set(sessionId, filteredEvents);
        cleanedCount += removedCount;

        // 如果没有事件了，删除会话
        if (filteredEvents.length === 0) {
          this.events.delete(sessionId);
        }
      }
    }

    if (cleanedCount > 0) {
      logger.info(`Cleaned up ${cleanedCount} expired events`);
    }

    return cleanedCount;
  }
}