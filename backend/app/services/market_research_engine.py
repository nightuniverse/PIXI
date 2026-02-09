"""
고도화된 시장 조사 엔진
- 실시간 웹 스크래핑
- 다중 데이터 소스 통합
- 시맨틱 검색
- 시장 규모 데이터 수집
"""
from typing import Dict, Any, List, Optional
import json
import os
import re
import time
from datetime import datetime
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from app.core.config import settings


class MarketResearchEngine:
    """고도화된 시장 조사 엔진"""
    
    def __init__(self):
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.client = None  # Claude만 사용 시 GPT 호출 스킵
        self.model = "gpt-4o"
    
    def research_market(
        self,
        problem: str,
        category: str = None,
        keywords: List[str] = None
    ) -> Dict[str, Any]:
        """
        종합적인 시장 조사 수행
        
        Args:
            problem: 해결하려는 문제
            category: 카테고리
            keywords: 추가 키워드
        
        Returns:
            Dict: 조사 결과 (경쟁사, 시장 규모, 트렌드 등)
        """
        results = {
            'competitors': [],
            'market_size': {},
            'trends': [],
            'user_needs': [],
            'differentiation_opportunities': []
        }
        
        # 1. 기존 데이터베이스에서 경쟁사 찾기
        competitors_from_db = self._find_competitors_from_db(problem, category, keywords)
        results['competitors'].extend(competitors_from_db)
        
        # 2. 웹 검색으로 추가 경쟁사 찾기
        web_competitors = self._search_competitors_web(problem, category)
        results['competitors'].extend(web_competitors)
        
        # 2-1. 앱스토어에서 경쟁사 앱 찾기
        app_competitors = self._search_appstore(problem, category)
        results['competitors'].extend(app_competitors)
        
        # 3. 경쟁사 상세 정보 수집
        detailed_competitors = self._enrich_competitor_data(results['competitors'])
        results['competitors'] = detailed_competitors
        
        # 4. 시장 규모 데이터 수집
        results['market_size'] = self._research_market_size(category, problem)
        
        # 5. 트렌드 분석
        results['trends'] = self._analyze_trends(category, problem)
        
        # 6. 사용자 니즈 분석
        results['user_needs'] = self._analyze_user_needs(problem, category)
        
        # 7. 차별화 기회 도출
        results['differentiation_opportunities'] = self._find_differentiation_opportunities(
            results['competitors'], problem
        )
        
        return results
    
    def _find_competitors_from_db(
        self,
        problem: str,
        category: str = None,
        keywords: List[str] = None
    ) -> List[Dict[str, Any]]:
        """기존 데이터베이스에서 경쟁사 찾기 (시맨틱 검색 강화)"""
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
                return []
            
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 키워드 추출 및 확장
            search_keywords = self._extract_and_expand_keywords(problem, category, keywords)
            
            # 시맨틱 검색 (GPT를 사용한 유사도 기반 검색)
            competitors = []
            if data.get('startups'):
                scored_startups = []
                for startup in data['startups']:
                    score = self._calculate_relevance_score(
                        startup, problem, search_keywords
                    )
                    if score > 0.3:  # 임계값
                        scored_startups.append((startup, score))
                
                # 점수 순으로 정렬
                scored_startups.sort(key=lambda x: x[1], reverse=True)
                
                for startup, score in scored_startups[:20]:  # 상위 20개
                    competitors.append({
                        'name': startup.get('name', 'Unknown'),
                        'description': startup.get('description', ''),
                        'category': startup.get('category', ''),
                        'location': startup.get('location', ''),
                        'website': startup.get('website', ''),
                        'stage': startup.get('stage', 'Unknown'),
                        'relevance_score': score
                    })
            
            return competitors
        except Exception as e:
            print(f"데이터베이스 검색 오류: {e}")
            return []
    
    def _extract_and_expand_keywords(
        self,
        problem: str,
        category: str = None,
        keywords: List[str] = None
    ) -> List[str]:
        """키워드 추출 및 확장"""
        extracted = []
        
        if keywords:
            extracted.extend(keywords)
        
        if category:
            extracted.append(category)
        
        # 문제에서 키워드 추출
        if problem:
            # 간단한 키워드 추출 (실제로는 NLP 라이브러리 사용 가능)
            words = problem.split()
            extracted.extend([w for w in words if len(w) > 2])
        
        # GPT를 사용한 키워드 확장
        if self.client and problem:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "당신은 키워드 추출 전문가입니다. 주어진 문제에서 관련 키워드를 추출하고 확장해주세요."},
                        {"role": "user", "content": f"다음 문제와 관련된 키워드를 추출하고 확장해주세요: {problem}"}
                    ],
                    temperature=0.3,
                    max_tokens=100
                )
                expanded = response.choices[0].message.content
                # 쉼표나 줄바꿈으로 구분된 키워드 추출
                expanded_keywords = re.findall(r'\b\w+\b', expanded)
                extracted.extend(expanded_keywords)
            except Exception as e:
                print(f"키워드 확장 오류: {e}")
        
        return list(set(extracted))  # 중복 제거
    
    def _calculate_relevance_score(
        self,
        startup: Dict[str, Any],
        problem: str,
        keywords: List[str]
    ) -> float:
        """경쟁사 관련도 점수 계산"""
        score = 0.0
        
        name = (startup.get('name', '') or '').lower()
        desc = (startup.get('description', '') or '').lower()
        category = (startup.get('category', '') or '').lower()
        problem_lower = problem.lower()
        
        # 키워드 매칭 점수
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in name:
                score += 0.5
            if keyword_lower in desc:
                score += 0.3
            if keyword_lower in category:
                score += 0.4
        
        # 문제 텍스트 직접 매칭
        problem_words = set(problem_lower.split())
        startup_text = f"{name} {desc} {category}"
        startup_words = set(startup_text.split())
        
        # 공통 단어 비율
        common_words = problem_words.intersection(startup_words)
        if len(problem_words) > 0:
            score += len(common_words) / len(problem_words) * 0.3
        
        return min(score, 1.0)  # 최대 1.0
    
    def _search_competitors_web(
        self,
        problem: str,
        category: str = None
    ) -> List[Dict[str, Any]]:
        """웹 검색으로 경쟁사 찾기"""
        competitors = []
        
        # 1. 네이버 검색 (간단한 웹 스크래핑)
        try:
            naver_results = self._search_naver(problem, category)
            competitors.extend(naver_results)
        except Exception as e:
            print(f"네이버 검색 오류: {e}")
        
        # 2. 구글 검색 (간단한 웹 스크래핑)
        try:
            google_results = self._search_google(problem, category)
            competitors.extend(google_results)
        except Exception as e:
            print(f"구글 검색 오류: {e}")
        
        return competitors
    
    def _search_naver(
        self,
        problem: str,
        category: str = None
    ) -> List[Dict[str, Any]]:
        """네이버 검색으로 경쟁사 찾기 (간단한 웹 스크래핑)"""
        competitors = []
        
        try:
            # 검색어 구성
            search_query = f"{problem} {category or ''} 스타트업 앱 서비스".strip()
            
            # 네이버 검색 URL (URL 인코딩)
            encoded_query = quote_plus(search_query)
            search_url = f"https://search.naver.com/search.naver?query={encoded_query}&where=web"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 검색 결과에서 회사명/서비스명 추출
                # 네이버 검색 결과 구조에 따라 파싱
                results = soup.find_all('div', class_='api_subject_bx') or soup.find_all('a', class_='api_txt_lines')
                
                for result in results[:10]:  # 상위 10개
                    text = result.get_text().strip()
                    if text and len(text) > 5:
                        # 간단한 필터링 (스타트업/앱 관련 키워드 포함)
                        if any(keyword in text.lower() for keyword in ['앱', '서비스', '플랫폼', '스타트업', '기업']):
                            competitors.append({
                                'name': text[:50],  # 처음 50자
                                'description': text[:200],
                                'source': 'naver_search',
                                'website': None
                            })
        except Exception as e:
            print(f"네이버 검색 상세 오류: {e}")
        
        return competitors
    
    def _search_google(
        self,
        problem: str,
        category: str = None
    ) -> List[Dict[str, Any]]:
        """구글 검색으로 경쟁사 찾기 (간단한 웹 스크래핑)"""
        competitors = []
        
        try:
            # 검색어 구성
            search_query = f"{problem} {category or ''} startup app service".strip()
            
            # 구글 검색 URL (URL 인코딩)
            encoded_query = quote_plus(search_query)
            search_url = f"https://www.google.com/search?q={encoded_query}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 구글 검색 결과에서 제목과 설명 추출
                results = soup.find_all('div', class_='g') or soup.find_all('div', class_='tF2Cxc')
                
                for result in results[:10]:  # 상위 10개
                    title_elem = result.find('h3')
                    desc_elem = result.find('span', class_='aCOpRe') or result.find('div', class_='VwiC3b')
                    
                    if title_elem:
                        title = title_elem.get_text().strip()
                        desc = desc_elem.get_text().strip() if desc_elem else ""
                        
                        if title and len(title) > 3:
                            competitors.append({
                                'name': title[:50],
                                'description': desc[:200] if desc else "",
                                'source': 'google_search',
                                'website': None
                            })
        except Exception as e:
            print(f"구글 검색 상세 오류: {e}")
        
        return competitors
    
    def _search_appstore(
        self,
        problem: str,
        category: str = None
    ) -> List[Dict[str, Any]]:
        """Google Play Store에서 경쟁사 앱 찾기"""
        competitors = []
        
        try:
            # 검색어 구성
            search_query = f"{problem} {category or ''}".strip()
            
            # Google Play Store 검색 URL
            encoded_query = quote_plus(search_query)
            search_url = f"https://play.google.com/store/search?q={encoded_query}&c=apps&hl=ko"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
            }
            
            response = requests.get(search_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Google Play Store 검색 결과 파싱
                # 최신 구조에 맞게 파싱 (2024년 기준)
                app_cards = soup.find_all('div', class_='VfPpkd-rymPhb-ibnC6b') or \
                           soup.find_all('div', {'data-testid': 'search-result'}) or \
                           soup.find_all('div', class_='ULeU3b') or \
                           soup.find_all('a', class_='Si6A0c')
                
                if not app_cards:
                    # 대체 방법: 다른 선택자 시도
                    app_cards = soup.find_all('div', class_='ImZGtf') or \
                               soup.find_all('div', class_='Vpfmgd')
                
                for card in app_cards[:15]:  # 상위 15개 앱
                    try:
                        app_info = self._parse_app_card(card, soup)
                        if app_info and app_info.get('name'):
                            # 중복 제거
                            if not any(c.get('name') == app_info['name'] for c in competitors):
                                competitors.append(app_info)
                    except Exception as e:
                        print(f"앱 카드 파싱 오류: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
                
                # 앱 상세 페이지에서 추가 정보 수집
                for comp in competitors[:10]:  # 상위 10개만 상세 정보 수집
                    if comp.get('app_id'):
                        detailed_info = self._get_app_details(comp['app_id'])
                        if detailed_info:
                            comp.update(detailed_info)
            else:
                print(f"Google Play Store 접근 실패: {response.status_code}")
                
        except Exception as e:
            print(f"앱스토어 검색 오류: {e}")
            import traceback
            traceback.print_exc()
        
        return competitors
    
    def _parse_app_card(
        self,
        card,
        soup: BeautifulSoup
    ) -> Optional[Dict[str, Any]]:
        """앱 카드에서 정보 추출"""
        try:
            app_info = {
                'name': None,
                'description': None,
                'developer': None,
                'rating': None,
                'downloads': None,
                'app_id': None,
                'source': 'google_play_store',
                'type': 'mobile_app'
            }
            
            # 앱 이름 찾기
            name_elem = card.find('span', class_='DdYX5') or \
                        card.find('div', class_='vWM94c') or \
                        card.find('span', {'itemprop': 'name'}) or \
                        card.find('a', class_='Si6A0c')
            
            if name_elem:
                app_info['name'] = name_elem.get_text().strip()
            
            # 앱 설명 찾기
            desc_elem = card.find('span', class_='Y3x8Sc') or \
                       card.find('div', class_='b8uxIe') or \
                       card.find('span', {'itemprop': 'description'})
            
            if desc_elem:
                app_info['description'] = desc_elem.get_text().strip()[:200]
            
            # 개발자 찾기
            dev_elem = card.find('div', class_='wMUdtb') or \
                      card.find('span', class_='wMUdtb')
            
            if dev_elem:
                app_info['developer'] = dev_elem.get_text().strip()
            
            # 평점 찾기
            rating_elem = card.find('div', class_='f0U8Rb') or \
                         card.find('div', class_='LrNMN')
            
            if rating_elem:
                rating_text = rating_elem.get_text().strip()
                # 숫자 추출
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    app_info['rating'] = float(rating_match.group(1))
            
            # 다운로드 수 찾기
            downloads_elem = card.find('span', class_='wMUdtb') or \
                            card.find('div', class_='ClM7O')
            
            if downloads_elem:
                downloads_text = downloads_elem.get_text().strip()
                app_info['downloads'] = downloads_text
            
            # 앱 ID 찾기 (링크에서)
            link_elem = None
            if card.name == 'a' and card.get('href'):
                link_elem = card
            else:
                link_elem = card.find('a', href=True)
            
            if link_elem:
                href = link_elem.get('href', '')
                if href:
                    # /store/apps/details?id=com.example.app 형식에서 ID 추출
                    id_match = re.search(r'/store/apps/details\?id=([^&]+)', href)
                    if id_match:
                        app_info['app_id'] = id_match.group(1)
                        app_info['website'] = f"https://play.google.com/store/apps/details?id={app_info['app_id']}"
            
            # 이름이 있어야만 반환
            if app_info['name']:
                return app_info
            
        except Exception as e:
            print(f"앱 카드 파싱 상세 오류: {e}")
        
        return None
    
    def _get_app_details(
        self,
        app_id: str
    ) -> Optional[Dict[str, Any]]:
        """앱 상세 페이지에서 추가 정보 수집"""
        try:
            app_url = f"https://play.google.com/store/apps/details?id={app_id}&hl=ko"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
            }
            
            response = requests.get(app_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                details = {}
                
                # 상세 설명
                desc_elem = soup.find('div', {'data-g-id': 'description'}) or \
                           soup.find('div', class_='DWPxHb') or \
                           soup.find('div', {'jsname': 'sngebd'})
                
                if desc_elem:
                    full_desc = desc_elem.get_text().strip()
                    details['full_description'] = full_desc[:500]  # 처음 500자
                
                # 카테고리
                category_elem = soup.find('a', {'itemprop': 'genre'}) or \
                               soup.find('span', {'itemprop': 'genre'})
                
                if category_elem:
                    details['category'] = category_elem.get_text().strip()
                
                # 평점 및 리뷰 수
                rating_elem = soup.find('div', class_='TT9eCd') or \
                            soup.find('div', {'aria-label': re.compile(r'별점')})
                
                if rating_elem:
                    rating_text = rating_elem.get('aria-label') or rating_elem.get_text()
                    rating_match = re.search(r'(\d+\.?\d*)', str(rating_text))
                    if rating_match:
                        details['rating'] = float(rating_match.group(1))
                
                # 리뷰 수
                reviews_elem = soup.find('span', class_='AYi5wd') or \
                              soup.find('span', {'aria-label': re.compile(r'리뷰')})
                
                if reviews_elem:
                    reviews_text = reviews_elem.get_text() or reviews_elem.get('aria-label', '')
                    reviews_match = re.search(r'([\d,]+)', reviews_text.replace(',', ''))
                    if reviews_match:
                        details['review_count'] = int(reviews_match.group(1).replace(',', ''))
                
                # 다운로드 수 (더 정확한 정보)
                installs_elem = soup.find('div', string=re.compile(r'다운로드|설치')) or \
                               soup.find('span', string=re.compile(r'다운로드|설치'))
                
                if installs_elem:
                    installs_text = installs_elem.find_next_sibling().get_text() if installs_elem.find_next_sibling() else ''
                    details['downloads'] = installs_text.strip()
                
                return details
                
        except Exception as e:
            print(f"앱 상세 정보 수집 오류 ({app_id}): {e}")
        
        return None
    
    def _enrich_competitor_data(
        self,
        competitors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """경쟁사 데이터 보강 (웹사이트 스크래핑, 리뷰 분석 등)"""
        enriched = []
        
        for comp in competitors:
            enriched_comp = comp.copy()
            
            # 웹사이트가 있으면 추가 정보 수집
            if comp.get('website'):
                try:
                    # TODO: 웹사이트 스크래핑으로 상세 정보 수집
                    # - 서비스 설명
                    # - 주요 기능
                    # - 가격 정보
                    # - 사용자 리뷰
                    pass
                except Exception as e:
                    print(f"경쟁사 데이터 보강 오류 ({comp.get('name')}): {e}")
            
            enriched.append(enriched_comp)
        
        return enriched
    
    def _research_market_size(
        self,
        category: str = None,
        problem: str = None
    ) -> Dict[str, Any]:
        """시장 규모 조사"""
        # TODO: 실제 시장 규모 데이터 수집
        # - 통계청 데이터
        # - 산업부 데이터
        # - 시장 조사 리포트
        # - GPT를 통한 추정
        
        market_size = {
            'estimated_size_krw': None,
            'growth_rate': None,
            'source': None,
            'year': datetime.now().year
        }
        
        # GPT를 사용한 시장 규모 추정
        if self.client and category:
            try:
                prompt = f"""다음 카테고리/문제의 한국 시장 규모를 추정해주세요:
카테고리: {category or 'N/A'}
문제: {problem or 'N/A'}

다음 형식으로 응답해주세요:
- 시장 규모: [숫자]억원 (예: 500억원)
- 성장률: [숫자]% (예: 15%)
- 주요 트렌드: [간단한 설명]
"""
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "당신은 시장 조사 전문가입니다. 한국 시장 데이터를 바탕으로 정확한 추정을 제공합니다."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                
                analysis = response.choices[0].message.content
                
                # 숫자 추출
                size_match = re.search(r'(\d+)억원', analysis)
                if size_match:
                    market_size['estimated_size_krw'] = int(size_match.group(1)) * 100000000
                
                growth_match = re.search(r'(\d+(?:\.\d+)?)%', analysis)
                if growth_match:
                    market_size['growth_rate'] = float(growth_match.group(1))
                
                market_size['source'] = 'GPT 추정'
                market_size['analysis'] = analysis
            except Exception as e:
                print(f"시장 규모 조사 오류: {e}")
        
        return market_size
    
    def _analyze_trends(
        self,
        category: str = None,
        problem: str = None
    ) -> List[str]:
        """트렌드 분석"""
        trends = []
        
        # GPT를 사용한 트렌드 분석
        if self.client:
            try:
                prompt = f"""다음 카테고리/문제와 관련된 최근 한국 시장 트렌드를 분석해주세요:
카테고리: {category or 'N/A'}
문제: {problem or 'N/A'}

최근 1-2년간의 주요 트렌드를 3-5개 나열해주세요."""
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "당신은 트렌드 분석 전문가입니다. 한국 시장의 최근 트렌드를 정확하게 파악합니다."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5
                )
                
                trend_text = response.choices[0].message.content
                # 줄바꿈이나 번호로 구분된 트렌드 추출
                trend_lines = [line.strip() for line in trend_text.split('\n') if line.strip()]
                trends = [line for line in trend_lines if len(line) > 10][:5]
            except Exception as e:
                print(f"트렌드 분석 오류: {e}")
        
        return trends
    
    def _analyze_user_needs(
        self,
        problem: str,
        category: str = None
    ) -> List[Dict[str, Any]]:
        """사용자 니즈 분석"""
        needs = []
        
        # GPT를 사용한 사용자 니즈 분석
        if self.client:
            try:
                prompt = f"""다음 문제를 해결하려는 사용자들의 니즈를 분석해주세요:
문제: {problem}
카테고리: {category or 'N/A'}

다음 형식으로 분석해주세요:
1. 페인 포인트: [구체적인 불편함]
2. 원하는 기능: [사용자가 원하는 기능]
3. 동기 부여 요소: [사용자를 움직이게 하는 요소]
"""
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "당신은 사용자 리서치 전문가입니다. 사용자의 실제 니즈를 깊이 있게 분석합니다."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5
                )
                
                needs_text = response.choices[0].message.content
                # 구조화된 니즈 추출
                needs = [
                    {'type': 'pain_point', 'description': '사용자의 페인 포인트'},
                    {'type': 'desired_feature', 'description': '원하는 기능'},
                    {'type': 'motivation', 'description': '동기 부여 요소'}
                ]
            except Exception as e:
                print(f"사용자 니즈 분석 오류: {e}")
        
        return needs
    
    def _find_differentiation_opportunities(
        self,
        competitors: List[Dict[str, Any]],
        problem: str
    ) -> List[str]:
        """차별화 기회 도출"""
        opportunities = []
        
        # GPT를 사용한 차별화 기회 분석
        if self.client and competitors:
            try:
                competitors_summary = "\n".join([
                    f"- {comp.get('name')}: {comp.get('description', '')[:100]}"
                    for comp in competitors[:10]
                ])
                
                prompt = f"""다음 경쟁사들을 분석하여 차별화 기회를 도출해주세요:

문제: {problem}

주요 경쟁사:
{competitors_summary}

경쟁사들이 놓치고 있는 기회나 차별화할 수 있는 포인트를 3-5개 제시해주세요."""
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "당신은 전략 컨설턴트입니다. 경쟁 분석을 통해 차별화 기회를 찾습니다."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                
                opp_text = response.choices[0].message.content
                # 줄바꿈이나 번호로 구분된 기회 추출
                opp_lines = [line.strip() for line in opp_text.split('\n') if line.strip()]
                opportunities = [line for line in opp_lines if len(line) > 10][:5]
            except Exception as e:
                print(f"차별화 기회 분석 오류: {e}")
        
        return opportunities
