"""
Image processing endpoints for FlowPlayground API.
"""
import uuid
import asyncio
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import StreamingResponse
import redis.asyncio as redis
import json

from app.core.config import settings
from app.core.security import get_api_key
from app.models import (
    ImageEnhanceRequest,
    StyleTransferRequest,
    ImageGenerateRequest,
    BatchProcessRequest,
    ImageResponse,
    JobResponse,
    BatchResponse,
    ErrorResponse,
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
    
    return "flowplayground:" + ":".join(key_parts)


@router.post("/enhance", response_model=ImageResponse)
async def enhance_image(
    request: ImageEnhanceRequest,
    file: UploadFile = File(...),
    api_key: str = Depends(get_api_key),
):
    """
    Enhance image quality using AI.
    
    Improves image quality by reducing noise, enhancing colors, and preserving details.
    """
    try:
        # Validate and save uploaded file
        file_data = await file_handler.validate_and_save_upload(file)
        
        if not file_data["file_info"]["is_image"]:
            raise HTTPException(
                status_code=400,
                detail="Only image files are supported for enhancement"
            )
        
        # Generate cache key
        cache_key = generate_cache_key(
            "enhance",
            request.dict(),
            file_data["file_info"]["file_hash"]
        )
        
        # Check cache first
        cached_result = await get_cached_result(cache_key)
        if cached_result:
            return ImageResponse(
                image_url=cached_result["image_url"],
                thumbnail_url=cached_result.get("thumbnail_url"),
                metadata=cached_result.get("metadata", {}),
                message="Image enhanced successfully (cached)",
                request_id=str(uuid.uuid4()),
            )
        
        # Get file content
        file_content = await file_handler.get_file_content(
            file_data["filename"],
            file_data["subdir"]
        )
        
        # Process with fal.ai
        result = await fal_ai_service.enhance_image(
            file_content,
            file_data["filename"],
            request
        )
        
        # Cache result
        await cache_result(cache_key, result)
        
        return ImageResponse(
            image_url=result["result_url"],
            thumbnail_url=file_data["thumbnail_url"],
            metadata=result["metadata"],
            message="Image enhanced successfully",
            request_id=str(uuid.uuid4()),
        )
        
    except FalAIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Image enhancement failed: {str(e)}"
        )


@router.post("/style-transfer", response_model=ImageResponse)
async def style_transfer(
    request: StyleTransferRequest,
    file: UploadFile = File(...),
    api_key: str = Depends(get_api_key),
):
    """
    Apply style transfer to an image.
    
    Transforms the image using artistic styles while preserving the original structure.
    """
    try:
        # Validate and save uploaded file
        file_data = await file_handler.validate_and_save_upload(file)
        
        if not file_data["file_info"]["is_image"]:
            raise HTTPException(
                status_code=400,
                detail="Only image files are supported for style transfer"
            )
        
        # Generate cache key
        cache_key = generate_cache_key(
            "style_transfer",
            request.dict(),
            file_data["file_info"]["file_hash"]
        )
        
        # Check cache first
        cached_result = await get_cached_result(cache_key)
        if cached_result:
            return ImageResponse(
                image_url=cached_result["image_url"],
                thumbnail_url=cached_result.get("thumbnail_url"),
                metadata=cached_result.get("metadata", {}),
                message="Style transfer applied successfully (cached)",
                request_id=str(uuid.uuid4()),
            )
        
        # Get file content
        file_content = await file_handler.get_file_content(
            file_data["filename"],
            file_data["subdir"]
        )
        
        # Process with fal.ai
        result = await fal_ai_service.style_transfer(
            file_content,
            file_data["filename"],
            request
        )
        
        # Cache result
        await cache_result(cache_key, result)
        
        return ImageResponse(
            image_url=result["result_url"],
            thumbnail_url=file_data["thumbnail_url"],
            metadata=result["metadata"],
            message="Style transfer applied successfully",
            request_id=str(uuid.uuid4()),
        )
        
    except FalAIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Style transfer failed: {str(e)}"
        )


