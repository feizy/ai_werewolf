"""Database management utilities."""

import asyncio
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from loguru import logger

from .connection import engine, SessionLocal, check_connection
from .models import Base
from .crud import PlayerCRUD, GameRoomCRUD, GameSessionCRUD, GameEventCRUD
from ..config import settings


class DatabaseManager:
    """Database manager for werewolf game."""

    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
        self.player_crud = PlayerCRUD()
        self.room_crud = GameRoomCRUD()
        self.session_crud = GameSessionCRUD()
        self.event_crud = GameEventCRUD()

    def initialize(self) -> bool:
        """Initialize database."""
        try:
            # Check connection
            if not check_connection():
                logger.error("Database connection failed")
                return False

            # Create tables
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False

    def get_session(self) -> Session:
        """Get database session."""
        return self.SessionLocal()

    def health_check(self) -> dict:
        """Perform health check."""
        try:
            with self.get_session() as db:
                # Test connection
                db.execute("SELECT 1")

                # Get basic stats
                player_count = db.query(self.player_crud.model).count()
                room_count = db.query(self.room_crud.model).count()
                session_count = db.query(self.session_crud.model).count()
                event_count = db.query(self.event_crud.model).count()

                return {
                    "status": "healthy",
                    "connection": "ok",
                    "stats": {
                        "players": player_count,
                        "rooms": room_count,
                        "sessions": session_count,
                        "events": event_count
                    }
                }

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "connection": "error",
                "error": str(e)
            }

    def cleanup_expired_data(self, days: int = 30) -> dict:
        """Clean up expired data."""
        try:
            with self.get_session() as db:
                from datetime import datetime, timedelta

                cutoff_date = datetime.utcnow() - timedelta(days=days)

                # Delete old finished rooms
                deleted_rooms = db.query(self.room_crud.model).filter(
                    self.room_crud.model.status == "finished",
                    self.room_crud.model.updated_at < cutoff_date
                ).count()

                # Delete old finished sessions
                deleted_sessions = db.query(self.session_crud.model).filter(
                    self.session_crud.model.winner.isnot(None),
                    self.session_crud.model.ended_at < cutoff_date
                ).count()

                db.commit()

                logger.info(f"Cleaned up {deleted_rooms} rooms and {deleted_sessions} sessions")

                return {
                    "deleted_rooms": deleted_rooms,
                    "deleted_sessions": deleted_sessions,
                    "status": "success"
                }

        except Exception as e:
            logger.error(f"Database cleanup failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def backup_database(self, backup_path: str) -> dict:
        """Create database backup."""
        try:
            if settings.database_url.startswith("sqlite"):
                # SQLite backup
                import shutil
                shutil.copy2(settings.database_url.replace("sqlite:///", ""), backup_path)
            else:
                # PostgreSQL backup (requires pg_dump)
                import subprocess

                cmd = [
                    "pg_dump",
                    settings.database_url,
                    "--file", backup_path,
                    "--verbose"
                ]

                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                if result.returncode != 0:
                    raise Exception(f"pg_dump failed: {result.stderr}")

            logger.info(f"Database backed up to {backup_path}")
            return {
                "status": "success",
                "backup_path": backup_path
            }

        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


# Global database manager instance
db_manager = DatabaseManager()


def get_db_manager() -> DatabaseManager:
    """Get database manager instance."""
    return db_manager


async def initialize_database() -> bool:
    """Initialize database asynchronously."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, db_manager.initialize)