import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from fastapi import Depends, HTTPException, Query, Request, status
from fastapi.security import (
    OAuth2PasswordBearer,
    HTTPBearer,
    HTTPAuthorizationCredentials
)
from backend.db.postgres import get_db_cursor

# Secure JWT configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET", "b9a1d4f2e6c8a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d3e5f7a9b1c3d5e7f9a1b3")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24 hours

# OAuth2PasswordBearer scheme: In Swagger docs "Authorize" dialog, renders username & password input fields!
oauth2_password_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    auto_error=False,
    scheme_name="OAuth2PasswordAuth",
    description="Authorize directly with your username and password."
)

# HTTPBearer scheme: Allows entering Bearer token directly
jwt_bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="BearerAuth",
    description="Or enter your JWT Bearer token directly."
)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token containing subject, user claims, and expiration."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=JWT_EXPIRE_MINUTES)
    
    # Standard JWT claims
    to_encode.update({
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "iss": "budget-management-system"
    })
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT access token."""
    try:
        # Strip potential 'Bearer ' prefix if passed directly
        cleaned_token = token.strip()
        if cleaned_token.lower().startswith("bearer "):
            cleaned_token = cleaned_token[7:].strip()
            
        payload = jwt.decode(
            cleaned_token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            issuer="budget-management-system"
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT token has expired. Please login again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid JWT token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )

def get_current_user_jwt(
    request: Request,
    token_oauth2: Optional[str] = Depends(oauth2_password_scheme),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(jwt_bearer_scheme)
) -> Dict[str, Any]:
    """
    FastAPI dependency for protected routes requiring valid JWT authentication.
    Supports either OAuth2 password authorization (typing username & password in Authorize modal)
    or HTTPBearer token entry.
    """
    token = token_oauth2 or (credentials.credentials if credentials else None)
    if not token and request:
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization required. Please click 'Authorize' in Swagger docs and enter your credentials or JWT Bearer token.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    payload = decode_access_token(token)
    
    user_id = payload.get("user_id") or payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing user identification ('sub' or 'user_id').",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        user_id_int = int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format in token payload.",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    with get_db_cursor() as (cur, conn):
        cur.execute("""
            SELECT user_id, name, email, username
            FROM users
            WHERE user_id = %s;
        """, (user_id_int,))
        row = cur.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"User associated with this token (ID {user_id_int}) no longer exists.",
                headers={"WWW-Authenticate": "Bearer"}
            )
            
        return {
            "user_id": row[0],
            "name": row[1],
            "email": row[2],
            "username": row[3],
            "jwt_claims": payload
        }

def get_optional_current_user_jwt(
    request: Request,
    token_oauth2: Optional[str] = Depends(oauth2_password_scheme),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(jwt_bearer_scheme),
    user_id: Optional[int] = Query(None, description="Optional user ID fallback if not using Bearer token")
) -> Dict[str, Any]:
    """
    Flexible dependency that authenticates via JWT if provided,
    or falls back to the user_id query parameter for backward compatibility.
    """
    token = token_oauth2 or (credentials.credentials if credentials else None)
    if not token and request:
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()

    if token:
        try:
            return get_current_user_jwt(request=request, token_oauth2=token, credentials=None)
        except HTTPException:
            if user_id is None:
                raise
    
    effective_id = user_id or 1
    with get_db_cursor() as (cur, conn):
        cur.execute("""
            SELECT user_id, name, email, username
            FROM users
            WHERE user_id = %s;
        """, (effective_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"User ID {effective_id} not found.")
        return {
            "user_id": row[0],
            "name": row[1],
            "email": row[2],
            "username": row[3],
            "jwt_claims": None
        }
