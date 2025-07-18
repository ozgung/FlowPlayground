"""
Media processing utilities and helpers.
"""
import os
import asyncio
import aiofiles
import hashlib
import mimetypes
from typing import Optional, Dict, Any, BinaryIO
from PIL import Image
import uuid
from datetime import datetime
import logging

from app.core.config import settings
from app.core.security import sanitize_filename, validate_file_type

logger = logging.getLogger(__name__)


class MediaProcessor:
    """Service for processing media files."""
    
    def __init__(self):
        self.upload_dir = settings.upload_path
        self.max_file_size = settings.max_file_size
        self.allowed_image_types = settings.allowed_image_types
        self.allowed_video_types = settings.allowed_video_types
        self._ensure_upload_dir()
    
    def _ensure_upload_dir(self):
        """Ensure upload directory exists."""
        os.makedirs(self.upload_dir, exist_ok=True)
        
        # Create subdirectories
        for subdir in ['images', 'videos', 'processed', 'thumbnails']:
            os.makedirs(os.path.join(self.upload_dir, subdir), exist_ok=True)
    
    def generate_unique_filename(self, original_filename: str) -> str:
        """Generate unique filename while preserving extension."""
        sanitized = sanitize_filename(original_filename)
        name, ext = os.path.splitext(sanitized)
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{name}_{timestamp}_{unique_id}{ext}"
    
    def get_file_path(self, filename: str, subdir: str = "") -> str:
        """Get full file path."""
        if subdir:
            return os.path.join(self.upload_dir, subdir, filename)
        return os.path.join(self.upload_dir, filename)
    
    def validate_file(self, content: bytes, content_type: str, filename: str) -> Dict[str, Any]:
        """Validate uploaded file."""
        # Check file size
        if len(content) > self.max_file_size:
            raise ValueError(f"File size exceeds maximum limit of {self.max_file_size} bytes")
        
        # Check content type
        is_image = validate_file_type(content_type, self.allowed_image_types)
        is_video = validate_file_type(content_type, self.allowed_video_types)
        
        if not (is_image or is_video):
            allowed_types = self.allowed_image_types + self.allowed_video_types
            raise ValueError(f"Unsupported file type. Allowed types: {allowed_types}")
        
        # Generate file hash for deduplication
        file_hash = hashlib.md5(content).hexdigest()
        
        return {
            "is_image": is_image,
            "is_video": is_video,
            "file_hash": file_hash,
            "file_size": len(content),
            "content_type": content_type,
            "filename": filename,
        }
    
    async def save_file(self, content: bytes, filename: str, subdir: str = "") -> str:
        """Save file to disk asynchronously."""
        file_path = self.get_file_path(filename, subdir)
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        logger.info(f"Saved file: {file_path}")
        return file_path
    
    async def load_file(self, filename: str, subdir: str = "") -> bytes:
        """Load file from disk asynchronously."""
        file_path = self.get_file_path(filename, subdir)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        async with aiofiles.open(file_path, 'rb') as f:
            content = await f.read()
        
        return content
    
    async def delete_file(self, filename: str, subdir: str = "") -> bool:
        """Delete file from disk."""
        file_path = self.get_file_path(filename, subdir)
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False
    
    def get_image_metadata(self, image_path: str) -> Dict[str, Any]:
        """Extract metadata from image file."""
        try:
            with Image.open(image_path) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                    "has_transparency": img.mode in ('RGBA', 'LA') or 'transparency' in img.info,
                    "file_size": os.path.getsize(image_path),
                }
        except Exception as e:
            logger.error(f"Failed to extract image metadata: {e}")
            return {}
    
    def get_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """Extract metadata from video file."""
        try:
            # This is a placeholder - in production, you'd use ffprobe or similar
            return {
                "file_size": os.path.getsize(video_path),
                "format": os.path.splitext(video_path)[1][1:].lower(),
                # Add more metadata extraction as needed
            }
        except Exception as e:
            logger.error(f"Failed to extract video metadata: {e}")
            return {}
    
    async def create_thumbnail(self, image_path: str, size: tuple = (256, 256)) -> str:
        """Create thumbnail from image."""
        try:
            thumbnail_filename = f"thumb_{os.path.basename(image_path)}"
            thumbnail_path = self.get_file_path(thumbnail_filename, "thumbnails")
            
            # Run in executor to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None, self._create_thumbnail_sync, image_path, thumbnail_path, size
            )
            
            return thumbnail_filename
        except Exception as e:
            logger.error(f"Failed to create thumbnail: {e}")
            raise
    
    def _create_thumbnail_sync(self, image_path: str, thumbnail_path: str, size: tuple):
        """Create thumbnail synchronously."""
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img, mask=img.split()[-1])
                img = background
            
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
    
    async def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """Clean up old files from upload directory."""
        deleted_count = 0
        current_time = datetime.now()
        
        for root, dirs, files in os.walk(self.upload_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    age_hours = (current_time - file_mtime).total_seconds() / 3600
                    
                    if age_hours > max_age_hours:
                        os.remove(file_path)
                        deleted_count += 1
                        logger.info(f"Deleted old file: {file_path}")
                        
                except Exception as e:
                    logger.error(f"Failed to delete old file {file_path}: {e}")
        
        logger.info(f"Cleanup completed. Deleted {deleted_count} old files.")
        return deleted_count
    
    def get_file_url(self, filename: str, subdir: str = "") -> str:
        """Generate URL for accessing file."""
        if subdir:
            return f"/files/{subdir}/{filename}"
        return f"/files/{filename}"
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        stats = {
            "total_files": 0,
            "total_size": 0,
            "by_type": {}
        }
        
        for root, dirs, files in os.walk(self.upload_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_size = os.path.getsize(file_path)
                    file_ext = os.path.splitext(file)[1][1:].lower()
                    
                    stats["total_files"] += 1
                    stats["total_size"] += file_size
                    
                    if file_ext not in stats["by_type"]:
                        stats["by_type"][file_ext] = {"count": 0, "size": 0}
                    
                    stats["by_type"][file_ext]["count"] += 1
                    stats["by_type"][file_ext]["size"] += file_size
                    
                except Exception as e:
                    logger.error(f"Failed to get stats for {file_path}: {e}")
        
        return stats


# Global service instance
media_processor = MediaProcessor()