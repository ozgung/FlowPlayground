"""
Request models for FlowPlayground API.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class ImageOperation(str, Enum):
    """Supported image operations."""
    ENHANCE = "enhance"
    STYLE_TRANSFER = "style_transfer"
    GENERATE = "generate"
    UPSCALE = "upscale"
    BACKGROUND_REMOVAL = "background_removal"


class VideoOperation(str, Enum):
    """Supported video operations."""
    ENHANCE = "enhance"
    STYLE_TRANSFER = "style_transfer"
    STABILIZE = "stabilize"


class ImageEnhanceRequest(BaseModel):
    """Request model for image enhancement."""
    
    strength: float = Field(default=0.8, ge=0.1, le=1.0)
    preserve_details: bool = Field(default=True)
    enhance_colors: bool = Field(default=True)
    reduce_noise: bool = Field(default=True)
    
    class Config:
        json_schema_extra = {
            "example": {
                "strength": 0.8,
                "preserve_details": True,
                "enhance_colors": True,
                "reduce_noise": True
            }
        }


class StyleTransferRequest(BaseModel):
    """Request model for style transfer."""
    
    style_strength: float = Field(default=0.8, ge=0.1, le=1.0)
    preserve_structure: bool = Field(default=True)
    style_reference: Optional[str] = Field(default=None, description="URL or ID of style reference")
    
    class Config:
        json_schema_extra = {
            "example": {
                "style_strength": 0.8,
                "preserve_structure": True,
                "style_reference": "artistic_style_001"
            }
        }


class ImageGenerateRequest(BaseModel):
    """Request model for image generation."""
    
    prompt: str = Field(..., min_length=1, max_length=1000)
    negative_prompt: Optional[str] = Field(default=None, max_length=1000)
    width: int = Field(default=512, ge=128, le=2048)
    height: int = Field(default=512, ge=128, le=2048)
    num_inference_steps: int = Field(default=20, ge=1, le=100)
    guidance_scale: float = Field(default=7.5, ge=1.0, le=20.0)
    seed: Optional[int] = Field(default=None, ge=0)
    
    @validator("width", "height")
    def validate_dimensions(cls, v):
        if v % 8 != 0:
            raise ValueError("Width and height must be multiples of 8")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "A beautiful landscape with mountains and a lake",
                "negative_prompt": "blurry, low quality, distorted",
                "width": 512,
                "height": 512,
                "num_inference_steps": 20,
                "guidance_scale": 7.5,
                "seed": 42
            }
        }


class VideoProcessRequest(BaseModel):
    """Request model for video processing."""
    
    operation: VideoOperation
    quality: str = Field(default="high", pattern="^(low|medium|high)$")
    fps: Optional[int] = Field(default=None, ge=1, le=60)
    resolution: Optional[str] = Field(default=None, pattern="^(480p|720p|1080p|4k)$")
    
    class Config:
        json_schema_extra = {
            "example": {
                "operation": "enhance",
                "quality": "high",
                "fps": 30,
                "resolution": "1080p"
            }
        }


class BatchProcessRequest(BaseModel):
    """Request model for batch processing."""
    
    operation: ImageOperation
    files: List[str] = Field(..., min_items=1, max_items=10)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "operation": "enhance",
                "files": ["file1.jpg", "file2.png"],
                "parameters": {
                    "strength": 0.8,
                    "preserve_details": True
                }
            }
        }


class WebhookRequest(BaseModel):
    """Request model for webhook notifications."""
    
    url: str = Field(..., pattern="^https?://")
    events: List[str] = Field(..., min_items=1)
    secret: Optional[str] = Field(default=None, min_length=16)
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://myapp.com/webhook",
                "events": ["job.completed", "job.failed"],
                "secret": "my-webhook-secret"
            }
        }