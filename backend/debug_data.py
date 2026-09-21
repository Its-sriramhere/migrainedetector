import sqlite3
import json

s = sqlite3.connect('migraine.db')
s.row_factory = sqlite3.Row

tables = ['users', 'assessment_questions', 'user_profiles', 'assessment_responses',
          'user_risk_profiles', 'devices', 'sensor_readings', 'migraine_episodes',
          'predictions', 'prediction_features', 'alerts', 'alert_advice',
          'notification_logs', 'datasets']

for t in tables:
    c = s.execute(f'SELECT COUNT(*) FROM "{t}"')
    print(f"{t}: {c.fetchone()[0]} rows")

# Check JSON columns in assessment_questions
print("\nassessment_questions options sample:")
c = s.execute('SELECT options FROM assessment_questions LIMIT 3')
for r in c.fetchall():
    print(f"  {r['options'][:100] if r['options'] else None}")

# Check migraine_episodes symptoms
print("\nChecking migraine_episodes symptoms:")
c = s.execute('SELECT symptoms, trigger, notes FROM migraine_episodes LIMIT 3')
for r in c.fetchall():
    print(f"  symptoms={r['symptoms']}, trigger={r['trigger']}")