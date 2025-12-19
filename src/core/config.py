from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    
    # App
    PROJECT_NAME: str = "Document Q&A API"
    API_V1_STR:str = "/api/v1"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_EMBEDDING_MODEL:str = "text-embedding-3-small"
    OPENAI_CHAT_MODEL: str = "gpt-3.5-turbo"
    
    # Vector Store
    CHROMA_PERSIST_DIR:str = "./chroma_db"
    CHROMA_COLLECTION_NAME:str = "documents"
    
    # RAG Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RESULTS: int =3
    
    # File Upload
    UPLOAD_DIR:str= "./uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024 #10MB
    
    # Usage
    API_KEY: str 
    
    class Config:
        env_file = ".env"
        case_sensitive=True
        
        
@lru_cache()
def get_settings() -> Settings:
    return Settings()