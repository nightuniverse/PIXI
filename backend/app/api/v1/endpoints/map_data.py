from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.core.database import get_db
from app.services.map_service import MapService

router = APIRouter()

@router.get("/clusters")
async def get_map_clusters(
    zoom: float = Query(..., ge=0, le=22),
    bounds: str = Query(..., description="south,west,north,east"),
    db: Session = Depends(get_db)
):
    """지도 줌 레벨과 경계에 따른 클러스터 데이터를 제공합니다."""
    service = MapService(db)
    
    # bounds 파싱: "south,west,north,east"
    try:
        south, west, north, east = map(float, bounds.split(','))
        bounds_dict = {"south": south, "west": west, "north": north, "east": east}
    except ValueError:
        return {"error": "Invalid bounds format"}
    
    clusters = service.get_clusters(zoom, bounds_dict)
    return {"clusters": clusters}

@router.get("/entities-in-bounds")
async def get_entities_in_bounds(
    bounds: str = Query(..., description="south,west,north,east"),
    entity_type: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """특정 경계 내의 엔티티들을 제공합니다."""
    service = MapService(db)
    
    try:
        south, west, north, east = map(float, bounds.split(','))
        bounds_dict = {"south": south, "west": west, "north": north, "east": east}
    except ValueError:
        return {"error": "Invalid bounds format"}
    
    entities = service.get_entities_in_bounds(bounds_dict, entity_type, limit)
    return {"entities": entities}

@router.get("/heatmap")
async def get_heatmap_data(
    bounds: str = Query(..., description="south,west,north,east"),
    metric: str = Query("startup_count", description="startup_count, funding_amount, hiring_count"),
    db: Session = Depends(get_db)
):
    """히트맵 데이터를 제공합니다."""
    service = MapService(db)
    
    try:
        south, west, north, east = map(float, bounds.split(','))
        bounds_dict = {"south": south, "west": west, "north": north, "east": east}
    except ValueError:
        return {"error": "Invalid bounds format"}
    
    heatmap_data = service.get_heatmap_data(bounds_dict, metric)
    return {"heatmap": heatmap_data}

@router.get("/city-stats")
async def get_city_statistics(
    city: str = Query(...),
    country: str = Query(...),
    db: Session = Depends(get_db)
):
    """특정 도시의 통계 정보를 제공합니다."""
    service = MapService(db)
    stats = service.get_city_statistics(city, country)
    
    if not stats:
        return {"error": "City not found"}
    
    return stats

@router.get("/country-stats")
async def get_country_statistics(
    country: str = Query(...),
    db: Session = Depends(get_db)
):
    """특정 국가의 통계 정보를 제공합니다."""
    service = MapService(db)
    stats = service.get_country_statistics(country)
    
    if not stats:
        return {"error": "Country not found"}
    
    return stats

@router.get("/global-overview")
async def get_global_overview(db: Session = Depends(get_db)):
    """전 세계 스타트업 생태계 개요를 제공합니다."""
    service = MapService(db)
    overview = service.get_global_overview()
    
    return overview
