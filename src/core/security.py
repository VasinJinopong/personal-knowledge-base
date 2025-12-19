from fastapi import Security, HTTPException, Request
from fastapi.security import APIKeyHeader
from src.core.config import get_settings


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


EXCLUDE_PATHS = ["/docs", "/redoc", "/openapi.json"]

def verify_api_key(request : Request,api_key: str = Security(api_key_header)):
    
    if request.url.path in EXCLUDE_PATHS:
        return
    
    if api_key != get_settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
    return api_key