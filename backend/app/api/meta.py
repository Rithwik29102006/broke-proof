from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models import Category

router = APIRouter(tags=["meta"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/categories")
def categories(db: Session = Depends(get_db)):
    return [c.name for c in db.scalars(select(Category).order_by(Category.name.asc()))]
