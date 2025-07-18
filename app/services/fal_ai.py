"""
fal.ai API integration service.
"""
import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import json

from app.core.config import settings
from app.models import (
    ImageEnhanceRequest,
    StyleTransferRequest,
    ImageGenerateRequest,
    VideoProcessRequest,
    JobStatus,
    ErrorCode,
)

logger = logging.getLogger(__name__)


class FalAIError(Exception):
    """Custom exception for fal.ai API errors."""
    
    def __init__(self, message: str, status_code: int = 500, error_code: str = "external_api_error"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class FalAIService:
    """Service for interacting with fal.ai API."""
    
    def __init__(self):
        self.base_url = settings.fal_ai_base_url
        self.api_key = settings.fal_ai_api_key
        self.timeout = settings.fal_ai_timeout
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            headers = {
                "Authorization": f"Key {self.api_key}",
                "Content-Type": "application/json",
            }
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers,
                connector=aiohttp.TCPConnector(limit=100, limit_per_host=30)
            )
        return self.session
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to fal.ai API."""
        session = await self._get_session()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            if files:
                # For file uploads, we need to use FormData
                form_data = aiohttp.FormData()
                for key, value in (data or {}).items():
                    form_data.add_field(key, json.dumps(value) if isinstance(value, dict) else str(value))
                for key, file_info in files.items():
                    form_data.add_field(key, file_info['content'], filename=file_info['filename'])
                
                # Remove Content-Type header for multipart
                headers = dict(session.headers)
                headers.pop('Content-Type', None)
                
                async with session.request(method, url, data=form_data, headers=headers) as response:
                    response_data = await response.json()
            else:
                async with session.request(method, url, json=data) as response:
                    response_data = await response.json()
            
            if response.status >= 400:
                error_msg = response_data.get('message', f'HTTP {response.status}')
                raise FalAIError(
                    message=error_msg,
                    status_code=response.status,
                    error_code=self._map_error_code(response.status)
                )
            
            return response_data
            
        except aiohttp.ClientError as e:
            logger.error(f"fal.ai API request failed: {e}")
            raise FalAIError(
                message=f"Connection error: {str(e)}",
                status_code=503,
                error_code="external_api_error"
            )
        except asyncio.TimeoutError:
            logger.error("fal.ai API request timed out")
            raise FalAIError(
                message="Request timed out",
                status_code=504,
                error_code="external_api_error"
            )
    
    def _map_error_code(self, status_code: int) -> str:
        """Map HTTP status codes to error codes."""
        if status_code == 400:
            return ErrorCode.VALIDATION_ERROR
        elif status_code == 401:
            return ErrorCode.AUTHENTICATION_ERROR
        elif status_code == 429:
            return ErrorCode.RATE_LIMIT_EXCEEDED
        elif status_code == 413:
            return ErrorCode.FILE_TOO_LARGE
        else:
            return ErrorCode.EXTERNAL_API_ERROR
    
    async def enhance_image(
        self, 
        image_data: bytes, 
        filename: str, 
        request: ImageEnhanceRequest
    ) -> Dict[str, Any]:
        """Enhance image using fal.ai."""
        try:
            job_id = str(uuid.uuid4())
            
            # Prepare request data
            data = {
                "strength": request.strength,
                "preserve_details": request.preserve_details,
                "enhance_colors": request.enhance_colors,
                "reduce_noise": request.reduce_noise,
            }
            
            files = {
                "image": {
                    "content": image_data,
                    "filename": filename
                }
            }
            
            # Make request to fal.ai
            response = await self._make_request(
                "POST",
                "/workflows/enhance-image",
                data=data,
                files=files
            )
            
            return {
                "job_id": job_id,
                "status": JobStatus.COMPLETED,
                "result_url": response.get("image_url"),
                "metadata": {
                    "model_used": "image-enhancement",
                    "processing_time": response.get("processing_time", 0),
                    "original_size": len(image_data),
                }
            }
            
        except FalAIError:
            raise
        except Exception as e:
            logger.error(f"Image enhancement failed: {e}")
            raise FalAIError(
                message="Image enhancement failed",
                status_code=500,
                error_code="processing_error"
            )
    
    async def style_transfer(
        self, 
        image_data: bytes, 
        filename: str, 
        request: StyleTransferRequest
    ) -> Dict[str, Any]:
        """Apply style transfer using fal.ai."""
        try:
            job_id = str(uuid.uuid4())
            
            data = {
                "style_strength": request.style_strength,
                "preserve_structure": request.preserve_structure,
                "style_reference": request.style_reference,
            }
            
            files = {
                "image": {
                    "content": image_data,
                    "filename": filename
                }
            }
            
            response = await self._make_request(
                "POST",
                "/workflows/style-transfer",
                data=data,
                files=files
            )
            
            return {
                "job_id": job_id,
                "status": JobStatus.COMPLETED,
                "result_url": response.get("image_url"),
                "metadata": {
                    "model_used": "style-transfer",
                    "processing_time": response.get("processing_time", 0),
                    "style_reference": request.style_reference,
                }
            }
            
        except FalAIError:
            raise
        except Exception as e:
            logger.error(f"Style transfer failed: {e}")
            raise FalAIError(
                message="Style transfer failed",
                status_code=500,
                error_code="processing_error"
            )
    
    async def generate_image(self, request: ImageGenerateRequest) -> Dict[str, Any]:
        """Generate image using fal.ai."""
        try:
            job_id = str(uuid.uuid4())
            
            data = {
                "prompt": request.prompt,
                "negative_prompt": request.negative_prompt,
                "width": request.width,
                "height": request.height,
                "num_inference_steps": request.num_inference_steps,
                "guidance_scale": request.guidance_scale,
                "seed": request.seed,
            }
            
            response = await self._make_request(
                "POST",
                "/workflows/stable-diffusion-xl",
                data=data
            )
            
            return {
                "job_id": job_id,
                "status": JobStatus.COMPLETED,
                "result_url": response.get("image_url"),
                "metadata": {
                    "model_used": "stable-diffusion-xl",
                    "processing_time": response.get("processing_time", 0),
                    "prompt": request.prompt,
                    "seed": response.get("seed", request.seed),
                    "dimensions": f"{request.width}x{request.height}",
                }
            }
            
        except FalAIError:
            raise
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise FalAIError(
                message="Image generation failed",
                status_code=500,
                error_code="processing_error"
            )
    
    async def process_video(
        self, 
        video_data: bytes, 
        filename: str, 
        request: VideoProcessRequest
    ) -> Dict[str, Any]:
        """Process video using fal.ai."""
        try:
            job_id = str(uuid.uuid4())
            
            data = {
                "operation": request.operation,
                "quality": request.quality,
                "fps": request.fps,
                "resolution": request.resolution,
            }
            
            files = {
                "video": {
                    "content": video_data,
                    "filename": filename
                }
            }
            
            response = await self._make_request(
                "POST",
                "/workflows/video-process",
                data=data,
                files=files
            )
            
            return {
                "job_id": job_id,
                "status": JobStatus.COMPLETED,
                "result_url": response.get("video_url"),
                "metadata": {
                    "model_used": f"video-{request.operation}",
                    "processing_time": response.get("processing_time", 0),
                    "original_size": len(video_data),
                    "quality": request.quality,
                    "fps": request.fps,
                }
            }
            
        except FalAIError:
            raise
        except Exception as e:
            logger.error(f"Video processing failed: {e}")
            raise FalAIError(
                message="Video processing failed",
                status_code=500,
                error_code="processing_error"
            )
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status from fal.ai."""
        try:
            response = await self._make_request(
                "GET",
                f"/jobs/{job_id}"
            )
            
            return {
                "job_id": job_id,
                "status": self._map_job_status(response.get("status")),
                "progress": response.get("progress", 0.0),
                "result_url": response.get("result_url"),
                "metadata": response.get("metadata", {}),
            }
            
        except FalAIError:
            raise
        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            raise FalAIError(
                message="Failed to get job status",
                status_code=500,
                error_code="processing_error"
            )
    
    def _map_job_status(self, fal_status: str) -> JobStatus:
        """Map fal.ai job status to our JobStatus enum."""
        status_map = {
            "queued": JobStatus.PENDING,
            "running": JobStatus.PROCESSING,
            "completed": JobStatus.COMPLETED,
            "failed": JobStatus.FAILED,
            "cancelled": JobStatus.CANCELLED,
        }
        return status_map.get(fal_status, JobStatus.PENDING)
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models from fal.ai."""
        try:
            response = await self._make_request("GET", "/models")
            return response.get("models", [])
            
        except FalAIError:
            raise
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            raise FalAIError(
                message="Failed to list models",
                status_code=500,
                error_code="processing_error"
            )


# Global service instance
fal_ai_service = FalAIService()