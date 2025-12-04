"""Module to allow running werewolf backend with `python -m werewolf`."""

from .main import create_app
import uvicorn
from loguru import logger

if __name__ == "__main__":
    # Create app
    app = create_app()

    # Configure logging
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )

    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )