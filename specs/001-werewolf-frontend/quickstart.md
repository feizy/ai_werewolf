# Quickstart Guide: Werewolf Game Frontend

**Date**: 2025-12-01
**Purpose**: Rapid development setup and initial implementation guidance for Werewolf game frontend

## Prerequisites

### Development Environment
- Node.js 18+ and npm 9+
- Modern web browser with WebSocket support
- Git client
- Code editor with TypeScript support (VS Code recommended)

### Required Dependencies
```bash
# Core dependencies
npm install react@18 react-dom@18
npm install typescript@5
npm install @types/react @types/react-dom

# State management
npm install zustand

# Real-time communication
npm install socket.io-client

# UI and styling
npm install styled-components
npm install @types/styled-components
npm install framer-motion

# Performance optimizations
npm install react-query
npm install react-virtualized
npm install react-window

# Development tools
npm install -D vite @vitejs/plugin-react
npm install -D @types/node
npm install -D eslint @typescript-eslint/eslint-plugin
npm install -D prettier eslint-config-prettier

# Testing
npm install -D jest @testing-library/react @testing-library/jest-dom
npm install -D @testing-library/user-event
npm install -D jest-environment-jsdom

# E2E testing
npm install -D playwright @playwright/test
```

## Project Setup

### 1. Initialize Vite Project
```bash
# Create new Vite + React + TypeScript project
npm create vite@latest werewolf-frontend -- --template react-ts
cd werewolf-frontend

# Install additional dependencies
npm install zustand socket.io-client styled-components framer-motion react-query react-virtualized

# Install dev dependencies
npm install -D @testing-library/react @testing-library/jest-dom @testing-library/user-event jest-environment-jsdom
```

### 2. Configure TypeScript
```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@/components/*": ["src/components/*"],
      "@/hooks/*": ["src/hooks/*"],
      "@/store/*": ["src/store/*"],
      "@/types/*": ["src/types/*"],
      "@/utils/*": ["src/utils/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### 3. Vite Configuration
```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@/components': path.resolve(__dirname, './src/components'),
      '@/hooks': path.resolve(__dirname, './src/hooks'),
      '@/store': path.resolve(__dirname, './src/store'),
      '@/types': path.resolve(__dirname, './src/types'),
      '@/utils': path.resolve(__dirname, './src/utils')
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/socket.io': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true
      }
    }
  }
})
```

## Core Implementation Steps

### 1. WebSocket Connection Setup

```typescript
// src/hooks/useWebSocket.ts
import { useEffect, useRef, useState } from 'react'
import { io, Socket } from 'socket.io-client'
import { GameState, WebSocketMessage } from '@/types/game'

export const useWebSocket = (gameId: string, playerId: string, token: string) => {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [gameState, setGameState] = useState<GameState | null>(null)
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected')
  const socketRef = useRef<Socket | null>(null)

  useEffect(() => {
    const newSocket = io('/game', {
      auth: { gameId, playerId, token },
      transports: ['websocket']
    })

    newSocket.on('connect', () => {
      setConnectionStatus('connected')
      setSocket(newSocket)
      socketRef.current = newSocket
    })

    newSocket.on('disconnect', () => {
      setConnectionStatus('disconnected')
    })

    newSocket.on('GAME_STATE_UPDATE', (message: WebSocketMessage) => {
      setGameState(message.payload.gameState)
    })

    newSocket.on('PLAYER_EVENT', (message: WebSocketMessage) => {
      // Handle player events
    })

    newSocket.on('PHASE_CHANGE', (message: WebSocketMessage) => {
      // Handle phase changes
    })

    newSocket.on('error', (error) => {
      setConnectionStatus('error')
      console.error('WebSocket error:', error)
    })

    return () => {
      newSocket.close()
    }
  }, [gameId, playerId, token])

  const sendMessage = useCallback((type: string, payload: any) => {
    if (socketRef.current) {
      socketRef.current.emit(type, payload)
    }
  }, [])

  return { socket, gameState, connectionStatus, sendMessage }
}
```

### 2. Game State Management

```typescript
// src/store/gameStore.ts
import { create } from 'zustand'
import { GameState, Player, GameEvent } from '@/types/game'

interface GameStore {
  gameState: GameState | null
  currentUserId: string | null
  selectedPlayerId: string | null
  hoveredPlayerId: string | null
  eventFilters: {
    categories: string[]
    playerIds: string[]
    searchText: string
  }

  // Actions
  setGameState: (gameState: GameState) => void
  setCurrentUserId: (userId: string) => void
  setSelectedPlayerId: (playerId: string | null) => void
  setHoveredPlayerId: (playerId: string | null) => void
  updateEventFilters: (filters: Partial<typeof this.eventFilters>) => void
  addGameEvent: (event: GameEvent) => void
}

