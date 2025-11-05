"""
Notes API - FastAPI CRUD endpoints for project annotations.

Provides full CRUD operations for project notes with markdown support,
type filtering, tagging, and quick note templates.

Created by The Collective Borg.tools
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from models.database import get_db
from models.note import ProjectNote, NOTE_TYPES
from models.project import Project


# Pydantic schemas for request/response validation
class NoteCreate(BaseModel):
    """Schema for creating a new note."""
    content: str = Field(..., min_length=1, max_length=10000, description="Markdown note content")
    note_type: str = Field(default="general", description="Note type (general/decision/idea/blocker/todo)")
    tags: List[str] = Field(default_factory=list, description="List of tags for filtering")

    @validator("note_type")
    def validate_note_type(cls, v):
        """Validate note_type is one of allowed values."""
        if v not in NOTE_TYPES:
            raise ValueError(f"note_type must be one of {NOTE_TYPES}")
        return v

    @validator("tags")
    def validate_tags(cls, v):
        """Validate tags are non-empty strings."""
        if v:
            for tag in v:
                if not isinstance(tag, str) or not tag.strip():
                    raise ValueError("All tags must be non-empty strings")
        return v


class NoteUpdate(BaseModel):
    """Schema for updating an existing note."""
    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    note_type: Optional[str] = None
    tags: Optional[List[str]] = None

    @validator("note_type")
    def validate_note_type(cls, v):
        """Validate note_type if provided."""
        if v is not None and v not in NOTE_TYPES:
            raise ValueError(f"note_type must be one of {NOTE_TYPES}")
        return v

    @validator("tags")
    def validate_tags(cls, v):
        """Validate tags if provided."""
        if v is not None:
            for tag in v:
                if not isinstance(tag, str) or not tag.strip():
                    raise ValueError("All tags must be non-empty strings")
        return v


class QuickNoteCreate(BaseModel):
    """Schema for quick note creation with templates."""
    type: str = Field(..., description="Quick note type: blocker, idea, or decision")
    content: str = Field(..., min_length=1, max_length=10000)

    @validator("type")
    def validate_quick_type(cls, v):
        """Validate quick note type."""
        allowed = ["blocker", "idea", "decision"]
        if v not in allowed:
            raise ValueError(f"Quick note type must be one of {allowed}")
        return v


class NoteResponse(BaseModel):
    """Schema for note responses."""
    id: str
    project_id: str
    content: str
    note_type: str
    tags: List[str]
    created_at: Optional[str]
    updated_at: Optional[str]

    class Config:
        from_attributes = True


# Create router
router = APIRouter()


# Template content for quick notes
QUICK_NOTE_TEMPLATES = {
    "blocker": "🚫 **BLOCKER**\n\n{content}\n\n---\n*Quick blocker note*",
    "idea": "💡 **IDEA**\n\n{content}\n\n---\n*Quick idea note*",
    "decision": "✅ **DECISION**\n\n{content}\n\n---\n*Quick decision note*",
}


@router.get("/projects/{project_id}/notes", response_model=List[NoteResponse])
def get_project_notes(
    project_id: str,
    note_type: Optional[str] = Query(None, description="Filter by note type"),
    db: Session = Depends(get_db)
) -> List[dict]:
    """
    Get all notes for a specific project.

    Args:
        project_id: UUID of the project
        note_type: Optional filter by note type
        db: Database session

    Returns:
        List of notes matching filters

    Raises:
        HTTPException: 404 if project not found
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    # Build query
    query = db.query(ProjectNote).filter(ProjectNote.project_id == project_id)

    # Apply note_type filter if provided
    if note_type:
        if note_type not in NOTE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid note_type. Must be one of {NOTE_TYPES}"
            )
        query = query.filter(ProjectNote.note_type == note_type)

    # Order by created_at descending (newest first)
    notes = query.order_by(ProjectNote.created_at.desc()).all()

    return [note.to_dict() for note in notes]


@router.post("/projects/{project_id}/notes", response_model=NoteResponse, status_code=201)
def create_note(
    project_id: str,
    note_data: NoteCreate,
    db: Session = Depends(get_db)
) -> dict:
    """
    Create a new note for a project.

    Args:
        project_id: UUID of the project
        note_data: Note creation data
        db: Database session

    Returns:
        Created note

    Raises:
        HTTPException: 404 if project not found, 400 if validation fails
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    # Create new note
    new_note = ProjectNote(
        project_id=project_id,
        content=note_data.content,
        note_type=note_data.note_type,
        tags=note_data.tags or []
    )

    db.add(new_note)
    db.commit()
    db.refresh(new_note)

    return new_note.to_dict()


@router.put("/notes/{note_id}", response_model=NoteResponse)
def update_note(
    note_id: str,
    note_data: NoteUpdate,
    db: Session = Depends(get_db)
) -> dict:
    """
    Update an existing note.

    Args:
        note_id: UUID of the note to update
        note_data: Note update data (only provided fields will be updated)
        db: Database session

    Returns:
        Updated note

    Raises:
        HTTPException: 404 if note not found, 400 if validation fails
    """
    # Find note
    note = db.query(ProjectNote).filter(ProjectNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail=f"Note {note_id} not found")

    # Update fields if provided
    if note_data.content is not None:
        note.content = note_data.content

    if note_data.note_type is not None:
        note.note_type = note_data.note_type

    if note_data.tags is not None:
        note.tags = note_data.tags

    # Manually set updated_at since onupdate may not trigger reliably
    note.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(note)

    return note.to_dict()


@router.delete("/notes/{note_id}", status_code=204)
def delete_note(
    note_id: str,
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a note (hard delete).

    Args:
        note_id: UUID of the note to delete
        db: Database session

    Raises:
        HTTPException: 404 if note not found
    """
    # Find note
    note = db.query(ProjectNote).filter(ProjectNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail=f"Note {note_id} not found")

    # Hard delete
    db.delete(note)
    db.commit()


@router.post("/projects/{project_id}/notes/quick", response_model=NoteResponse, status_code=201)
def create_quick_note(
    project_id: str,
    quick_note: QuickNoteCreate,
    db: Session = Depends(get_db)
) -> dict:
    """
    Create a quick note with template formatting.

    This endpoint provides a simplified interface for creating common note types
    (blocker, idea, decision) with pre-formatted markdown templates.

    Args:
        project_id: UUID of the project
        quick_note: Quick note data (type and content)
        db: Database session

    Returns:
        Created note with template-formatted content

    Raises:
        HTTPException: 404 if project not found, 400 if validation fails
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    # Get template and format content
    template = QUICK_NOTE_TEMPLATES[quick_note.type]
    formatted_content = template.format(content=quick_note.content)

    # Auto-tag based on type
    auto_tags = [quick_note.type]

    # Create note with template content
    new_note = ProjectNote(
        project_id=project_id,
        content=formatted_content,
        note_type=quick_note.type,
        tags=auto_tags
    )

    db.add(new_note)
    db.commit()
    db.refresh(new_note)

    return new_note.to_dict()
