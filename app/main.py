"""
FastAPI main application for FlowPlayground.
"""
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
import uvicorn
import os
import time

from app.core.config import settings
from app.api.v1 import api_router
from app.services import fal_ai_service
from app.models.responses import ErrorResponse, ErrorCode

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format=settings.log_format,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("flowplayground.log") if not settings.is_development else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting FlowPlayground API...")
    
    # Ensure upload directory exists
    os.makedirs(settings.upload_path, exist_ok=True)
    
    # Initialize services
    try:
        # Test fal.ai connection
        await fal_ai_service._get_session()
        logger.info("fal.ai service initialized successfully")
    except Exception as e:
        logger.warning(f"fal.ai service initialization failed: {e}")
    
    # Background tasks
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    logger.info("FlowPlayground API startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FlowPlayground API...")
    
    # Cancel background tasks
    cleanup_task.cancel()
    
    # Close services
    try:
        await fal_ai_service.close()
    except Exception as e:
        logger.error(f"Error closing fal.ai service: {e}")
    
    logger.info("FlowPlayground API shutdown complete")


async def periodic_cleanup():
    """Periodic cleanup task for temporary files."""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            from app.utils.file_handler import file_handler
            deleted_count = await file_handler.cleanup_temp_files(24)  # Delete files older than 24 hours
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} temporary files")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="AI-powered photo and video processing API for iOS applications",
    version=settings.app_version,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
    openapi_url="/openapi.json" if not settings.is_production else None,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests."""
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# Rate limiting middleware (simple implementation)
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Simple rate limiting middleware."""
    # This is a basic implementation - in production, use Redis or similar
    # For now, we'll skip rate limiting and let it be handled by reverse proxy
    return await call_next(request)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error_code=ErrorCode.VALIDATION_ERROR,
            message="Validation error",
            details={"errors": exc.errors()},
            request_id=getattr(request.state, "request_id", None)
        ).dict()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    error_code = ErrorCode.INTERNAL_ERROR
    
    if exc.status_code == 400:
        error_code = ErrorCode.VALIDATION_ERROR
    elif exc.status_code == 401:
        error_code = ErrorCode.AUTHENTICATION_ERROR
    elif exc.status_code == 413:
        error_code = ErrorCode.FILE_TOO_LARGE
    elif exc.status_code == 415:
        error_code = ErrorCode.UNSUPPORTED_FORMAT
    elif exc.status_code == 429:
        error_code = ErrorCode.RATE_LIMIT_EXCEEDED
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=error_code,
            message=exc.detail,
            request_id=getattr(request.state, "request_id", None)
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Internal server error" if settings.is_production else str(exc),
            request_id=getattr(request.state, "request_id", None)
        ).dict()
    )


# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Serve static files (upload directory)
if os.path.exists(settings.upload_path):
    app.mount("/files", StaticFiles(directory=settings.upload_path), name="files")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "AI-powered photo and video processing API",
        "status": "online",
        "environment": settings.environment,
        "docs_url": "/docs" if not settings.is_production else None,
        "api_v1": "/api/v1",
        "health_check": "/api/v1/health"
    }


# Health check endpoint at root level
@app.get("/health")
async def health():
    """Simple health check endpoint."""
    return {"status": "healthy", "timestamp": time.time()}


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
        workers=1 if settings.reload else 4,
        access_log=not settings.is_production,
    )