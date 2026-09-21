import sqlite3
import json

src = sqlite3.connect('migraine.db')
src.row_factory = sqlite3.Row

# Check assessment_responses answer column
c = src.execute('SELECT answer FROM assessment_responses WHERE answer LIKE "{%" LIMIT 3')
for r in c.fetchall():
    print(f"answer: {repr(r['answer'])[:200]}")

# Also check user_risk_profiles trigger_profile for non-empty values
c = src.execute('SELECT trigger_profile FROM user_risk_profiles WHERE trigger_profile != "[]" AND trigger_profile IS NOT NULL LIMIT 3')
for r in c.fetchall():
    print(f"trigger_profile: {repr(r['trigger_profile'])[:200]}")

# Check all tables for values starting with {
tables = ['users', 'assessment_questions', 'assessment_responses', 'user_risk_profiles', 'devices',
          'sensor_readings', 'predictions', 'prediction_features', 'alerts']
for t in tables:
    try:
        c = src.execute(f'SELECT * FROM "{t}" WHERE CAST(ROWID AS TEXT) IS NOT NULL LIMIT 5')
        cols = [d[0] for d in c.description]
        for r in c.fetchall():
            for col in cols:
                v = r[col]
                if isinstance(v, str) and v.strip().startswith('{'):
                    try:
                        json.loads(v)
                    except json.JSONDecodeError:
                        print(f"{t}.{col}: INVALID JSON: {v[:100]}")
    except:
        pass