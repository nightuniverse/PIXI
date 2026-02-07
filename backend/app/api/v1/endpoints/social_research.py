"""
소셜 미디어 조사 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.services.social_research_service import SocialResearchService

router = APIRouter()

@router.get("/search")
async def search_social_media(
    query: str = Query(..., description="검색어"),
    source: Optional[str] = Query(None, description="소스 (reddit, naver_cafe, all)"),
    limit: int = Query(10, ge=1, le=50, description="결과 개수")
):
    """
    소셜 미디어에서 검색합니다.
    
    - **query**: 검색어
    - **source**: 소스 선택 (reddit, naver_cafe, all)
    - **limit**: 결과 개수 (최대 50)
    """
    try:
        service = SocialResearchService()
        
        if source == 'reddit':
            results = service.search_reddit(query, limit)
        elif source == 'naver_cafe':
            results = service.search_naver_cafe(query, limit)
        else:
            # 둘 다 검색
            reddit_results = service.search_reddit(query, limit // 2)
            naver_results = service.search_naver_cafe(query, limit // 2)
            results = reddit_results + naver_results
        
        return {
            "query": query,
            "source": source or "all",
            "count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 중 오류가 발생했습니다: {str(e)}")

@router.post("/research")
async def research_topic(
    topic: str = Query(..., description="조사 주제"),
    keywords: Optional[List[str]] = Query(None, description="추가 키워드")
):
    """
    주제에 대한 종합 조사를 수행합니다.
    """
    try:
        service = SocialResearchService()
        result = service.research_topic(topic, keywords or [])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"조사 중 오류가 발생했습니다: {str(e)}")
