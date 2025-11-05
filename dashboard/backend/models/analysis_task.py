"""
Analysis Task Model - Tracks background deep analysis jobs

Lifecycle: queued → running → completed/failed
Progress: 0.0 - 1.0 (incremental updates via WebSocket)

Created by The Collective Borg.tools
"""

from sqlalchemy import Column, String, Float, JSON, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from .database import Base


class AnalysisTask(Base):
    """
    Background task for deep project analysis

    Tracks progress of:
    - Code analysis (AST-based complexity metrics)
    - Deployment analysis (Docker, env vars, build config)
    - Documentation analysis (README, API docs)
    - LLM analysis (multi-model pipeline - optional)

    Used by /api/projects/{id}/deep-analysis endpoint
    """
    __tablename__ = "analysis_tasks"

    # Primary key
    id = Column(String(36), primary_key=True)  # UUID

    # Foreign key to projects
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)

    # Status tracking
    status = Column(String(20), nullable=False, default="queued", index=True)
    # Allowed values: queued, running, completed, failed

    progress = Column(Float, default=0.0)  # 0.0 - 1.0
    current_phase = Column(String(100), nullable=True)
    # e.g., "Code Analysis", "LLM Analysis (Architect Model)"

    # Results storage (JSON)
    results = Column(JSON, default=dict)
    # Structure:
    # {
    #   "code_analysis": {...},        # From modules/code_analyzer.py
    #   "deployment_analysis": {...},   # From modules/deployment_detector.py
    #   "documentation_analysis": {...},# From modules/doc_analyzer.py
    #   "llm_analysis": {...}           # From modules/llm_orchestrator.py (optional)
    # }

    # Error tracking
    error = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<AnalysisTask {self.id[:8]} ({self.status})>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "status": self.status,
            "progress": self.progress,
            "current_phase": self.current_phase,
            "results": self.results,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
