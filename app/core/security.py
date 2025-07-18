"""
Security utilities for FlowPlayground.
"""
import hashlib
import hmac
import secrets
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings


security = HTTPBearer(auto_error=False)


class APIKeyAuth:
    """API Key authentication handler."""
    
    def __init__(self):
        self.valid_api_keys = self._load_api_keys()
    
    def _load_api_keys(self) -> dict:
        """Load valid API keys from environment or database."""
        # For now, we'll use a simple environment variable approach
        # In production, this should be stored in a database
        keys = {}
        api_keys_env = settings.secret_key  # This should be a comma-separated list in production
        
        # Generate a default API key for development
        if settings.is_development:
            default_key = "dev-api-key-" + secrets.token_urlsafe(32)
            keys[default_key] = {"name": "Development Key", "active": True}
        
        return keys
    
    def verify_api_key(self, api_key: str) -> bool:
        """Verify if the provided API key is valid."""
        return api_key in self.valid_api_keys and self.valid_api_keys[api_key]["active"]
    
    def generate_api_key(self, name: str) -> str:
        """Generate a new API key."""
        api_key = secrets.token_urlsafe(32)
        self.valid_api_keys[api_key] = {"name": name, "active": True}
        return api_key


api_key_auth = APIKeyAuth()


async def get_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> str:
    """
    Dependency to extract and validate API key from Authorization header.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not api_key_auth.verify_api_key(credentials.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return credentials.credentials


def verify_request_signature(
    payload: bytes, 
    signature: str, 
    secret: str
) -> bool:
    """
    Verify request signature for iOS app requests.
    """
    expected_signature = hmac.new(
        secret.encode(), 
        payload, 
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected_signature}", signature)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal attacks.
    """
    # Remove path separators and other dangerous characters
    filename = filename.replace("/", "_").replace("\\", "_")
    filename = filename.replace("..", "_").replace("~", "_")
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        filename = name[:250] + ("." + ext if ext else "")
    
    return filename


def validate_file_type(content_type: str, allowed_types: list) -> bool:
    """
    Validate if the file type is allowed.
    """
    return content_type in allowed_types