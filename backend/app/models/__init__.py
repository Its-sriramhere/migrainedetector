from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from ..core.security import utcnow
from ..db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), default="")
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    consent_given = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    date_of_birth = Column(String(20), nullable=True)
    migraine_history = Column(String(60), nullable=True)
    typical_frequency = Column(String(60), nullable=True)
    typical_duration = Column(String(60), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(20), default="single")
    options = Column(JSON, nullable=False, default=list)
    active = Column(Boolean, default=True)


class AssessmentResponse(Base):
    __tablename__ = "assessment_responses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    question_id = Column(Integer, ForeignKey("assessment_questions.id"), nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)
    __table_args__ = (UniqueConstraint("user_id", "question_id", name="uq_user_question"),)


class UserRiskProfile(Base):
    __tablename__ = "user_risk_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    migraine_history_score = Column(Float, default=0.0)
    sleep_profile = Column(String(60), nullable=True)
    stress_profile = Column(String(60), nullable=True)
    activity_profile = Column(String(60), nullable=True)
    hydration_profile = Column(String(60), nullable=True)
    caffeine_profile = Column(String(60), nullable=True)
    trigger_profile = Column(JSON, default=list)
    sleep_hours = Column(Float, nullable=True)
    resting_hr = Column(Float, nullable=True)
    profile_version = Column(String(20), default="v1")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    device_identifier = Column(String(120), unique=True, index=True, nullable=False)
    device_name = Column(String(120), default="Raspberry Pi")
    status = Column(String(20), default="online")
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    source = Column(String(20), default="pi")
    timestamp = Column(DateTime, default=utcnow, index=True)
    heart_rate = Column(Float, nullable=True)
    hrv = Column(Float, nullable=True)
    systolic_bp = Column(Float, nullable=True)
    diastolic_bp = Column(Float, nullable=True)
    spo2 = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    activity = Column(Float, nullable=True)
    signal_quality = Column(Float, default=1.0)


class MigraineEpisode(Base):
    __tablename__ = "migraine_episodes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    severity = Column(String(20), nullable=True)
    symptoms = Column(JSON, default=list)
    trigger = Column(String(120), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    timestamp = Column(DateTime, default=utcnow, index=True)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)
    prediction_window = Column(Integer, default=60)
    model_version = Column(String(20), default="heuristic-v1")
    outcome = Column(String(20), default="pending")
    source = Column(String(20), default="pi")
    created_at = Column(DateTime, default=utcnow)

    @property
    def advice_texts(self) -> list[str]:
        from ..services.advice import build_advice

        return [item["guidance"] for item in build_advice(self.risk_level, self.features)]

    features = relationship("PredictionFeature",
                            backref="prediction",
                            cascade="all, delete-orphan",
                            order_by="PredictionFeature.contribution.desc()")


class PredictionFeature(Base):
    __tablename__ = "prediction_features"

    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), index=True, nullable=False)
    feature_name = Column(String(120), nullable=False)
    feature_value = Column(Float, nullable=True)
    contribution = Column(Float, nullable=False)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=True)
    timestamp = Column(DateTime, default=utcnow, index=True)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    acknowledged = Column(Boolean, default=False)
    feedback = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    advice = relationship(
        "AlertAdvice",
        backref="alert",
        cascade="all, delete-orphan",
        order_by="AlertAdvice.step",
    )

    @property
    def advice_texts(self) -> list[str]:
        return [row.guidance for row in self.advice]


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=True)
    kind = Column(String(20), default="sms")
    provider = Column(String(20), default="mock")
    recipient = Column(String(120), nullable=True)
    risk_level = Column(String(20), nullable=True)
    status = Column(String(20), default="sent")
    detail = Column(String(255), nullable=True)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)


class AlertAdvice(Base):
    """Calming "what to do now" steps attached to an alert (explainable AI)."""

    __tablename__ = "alert_advice"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), index=True, nullable=False)
    step = Column(Integer, default=1, nullable=False)
    guidance = Column(Text, nullable=False)


class DatasetFile(Base):
    """Metadata for the bundled migraine datasets, mirrored to Supabase Storage."""

    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    path = Column(String(1024), nullable=True)
    rows = Column(Integer, default=0)
    columns = Column(JSON, default=list)
    size_bytes = Column(Integer, default=0)
    modified = Column(Float, nullable=True)
    storage_bucket = Column(String(120), default="datasets")
    storage_key = Column(String(255), default="")
    stored = Column(Boolean, default=False)
    uploaded_at = Column(DateTime, nullable=True)