from pydantic import BaseModel,Field
from typing import Optional,List
from datetime import datetime

class QuestionRequest(BaseModel):
    """Request schema for asking questions"""
    question: str = Field(...,min_length=1, description="Question to ask")
    document_ids: Optional[List[str]] = Field(
        None, description="Specific document IDs to search (optional)"
    )
    top_k : Optional[int] = Field(
        None,
        ge=1,
        le=10,
        description= "Number of relavant chunks to retrieve"
    )
    
    
class SourceChunk(BaseModel):
    """Schema for source chunk"""
    document_id:str
    document_title:str
    chunk_index: Optional[int]
    content: str
    similarity_score: float
    
    
class AnswerResponse(BaseModel):
    """Response schema for answer"""
    id: str
    question: str
    answer: str
    sources: List[SourceChunk]
    confidence: Optional[str] = Field(
        None, description="Confidence level: high/medium/low"
    )
    sub_questions:Optional[List[str]] = None
    created_at: datetime
    
    
class ChatHistoryResponse(BaseModel):
    """Schema for chat history"""
    id: str
    question: str
    answer: str
    confidence: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes= True