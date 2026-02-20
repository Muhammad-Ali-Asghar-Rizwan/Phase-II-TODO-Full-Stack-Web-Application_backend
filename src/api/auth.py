from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from ..core.security import verify_token
from typing import Annotated

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user_token(token: Annotated[str, Depends(oauth2_scheme)]):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

@router.get("/whoami")
def read_users_me(token_payload: Annotated[dict, Depends(get_current_user_token)]):
    return token_payload
