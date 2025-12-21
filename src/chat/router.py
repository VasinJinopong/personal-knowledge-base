from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List

from src.chat.schemas import QuestionRequest, AnswerResponse, ChatHistoryResponse, SourceChunk
from src.chat.service import chat_service
from src.database import get_db
from src.core.logging import log_request
from src.core.rate_limit import limiter


router = APIRouter()

@router.post("/ask",response_model=AnswerResponse)
@limiter.limit("10/minute")
async def ask_question(
    request: Request,
    question_data: QuestionRequest,
    use_multi_query:bool = True,
    db: Session = Depends(get_db),
):
    """Ask a question and get an answer based on documents"""
    log_request("/chat/ask", "POST", question= question_data.question[:50])
    
    try:
        service = chat_service
        
        # Choose RAG method
        if use_multi_query:
            result = chat_service.multi_query_rag(
                question=question_data.question,
                top_k_per_query=2
            )
            
            # Convert to AnswerResponse format
            sources = []
            for chunk in result.get('sources', []):
                source = SourceChunk(
                    document_id=chunk['metadata'].get('document_id',''),
                    document_title=chunk['metadata'].get('title','Unknown'),
                    chunk_index=chunk['metadata'].get('chunk_index',0),
                    content=chunk['content'][:300] + "..." if len(chunk['content']) > 300 else chunk['content'],
                    similarity_score=chunk.get('score',0.0)
                )
                
                sources.append(source)
                
            chat = service.save_chat(
                question = question_data.question,
                answer = result['answer'],
                confidence=result['confidence'],
                top_k = len(sources),
                document_ids=question_data.document_ids,
                db=db
            )
            
            return AnswerResponse(
                id=chat.id,
                question=question_data.question,
                answer=result['answer'],
                sources=sources,
                confidence=result['confidence'],
                sub_questions=result.get('sub_questions'),
                created_at=chat.created_at
            )
        else:
        
            result = chat_service.ask_question(
                question=question_data.question,
                document_ids=question_data.document_ids,
                top_k=question_data.top_k or 3,
                db=db
            )
            
            return result
    
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
        
        # Convert to response format
        
        return history
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get history: {str(e)}"
        )