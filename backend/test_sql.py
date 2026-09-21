import sys
sys.path.insert(0, r'C:\Users\LOQ\Desktop\MigraineDetector\backend')
from sqlalchemy import create_engine, text
engine = create_engine('sqlite:///./migraine.db')
conn = engine.connect()
conn.execute(text('CREATE TABLE IF NOT EXISTS test_batch (id INTEGER, name TEXT)'))
conn.execute(text('INSERT INTO test_batch VALUES (1, "a"), (2, "b")'))
result = conn.execute(text('SELECT * FROM test_batch')).fetchall()
print('Batch insert works:', result)
conn.close()