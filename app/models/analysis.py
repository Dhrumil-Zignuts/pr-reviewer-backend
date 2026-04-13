from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
    JSON,
    Boolean,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    repo_owner = Column(String, index=True, nullable=False)
    repo_name = Column(String, index=True, nullable=False)
    pull_number = Column(Integer, index=True, nullable=False)
    overall_summary = Column(Text, nullable=True)
    overall_risk_score = Column(Float, nullable=True)
    final_recommendation = Column(String, nullable=True)
    status = Column(String, default="pending", nullable=False)
    error_message = Column(Text, nullable=True)
    is_notified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    reviews = relationship(
        "AnalysisReview", back_populates="analysis", cascade="all, delete-orphan"
    )


class AnalysisReview(Base):
    __tablename__ = "analysis_reviews"

    id = Column(Integer, primary_key=True)
    analysis_id = Column(
        Integer, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False
    )
    filename = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    issues = Column(
        JSON, nullable=True
    )  # List of dicts: {"description": str, "snippet": str}
    risk_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    analysis = relationship("Analysis", back_populates="reviews")
