from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List

from src.chat.schemas import QuestionRequest, AnswerResponse, ChatHistoryResponse
from src.chat.service import chat_service
from src.database import get_db
from src.core.logging import log_request
from src.core.rate_limit import limiter
from src.core.security import verify_api_key

router = APIRouter()

@router.post("/ask",response_model=AnswerResponse)
@limiter.limit("10/minute")
async def ask_question(
    request: Request,
    question_data: QuestionRequest,
    db: Session = Depends(get_db),
):
    """Ask a question and get an answer based on documents"""
    log_request("/chat/ask", "POST", question= question_data.question[:50])
    
    try:
        answer = chat_service.ask_question(
            question=question_data.question,
            document_ids=question_data.document_ids,
            top_k=question_data.top_k or 3,
            db=db
        )
        
        return answer
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to answer question: {str(e)}"
        )
        
        
@router.get("/ask/simple")
@limiter.limit("10/minute")
async def ask_question_simple(
    question: str,
    request : Request,
    db: Session = Depends(get_db),
):
    """Simple endpoint: just ask a question"""
    log_request("/chat/ask/simple","GET", question = question[:50])
    
    try:
        answer = chat_service.ask_question(
            question=question,
            document_ids=None,
            top_k=3,
            db=db
        )
        
        return {
            "question" :question,
            "answer" : answer.answer,
            "confidence" : answer.confidence,
            "sources_count": len(answer.sources)    
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,detail=f"Failed to answer question: {str(e)}"
        )
        
        
        
@router.get("/history", response_model=List[ChatHistoryResponse])
@limiter.limit("10/minute")
async def get_chat_history(
    request : Request,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Get recent chat history"""
    log_request("/chat/history", "GET", limit=limit)
    
    if limit > 100:
        limit = 100
        
    try:
        history = chat_service.get_chat_history(db, limit=limit)
        return history
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get history: {str(e)}"
        )