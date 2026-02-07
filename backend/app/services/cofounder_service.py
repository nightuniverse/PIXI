"""
AI 공동창업자 서비스 - 단계별 가이드 제공
"""
from typing import Dict, Any, List, Optional
import json
import os
import time
import re
from openai import OpenAI
from app.core.config import settings
from app.schemas.startup_advisor import StartupIdeaRequest
from app.services.market_research_engine import MarketResearchEngine
# 소셜 미디어 조사 기능은 제외됨
# from app.services.social_research_service import SocialResearchService

class CofounderService:
    """AI 공동창업자 서비스"""
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o"
        self.market_research_engine = MarketResearchEngine()
        # 소셜 미디어 조사 기능은 제외됨
        # self.social_research = SocialResearchService()
    
    def process_message(
        self,
        message: str,
        current_phase: str,
        project_state: Dict[str, Any],
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        사용자 메시지를 처리하고 AI 응답을 생성합니다.
        
        Args:
            message: 사용자 메시지
            current_phase: 현재 단계 ('idea', 'research', 'solution', 'mvp', 'launch')
            project_state: 프로젝트 상태
            conversation_history: 대화 기록
        
        Returns:
            Dict: 응답, 다음 단계, 프로젝트 상태 업데이트
        """
        
        # 실제 시장 데이터 가져오기 및 분석 (조사 단계에서만)
        analyzed_documents = []
        market_data = None
        if current_phase == 'research' and project_state.get('problem'):
            try:
                # 고도화된 시장 조사 엔진 사용
                research_keywords = ['경쟁사', '시장', '조사', '분석', '비교', '경쟁', '시장 규모', '경쟁사 분석', '시장 조사', '조사해', '분석해', '경쟁사 찾아', '시장 찾아']
                message_lower = message.lower()
                
                if any(keyword in message_lower for keyword in research_keywords):
                    print("고도화된 시장 조사 엔진 실행 중...")
                    # 고도화된 조사 엔진으로 종합 조사 수행
                    research_results = self.market_research_engine.research_market(
                        problem=project_state.get('problem', ''),
                        category=project_state.get('category'),
                        keywords=project_state.get('keywords', [])
                    )
                    
                    print(f"조사 결과: 경쟁사 {len(research_results.get('competitors', []))}개, 시장 규모: {research_results.get('market_size', {})}")
                    
                    # 조사 결과를 문서로 변환
                    analyzed_doc = self._create_research_document(research_results, project_state)
                    if analyzed_doc:
                        analyzed_documents.append(analyzed_doc)
                        print(f"✅ 고도화된 조사 완료: 문서 생성됨 - {analyzed_doc.get('title')} (체크리스트 {len(analyzed_doc.get('checklist', []))}개)")
                    else:
                        print("⚠️ 문서 생성 실패")
                    
                    # 기존 방식도 백업으로 사용
                    market_data = self._get_market_data(project_state)
                else:
                    # 일반적인 경우 기존 방식 사용
                    market_data = self._get_market_data(project_state)
            except Exception as e:
                print(f"시장 데이터 조회 오류: {e}")
                import traceback
                traceback.print_exc()
                # 오류 발생 시 기존 방식으로 폴백
                try:
                    market_data = self._get_market_data(project_state)
                except:
                    pass
        
        system_prompt = self._build_system_prompt(current_phase, project_state)
        
        user_prompt = self._build_user_prompt(
            message, current_phase, project_state, conversation_history, market_data
        )
        
        # GPT 호출
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            
            if not response.choices or not response.choices[0].message:
                raise ValueError("GPT 응답이 비어있습니다.")
            
            ai_response = response.choices[0].message.content
            
            if not ai_response:
                raise ValueError("GPT 응답 내용이 없습니다.")
        except Exception as e:
            error_msg = f"OpenAI API 호출 실패: {str(e)}"
            print(f"ERROR: {error_msg}")
            raise Exception(error_msg)
        
        # 응답 파싱 (JSON 형식으로 구조화된 정보가 포함될 수 있음)
        try:
            parsed = self._parse_response(ai_response, current_phase, project_state)
        except Exception as e:
            print(f"WARNING: 응답 파싱 오류 (응답은 그대로 반환): {e}")
            # 파싱 실패해도 응답은 반환
            parsed = {
                "response": ai_response,
                "next_phase": current_phase,
                "project_state": {},
                "actions": []
            }
        
        # 프로젝트 상태 초기화
        result = {
            "response": parsed["response"],
            "next_phase": parsed.get("next_phase"),
            "project_state": parsed.get("project_state", {}),
            "actions": parsed.get("actions", [])
        }
        
        # 분석된 문서 추가 (시장 데이터 분석에서 생성된 경우)
        if analyzed_documents:
            if "documents" not in result["project_state"]:
                result["project_state"]["documents"] = []
            # 중복 제거
            existing_ids = {doc.get('id') for doc in result["project_state"]["documents"] if doc.get('id')}
            existing_titles = {doc.get('title') for doc in result["project_state"]["documents"] if doc.get('title')}
            for doc in analyzed_documents:
                # ID와 제목 모두 확인하여 중복 제거
                if doc.get('id') not in existing_ids and doc.get('title') not in existing_titles:
                    result["project_state"]["documents"].append(doc)
                    print(f"문서 추가됨: {doc.get('title')} (ID: {doc.get('id')})")
        
        # 디버깅: 문서가 있는지 확인
        if result["project_state"].get("documents"):
            print(f"반환되는 문서 수: {len(result['project_state']['documents'])}")
            for doc in result["project_state"]["documents"]:
                print(f"  - {doc.get('title')} (ID: {doc.get('id')})")
        
        # 응답에서 추가 문서 추출 (AI가 응답에서 문서를 생성한 경우)
        documents = []
        if current_phase == 'research':
            # 경쟁사 분석이나 시장 조사 관련 키워드가 있으면 문서 생성
            research_keywords = ['경쟁사', '시장', '조사', '분석', '비교', '경쟁', '시장 규모']
            if any(keyword in ai_response for keyword in research_keywords):
                # 문서 추출 시도
                doc_hint = self._extract_document_hint(ai_response)
                if doc_hint:
                    documents.append(doc_hint)
        
        # 문서가 있으면 project_state에 추가
        if documents:
            if "documents" not in result["project_state"]:
                result["project_state"]["documents"] = []
            # 중복 제거
            existing_titles = {doc.get('title') for doc in result["project_state"]["documents"]}
            for doc in documents:
                if doc.get('title') not in existing_titles:
                    result["project_state"]["documents"].append(doc)
        
        return result
    
    def _build_system_prompt(self, current_phase: str, project_state: Dict[str, Any]) -> str:
        """시스템 프롬프트 구성"""
        
        phase_instructions = {
            'idea': """당신은 아이디어 단계를 이끄는 AI 공동창업자입니다.
- 사용자가 문제를 발견하도록 도와주세요
- 아이디어가 없으면 문제 중심으로 브레인스토밍을 도와주세요
- 구체적인 문제를 찾도록 질문하세요
- "사용자 경험 개선" 같은 추상적 표현을 피하고, 구체적인 페인 포인트를 찾도록 하세요
- 한국 시장의 실제 문제를 다루도록 하세요
- 문제가 명확해지면 조사 단계로 넘어갑니다
- 사용자의 아이디어나 문제를 프로젝트 상태에 저장하세요 (JSON 형식: {"project_state": {"idea": "...", "problem": "..."}})""",
            
            'research': """당신은 조사 단계를 이끄는 AI 공동창업자입니다.

**절대 금지 사항:**
- "조사 방법을 안내하겠습니다" 같은 표현 금지
- "제가 조사해드릴 수는 없지만" 같은 표현 금지
- "조사하시면" 같은 조건문 사용 금지
- 사용자에게 조사를 요청하는 것 금지

**반드시 수행해야 할 것:**
- 제공된 경쟁사 데이터를 **직접 분석**하여 구체적인 결과를 제시하세요
- 각 경쟁사의 서비스, 강점, 약점을 **실제 데이터 기반으로** 분석하세요
- 시장 규모, 경쟁사 수, 성장률 등을 **구체적인 숫자와 함께** 제시하세요
- "조사했습니다" 또는 "분석했습니다"라는 과거형으로 응답하세요

**문서 형태로 정리:**
- 경쟁사 분석이나 시장 조사를 수행할 때는 반드시 문서 형태로 정리해주세요
- 체크리스트 형식으로 **완료된 작업**을 제시하세요:
  * "[경쟁사명] 분석 완료: [구체적인 분석 내용]"
  * "시장 규모 조사 완료: [구체적인 숫자와 데이터]"
  * "차별화 포인트 도출 완료: [구체적인 기회 포인트]"
- 문서 제목은 "경쟁사 분석 및 시장 조사" 등으로 명확하게 제시하세요
- 각 분석 항목을 체크리스트 형태로 정리하여 사용자가 진행 상황을 추적할 수 있도록 하세요

**응답 예시 (올바른 방식):**
"제공된 경쟁사 데이터를 분석한 결과입니다. [구체적인 분석 내용]"

**응답 예시 (잘못된 방식 - 절대 사용 금지):**
"조사 방법을 안내하겠습니다" / "제가 조사해드릴 수는 없지만" / "조사하시면"

- 검증이 완료되면 솔루션 단계로 넘어갑니다""",
            
            'solution': """당신은 솔루션 단계를 이끄는 AI 공동창업자입니다.
- 발견된 문제에 대한 최적의 솔루션을 설계하도록 도와주세요
- 기능을 우선순위화하세요 (Must-have, Should-have, Nice-to-have)
- 비즈니스 모델을 구체적으로 제안하세요
- 기술 스택과 구현 방법을 논의하세요
- 솔루션이 명확해지면 MVP 단계로 넘어갑니다""",
            
            'mvp': """당신은 MVP 단계를 이끄는 AI 공동창업자입니다.
- 최소 기능 제품의 범위를 명확히 하세요
- 개발 우선순위를 정하세요
- 첫 100명 사용자 확보 전략을 논의하세요
- MVP 성공 지표를 설정하세요
- MVP 계획이 완성되면 런칭 단계로 넘어갑니다""",
            
            'launch': """당신은 런칭 단계를 이끄는 AI 공동창업자입니다.
- 런칭 전 체크리스트를 확인하세요
- 마케팅 전략을 구체적으로 제안하세요
- 초기 사용자 확보 방법을 논의하세요
- 성장 전략을 수립하세요
- 프로젝트를 완료합니다"""
        }
        
        return f"""당신은 한국 창업자를 위한 AI 공동창업자입니다. Y Combinator의 파트너 수준의 전문성을 가지고 있으며, 실제 창업자가 필요로 하는 구체적이고 실행 가능한 조언을 제공합니다.

현재 단계: {current_phase}

{phase_instructions.get(current_phase, '')}

프로젝트 상태:
{json.dumps(project_state, ensure_ascii=False, indent=2)}

당신의 역할:
1. **대화를 주도**: 사용자가 다음에 무엇을 해야 할지 명확하게 안내하세요
2. **구체적 질문**: 추상적 질문이 아닌, 실행 가능한 답변을 이끌어내는 질문을 하세요
3. **한국 시장 특화**: 한국의 정부 정책, 규제, 시장 특성을 고려하세요
4. **실제 데이터 요구**: "시장이 좋아 보인다"가 아닌, 구체적인 숫자와 데이터를 요구하세요
5. **단계별 진행**: 각 단계가 완료되면 자연스럽게 다음 단계로 넘어가도록 하세요

응답 형식:
- 자연스러운 대화 형식으로 응답하세요
- 필요시 JSON 형식으로 구조화된 정보를 포함할 수 있습니다 (예: {{"next_phase": "research", "project_state": {{"problem": "..."}}}})
- 사용자에게 구체적인 다음 액션을 제시하세요"""
    
    def _build_user_prompt(
        self,
        message: str,
        current_phase: str,
        project_state: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        market_data: Dict[str, Any] = None
    ) -> str:
        """사용자 프롬프트 구성"""
        
        history_text = ""
        if conversation_history:
            history_text = "\n\n## 대화 기록\n"
            for msg in conversation_history[-5:]:  # 최근 5개만
                # ChatMessage는 Pydantic 모델이므로 속성으로 접근
                role = msg.role if hasattr(msg, 'role') else msg.get('role', 'user')
                content = msg.content if hasattr(msg, 'content') else msg.get('content', '')
                history_text += f"{role}: {content}\n"
        
        market_data_text = ""
        if market_data and market_data.get('competitors'):
            market_data_text = "\n\n## 한국 시장 데이터 (기존 스타트업 생태계)\n"
            market_data_text += f"관련 카테고리: {', '.join(market_data.get('categories', []))}\n"
            market_data_text += f"경쟁사 수: {len(market_data.get('competitors', []))}개\n\n"
            market_data_text += "주요 경쟁사:\n"
            for i, comp in enumerate(market_data.get('competitors', [])[:10], 1):
                market_data_text += f"{i}. {comp.get('name', 'Unknown')}\n"
                if comp.get('description'):
                    market_data_text += f"   설명: {comp.get('description', '')[:150]}...\n"
                if comp.get('location'):
                    market_data_text += f"   위치: {comp.get('location', '')}\n"
                if comp.get('stage'):
                    market_data_text += f"   단계: {comp.get('stage', '')}\n"
                market_data_text += "\n"
            market_data_text += "\n**중요: 이 시장 데이터를 바탕으로 실제로 분석하고 문서 형태로 정리해주세요:**\n"
            market_data_text += "**절대 금지: \"조사 방법을 안내하겠습니다\" 같은 표현 사용 금지. 실제로 분석한 결과를 제시하세요.**\n"
            market_data_text += "1. 각 경쟁사를 실제로 분석하여 상세 분석 제시 (서비스, 강점, 약점, 타겟 고객)\n"
            market_data_text += "2. 시장 기회를 실제로 분석하여 제시 (경쟁사들이 놓치고 있는 부분)\n"
            market_data_text += "3. 차별화 포인트 도출\n"
            market_data_text += "4. 시장 진입 전략\n\n"
            market_data_text += "**반드시 체크리스트 형식으로 문서를 생성해주세요.** 예시:\n"
            market_data_text += "제목: 경쟁사 분석\n"
            market_data_text += "섹션: 초기 조사\n"
            market_data_text += "- 경쟁사 A 분석 완료\n"
            market_data_text += "- 경쟁사 B 분석 완료\n"
            market_data_text += "- 시장 기회 도출 완료"
        
        return f"""사용자 메시지: {message}

{history_text}
{market_data_text}

현재 프로젝트 상태를 업데이트하고, 다음 단계로 진행할 준비가 되었는지 판단해주세요.
사용자에게 자연스럽고 구체적인 응답을 제공하고, 필요시 다음 단계로 넘어가도록 안내해주세요."""
    
    def _parse_response(
        self,
        ai_response: str,
        current_phase: str,
        project_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """AI 응답을 파싱하여 구조화된 정보 추출"""
        
        result = {
            "response": ai_response,
            "next_phase": current_phase,
            "project_state": {},
            "actions": []
        }
        
        # JSON 형식의 정보가 포함되어 있는지 확인
        try:
            import re
            # 더 포괄적인 JSON 패턴 찾기 (중첩 객체 지원)
            json_patterns = [
                r'\{[^{}]*(?:"next_phase"|"project_state")[^{}]*\}',  # 간단한 패턴
                r'\{.*?"next_phase".*?\}',  # next_phase 포함
                r'\{.*?"project_state".*?\}',  # project_state 포함
                r'```json\s*(\{.*?\})\s*```',  # 코드 블록 내 JSON
                r'```\s*(\{.*?\})\s*```',  # 코드 블록 내 JSON (json 없이)
            ]
            
            for pattern in json_patterns:
                json_match = re.search(pattern, ai_response, re.DOTALL | re.IGNORECASE)
                if json_match:
                    json_str = json_match.group(1) if json_match.lastindex else json_match.group()
                    try:
                        parsed_json = json.loads(json_str)
                        if "next_phase" in parsed_json:
                            result["next_phase"] = parsed_json.get("next_phase", current_phase)
                        if "project_state" in parsed_json:
                            result["project_state"] = parsed_json.get("project_state", {})
                        if "actions" in parsed_json:
                            result["actions"] = parsed_json.get("actions", [])
                        # JSON 부분을 응답에서 제거
                        result["response"] = ai_response.replace(json_match.group(), "").strip()
                        break
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"JSON 파싱 오류: {e}")
            pass
        
        # 단계 전환 로직 (프로젝트 상태 기반)
        if current_phase == 'idea' and project_state.get('problem'):
            # 문제가 명확해지면 조사 단계로
            if len(project_state.get('problem', '')) > 50:
                result["next_phase"] = "research"
        
        elif current_phase == 'research' and project_state.get('validated'):
            # 검증이 완료되면 솔루션 단계로
            result["next_phase"] = "solution"
        
        elif current_phase == 'solution' and project_state.get('solution'):
            # 솔루션이 명확해지면 MVP 단계로
            if len(project_state.get('solution', '')) > 50:
                result["next_phase"] = "mvp"
        
        elif current_phase == 'mvp' and project_state.get('mvp_plan'):
            # MVP 계획이 완성되면 런칭 단계로
            result["next_phase"] = "launch"
        
        return result
    
    def _get_market_data(self, project_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        프로젝트 상태를 기반으로 관련 시장 데이터를 가져옵니다.
        
        Args:
            project_state: 프로젝트 상태 (idea, problem 등 포함)
        
        Returns:
            Dict: 시장 데이터 (경쟁사, 카테고리 등)
        """
        try:
            # 데이터 파일 경로 찾기
            possible_paths = [
                os.path.join(os.path.dirname(__file__), '../../../../frontend/public/data/koreanEcosystemData.json'),
                os.path.join(os.path.dirname(__file__), '../../../../data/korean_ecosystem_data_latest.json'),
                os.path.join(os.path.dirname(__file__), '../../../../data-pipeline/data/korean_ecosystem_data_latest.json'),
            ]
            
            data_file = None
            for path in possible_paths:
                if os.path.exists(path):
                    data_file = path
                    break
            
            if not data_file:
                return None
            
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 키워드 추출 (idea, problem에서)
            keywords = []
            if project_state.get('idea'):
                keywords.extend(project_state['idea'].split()[:5])
            if project_state.get('problem'):
                keywords.extend(project_state['problem'].split()[:5])
            
            # 관련 스타트업 찾기
            competitors = []
            if data.get('startups'):
                for startup in data['startups']:
                    # 키워드 매칭 (이름, 설명, 카테고리)
                    name = (startup.get('name', '') or '').lower()
                    desc = (startup.get('description', '') or '').lower()
                    category = (startup.get('category', '') or '').lower()
                    
                    # 키워드가 포함되어 있으면 경쟁사로 간주
                    for keyword in keywords:
                        if keyword.lower() in name or keyword.lower() in desc or keyword.lower() in category:
                            competitors.append({
                                'name': startup.get('name', 'Unknown'),
                                'description': startup.get('description', ''),
                                'category': startup.get('category', ''),
                                'location': startup.get('location', ''),
                                'website': startup.get('website', ''),
                                'stage': startup.get('stage', 'Unknown')
                            })
                            break
            
            # 카테고리 추출
            categories = list(set([c.get('category', '') for c in competitors if c.get('category')]))
            
            return {
                'competitors': competitors[:20],  # 최대 20개
                'categories': categories,
                'total_competitors': len(competitors)
            }
        except Exception as e:
            print(f"시장 데이터 로드 오류: {e}")
            return None
    
    def _analyze_market_data(self, market_data: Dict[str, Any], project_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        시장 데이터를 실제로 분석하여 문서를 생성합니다.
        
        Args:
            market_data: 시장 데이터 (경쟁사, 카테고리 등)
            project_state: 프로젝트 상태
        
        Returns:
            Dict: 분석된 문서 정보
        """
        try:
            competitors = market_data.get('competitors', [])
            if not competitors:
                return None
            
            # GPT를 사용하여 실제 분석 수행
            # 경쟁사 정보를 텍스트로 정리
            competitors_text = ""
            for i, comp in enumerate(competitors[:10], 1):
                competitors_text += f"\n{i}. {comp.get('name', 'Unknown')}\n"
                if comp.get('description'):
                    competitors_text += f"   설명: {comp.get('description', '')}\n"
                if comp.get('category'):
                    competitors_text += f"   카테고리: {comp.get('category', '')}\n"
                if comp.get('location'):
                    competitors_text += f"   위치: {comp.get('location', '')}\n"
                if comp.get('stage'):
                    competitors_text += f"   단계: {comp.get('stage', '')}\n"
                if comp.get('website'):
                    competitors_text += f"   웹사이트: {comp.get('website', '')}\n"
            
            analysis_prompt = f"""**중요: 제공된 경쟁사 데이터를 직접 분석하여 구체적인 결과를 제시하세요.**

**절대 금지:**
- "조사 방법을 안내하겠습니다" 같은 표현 사용 금지
- "제가 조사해드릴 수는 없지만" 같은 표현 사용 금지
- 사용자에게 조사를 요청하는 것 금지
- 추상적이고 일반적인 표현 사용 금지

**반드시 수행:**
- 제공된 경쟁사 데이터를 **직접 분석**하여 구체적인 결과를 제시하세요
- 각 경쟁사의 서비스, 강점, 약점을 **실제 데이터 기반으로** 분석하세요
- "분석 완료" 또는 "조사 완료"라는 과거형으로 작성하세요

프로젝트 문제: {project_state.get('problem', '알 수 없음')}
관련 카테고리: {', '.join(market_data.get('categories', []))}
총 경쟁사 수: {len(competitors)}개

주요 경쟁사 정보:
{competitors_text}

**위 경쟁사 데이터를 바탕으로 실제로 분석한 결과를 다음 형식으로 제시하세요:**

제목: 경쟁사 분석 및 시장 조사
섹션: 초기 조사

체크리스트:
- [경쟁사명] 분석 완료: [제공된 데이터를 바탕으로 구체적으로 작성 - 주요 서비스, 강점, 약점, 타겟 고객]
- [경쟁사명] 분석 완료: [제공된 데이터를 바탕으로 구체적으로 작성 - 주요 서비스, 강점, 약점, 타겟 고객]
- [경쟁사명] 분석 완료: [제공된 데이터를 바탕으로 구체적으로 작성 - 주요 서비스, 강점, 약점, 타겟 고객]
- 시장 규모 조사 완료: [한국 시장 기준으로 실제 시장 규모 추정치, 성장률, 주요 트렌드]
- 경쟁사 수 조사 완료: 총 {len(competitors)}개 경쟁사 확인, 주요 플레이어 {min(5, len(competitors))}개
- 차별화 포인트 도출 완료: [경쟁사들이 놓치고 있는 기회, 우리가 차별화할 수 있는 구체적인 포인트]
- 사용자 니즈 조사 완료: [페인 포인트, 동기 부여 요소, 사용자가 원하는 기능]

**각 항목을 구체적으로 작성하세요:**
- 경쟁사명은 실제 데이터에서 가져온 이름을 사용하세요
- 각 경쟁사의 설명, 카테고리, 위치, 단계 정보를 바탕으로 구체적으로 분석하세요
- 추상적인 표현("좋은 서비스", "다양한 기능") 대신 구체적인 정보를 제공하세요
- 시장 규모는 한국 시장 기준으로 추정치를 제시하세요"""

            analysis_response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": """당신은 시장 조사 전문가입니다. 

**절대 금지:**
- "조사 방법을 안내하겠습니다" 같은 표현 사용 금지
- "제가 조사해드릴 수는 없지만" 같은 표현 사용 금지
- 사용자에게 조사를 요청하는 것 금지

**반드시 수행:**
- 제공된 데이터를 직접 분석하여 구체적인 결과를 제시하세요
- "분석 완료" 또는 "조사 완료"라는 과거형으로 작성하세요
- 추상적인 표현 대신 구체적인 정보를 제공하세요"""},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.7
            )
            
            analysis_text = analysis_response.choices[0].message.content
            
            # 분석 결과에서 문서 추출
            doc_hint = self._extract_document_hint(analysis_text)
            if doc_hint:
                # 실제 분석 내용을 content에 포함
                return {
                    'id': f'doc_{int(time.time() * 1000)}',
                    'title': doc_hint.get('title', '경쟁사 분석 및 시장 조사'),
                    'section': doc_hint.get('section', '초기 조사'),
                    'checklist': doc_hint.get('checklist', []),
                    'content': analysis_text,  # 전체 분석 내용 포함
                    'x': 50,
                    'y': 50
                }
            
            return None
        except Exception as e:
            print(f"시장 데이터 분석 오류: {e}")
            return None
    
    def _create_research_document(
        self,
        research_results: Dict[str, Any],
        project_state: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        고도화된 조사 결과를 문서 형태로 변환
        
        Args:
            research_results: 시장 조사 엔진의 결과
            project_state: 프로젝트 상태
        
        Returns:
            Dict: 문서 카드 데이터
        """
        try:
            competitors = research_results.get('competitors', [])
            market_size = research_results.get('market_size', {})
            trends = research_results.get('trends', [])
            user_needs = research_results.get('user_needs', [])
            opportunities = research_results.get('differentiation_opportunities', [])
            
            # 체크리스트 생성
            checklist = []
            
            # 경쟁사 분석 항목
            for comp in competitors[:5]:  # 상위 5개
                comp_name = comp.get('name', 'Unknown')
                comp_desc = comp.get('description', '')[:50]
                checklist.append({
                    'id': f'comp_{comp.get("name", "").lower().replace(" ", "_")}',
                    'text': f'{comp_name} 분석 완료: {comp_desc}...',
                    'checked': True
                })
            
            # 시장 규모 조사
            if market_size.get('estimated_size_krw'):
                size_billion = market_size['estimated_size_krw'] / 100000000
                growth = market_size.get('growth_rate', 'N/A')
                checklist.append({
                    'id': 'market_size',
                    'text': f'시장 규모 조사 완료: 약 {size_billion:.0f}억원, 성장률 {growth}%',
                    'checked': True
                })
            
            # 경쟁사 수
            if competitors:
                checklist.append({
                    'id': 'competitor_count',
                    'text': f'경쟁사 수 조사 완료: 총 {len(competitors)}개 경쟁사 확인',
                    'checked': True
                })
            
            # 트렌드
            if trends:
                checklist.append({
                    'id': 'trends',
                    'text': f'시장 트렌드 분석 완료: {len(trends)}개 주요 트렌드 확인',
                    'checked': True
                })
            
            # 차별화 포인트
            if opportunities:
                checklist.append({
                    'id': 'differentiation',
                    'text': f'차별화 포인트 도출 완료: {len(opportunities)}개 기회 확인',
                    'checked': True
                })
            
            # 사용자 니즈
            if user_needs:
                checklist.append({
                    'id': 'user_needs',
                    'text': f'사용자 니즈 조사 완료: 페인 포인트 및 니즈 분석 완료',
                    'checked': True
                })
            
            # 상세 내용 생성
            content_parts = []
            
            if competitors:
                content_parts.append("## 주요 경쟁사 분석\n")
                for comp in competitors[:5]:
                    content_parts.append(f"### {comp.get('name')}")
                    if comp.get('description'):
                        content_parts.append(f"- 설명: {comp.get('description')}")
                    if comp.get('category'):
                        content_parts.append(f"- 카테고리: {comp.get('category')}")
                    if comp.get('website'):
                        content_parts.append(f"- 웹사이트: {comp.get('website')}")
                    content_parts.append("")
            
            if market_size.get('estimated_size_krw'):
                content_parts.append("## 시장 규모\n")
                size_billion = market_size['estimated_size_krw'] / 100000000
                content_parts.append(f"- 추정 시장 규모: 약 {size_billion:.0f}억원")
                if market_size.get('growth_rate'):
                    content_parts.append(f"- 성장률: {market_size['growth_rate']}%")
                if market_size.get('analysis'):
                    content_parts.append(f"\n{market_size['analysis']}")
                content_parts.append("")
            
            if trends:
                content_parts.append("## 시장 트렌드\n")
                for i, trend in enumerate(trends[:5], 1):
                    content_parts.append(f"{i}. {trend}")
                content_parts.append("")
            
            if opportunities:
                content_parts.append("## 차별화 기회\n")
                for i, opp in enumerate(opportunities[:5], 1):
                    content_parts.append(f"{i}. {opp}")
                content_parts.append("")
            
            content = "\n".join(content_parts)
            
            return {
                'id': f'doc_{int(time.time() * 1000)}',
                'title': '경쟁사 분석 및 시장 조사',
                'section': '초기 조사',
                'checklist': checklist,
                'content': content,
                'x': 50,
                'y': 50
            }
        except Exception as e:
            print(f"문서 생성 오류: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_document_hint(self, response: str) -> Optional[Dict[str, Any]]:
        """
        AI 응답에서 문서 생성 힌트를 추출합니다.
        
        Args:
            response: AI 응답 텍스트
        
        Returns:
            Dict: 문서 정보 (title, section, checklist)
        """
        # 문서 제목 찾기
        title_patterns = [
            r'(?:제목|문서|계획|분석)[\s:]*\n?([^\n]+)',
            r'##\s*([^\n]+)',
            r'#\s*([^\n]+)',
        ]
        
        title = None
        for pattern in title_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                # 일반적인 마크다운 제목 제거
                if title.startswith('#'):
                    title = title.lstrip('#').strip()
                break
        
        # 섹션 찾기
        section_patterns = [
            r'(?:섹션|단계|영역|카테고리)[\s:]*\n?([^\n]+)',
            r'###\s*([^\n]+)',
        ]
        
        section = None
        for pattern in section_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                section = match.group(1).strip()
                if section.startswith('#'):
                    section = section.lstrip('#').strip()
                break
        
        # 체크리스트 항목 찾기
        checklist_patterns = [
            r'(?:[-•*]\s*)([^\n]+)',
            r'(?:\d+[\.\)]\s*)([^\n]+)',
            r'(?:□|☐|✓|✔|☑)\s*([^\n]+)',
        ]
        
        checklist = []
        for pattern in checklist_patterns:
            matches = re.findall(pattern, response)
            if matches:
                checklist = [
                    {
                        'id': f'item_{i}',
                        'text': item.strip(),
                        'checked': False
                    }
                    for i, item in enumerate(matches[:10])  # 최대 10개
                ]
                break
        
        # 경쟁사 분석이나 시장 조사 관련 키워드가 있으면 문서 생성
        research_keywords = ['경쟁사', '시장', '조사', '분석', '비교']
        has_research_content = any(keyword in response for keyword in research_keywords)
        
        # 문서 생성 조건
        if has_research_content and (title or checklist or section):
            return {
                'id': f'doc_{int(time.time() * 1000)}',
                'title': title or ('경쟁사 분석' if '경쟁사' in response else '시장 조사'),
                'section': section or '초기 조사',
                'checklist': checklist if checklist else [
                    {'id': 'item_1', 'text': '경쟁사 데이터 수집', 'checked': False},
                    {'id': 'item_2', 'text': '시장 규모 분석', 'checked': False},
                    {'id': 'item_3', 'text': '차별화 포인트 도출', 'checked': False}
                ],
                'x': 50,
                'y': 50
            }
        
        return None
