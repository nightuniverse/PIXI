from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # API 설정
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "PIXI"
    
    # CORS 설정
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://pixi.vercel.app"
    ]
    
    # 데이터베이스 설정
    DATABASE_URL: str = "postgresql://user:password@localhost/pixi_db"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "pixi_user"
    POSTGRES_PASSWORD: str = "pixi_password"
    POSTGRES_DB: str = "pixi_db"
    
    # Redis 설정
    REDIS_URL: str = "redis://localhost:6379"
    
    # Mapbox 설정
    MAPBOX_ACCESS_TOKEN: Optional[str] = None
    
    # 외부 API 설정
    CRUNCHBASE_API_KEY: Optional[str] = None
    LINKEDIN_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # 소셜 미디어 API 설정
    REDDIT_CLIENT_ID: Optional[str] = None
    REDDIT_CLIENT_SECRET: Optional[str] = None
    REDDIT_USER_AGENT: Optional[str] = "PIXI Startup Research Bot"
    NAVER_CLIENT_ID: Optional[str] = None
    NAVER_CLIENT_SECRET: Optional[str] = None
    
    # 보안 설정
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
