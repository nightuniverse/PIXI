"""
창업 아이템 분석 서비스 - GPT-4o를 활용한 고도화된 분석
"""
from typing import Dict, Any, List
import json
from openai import OpenAI
from app.core.config import settings
from app.schemas.startup_advisor import (
    StartupAnalysisResponse,
    BusinessModel,
    MarketOpportunity,
    CompetitiveAdvantage,
    RiskAnalysis,
    ActionPlan,
    TargetCustomer,
    CompetitorAnalysis,
    KoreanMarketSpecifics,
    InvestmentPerspective,
    FailureCase,
    RevenueStream
)

class StartupAdvisorService:
    """창업 아이템 분석 서비스"""
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o"
    
    def analyze_startup_idea(
        self,
        category: str,
        idea_description: str = "",
        market_data: Dict[str, Any] = None
    ) -> StartupAnalysisResponse:
        """
        창업 아이템을 종합적으로 분석합니다.
        
        Args:
            category: 카테고리
            idea_description: 아이디어 설명
            market_data: 시장 데이터 (회사 수, 경쟁사 등)
        
        Returns:
            StartupAnalysisResponse: 분석 결과
        """
        
        # 프롬프트 구성
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(category, idea_description, market_data)
        
        # GPT 호출
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        # 응답 파싱
        result = json.loads(response.choices[0].message.content)
        
        # 응답 객체 생성
        return self._parse_response(result, market_data)
    
    def _build_system_prompt(self) -> str:
        """시스템 프롬프트 구성"""
        return """당신은 한국 스타트업 생태계를 깊이 이해한 창업 전문가입니다. Y Combinator, Techstars 같은 글로벌 액셀러레이터의 파트너 수준의 인사이트를 제공해야 합니다.

당신의 역할:
1. **실제 데이터 기반 분석**: 제공된 경쟁사 데이터를 깊이 분석하고, 각 경쟁사의 강점/약점을 구체적으로 파악
2. **한국 시장 특화**: 한국의 정부 정책, 규제 환경, 시장 특성, 투자 트렌드를 반영한 현실적인 조언
3. **구체적인 숫자와 메트릭**: CAC, LTV, 시장 규모, 성장률 등 실제 비즈니스 메트릭 제시
4. **실행 가능한 액션**: "사용자 경험 개선" 같은 추상적 조언이 아닌, "첫 100명 고객 확보를 위한 콜드 이메일 템플릿 작성" 같은 구체적 액션
5. **투자자 관점**: 실제 VC가 보는 관점에서 아이디어의 투자 가능성과 밸류에이션 제시
6. **실패 사례 학습**: 유사한 아이디어로 실패한 사례와 그 이유, 교훈 제시

금지 사항:
- "사용자 경험 개선", "차별화 전략", "시장 진입" 같은 일반적인 조언
- "높음/중간/낮음" 같은 모호한 표현 (구체적 숫자나 비율 사용)
- ChatGPT가 자주 하는 일반적인 창업 조언

필수 포함 사항:
- 실제 경쟁사와의 구체적 비교 (각 경쟁사의 강점/약점)
- 한국 정부 정책/규제 정보 (해당 분야)
- 구체적인 숫자 (시장 규모, 예상 매출, CAC, LTV 등)
- 실제 실행 가능한 첫 3개월 액션 플랜
- 투자자 관점에서의 밸류에이션과 투자 가능성"""
    
    def _build_user_prompt(
        self,
        category: str,
        idea_description: str,
        market_data: Dict[str, Any]
    ) -> str:
        """사용자 프롬프트 구성"""
        
        # 경쟁사 상세 정보 구성
        competitors_detail = ""
        if market_data and market_data.get('competitors'):
            competitors_detail = "\n## 주요 경쟁사 상세 정보\n"
            for idx, comp in enumerate(market_data.get('competitors', [])[:5], 1):
                competitors_detail += f"""
{idx}. **{comp.get('name', 'N/A')}**
   - 설명: {comp.get('description', '정보 없음')[:200]}
   - 위치: {comp.get('location', 'N/A')}
   - 웹사이트: {comp.get('website', 'N/A')}
"""
        
        market_info = ""
        if market_data:
            market_info = f"""
## 시장 현황 데이터
- 전체 회사 수: {market_data.get('total_companies', 'N/A')}개
- 지역 분포: {', '.join([f'{k}({v}개)' for k, v in list(market_data.get('locations', {}).items())[:5]])}
{competitors_detail}
"""
        
        return f"""당신은 한국 스타트업 생태계의 베테랑 창업가이자 투자자입니다. 다음 아이디어를 실제 창업자가 필요로 하는 수준으로 깊이 있게 분석해주세요.

## 분석 대상 아이템

**카테고리**: {category}

**아이디어 설명**: 
{idea_description if idea_description else '사용자가 구체적인 아이디어를 제공하지 않았습니다. 카테고리 기반으로 분석하되, 실제 창업자가 고려해야 할 구체적인 사항들을 제시해주세요.'}

{market_info}

## 분석 요청사항

위 경쟁사 데이터를 바탕으로 다음을 분석해주세요:

1. **각 경쟁사의 강점과 약점**을 구체적으로 파악하고, 그들이 놓치고 있는 기회는 무엇인지
2. **한국 시장 특성**: 해당 분야의 한국 정부 정책, 규제, 시장 특성 (예: 개인정보보호법, 전자상거래법 등)
3. **구체적인 숫자**: 예상 시장 규모(억원 단위), 첫 해 목표 매출, CAC, LTV 등
4. **실제 실행 가능한 첫 3개월 액션**: "사용자 경험 개선"이 아닌 "카카오톡 오픈채팅방 10개에 매일 3회씩 프로덕트 소개" 같은 구체적 액션
5. **투자자 관점**: 이 아이디어가 투자를 받을 수 있는지, 예상 밸류에이션, 필요한 자금 규모

다음 JSON 형식으로 응답해주세요:

## 카테고리
{category}

## 아이디어 설명
{idea_description if idea_description else '사용자가 구체적인 아이디어를 제공하지 않았습니다. 카테고리 기반으로 일반적인 분석을 제공해주세요.'}
{market_info}

## 분석 요청사항

다음 JSON 형식으로 응답해주세요:

{{
  "idea_summary": "아이디어를 한 문장으로 요약 (구체적으로)",
  "market_analysis": "시장 상황을 구체적인 숫자와 함께 분석. 예: '한국 SaaS 시장은 2024년 기준 약 2조원 규모이며, 연평균 15% 성장 중. 특히 중소기업 대상 SaaS는 전체의 40%를 차지하며 가장 빠르게 성장하는 세그먼트'",
  "target_customers": [
    {{
      "segment": "구체적인 타겟 세그먼트 (예: 직원 10-50명 규모의 온라인 쇼핑몰 운영 중소기업)",
      "size": "예상 고객 수 (예: 약 5만개 사업체)",
      "pain_points": ["구체적인 페인 포인트 1", "구체적인 페인 포인트 2"],
      "willingness_to_pay": "예상 지불 의향 (예: 월 5-10만원)"
    }}
  ],
  "competitor_analysis": [
    {{
      "competitor_name": "경쟁사 이름",
      "strengths": ["구체적 강점 1", "구체적 강점 2"],
      "weaknesses": ["구체적 약점 1 (예: 가격이 월 30만원으로 높음)", "구체적 약점 2"],
      "market_position": "시장 포지션 (예: 프리미엄 시장 점유율 30%)",
      "opportunity_gap": "이 경쟁사가 놓치고 있는 기회"
    }}
  ],
  "business_models": [
    {{
      "model_type": "모델 유형",
      "description": "왜 이 모델인지 구체적 설명",
      "revenue_streams": [
        {{
          "stream": "수익원 이름",
          "description": "구체적 설명",
          "expected_revenue": "예상 수익 (예: 첫 해 월 500만원)"
        }}
      ],
      "pricing_strategy": "구체적 가격 전략 (예: 기본 플랜 월 9.9만원, 프로 플랜 월 19.9만원, 엔터프라이즈 연 500만원)",
      "unit_economics": "단위 경제성 (예: CAC 5만원, LTV 120만원, LTV/CAC 비율 24:1)"
    }}
  ],
  "recommended_model": {{
    "model_type": "추천 모델",
    "reason": "왜 이 모델을 추천하는지 구체적 이유",
    "revenue_streams": ["수익원 1", "수익원 2"],
    "pricing_strategy": "구체적 가격",
    "first_year_revenue_target": "첫 해 목표 매출 (예: 1억원)",
    "break_even_timeline": "손익분기점 달성 시기 (예: 18개월)"
  }},
  "korean_market_specifics": {{
    "government_policies": "관련 정부 정책 (예: 중소벤처기업부의 스타트업 지원 프로그램)",
    "regulations": "주의해야 할 규제 (예: 개인정보보호법, 전자상거래법)",
    "market_characteristics": "한국 시장 특성 (예: 빠른 채택 속도, 높은 모바일 사용률)",
    "investment_trends": "투자 트렌드 (예: 해당 분야 최근 투자 사례)"
  }},
  "opportunities": [
    {{
      "opportunity": "구체적 기회 설명",
      "market_size": "시장 규모 (예: 2024년 기준 약 500억원, 연 20% 성장)",
      "growth_potential": "성장 잠재력과 이유 (예: 높음 - 정부의 디지털 전환 정책으로 중소기업 SaaS 수요 급증)",
      "entry_barriers": ["구체적 진입 장벽 1", "구체적 진입 장벽 2"],
      "time_window": "기회의 시간적 윈도우 (예: 향후 2-3년 내)"
    }}
  ],
  "competitive_advantages": [
    {{
      "advantage": "구체적 경쟁 우위 (예: AI 기반 자동화로 경쟁사 대비 설정 시간 90% 단축)",
      "sustainability": "지속 가능성과 이유",
      "moat_strength": "weak/medium/strong",
      "defensibility": "방어 가능성 설명 (예: 데이터 축적으로 시간이 갈수록 강해지는 네트워크 효과)"
    }}
  ],
  "risks": [
    {{
      "risk": "구체적 리스크 (예: 대기업 무료 서비스 출시로 가격 경쟁 심화)",
      "probability": "low/medium/high",
      "impact": "low/medium/high",
      "mitigation": "구체적 완화 방안 (예: 초기 고객과 장기 계약 체결로 이탈 방지)",
      "contingency_plan": "대비 계획"
    }}
  ],
  "action_plan": [
    {{
      "phase": "첫 3개월 (MVP 검증)",
      "timeline": "구체적 타임라인",
      "key_actions": [
        "구체적 액션 1 (예: 카카오톡 오픈채팅방 10개에 매일 프로덕트 소개)",
        "구체적 액션 2 (예: Product Hunt 출시 준비 및 런칭)",
        "구체적 액션 3 (예: 첫 10명 고객과 1:1 인터뷰 진행)"
      ],
      "success_metrics": ["구체적 지표 1 (예: 첫 3개월 내 50명 유료 고객 확보)", "구체적 지표 2"],
      "budget": "필요 예산 (예: 약 500만원)"
    }},
    {{
      "phase": "4-6개월 (시장 진입)",
      "timeline": "구체적 타임라인",
      "key_actions": ["구체적 액션들"],
      "success_metrics": ["구체적 지표들"],
      "budget": "필요 예산"
    }}
  ],
  "investment_perspective": {{
    "investability": "투자 가능성 (high/medium/low)",
    "valuation_estimate": "예상 밸류에이션 (예: 시드 라운드 기준 10-15억원)",
    "funding_needs": "필요 자금 규모 (예: 시드 라운드 3억원)",
    "investor_fit": "적합한 투자자 유형 (예: B2B SaaS 전문 VC)",
    "key_metrics_for_investors": "투자자가 보는 핵심 지표 (예: MRR, Churn Rate, CAC Payback Period)"
  }},
  "key_insights": [
    "실제 창업자가 알아야 할 핵심 인사이트 1 (구체적으로)",
    "핵심 인사이트 2",
    "핵심 인사이트 3"
  ],
  "next_steps": [
    "즉시 실행 가능한 다음 단계 1 (예: 경쟁사 웹사이트 5개 분석하고 각각의 가격 정책 정리)",
    "즉시 실행 가능한 다음 단계 2",
    "즉시 실행 가능한 다음 단계 3"
  ],
  "failure_cases": [
    {{
      "case": "유사 아이디어로 실패한 사례",
      "failure_reason": "실패 이유",
      "lesson": "교훈"
    }}
  ]
}}

**중요 지침:**
1. 모든 내용은 구체적이고 실행 가능해야 함
2. "높음/중간/낮음" 같은 모호한 표현 금지 → 구체적 숫자나 비율 사용
3. "사용자 경험 개선" 같은 추상적 조언 금지 → "카카오톡 오픈채팅방에 매일 3회 프로덕트 소개" 같은 구체적 액션
4. 실제 경쟁사 데이터를 바탕으로 각 경쟁사의 강점/약점을 구체적으로 분석
5. 한국 시장 특성 (정부 정책, 규제, 투자 트렌드) 반드시 포함
6. 투자자 관점에서의 분석 포함 (밸류에이션, 투자 가능성 등)
7. 실패 사례와 교훈 포함"""
    
    def _parse_response(
        self,
        result: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> StartupAnalysisResponse:
        """GPT 응답을 파싱하여 StartupAnalysisResponse 객체 생성"""
        
        # TargetCustomer 파싱 (기존 문자열 리스트 또는 새로운 객체 리스트 모두 처리)
        target_customers_raw = result.get("target_customers", [])
        target_customers = []
        for tc in target_customers_raw:
            if isinstance(tc, str):
                # 기존 형식: 문자열 리스트
                target_customers.append(TargetCustomer(
                    segment=tc,
                    size=None,
                    pain_points=[],
                    willingness_to_pay=None
                ))
            else:
                # 새로운 형식: 객체
                target_customers.append(TargetCustomer(**tc))
        
        # CompetitorAnalysis 파싱
        competitor_analysis = [
            CompetitorAnalysis(**comp) for comp in result.get("competitor_analysis", [])
        ]
        
        # BusinessModel 파싱 (revenue_streams 처리)
        business_models = []
        for bm in result.get("business_models", []):
            revenue_streams_raw = bm.get("revenue_streams", [])
            revenue_streams = []
            for rs in revenue_streams_raw:
                if isinstance(rs, str):
                    revenue_streams.append(RevenueStream(stream=rs, description="", expected_revenue=None))
                else:
                    revenue_streams.append(RevenueStream(**rs))
            bm["revenue_streams"] = revenue_streams
            business_models.append(BusinessModel(**bm))
        
        # RecommendedModel 파싱
        rec_model_raw = result.get("recommended_model", {})
        rec_revenue_streams_raw = rec_model_raw.get("revenue_streams", [])
        rec_revenue_streams = []
        for rs in rec_revenue_streams_raw:
            if isinstance(rs, str):
                rec_revenue_streams.append(RevenueStream(stream=rs, description="", expected_revenue=None))
            else:
                rec_revenue_streams.append(RevenueStream(**rs))
        rec_model_raw["revenue_streams"] = rec_revenue_streams
        recommended_model = BusinessModel(**rec_model_raw)
        
        # KoreanMarketSpecifics 파싱
        korean_market = None
        if result.get("korean_market_specifics"):
            korean_market = KoreanMarketSpecifics(**result.get("korean_market_specifics", {}))
        
        # MarketOpportunity 파싱
        opportunities = [
            MarketOpportunity(**opp) for opp in result.get("opportunities", [])
        ]
        
        # CompetitiveAdvantage 파싱
        competitive_advantages = [
            CompetitiveAdvantage(**adv) for adv in result.get("competitive_advantages", [])
        ]
        
        # RiskAnalysis 파싱
        risks = [
            RiskAnalysis(**risk) for risk in result.get("risks", [])
        ]
        
        # ActionPlan 파싱
        action_plan = [
            ActionPlan(**plan) for plan in result.get("action_plan", [])
        ]
        
        # InvestmentPerspective 파싱
        investment_perspective = None
        if result.get("investment_perspective"):
            investment_perspective = InvestmentPerspective(**result.get("investment_perspective", {}))
        
        # FailureCase 파싱
        failure_cases = [
            FailureCase(**fc) for fc in result.get("failure_cases", [])
        ]
        
        return StartupAnalysisResponse(
            idea_summary=result.get("idea_summary", ""),
            market_analysis=result.get("market_analysis", ""),
            target_customers=target_customers,
            competitor_analysis=competitor_analysis,
            business_models=business_models,
            recommended_model=recommended_model,
            korean_market_specifics=korean_market,
            opportunities=opportunities,
            competitive_advantages=competitive_advantages,
            risks=risks,
            action_plan=action_plan,
            investment_perspective=investment_perspective,
            key_insights=result.get("key_insights", []),
            next_steps=result.get("next_steps", []),
            failure_cases=failure_cases,
            market_data_summary=market_data
        )
