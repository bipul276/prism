from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Text
from sqlalchemy.sql import func
from ml.database import Base

class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    source_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="pending") # pending, processing, completed, failed

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id"))
    style_risk_score = Column(Float, nullable=True)
    stance_distribution = Column(JSON, nullable=True)
    explanation = Column(Text, nullable=True)
    linguistic_verdict = Column(Text, nullable=True)
    linguistic_signals = Column(JSON, nullable=True)
    model_version = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
