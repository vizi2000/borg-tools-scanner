import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, Index
from sqlalchemy.dialects.sqlite import JSON
from .database import Base


class Project(Base):
    __tablename__ = "projects"

    # Primary Key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Basic Info
    name = Column(String(200), nullable=False, index=True)
    path = Column(String(500), nullable=False, unique=True)
    stage = Column(String(50), nullable=False, index=True)  # idea/prototype/mvp/beta/production/abandoned

    # Scores
    priority = Column(Integer, nullable=False, index=True)  # 0-20
    value_score = Column(Float, nullable=False)  # 0-10
    risk_score = Column(Float, nullable=False)  # 0-10
    code_quality_score = Column(Float, nullable=False, default=0.0)  # 0-10, extracted from vibe_notes

    # Languages & Dependencies
    languages = Column(JSON, nullable=False, default=list)  # ["python", "node"]
    deps = Column(JSON, nullable=False, default=dict)  # {node: [...], python: [...]}

    # Boolean Flags
    has_readme = Column(Boolean, nullable=False, default=False)
    has_license = Column(Boolean, nullable=False, default=False)
    has_tests = Column(Boolean, nullable=False, default=False)
    has_ci = Column(Boolean, nullable=False, default=False)

    # Git Stats
    commits_count = Column(Integer, nullable=True)
    branches_count = Column(Integer, nullable=True)
    last_commit_dt = Column(DateTime, nullable=True)

    # TODOs
    todos = Column(JSON, nullable=False, default=list)  # list of TODO strings
    todo_now = Column(JSON, nullable=False, default=list)  # from suggestions.todo_now
    todo_next = Column(JSON, nullable=False, default=list)  # from suggestions.todo_next

    # Errors
    fundamental_errors = Column(JSON, nullable=False, default=list)  # ["brak CI", "brak LICENSE"]

    # Raw Data
    raw_data = Column(JSON, nullable=False)  # Complete borg_dashboard.json entry

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<Project(name={self.name}, stage={self.stage}, priority={self.priority})>"
