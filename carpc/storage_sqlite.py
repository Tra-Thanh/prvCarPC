from __future__ import annotations

import sqlite3
from pathlib import Path

from .model import RawFrame, SignalSample


SCHEMA_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS raw_frames (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts_unix REAL NOT NULL,
  channel TEXT NOT NULL,
  arbitration_id INTEGER NOT NULL,
  is_extended_id INTEGER NOT NULL,
  dlc INTEGER NOT NULL,
  data BLOB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_raw_frames_ts ON raw_frames (ts_unix);
CREATE INDEX IF NOT EXISTS idx_raw_frames_id ON raw_frames (arbitration_id);

CREATE TABLE IF NOT EXISTS signal_samples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts_unix REAL NOT NULL,
  channel TEXT NOT NULL,
  message_name TEXT NOT NULL,
  signal_name TEXT NOT NULL,
  value REAL NOT NULL,
  unit TEXT
);

CREATE INDEX IF NOT EXISTS idx_signal_samples_ts ON signal_samples (ts_unix);
CREATE INDEX IF NOT EXISTS idx_signal_samples_name ON signal_samples (message_name, signal_name);
"""


class SQLiteStorage:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        parent = Path(db_path).parent
        if str(parent) not in ("", "."):
            parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, isolation_level=None)
        self._conn.execute("PRAGMA foreign_keys=ON;")

    def close(self) -> None:
        self._conn.close()

    def init_schema(self) -> None:
        self._conn.executescript(SCHEMA_SQL)

    def insert_raw_frame(self, frame: RawFrame) -> None:
        self._conn.execute(
            """
            INSERT INTO raw_frames(ts_unix, channel, arbitration_id, is_extended_id, dlc, data)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                frame.ts_unix,
                frame.channel,
                frame.arbitration_id,
                1 if frame.is_extended_id else 0,
                frame.dlc,
                frame.data,
            ),
        )

    def insert_signal_samples(self, samples: list[SignalSample]) -> None:
        if not samples:
            return
        self._conn.executemany(
            """
            INSERT INTO signal_samples(ts_unix, channel, message_name, signal_name, value, unit)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    s.ts_unix,
                    s.channel,
                    s.message_name,
                    s.signal_name,
                    float(s.value),
                    s.unit,
                )
                for s in samples
            ],
        )

