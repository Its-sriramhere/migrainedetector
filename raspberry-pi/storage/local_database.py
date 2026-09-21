"""Local SQLite buffer so measurements are never lost during outages."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class LocalDatabase:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._create()

    def _create(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS local_sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                heart_rate REAL,
                hrv REAL,
                spo2 REAL,
                systolic_bp REAL,
                diastolic_bp REAL,
                temperature REAL,
                activity REAL,
                signal_quality REAL,
                uploaded INTEGER DEFAULT 0
            )
            """
        )
        self._conn.commit()

    def save(self, sample: dict) -> int:
        cursor = self._conn.execute(
            """
            INSERT INTO local_sensor_data
                (timestamp, heart_rate, hrv, spo2, systolic_bp, diastolic_bp,
                 temperature, activity, signal_quality, uploaded)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                sample.get("timestamp") or _now(),
                sample.get("heart_rate"),
                sample.get("hrv"),
                sample.get("spo2"),
                sample.get("systolic_bp"),
                sample.get("diastolic_bp"),
                sample.get("temperature"),
                sample.get("activity"),
                sample.get("signal_quality"),
            ),
        )
        self._conn.commit()
        return cursor.lastrowid

    def pending(self, limit: int = 100) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM local_sensor_data WHERE uploaded = 0 ORDER BY id LIMIT ?", (limit,)
        ).fetchall()
        columns = [c[0] for c in self._conn.execute("SELECT * FROM local_sensor_data LIMIT 1").description]
        return list(map(dict, zip([columns] * len(rows), rows))) if rows else []

    def mark_uploaded(self, ids: list[int]) -> None:
        if not ids:
            return
        placeholders = ",".join("?" for _ in ids)
        self._conn.execute(
            f"UPDATE local_sensor_data SET uploaded = 1 WHERE id IN ({placeholders})", ids
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def stats(self) -> dict:
        total, pending = self._conn.execute(
            "SELECT COUNT(*), SUM(uploaded = 0) FROM local_sensor_data"
        ).fetchone()
        return {"total": total or 0, "pending": pending or 0}