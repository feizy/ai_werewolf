import { useEffect, useRef, useCallback } from 'react';
import { useGameStore } from '@/store/gameStore';
import { GameEvent, GameState, Player } from '@/types/game';
import { getFullGameData, getGameEvents } from '@/services/api';
import { cleanupGame } from '@/services/api';

// 轮询后端获取游戏状态（备选方案，当 WebSocket 不可用时使用）
const API_BASE = 'http://localhost:8001';

interface BackendGameState {
  id: string;
  room_id: string;
  day_count: number;
  current_phase: string;
  players: Array<{
    id: string;
    name: string;
    position: number;
    role?: string;
    status: string;
    is_sheriff: boolean;
    voting_weight: number;
    role_abilities?: {
      witch_has_antidote?: boolean;
      witch_has_poison?: boolean;
      hunter_can_shoot?: boolean;
    };
  }>;
  events: Array<{
    id: string;
    timestamp: string;
    day_count: number;
    phase: string;
    type: string;
    content: string;
    actor_id?: string;
    actor_name?: string;
    target_id?: string;
    target_name?: string;
  }>;
  sheriff_id?: string;
  winner?: string;
  is_running: boolean;
}

// 转换后端数据格式到前端格式
export function convertGameState(backend: BackendGameState): GameState {
  const players: Player[] = backend.players.map(p => ({
    id: p.id,
    name: p.name,
    position: p.position,
    role: p.role as Player['role'],
    status: p.status === 'alive' ? 'alive' : 'dead',
    isSheriff: p.is_sheriff,
    votingWeight: p.voting_weight,
    abilities: p.role_abilities ? {
      witchHasAntidote: p.role_abilities.witch_has_antidote,
      witchHasPoison: p.role_abilities.witch_has_poison,
      hunterCanShoot: p.role_abilities.hunter_can_shoot,
    } : undefined,
  }));

  const events: GameEvent[] = backend.events.map(e => ({
    id: e.id,
    timestamp: e.timestamp,
    day: e.day_count,
    phase: convertPhase(e.phase),
    category: convertEventType(e.type),
    content: e.content,
    actorId: e.actor_id,
    actorName: e.actor_name,
    targetId: e.target_id,
    targetName: e.target_name,
  }));

  return {
    id: backend.id,
    roomId: backend.room_id,
    day: backend.day_count,
    phase: convertPhase(backend.current_phase),
    players,
    events,
    sheriffId: backend.sheriff_id,
    winner: backend.winner as GameState['winner'],
    isRunning: backend.is_running,
  };
}

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
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastEventIdRef = useRef<string | null>(null);
  
  const { setGameState, addEvents, setConnectionStatus } = useGameStore();

  const fetchGameState = useCallback(async () => {
    if (!roomId) return;

    try {
      // 分别获取游戏状态和事件
      const [gameData, eventsData] = await Promise.all([
        getFullGameData(roomId),
        getGameEvents(roomId)
      ]);

      // 转换游戏状态数据格式
      const gameState = {
        id: gameData.session_id,
        roomId: gameData.room_id,
        day: gameData.day_count,
        phase: gameData.current_phase === 'running' ? 'day_discussion' : convertPhase(gameData.current_phase),
        players: gameData.players.map((p: any) => ({
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
        events: eventsData.map((e: any) => ({
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
        winner: gameData.winner ? (gameData.winner === 'werewolf' ? 'werewolf' : 'villager') as GameState['winner'] : undefined,
        isRunning: gameData.is_running,
      };

      setGameState(gameState);
      setConnectionStatus('connected');

      console.log(`✅ 获取到游戏状态，玩家数量: ${gameState.players.length}`);
      console.log(`✅ 获取到事件数据，事件数量: ${gameState.events.length}`);

      // 记录最后一个事件 ID
      if (gameState.events.length > 0) {
        lastEventIdRef.current = gameState.events[gameState.events.length - 1].id;
      }
    } catch (err) {
      console.error('Failed to fetch game data:', err);
      setConnectionStatus('error');
    }
  }, [roomId, setGameState, setConnectionStatus]);

  const startPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    // 立即获取一次
    fetchGameState();

    // 开始轮询
    intervalRef.current = setInterval(fetchGameState, interval);
  }, [fetchGameState, interval]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (roomId) {
      startPolling();
    }
    return () => {
      stopPolling();

      // 当组件卸载时，清理游戏资源（强制清理）
      if (roomId) {
        cleanupGame(roomId, true).catch(error => {
          console.warn('清理游戏资源失败:', error);
        });
      }
    };
  }, [roomId, startPolling, stopPolling]);

  return { fetchGameState, startPolling, stopPolling };
};


