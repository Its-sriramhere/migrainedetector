import sqlite3
import psycopg
import json
import sys
sys.path.insert(0, '.')

# Connect to SQLite
src = sqlite3.connect('migraine.db')
src.row_factory = sqlite3.Row

# Connect to Supabase
dst = psycopg.connect(host='db.lrulmcudqdlidhldncok.supabase.co', port=5432, dbname='postgres', user='postgres', password='Headachepps@247', sslmode='require')
dst.autocommit = True
cur = dst.cursor()

TABLES = [
    "users", "assessment_questions", "user_profiles", "assessment_responses",
    "user_risk_profiles", "devices", "sensor_readings", "migraine_episodes",
    "predictions", "prediction_features", "alerts", "alert_advice",
    "notification_logs", "datasets"
]

JSON_COLS = {"options", "trigger_profile", "symptoms", "trigger", "columns", "metadata"}

def _convert(col, v):
    if v is None:
        return None
    if col in BOOLEAN_COLS:
        return bool(v)
    if col in JSON_COLS:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return v
        return v
    return v

for table in TABLES:
    # Check if target has rows
    cur.execute(f'SELECT COUNT(*) FROM "{table}"')
    count = cur.fetchone()[0]
    if count > 0:
        print(f"  skip   {table:24s} (already {count} rows)")
        continue

    # Get rows from SQLite
    src_cur = src.execute(f'SELECT * FROM "{table}"')
    rows = src_cur.fetchall()
    if not rows:
        print(f"  empty   <- {table}")
        continue

    cols = [desc[0] for desc in src_cur.description]
    col_str = ', '.join(f'"{c}"' for c in cols)
    placeholders = ', '.join(['%s'] * len(cols))
    insert_sql = f'INSERT INTO "{table}" ({col_str}) VALUES ({placeholders})'

    data = []
    for row in rows:
        vals = [_convert(col, row[col]) for col in cols]
        data.append(tuple(vals))

    cur.executemany(insert_sql, data)
    print(f"  copied ({len(data)} rows) <- {table}")

cur.close()
dst.close()
src.close()
print("\nMigration finished.")