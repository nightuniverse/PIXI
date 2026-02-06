from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.schemas.entity import Entity, EntityCreate, EntityUpdate, EntityList, EntityFilter
from app.core.database import get_db
from app.services.entity_service import EntityService

router = APIRouter()

@router.get("/", response_model=EntityList)
async def get_entities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    type: Optional[str] = None,
    country: Optional[str] = None,
    city: Optional[str] = None,
    is_hiring: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """엔티티 목록을 조회합니다."""
    filters = EntityFilter(
        type=type,
        country=country,
        city=city,
        is_hiring=is_hiring
    )
    
    service = EntityService(db)
    entities, total = service.get_entities(filters, skip, limit)
    
    return EntityList(
        entities=entities,
        total=total,
        page=skip // limit + 1,
        size=limit
    )

@router.get("/{entity_id}", response_model=Entity)
async def get_entity(entity_id: int, db: Session = Depends(get_db)):
    """특정 엔티티를 조회합니다."""
    service = EntityService(db)
    entity = service.get_entity(entity_id)
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return entity

@router.post("/", response_model=Entity)
async def create_entity(entity: EntityCreate, db: Session = Depends(get_db)):
    """새로운 엔티티를 생성합니다."""
    service = EntityService(db)
    return service.create_entity(entity)

@router.put("/{entity_id}", response_model=Entity)
async def update_entity(
    entity_id: int,
    entity_update: EntityUpdate,
    db: Session = Depends(get_db)
):
    """엔티티를 업데이트합니다."""
    service = EntityService(db)
    entity = service.update_entity(entity_id, entity_update)
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return entity

@router.delete("/{entity_id}")
async def delete_entity(entity_id: int, db: Session = Depends(get_db)):
    """엔티티를 삭제합니다."""
    service = EntityService(db)
    success = service.delete_entity(entity_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return {"message": "Entity deleted successfully"}

@router.get("/{entity_id}/growth-score")
async def get_entity_growth_score(entity_id: int, db: Session = Depends(get_db)):
    """엔티티의 성장 시그널 점수를 조회합니다."""
    service = EntityService(db)
    score = service.calculate_growth_score(entity_id)
    
    if not score:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return score