@router.post("/generate", response_model=ImageResponse)
async def generate_image(
    request: ImageGenerateRequest,
    api_key: str = Depends(get_api_key),
):
    """
    Generate images from text prompts.
    
    Creates new images based on text descriptions using AI models.
    """
    try:
        # Generate cache key
        cache_key = generate_cache_key("generate", request.dict())
        
        # Check cache first
        cached_result = await get_cached_result(cache_key)
        if cached_result:
            return ImageResponse(
                image_url=cached_result["image_url"],
                thumbnail_url=cached_result.get("thumbnail_url"),
                metadata=cached_result.get("metadata", {}),
                message="Image generated successfully (cached)",
                request_id=str(uuid.uuid4()),
            )
        
        # Process with fal.ai
        result = await fal_ai_service.generate_image(request)
        
        # Cache result
        await cache_result(cache_key, result)
        
        return ImageResponse(
            image_url=result["result_url"],
            thumbnail_url=None,  # No thumbnail for generated images initially
            metadata=result["metadata"],
            message="Image generated successfully",
            request_id=str(uuid.uuid4()),
        )
        
    except FalAIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Image generation failed: {str(e)}"
        )


@router.post("/batch", response_model=BatchResponse)
async def batch_process(
    request: BatchProcessRequest,
    files: List[UploadFile] = File(...),
    api_key: str = Depends(get_api_key),
):
    """
    Process multiple images in batch.
    
    Applies the same operation to multiple images efficiently.
    """
    try:
        if len(files) > 10:
            raise HTTPException(
                status_code=400,
                detail="Maximum 10 files allowed per batch"
            )
        
        batch_id = str(uuid.uuid4())
        results = []
        
        # Process files concurrently
        tasks = []
        for file in files:
            task = asyncio.create_task(
                process_single_file(file, request, batch_id)
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        file_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        completed_items = 0
        failed_items = 0
        
        for i, result in enumerate(file_results):
            if isinstance(result, Exception):
                results.append({
                    "file": files[i].filename,
                    "status": "failed",
                    "error": str(result)
                })
                failed_items += 1
            else:
                results.append(result)
                if result["status"] == "completed":
                    completed_items += 1
                else:
                    failed_items += 1
        
        return BatchResponse(
            batch_id=batch_id,
            total_items=len(files),
            completed_items=completed_items,
            failed_items=failed_items,
            results=results,
            message=f"Batch processing completed: {completed_items} successful, {failed_items} failed",
            request_id=str(uuid.uuid4()),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch processing failed: {str(e)}"
        )


async def process_single_file(
    file: UploadFile,
    request: BatchProcessRequest,
    batch_id: str
) -> Dict[str, Any]:
    """Process a single file in batch operation."""
    try:
        # Validate and save file
        file_data = await file_handler.validate_and_save_upload(file)
        
        if not file_data["file_info"]["is_image"]:
            return {
                "file": file.filename,
                "status": "failed",
                "error": "Only image files are supported"
            }
        
        # Get file content
        file_content = await file_handler.get_file_content(
            file_data["filename"],
            file_data["subdir"]
        )
        
        # Process based on operation
        if request.operation == "enhance":
            enhance_request = ImageEnhanceRequest(**request.parameters)
            result = await fal_ai_service.enhance_image(
                file_content,
                file_data["filename"],
                enhance_request
            )
        elif request.operation == "style_transfer":
            style_request = StyleTransferRequest(**request.parameters)
            result = await fal_ai_service.style_transfer(
                file_content,
                file_data["filename"],
                style_request
            )
        else:
            return {
                "file": file.filename,
                "status": "failed",
                "error": f"Unsupported operation: {request.operation}"
            }
        
        return {
            "file": file.filename,
            "status": "completed",
            "result_url": result["result_url"],
            "metadata": result["metadata"]
        }
        
    except Exception as e:
        return {
            "file": file.filename,
            "status": "failed",
            "error": str(e)
        }


@router.get("/job/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: str,
    api_key: str = Depends(get_api_key),
):
    """
    Get the status of an image processing job.
    
    Returns the current status and progress of a processing job.
    """
    try:
        result = await fal_ai_service.get_job_status(job_id)
        
        return JobResponse(
            job_id=job_id,
            status=result["status"],
            progress=result.get("progress", 0.0),
            result_url=result.get("result_url"),
            metadata=result.get("metadata", {}),
            message=f"Job {job_id} is {result['status']}",
            request_id=str(uuid.uuid4()),
        )
        
    except FalAIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job status: {str(e)}"
        )