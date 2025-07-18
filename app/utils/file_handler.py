"""
File handling utilities for FlowPlayground.
"""
import os
import asyncio
import aiofiles
import tempfile
import shutil
from typing import Optional, Dict, Any, List
from fastapi import UploadFile, HTTPException
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.services.media_processor import media_processor

logger = logging.getLogger(__name__)


class FileHandler:
    """Utility class for handling file operations."""
    
    @staticmethod
    async def validate_and_save_upload(upload_file: UploadFile) -> Dict[str, Any]:
        """Validate and save uploaded file."""
        try:
            # Read file content
            content = await upload_file.read()
            await upload_file.seek(0)  # Reset file pointer
            
            # Validate file
            file_info = media_processor.validate_file(
                content, 
                upload_file.content_type or "application/octet-stream",
                upload_file.filename or "unknown"
            )
            
            # Generate unique filename
            unique_filename = media_processor.generate_unique_filename(
                upload_file.filename or "upload"
            )
            
            # Determine subdirectory
            subdir = "images" if file_info["is_image"] else "videos"
            
            # Save file
            file_path = await media_processor.save_file(content, unique_filename, subdir)
            
            # Get metadata
            if file_info["is_image"]:
                metadata = media_processor.get_image_metadata(file_path)
            else:
                metadata = media_processor.get_video_metadata(file_path)
            
            # Create thumbnail for images
            thumbnail_filename = None
            if file_info["is_image"]:
                try:
                    thumbnail_filename = await media_processor.create_thumbnail(file_path)
                except Exception as e:
                    logger.warning(f"Failed to create thumbnail: {e}")
            
            return {
                "filename": unique_filename,
                "original_filename": upload_file.filename,
                "file_path": file_path,
                "subdir": subdir,
                "thumbnail_filename": thumbnail_filename,
                "file_info": file_info,
                "metadata": metadata,
                "file_url": media_processor.get_file_url(unique_filename, subdir),
                "thumbnail_url": media_processor.get_file_url(thumbnail_filename, "thumbnails") if thumbnail_filename else None,
            }
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to process upload: {e}")
            raise HTTPException(status_code=500, detail="Failed to process file upload")
    
    @staticmethod
    async def validate_multiple_uploads(upload_files: List[UploadFile]) -> List[Dict[str, Any]]:
        """Validate and save multiple uploaded files."""
        if len(upload_files) > 10:  # Limit batch size
            raise HTTPException(status_code=400, detail="Too many files. Maximum 10 files allowed.")
        
        results = []
        for upload_file in upload_files:
            try:
                result = await FileHandler.validate_and_save_upload(upload_file)
                results.append(result)
            except HTTPException as e:
                # Include filename in error for batch processing
                results.append({
                    "filename": upload_file.filename,
                    "error": e.detail,
                    "status_code": e.status_code
                })
        
        return results
    
    @staticmethod
    async def get_file_content(filename: str, subdir: str = "") -> bytes:
        """Get file content by filename."""
        try:
            return await media_processor.load_file(filename, subdir)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="File not found")
        except Exception as e:
            logger.error(f"Failed to load file {filename}: {e}")
            raise HTTPException(status_code=500, detail="Failed to load file")
    
    @staticmethod
    async def delete_file(filename: str, subdir: str = "") -> bool:
        """Delete file by filename."""
        try:
            success = await media_processor.delete_file(filename, subdir)
            if not success:
                raise HTTPException(status_code=404, detail="File not found")
            return success
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete file {filename}: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete file")
    
    @staticmethod
    @asynccontextmanager
    async def temporary_file(content: bytes, suffix: str = ""):
        """Context manager for temporary file handling."""
        temp_file = None
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_file.write(content)
            temp_file.flush()
            temp_file.close()
            
            yield temp_file.name
            
        finally:
            # Clean up
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file: {e}")
    
    @staticmethod
    async def copy_file(source_path: str, dest_filename: str, dest_subdir: str = "") -> str:
        """Copy file to destination."""
        try:
            dest_path = media_processor.get_file_path(dest_filename, dest_subdir)
            
            # Run in executor to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None, shutil.copy2, source_path, dest_path
            )
            
            return dest_path
        except Exception as e:
            logger.error(f"Failed to copy file: {e}")
            raise HTTPException(status_code=500, detail="Failed to copy file")
    
    @staticmethod
    async def move_file(source_path: str, dest_filename: str, dest_subdir: str = "") -> str:
        """Move file to destination."""
        try:
            dest_path = media_processor.get_file_path(dest_filename, dest_subdir)
            
            # Run in executor to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None, shutil.move, source_path, dest_path
            )
            
            return dest_path
        except Exception as e:
            logger.error(f"Failed to move file: {e}")
            raise HTTPException(status_code=500, detail="Failed to move file")
    
    @staticmethod
    def get_file_info(filename: str, subdir: str = "") -> Dict[str, Any]:
        """Get file information."""
        file_path = media_processor.get_file_path(filename, subdir)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        try:
            stat = os.stat(file_path)
            return {
                "filename": filename,
                "subdir": subdir,
                "file_path": file_path,
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "is_file": os.path.isfile(file_path),
                "file_url": media_processor.get_file_url(filename, subdir),
            }
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            raise HTTPException(status_code=500, detail="Failed to get file information")
    
    @staticmethod
    async def cleanup_temp_files(max_age_hours: int = 1) -> int:
        """Clean up temporary files."""
        try:
            return await media_processor.cleanup_old_files(max_age_hours)
        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {e}")
            return 0
    
    @staticmethod
    def validate_filename(filename: str) -> str:
        """Validate and sanitize filename."""
        if not filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        # Check for dangerous patterns
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        # Check length
        if len(filename) > 255:
            raise HTTPException(status_code=400, detail="Filename too long")
        
        return filename
    
    @staticmethod
    def get_storage_stats() -> Dict[str, Any]:
        """Get storage statistics."""
        return media_processor.get_storage_stats()


# Global file handler instance
file_handler = FileHandler()