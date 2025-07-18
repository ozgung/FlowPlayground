"""
Service layer for FlowPlayground.
"""
from .fal_ai import fal_ai_service, FalAIError
from .media_processor import media_processor

__all__ = [
    "fal_ai_service",
    "FalAIError",
    "media_processor",
]