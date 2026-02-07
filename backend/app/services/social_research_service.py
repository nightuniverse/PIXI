"""
소셜 미디어 조사 서비스 - Reddit, 네이버 카페 등에서 실제 사용자 니즈 조사
"""
import praw
import requests
from typing import List, Dict, Any, Optional
from app.core.config import settings
import time

class SocialResearchService:
    """소셜 미디어 조사 서비스"""
    
    def __init__(self):
        # Reddit 설정 (선택사항)
        self.reddit_client = None
        if hasattr(settings, 'REDDIT_CLIENT_ID') and settings.REDDIT_CLIENT_ID:
            self.reddit_client = praw.Reddit(
                client_id=settings.REDDIT_CLIENT_ID,
                client_secret=settings.REDDIT_CLIENT_SECRET,
                user_agent="PIXI Startup Research Bot"
            )
        
        # 네이버 검색 API 설정
        self.naver_client_id = getattr(settings, 'NAVER_CLIENT_ID', None)
        self.naver_client_secret = getattr(settings, 'NAVER_CLIENT_SECRET', None)
    
    def search_reddit(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Reddit에서 검색
        
        Args:
            query: 검색어
            limit: 결과 개수
        
        Returns:
            List[Dict]: 검색 결과
        """
        if not self.reddit_client:
            return []
        
        try:
            results = []
            for submission in self.reddit_client.subreddit('all').search(query, limit=limit, sort='relevance'):
                results.append({
                    'title': submission.title,
                    'content': submission.selftext[:500] if submission.selftext else '',
                    'url': submission.url,
                    'score': submission.score,
                    'comments': submission.num_comments,
                    'subreddit': submission.subreddit.display_name,
                    'created_utc': submission.created_utc,
                    'source': 'reddit'
                })
            return results
        except Exception as e:
            print(f"Reddit 검색 오류: {e}")
            return []
    
    def search_naver_cafe(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        네이버 카페에서 검색 (검색 API 사용)
        
        Args:
            query: 검색어
            limit: 결과 개수
        
        Returns:
            List[Dict]: 검색 결과
        """
        if not self.naver_client_id or not self.naver_client_secret:
            return []
        
        try:
            url = "https://openapi.naver.com/v1/search/cafearticle.json"
            headers = {
                "X-Naver-Client-Id": self.naver_client_id,
                "X-Naver-Client-Secret": self.naver_client_secret
            }
            params = {
                "query": query,
                "display": min(limit, 100),  # 최대 100개
                "sort": "sim"  # 정확도순
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get('items', []):
                # HTML 태그 제거
                title = item.get('title', '').replace('<b>', '').replace('</b>', '')
                description = item.get('description', '').replace('<b>', '').replace('</b>', '')
                
                results.append({
                    'title': title,
                    'content': description,
                    'url': item.get('link', ''),
                    'cafe_name': item.get('cafename', ''),
                    'cafe_url': item.get('cafeurl', ''),
                    'source': 'naver_cafe'
                })
            
            return results
        except Exception as e:
            print(f"네이버 카페 검색 오류: {e}")
            return []
    
    def research_topic(self, topic: str, keywords: List[str] = None) -> Dict[str, Any]:
        """
        주제에 대한 종합 조사
        
        Args:
            topic: 조사 주제
            keywords: 추가 키워드 리스트
        
        Returns:
            Dict: 조사 결과 요약
        """
        if keywords is None:
            keywords = []
        
        all_keywords = [topic] + keywords
        all_results = []
        
        # Reddit 검색
        for keyword in all_keywords[:3]:  # 최대 3개 키워드만
            reddit_results = self.search_reddit(keyword, limit=5)
            all_results.extend(reddit_results)
            time.sleep(1)  # Rate limit 방지
        
        # 네이버 카페 검색
        for keyword in all_keywords[:3]:
            naver_results = self.search_naver_cafe(keyword, limit=5)
            all_results.extend(naver_results)
            time.sleep(0.5)  # Rate limit 방지
        
        # 결과 분석
        return {
            'total_results': len(all_results),
            'reddit_count': len([r for r in all_results if r.get('source') == 'reddit']),
            'naver_cafe_count': len([r for r in all_results if r.get('source') == 'naver_cafe']),
            'results': all_results[:20],  # 최대 20개만 반환
            'summary': self._analyze_results(all_results, topic)
        }
    
    def _analyze_results(self, results: List[Dict[str, Any]], topic: str) -> str:
        """결과 분석 및 요약"""
        if not results:
            return f"{topic}에 대한 소셜 미디어 검색 결과가 없습니다."
        
        # 주요 키워드 추출 (간단한 버전)
        common_words = {}
        for result in results:
            text = (result.get('title', '') + ' ' + result.get('content', '')).lower()
            # 간단한 키워드 추출 (실제로는 더 정교한 NLP 필요)
        
        return f"{topic}에 대해 총 {len(results)}개의 관련 게시글을 찾았습니다. Reddit과 네이버 카페에서 실제 사용자들의 니즈와 문제점을 확인할 수 있습니다."
