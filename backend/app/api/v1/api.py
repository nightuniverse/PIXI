from fastapi import APIRouter
from app.api.v1.endpoints import entities, search, map_data

api_router = APIRouter()

api_router.include_router(entities.router, prefix="/entities", tags=["entities"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(map_data.router, prefix="/map", tags=["map"])
