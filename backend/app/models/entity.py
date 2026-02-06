from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime
from typing import List, Optional

Base = declarative_base()

class Entity(Base):
    __tablename__ = "entities"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False, index=True)  # startup, investor, accelerator, space, event
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    website = Column(String(500))
    domains = Column(ARRAY(String))  # 도메인 태그들
    founded_year = Column(Integer)
    
    # 위치 정보
    country = Column(String(100), index=True)
    city = Column(String(100), index=True)
    lat = Column(Float)
    lon = Column(Float)
    
    # 펀딩 정보
    last_funding_round = Column(String(50))  # pre-seed, seed, Series A, etc.
    last_funding_amount_usd = Column(Float)
    last_funding_date = Column(DateTime)
    total_funding_usd = Column(Float)
    
    # 인력 정보
    headcount_estimate = Column(Integer)
    headcount_growth_12m_pct = Column(Float)
    
    # 채용 정보
    is_hiring = Column(Boolean, default=False)
    hiring_roles = Column(ARRAY(String))
    remote_ratio = Column(Float)  # 0.0 ~ 1.0
    
    # 성장 시그널
    web_traffic_trend = Column(Float)
    github_stars = Column(Integer)
    github_releases_90d = Column(Integer)
    app_reviews_count = Column(Integer)
    social_followers = Column(Integer)
    pr_frequency = Column(Float)
    
    # 링크들
    links = Column(JSON)  # {crunchbase, linkedin, github, careers, twitter}
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source_refs = Column(ARRAY(String))  # 데이터 출처들
    
    # 관계
    funding_rounds = relationship("FundingRound", back_populates="entity")
    investors = relationship("Investment", back_populates="startup")

class FundingRound(Base):
    __tablename__ = "funding_rounds"
    
    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("entities.id"))
    round_type = Column(String(50), nullable=False)  # pre-seed, seed, Series A, etc.
    amount_usd = Column(Float)
    date = Column(DateTime)
    investors = Column(ARRAY(String))  # 투자자 이름들
    
    entity = relationship("Entity", back_populates="funding_rounds")

class Investment(Base):
    __tablename__ = "investments"
    
    id = Column(Integer, primary_key=True, index=True)
    startup_id = Column(Integer, ForeignKey("entities.id"))
    investor_id = Column(Integer, ForeignKey("entities.id"))
    round_type = Column(String(50))
    amount_usd = Column(Float)
    date = Column(DateTime)
    
    startup = relationship("Entity", back_populates="investors")

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    event_type = Column(String(100))  # demo day, conference, meetup, etc.
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    location = Column(String(255))
    lat = Column(Float)
    lon = Column(Float)
    website = Column(String(500))
    organizers = Column(ARRAY(String))
    attendees_count = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
