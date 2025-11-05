"""Projects API endpoints."""

import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.database import get_db
from models.project import Project
from models.schemas import ProjectListItem, ProjectDetail, StatsResponse

router = APIRouter()


@router.get("/projects", response_model=list[ProjectListItem])
def list_projects(
    stage: Optional[str] = Query(None, description="Filter by stage"),
    has_tests: Optional[bool] = Query(None, description="Filter by has_tests"),
    has_ci: Optional[bool] = Query(None, description="Filter by has_ci"),
    min_quality: Optional[float] = Query(None, description="Minimum code quality score"),
    search: Optional[str] = Query(None, description="Search in project name"),
    sort: str = Query("priority", description="Sort by: priority, code_quality_score, name"),
    order: str = Query("desc", description="Order: asc or desc"),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List all projects with optional filtering and sorting."""

    query = db.query(Project)

    # Apply filters
    if stage:
        query = query.filter(Project.stage == stage)
    if has_tests is not None:
        query = query.filter(Project.has_tests == has_tests)
    if has_ci is not None:
        query = query.filter(Project.has_ci == has_ci)
    if min_quality is not None:
        query = query.filter(Project.code_quality_score >= min_quality)
    if search:
        query = query.filter(Project.name.ilike(f"%{search}%"))

    # Apply sorting
    if sort == "priority":
        order_by = Project.priority.desc() if order == "desc" else Project.priority.asc()
    elif sort == "code_quality_score":
        order_by = Project.code_quality_score.desc() if order == "desc" else Project.code_quality_score.asc()
    elif sort == "name":
        order_by = Project.name.desc() if order == "desc" else Project.name.asc()
    else:
        order_by = Project.priority.desc()

    query = query.order_by(order_by)

    # Apply pagination
    query = query.limit(limit).offset(offset)

    projects = query.all()

    # Convert to response model
    return [
        ProjectListItem(
            id=p.id,
            name=p.name,
            stage=p.stage,
            priority=p.priority,
            code_quality_score=p.code_quality_score,
            languages=p.languages or [],
            has_tests=p.has_tests,
            has_ci=p.has_ci,
            fundamental_errors=p.fundamental_errors or [],
            todo_now=(p.todo_now or [])[:3],  # Max 3 items
        )
        for p in projects
    ]


@router.get("/projects/{project_id}", response_model=ProjectDetail)
def get_project_detail(
    project_id: str,
    db: Session = Depends(get_db),
):
    """Get detailed information about a specific project."""

    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Try to load VibeSummary.md content
    vibesummary_content = None
    vibesummary_path = os.path.join(project.path, "VibeSummary.md")

    if os.path.exists(vibesummary_path):
        try:
            with open(vibesummary_path, "r", encoding="utf-8") as f:
                vibesummary_content = f.read()
        except Exception as e:
            # If we can't read the file, just skip it
            print(f"Warning: Could not read VibeSummary.md for {project.name}: {e}")

    return ProjectDetail(
        id=project.id,
        name=project.name,
        path=project.path,
        stage=project.stage,
        priority=project.priority,
        value_score=project.value_score,
        risk_score=project.risk_score,
        code_quality_score=project.code_quality_score,
        languages=project.languages or [],
        deps=project.deps or {},
        has_readme=project.has_readme,
        has_license=project.has_license,
        has_tests=project.has_tests,
        has_ci=project.has_ci,
        commits_count=project.commits_count,
        branches_count=project.branches_count,
        last_commit_dt=project.last_commit_dt,
        todos=project.todos or [],
        todo_now=project.todo_now or [],
        todo_next=project.todo_next or [],
        fundamental_errors=project.fundamental_errors or [],
        vibesummary_content=vibesummary_content,
        created_at=project.created_at,
    )


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    """Get portfolio statistics."""

    total = db.query(func.count(Project.id)).scalar()

    # Count by stage
    by_stage_raw = (
        db.query(Project.stage, func.count(Project.id))
        .group_by(Project.stage)
        .all()
    )
    by_stage = {stage: count for stage, count in by_stage_raw}

    # Average code quality
    avg_quality = db.query(func.avg(Project.code_quality_score)).scalar() or 0.0

    # Projects with tests/CI
    with_tests = db.query(func.count(Project.id)).filter(Project.has_tests == True).scalar()
    with_ci = db.query(func.count(Project.id)).filter(Project.has_ci == True).scalar()

    return StatsResponse(
        total_projects=total,
        by_stage=by_stage,
        avg_code_quality=round(avg_quality, 2),
        projects_with_tests=with_tests,
        projects_with_ci=with_ci,
    )
