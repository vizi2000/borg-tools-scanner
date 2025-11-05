"""
Deep Analysis API - Background task execution with WebSocket progress updates

Provides endpoints for:
- POST /api/projects/{project_id}/deep-analysis - Queue deep analysis task
- GET /api/analysis/{task_id}/status - Get task status
- WebSocket /ws/analysis/{task_id} - Real-time progress updates

Orchestrates:
1. Code Analysis (AST-based complexity metrics)
2. Deployment Detection (Docker, env vars, build config)
3. Documentation Analysis (README, API docs)
4. LLM Analysis (multi-model pipeline - optional)

Created by The Collective Borg.tools
"""

import asyncio
import sys
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    HTTPException,
    Query
)
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

# Add modules directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "modules"))

from models.database import get_db
from models.project import Project
from models.analysis_task import AnalysisTask

# Import analysis modules
from code_analyzer import analyze_code
from deployment_detector import detect_deployment
from doc_analyzer import analyze_documentation
from llm_orchestrator import analyze_with_llm


router = APIRouter()


# ============================================================================
# WebSocket Connection Manager
# ============================================================================


class ConnectionManager:
    """
    Manages WebSocket connections for real-time progress updates.

    Supports multiple clients per task_id (e.g., user opens multiple tabs)
    """

    def __init__(self):
        # task_id -> list of WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, task_id: str, websocket: WebSocket):
        """Accept new WebSocket connection for task_id"""
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = []
        self.active_connections[task_id].append(websocket)
        print(f"✅ WebSocket connected for task {task_id[:8]} (total: {len(self.active_connections[task_id])})")

    def disconnect(self, task_id: str, websocket: WebSocket):
        """Remove WebSocket connection"""
        if task_id in self.active_connections:
            if websocket in self.active_connections[task_id]:
                self.active_connections[task_id].remove(websocket)
                print(f"❌ WebSocket disconnected for task {task_id[:8]} (remaining: {len(self.active_connections[task_id])})")

            # Clean up empty lists
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]

    async def send_update(self, task_id: str, message: Dict[str, Any]):
        """
        Broadcast update to all connected clients for task_id

        Args:
            task_id: Analysis task UUID
            message: JSON-serializable dict with progress update
        """
        if task_id not in self.active_connections:
            return

        # Send to all connected clients
        disconnected = []
        for websocket in self.active_connections[task_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"⚠️  Failed to send WebSocket message: {e}")
                disconnected.append(websocket)

        # Clean up disconnected clients
        for ws in disconnected:
            self.disconnect(task_id, ws)


# Global connection manager instance
manager = ConnectionManager()


# ============================================================================
# Background Task: Deep Analysis Orchestration
# ============================================================================


