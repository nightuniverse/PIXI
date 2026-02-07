from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class StartupIdeaRequest(BaseModel):
    """창업 아이템 분석 요청"""
    category: str = Field(..., description="카테고리 (예: SaaS, AI, 핀테크)")
    idea_description: Optional[str] = Field(None, description="아이디어 설명")
    market_data: Optional[Dict[str, Any]] = Field(None, description="시장 데이터 (회사 수, 경쟁사 등)")
    user_background: Optional[str] = Field(None, description="사용자 배경 (선택사항)")

class RevenueStream(BaseModel):
    """수익원 상세"""
    stream: str = Field(..., description="수익원 이름")
    description: str = Field(..., description="구체적 설명")
    expected_revenue: Optional[str] = Field(None, description="예상 수익")

class BusinessModel(BaseModel):
    """비즈니스 모델 제안"""
    model_type: str = Field(..., description="모델 유형 (예: SaaS, 마켓플레이스, 프리미엄)")
    description: str = Field(..., description="모델 설명")
    revenue_streams: List[RevenueStream] = Field(..., description="수익원 상세")
    pricing_strategy: Optional[str] = Field(None, description="가격 전략")
    unit_economics: Optional[str] = Field(None, description="단위 경제성 (CAC, LTV 등)")

class TargetCustomer(BaseModel):
    """타겟 고객 상세"""
    segment: str = Field(..., description="구체적인 타겟 세그먼트")
    size: Optional[str] = Field(None, description="예상 고객 수")
    pain_points: List[str] = Field(..., description="페인 포인트")
    willingness_to_pay: Optional[str] = Field(None, description="예상 지불 의향")

class CompetitorAnalysis(BaseModel):
    """경쟁사 분석"""
    competitor_name: str = Field(..., description="경쟁사 이름")
    strengths: List[str] = Field(..., description="강점")
    weaknesses: List[str] = Field(..., description="약점")
    market_position: Optional[str] = Field(None, description="시장 포지션")
    opportunity_gap: Optional[str] = Field(None, description="놓치고 있는 기회")

class MarketOpportunity(BaseModel):
    """시장 기회 분석"""
    opportunity: str = Field(..., description="기회 설명")
    market_size: Optional[str] = Field(None, description="시장 규모 추정")
    growth_potential: str = Field(..., description="성장 잠재력")
    entry_barriers: List[str] = Field(..., description="진입 장벽")
    time_window: Optional[str] = Field(None, description="기회의 시간적 윈도우")

class CompetitiveAdvantage(BaseModel):
    """경쟁 우위"""
    advantage: str = Field(..., description="우위 요소")
    sustainability: str = Field(..., description="지속 가능성")
    moat_strength: str = Field(..., description="방어력 강도 (weak/medium/strong)")

class RiskAnalysis(BaseModel):
    """리스크 분석"""
    risk: str = Field(..., description="리스크 설명")
    probability: str = Field(..., description="발생 확률 (low/medium/high)")
    impact: str = Field(..., description="영향도 (low/medium/high)")
    mitigation: str = Field(..., description="완화 방안")
    contingency_plan: Optional[str] = Field(None, description="대비 계획")

class ActionPlan(BaseModel):
    """실행 계획"""
    phase: str = Field(..., description="단계 (예: MVP, 시장 진입, 확장)")
    timeline: str = Field(..., description="예상 기간")
    key_actions: List[str] = Field(..., description="핵심 액션")
    success_metrics: List[str] = Field(..., description="성공 지표")
    budget: Optional[str] = Field(None, description="필요 예산")

class KoreanMarketSpecifics(BaseModel):
    """한국 시장 특화 정보"""
    government_policies: Optional[str] = Field(None, description="관련 정부 정책")
    regulations: Optional[str] = Field(None, description="주의해야 할 규제")
    market_characteristics: Optional[str] = Field(None, description="한국 시장 특성")
    investment_trends: Optional[str] = Field(None, description="투자 트렌드")

class InvestmentPerspective(BaseModel):
    """투자자 관점"""
    investability: str = Field(..., description="투자 가능성 (high/medium/low)")
    valuation_estimate: Optional[str] = Field(None, description="예상 밸류에이션")
    funding_needs: Optional[str] = Field(None, description="필요 자금 규모")
    investor_fit: Optional[str] = Field(None, description="적합한 투자자 유형")
    key_metrics_for_investors: Optional[List[str]] = Field(None, description="투자자가 보는 핵심 지표")

class FailureCase(BaseModel):
    """실패 사례"""
    case: str = Field(..., description="유사 아이디어로 실패한 사례")
    failure_reason: str = Field(..., description="실패 이유")
    lesson: str = Field(..., description="교훈")

class StartupAnalysisResponse(BaseModel):
    """창업 아이템 분석 응답"""
    # 핵심 분석
    idea_summary: str = Field(..., description="아이디어 요약")
    market_analysis: str = Field(..., description="시장 분석")
    target_customers: List[TargetCustomer] = Field(..., description="타겟 고객 상세")
    
    # 경쟁사 분석
    competitor_analysis: List[CompetitorAnalysis] = Field(default_factory=list, description="경쟁사 분석")
    
    # 비즈니스 모델
    business_models: List[BusinessModel] = Field(..., description="비즈니스 모델 제안")
    recommended_model: BusinessModel = Field(..., description="추천 모델")
    
    # 한국 시장 특화
    korean_market_specifics: Optional[KoreanMarketSpecifics] = Field(None, description="한국 시장 특화 정보")
    
    # 시장 기회
    opportunities: List[MarketOpportunity] = Field(..., description="시장 기회")
    
    # 경쟁 우위
    competitive_advantages: List[CompetitiveAdvantage] = Field(..., description="경쟁 우위")
    
    # 리스크
    risks: List[RiskAnalysis] = Field(..., description="리스크 분석")
    
    # 실행 계획
    action_plan: List[ActionPlan] = Field(..., description="실행 계획")
    
    # 투자자 관점
    investment_perspective: Optional[InvestmentPerspective] = Field(None, description="투자자 관점")
    
    # 추가 인사이트
    key_insights: List[str] = Field(..., description="핵심 인사이트")
    next_steps: List[str] = Field(..., description="다음 단계")
    
    # 실패 사례
    failure_cases: List[FailureCase] = Field(default_factory=list, description="실패 사례와 교훈")
    
    # 데이터 기반 분석
    market_data_summary: Optional[Dict[str, Any]] = Field(None, description="시장 데이터 요약")
