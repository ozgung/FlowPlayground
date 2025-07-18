"""
API v1 router configuration.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import get_api_key
from app.models import CapabilitiesResponse
from app.core.config import settings

from .endpoints import health, image, video

# Create API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(image.router, prefix="/image", tags=["image"])
api_router.include_router(video.router, prefix="/video", tags=["video"])


@api_router.get("/capabilities", response_model=CapabilitiesResponse)
async def get_capabilities(api_key: str = Depends(get_api_key)):
    """
    Get API capabilities and available operations.
    
    Returns information about available AI operations, models, and limitations.
    """
    try:
        capabilities = {
            "image": [
                "enhance",
                "style_transfer", 
                "generate",
                "upscale",
                "background_removal"
            ],
            "video": [
                "enhance",
                "stabilize",
                "style_transfer"
            ]
        }
        
        models = {
            "stable-diffusion-xl": {
                "description": "High-quality image generation from text prompts",
                "type": "image_generation",
                "max_resolution": "1024x1024",
                "supported_operations": ["generate"]
            },
            "image-enhancement": {
                "description": "AI-powered image quality improvement",
                "type": "image_enhancement",
                "max_resolution": "4096x4096",
                "supported_operations": ["enhance"]
            },
            "style-transfer": {
                "description": "Artistic style transfer for images and videos",
                "type": "style_transfer",
                "max_resolution": "2048x2048",
                "supported_operations": ["style_transfer"]
            },
            "video-enhancement": {
                "description": "Video quality improvement and stabilization",
                "type": "video_processing",
                "max_resolution": "1920x1080",
                "supported_operations": ["enhance", "stabilize"]
            }
        }
        
        limits = {
            "max_file_size": settings.max_file_size,
            "max_image_resolution": "4096x4096",
            "max_video_resolution": "1920x1080",
            "max_video_duration": 300,  # 5 minutes
            "rate_limit": {
                "requests_per_hour": settings.rate_limit_requests,
                "concurrent_jobs": 5
            },
            "supported_formats": {
                "image": settings.allowed_image_types,
                "video": settings.allowed_video_types
            }
        }
        
        return CapabilitiesResponse(
            capabilities=capabilities,
            models=models,
            limits=limits,
            message="FlowPlayground API capabilities",
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get capabilities: {str(e)}"
        )


@api_router.get("/")
async def api_info():
    """
    Get API information.
    
    Returns basic information about the FlowPlayground API.
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "AI-powered photo and video processing API",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "health_url": "/api/v1/health",
        "capabilities_url": "/api/v1/capabilities",
        "environment": settings.environment,
        "endpoints": {
            "image": {
                "enhance": "/api/v1/image/enhance",
                "style_transfer": "/api/v1/image/style-transfer",
                "generate": "/api/v1/image/generate",
                "batch": "/api/v1/image/batch"
            },
            "video": {
                "process": "/api/v1/video/process",
                "enhance": "/api/v1/video/enhance",
                "stabilize": "/api/v1/video/stabilize",
                "style_transfer": "/api/v1/video/style-transfer"
            },
            "health": {
                "basic": "/api/v1/health",
                "detailed": "/api/v1/health/detailed",
                "readiness": "/api/v1/health/readiness",
                "liveness": "/api/v1/health/liveness"
            }
        }
    }