async def run_deep_analysis(
    task_id: str,
    project_id: str,
    include_llm: bool,
    db_path: str
):
    """
    Background task that runs complete deep analysis pipeline.

    Pipeline stages:
    1. Code Analysis (0.0 → 0.33)
    2. Deployment Detection (0.33 → 0.66)
    3. Documentation Analysis (0.66 → 0.75)
    4. LLM Analysis - optional (0.75 → 1.0)

    Updates database and sends WebSocket notifications at each stage.

    Args:
        task_id: AnalysisTask UUID
        project_id: Project UUID
        include_llm: Whether to run LLM analysis
        db_path: Path to SQLite database (for thread-safe session creation)
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Create thread-safe database session
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    # Initialize task variable (may be None if error occurs before loading)
    task = None

    try:
        # Load task and project
        task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        project = db.query(Project).filter(Project.id == project_id).first()

        if not task or not project:
            raise Exception(f"Task or project not found: {task_id}, {project_id}")

        # Initialize task
        task.status = "running"
        task.progress = 0.0
        task.current_phase = "Initializing"
        db.commit()

        await manager.send_update(task_id, {
            "type": "progress",
            "progress": 0.0,
            "phase": "Initializing",
            "status": "running"
        })

        results = {}

        # ================================================================
        # Stage 1: Code Analysis (0.0 → 0.33)
        # ================================================================

        try:
            task.current_phase = "Code Analysis"
            task.progress = 0.05
            db.commit()

            await manager.send_update(task_id, {
                "type": "progress",
                "progress": 0.05,
                "phase": "Code Analysis",
                "status": "running"
            })

            print(f"  📊 Running code analysis for {project.name}...")
            code_results = analyze_code(
                project_path=project.path,
                languages=project.languages or []
            )
            results["code_analysis"] = code_results

            task.progress = 0.33
            task.results = results
            db.commit()

            await manager.send_update(task_id, {
                "type": "progress",
                "progress": 0.33,
                "phase": "Code Analysis",
                "status": "running",
                "results": results
            })

            print(f"  ✅ Code analysis complete")

        except Exception as e:
            print(f"  ⚠️  Code analysis failed: {e}")
            results["code_analysis"] = {"error": str(e)}

        # ================================================================
        # Stage 2: Deployment Detection (0.33 → 0.66)
        # ================================================================

        try:
            task.current_phase = "Deployment Detection"
            task.progress = 0.40
            db.commit()

            await manager.send_update(task_id, {
                "type": "progress",
                "progress": 0.40,
                "phase": "Deployment Detection",
                "status": "running"
            })

            print(f"  🚀 Running deployment detection for {project.name}...")

            # Build facts dict from project data
            facts = {
                "deps": project.deps or {},
                "has_ci": project.has_ci,
                "has_tests": project.has_tests,
                "has_readme": project.has_readme,
                "has_license": project.has_license,
            }

            deployment_results = detect_deployment(
                project_path=project.path,
                languages=project.languages or [],
                facts=facts
            )
            results["deployment_analysis"] = deployment_results

            task.progress = 0.66
            task.results = results
            db.commit()

            await manager.send_update(task_id, {
                "type": "progress",
                "progress": 0.66,
                "phase": "Deployment Detection",
                "status": "running",
                "results": results
            })

            print(f"  ✅ Deployment detection complete")

        except Exception as e:
            print(f"  ⚠️  Deployment detection failed: {e}")
            results["deployment_analysis"] = {"error": str(e)}

        # ================================================================
        # Stage 3: Documentation Analysis (0.66 → 0.75)
        # ================================================================

        try:
            task.current_phase = "Documentation Analysis"
            task.progress = 0.68
            db.commit()

            await manager.send_update(task_id, {
                "type": "progress",
                "progress": 0.68,
                "phase": "Documentation Analysis",
                "status": "running"
            })

            print(f"  📝 Running documentation analysis for {project.name}...")

            doc_results = analyze_documentation(
                project_path=project.path,
                languages=project.languages or [],
                facts=facts,
                entry_points=None  # Will auto-detect
            )
            results["documentation_analysis"] = doc_results

            task.progress = 0.75
            task.results = results
            db.commit()

            await manager.send_update(task_id, {
                "type": "progress",
                "progress": 0.75,
                "phase": "Documentation Analysis",
                "status": "running",
                "results": results
            })

            print(f"  ✅ Documentation analysis complete")

        except Exception as e:
            print(f"  ⚠️  Documentation analysis failed: {e}")
            results["documentation_analysis"] = {"error": str(e)}

        # ================================================================
        # Stage 4: LLM Analysis (0.75 → 1.0) - OPTIONAL
        # ================================================================

        if include_llm:
            try:
                task.current_phase = "LLM Analysis (Multi-Model Pipeline)"
                task.progress = 0.80
                db.commit()

                await manager.send_update(task_id, {
                    "type": "progress",
                    "progress": 0.80,
                    "phase": "LLM Analysis (Multi-Model Pipeline)",
                    "status": "running"
                })

                print(f"  🤖 Running LLM analysis for {project.name}...")

                # Prepare project data for LLM
                project_data = {
                    "name": project.name,
                    "path": project.path,
                    "languages": project.languages or [],
                    "stage": project.stage,
                    "code_analysis": results.get("code_analysis", {}),
                    "deployment_analysis": results.get("deployment_analysis", {}),
                    "documentation_analysis": results.get("documentation_analysis", {}),
                }

                # Run async LLM analysis
                llm_results = await analyze_with_llm(
                    project_data=project_data,
                    dry_run=False
                )
                results["llm_analysis"] = llm_results

                task.progress = 1.0
                task.results = results
                db.commit()

                await manager.send_update(task_id, {
                    "type": "progress",
                    "progress": 1.0,
                    "phase": "LLM Analysis (Multi-Model Pipeline)",
                    "status": "running",
                    "results": results
                })

                print(f"  ✅ LLM analysis complete")

            except Exception as e:
                print(f"  ⚠️  LLM analysis failed: {e}")
                results["llm_analysis"] = {"error": str(e)}
        else:
            # Skip LLM, go straight to complete
            task.progress = 1.0

        # ================================================================
        # Finalization
        # ================================================================

        task.status = "completed"
        task.progress = 1.0
        task.current_phase = "Complete"
        task.results = results
        task.completed_at = datetime.utcnow()
        db.commit()

        await manager.send_update(task_id, {
            "type": "complete",
            "progress": 1.0,
            "phase": "Complete",
            "status": "completed",
            "results": results
        })

        print(f"✅ Deep analysis complete for {project.name}")

    except Exception as e:
        # Handle catastrophic failure
        print(f"❌ Deep analysis failed: {e}")

        # Only update task if it was successfully loaded
        if task is not None:
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.utcnow()
            db.commit()

        await manager.send_update(task_id, {
            "type": "error",
            "status": "failed",
            "error": str(e)
        })

    finally:
        db.close()


# ============================================================================
# REST API Endpoints
# ============================================================================


@router.post("/projects/{project_id}/deep-analysis")
async def create_deep_analysis(
    project_id: str,
    background_tasks: BackgroundTasks,
    include_llm: bool = Query(True, description="Include LLM analysis (slower)"),
    force_refresh: bool = Query(False, description="Force new analysis even if recent one exists"),
    db: Session = Depends(get_db),
):
    """
    Queue a deep analysis task for a project.

    Returns immediately with task_id - use WebSocket or status endpoint to track progress.

    If a recent analysis exists (< 1 hour) and force_refresh=False, returns cached results.

    Args:
        project_id: Project UUID
        include_llm: Whether to run LLM analysis (default: True)
        force_refresh: Force new analysis even if recent one exists (default: False)

    Returns:
        {"task_id": "uuid", "status": "queued"} or cached results
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    # Check for recent analysis (< 1 hour)
    if not force_refresh:
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_task = (
            db.query(AnalysisTask)
            .filter(
                AnalysisTask.project_id == project_id,
                AnalysisTask.status == "completed",
                AnalysisTask.completed_at >= one_hour_ago
            )
            .order_by(AnalysisTask.completed_at.desc())
            .first()
        )

        if recent_task:
            print(f"♻️  Returning cached analysis for {project.name}")
            return {
                "task_id": recent_task.id,
                "status": "completed",
                "cached": True,
                "progress": 1.0,
                "results": recent_task.results,
                "completed_at": recent_task.completed_at.isoformat()
            }

    # Create new analysis task
    task_id = str(uuid.uuid4())
    task = AnalysisTask(
        id=task_id,
        project_id=project_id,
        status="queued",
        progress=0.0,
        current_phase="Queued",
        results={}
    )
    db.add(task)
    db.commit()

    print(f"📋 Queued deep analysis for {project.name} (task_id: {task_id[:8]})")

    # Get database path for background task
    # Use test database path if in test environment
    db_path = getattr(db.bind.engine.url, 'database', None)
    if db_path is None:
        db_path = str(Path(__file__).parent.parent / "borg.db")

    # Queue background task
    background_tasks.add_task(
        run_deep_analysis,
        task_id=task_id,
        project_id=project_id,
        include_llm=include_llm,
        db_path=str(db_path)
    )

    return {
        "task_id": task_id,
        "status": "queued",
        "cached": False
    }


