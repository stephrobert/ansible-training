"""Persistence SQLite des runs pytest.

Schéma versionné (table `schema_version` pour migrations futures).
Stocke chaque run pytest avec son score, sa durée, et le détail des tests.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

DB_VERSION = 1


def default_db_path() -> Path:
    """Chemin par défaut de la DB (override : env DSOXLAB_DB).

    XDG : ~/.local/share/dsoxlab/progress.db (partagé avec le futur outil
    dsoxlab standalone).
    """
    override = os.environ.get("DSOXLAB_DB")
    if override:
        return Path(override)
    xdg_data = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    base = xdg_data / "dsoxlab"
    base.mkdir(parents=True, exist_ok=True)
    return base / "progress.db"


_SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lab_path TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    duration_seconds REAL,
    tests_total INTEGER NOT NULL DEFAULT 0,
    tests_passed INTEGER NOT NULL DEFAULT 0,
    tests_failed INTEGER NOT NULL DEFAULT 0,
    tests_skipped INTEGER NOT NULL DEFAULT 0,
    score_percent REAL,
    status TEXT NOT NULL DEFAULT 'started'
);
CREATE INDEX IF NOT EXISTS idx_runs_lab_path ON runs(lab_path);
CREATE INDEX IF NOT EXISTS idx_runs_started_at ON runs(started_at DESC);

CREATE TABLE IF NOT EXISTS test_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    test_name TEXT NOT NULL,
    status TEXT NOT NULL,
    duration_seconds REAL,
    failure_message TEXT
);
CREATE INDEX IF NOT EXISTS idx_test_results_run_id ON test_results(run_id);
"""


def init_db(db_path: Path | None = None) -> Path:
    """Crée la DB + schéma si absent. Idempotent."""
    if db_path is None:
        db_path = default_db_path()
    with sqlite3.connect(db_path) as conn:
        conn.executescript(_SCHEMA)
        cur = conn.execute("SELECT MAX(version) FROM schema_version")
        current = cur.fetchone()[0]
        if current is None:
            conn.execute(
                "INSERT INTO schema_version(version) VALUES (?)", (DB_VERSION,)
            )
        conn.commit()
    return db_path


@contextmanager
def get_conn(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Context manager — connection SQLite avec row_factory dict-like."""
    if db_path is None:
        db_path = default_db_path()
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ------------------------------------------------------------------ Runs

def insert_run_started(conn: sqlite3.Connection, lab_path: str) -> int:
    """Démarre un run (status='started', tests à 0). Retourne l'ID."""
    cur = conn.execute(
        """INSERT INTO runs(lab_path, started_at, status)
           VALUES (?, ?, 'started')""",
        (lab_path, datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")),
    )
    return cur.lastrowid


def finalize_run(
    conn: sqlite3.Connection,
    run_id: int,
    *,
    total: int,
    passed: int,
    failed: int,
    skipped: int,
) -> None:
    """Finalise un run : compte les tests, calcule score et durée."""
    cur = conn.execute("SELECT started_at FROM runs WHERE id = ?", (run_id,))
    row = cur.fetchone()
    if row is None:
        return
    started_at = datetime.fromisoformat(row["started_at"])
    finished_at = datetime.now(timezone.utc).replace(tzinfo=None)
    duration = (finished_at - started_at).total_seconds()

    # Score : 100 % si total - skipped == passed, sinon ratio
    runnable = total - skipped
    score = 100.0 if runnable == 0 else round(100.0 * passed / runnable, 1)

    if failed == 0 and runnable > 0:
        status = "completed"
    elif passed == 0 and failed > 0:
        status = "failed"
    elif failed > 0:
        status = "in_progress"
    elif total > 0 and skipped == total:
        status = "skipped"
    else:
        status = "in_progress"

    conn.execute(
        """UPDATE runs SET
            finished_at = ?,
            duration_seconds = ?,
            tests_total = ?,
            tests_passed = ?,
            tests_failed = ?,
            tests_skipped = ?,
            score_percent = ?,
            status = ?
           WHERE id = ?""",
        (
            finished_at.isoformat(timespec="seconds"),
            duration,
            total,
            passed,
            failed,
            skipped,
            score,
            status,
            run_id,
        ),
    )


def insert_test_result(
    conn: sqlite3.Connection,
    run_id: int,
    test_name: str,
    status: str,
    duration: float | None,
    failure_message: str | None,
) -> None:
    conn.execute(
        """INSERT INTO test_results(run_id, test_name, status, duration_seconds, failure_message)
           VALUES (?, ?, ?, ?, ?)""",
        (run_id, test_name, status, duration, failure_message),
    )


# ------------------------------------------------------------------ Queries

def best_run_per_lab(conn: sqlite3.Connection) -> dict[str, sqlite3.Row]:
    """Retourne, pour chaque lab_path, le run avec le meilleur score (puis le plus récent)."""
    cur = conn.execute(
        """SELECT r.* FROM runs r
           WHERE r.id = (
               SELECT id FROM runs
               WHERE lab_path = r.lab_path
               ORDER BY score_percent DESC NULLS LAST, started_at DESC
               LIMIT 1
           )"""
    )
    return {row["lab_path"]: row for row in cur.fetchall()}


def last_run_per_lab(conn: sqlite3.Connection) -> dict[str, sqlite3.Row]:
    """Retourne le dernier run pour chaque lab_path."""
    cur = conn.execute(
        """SELECT r.* FROM runs r
           WHERE r.id = (
               SELECT id FROM runs
               WHERE lab_path = r.lab_path
               ORDER BY started_at DESC
               LIMIT 1
           )"""
    )
    return {row["lab_path"]: row for row in cur.fetchall()}


def all_runs_for_lab(conn: sqlite3.Connection, lab_path: str) -> list[sqlite3.Row]:
    cur = conn.execute(
        "SELECT * FROM runs WHERE lab_path = ? ORDER BY started_at DESC",
        (lab_path,),
    )
    return list(cur.fetchall())


def reset_lab(conn: sqlite3.Connection, lab_path: str) -> int:
    """Supprime tous les runs d'un lab. Retourne le nombre supprimé."""
    cur = conn.execute("DELETE FROM runs WHERE lab_path = ?", (lab_path,))
    return cur.rowcount


def reset_all(conn: sqlite3.Connection) -> int:
    cur = conn.execute("DELETE FROM runs")
    return cur.rowcount
