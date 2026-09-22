from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from ..models import IncomeCycle, User
from ..schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def tokens_for(user_id: int) -> TokenResponse:
    return TokenResponse(access_token=create_access_token(user_id), refresh_token=create_refresh_token(user_id))


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(name=payload.name.strip(), email=payload.email.lower(), password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()
    cycle = IncomeCycle(
        user_id=user.id,
        start_date=payload.cycle_start,
        end_date=payload.cycle_end,
        starting_balance=payload.starting_balance,
        income_label="Current cycle",
    )
    db.add(cycle)
    db.commit()
    return tokens_for(user.id)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return tokens_for(user.id)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest):
    user_id = decode_token(payload.refresh_token, expected_type="refresh")
    return tokens_for(user_id)
