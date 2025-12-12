import { useEffect, useRef, useCallback } from 'react';
import { useGameStore } from '@/store/gameStore';
import { GameEvent, GameState, Player } from '@/types/game';
import { getFullGameData, getGameEvents, cleanupGame } from '@/services/api';

function convertPhase(phase: string): GameState['phase'] {
  const phaseMap: Record<string, GameState['phase']> = {
    'night': 'night',
    'sheriff_election': 'sheriff_election',
    'day_discussion': 'day_discussion',
    'voting': 'voting',
    'game_over': 'game_over',
  };
  return phaseMap[phase] || 'day_discussion';
}

function convertEventType(type: string): GameEvent['category'] {
  const typeMap: Record<string, GameEvent['category']> = {
    'game_start': 'MODERATOR',
    'game_end': 'MODERATOR',
    'phase_change': 'MODERATOR',
    'werewolf_kill': 'ACTION',
    'seer_check': 'ACTION',
    'witch_save': 'ACTION',
    'witch_poison': 'ACTION',
    'hunter_shoot': 'ACTION',
    'player_speak': 'SPEECH',
    'player_speech': 'SPEECH',
    'vote_start': 'VOTE',
    'player_vote': 'VOTE',
    'vote_result': 'VOTE',
    'player_death': 'DEATH',
    'death_announce': 'DEATH',
  };
  return typeMap[type] || 'SYSTEM';
}

