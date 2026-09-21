import sqlite3
import json

src = sqlite3.connect('migraine.db')
src.row_factory = sqlite3.Row

# Check all tables for JSON-like columns
tables = ['users', 'assessment_questions', 'user_profiles', 'assessment_responses',
          'user_risk_profiles', 'devices', 'sensor_readings', 'migraine_episodes',
          'predictions', 'prediction_features', 'alerts', 'alert_advice',
          'notification_logs', 'datasets']

for t in tables:
    try:
        src.execute(f'SELECT 1 FROM "{t}" LIMIT 1')
    except sqlite3.OperationalError:
        continue
    c = src.execute(f'PRAGMA table_info("{t}")')
    cols = [r[1] for r in c.fetchall()]
    print(f"\n{t} columns: {cols}")
    # Check for JSON-like data
    for col in cols:
        try:
            c2 = src.execute(f'SELECT "{col}" FROM "{t}" WHERE "{col}" IS NOT NULL LIMIT 1')
            r = c2.fetchone()
            if r and r[0] and isinstance(r[0], str) and r[0].strip().startswith(('{', '[')):
                try:
                    json.loads(r[0])
                    print(f"  {col}: VALID JSON: {r[0][:80]}")
                except json.JSONDecodeError as e:
                    print(f"  {col}: INVALID JSON: {r[0][:80]}")
        except:
            pass