import { useEffect, useRef, useCallback } from 'react';
import { useGameStore } from '@/store/gameStore';
import { GameState, GameEvent } from '@/types/game';

interface WebSocketMessage {
  type: string;
  data: unknown;
}

// 后端地址配置
const WS_BASE_URL = 'ws://localhost:8001';

export const useWebSocket = (gameId: string | null) => {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  
  const { 
    setGameState,
    addEvent,
    addEvents,
    updatePlayer,
    setConnectionStatus 
  } = useGameStore();

  const handleMessage = useCallback((message: WebSocketMessage) => {
    console.log('WS Message:', message.type, message.data);
    
    switch (message.type) {
      case 'GAME_STATE':
      case 'game_state':
        setGameState(message.data as GameState);
        break;
      
      case 'GAME_EVENT':
      case 'game_event':
        addEvent(message.data as GameEvent);
        break;
      
      case 'GAME_EVENTS':
      case 'game_events':
        addEvents(message.data as GameEvent[]);
        break;
      
      case 'PLAYER_UPDATE':
      case 'player_update':
        const playerData = message.data as { playerId: string; updates: unknown };
        updatePlayer(playerData.playerId, playerData.updates as Parameters<typeof updatePlayer>[1]);
        break;
      
      case 'PHASE_CHANGE':
      case 'phase_change':
        const phaseData = message.data as { phase: string; day: number };
        useGameStore.getState().updateGameState({ 
          phase: phaseData.phase as GameState['phase'],
          day: phaseData.day 
        });
        break;
      
      default:
        console.log('Unknown message type:', message.type, message.data);
    }
  }, [setGameState, addEvent, addEvents, updatePlayer]);

  const connect = useCallback(() => {
    if (!gameId) return;

    setConnectionStatus('connecting');

    // 直接连接后端 WebSocket
    const wsUrl = `${WS_BASE_URL}/ws/game/${gameId}`;
    console.log('Connecting to WebSocket:', wsUrl);
    
    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected to', wsUrl);
        setConnectionStatus('connected');
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          handleMessage(message);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err, event.data);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
      };

      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setConnectionStatus('disconnected');
        
        // 自动重连（如果不是主动关闭）
        if (event.code !== 1000) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...');
            connect();
          }, 3000);
        }
      };
    } catch (err) {
      console.error('Failed to connect WebSocket:', err);
      setConnectionStatus('error');
    }
  }, [gameId, setConnectionStatus, handleMessage]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnect');
      wsRef.current = null;
    }
    setConnectionStatus('disconnected');
  }, [setConnectionStatus]);

  const sendMessage = useCallback((type: string, data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const message = JSON.stringify({ type, data });
      console.log('Sending WS message:', message);
      wsRef.current.send(message);
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  }, []);

  useEffect(() => {
    if (gameId) {
      connect();
    }
    return () => disconnect();
  }, [gameId, connect, disconnect]);

  return { sendMessage, disconnect, reconnect: connect };
};

