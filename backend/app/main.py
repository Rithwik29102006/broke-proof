from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from .api import auth, controller, dashboard, meta, transactions
from .core.config import get_settings
from .core.database import Base, SessionLocal, engine
from .models import Category
from .services.categorizer import DEFAULT_CATEGORIES, FIXED_CATEGORIES

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(dashboard.router, prefix=settings.api_prefix)
app.include_router(transactions.router, prefix=settings.api_prefix)
app.include_router(controller.router, prefix=settings.api_prefix)
app.include_router(meta.router, prefix=settings.api_prefix)


def init_db():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        existing = set(db.scalars(select(Category.name)))
        for name in DEFAULT_CATEGORIES:
            if name not in existing:
                db.add(Category(name=name, is_fixed=name in FIXED_CATEGORIES))
        db.commit()
