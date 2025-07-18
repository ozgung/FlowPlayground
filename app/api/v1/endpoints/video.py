"""
Video processing endpoints for FlowPlayground API.
"""
import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
import redis.asyncio as redis
import json

from app.core.config import settings
from app.core.security import get_api_key
from app.models import (
    VideoProcessRequest,
    VideoResponse,
    JobResponse,
    ErrorCode,
)
from app.services import fal_ai_service, FalAIError
from app.utils.file_handler import file_handler

router = APIRouter()

# Redis client for caching
redis_client = redis.from_url(settings.redis_url)


async def get_cached_result(cache_key: str) -> Dict[str, Any]:
    """Get cached result from Redis."""
    try:
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
    except Exception:
        pass
    return None


async def cache_result(cache_key: str, result: Dict[str, Any], expire_time: int = None):
    """Cache result in Redis."""
    try:
        expire_time = expire_time or settings.redis_expire_time
        await redis_client.setex(
            cache_key,
            expire_time,
            json.dumps(result, default=str)
        )
    except Exception:
        pass


def generate_cache_key(operation: str, params: Dict[str, Any], file_hash: str = None) -> str:
    """Generate cache key for operation."""
    key_parts = [operation]
    if file_hash:
        key_parts.append(file_hash)
    
    # Sort parameters for consistent keys
    sorted_params = sorted(params.items())
    param_str = "_".join(f"{k}:{v}" for k, v in sorted_params)
    key_parts.append(param_str)
    
    return "flowplayground:video:" + ":".join(key_parts)


@router.post("/process", response_model=VideoResponse)
async def process_video(
    request: VideoProcessRequest,
    file: UploadFile = File(...),
    api_key: str = Depends(get_api_key),
):
    """
    Process video using AI.
    
    Applies various video processing operations like enhancement, stabilization, etc.
    """
    try:
        # Validate and save uploaded file
        file_data = await file_handler.validate_and_save_upload(file)
        
        if not file_data["file_info"]["is_video"]:
            raise HTTPException(
                status_code=400,
                detail="Only video files are supported for video processing"
            )
        
        # Generate cache key
        cache_key = generate_cache_key(
            f"video_{request.operation}",
            request.dict(),
            file_data["file_info"]["file_hash"]
        )
        
        # Check cache first
        cached_result = await get_cached_result(cache_key)
        if cached_result:
            return VideoResponse(
                video_url=cached_result["video_url"],
                thumbnail_url=cached_result.get("thumbnail_url"),
                preview_url=cached_result.get("preview_url"),
                metadata=cached_result.get("metadata", {}),
                message="Video processed successfully (cached)",
                request_id=str(uuid.uuid4()),
            )
        
        # Get file content
        file_content = await file_handler.get_file_content(
            file_data["filename"],
            file_data["subdir"]
        )
        
        # Process with fal.ai
        result = await fal_ai_service.process_video(
            file_content,
            file_data["filename"],
            request
        )
        
        # Cache result
        await cache_result(cache_key, result)
        
        return VideoResponse(
            video_url=result["result_url"],
            thumbnail_url=None,  # TODO: Generate video thumbnail
            preview_url=None,    # TODO: Generate video preview
            metadata=result["metadata"],
            message="Video processed successfully",
            request_id=str(uuid.uuid4()),
        )
        
    except FalAIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Video processing failed: {str(e)}"
        )


@router.post("/enhance", response_model=VideoResponse)
async def enhance_video(
    file: UploadFile = File(...),
    quality: str = "high",
    api_key: str = Depends(get_api_key),
):
    """
    Enhance video quality.
    
    Improves video quality by reducing noise and enhancing details.
    """
    try:
        # Create request object
        request = VideoProcessRequest(
            operation="enhance",
            quality=quality
        )
        
        # Use the main process_video function
        return await process_video(request, file, api_key)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Video enhancement failed: {str(e)}"
        )


@router.post("/stabilize", response_model=VideoResponse)
async def stabilize_video(
    file: UploadFile = File(...),
    quality: str = "high",
    api_key: str = Depends(get_api_key),
):
    """
    Stabilize shaky video.
    
    Reduces camera shake and improves video stability.
    """
    try:
        # Create request object
        request = VideoProcessRequest(
            operation="stabilize",
            quality=quality
        )
        
        # Use the main process_video function
        return await process_video(request, file, api_key)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Video stabilization failed: {str(e)}"
        )


@router.get("/job/{job_id}", response_model=JobResponse)
async def get_video_job_status(
    job_id: str,
    api_key: str = Depends(get_api_key),
):
    """
    Get the status of a video processing job.
    
    Returns the current status and progress of a video processing job.
    """
    try:
        result = await fal_ai_service.get_job_status(job_id)
        
        return JobResponse(
            job_id=job_id,
            status=result["status"],
            progress=result.get("progress", 0.0),
            result_url=result.get("result_url"),
            metadata=result.get("metadata", {}),
            message=f"Video job {job_id} is {result['status']}",
            request_id=str(uuid.uuid4()),
        )
        
    except FalAIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get video job status: {str(e)}"
        )


@router.post("/style-transfer", response_model=VideoResponse)
async def video_style_transfer(
    file: UploadFile = File(...),
    style_reference: str = "artistic",
    quality: str = "high",
    api_key: str = Depends(get_api_key),
):
    """
    Apply style transfer to video.
    
    Transforms video using artistic styles while maintaining temporal consistency.
    """
    try:
        # Create request object
        request = VideoProcessRequest(
            operation="style_transfer",
            quality=quality
        )
        
        # Use the main process_video function
        return await process_video(request, file, api_key)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Video style transfer failed: {str(e)}"
        )


@router.get("/formats")
async def get_supported_formats(api_key: str = Depends(get_api_key)):
    """
    Get supported video formats and specifications.
    
    Returns information about supported video formats, codecs, and limitations.
    """
    try:
        return {
            "supported_formats": {
                "input": settings.allowed_video_types,
                "output": ["video/mp4", "video/avi", "video/mov"]
            },
            "specifications": {
                "max_file_size": settings.max_file_size,
                "max_duration": 300,  # 5 minutes
                "supported_resolutions": ["480p", "720p", "1080p", "4k"],
                "supported_fps": [24, 30, 60],
                "supported_codecs": ["h264", "h265", "vp9"]
            },
            "operations": {
                "enhance": {
                    "description": "Improve video quality and reduce noise",
                    "parameters": ["quality"]
                },
                "stabilize": {
                    "description": "Reduce camera shake and improve stability",
                    "parameters": ["quality"]
                },
                "style_transfer": {
                    "description": "Apply artistic styles to video",
                    "parameters": ["style_reference", "quality"]
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get supported formats: {str(e)}"
        )