from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader
from src.core.config import get_settings


api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != get_settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
    return api_key