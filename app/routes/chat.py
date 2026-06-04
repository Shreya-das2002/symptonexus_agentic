from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import SymptomChatRequest, SymptomChatResponse
from app.services.symptom_agent import SymptomAgent


router = APIRouter(prefix="/api/chat", tags=["Symptom Chatbot"])


@router.post("/symptom-check", response_model=SymptomChatResponse)
def symptom_check(payload: SymptomChatRequest, db: Session = Depends(get_db)):
    try:
        agent = SymptomAgent(db)
        result = agent.chat(
            user_message=payload.message,
            conversation=[item.model_dump() for item in payload.conversation],
        )
        return SymptomChatResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
