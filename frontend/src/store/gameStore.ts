import { create } from 'zustand';
import { GameState, GameEvent, Player, EventCategory } from '@/types/game';

interface GameStore {
  // 状态
  gameState: GameState | null;
  connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error';
  selectedPlayerId: string | null;
  eventFilters: EventCategory[];
  autoScroll: boolean;

  // Actions
  setGameState: (state: GameState) => void;
  updateGameState: (partial: Partial<GameState>) => void;
  addEvent: (event: GameEvent) => void;
  addEvents: (events: GameEvent[]) => void;
  updatePlayer: (playerId: string, updates: Partial<Player>) => void;
  setConnectionStatus: (status: 'disconnected' | 'connecting' | 'connected' | 'error') => void;
  setSelectedPlayerId: (playerId: string | null) => void;
  setEventFilters: (filters: EventCategory[]) => void;
  toggleEventFilter: (category: EventCategory) => void;
  setAutoScroll: (autoScroll: boolean) => void;
  reset: () => void;
}

const initialState = {
  gameState: null,
  connectionStatus: 'disconnected' as const,
  selectedPlayerId: null,
  eventFilters: [] as EventCategory[],
  autoScroll: true,
};

export const useGameStore = create<GameStore>((set, get) => ({
  ...initialState,

  setGameState: (gameState) => set({ gameState }),

  updateGameState: (partial) => set((state) => ({
    gameState: state.gameState ? { ...state.gameState, ...partial } : null
  })),

  addEvent: (event) => set((state) => ({
    gameState: state.gameState ? {
      ...state.gameState,
      events: [...state.gameState.events, event]
    } : null
  })),

  addEvents: (events) => set((state) => ({
    gameState: state.gameState ? {
      ...state.gameState,
      events: [...state.gameState.events, ...events]
    } : null
  })),

  updatePlayer: (playerId, updates) => set((state) => ({
    gameState: state.gameState ? {
      ...state.gameState,
      players: state.gameState.players.map(p => 
        p.id === playerId ? { ...p, ...updates } : p
      )
    } : null
  })),

  setConnectionStatus: (connectionStatus) => set({ connectionStatus }),

  setSelectedPlayerId: (selectedPlayerId) => set({ selectedPlayerId }),

  setEventFilters: (eventFilters) => set({ eventFilters }),

  toggleEventFilter: (category) => set((state) => ({
    eventFilters: state.eventFilters.includes(category)
      ? state.eventFilters.filter(c => c !== category)
      : [...state.eventFilters, category]
  })),

  setAutoScroll: (autoScroll) => set({ autoScroll }),

  reset: () => set(initialState),
}));


