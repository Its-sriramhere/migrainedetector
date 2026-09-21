import sys
sys.path.insert(0, '.')
from app.db.session import engine, Base
from app.models import User, UserProfile, AssessmentQuestion, AssessmentResponse, UserRiskProfile, Device, SensorReading, MigraineEpisode, Prediction, PredictionFeature, Alert, NotificationLog, AlertAdvice, DatasetFile

Base.metadata.create_all(engine)
print("All tables created in Supabase!")