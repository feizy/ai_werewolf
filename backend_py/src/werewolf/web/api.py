"""FastAPI REST API for werewolf game."""

from typing import Dict, List, Optional, Any
import asyncio
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
import uvicorn

from loguru import logger

from ..models.player import Player, Role
from ..models.room import GameRoom, RoomStatus
from ..models.game import GameSession, GamePhase, Team
from ..services.ai_manager import AIManager
from ..services.ai_game_engine import AIGameEngine


# Pydantic models for API
class PlayerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=20, description="Player name")
    ai_config: Optional[Dict[str, Any]] = Field(default=None, description="AI configuration")

class RoomCreate(BaseModel):
    player_name: str = Field(..., min_length=1, max_length=20)
    room_name: Optional[str] = Field(None, max_length=50)
    max_players: int = Field(9, ge=4, le=20)

class RoomResponse(BaseModel):
    room_id: str
    player_id: str
    room_name: Optional[str]
    creator_id: str
    current_players: int
    max_players: int
    status: str

class RoomJoin(BaseModel):
    room_id: str
    player_name: str = Field(..., min_length=1, max_length=20)
    ai_config: Optional[Dict[str, Any]] = Field(default=None, description="AI configuration")
    model_configuration: Optional[Dict[str, Any]] = Field(default=None, description="Model configuration")

class RoomStatusResponse(BaseModel):
    id: str
    name: Optional[str]
    creator_name: str
    current_players: int
    max_players: int
    status: str
    players: List[Dict[str, Any]]

class GameStart(BaseModel):
    player_id: str

class GameStateResponse(BaseModel):
    session_id: str
    room_id: str
    status: str
    current_phase: str
    day_count: int
    players: List[Dict[str, Any]]
    winner: Optional[str]
    start_time: str
    end_time: Optional[str]
    duration: float

class SystemStatus(BaseModel):
    server: Dict[str, Any]
    websocket: Dict[str, Any]
    agentscope: Dict[str, Any]
    memory: Dict[str, Any]
    timestamp: str

class ReplayRequest(BaseModel):
    game_id: str

class ReplayResponse(BaseModel):
    success: bool
    game_info: Optional[Dict[str, Any]]
    error: Optional[str]

class ReplayDayRequest(BaseModel):
    game_id: str
    day_number: int

class ReplayDayResponse(BaseModel):
    day_number: int
    player_states: List[Dict[str, Any]]
    game_state: Dict[str, Any]
    available_events: List[Dict[str, Any]]

# Security
security = HTTPBearer(auto_error=False)


