"""
Borg Scanner Dashboard - FastAPI Backend

Usage:
    uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models.database import engine, Base
from api import projects, chat, analysis, notes

# Create FastAPI app
app = FastAPI(
    title="Borg Scanner Dashboard API",
    description="Backend API for Borg Tools Scanner Dashboard with AI Chat Agent",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",  # Vite default port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(projects.router, prefix="/api", tags=["projects"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])
app.include_router(notes.router, prefix="/api", tags=["notes"])


@app.on_event("startup")
def startup_event():
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": "Borg Scanner Dashboard API",
        "version": "1.0.0",
        "endpoints": {
            "projects": "/api/projects",
            "project_detail": "/api/projects/{id}",
            "stats": "/api/stats",
            "chat": "/api/chat",
            "chat_history": "/api/chat/{session_id}/history",
            "deep_analysis": "/api/projects/{id}/deep-analysis",
            "analysis_status": "/api/analysis/{task_id}/status",
            "analysis_ws": "/ws/analysis/{task_id}",
            "project_notes": "/api/projects/{project_id}/notes",
            "note_detail": "/api/notes/{note_id}",
            "quick_note": "/api/projects/{project_id}/notes/quick",
        },
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
