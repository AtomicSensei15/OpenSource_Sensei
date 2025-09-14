"""
Security utilities for authentication and authorization.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
import hashlib
import secrets
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from .config import get_settings

settings = get_settings()

# JWT token handler
security = HTTPBearer()


class TokenData(BaseModel):
    """Token data model."""
    username: Optional[str] = None
    scopes: list[str] = []


class User(BaseModel):
    """User model for authentication."""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: bool = False
    scopes: list[str] = []


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using SHA-256."""
    # Simple hash comparison for demo purposes
    # In production, use proper password hashing like bcrypt
    plain_hash = hashlib.sha256(plain_password.encode()).hexdigest()
    return plain_hash == hashed_password


def get_password_hash(password: str) -> str:
    """Hash a password using SHA-256."""
    # In production, use proper password hashing like bcrypt with salt
    return hashlib.sha256(password.encode()).hexdigest()


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(credentials: HTTPAuthorizationCredentials) -> User:
    """Get current user from token."""
    token = credentials.credentials
    payload = verify_token(token)
    
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # In a real application, you would fetch user from database
    # For now, return a mock user
    return User(
        username=username,
        scopes=payload.get("scopes", [])
    )


def require_scopes(required_scopes: list[str]):
    """Decorator to require specific scopes for endpoint access."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This would be implemented with FastAPI's Security dependency
            # For now, just return the function
            return func(*args, **kwargs)
        return wrapper
    return decorator


def generate_api_key() -> str:
    """Generate a secure API key."""
    import secrets
    return secrets.token_urlsafe(32)


def validate_api_key(api_key: str) -> bool:
    """Validate an API key."""
    # In a real application, you would check against database
    # For now, just check if it's not empty
    return bool(api_key and len(api_key) >= 32)


class APIKeyManager:
    """Manage API keys for service authentication."""
    
    def __init__(self):
        self.active_keys: Dict[str, Dict[str, Any]] = {}
    
    def create_api_key(self, name: str, scopes: list[str] | None = None) -> str:
        """Create a new API key."""
        api_key = generate_api_key()
        self.active_keys[api_key] = {
            "name": name,
            "scopes": scopes or [],
            "created_at": datetime.utcnow(),
            "last_used": None,
            "usage_count": 0
        }
        return api_key
    
    def validate_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate and get API key info."""
        key_info = self.active_keys.get(api_key)
        if key_info:
            key_info["last_used"] = datetime.utcnow()
            key_info["usage_count"] += 1
        return key_info
    
    def revoke_key(self, api_key: str) -> bool:
        """Revoke an API key."""
        return self.active_keys.pop(api_key, None) is not None
    
    def list_keys(self) -> Dict[str, Dict[str, Any]]:
        """List all active API keys."""
        return self.active_keys.copy()


# Global API key manager instance
api_key_manager = APIKeyManager()


def sanitize_input(input_string: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent injection attacks."""
    if not isinstance(input_string, str):
        return ""
    
    # Remove null bytes
    sanitized = input_string.replace('\x00', '')
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', '\r', '\n']
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    return sanitized.strip()


def validate_file_upload(filename: str, content_type: str, file_size: int) -> bool:
    """Validate file upload parameters."""
    # Check file size
    if file_size > settings.max_file_size:
        return False
    
    # Check file extension
    file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
    allowed_extensions = [ext.lstrip('.') for ext in settings.allowed_file_types]
    
    if file_ext not in allowed_extensions:
        return False
    
    # Check content type (basic validation)
    allowed_content_types = [
        'application/zip',
        'application/x-tar',
        'application/gzip',
        'application/x-rar-compressed',
        'text/plain',
        'text/x-python',
        'application/javascript',
        'text/javascript',
    ]
    
    if content_type not in allowed_content_types:
        return False
    
    return True