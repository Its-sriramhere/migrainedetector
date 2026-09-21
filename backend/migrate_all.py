import sqlite3
import psycopg
from psycopg.types.json import Json
import json
import sys
sys.path.insert(0, '.')

src = sqlite3.connect('migraine.db')
src.row_factory = sqlite3.Row

dst = psycopg.connect(host='db.lrulmcudqdlidhldncok.supabase.co', port=5432, dbname='postgres', user='postgres', password='Headachepps@247', sslmode='require')
dst.autocommit = True
cur = dst.cursor()

TABLES = ["users", "assessment_questions", "user_profiles", "assessment_responses",
          "user_risk_profiles", "devices", "sensor_readings", "migraine_episodes",
          "predictions", "prediction_features", "alerts", "alert_advice",
          "notification_logs", "datasets"]

BOOLEAN_COLS = {"consent_given", "active", "acknowledged", "stored"}
JSON_COLS = {"options", "trigger_profile", "symptoms", "columns", "metadata"}

def _conv(col, v):
    if v is None: return None
    if col in BOOLEAN_COLS: return bool(v)
    if col in JSON_COLS and isinstance(v, str):
        try:
            parsed = json.loads(v)
            return Json(parsed)
        except (json.JSONDecodeError, TypeError):
            return Json(v)
    if isinstance(v, str) and len(v) > 20 and col in ("model_version", "outcome", "status", "feedback", "source"):
        v = v[:20]
    return v

for table in TABLES:
    try:
        src.execute(f'SELECT 1 FROM "{table}" LIMIT 1')
    except sqlite3.OperationalError:
        print(f"  skip   {table:24s} (not in SQLite)")
        continue
    cur.execute(f'TRUNCATE TABLE "{table}" CASCADE')
    src_cur = src.execute(f'SELECT * FROM "{table}"')
    rows = src_cur.fetchall()
    if not rows:
        print(f"  empty   <- {table}")
        continue
    cols = [d[0] for d in src_cur.description]
    col_str = ', '.join(f'"{c}"' for c in cols)
    placeholders = ', '.join(['%s'] * len(cols))
    insert_sql = f'INSERT INTO "{table}" ({col_str}) VALUES ({placeholders})'
    data = [tuple(_conv(c, row[c]) for c in cols) for row in rows]
    cur.executemany(insert_sql, data)
    print(f"  copied ({len(data)} rows) <- {table}")

cur.close(); dst.close(); src.close()
print("\nMigration finished.")