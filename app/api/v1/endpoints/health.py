"""
Health check endpoints for FlowPlayground API.
"""
import asyncio
import time
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
import aiohttp
import redis.asyncio as redis

from app.core.config import settings
from app.models.responses import HealthResponse
from app.services import fal_ai_service
from app.utils.file_handler import file_handler

router = APIRouter()

# Track application start time
app_start_time = time.time()


async def check_fal_ai_service() -> str:
    """Check fal.ai service connectivity."""
    try:
        # Simple connectivity check
        session = await fal_ai_service._get_session()
        timeout = aiohttp.ClientTimeout(total=5)
        
        async with session.get(
            f"{settings.fal_ai_base_url}/health",
            timeout=timeout
        ) as response:
            if response.status == 200:
                return "connected"
            else:
                return "degraded"
    except Exception:
        return "disconnected"


async def check_redis_service() -> str:
    """Check Redis service connectivity."""
    try:
        redis_client = redis.from_url(settings.redis_url)
        await redis_client.ping()
        await redis_client.close()
        return "connected"
    except Exception:
        return "disconnected"


async def check_storage_service() -> str:
    """Check storage service health."""
    try:
        stats = file_handler.get_storage_stats()
        # Check if we can get stats successfully
        if isinstance(stats, dict):
            return "healthy"
        else:
            return "degraded"
    except Exception:
        return "unhealthy"


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns the health status of the application and its dependencies.
    """
    try:
        # Calculate uptime
        uptime = time.time() - app_start_time
        
        # Check all services concurrently
        fal_ai_status, redis_status, storage_status = await asyncio.gather(
            check_fal_ai_service(),
            check_redis_service(),
            check_storage_service(),
            return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(fal_ai_status, Exception):
            fal_ai_status = "error"
        if isinstance(redis_status, Exception):
            redis_status = "error"
        if isinstance(storage_status, Exception):
            storage_status = "error"
        
        services = {
            "fal_ai": fal_ai_status,
            "redis": redis_status,
            "storage": storage_status,
        }
        
        # Determine overall health
        overall_status = "healthy"
        if any(status in ["disconnected", "unhealthy", "error"] for status in services.values()):
            overall_status = "unhealthy"
        elif any(status == "degraded" for status in services.values()):
            overall_status = "degraded"
        
        return HealthResponse(
            status=overall_status,
            version=settings.app_version,
            uptime=uptime,
            services=services,
            message=f"FlowPlayground is {overall_status}",
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check endpoint with more information.
    
    Provides detailed information about system health and metrics.
    """
    try:
        # Basic health info
        health_response = await health_check()
        
        # Additional detailed information
        storage_stats = file_handler.get_storage_stats()
        
        detailed_info = {
            **health_response.dict(),
            "environment": settings.environment,
            "debug_mode": settings.debug,
            "storage_stats": storage_stats,
            "configuration": {
                "max_file_size": settings.max_file_size,
                "allowed_image_types": settings.allowed_image_types,
                "allowed_video_types": settings.allowed_video_types,
                "rate_limit": f"{settings.rate_limit_requests}/{settings.rate_limit_period}s",
                "gradio_enabled": settings.gradio_enabled,
            },
            "system_info": {
                "upload_directory": settings.upload_path,
                "cors_origins": settings.cors_origins,
            }
        }
        
        return detailed_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Detailed health check failed: {str(e)}"
        )


@router.get("/health/readiness")
async def readiness_check():
    """
    Readiness check endpoint for Kubernetes.
    
    Returns 200 if the application is ready to serve requests.
    """
    try:
        # Check critical services
        fal_ai_status = await check_fal_ai_service()
        
        if fal_ai_status == "disconnected":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="fal.ai service is not available"
            )
        
        return {"ready": True, "message": "Application is ready"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Readiness check failed: {str(e)}"
        )


@router.get("/health/liveness")
async def liveness_check():
    """
    Liveness check endpoint for Kubernetes.
    
    Returns 200 if the application is alive and running.
    """
    try:
        # Simple check that the application is running
        return {
            "alive": True,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": time.time() - app_start_time
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Liveness check failed: {str(e)}"
        )