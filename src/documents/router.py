from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil

from src.documents.schemas import DocumentResponse, DocumentStats,VectorStoreStats
from src.documents.service import document_service
from src.database import get_db
from src.vector_store.client import vector_store
from src.core.config import get_settings
from src.core.logging import log_request
from src.core.rate_limit import limiter
from src.core.security import verify_api_key


settings = get_settings()
router = APIRouter()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@router.post("/upload" , response_model=dict)
@limiter.limit("5/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    title:str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Upload and index a document"""
    log_request("/documents/upload", "POST", file = file.filename, title= title)
    
    # Security Settings
    allowed_extensions = ['.pdf','.docx','.txt']
    
    # 1. Check file extension
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}")
    
    # 2. check file size
    file.file.seek(0,2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400, detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE / (1024*1024):.1f}MB"
        )
        
    if file_size == 0:
        raise HTTPException(status_code=400, detail="File is empty")
        
    try:
        import uuid
        unique_id = str(uuid.uuid4())
        file_name = f"{unique_id}{file_extension}"
        file_path = os.path.join(settings.UPLOAD_DIR,file_name)
        
        with open(file_path, 'wb') as buffer:
            shutil.copyfileobj(file.file,buffer)
            
        document, stats = document_service.upload_pdf(
            file_path= file_path,
            title = title,
            description = description or "",
            db=db
        )
        
        return {
            "message": "Document uploaded and indexed successfully",
            "document" : DocumentResponse.model_validate(document),
            "stats" : DocumentStats(**stats)
        }
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
            
            
        raise HTTPException(
            status_code=500, detail = f"Failed to process document: {str(e)}"
        )
        

@router.get("/documents", response_model= List[DocumentResponse])
@limiter.limit("30/minute")
async def list_documents(
    request: Request,
    skip:int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all documents"""
    log_request("/documents" , "GET" , skip = skip , limit = limit)
    documents = document_service.list_documents(db, skip=skip, limit =limit)
    return documents


@router.get("/documents/{document_id}",response_model=DocumentResponse)
@limiter.limit("30/minute")
async def get_document(
    request : Request,
    document_id : str,
    db: Session = Depends(get_db)
):
    """Get document by ID"""
    log_request(f"/documents/{document_id}","GET")
    
    try:
        document = document_service.get_document(document_id, db)
        return document
    except Exception as e:
        raise HTTPException(status=400, detail=str(e))
    
    
@router.delete("/documents/{document_id}")
@limiter.limit("10/minute")
async def delete_document(
    request: Request,
    document_id: str,
    db: Session = Depends(get_db)
):
    """Delete a document"""
    log_request(f"/documents/{document_id}", "DELETE")
    
    try:
        document_service.delete_document(document_id,db)
        return {
            "message" : "Document deleted successfully",
            "document_id" : document_id
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/stats", response_model=VectorStoreStats)
async def get_vector_store_stats():
    """Get vector store statistics"""
    log_request("/documents/stats","GET")
    stats = vector_store.get_stats()
    return VectorStoreStats(**stats)