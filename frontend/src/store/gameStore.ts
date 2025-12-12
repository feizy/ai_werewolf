import { create } from 'zustand';
import { GameState, GameEvent, Player, EventCategory, Room, RoomPlayer, LLMConfig, ViewType } from '@/types/game';

interface GameStore {
  // 房间状态
  room: Room | null;
  currentView: ViewType;

  // 游戏状态
  gameState: GameState | null;
  connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error';
  selectedPlayerId: string | null;
  eventFilters: EventCategory[];
  autoScroll: boolean;

  // Actions - 房间管理
  setRoom: (room: Room) => void;
  updateRoom: (partial: Partial<Room>) => void;
  addPlayerToRoom: (player: RoomPlayer) => void;
  updateRoomPlayer: (playerId: string, updates: Partial<RoomPlayer>) => void;
  setCurrentView: (view: ViewType) => void;

  // Actions - 游戏管理
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
  room: null,
  currentView: 'home' as const,
  gameState: null,
  connectionStatus: 'disconnected' as const,
  selectedPlayerId: null,
  eventFilters: [] as EventCategory[],
  autoScroll: true,
};

export const useGameStore = create<GameStore>((set, get) => ({
  ...initialState,

  // 房间管理
  setRoom: (room) => set({ room }),
  updateRoom: (partial) => set((state) => ({
    room: state.room ? { ...state.room, ...partial } : null
  })),
  addPlayerToRoom: (player) => set((state) => ({
    room: state.room ? {
      ...state.room,
      players: [...state.room.players, player],
      currentPlayers: state.room.currentPlayers + 1,
      canStartGame: state.room.currentPlayers + 1 >= 4
    } : null
  })),
  updateRoomPlayer: (playerId, updates) => set((state) => ({
    room: state.room ? {
      ...state.room,
      players: state.room.players.map(p =>
        p.id === playerId ? { ...p, ...updates } : p
      )
    } : null
  })),
  setCurrentView: (currentView) => set({ currentView }),

  // 游戏管理
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

  toggleEventFilter: (category) => set((state) => {
    // 如果点击"全部"，清除所有过滤器
    if (category === 'ALL' as any) {
      return { eventFilters: [] };
    }

    // 正常的类别切换逻辑
    const newFilters = state.eventFilters.includes(category)
      ? state.eventFilters.filter(c => c !== category)
      : [...state.eventFilters, category];

    return { eventFilters: newFilters };
  }),

  setAutoScroll: (autoScroll) => set({ autoScroll }),

  reset: () => set(initialState),
}));


