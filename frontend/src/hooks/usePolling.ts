import { useEffect, useRef, useCallback } from 'react';
import { useGameStore } from '@/store/gameStore';
import { GameEvent, GameState, Player } from '@/types/game';
import { getFullGameData, getGameEvents, cleanupGame } from '@/services/api';
import { None } from 'framer-motion';

export function convertPhase(phase: string): GameState['phase'] {
  const phaseMap: Record<string, GameState['phase']> = {
    'night': 'night',
    'sheriff_election': 'sheriff_election',
    'day_discussion': 'day_discussion',
    'voting': 'voting',
    'game_over': 'game_over',
  };
  return phaseMap[phase] || 'day_discussion';
}

export function convertEventType(type: string): GameEvent['category'] {
  const typeMap: Record<string, GameEvent['category']> = {
    'game_start': 'MODERATOR',
    'game_end': 'MODERATOR',
    'phase_change': 'MODERATOR',
    'werewolf_kill': 'ACTION',
    'werewolf_discuss': 'ACTION',
    'sheriff_election_start': 'MODERATOR',
    'sheriff_candidacy': 'ACTION',
    'sheriff_speech': 'ACTION',
    'sheriff_elected': 'MODERATOR',
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

  const { setGameState, setConnectionStatus } = useGameStore();

  const startPolling = useCallback(() => {
    // 停止现有轮询
    stopPolling();

    // 立即获取一次完整数据
    (async () => {
      if (!roomId) return;

      try {
        // 首次获取完整数据
        console.log('🔄 获取游戏数据:', roomId);
        const gameData = await getFullGameData(roomId);
        console.log('✅ 游戏数据获取成功:', gameData);

        console.log('🔄 获取事件数据:', roomId);
        const eventsData = await getGameEvents(roomId);
        console.log('✅ 事件数据获取成功, 数量:', eventsData.length);

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

        console.log('🎮 设置游戏状态:', gameState);
        setGameState(gameState);
        setConnectionStatus('connected');

        // 记录最后一个事件 ID
        if (gameState.events.length > 0) {
          lastEventIdRef.current = gameState.events[gameState.events.length - 1].id;
        }
        console.log('✅ 初始数据设置完成');
      } catch (err) {
        console.error('❌ 初始数据获取失败:', err);
        setConnectionStatus('error');
      }
    })();

    // 快速事件轮询（2秒）- 只获取事件
    eventIntervalRef.current = setInterval(async () => {
      if (!roomId) return;

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
        setGameState((prevState: GameState| null) => {
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
      if (!roomId) return;

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