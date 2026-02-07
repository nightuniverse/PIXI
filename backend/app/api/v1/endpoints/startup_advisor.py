"""
창업 아이템 분석 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.startup_advisor import StartupIdeaRequest, StartupAnalysisResponse
from app.services.startup_advisor_service import StartupAdvisorService

router = APIRouter()

@router.post("/analyze", response_model=StartupAnalysisResponse)
async def analyze_startup_idea(request: StartupIdeaRequest):
    """
    창업 아이템을 GPT-4o를 활용하여 종합적으로 분석합니다.
    
    - **category**: 카테고리 (필수)
    - **idea_description**: 아이디어 설명 (선택)
    - **market_data**: 시장 데이터 (선택)
    """
    try:
        service = StartupAdvisorService()
        result = service.analyze_startup_idea(
            category=request.category,
            idea_description=request.idea_description or "",
            market_data=request.market_data or {}
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 중 오류가 발생했습니다: {str(e)}")
