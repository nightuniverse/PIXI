#!/usr/bin/env python3
"""
개선된 스타트업 생태계 크롤러
더 안정적이고 실제로 작동하는 크롤링을 제공합니다.
"""

import asyncio
import json
import logging
import time
import random
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse, quote
import re

import aiohttp
import pandas as pd
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('improved_ecosystem_crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ImprovedEcosystemCrawler:
    def __init__(self):
        self.session = None
        self.browser = None
        self.page = None
        self.ecosystem_data = {
            'startups': [],
            'investors': [],
            'accelerators': [],
            'coworking_spaces': [],
            'events': [],
            'crawled_at': datetime.now().isoformat()
        }
        
        # User-Agent 목록
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # 크롤링 설정
        self.delay_range = (3, 6)
        self.max_retries = 3
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox', 
                '--disable-dev-shm-usage', 
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        self.page = await self.browser.new_page()
        
        # User-Agent 설정
        await self.page.set_extra_http_headers({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def random_delay(self, min_delay=None, max_delay=None):
        """랜덤 지연으로 차단 방지"""
        if min_delay is None:
            min_delay = self.delay_range[0]
        if max_delay is None:
            max_delay = self.delay_range[1]
        
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)
    
    async def crawl_github_startups(self, max_results: int = 50) -> List[Dict]:
        """GitHub에서 스타트업 관련 저장소 크롤링"""
        logger.info("GitHub 스타트업 저장소 크롤링 시작")
        startups = []
        
        # GitHub 트렌딩 저장소 검색
        search_queries = [
            "startup",
            "ai startup", 
            "fintech",
            "healthtech",
            "edtech"
        ]
        
        for query in search_queries:
            try:
                logger.info(f"GitHub '{query}' 검색 중...")
                
                search_url = f"https://github.com/search?q={quote(query)}&type=repositories&s=stars&o=desc"
                await self.page.goto(search_url, wait_until='networkidle')
                await self.random_delay()
                
                # 저장소 목록 대기
                try:
                    await self.page.wait_for_selector('.repo-list-item', timeout=15000)
                except:
                    logger.warning(f"'{query}' 검색 결과를 찾을 수 없습니다")
                    continue
                
                repo_items = await self.page.query_selector_all('.repo-list-item')
                
                for i, item in enumerate(repo_items[:max_results//len(search_queries)]):
                    try:
                        # 저장소명
                        name_elem = await item.query_selector('a[data-hydro-click]')
                        name = await name_elem.text_content() if name_elem else "Unknown"
                        
                        # 설명
                        desc_elem = await item.query_selector('p')
                        description = await desc_elem.text_content() if desc_elem else ""
                        
                        # 언어
                        lang_elem = await item.query_selector('[itemprop="programmingLanguage"]')
                        language = await lang_elem.text_content() if lang_elem else ""
                        
                        # 스타 수
                        stars_elem = await item.query_selector('a[href*="/stargazers"]')
                        stars = await stars_elem.text_content() if stars_elem else "0"
                        
                        # 링크
                        link_elem = await item.query_selector('a[data-hydro-click]')
                        link = await link_elem.get_attribute('href') if link_elem else ""
                        
                        startup_data = {
                            'name': name.strip(),
                            'description': description.strip()[:500],
                            'language': language.strip(),
                            'stars': stars.strip(),
                            'website': f"https://github.com{link}" if link.startswith('/') else link,
                            'category': query,
                            'source': 'GitHub',
                            'type': 'startup',
                            'crawled_at': datetime.now().isoformat()
                        }
                        
                        startups.append(startup_data)
                        logger.info(f"GitHub 크롤링: {name[:50]}... ({stars} stars)")
                        
                    except Exception as e:
                        logger.error(f"저장소 크롤링 실패: {e}")
                        continue
                
                await self.random_delay(2, 4)
                
            except Exception as e:
                logger.error(f"GitHub '{query}' 크롤링 실패: {e}")
                continue
        
        logger.info(f"GitHub 크롤링 완료: {len(startups)}개 저장소")
        return startups
    
    async def crawl_product_hunt(self, max_results: int = 30) -> List[Dict]:
        """Product Hunt에서 스타트업 제품 정보 크롤링"""
        logger.info("Product Hunt 스타트업 제품 크롤링 시작")
        startups = []
        
        try:
            # Product Hunt 홈페이지
            url = "https://www.producthunt.com/"
            await self.page.goto(url, wait_until='networkidle')
            await self.random_delay()
            
            # 제품 카드 대기
            try:
                await self.page.wait_for_selector('[data-test="post-item"]', timeout=15000)
            except:
                logger.warning("Product Hunt 제품을 찾을 수 없습니다")
                return startups
            
            product_items = await self.page.query_selector_all('[data-test="post-item"]')
            
            for i, item in enumerate(product_items[:max_results]):
                try:
                    # 제품명
                    name_elem = await item.query_selector('h3, [data-test="post-name"]')
                    name = await name_elem.text_content() if name_elem else "Unknown"
                    
                    # 설명
                    desc_elem = await item.query_selector('p, [data-test="post-tagline"]')
                    description = await desc_elem.text_content() if desc_elem else ""
                    
                    # 카테고리
                    category_elem = await item.query_selector('[data-test="post-topic"]')
                    category = await category_elem.text_content() if category_elem else ""
                    
                    # 링크
                    link_elem = await item.query_selector('a')
                    link = await link_elem.get_attribute('href') if link_elem else ""
                    
                    startup_data = {
                        'name': name.strip(),
                        'description': description.strip()[:500],
                        'category': category.strip(),
                        'website': link if link.startswith('http') else f"https://www.producthunt.com{link}",
                        'source': 'Product Hunt',
                        'type': 'startup',
                        'crawled_at': datetime.now().isoformat()
                    }
                    
                    startups.append(startup_data)
                    logger.info(f"Product Hunt 크롤링: {name[:50]}...")
                    
                except Exception as e:
                    logger.error(f"제품 크롤링 실패: {e}")
                    continue
                
        except Exception as e:
            logger.error(f"Product Hunt 크롤링 실패: {e}")
        
        logger.info(f"Product Hunt 크롤링 완료: {len(startups)}개 제품")
        return startups
    
    async def crawl_medium_startups(self, max_pages: int = 3) -> List[Dict]:
        """Medium에서 스타트업 관련 글 크롤링"""
        logger.info("Medium 스타트업 글 크롤링 시작")
        startups = []
        
        # Medium 스타트업 태그 검색
        search_queries = [
            "startup",
            "entrepreneurship",
            "venture-capital",
            "tech-startup"
        ]
        
        for query in search_queries:
            try:
                logger.info(f"Medium '{query}' 검색 중...")
                
                search_url = f"https://medium.com/tag/{query}"
                await self.page.goto(search_url, wait_until='networkidle')
                await self.random_delay()
                
                # 글 목록 대기
                try:
                    await self.page.wait_for_selector('article', timeout=15000)
                except:
                    logger.warning(f"'{query}' 검색 결과를 찾을 수 없습니다")
                    continue
                
                articles = await self.page.query_selector_all('article')
                
                for i, article in enumerate(articles[:max_results//len(search_queries)]):
                    try:
                        # 제목
                        title_elem = await article.query_selector('h2, h3')
                        title = await title_elem.text_content() if title_elem else "No Title"
                        
                        # 요약
                        excerpt_elem = await article.query_selector('p')
                        excerpt = await excerpt_elem.text_content() if excerpt_elem else ""
                        
                        # 작성자
                        author_elem = await article.query_selector('[data-testid="authorName"]')
                        author = await author_elem.text_content() if author_elem else ""
                        
                        # 링크
                        link_elem = await article.query_selector('a')
                        link = await link_elem.get_attribute('href') if link_elem else ""
                        
                        startup_data = {
                            'name': title.strip()[:100],
                            'description': excerpt.strip()[:500],
                            'author': author.strip(),
                            'website': link if link.startswith('http') else f"https://medium.com{link}",
                            'category': query,
                            'source': 'Medium',
                            'type': 'startup',
                            'crawled_at': datetime.now().isoformat()
                        }
                        
                        startups.append(startup_data)
                        logger.info(f"Medium 크롤링: {title[:50]}...")
                        
                    except Exception as e:
                        logger.error(f"글 크롤링 실패: {e}")
                        continue
                
                await self.random_delay(2, 4)
                
            except Exception as e:
                logger.error(f"Medium '{query}' 크롤링 실패: {e}")
                continue
        
        logger.info(f"Medium 크롤링 완료: {len(startups)}개 글")
        return startups
    
    async def crawl_manual_startup_data(self) -> List[Dict]:
        """수동으로 수집한 주요 스타트업 데이터"""
        logger.info("수동 스타트업 데이터 수집 시작")
        
        manual_startups = [
            {
                "name": "OpenAI",
                "description": "AI 연구 및 개발 기업, ChatGPT 개발사",
                "location": "San Francisco, CA",
                "industry": "Artificial Intelligence",
                "founded": "2015",
                "funding": "Series Unknown",
                "website": "https://openai.com",
                "source": "Manual Data"
            },
            {
                "name": "Stripe",
                "description": "온라인 결제 처리 플랫폼",
                "location": "San Francisco, CA",
                "industry": "Fintech",
                "founded": "2010",
                "funding": "Series Unknown",
                "website": "https://stripe.com",
                "source": "Manual Data"
            },
            {
                "name": "Notion",
                "description": "협업 및 생산성 도구",
                "location": "San Francisco, CA",
                "industry": "Productivity",
                "founded": "2013",
                "funding": "Series Unknown",
                "website": "https://notion.so",
                "source": "Manual Data"
            },
            {
                "name": "Figma",
                "description": "협업 디자인 도구",
                "location": "San Francisco, CA",
                "industry": "Design",
                "founded": "2012",
                "funding": "Series Unknown",
                "website": "https://figma.com",
                "source": "Manual Data"
            },
            {
                "name": "Canva",
                "description": "온라인 디자인 플랫폼",
                "location": "Sydney, Australia",
                "industry": "Design",
                "founded": "2012",
                "funding": "Series Unknown",
                "website": "https://canva.com",
                "source": "Manual Data"
            }
        ]
        
        for startup in manual_startups:
            startup['type'] = 'startup'
            startup['crawled_at'] = datetime.now().isoformat()
        
        logger.info(f"수동 스타트업 데이터 수집 완료: {len(manual_startups)}개")
        return manual_startups
    
    async def crawl_manual_investor_data(self) -> List[Dict]:
        """수동으로 수집한 주요 투자자 데이터"""
        logger.info("수동 투자자 데이터 수집 시작")
        
        manual_investors = [
            {
                "name": "Sequoia Capital",
                "description": "실리콘밸리의 대표적인 벤처캐피탈",
                "location": "Menlo Park, CA",
                "focus": "Technology, Healthcare, Consumer",
                "website": "https://www.sequoiacap.com",
                "source": "Manual Data"
            },
            {
                "name": "Andreessen Horowitz",
                "description": "기술 중심의 벤처캐피탈",
                "location": "Menlo Park, CA",
                "focus": "Software, Internet, Mobile",
                "website": "https://a16z.com",
                "source": "Manual Data"
            },
            {
                "name": "Y Combinator",
                "description": "스타트업 액셀러레이터",
                "location": "Mountain View, CA",
                "focus": "Early-stage startups",
                "website": "https://www.ycombinator.com",
                "source": "Manual Data"
            }
        ]
        
        for investor in manual_investors:
            investor['type'] = 'investor'
            investor['crawled_at'] = datetime.now().isoformat()
        
        logger.info(f"수동 투자자 데이터 수집 완료: {len(manual_investors)}개")
        return manual_investors
    
    async def crawl_all_improved_sources(self) -> Dict[str, Any]:
        """모든 개선된 소스에서 데이터 크롤링"""
        logger.info("개선된 생태계 데이터 크롤링 시작")
        
        # 1. GitHub 스타트업 저장소
        github_startups = await self.crawl_github_startups()
        self.ecosystem_data['startups'].extend(github_startups)
        
        # 2. Product Hunt 제품
        product_hunt_startups = await self.crawl_product_hunt()
        self.ecosystem_data['startups'].extend(product_hunt_startups)
        
        # 3. Medium 스타트업 글
        medium_startups = await self.crawl_medium_startups()
        self.ecosystem_data['startups'].extend(medium_startups)
        
        # 4. 수동 스타트업 데이터
        manual_startups = await self.crawl_manual_startup_data()
        self.ecosystem_data['startups'].extend(manual_startups)
        
        # 5. 수동 투자자 데이터
        manual_investors = await self.crawl_manual_investor_data()
        self.ecosystem_data['investors'].extend(manual_investors)
        
        # 중복 제거
        self._remove_duplicates()
        
        # 통계 정보 추가
        self._add_statistics()
        
        logger.info("개선된 생태계 데이터 크롤링 완료")
        return self.ecosystem_data
    
    def _remove_duplicates(self):
        """중복 데이터 제거"""
        logger.info("중복 데이터 제거 중...")
        
        # 회사명 기반 중복 제거
        seen_names = set()
        unique_startups = []
        
        for startup in self.ecosystem_data['startups']:
            name_normalized = startup['name'].lower().strip()
            if name_normalized not in seen_names:
                seen_names.add(name_normalized)
                unique_startups.append(startup)
        
        self.ecosystem_data['startups'] = unique_startups
        
        logger.info(f"중복 제거 후 스타트업 수: {len(unique_startups)}")
    
    def _add_statistics(self):
        """통계 정보 추가"""
        stats = {
            'total_startups': len(self.ecosystem_data['startups']),
            'total_investors': len(self.ecosystem_data['investors']),
            'total_accelerators': len(self.ecosystem_data['accelerators']),
            'total_coworking_spaces': len(self.ecosystem_data['coworking_spaces']),
            'total_events': len(self.ecosystem_data['events']),
            'total_entities': sum([
                len(self.ecosystem_data['startups']),
                len(self.ecosystem_data['investors']),
                len(self.ecosystem_data['accelerators']),
                len(self.ecosystem_data['coworking_spaces']),
                len(self.ecosystem_data['events'])
            ])
        }
        
        self.ecosystem_data['statistics'] = stats
        logger.info(f"통계 정보 추가 완료: 총 {stats['total_entities']}개 엔티티")
    
    def save_data(self, filename: str = None):
        """데이터를 파일로 저장"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"improved_ecosystem_data_{timestamp}.json"
        
        filepath = f"data/{filename}"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.ecosystem_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"데이터 저장 완료: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"데이터 저장 실패: {e}")
            return None

async def main():
    """메인 함수"""
    logger.info("🚀 개선된 스타트업 생태계 탐색 크롤러 시작")
    
    async with ImprovedEcosystemCrawler() as crawler:
        try:
            # 전체 개선된 소스에서 데이터 크롤링
            ecosystem_data = await crawler.crawl_all_improved_sources()
            
            # 데이터 저장
            filename = crawler.save_data()
            
            if filename:
                logger.info(f"✅ 개선된 크롤링 완료! 데이터 저장됨: {filename}")
                
                # 결과 요약 출력
                stats = ecosystem_data.get('statistics', {})
                logger.info(f"📊 개선된 크롤링 결과 요약:")
                logger.info(f"   - 스타트업: {stats.get('total_startups', 0)}개")
                logger.info(f"   - 투자자: {stats.get('total_investors', 0)}개")
                logger.info(f"   - 액셀러레이터: {stats.get('total_accelerators', 0)}개")
                logger.info(f"   - 코워킹 스페이스: {stats.get('total_coworking_spaces', 0)}개")
                logger.info(f"   - 이벤트: {stats.get('total_events', 0)}개")
                logger.info(f"   - 총 엔티티: {stats.get('total_entities', 0)}개")
            else:
                logger.error("❌ 데이터 저장 실패")
                
        except Exception as e:
            logger.error(f"크롤링 중 오류 발생: {e}")

if __name__ == "__main__":
    asyncio.run(main())
