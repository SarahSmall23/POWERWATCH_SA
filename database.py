"""
database.py
PowerWatch SA — SQLite persistence layer.

One table logs every grid state transition (outage start / recovery) with a
timestamp, and a second stores periodic battery readings so the dashboard
can plot a charge-over-time graph. SQLite needs no separate server process,
which suits a single Raspberry Pi deployment.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime

DB_PATH = "powerwatch.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS outage_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,          -- 'outage_start' or 'recovery'
    timestamp TEXT NOT NULL,
    battery_percent REAL
);

CREATE TABLE IF NOT EXISTS battery_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    battery_percent REAL NOT NULL,
    battery_voltage REAL NOT NULL,
    grid_up INTEGER NOT NULL
);
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def log_event(event_type: str, battery_percent: float):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO outage_events (event_type, timestamp, battery_percent) VALUES (?, ?, ?)",
            (event_type, datetime.now().isoformat(timespec="seconds"), battery_percent),
        )


def log_reading(battery_percent: float, battery_voltage: float, grid_up: bool):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO battery_readings (timestamp, battery_percent, battery_voltage, grid_up) "
            "VALUES (?, ?, ?, ?)",
            (datetime.now().isoformat(timespec="seconds"), battery_percent, battery_voltage, int(grid_up)),
        )


def recent_events(limit: int = 20):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM outage_events ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def recent_readings(limit: int = 60):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM battery_readings ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in reversed(rows)]


def outage_stats():
    """Total outage count and total downtime (minutes) from logged events."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT event_type, timestamp FROM outage_events ORDER BY id ASC"
        ).fetchall()

    total_outages = 0
    total_minutes = 0.0
    last_start = None
    for row in rows:
        if row["event_type"] == "outage_start":
            last_start = datetime.fromisoformat(row["timestamp"])
            total_outages += 1
        elif row["event_type"] == "recovery" and last_start:
            end = datetime.fromisoformat(row["timestamp"])
            total_minutes += (end - last_start).total_seconds() / 60.0
            last_start = None

    return {"total_outages": total_outages, "total_minutes": round(total_minutes, 1)}
