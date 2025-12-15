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

        // 验证数据完整性
        if (!gameData || !eventsData) {
          throw new Error('游戏数据或事件数据为空');
        }

        console.log('📋 游戏原始数据:', {
          id: gameData.id,
          sessionId: gameData.session_id,
          roomId: gameData.room_id,
          dayCount: gameData.day_count,
          currentPhase: gameData.current_phase,
          playersCount: gameData.players?.length,
          eventsCount: eventsData.length
        });

        const gameState: GameState = {
          id: gameData.id || 'unknown',  // 修复：应该是 id 而不是 session_id
          roomId: gameData.room_id || roomId,
          day: gameData.day_count || 1,
          phase: gameData.current_phase === 'running' ? 'day_discussion' : convertPhase(gameData.current_phase || 'day_discussion'),
          players: (gameData.players || []).map((p: any): Player => ({
            id: p.id || 'unknown',
            name: p.name || 'Unknown',
            position: p.position || 0,
            role: p.role || 'villager',
            status: p.status === 'alive' ? 'alive' : 'dead',
            isSheriff: p.is_sheriff || false,
            votingWeight: p.voting_weight || 1,
            abilities: p.role_abilities ? {
              witchHasAntidote: p.role_abilities.witch_has_antidote,
              witchHasPoison: p.role_abilities.witch_has_poison,
              hunterCanShoot: p.role_abilities.hunter_can_shoot,
            } : undefined,
          })),
          events: (eventsData || []).map((e: any): GameEvent => ({
            id: e.id || 'unknown',
            timestamp: e.timestamp || new Date().toISOString(),
            day: e.day_count || 1,
            phase: convertPhase(e.phase || 'day_discussion'),
            category: convertEventType(e.type || e.event_type || 'system'),
            content: e.content || 'Unknown event',
            actorId: e.actor_id,
            actorName: e.actor_name,
            targetId: e.target_id,
            targetName: e.target_name,
          })),
          winner: gameData.winner ? (gameData.winner === 'werewolf' ? 'werewolf' : 'villager' as const) : undefined,
          isRunning: gameData.is_running || false,
        };

        console.log('🎮 设置游戏状态:', {
          id: gameState.id,
          phase: gameState.phase,
          day: gameState.day,
          isRunning: gameState.isRunning,
          playerCount: gameState.players.length,
          eventCount: gameState.events.length
        });

        // 确保 gameState 设置成功
        setGameState(gameState);

        // 验证设置是否成功
        setTimeout(() => {
          const currentState = useGameStore.getState().gameState;
          console.log('🔍 验证 gameState 设置:', {
            hasState: !!currentState,
            id: currentState?.id,
            idMatch: currentState?.id === gameState.id
          });
        }, 100);
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

    // 快速事件轮询（2秒）- 使用 Zustand 直接更新避免并发问题
    eventIntervalRef.current = setInterval(async () => {
      if (!roomId) return;

      try {
        const eventsData = await getGameEvents(roomId) as any[];

        // 检查是否有新的事件
        const latestEventId = eventsData.length > 0 ? eventsData[eventsData.length - 1].id : null;
        if (latestEventId === lastEventIdRef.current) {
          return; // 没有新事件，跳过更新
        }

        console.log('📝 发现新事件，数量:', eventsData.length);

        // 转换事件数据
        const newEvents = eventsData.map((e: any): GameEvent => ({
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
        }));

        // 使用 Zustand 的直接状态更新，避免 React 并发问题
        const { addEvents, updateGameState } = useGameStore.getState();

        if (newEvents.length > 0) {
          // 先添加新事件
          addEvents(newEvents);
          console.log('✅ 添加了', newEvents.length, '个新事件');

          // 统计 WEREWOLF_DISCUSS 事件
          const werewolfDiscussEvents = newEvents.filter(e =>
            e.category === 'ACTION' && e.content.includes('建议击杀')
          );
          if (werewolfDiscussEvents.length > 0) {
            console.log('🐺 发现狼人建议事件:', werewolfDiscussEvents.length, '个');
          }
        }

        lastEventIdRef.current = latestEventId;
      } catch (err) {
        console.error('❌ 事件轮询失败:', err);
        // 不要重置 gameState，只是记录错误
      }
    }, interval);

    // 低频率完整状态更新（30秒）- 暂时禁用来排除问题
    // stateIntervalRef.current = setInterval(async () => {
    //   if (!roomId) return;

    //   try {
    //     const gameData = await getFullGameData(roomId);
    //     console.log('🔄 状态更新轮询，获取到的数据:', {
    //       id: gameData.id,
    //       phase: gameData.current_phase,
    //       playerCount: gameData.players?.length
    //     });

    //     setGameState((prevState: GameState| null) => {
    //       if (!prevState) {
    //         console.log('⚠️ 状态更新轮询：prevState 为 null，跳过');
    //         return null;
    //       }
    //       return {
    //         ...prevState,
    //         id: gameData.id,
    //         roomId: gameData.room_id,
    //         players: gameData.players.map((p: any): Player => ({
    //           id: p.id,
    //           name: p.name,
    //           position: p.position,
    //           role: p.role,
    //           status: p.status === 'alive' ? 'alive' : 'dead',
    //           isSheriff: p.is_sheriff,
    //           votingWeight: p.voting_weight,
    //           abilities: p.role_abilities ? {
    //             witchHasAntidote: p.role_abilities.witch_has_antidote,
    //             witchHasPoison: p.role_abilities.witch_has_poison,
    //             hunterCanShoot: p.role_abilities.hunter_can_shoot,
    //           } : undefined,
    //         })),
    //         winner: gameData.winner ? (gameData.winner === 'werewolf' ? 'werewolf' : 'villager' as const) : undefined,
    //       };
    //     });
    //     setConnectionStatus('connected');
    //   } catch (err) {
    //     console.error('❌ 状态更新失败:', err);
    //     // 不要重置 gameState，只是记录错误
    //   }
    // }, 30000);

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

      // 注意：不要在这里自动清理游戏资源
      // 让用户手动通过"退出房间"按钮来清理
      console.log('🛑 轮询清理完成');
    };
  }, [roomId, startPolling, stopPolling]);

  return { startPolling, stopPolling };
};