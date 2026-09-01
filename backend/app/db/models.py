from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.database import Base

class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    analyses = relationship("AnalysisModel", back_populates="user", cascade="all, delete-orphan")


class AnalysisModel(Base):
    __tablename__ = "analyses"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    dataset_id = Column(String(64), nullable=True, index=True)
    filename = Column(String(255), nullable=True)
    question = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="CREATED", index=True)  # CREATED, QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED
    
    # Progress & Job Stage
    job_stage = Column(String(64), nullable=False, default="UNDERSTANDING_QUESTION")
    job_progress = Column(Integer, nullable=False, default=0)
    
    # Provider metadata & failover tracking
    provider_used = Column(String(32), nullable=True)
    fallback_used = Column(Boolean, nullable=True, default=False)
    fallback_reason = Column(Text, nullable=True)
    
    # Structured analytical results stored as JSON
    dataset_profile = Column(JSON, nullable=True)
    investigation_plan = Column(JSON, nullable=True)
    hypotheses = Column(JSON, nullable=True)
    executed_analyses = Column(JSON, nullable=True)
    evidence = Column(JSON, nullable=True)
    alternative_explanations = Column(JSON, nullable=True)
    validation = Column(JSON, nullable=True)
    confidence = Column(String(32), nullable=True)
    conclusion = Column(Text, nullable=True)
    recommendations = Column(JSON, nullable=True)
    limitations = Column(JSON, nullable=True)
    error_summary = Column(Text, nullable=True)

    # Phase 9 Advanced Autonomous Scientist fields
    evidence_graph = Column(JSON, nullable=True)
    audit_trail = Column(JSON, nullable=True)
    what_if_analysis = Column(JSON, nullable=True)
    predictions = Column(JSON, nullable=True)
    contradictions = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("UserModel", back_populates="analyses")
    messages = relationship("ChatMessageModel", back_populates="analysis", cascade="all, delete-orphan")


class ChatMessageModel(Base):
    __tablename__ = "chat_messages"

    id = Column(String(64), primary_key=True, index=True)
    analysis_id = Column(String(64), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(16), nullable=False)  # USER or ASSISTANT / AI
    text = Column(Text, nullable=False)
    confidence = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    analysis = relationship("AnalysisModel", back_populates="messages")


class DatasetModel(Base):
    __tablename__ = "datasets"

    id = Column(String(64), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    rows = Column(Integer, nullable=True)
    columns = Column(Integer, nullable=True)
    column_names = Column(JSON, nullable=True)
    file_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
