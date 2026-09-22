from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from .database import get_db
from .security import decode_token
from ..models import User


def get_current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")
    user_id = decode_token(authorization.split(" ", 1)[1].strip())
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