class WerewolfAPI:
    """FastAPI application for werewolf game."""

    def __init__(self):
        self.app = FastAPI(
            title="AI Werewolf Game API",
            description="REST API for AI-powered werewolf game with AgentScope integration",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )

        self.rooms: Dict[str, GameRoom] = {}
        self.game_engines: Dict[str, AIGameEngine] = {}
        self.ai_manager: Optional[AIManager] = None
        
        self._setup_middleware()
        self._setup_routes()
        self._setup_exception_handlers()

    def _setup_middleware(self) -> None:
        """Setup FastAPI middleware."""
        # CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000", "http://localhost:3001"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Compression
        
    def _setup_routes(self) -> None:
        """Setup API routes."""
        # Health check
        @self.app.get("/health", response_model=Dict[str, Any])
        async def health_check():
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "uptime": asyncio.get_event_loop().time(),
                "version": "1.0.0"
            }

        # Room management
        @self.app.get("/rooms", response_model=List[Dict[str, Any]])
        async def get_rooms():
            """Get all rooms."""
            return [room.get_summary() for room in self.rooms.values()]

        @self.app.get("/rooms/{room_id}", response_model=Dict[str, Any])
        async def get_room(room_id: str):
            """Get room by ID."""
            room = self.rooms.get(room_id)
            if not room:
                raise HTTPException(status_code=404, detail="Room not found")
            return room.get_summary()

        @self.app.post("/rooms", response_model=RoomResponse)
        async def create_room(room_data: RoomCreate):
            """Create new room."""
            try:
                # Create room with creator
                room = GameRoom.create_room(
                    creator_name=room_data.player_name,
                    room_name=room_data.room_name,
                    max_players=room_data.max_players,
                    creator_id=f"creator-{datetime.now().timestamp()}"
                )

                self.rooms[room.id] = room

                return RoomResponse(
                    room_id=room.id,
                    player_id=room.creator_id,
                    room_name=room.name,
                    creator_id=room.creator_id,
                    current_players=room.current_players,
                    max_players=room.max_players,
                    status=room.status.value
                )

            except Exception as e:
                logger.error(f"Error creating room: {e}")
                raise HTTPException(status_code=500, detail="Failed to create room")

        @self.app.post("/rooms/{room_id}/join", response_model=RoomStatusResponse)
        async def join_room(room_id: str, join_data: RoomJoin):
            """Join existing room."""
            room = self.rooms.get(room_id)
            if not room:
                raise HTTPException(status_code=404, detail="Room not found")

            if room.is_full:
                raise HTTPException(status_code=400, detail="Room is full")

            if room.status != RoomStatus.WAITING:
                raise HTTPException(status_code=400, detail="Game is already in progress")

            try:
                # Create new player
                player = Player.create_ai_player(
                    name=join_data.player_name,
                    room_id=room_id,
                    position=room.current_players + 1,
                    ai_config=join_data.ai_config,
                    model_config=join_data.model_configuration
                )

                if not room.add_player(player):
                    raise HTTPException(status_code=400, detail="Failed to join room")

                return RoomStatusResponse(
                    id=room.id,
                    name=room.name,
                    creator_name=room.get_player(room.creator_id).name if room.get_player(room.creator_id) else "Unknown",
                    current_players=room.current_players,
                    max_players=room.max_players,
                    status=room.status.value,
                    players=[{
                "id": p.id,
                "name": p.name,
                "room_id": p.room_id,
                "role": p.role.value if p.role else None,
                "status": p.status.value,
                "position": p.position,
                "connection_state": p.connection_state,
                "joined_at": p.joined_at,
                "last_active_at": p.last_active_at,
                "voting_weight": p.voting_weight,
                "is_alive": p.is_alive,
                "team": p.team.value if p.team else None
            } for p in room.players]
                )

            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Error joining room: {e}")
                raise HTTPException(status_code=500, detail="Failed to join room")

        # Game management
        @self.app.get("/games/{game_id}", response_model=Dict[str, Any])
        async def get_game(game_id: str):
            """Get game information."""
            # Find game engine
            game_engine = None
            for engine in self.game_engines.values():
                if engine.get_session() and engine.get_session().id == game_id:
                    game_engine = engine
                    break

            if not game_engine:
                raise HTTPException(status_code=404, detail="Game not found")

            return game_engine.get_session().to_dict()

        @self.app.get("/games/{game_id}/state", response_model=GameStateResponse)
        async def get_game_state(game_id: str):
            """Get current game state."""
            game_engine = None
            for engine in self.game_engines.values():
                if engine.get_session() and engine.get_session().id == game_id:
                    game_engine = engine
                    break

            if not game_engine:
                raise HTTPException(status_code=404, detail="Game not found")

            return game_engine.get_game_summary()

        @self.app.post("/games/{game_id}/start")
        async def start_game(game_id: str, game_data: GameStart):
            """Start game in room."""
            # Find room by game_id (game_id should be room_id)
            room = self.rooms.get(game_id)
            if not room:
                raise HTTPException(status_code=404, detail="Room not found")

            # Check if room can start game
            if not room.can_start_game:
                raise HTTPException(status_code=400, detail="Cannot start game: room not ready")

            # Find or create game engine
            game_engine = self.game_engines.get(game_id)
            if not game_engine:
                # Create game engine for this room
                from ..services.ai_game_engine import AIGameEngine
                from ..models.events import EventService

                event_service = EventService()
                game_engine = AIGameEngine(room, event_service)
                self.game_engines[game_id] = game_engine
                logger.info(f"Created game engine for room {game_id}")

            try:
                # Start game
                session = await game_engine.start_game()

                return {
                    "game_id": session.id,
                    "status": "started",
                    "message": "Game started successfully"
                }

            except Exception as e:
                logger.error(f"Error starting game: {e}")
                raise HTTPException(status_code=500, detail="Failed to start game")

        # Replay system
        @self.app.post("/replays", response_model=ReplayResponse)
        async def access_replay(replay_data: ReplayRequest):
            """Access game replay."""
            # Find game
            game_session = None
            for engine in self.game_engines.values():
                session = engine.get_session()
                if session and session.id == replay_data.game_id:
                    game_session = session
                    break

            if not game_session:
                return ReplayResponse(
                    success=False,
                    error="Game not found"
                )

            return ReplayResponse(
                success=True,
                game_info={
                    "game_id": game_session.id,
                    "duration": int(game_session.get_summary()["duration"]),
                    "total_days": game_session.day_count,
                    "winner": game_session.winner.value if game_session.winner else None,
                    "player_count": len(game_session.players),
                    "can_replay": True
                }
            )

        @self.app.post("/replays/days", response_model=List[Dict[str, Any]])
        async def get_replay_days(replay_data: ReplayRequest):
            """Get available replay days."""
            game_session = None
            for engine in self.game_engines.values():
                session = engine.get_session()
                if session and session.id == replay_data.game_id:
                    game_session = session
                    break

            if not game_session:
                raise HTTPException(status_code=404, detail="Game not found")

            days = []
            for i in range(1, game_session.day_count + 1):
                days.append({
                    "day_number": i,
                    "timestamp": game_session.phase_start_time.isoformat(),
                    "has_events": len(game_session.get_events_by_day(i)) > 0
                })

            return days

        @self.app.post("/replays/day", response_model=ReplayDayResponse)
        async def get_replay_day(day_data: ReplayDayRequest):
            """Get replay data for specific day."""
            game_session = None
            for engine in self.game_engines.values():
                session = engine.get_session()
                if session and session.id == day_data.game_id:
                    game_session = session
                    break

            if not game_session:
                raise HTTPException(status_code=404, detail="Game not found")

            day_number = day_data.day_number
            if day_number > game_session.day_count:
                raise HTTPException(status_code=400, detail="Day not found")

            return ReplayDayResponse(
                day_number=day_number,
                player_states=game_session.game_state.players,
                game_state={
                    "phase": game_session.current_phase,
                    "sheriff": {
                        "player_id": game_session.sheriff.player_id,
                        "player_name": game_session.sheriff.player_name
                    } if game_session.sheriff else None,
                    "alive_players": len(game_session.get_alive_players())
                },
                available_events=[
                    {
                        "event_id": event.id,
                        "type": event.type.value,
                        "timestamp": event.timestamp.isoformat(),
                        "description": event.content,
                        "participants": [
                            p for p in [event.actor_id, event.target_id] if p
                        ]
                    }
                    for event in game_session.get_events_by_day(day_number)
                ]
            )

        # System status
        @self.app.get("/status", response_model=SystemStatus)
        async def get_system_status():
            """Get system status."""
            websocket_status = {
                "connected_clients": 0,  # Would be populated by WebSocket service
                "active_rooms": len(self.rooms),
                "active_games": len(self.game_engines),
                "uptime": asyncio.get_event_loop().time()
            }

            agentscope_status = await self.ai_manager.health_check() if self.ai_manager else {
                "status": "not_initialized"
            }

            return SystemStatus(
                server={
                    "status": "healthy",
                    "uptime": websocket_status["uptime"],
                    "version": "1.0.0",
                    "environment": "development"
                },
                websocket=websocket_status,
                agentscope=agentscope_status,
                memory={
                    "rss": 0,  # Would get actual memory usage
                    "vms": 0,
                    "heap_used": 0,
                    "heap_total": 0
                },
                timestamp=datetime.now().isoformat()
            )

        # Metrics
        @self.app.get("/metrics")
        async def get_metrics():
            """Get system metrics."""
            return {
                "performance": {
                    "uptime": asyncio.get_event_loop().time(),
                    "memory_usage": {},
                    "cpu_usage": {}
                },
                "services": {
                    "websocket": {
                        "connected_clients": len(self.rooms),
                        "active_rooms": len(self.rooms),
                        "active_games": len(self.game_engines)
                    },
                    "agentscope": await self.ai_manager.health_check() if self.ai_manager else {},
                    "event_service": self.event_service.get_service_status()
                },
                "timestamp": datetime.now().isoformat()
            }

    def _setup_exception_handlers(self) -> None:
        """Setup exception handlers."""
        @self.app.exception_handler(404)
        async def not_found_handler(request, exc):
            # Safely extract error message
            error_msg = str(exc.detail) if hasattr(exc, 'detail') else str(exc)
            return JSONResponse(
                status_code=404,
                content={"error": "Not Found", "message": error_msg},
            )

        @self.app.exception_handler(500)
        async def internal_error_handler(request, exc):
            logger.error(f"Internal server error: {exc}")
            # Safely extract error message
            error_msg = str(exc.detail) if hasattr(exc, 'detail') else str(exc)
            return JSONResponse(
                status_code=500,
                content={"error": "Internal Server Error", "message": error_msg},
            )

    async def initialize_ai_manager(self) -> None:
        """Initialize AI manager."""
        try:
            self.ai_manager = AIManager()
            await self.ai_manager.initialize()
            logger.info("AI Manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI Manager: {e}")
            raise

    def create_game_engine(self, room: GameRoom) -> AIGameEngine:
        """Create and store game engine for room."""
        game_engine = AIGameEngine(
            room=room,
            event_service=self.event_service
        )

        self.game_engines[room.id] = game_engine

        # Set up callbacks
        game_engine.set_phase_change_callback(self._on_phase_change)
        game_engine.set_player_death_callback(self._on_player_death)
        game_engine.set_game_end_callback(self._on_game_end)

        return game_engine

    async def _on_phase_change(self, old_phase: GamePhase, new_phase: GamePhase) -> None:
        """Handle phase change."""
        logger.info(f"Phase changed: {old_phase} -> {new_phase}")

    async def _on_player_death(self, player: Player, cause) -> None:
        """Handle player death."""
        logger.info(f"Player {player.name} died: {cause}")

    async def _on_game_end(self, winner: Team) -> None:
        """Handle game end."""
        logger.info(f"Game ended. Winner: {winner}")

        # Clean up game engine
        engines_to_remove = []
        for room_id, engine in self.game_engines.items():
            if engine.get_session() and engine.get_session().winner == winner:
                engines_to_remove.append(room_id)

        for room_id in engines_to_remove:
            del self.game_engines[room_id]

    def get_app(self) -> FastAPI:
        """Get FastAPI application instance."""
        return self.app


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    api = WerewolfAPI()

    # Initialize AI manager (async, but we need to call it during app startup)
    # This would normally be called during application startup

    return api.app


if __name__ == "__main__":
    # Run the server
    app = create_app()

    # Initialize AI manager
    async def init_ai():
        api_instance = WerewolfAPI()
        await api_instance.initialize_ai_manager()

    # Run startup tasks
    import asyncio
    asyncio.run(init_ai())

    # Run server
    uvicorn.run(app.app, host="0.0.0.0", port=8000, reload=True)