export const useGameStore = create<GameStore>((set, get) => ({
  gameState: null,
  currentUserId: null,
  selectedPlayerId: null,
  hoveredPlayerId: null,
  eventFilters: {
    categories: [],
    playerIds: [],
    searchText: ''
  },

  setGameState: (gameState) => set({ gameState }),
  setCurrentUserId: (currentUserId) => set({ currentUserId }),
  setSelectedPlayerId: (selectedPlayerId) => set({ selectedPlayerId }),
  setHoveredPlayerId: (hoveredPlayerId) => set({ hoveredPlayerId }),
  updateEventFilters: (filters) => set((state) => ({
    eventFilters: { ...state.eventFilters, ...filters }
  })),
  addGameEvent: (event) => set((state) => ({
    gameState: state.gameState ? {
      ...state.gameState,
      events: [...state.gameState.events, event]
    } : null
  }))
}))
```

### 3. Basic Game Table Component

```typescript
// src/components/GameTable/PlayerCircle.tsx
import React, { useMemo } from 'react'
import styled from 'styled-components'
import { motion } from 'framer-motion'
import { PlayerCard } from './PlayerCard'
import { Player } from '@/types/game'

interface PlayerCircleProps {
  players: Player[]
  selectedPlayerId?: string | null
  hoveredPlayerId?: string | null
  onPlayerClick?: (playerId: string) => void
  onPlayerHover?: (playerId: string | null) => void
}

const CircleContainer = styled.div<{ radius: number }>`
  position: relative;
  width: ${({ radius }) => radius * 2}px;
  height: ${({ radius }) => radius * 2}px;
  margin: 0 auto;
`

export const PlayerCircle: React.FC<PlayerCircleProps> = ({
  players,
  selectedPlayerId,
  hoveredPlayerId,
  onPlayerClick,
  onPlayerHover
}) => {
  const radius = 300
  const angleStep = (2 * Math.PI) / players.length

  const playerPositions = useMemo(() => {
    return players.map((player, index) => {
      const angle = index * angleStep - Math.PI / 2
      const x = Math.cos(angle) * radius
      const y = Math.sin(angle) * radius
      return { player, x, y, index }
    })
  }, [players, radius, angleStep])

  return (
    <CircleContainer radius={radius}>
      {playerPositions.map(({ player, x, y, index }) => (
        <motion.div
          key={player.id}
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: index * 0.1 }}
          style={{
            position: 'absolute',
            left: `${radius + x}px`,
            top: `${radius + y}px`,
            transform: 'translate(-50%, -50%)'
          }}
        >
          <PlayerCard
            player={player}
            isSelected={selectedPlayerId === player.id}
            isHovered={hoveredPlayerId === player.id}
            onClick={() => onPlayerClick?.(player.id)}
            onHover={(isHovered) => onPlayerHover?.(isHovered ? player.id : null)}
          />
        </motion.div>
      ))}
    </CircleContainer>
  )
}
```

### 4. Event Log Component

```typescript
// src/components/EventLog/EventList.tsx
import React, { useMemo } from 'react'
import { FixedSizeList as List } from 'react-window'
import { GameEvent } from '@/types/game'
import { EventItem } from './EventItem'

interface EventListProps {
  events: GameEvent[]
  maxHeight: number
  itemHeight: number
  onEventClick?: (eventId: string) => void
}

export const EventList: React.FC<EventListProps> = ({
  events,
  maxHeight,
  itemHeight,
  onEventClick
}) => {
  const Row = ({ index, style }: { index: number, style: React.CSSProperties }) => (
    <div style={style}>
      <EventItem
        event={events[index]}
        onClick={() => onEventClick?.(events[index].id)}
      />
    </div>
  )

  return (
    <List
      height={maxHeight}
      itemCount={events.length}
      itemSize={itemHeight}
      width="100%"
    >
      {Row}
    </List>
  )
}
```

### 5. Main App Component

```typescript
// src/App.tsx
import React from 'react'
import styled, { ThemeProvider, createGlobalStyle } from 'styled-components'
import { GameTable } from '@/components/GameTable'
import { EventLog } from '@/components/EventLog'
import { useGameStore } from '@/store/gameStore'
import { useWebSocket } from '@/hooks/useWebSocket'

const AppContainer = styled.div`
  min-height: 100vh;
  background: #1a1a2e;
  color: #ffffff;
  font-family: 'Inter', sans-serif;
`

const GameLayout = styled.div`
  display: flex;
  height: 100vh;
`

const GameSection = styled.div`
  flex: 1;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
`