@router.get("/analysis/{task_id}/status")
def get_analysis_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    Get current status of an analysis task.

    Polling alternative to WebSocket for simpler clients.

    Args:
        task_id: Analysis task UUID

    Returns:
        Task status including progress, phase, results, and errors
    """
    task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    return task.to_dict()


@router.websocket("/ws/analysis/{task_id}")
async def websocket_analysis_progress(
    websocket: WebSocket,
    task_id: str
):
    """
    WebSocket endpoint for real-time analysis progress updates.

    Message format:
    {
        "type": "progress" | "complete" | "error",
        "progress": 0.0-1.0,
        "phase": "Current phase name",
        "status": "queued" | "running" | "completed" | "failed",
        "results": {...},  // Partial or complete results
        "error": "..."     // Only if type="error"
    }

    Usage:
        const ws = new WebSocket('ws://localhost:8000/api/ws/analysis/' + taskId);
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Progress:', data.progress, data.phase);
        };

    Args:
        task_id: Analysis task UUID
    """
    await manager.connect(task_id, websocket)

    try:
        # Keep connection alive and wait for disconnection
        while True:
            # Receive any client messages (ping/pong, etc.)
            data = await websocket.receive_text()
            # Echo back for debugging (optional)
            # await websocket.send_text(f"Received: {data}")

    except WebSocketDisconnect:
        manager.disconnect(task_id, websocket)
        print(f"🔌 Client disconnected from task {task_id[:8]}")
