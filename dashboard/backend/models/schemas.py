from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class ProjectListItem(BaseModel):
    """Schema for project list endpoint - only essential fields."""
    id: str
    name: str
    stage: str
    priority: int
    code_quality_score: float
    languages: list[str]
    has_tests: bool
    has_ci: bool
    fundamental_errors: list[str]
    todo_now: list[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ProjectDetail(BaseModel):
    """Schema for project detail endpoint - all fields + VibeSummary."""
    id: str
    name: str
    path: str
    stage: str
    priority: int
    value_score: float
    risk_score: float
    code_quality_score: float
    languages: list[str]
    deps: dict
    has_readme: bool
    has_license: bool
    has_tests: bool
    has_ci: bool
    commits_count: Optional[int] = None
    branches_count: Optional[int] = None
    last_commit_dt: Optional[datetime] = None
    todos: list[str]
    todo_now: list[str]
    todo_next: list[str]
    fundamental_errors: list[str]
    vibesummary_content: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str
    project_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""
    response: str
    session_id: str
    message_id: str


class ChatMessageSchema(BaseModel):
    """Schema for chat message."""
    id: str
    session_id: str
    role: str
    content: str
    project_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    """Response schema for stats endpoint."""
    total_projects: int
    by_stage: dict[str, int]
    avg_code_quality: float
    projects_with_tests: int
    projects_with_ci: int
