"""JWT token generation and verification utilities."""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()

# JWT Configuration
# IMPORTANT: Both frontend and backend must use the SAME SECRET_KEY
SECRET_KEY = os.getenv("SECRET_KEY", "same-secret-key-for-both-frontend-and-backend-dev-only")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))  # 7 days


def create_access_token(user_id: str, email: str) -> str:
    """Create JWT access token for user."""
    expire = datetime.utcnow() + timedelta(minutes=EXPIRE_MINUTES)
    to_encode = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict]:
    """Verify JWT token and return payload if valid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        if user_id is None or email is None:
            return None
        return {"user_id": user_id, "email": email}
    except JWTError as e:
        # Token is invalid (expired, wrong secret, malformed, etc.)
        print(f"Token verification failed (JWTError): {e}")
        return None
    except Exception as e:
        # Any other unexpected error
        print(f"Unexpected error during token verification: {e}")
        return None


def decode_token(token: str) -> Optional[str]:
    """Decode JWT token and return user_id if valid."""
    payload = verify_token(token)
    if payload:
        return payload["user_id"]
    return None
