import sys
sys.path.insert(0, r'C:\Users\LOQ\Desktop\MigraineDetector\backend')
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from app.db.session import engine, SessionLocal

db = SessionLocal()
try:
    # Test the batch insert syntax
    rows = [{"uid": 1, "qid": i, "ans": f"answer{i}"} for i in range(1, 5)]
    db.execute(
        text("""INSERT INTO assessment_responses (user_id, question_id, answer)
                VALUES (:uid, :qid, :ans)"""),
        rows,
    )
    db.commit()
    print("Batch insert works!")
    result = db.execute(text("SELECT * FROM assessment_responses WHERE user_id = 1")).fetchall()
    print(f"Found {len(result)} rows")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
finally:
    db.close()