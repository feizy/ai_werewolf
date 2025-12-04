"""Test FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
import json


class TestHealthCheck:
    """Test health check endpoints."""

    def test_root_endpoint(self, test_client: TestClient):
        """Test root endpoint."""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

    def test_health_check(self, test_client: TestClient):
        """Test health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestRoomManagement:
    """Test room management endpoints."""

    def test_create_room(self, test_client: TestClient, sample_room_data: dict):
        """Test room creation."""
        response = test_client.post("/rooms", json=sample_room_data)
        assert response.status_code == 200
        data = response.json()
        assert "room_id" in data
        assert "player_id" in data
        assert data["room_name"] == sample_room_data["room_name"]

    def test_get_rooms(self, test_client: TestClient, sample_room_data: dict):
        """Test getting all rooms."""
        # Create a room first
        test_client.post("/rooms", json=sample_room_data)

        response = test_client.get("/rooms")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_room_by_id(self, test_client: TestClient, sample_room_data: dict):
        """Test getting room by ID."""
        # Create a room first
        create_response = test_client.post("/rooms", json=sample_room_data)
        room_id = create_response.json()["room_id"]

        response = test_client.get(f"/rooms/{room_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == room_id

    def test_get_nonexistent_room(self, test_client: TestClient):
        """Test getting non-existent room."""
        response = test_client.get("/rooms/nonexistent-id")
        assert response.status_code == 404

    def test_join_room(self, test_client: TestClient, sample_room_data: dict):
        """Test joining room."""
        # Create a room first
        create_response = test_client.post("/rooms", json=sample_room_data)
        room_id = create_response.json()["room_id"]

        join_data = {
            "room_id": room_id,
            "player_name": "NewPlayer"
        }

        response = test_client.post(f"/rooms/{room_id}/join", json=join_data)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == room_id
        assert "players" in data

    def test_join_full_room(self, test_client: TestClient):
        """Test joining full room."""
        # Create a room with max 2 players
        room_data = {
            "player_name": "Creator",
            "room_name": "Full Room",
            "max_players": 2
        }

        create_response = test_client.post("/rooms", json=room_data)
        room_id = create_response.json()["room_id"]

        # Join with first player
        join_data1 = {
            "room_id": room_id,
            "player_name": "Player1"
        }
        test_client.post(f"/rooms/{room_id}/join", json=join_data1)

        # Try to join with second player (should be full)
        join_data2 = {
            "room_id": room_id,
            "player_name": "Player2"
        }
        response = test_client.post(f"/rooms/{room_id}/join", json=join_data2)
        assert response.status_code == 400

    def test_join_nonexistent_room(self, test_client: TestClient):
        """Test joining non-existent room."""
        join_data = {
            "room_id": "nonexistent-id",
            "player_name": "Player"
        }

        response = test_client.post("/rooms/nonexistent-id/join", json=join_data)
        assert response.status_code == 404


class TestGameManagement:
    """Test game management endpoints."""

    def test_get_game(self, test_client: TestClient, sample_room_data: dict, mock_game_engine):
        """Test getting game information."""
        # This test would require setting up a complete game session
        # For now, test the 404 case
        response = test_client.get("/games/nonexistent-game-id")
        assert response.status_code == 404

    def test_get_game_state(self, test_client: TestClient):
        """Test getting game state."""
        response = test_client.get("/games/nonexistent-game-id/state")
        assert response.status_code == 404

    def test_start_game(self, test_client: TestClient, sample_room_data: dict):
        """Test starting game."""
        # Create room
        create_response = test_client.post("/rooms", json=sample_room_data)
        room_id = create_response.json()["room_id"]
        player_id = create_response.json()["player_id"]

        # Try to start game (should fail - not enough players)
        start_data = {"player_id": player_id}
        response = test_client.post(f"/games/{room_id}/start", json=start_data)
        # Should fail because game doesn't exist yet or room not ready
        assert response.status_code in [400, 404]


class TestReplaySystem:
    """Test replay system endpoints."""

    def test_access_replay_nonexistent(self, test_client: TestClient):
        """Test accessing replay for non-existent game."""
        replay_data = {"game_id": "nonexistent-game-id"}
        response = test_client.post("/replays", json=replay_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    def test_get_replay_days_nonexistent(self, test_client: TestClient):
        """Test getting replay days for non-existent game."""
        replay_data = {"game_id": "nonexistent-game-id"}
        response = test_client.post("/replays/days", json=replay_data)
        assert response.status_code == 404

    def test_get_replay_day_nonexistent(self, test_client: TestClient):
        """Test getting replay day for non-existent game."""
        day_data = {"game_id": "nonexistent-game-id", "day_number": 1}
        response = test_client.post("/replays/day", json=day_data)
        assert response.status_code == 404


class TestSystemEndpoints:
    """Test system endpoints."""

    def test_get_system_status(self, test_client: TestClient):
        """Test getting system status."""
        response = test_client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert "server" in data
        assert "websocket" in data
        assert "timestamp" in data

    def test_get_metrics(self, test_client: TestClient):
        """Test getting system metrics."""
        response = test_client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "performance" in data
        assert "services" in data
        assert "timestamp" in data


class TestErrorHandling:
    """Test error handling."""

    def test_404_handling(self, test_client: TestClient):
        """Test 404 error handling."""
        response = test_client.get("/nonexistent-endpoint")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data

    def test_invalid_request_data(self, test_client: TestClient):
        """Test invalid request data handling."""
        # Test creating room with invalid data
        invalid_data = {
            "player_name": "",  # Empty name should fail validation
            "max_players": 1    # Less than minimum should fail
        }

        response = test_client.post("/rooms", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_missing_required_fields(self, test_client: TestClient):
        """Test missing required fields."""
        # Test creating room with missing fields
        incomplete_data = {
            "player_name": "TestPlayer"
            # Missing max_players
        }

        response = test_client.post("/rooms", json=incomplete_data)
        # Should still work because max_players has default value
        assert response.status_code == 200