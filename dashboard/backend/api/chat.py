"""Chat API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.database import get_db
from models.chat import ChatMessage
from models.schemas import ChatRequest, ChatResponse, ChatMessageSchema
from services.chat_agent import ChatAgent
from config import settings

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def send_chat_message(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    """Send a chat message and get AI response."""

    # Validate project_id if provided
    if request.project_id:
        from models.project import Project

        project = db.query(Project).filter(Project.id == request.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    # Create chat agent
    agent = ChatAgent(api_key=settings.OPENROUTER_API_KEY)

    try:
        # Send message and get response
        response_text, message_id = agent.send_message(
            message=request.message,
            session_id=request.session_id,
            project_id=request.project_id,
            db=db,
        )

        return ChatResponse(
            response=response_text,
            session_id=request.session_id,
            message_id=message_id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat message: {str(e)}",
        )


@router.get("/chat/{session_id}/history", response_model=list[ChatMessageSchema])
def get_chat_history(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Get chat history for a session."""

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return [
        ChatMessageSchema(
            id=msg.id,
            session_id=msg.session_id,
            role=msg.role,
            content=msg.content,
            project_id=msg.project_id,
            created_at=msg.created_at,
        )
        for msg in messages
    ]


@router.delete("/chat/{session_id}")
def clear_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Clear all messages in a chat session."""

    deleted_count = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .delete()
    )

    db.commit()

    return {"deleted": deleted_count, "session_id": session_id}
