import sys
sys.path.insert(0, r'C:\Users\LOQ\Desktop\MigraineDetector\backend')
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from app.db.session import engine, SessionLocal

# Test directly
db = SessionLocal()
try:
    # Get questions
    rows = db.execute(text("SELECT * FROM assessment_questions")).fetchall()
    print(f"Questions: {len(rows)}")
    
    # Insert assessment response
    db.execute(text("INSERT INTO assessment_responses (user_id, question_id, answer) VALUES (1, 1, 'test')"))
    db.commit()
    print("Assessment response inserted")
    
    # Build risk profile
    from app.db.seed import build_risk_profile
    answers = {"Have you experienced migraine or headache episodes before?": {"answer": "Frequently", "type": "single"}}
    build_risk_profile(db, 1, answers)
    print("Risk profile built")
    
    # Get profile
    profile = db.execute(text("SELECT * FROM user_risk_profiles WHERE user_id = 1")).fetchone()
    print(f"Profile: {profile}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
finally:
    db.close()