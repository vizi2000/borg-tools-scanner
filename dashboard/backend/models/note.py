"""
ProjectNote Model - SQLAlchemy ORM for project annotations.

Supports markdown notes with types (general, decision, idea, blocker, todo),
tags for filtering, and full timestamp tracking.

Created by The Collective Borg.tools
"""

import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship
from .database import Base


# Valid note types
NOTE_TYPES = ["general", "decision", "idea", "blocker", "todo"]


class ProjectNote(Base):
    """
    Project annotation model with markdown support.

    Attributes:
        id: UUID primary key
        project_id: Foreign key to projects table
        content: Markdown formatted note content
        note_type: Category (general/decision/idea/blocker/todo)
        tags: JSON array of tag strings for filtering
        created_at: UTC timestamp of creation
        updated_at: UTC timestamp of last update
    """
    __tablename__ = "project_notes"

    # Primary Key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign Key to Project
    project_id = Column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Content
    content = Column(Text, nullable=False)

    # Type classification
    note_type = Column(String(20), nullable=False, default="general", index=True)

    # Tags for filtering/search
    tags = Column(JSON, nullable=False, default=list)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now()
    )

    # Relationship (optional, requires Project model to define relationship back)
    # project = relationship("Project", back_populates="notes")

    def __repr__(self) -> str:
        """String representation of note."""
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<ProjectNote(id={self.id}, type={self.note_type}, content='{content_preview}')>"

    def to_dict(self) -> dict:
        """
        Convert note to dictionary for API responses.

        Returns:
            Dictionary with all note fields, timestamps as ISO strings
        """
        return {
            "id": self.id,
            "project_id": self.project_id,
            "content": self.content,
            "note_type": self.note_type,
            "tags": self.tags or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @staticmethod
    def validate_note_type(note_type: str) -> bool:
        """
        Validate that note_type is one of the allowed values.

        Args:
            note_type: Type string to validate

        Returns:
            True if valid, False otherwise
        """
        return note_type in NOTE_TYPES
