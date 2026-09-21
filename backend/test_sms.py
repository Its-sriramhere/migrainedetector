import sys
sys.path.insert(0, r'C:\Users\LOQ\Desktop\MigraineDetector\backend')
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from app.services.notifications import send_alert_notification

engine = create_engine('sqlite:///./migraine.db', connect_args={'check_same_thread': False})
db = Session(engine)
db.execute(text('DELETE FROM notification_logs'))
db.commit()

r1 = send_alert_notification(db, 1, 1, 'high', 'Migraine detector alert')
print('Send 1:', r1.status, '|', r1.provider)

r2 = send_alert_notification(db, 1, 1, 'high', 'Migraine detector alert 2')
print('Send 2:', r2.status, '|', r2.provider)

logs = db.execute(text('SELECT id, provider, status FROM notification_logs')).fetchall()
for l in logs:
    print(f'  Log {l[0]}: {l[1]}/{l[2]}')

quota = db.execute(text('SELECT COUNT(*) FROM notification_logs WHERE provider=\'twilio\'')).fetchone()
print('Twilio attempts:', quota[0], '/ max 2')