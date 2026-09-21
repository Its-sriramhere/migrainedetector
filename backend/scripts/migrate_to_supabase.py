"""One-time migration of the local SQLite database into Supabase Postgres.

Usage:
    python scripts/migrate_to_supabase.py --target <postgres-url>

Copies every table from the local SQLite app (current ``DATABASE_URL`` when it is
sqlite, or ``--source``) into the target Postgres URL (env ``SUPABASE_DATABASE_URL``
or ``--target``).

- Creates the target schema first (same models as the app) if it is missing.
- Runs in FK-safe order (users -> questions -> profiles -> devices -> readings
  -> episodes -> predictions -> features -> alerts -> advice -> notifications).
- Idempotent: any table that already has rows in the target is skipped.
- Fixes Postgres ``serial`` sequences after explicit-id inserts.

Stop the backend first so nothing writes mid-copy.
"""
import argparse
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))


TABLES = [
    "users",
    "assessment_questions",
    "user_profiles",
    "assessment_responses",
    "user_risk_profiles",
    "devices",
    "sensor_readings",
    "migraine_episodes",
    "predictions",
    "prediction_features",
    "alerts",
    "alert_advice",
    "notification_logs",
    "datasets",
]


def _current_sqlite_url() -> str:
    from app.core.config import settings

    return settings.DATABASE_URL


def _table_has_rows(session: Session, table: str) -> int:
    return session.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar() or 0


def _copy_table(src: Session, dst: Session, table: str) -> str:
    src_rows = [
        dict(r)
        for r in src.execute(text(f'SELECT * FROM "{table}"')).mappings()
    ]
    if not src_rows:
        return "empty"

    placeholders = ", ".join(f":c{i}" for i in range(len(src_rows[0])))
    col_names = ", ".join(f'"{c}"' for c in src_rows[0])
    for row in src_rows:
        dst.execute(
            text(f'INSERT INTO "{table}" ({col_names}) VALUES ({placeholders})'),
            {f"c{i}": v for i, v in enumerate(row.values())},
        )
    dst.commit()
    return f"copied ({len(src_rows)} rows)"


def _bump_sequence(dst: Session, table: str, inspector) -> None:
    pk = None
    for col in inspector.get_columns(table):
        if col.get("primary_key"):
            pk = col["name"]
            break
    if not pk:
        return
    max_id = dst.execute(
        text(f'SELECT COALESCE(MAX("{pk}"), 0) FROM "{table}"')
    ).scalar()
    try:
        dst.execute(
            text(
                f"SELECT setval(pg_get_serial_sequence(:t, :c), :v, true)"
            ),
            {"t": table, "c": pk, "v": max_id},
        )
        dst.commit()
    except Exception:  # noqa: BLE001 - column is not a serial
        dst.rollback()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=None, help="SQLite URL to copy FROM.")
    parser.add_argument(
        "--target",
        default=os.environ.get("SUPABASE_DATABASE_URL"),
        help="Postgres URL to copy INTO (default: env SUPABASE_DATABASE_URL).",
    )
    args = parser.parse_args()

    src_url = args.source or _current_sqlite_url()
    if not src_url.startswith("sqlite"):
        raise SystemExit("--source must be a sqlite URL; refusing to copy from non-SQLite.")
    if not args.target or not args.target.startswith(("postgresql", "postgres")):
        raise SystemExit("--target must be a postgres URL (or set SUPABASE_DATABASE_URL).")

    db_file = src_url.replace("sqlite:///", "").replace("sqlite://", "")
    if not os.path.exists(db_file):
        raise SystemExit(f"source DB file not found: {db_file}")

    src = create_engine(src_url, connect_args={"check_same_thread": False})
    dst = create_engine(args.target, connect_args={"sslmode": "require"})

    from app.models import Base

    dst_insp = inspect(dst)
    Base.metadata.create_all(dst)
    print(f"source: {src_url}")
    host = args.target.split("//")[1].split("@")[-1].split("/")[0]
    print(f"target: {host}")
    print()

    with Session(src) as sdb, Session(dst) as ddb:
        for table in TABLES:
            try:
                count = _table_has_rows(ddb, table)
            except Exception:  # noqa: BLE001
                continue
            if count:
                print(f"  skip   {table:24s} (already {count} rows)")
                continue
            status = _copy_table(sdb, ddb, table)
            _bump_sequence(ddb, table, dst_insp)
            print(f"  {status:24s} <- {table}")

    print("\nMigration finished.")


if __name__ == "__main__":
    main()