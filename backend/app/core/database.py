from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from app.core.config import settings

Base = declarative_base()
engine = None
SessionLocal = None

try:
    SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    import warnings
    warnings.warn(f"DB 미연결 상태로 실행됩니다 (cofounder 등은 동작): {e}")
    engine = None
    SessionLocal = None

def get_db():
    if SessionLocal is None:
        raise HTTPException(status_code=503, detail="Database not configured. Set DATABASE_URL or install psycopg2-binary.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    if engine is not None:
        Base.metadata.create_all(bind=engine)
