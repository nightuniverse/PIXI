from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class EntityType(str, Enum):
    STARTUP = "startup"
    INVESTOR = "investor"
    ACCELERATOR = "accelerator"
    SPACE = "space"
    EVENT = "event"

class FundingRoundType(str, Enum):
    PRE_SEED = "pre-seed"
    SEED = "seed"
    SERIES_A = "Series A"
    SERIES_B = "Series B"
    SERIES_C = "Series C"
    SERIES_D = "Series D"
    IPO = "IPO"

class EntityBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    website: Optional[HttpUrl] = None
    domains: List[str] = []
    founded_year: Optional[int] = None
    
    # 위치 정보
    country: Optional[str] = None
    city: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None

class EntityCreate(EntityBase):
    type: EntityType

class EntityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[HttpUrl] = None
    domains: Optional[List[str]] = None
    founded_year: Optional[int] = None
    country: Optional[str] = None
    city: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None

class Entity(EntityBase):
    id: int
    type: EntityType
    
    # 펀딩 정보
    last_funding_round: Optional[str] = None
    last_funding_amount_usd: Optional[float] = None
    last_funding_date: Optional[datetime] = None
    total_funding_usd: Optional[float] = None
    
    # 인력 정보
    headcount_estimate: Optional[int] = None
    headcount_growth_12m_pct: Optional[float] = None
    
    # 채용 정보
    is_hiring: bool = False
    hiring_roles: List[str] = []
    remote_ratio: Optional[float] = None
    
    # 성장 시그널
    web_traffic_trend: Optional[float] = None
    github_stars: Optional[int] = None
    github_releases_90d: Optional[int] = None
    app_reviews_count: Optional[int] = None
    social_followers: Optional[int] = None
    pr_frequency: Optional[float] = None
    
    # 링크들
    links: Dict[str, str] = {}
    
    # 메타데이터
    created_at: datetime
    updated_at: datetime
    source_refs: List[str] = []
    
    class Config:
        from_attributes = True

class EntityList(BaseModel):
    entities: List[Entity]
    total: int
    page: int
    size: int

class EntityFilter(BaseModel):
    type: Optional[EntityType] = None
    domains: Optional[List[str]] = None
    country: Optional[str] = None
    city: Optional[str] = None
    funding_stage: Optional[FundingRoundType] = None
    is_hiring: Optional[bool] = None
    min_funding: Optional[float] = None
    max_funding: Optional[float] = None
    min_headcount: Optional[int] = None
    max_headcount: Optional[int] = None
    search: Optional[str] = None

class EntitySearch(BaseModel):
    query: str
    filters: Optional[EntityFilter] = None
    page: int = 1
    size: int = 20
    sort_by: str = "name"
    sort_order: str = "asc"

class GrowthScore(BaseModel):
    entity_id: int
    score: float
    factors: Dict[str, float]
    calculated_at: datetime
    
    class Config:
        from_attributes = True
