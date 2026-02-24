import os
import sqlite3
from pathlib import Path
from typing import Optional


def get_db_path(override: Optional[str] = None) -> Path:
    """Resolve the database path using precedence:
    override arg > POSSESSION_DB env var > ~/.possession/possession.db
    """
    if override:
        return Path(override)
    env_path = os.environ.get("POSSESSION_DB")
    if env_path:
        return Path(env_path)
    return Path.home() / ".possession" / "possession.db"


def get_connection(path: Path) -> sqlite3.Connection:
    """Open a SQLite connection with WAL mode and foreign keys enabled."""
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(override: Optional[str] = None) -> Path:
    """Initialize the database at the resolved path, creating tables if needed.

    Returns the resolved path to the database file.
    """
    path = get_db_path(override)
    conn = get_connection(path)
    schema_path = Path(__file__).parent / "schema.sql"
    schema_sql = schema_path.read_text()
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()
    return path
