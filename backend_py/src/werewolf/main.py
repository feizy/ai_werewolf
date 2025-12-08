"""Main application entry point for werewolf game backend."""

import asyncio
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

from loguru import logger

from .web.api import WerewolfAPI
from .web.websocket import create_socketio_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting werewolf game backend...")

    # Initialize AI manager
    api_instance = app.state.api
    try:
        await api_instance.initialize_ai_manager()
        logger.info("AI Manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize AI Manager: {e}")
        raise

    logger.info("Backend startup complete")

    yield

    # Cleanup
    logger.info("Shutting down werewolf game backend...")

    # Cleanup WebSocket manager
    if hasattr(app.state, 'websocket_manager'):
        await app.state.websocket_manager.cleanup()

    # Shutdown AI manager
    if api_instance.ai_manager:
        await api_instance.ai_manager.shutdown()

    logger.info("Backend shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    # Create API instance
    api = WerewolfAPI()
    app = api.get_app()

    # Store API instance in app state
    app.state.api = api

    # Setup lifespan
    app.router.lifespan_context = lifespan

    # Setup WebSocket
    try:
        websocket_manager = create_socketio_app(app)
        app.state.websocket_manager = websocket_manager
        logger.info("WebSocket manager initialized")
    except Exception as e:
        logger.error(f"Failed to initialize WebSocket manager: {e}")
        # Continue without WebSocket if it fails

    # Add root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "AI Werewolf Game Backend",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs",
            "websocket": "/socket.io"
        }

    return app


if __name__ == "__main__":
    # Create app
    app = create_app()

    # Configure logging
    logger.remove()
    logger.add(
        "logs/werewolf_backend.log",
        rotation="10 MB",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    )
    logger.add(
        lambda msg: print(msg, end=""),
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )

    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )