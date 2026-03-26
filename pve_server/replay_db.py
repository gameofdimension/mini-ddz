"""
SQLite database module for storing replay data.
"""

import json
import os
import sqlite3
from typing import Any, Dict, List, Optional

# Database path
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "replays")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "replays.db")


def init_db():
    """Initialize the database with required tables and migrate if needed."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS replays (
            replay_id TEXT PRIMARY KEY,
            player_info TEXT NOT NULL,
            init_hands TEXT NOT NULL,
            move_history TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migration: Add source column if not exists
    cursor.execute("PRAGMA table_info(replays)")
    columns = [column[1] for column in cursor.fetchall()]
    if "source" not in columns:
        cursor.execute("ALTER TABLE replays ADD COLUMN source TEXT DEFAULT 'pve'")
        # Migrate existing data: infer source from player_info
        cursor.execute("SELECT replay_id, player_info FROM replays")
        for row in cursor.fetchall():
            player_info = json.loads(row[1])
            # If all players are DouZero, it's AI battle
            is_ai_battle = all(p.get("agentInfo", {}).get("name", "").startswith("DouZero") for p in player_info)
            source = "ai_battle" if is_ai_battle else "pve"
            cursor.execute("UPDATE replays SET source = ? WHERE replay_id = ?", (source, row[0]))

    conn.commit()
    conn.close()


def save_replay(replay_id: str, replay_data: Dict[str, Any]) -> bool:
    """
    Save a replay to the database.

    Args:
        replay_id: Unique identifier for the replay
        replay_data: Dictionary containing replay data

    Returns:
        True if successful, False otherwise
    """
    try:
        init_db()  # Ensure table exists

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO replays (replay_id, player_info, init_hands, move_history, source)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                replay_id,
                json.dumps(replay_data.get("playerInfo", [])),
                json.dumps(replay_data.get("initHands", [])),
                json.dumps(replay_data.get("moveHistory", [])),
                replay_data.get("source", "pve"),
            ),
        )

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving replay: {e}")
        return False


def get_replay(replay_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a replay by ID.

    Args:
        replay_id: Unique identifier for the replay

    Returns:
        Replay data dictionary or None if not found
    """
    try:
        init_db()  # Ensure table exists

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT replay_id, player_info, init_hands, move_history, created_at, source
            FROM replays
            WHERE replay_id = ?
        """,
            (replay_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "replay_id": row[0],
                "playerInfo": json.loads(row[1]),
                "initHands": json.loads(row[2]),
                "moveHistory": json.loads(row[3]),
                "created": row[4],
                "source": row[5] or "pve",
            }
        return None
    except Exception as e:
        print(f"Error getting replay: {e}")
        return None


def list_replays(limit: int = 100, source: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all available replays, sorted by creation time (newest first).

    Args:
        limit: Maximum number of replays to return
        source: Filter by source type ('pve' or 'ai_battle'), None for all

    Returns:
        List of replay metadata dictionaries
    """
    try:
        init_db()  # Ensure table exists

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if source:
            cursor.execute(
                """
                SELECT replay_id, created_at, source
                FROM replays
                WHERE source = ?
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (source, limit),
            )
        else:
            cursor.execute(
                """
                SELECT replay_id, created_at, source
                FROM replays
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (limit,),
            )

        rows = cursor.fetchall()
        conn.close()

        replays = []
        for row in rows:
            # Return ISO format string for proper timezone handling
            replays.append({"replay_id": row[0], "created": row[1], "source": row[2] or "pve"})

        return replays
    except Exception as e:
        print(f"Error listing replays: {e}")
        return []


def delete_replay(replay_id: str) -> bool:
    """
    Delete a replay by ID.

    Args:
        replay_id: Unique identifier for the replay

    Returns:
        True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM replays WHERE replay_id = ?", (replay_id,))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting replay: {e}")
        return False