export const usePolling = (roomId: string | null, interval: number = 2000) => {
  const eventIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const stateIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastEventIdRef = useRef<string | null>(null);
  const isActiveRef = useRef<boolean>(true);

  const { setGameState, setConnectionStatus } = useGameStore();

  // 监听页面可见性变化
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        console.log('页面隐藏，暂停轮询');
        isActiveRef.current = false;
      } else {
        console.log('页面显示，恢复轮询');
        isActiveRef.current = true;
      }
    };

    const handleBeforeUnload = () => {
      console.log('页面即将卸载，标记为非活跃状态');
      isActiveRef.current = false;
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

  const startPolling = useCallback(() => {
    // 停止现有轮询
    stopPolling();

    // 立即获取一次完整数据
    (async () => {
      if (!roomId || !isActiveRef.current) return;

      try {
        // 首次获取完整数据
        const gameData = await getFullGameData(roomId);
        const eventsData = await getGameEvents(roomId);

        const gameState: GameState = {
          id: gameData.session_id,
          roomId: gameData.room_id,
          day: gameData.day_count,
          phase: gameData.current_phase === 'running' ? 'day_discussion' : convertPhase(gameData.current_phase),
          players: gameData.players.map((p: any): Player => ({
            id: p.id,
            name: p.name,
            position: p.position,
            role: p.role,
            status: p.status === 'alive' ? 'alive' : 'dead',
            isSheriff: p.is_sheriff,
            votingWeight: p.voting_weight,
            abilities: p.role_abilities ? {
              witchHasAntidote: p.role_abilities.witch_has_antidote,
              witchHasPoison: p.role_abilities.witch_has_poison,
              hunterCanShoot: p.role_abilities.hunter_can_shoot,
            } : undefined,
          })),
          events: eventsData.map((e: any): GameEvent => ({
            id: e.id,
            timestamp: e.timestamp,
            day: e.day_count,
            phase: convertPhase(e.phase),
            category: convertEventType(e.type || e.event_type),
            content: e.content,
            actorId: e.actor_id,
            actorName: e.actor_name,
            targetId: e.target_id,
            targetName: e.target_name,
          })),
          winner: gameData.winner ? (gameData.winner === 'werewolf' ? 'werewolf' : 'villager' as const) : undefined,
          isRunning: gameData.is_running,
        };

        setGameState(gameState);
        setConnectionStatus('connected');

        // 记录最后一个事件 ID
        if (gameState.events.length > 0) {
          lastEventIdRef.current = gameState.events[gameState.events.length - 1].id;
        }
      } catch (err) {
        console.error('初始数据获取失败:', err);
        setConnectionStatus('error');
      }
    })();

    // 快速事件轮询（2秒）- 只获取事件
    eventIntervalRef.current = setInterval(async () => {
      if (!roomId || !isActiveRef.current) return;

      try {
        const eventsData = await getGameEvents(roomId) as any[];

        // 检查是否有新的事件
        const latestEventId = eventsData.length > 0 ? eventsData[eventsData.length - 1].id : null;
        if (latestEventId === lastEventIdRef.current) {
          return; // 没有新事件，跳过更新
        }

        // 从事件数据中推断游戏状态
        const latestPhaseEvent = eventsData
          .filter((e: any) => e.type === 'phase_change' || e.type === 'game_start' || e.type === 'game_end')
          .sort((a: any, b: any) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())[0];

        const currentPhase = latestPhaseEvent ? convertPhase(latestPhaseEvent.phase) : 'day_discussion';
        const currentDay = Math.max(...eventsData.map((e: any) => e.day_count), 1);
        const hasGameEndEvent = eventsData.some((e: any) => e.type === 'game_end');

        // 更新事件和状态
        setGameState((prevState: GameState | null) => {
          if (!prevState) return prevState;
          return {
            ...prevState,
            day: currentDay,
            phase: currentPhase,
            isRunning: !hasGameEndEvent,
            events: eventsData.map((e: any): GameEvent => ({
              id: e.id,
              timestamp: e.timestamp,
              day: e.day_count,
              phase: convertPhase(e.phase),
              category: convertEventType(e.type || e.event_type),
              content: e.content,
              actorId: e.actor_id,
              actorName: e.actor_name,
              targetId: e.target_id,
              targetName: e.target_name,
            }))
          };
        });

        lastEventIdRef.current = latestEventId;
      } catch (err) {
        console.warn('事件轮询失败:', err);
      }
    }, interval);

    // 低频率完整状态更新（30秒）- 获取玩家信息等
    stateIntervalRef.current = setInterval(async () => {
      if (!roomId || !isActiveRef.current) return;

      try {
        const gameData = await getFullGameData(roomId);
        setGameState((prevState: GameState| null) => {
          if (!prevState) return prevState;
          return {
            ...prevState,
            id: gameData.session_id,
            roomId: gameData.room_id,
            players: gameData.players.map((p: any): Player => ({
              id: p.id,
              name: p.name,
              position: p.position,
              role: p.role,
              status: p.status === 'alive' ? 'alive' : 'dead',
              isSheriff: p.is_sheriff,
              votingWeight: p.voting_weight,
              abilities: p.role_abilities ? {
                witchHasAntidote: p.role_abilities.witch_has_antidote,
                witchHasPoison: p.role_abilities.witch_has_poison,
                hunterCanShoot: p.role_abilities.hunter_can_shoot,
              } : undefined,
            })),
            winner: gameData.winner ? (gameData.winner === 'werewolf' ? 'werewolf' : 'villager' as const) : undefined,
          };
        });
        setConnectionStatus('connected');
      } catch (err) {
        console.warn('状态更新失败:', err);
      }
    }, 30000);

    console.log(`✅ 轮询已启动: 事件 ${interval}ms, 状态 30s`);
  }, [interval, roomId]);

  const stopPolling = useCallback(() => {
    if (eventIntervalRef.current) {
      clearInterval(eventIntervalRef.current);
      eventIntervalRef.current = null;
    }
    if (stateIntervalRef.current) {
      clearInterval(stateIntervalRef.current);
      stateIntervalRef.current = null;
    }
    console.log('🛑 轮询已停止');
  }, []);

  useEffect(() => {
    if (roomId) {
      startPolling();
    }
    return () => {
      stopPolling();

      // 只有在页面真正卸载时才清理游戏
      if (roomId && !isActiveRef.current) {
        console.log('页面卸载，清理游戏资源:', roomId);
        cleanupGame(roomId, true).catch(error => {
          console.warn('清理游戏资源失败:', error);
        });
      }
    };
  }, [roomId, startPolling, stopPolling]);

  return { startPolling, stopPolling };
};