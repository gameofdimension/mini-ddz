"""Tests for replay_db.py"""

import os
import shutil
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pve_server"))

import replay_db as db


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    original_db_path = db.DB_PATH
    original_db_dir = db.DB_DIR

    # Override database path
    db.DB_DIR = temp_dir
    db.DB_PATH = os.path.join(temp_dir, "test.db")

    yield temp_dir

    # Cleanup
    db.DB_PATH = original_db_path
    db.DB_DIR = original_db_dir
    shutil.rmtree(temp_dir)


class TestInitDb:
    """Test init_db function."""

    def test_init_db_creates_table(self, temp_db):
        """Test that init_db creates the replays table."""
        db.init_db()
        # Verify by checking if we can query the table
        import sqlite3

        conn = sqlite3.connect(db.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='replays'")
        result = cursor.fetchone()
        conn.close()
        assert result is not None

    def test_init_db_idempotent(self, temp_db):
        """Test that init_db can be called multiple times without error."""
        db.init_db()
        db.init_db()  # Should not raise error


class TestSaveReplay:
    """Test save_replay function."""

    def test_save_new_replay(self, temp_db):
        """Test saving a new replay."""
        replay_data = {
            "playerInfo": [{"id": 0, "role": "landlord"}],
            "initHands": ["S3 S4 S5", "H3 H4 H5", "D3 D4 D5"],
            "moveHistory": [{"playerIdx": 0, "move": "pass"}],
        }
        result = db.save_replay("test123", replay_data)
        assert result is True

    def test_save_replay_with_existing_id(self, temp_db):
        """Test saving replay with duplicate ID fails."""
        replay_data = {
            "playerInfo": [{"id": 0, "role": "landlord"}],
            "initHands": ["S3 S4 S5", "H3 H4 H5", "D3 D4 D5"],
            "moveHistory": [],
        }
        db.save_replay("test123", replay_data)
        result = db.save_replay("test123", replay_data)
        assert result is False  # Should fail due to primary key constraint

    def test_save_empty_replay(self, temp_db):
        """Test saving replay with minimal data."""
        replay_data = {"playerInfo": [], "initHands": [], "moveHistory": []}
        result = db.save_replay("empty123", replay_data)
        assert result is True

    def test_save_replay_with_complex_data(self, temp_db):
        """Test saving replay with complex move history."""
        replay_data = {
            "playerInfo": [
                {"id": 0, "index": 0, "role": "landlord", "agentInfo": {"name": "Test"}},
                {"id": 1, "index": 1, "role": "peasant"},
                {"id": 2, "index": 2, "role": "peasant"},
            ],
            "initHands": ["RJ BJ S2 S2 S2 S2", "H3 H4 H5 H6 H7 H8", "D3 D4 D5 D6 D7 D8"],
            "moveHistory": [
                {"playerIdx": 0, "move": "RJ", "info": {"values": {"RJ": 0.5}}},
                {"playerIdx": 1, "move": "pass"},
                {"playerIdx": 2, "move": "BJ"},
            ],
        }
        result = db.save_replay("complex456", replay_data)
        assert result is True


class TestGetReplay:
    """Test get_replay function."""

    def test_get_existing_replay(self, temp_db):
        """Test retrieving an existing replay."""
        replay_data = {
            "playerInfo": [{"id": 0, "role": "landlord"}],
            "initHands": ["S3 S4 S5", "H3 H4 H5", "D3 D4 D5"],
            "moveHistory": [{"playerIdx": 0, "move": "pass"}],
        }
        db.save_replay("test789", replay_data)

        result = db.get_replay("test789")
        assert result is not None
        assert result["replay_id"] == "test789"
        assert result["playerInfo"] == [{"id": 0, "role": "landlord"}]
        assert "created" in result

    def test_get_nonexistent_replay(self, temp_db):
        """Test retrieving a non-existent replay."""
        result = db.get_replay("nonexistent")
        assert result is None

    def test_get_returns_proper_types(self, temp_db):
        """Test that get_replay returns properly deserialized data."""
        replay_data = {
            "playerInfo": [{"id": 0, "role": "landlord"}],
            "initHands": ["S3 S4 S5"],
            "moveHistory": [{"playerIdx": 0, "move": "pass"}],
        }
        db.save_replay("typestest", replay_data)

        result = db.get_replay("typestest")
        assert isinstance(result["playerInfo"], list)
        assert isinstance(result["initHands"], list)
        assert isinstance(result["moveHistory"], list)


class TestListReplays:
    """Test list_replays function."""

    def test_list_empty(self, temp_db):
        """Test listing when no replays exist."""
        result = db.list_replays()
        assert result == []

    def test_list_single_replay(self, temp_db):
        """Test listing with one replay."""
        replay_data = {"playerInfo": [], "initHands": [], "moveHistory": []}
        db.save_replay("single", replay_data)

        result = db.list_replays()
        assert len(result) == 1
        assert result[0]["replay_id"] == "single"
        assert "created" in result[0]

    def test_list_multiple_replays(self, temp_db):
        """Test listing multiple replays."""
        for i in range(5):
            replay_data = {"playerInfo": [{"id": i}], "initHands": [], "moveHistory": []}
            db.save_replay(f"replay{i}", replay_data)

        result = db.list_replays()
        assert len(result) == 5

    def test_list_ordered_by_time(self, temp_db):
        """Test that replays are ordered by creation time (newest first)."""
        import time

        for i in range(3):
            replay_data = {"playerInfo": [], "initHands": [], "moveHistory": []}
            db.save_replay(f"order{i}", replay_data)
            time.sleep(0.05)  # Small delay to ensure different timestamps

        result = db.list_replays()
        # Newest should be first
        assert len(result) == 3
        # Check that they are in descending order by time
        assert result[0]["replay_id"] > result[2]["replay_id"] or result[0]["created"] >= result[2]["created"]

    def test_list_limit(self, temp_db):
        """Test listing with limit."""
        for i in range(10):
            replay_data = {"playerInfo": [], "initHands": [], "moveHistory": []}
            db.save_replay(f"limit{i}", replay_data)

        result = db.list_replays(limit=5)
        assert len(result) == 5


class TestDeleteReplay:
    """Test delete_replay function."""

    def test_delete_existing_replay(self, temp_db):
        """Test deleting an existing replay."""
        replay_data = {"playerInfo": [], "initHands": [], "moveHistory": []}
        db.save_replay("delete_me", replay_data)

        result = db.delete_replay("delete_me")
        assert result is True

        # Verify it's gone
        assert db.get_replay("delete_me") is None

    def test_delete_nonexistent_replay(self, temp_db):
        """Test deleting a non-existent replay."""
        # Initialize database first
        db.init_db()
        result = db.delete_replay("nonexistent")
        # Should return True (no error) as there's nothing to delete
        assert result is True

    def test_delete_specific_replay(self, temp_db):
        """Test that deleting one replay doesn't affect others."""
        replay_data = {"playerInfo": [], "initHands": [], "moveHistory": []}
        db.save_replay("keep", replay_data)
        db.save_replay("remove", replay_data)

        db.delete_replay("remove")

        assert db.get_replay("keep") is not None
        assert db.get_replay("remove") is None


class TestIntegration:
    """Integration tests for all database operations."""

    def test_full_workflow(self, temp_db):
        """Test complete workflow: save, list, get, delete."""
        # Save
        replay_data = {
            "playerInfo": [{"id": 0, "role": "landlord"}],
            "initHands": ["S3 S4", "H3 H4", "D3 D4"],
            "moveHistory": [{"playerIdx": 0, "move": "pass"}],
        }
        assert db.save_replay("workflow", replay_data) is True

        # List
        replays = db.list_replays()
        assert len(replays) == 1

        # Get
        retrieved = db.get_replay("workflow")
        assert retrieved["replay_id"] == "workflow"
        assert retrieved["playerInfo"][0]["role"] == "landlord"

        # Delete
        assert db.delete_replay("workflow") is True

        # Verify deletion
        assert db.get_replay("workflow") is None
        assert len(db.list_replays()) == 0
