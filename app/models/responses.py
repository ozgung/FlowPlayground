"""
Response models for FlowPlayground API.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """Job processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ErrorCode(str, Enum):
    """Error codes for API responses."""
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    FILE_TOO_LARGE = "file_too_large"
    UNSUPPORTED_FORMAT = "unsupported_format"
    PROCESSING_ERROR = "processing_error"
    EXTERNAL_API_ERROR = "external_api_error"
    INTERNAL_ERROR = "internal_error"


class APIResponse(BaseModel):
    """Base API response model."""
    
    success: bool = Field(...)
    message: Optional[str] = Field(default=None)
    request_id: Optional[str] = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(APIResponse):
    """Error response model."""
    
    success: bool = Field(default=False)
    error_code: ErrorCode = Field(...)
    details: Optional[Dict[str, Any]] = Field(default=None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "Invalid file format",
                "error_code": "unsupported_format",
                "details": {
                    "supported_formats": ["jpg", "png", "webp"]
                },
                "request_id": "req_123456",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }


class HealthResponse(APIResponse):
    """Health check response model."""
    
    success: bool = Field(default=True)
    status: str = Field(default="healthy")
    version: str = Field(...)
    uptime: float = Field(...)
    services: Dict[str, str] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "status": "healthy",
                "version": "1.0.0",
                "uptime": 3600.0,
                "services": {
                    "fal_ai": "connected",
                    "redis": "connected"
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }


class JobResponse(APIResponse):
    """Job processing response model."""
    
    success: bool = Field(default=True)
    job_id: str = Field(...)
    status: JobStatus = Field(...)
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    result_url: Optional[str] = Field(default=None)
    metadata: Optional[Dict[str, Any]] = Field(default=None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "job_id": "job_123456",
                "status": "completed",
                "progress": 1.0,
                "result_url": "https://api.example.com/results/job_123456",
                "metadata": {
                    "processing_time": 12.5,
                    "model_used": "stable-diffusion-xl"
                },
                "request_id": "req_123456",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }


class ImageResponse(APIResponse):
    """Image processing response model."""
    
    success: bool = Field(default=True)
    image_url: str = Field(...)
    thumbnail_url: Optional[str] = Field(default=None)
    metadata: Optional[Dict[str, Any]] = Field(default=None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "image_url": "https://api.example.com/images/processed_123456.jpg",
                "thumbnail_url": "https://api.example.com/images/thumb_123456.jpg",
                "metadata": {
                    "width": 1024,
                    "height": 1024,
                    "format": "jpeg",
                    "file_size": 512000
                },
                "request_id": "req_123456",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }


class VideoResponse(APIResponse):
    """Video processing response model."""
    
    success: bool = Field(default=True)
    video_url: str = Field(...)
    thumbnail_url: Optional[str] = Field(default=None)
    preview_url: Optional[str] = Field(default=None)
    metadata: Optional[Dict[str, Any]] = Field(default=None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "video_url": "https://api.example.com/videos/processed_123456.mp4",
                "thumbnail_url": "https://api.example.com/videos/thumb_123456.jpg",
                "preview_url": "https://api.example.com/videos/preview_123456.gif",
                "metadata": {
                    "duration": 30.5,
                    "width": 1920,
                    "height": 1080,
                    "fps": 30,
                    "file_size": 15728640
                },
                "request_id": "req_123456",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }


class BatchResponse(APIResponse):
    """Batch processing response model."""
    
    success: bool = Field(default=True)
    batch_id: str = Field(...)
    total_items: int = Field(...)
    completed_items: int = Field(default=0)
    failed_items: int = Field(default=0)
    results: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "batch_id": "batch_123456",
                "total_items": 5,
                "completed_items": 5,
                "failed_items": 0,
                "results": [
                    {
                        "file": "image1.jpg",
                        "status": "completed",
                        "result_url": "https://api.example.com/results/image1_processed.jpg"
                    }
                ],
                "request_id": "req_123456",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }


class CapabilitiesResponse(APIResponse):
    """API capabilities response model."""
    
    success: bool = Field(default=True)
    capabilities: Dict[str, List[str]] = Field(...)
    models: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    limits: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "capabilities": {
                    "image": ["enhance", "style_transfer", "generate"],
                    "video": ["enhance", "stabilize"]
                },
                "models": {
                    "stable-diffusion-xl": {
                        "description": "High-quality image generation",
                        "max_resolution": "1024x1024"
                    }
                },
                "limits": {
                    "max_file_size": 52428800,
                    "rate_limit": 100,
                    "concurrent_jobs": 5
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }