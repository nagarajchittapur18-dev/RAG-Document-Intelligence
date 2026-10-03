import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.services.document_store import DatabaseManager, UserRecord
from app.utils.security import decode_access_token

logger = logging.getLogger("ragmate.dependencies")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)
db = DatabaseManager()


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> UserRecord:
    """
    FastAPI dependency validating Bearer JWT and returning the authenticated user.
    Rejects unauthorized, expired, or malformed requests with HTTP 401.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(token)
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError as e:
        logger.warning("JWT validation failed: %s", e)
        raise credentials_exception
    except Exception as e:
        logger.error("Unexpected error in JWT decoding: %s", e)
        raise credentials_exception

    user = db.get_user_by_id(user_id)
    if user is None:
        raise credentials_exception

    return user
