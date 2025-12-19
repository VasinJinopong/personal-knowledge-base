from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

from src.core.config import get_settings
from src.core.logging import logger
from src.database import init_db
from src.documents.router import router as documents_router
from src.chat.router import router as chat_router

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from src.core.rate_limit import limiter

settings = get_settings()

# API Key Middleware
class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Skip health check endpoint
        if request.url.path in ["/","/health"]:
            return await call_next(request)
        
        # Check API Key
        api_key = request.headers.get("X-API-Key")
        
        if api_key != settings.API_KEY:
            return JSONResponse(
                status_code=403, content={"detail":"Invalid or missing API Key"}
            )
        
        response = await call_next(request)
        return response



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events"""
    # Startup
    logger.info("Starting Document Q&A API...")
    init_db()
    logger.info("Database initialized")
    logger.info(f"API running at: http://0.0.0.0:8000")
    logger.info(f"Docs at: http://0.0.0.0:8000/docs")
    
    yield
    
    # Shutdown (if needed)
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="RAG-powered Document Q&A API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add Rate Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add API Key Middleware
app.add_middleware(APIKeyMiddleware)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


class HealthCheck(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"


@app.get("/", response_model=HealthCheck)
async def root():
    """Root endpoint"""
    return HealthCheck()


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck()


app.include_router(
    documents_router,
    prefix=f"{settings.API_V1_STR}/documents",
    tags=["documents"]
)

app.include_router(
    chat_router,
    prefix=f"{settings.API_V1_STR}/chat",
    tags=["chat"]
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )