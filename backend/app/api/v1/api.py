from fastapi import APIRouter
from app.api.v1.endpoints import entities, search, map_data, startup_advisor, cofounder
# 소셜 미디어 조사 기능은 제외됨 (praw 의존성 문제)
# from app.api.v1.endpoints import social_research

api_router = APIRouter()

api_router.include_router(entities.router, prefix="/entities", tags=["entities"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(map_data.router, prefix="/map", tags=["map"])
api_router.include_router(startup_advisor.router, prefix="/startup-advisor", tags=["startup-advisor"])
api_router.include_router(cofounder.router, prefix="/cofounder", tags=["cofounder"])
# 소셜 미디어 조사 기능은 제외됨
# api_router.include_router(social_research.router, prefix="/social-research", tags=["social-research"])