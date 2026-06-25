from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.ai import run_chat, ChatRequest, ChatResponse
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not body.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty",
        )

    try:
        history_text = "\n".join(
            f"{'User' if h.role == 'user' else 'Assistant'}: {h.content}"
            for h in body.history
        )
        response_text = run_chat(db, current_user, history_text, body.message)
        return ChatResponse(response=response_text or "")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service unavailable: {e}",
        )
