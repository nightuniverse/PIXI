from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.schemas.entity import EntitySearch, EntityList
from app.core.database import get_db
from app.services.search_service import SearchService

router = APIRouter()

@router.post("/", response_model=EntityList)
async def search_entities(
    search_query: EntitySearch,
    db: Session = Depends(get_db)
):
    """엔티티를 검색합니다."""
    service = SearchService(db)
    entities, total = service.search_entities(search_query)
    
    return EntityList(
        entities=entities,
        total=total,
        page=search_query.page,
        size=search_query.size
    )

@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """검색어 자동완성 제안을 제공합니다."""
    service = SearchService(db)
    suggestions = service.get_search_suggestions(q, limit)
    
    return {"suggestions": suggestions}

@router.get("/trending")
async def get_trending_searches(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """인기 검색어를 제공합니다."""
    service = SearchService(db)
    trending = service.get_trending_searches(limit)
    
    return {"trending": trending}

@router.get("/domains")
async def get_available_domains(db: Session = Depends(get_db)):
    """사용 가능한 도메인 태그들을 제공합니다."""
    service = SearchService(db)
    domains = service.get_available_domains()
    
    return {"domains": domains}

@router.get("/locations")
async def get_available_locations(db: Session = Depends(get_db)):
    """사용 가능한 국가/도시들을 제공합니다."""
    service = SearchService(db)
    locations = service.get_available_locations()
    
    return {"locations": locations}