const LogSection = styled.div`
  width: 400px;
  background: #2d2d44;
  border-left: 1px solid #3d3d5c;
  padding: 1rem;
  overflow: hidden;
  display: flex;
  flex-direction: column;
`

const GlobalStyle = createGlobalStyle`
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  body {
    margin: 0;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #1a1a2e;
  }
`

const theme = {
  colors: {
    primary: #8b5cf6,
    secondary: #6366f1,
    success: #10b981,
    warning: #f59e0b,
    error: #ef4444,
    background: #1a1a2e,
    surface: #2d2d44,
    text: #ffffff
  }
}

export const App: React.FC = () => {
  const { gameState, selectedPlayerId, setSelectedPlayerId } = useGameStore()

  // Mock WebSocket connection - replace with real implementation
  const { connectionStatus } = useWebSocket('mock-game-id', 'mock-player-id', 'mock-token')

  if (!gameState) {
    return <div>Loading game...</div>
  }

  return (
    <ThemeProvider theme={theme}>
      <GlobalStyle />
      <AppContainer>
        <GameLayout>
          <GameSection>
            <GameTable
              gameState={gameState}
              selectedPlayerId={selectedPlayerId}
              onPlayerClick={setSelectedPlayerId}
            />
          </GameSection>
          <LogSection>
            <EventLog
              events={gameState.events}
              filters={{
                categories: [],
                playerIds: [],
                searchText: ''
              }}
            />
          </LogSection>
        </GameLayout>
      </AppContainer>
    </ThemeProvider>
  )
}
```

## Development Workflow

### 1. Component Development Pattern

```bash
# Create new component directory
mkdir src/components/NewFeature
cd src/components/NewFeature

# Create component files
touch NewFeature.tsx NewFeature.styles.ts NewFeature.test.tsx index.ts
```

### 2. Component Structure Template

```typescript
// src/components/NewFeature/NewFeature.tsx
import React from 'react'
import styled from 'styled-components'
import { NewFeatureProps } from './types'

const Container = styled.div`
  /* Component styles */
`

export const NewFeature: React.FC<NewFeatureProps> = ({
  prop1,
  prop2,
  onAction
}) => {
  return (
    <Container>
      {/* Component implementation */}
    </Container>
  )
}
```

### 3. Testing Setup

```typescript
// src/components/NewFeature/NewFeature.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { NewFeature } from './NewFeature'

describe('NewFeature', () => {
  it('renders correctly', () => {
    render(<NewFeature prop1="value" prop2={false} />)
    expect(screen.getByText('expected text')).toBeInTheDocument()
  })

  it('handles interactions', () => {
    const onAction = jest.fn()
    render(<NewFeature prop1="value" onAction={onAction} />)

    fireEvent.click(screen.getByRole('button'))
    expect(onAction).toHaveBeenCalled()
  })
})
```

### 4. Development Server

```bash
# Start development server
npm run dev

# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Build for production
npm run build

# Preview production build
npm run preview
```

## Performance Optimizations

### 1. React.memo for Component Optimization

```typescript
export const OptimizedComponent = React.memo<ComponentProps>((props) => {
  return <div>{/* component content */}</div>
}, (prevProps, nextProps) => {
  return prevProps.id === nextProps.id && prevProps.status === nextProps.status
})
```

### 2. useMemo for Computed Values

```typescript
const filteredEvents = useMemo(() => {
  return events.filter(event =>
    filters.categories.includes(event.category) &&
    filters.playerIds.some(id => event.participants.includes(id))
  )
}, [events, filters])
```

### 3. useCallback for Event Handlers

```typescript
const handlePlayerClick = useCallback((playerId: string) => {
  setSelectedPlayerId(playerId)
  onPlayerInteraction?.(playerId)
}, [onPlayerInteraction])
```

## Common Implementation Issues

### WebSocket Connection Issues
- Ensure WebSocket server is running on correct port
- Check CORS configuration
- Verify authentication tokens
- Handle reconnection gracefully

### Performance Issues
- Use React.memo for expensive components
- Implement virtual scrolling for large lists
- Debounce rapid state updates
- Optimize re-renders with proper dependencies

### State Management Issues
- Avoid deep mutations in state
- Use immutable update patterns
- Implement proper error boundaries
- Handle loading states consistently

## Next Steps

1. **Implement PlayerCard component** with role indicators and animations
2. **Create EventLog filtering system** with category and player filters
3. **Add SheriffElection components** for nomination and voting
4. **Implement ReplayMode with day selection and timeline**
5. **Add connection status indicators** and error handling
6. **Create comprehensive test suite** for all components
7. **Set up CI/CD pipeline** for automated testing and deployment

This quickstart provides the foundation for implementing the Werewolf game frontend with all required features and performance optimizations.