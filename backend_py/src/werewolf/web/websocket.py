"""WebSocket integration for werewolf game using Socket.IO."""

import json
import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

try:
    import socketio
    from fastapi import FastAPI
    from socketio import ASGIApp
    AGENTSCOPE_WEBSOCKET_AVAILABLE = True
except ImportError:
    AGENTSCOPE_WEBSOCKET_AVAILABLE = False

    # Create mock classes for testing
    class socketio:
        class ASGIApp:
            def __init__(self, *args, **kwargs):
                pass

        class AsyncServer:
            def __init__(self, *args, **kwargs):
                pass

        class cors:
            def __init__(self, *args, **kwargs):
                pass

from loguru import logger

from ..models.player import Player
from ..models.room import GameRoom
from ..services.game_engine import GameEngine
from .api import WerewolfAPI


class WebSocketManager:
    """WebSocket manager for werewolf game."""

    def __init__(self, app: FastAPI):
        self.app = app
        self.connected_clients: Dict[str, Dict[str, Any]] = {}
        self.room_clients: Dict[str, List[str]] = {}
        self.game_rooms: Dict[str, GameRoom] = {}
        self.game_engines: Dict[str, GameEngine] = {}

        # Create Socket.IO app
        if AGENTSCOPE_WEBSOCKET_AVAILABLE:
            self.sio = socketio.AsyncServer(
                cors_allowed_origins=["http://localhost:3000", "http://localhost:3001"],
                async_mode='auto',
                engineio_logger=True,
                logger=True
            )
            self.asgi_app = ASGIApp(self.sio, socketio_path="/socket.io")
        else:
            self.sio = None
            self.asgi_app = None

        self._setup_event_handlers()

    def _setup_event_handlers(self) -> None:
        """Setup Socket.IO event handlers."""
        if not self.sio:
            return

        @self.sio.event
        async def connect(sid, environ):
            """Handle client connection."""
            client_info = {
                "sid": sid,
                "connected_at": datetime.now().isoformat(),
                "ip": environ.get("REMOTE_ADDR", "unknown"),
                "user_agent": environ.get("HTTP_USER_AGENT", "unknown")
            }

            self.connected_clients[sid] = client_info
            logger.info(f"Client connected: {sid} from {client_info['ip']}")

            # Send connection confirmation
            await self.sio.emit("connection_established", {
                "connection_id": sid,
                "timestamp": datetime.now().isoformat(),
                "server_time": datetime.now().isoformat()
            }, room=sid)

        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection."""
            client_info = self.connected_clients.get(sid)
            if client_info:
                logger.info(f"Client disconnected: {sid}")

                # Remove from rooms
                for room_id, clients in self.room_clients.items():
                    if sid in clients:
                        clients.remove(sid)
                        # Broadcast player left
                        await self.sio.emit(
                            "player_left",
                            {
                                "player_id": client_info.get("player_id"),
                                "player_name": client_info.get("player_name"),
                                "player_count": len(clients)
                            },
                            room=room_id
                        )

            del self.connected_clients[sid]

        @self.sio.event
        async def create_room(sid, data):
            """Handle room creation."""
            try:
                await self.handle_create_room(sid, data)
            except Exception as e:
                logger.error(f"Error creating room: {e}")
                await self.sio.emit("room_creation_error", {
                    "error": str(e)
                }, room=sid)

        @self.sio.event
        async def join_room(sid, data):
            """Handle room joining."""
            try:
                await self.handle_join_room(sid, data)
            except Exception as e:
                logger.error(f"Error joining room: {e}")
                await self.sio.emit("room_join_error", {
                    "error": str(e)
                }, room=sid)

        @self.sio.event
        async def leave_room(sid, data):
            """Handle room leaving."""
            try:
                await self.handle_leave_room(sid, data)
            except Exception as e:
                logger.error(f"Error leaving room: {e}")

        @self.sio.event
        async def start_game(sid, data):
            """Handle game start."""
            try:
                await self.handle_start_game(sid, data)
            except Exception as e:
                logger.error(f"Error starting game: {e}")
                await self.sio.emit("game_start_error", {
                    "error": str(e)
                }, room=sid)

        @self.sio.event
        async def heartbeat(sid, data):
            """Handle heartbeat."""
            client_info = self.connected_clients.get(sid)
            if client_info:
                client_info["last_active"] = time.time()

            await self.sio.emit("heartbeat_response", {
                "timestamp": datetime.now().isoformat(),
                "server_time": datetime.now().isoformat()
            }, room=sid)

        @self.sio.event
        async def reconnect(sid, data):
            """Handle reconnection."""
            try:
                await self.handle_reconnect(sid, data)
            except Exception as e:
                logger.error(f"Error reconnecting: {e}")
                await self.sio.emit("reconnect_response", {
                    "success": False,
                    "error": str(e)
                }, room=sid)

    async def handle_create_room(self, sid: str, data: Dict[str, Any]) -> None:
        """Handle room creation."""
        from .api import RoomCreate

        try:
            room_data = RoomCreate(**data)

            # Create room
            room = GameRoom.create_room(
                creator_name=room_data.player_name,
                room_name=room_data.room_name,
                max_players=room_data.max_players,
                creator_id=f"creator-{int(time.time())}"
            )

            # Store room
            self.game_rooms[room.id] = room

            # Update client info
            client_info = self.connected_clients.get(sid)
            if client_info:
                client_info["player_id"] = room.creator_id
                client_info["room_id"] = room.id
                client_info["player_name"] = room_data.player_name

            # Create game engine
            api = WerewolfAPI()
            game_engine = api.create_game_engine(room)
            self.game_engines[room.id] = game_engine

            # Join room
            await self.sio.enter_room(sid, room.id)
            self.room_clients[room.id] = [sid]

            # Send response
            await self.sio.emit("room_created", {
                "type": "roomCreated",
                "timestamp": datetime.now().isoformat(),
                "payload": {
                    "roomId": room.id,
                    "playerId": room.creator_id,
                    "roomName": room.name,
                    "creatorId": room.creator_id
                }
            }, room=sid)

            logger.info(f"Room created: {room.id} by {room_data.player_name}")

        except Exception as e:
            logger.error(f"Room creation failed: {e}")
            raise

    async def handle_join_room(self, sid: str, data: Dict[str, Any]) -> None:
        """Handle room joining."""
        from .api import RoomJoin

        try:
            join_data = RoomJoin(**data)
            room = self.game_rooms.get(join_data.room_id)

            if not room:
                await self.sio.emit("room_join_error", {
                    "type": "room_join_error",
                    "timestamp": datetime.now().isoformat(),
                    "payload": {
                        "error": "Room not found",
                        "code": "ROOM_NOT_FOUND"
                    }
                }, room=sid)
                return

            if room.is_full():
                await self.sio.emit("room_join_error", {
                    "type": "room_join_error",
                    "timestamp": datetime.now().isoformat(),
                    "payload": {
                        "error": "Room is full",
                        "code": "ROOM_FULL"
                    }
                }, room=sid)
                return

            if room.status != "waiting":
                await self.sio.emit("room_join_error", {
                    "type": "room_join_error",
                    "timestamp": datetime.now().isoformat(),
                    "payload": {
                        "error": "Game is already in progress",
                        "code": "GAME_NOT_STARTED"
                    }
                }, room=sid)
                return

            # Create new player
            player = Player.create_ai_player(
                name=join_data.player_name,
                room_id=room.id,
                position=room.current_players + 1
            )

            if not room.add_player(player):
                await self.sio.emit("room_join_error", {
                    "type": "room_join_error",
                    "timestamp": datetime.now().isoformat(),
                    "payload": {
                        "error": "Failed to join room",
                        "code": "ROOM_FULL"
                    }
                }, room=sid)
                return

            # Update client info
            client_info = self.connected_clients.get(sid)
            if client_info:
                client_info["player_id"] = player.id
                client_info["room_id"] = room.id
                client_info["player_name"] = player.name

            # Join room
            await self.sio.enter_room(sid, room.id)
            if room.id not in self.room_clients:
                self.room_clients[room.id] = []
            self.room_clients[room.id].append(sid)

            # Send response to client
            await self.sio.emit("room_joined", {
                "type": "RoomJoined",
                "timestamp": datetime.now().isoformat(),
                "payload": {
                    "roomId": room.id,
                    "playerId": player.id,
                    "roomInfo": {
                        "name": room.name,
                        "creatorName": room.get_player(room.creator_id).name if room.get_player(room.creator_id) else "Unknown",
                        "currentPlayers": room.current_players,
                        "maxPlayers": room.max_players
                    },
                    "players": room.get_players_info()
                }
            }, room=sid)

            # Broadcast to other players in room
            await self.sio.emit("player_joined", {
                "type": "PlayerJoined",
                "timestamp": datetime.now().isoformat(),
                "payload": {
                    "playerId": player.id,
                    "playerName": player.name,
                    "playerCount": room.current_players,
                    "players": room.get_players_info()
                }
            }, room=room.id, skip_sid=sid)

            logger.info(f"Player {player.name} joined room {room.id}")

        except Exception as e:
            logger.error(f"Room join failed: {e}")
            raise

    async def handle_leave_room(self, sid: str, data: Dict[str, Any]) -> None:
        """Handle room leaving."""
        client_info = self.connected_clients.get(sid)
        if not client_info or not client_info.get("room_id"):
            return

        room_id = client_info["room_id"]
        room = self.game_rooms.get(room_id)

        if room:
            player = room.get_player(client_info["player_id"])
            if player:
                room.remove_player(player.id)

                # Leave Socket.IO room
                await self.sio.leave_room(sid, room_id)

                # Remove from room clients
                if room_id in self.room_clients:
                    if sid in self.room_clients[room_id]:
                        self.room_clients[room_id].remove(sid)

                # Broadcast player left
                await self.sio.emit("player_left", {
                    "type": "PlayerLeft",
                    "timestamp": datetime.now().isoformat(),
                    "payload": {
                        "playerId": player.id,
                        "playerName": player.name,
                        "playerCount": room.current_players
                    }
                }, room=room_id)

                logger.info(f"Player {player.name} left room {room_id}")

        # Clear client info
        if client_info:
            client_info["player_id"] = None
            client_info["room_id"] = None

    async def handle_start_game(self, sid: str, data: Dict[str, Any]) -> None:
        """Handle game start."""
        from .api import GameStart

        try:
            start_data = GameStart(**data)
            client_info = self.connected_clients.get(sid)

            if not client_info or client_info.get("player_id") != start_data.player_id:
                await self.sio.emit("game_start_error", {
                    "type": "GameStartError",
                    "timestamp": datetime.now().isoformat(),
                    "payload": {
                        "error": "Invalid player ID",
                        "code": "INSUFFICIENT_PERMISSIONS"
                    }
                }, room=sid)
                return

            room_id = client_info["room_id"]
            room = self.game_rooms.get(room_id)

            if not room:
                await self.sio.emit("game_start_error", {
                    "type": "GameStartError",
                    "timestamp": datetime.now().isoformat(),
                    "payload": {
                        "error": "Room not found",
                        "code": "ROOM_NOT_FOUND"
                    }
                }, room=sid)
                return

            # Check if creator
            if room.creator_id != start_data.player_id:
                await self.sio.emit("game_start_error", {
                    "type": "GameStartError",
                    "timestamp": datetime.now().isoformat(),
                    "payload": {
                        "error": "Only room creator can start game",
                        "code": "INSUFFICIENT_PERMISSIONS"
                    }
                }, room=sid)
                return

            if not room.can_start_game():
                await self.sio.emit("game_start_error", {
                    "type": "GameStartError",
                    "timestamp": datetime.now().isoformat(),
                    "payload": {
                        "error": "Cannot start game: room not ready",
                        "code": "GAME_NOT_STARTED"
                    }
                }, room=sid)
                return

            # Start game
            room.start_game()
            game_engine = self.game_engines.get(room_id)
            session = await game_engine.start_game()

            # Get player info
            game_players = [p.get_private_info() for p in room.players]

            # Broadcast game started
            await self.sio.emit("game_started", {
                "type": "GameStarted",
                "timestamp": datetime.now().isoformat(),
                "payload": {
                    "gameId": session.id,
                    "players": game_players,
                    "initialPhase": "night",
                    "dayCount": 1
                }
            }, room=room_id)

            logger.info(f"Game started in room {room_id}")

        except Exception as e:
            logger.error(f"Game start failed: {e}")
            raise

    async def handle_reconnect(self, sid: str, data: Dict[str, Any]) -> None:
        """Handle reconnection."""
        try:
            player_id = data.get("playerId")
            room_id = data.get("roomId")
            last_event_id = data.get("lastEventId")

            if not player_id or not room_id:
                await self.sio.emit("reconnect_response", {
                    "type": "ReconnectResponse",
                    "timestamp": datetime.now().isoformat(),
                    "payload": {
                        "success": False,
                        "error": "Missing player_id or room_id"
                    }
                }, room=sid)
                return

            room = self.game_rooms.get(room_id)
            if not room:
                await self.sio.emit("reconnect_response", {
                    "type": "ReconnectResponse",
                    "timestamp": datetime.now().isoformat(),
                    "payload": {
                        "success": False,
                        "error": "Room not found"
                    }
                }, room=sid)
                return

            player = room.get_player(player_id)
            if not player:
                await self.sio.emit("reconnect_response", {
                    "type": "ReconnectResponse",
                    "timestamp": datetime.now().isoformat(),
                    "payload": {
                        "success": False,
                        "error": "Player not found in room"
                    }
                }, room=sid)
                return

            # Update client info
            client_info = self.connected_clients.get(sid)
            if client_info:
                client_info["player_id"] = player_id
                client_info["room_id"] = room_id
                client_info["player_name"] = player.name

            # Rejoin room
            await self.sio.enter_room(sid, room_id)
            if room_id not in self.room_clients:
                self.room_clients[room_id] = []
            self.room_clients[room_id].append(sid)

            # Get missed events (simplified)
            missed_events = []  # Would implement actual event retrieval
            current_state = None  # Would get from game engine

            game_engine = self.game_engines.get(room_id)
            if game_engine:
                current_state = game_engine.get_current_state()

            await self.sio.emit("reconnect_response", {
                "type": "ReconnectResponse",
                "timestamp": datetime.now().isoformat(),
                "payload": {
                    "success": True,
                    "missedEvents": missed_events[:10],  # Limit to 10 events
                    "currentGameState": current_state
                }
            }, room=sid)

            logger.info(f"Player {player.name} reconnected to room {room_id}")

        except Exception as e:
            logger.error(f"Reconnect failed: {e}")
            raise

    def get_service_status(self) -> Dict[str, Any]:
        """Get WebSocket service status."""
        return {
            "connected_clients": len(self.connected_clients),
            "active_rooms": len(self.room_clients),
            "active_games": len(self.game_engines),
            "uptime": time.time()
        }

    async def broadcast_game_event(self, room_id: str, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcast game event to room."""
        if room_id not in self.room_clients:
            return

        await self.sio.emit(event_type, {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "payload": data
        }, room=room_id)

    async def broadcast_to_room(self, room_id: str, event: Dict[str, Any], exclude_sid: Optional[str] = None):
        """Broadcast event to room (excluding specific client)."""
        if room_id not in self.room_clients:
            return

        if exclude_sid:
            await self.sio.emit(
                event["type"],
                {
                    "type": event["type"],
                    "timestamp": datetime.now().isoformat(),
                    "payload": event.get("payload", {})
                },
                room=room_id,
                skip_sid=exclude_sid
            )
        else:
            await self.sio.emit(
                event["type"],
                {
                    "type": event["type"],
                    "timestamp": datetime.now().isoformat(),
                    "payload": event.get("payload", {})
                },
                room=room_id
            )

    async def cleanup(self) -> None:
        """Cleanup WebSocket manager."""
        logger.info("Cleaning up WebSocket manager")

        # Stop all game engines
        for game_engine in self.game_engines.values():
            try:
                await game_engine.stop_game()
            except Exception as e:
                logger.error(f"Error stopping game engine: {e}")

        # Disconnect all clients
        if self.sio:
            await self.sio.disconnect()

        # Clear data
        self.connected_clients.clear()
        self.room_clients.clear()
        self.game_rooms.clear()
        self.game_engines.clear()

        logger.info("WebSocket manager cleanup complete")

    def create_socketio_app(self) -> ASGIApp:
        """Create Socket.IO ASGI app."""
        if not AGENTSCOPE_WEBSOCKET_AVAILABLE:
            raise RuntimeError("WebSocket not available")

        return self.asgi_app


def create_socketio_app(app: FastAPI) -> WebSocketManager:
    """Create WebSocket manager for FastAPI app."""
    manager = WebSocketManager(app)

    # Mount Socket.IO app to FastAPI
    app.mount("/socket.io", manager.create_socketio_app())

    return manager