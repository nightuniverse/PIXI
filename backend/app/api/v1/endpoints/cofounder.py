"""
AI 공동창업자 채팅 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.services.cofounder_service import CofounderService

router = APIRouter()

class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    message: str
    current_phase: str  # 'idea', 'research', 'solution', 'mvp', 'launch'
    project_state: Optional[Dict[str, Any]] = None
    conversation_history: Optional[List[ChatMessage]] = None

class ChatResponse(BaseModel):
    response: str
    next_phase: Optional[str] = None
    project_state: Optional[Dict[str, Any]] = None
    actions: Optional[List[str]] = None

@router.post("/chat", response_model=ChatResponse)
async def chat_with_cofounder(request: ChatRequest):
    """
    AI 공동창업자와 대화합니다.
    
    - **message**: 사용자 메시지
    - **current_phase**: 현재 단계
    - **project_state**: 프로젝트 상태 (선택)
    - **conversation_history**: 대화 기록 (선택)
    """
    import traceback
    try:
        service = CofounderService()
        # ChatMessage 객체를 딕셔너리로 변환
        conversation_history_dict = []
        if request.conversation_history:
            for msg in request.conversation_history:
                conversation_history_dict.append({
                    'role': msg.role,
                    'content': msg.content
                })
        
        result = service.process_message(
            message=request.message,
            current_phase=request.current_phase,
            project_state=request.project_state or {},
            conversation_history=conversation_history_dict
        )
        return result
    except ValueError as e:
        # 설정 오류 (예: OPENAI_API_KEY 없음)
        raise HTTPException(status_code=400, detail=f"설정 오류: {str(e)}")
    except Exception as e:
        # 상세한 에러 정보 로깅
        error_trace = traceback.format_exc()
        print(f"ERROR in chat_with_cofounder: {str(e)}")
        print(f"Traceback: {error_trace}")
        raise HTTPException(
            status_code=500, 
            detail=f"처리 중 오류가 발생했습니다: {str(e)}"
        )
