#!/usr/bin/env python3
"""
스타트업 생태계 종합 탐색 크롤러
여러 소스에서 스타트업, 투자자, 액셀러레이터, 코워킹 스페이스 등의 정보를 수집합니다.
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
        logging.FileHandler('ecosystem_crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EcosystemCrawler:
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
        self.delay_range = (2, 5)  # 요청 간 지연 시간 (초)
        self.max_retries = 3
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-blink-features=AutomationControlled']
        )
        self.page = await self.browser.new_page()
        
        # User-Agent 설정
        await self.page.set_extra_http_headers({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
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
    
    async def crawl_techcrunch_startups(self, max_pages: int = 5) -> List[Dict]:
        """TechCrunch에서 스타트업 뉴스 및 정보 크롤링"""
        logger.info("TechCrunch 스타트업 정보 크롤링 시작")
        startups = []
        
        try:
            for page in range(1, max_pages + 1):
                url = f"https://techcrunch.com/category/startups/page/{page}/"
                logger.info(f"페이지 {page} 크롤링: {url}")
                
                await self.page.goto(url, wait_until='networkidle')
                await self.random_delay()
                
                # 기사 목록 대기
                try:
                    await self.page.wait_for_selector('article', timeout=10000)
                except:
                    logger.warning(f"페이지 {page}에서 기사를 찾을 수 없습니다")
                    break
                
                articles = await self.page.query_selector_all('article')
                
                for article in articles:
                    try:
                        # 제목
                        title_elem = await article.query_selector('h2, h3')
                        title = await title_elem.text_content() if title_elem else "No Title"
                        
                        # 링크
                        link_elem = await article.query_selector('a')
                        link = await link_elem.get_attribute('href') if link_elem else ""
                        
                        # 요약
                        excerpt_elem = await article.query_selector('p, div[class*="excerpt"]')
                        excerpt = await excerpt_elem.text_content() if excerpt_elem else ""
                        
                        # 카테고리/태그
                        category_elem = await article.query_selector('[class*="category"], [class*="tag"]')
                        category = await category_elem.text_content() if category_elem else ""
                        
                        startup_data = {
                            'name': title.strip()[:100],
                            'description': excerpt.strip()[:500],
                            'website': link if link.startswith('http') else f"https://techcrunch.com{link}",
                            'category': category.strip(),
                            'source': 'TechCrunch',
                            'type': 'startup',
                            'crawled_at': datetime.now().isoformat()
                        }
                        
                        startups.append(startup_data)
                        logger.info(f"TechCrunch 크롤링: {title[:50]}...")
                        
                    except Exception as e:
                        logger.error(f"기사 크롤링 실패: {e}")
                        continue
                
                await self.random_delay(3, 6)  # 페이지 간 더 긴 지연
                
        except Exception as e:
            logger.error(f"TechCrunch 크롤링 실패: {e}")
        
        logger.info(f"TechCrunch 크롤링 완료: {len(startups)}개 스타트업")
        return startups
    
    async def crawl_angel_list(self, search_queries: List[str] = None, max_results: int = 20) -> List[Dict]:
        """AngelList에서 스타트업 정보 크롤링"""
        if search_queries is None:
            search_queries = ["AI", "Fintech", "HealthTech", "EdTech", "SaaS"]
        
        logger.info("AngelList 스타트업 정보 크롤링 시작")
        startups = []
        
        for query in search_queries:
            try:
                logger.info(f"AngelList '{query}' 검색 중...")
                
                # AngelList 검색 URL
                search_url = f"https://angel.co/companies?keywords={quote(query)}"
                await self.page.goto(search_url, wait_until='networkidle')
                await self.random_delay()
                
                # 검색 결과 대기
                try:
                    await self.page.wait_for_selector('[data-testid="company-card"], .company-card', timeout=15000)
                except:
                    logger.warning(f"'{query}' 검색 결과를 찾을 수 없습니다")
                    continue
                
                company_cards = await self.page.query_selector_all('[data-testid="company-card"], .company-card')
                
                for i, card in enumerate(company_cards[:max_results//len(search_queries)]):
                    try:
                        # 회사명
                        name_elem = await card.query_selector('h3, .company-name')
                        name = await name_elem.text_content() if name_elem else "Unknown"
                        
                        # 설명
                        desc_elem = await card.query_selector('p, .description')
                        description = await desc_elem.text_content() if desc_elem else ""
                        
                        # 위치
                        location_elem = await card.query_selector('[class*="location"], .location')
                        location = await location_elem.text_content() if location_elem else ""
                        
                        # 펀딩 정보
                        funding_elem = await card.query_selector('[class*="funding"], .funding')
                        funding = await funding_elem.text_content() if funding_elem else ""
                        
                        startup_data = {
                            'name': name.strip(),
                            'description': description.strip()[:500],
                            'location': location.strip(),
                            'funding': funding.strip(),
                            'category': query,
                            'source': 'AngelList',
                            'type': 'startup',
                            'crawled_at': datetime.now().isoformat()
                        }
                        
                        startups.append(startup_data)
                        logger.info(f"AngelList 크롤링: {name[:50]}...")
                        
                    except Exception as e:
                        logger.error(f"회사 카드 크롤링 실패: {e}")
                        continue
                
                await self.random_delay(2, 4)
                
            except Exception as e:
                logger.error(f"AngelList '{query}' 크롤링 실패: {e}")
                continue
        
        logger.info(f"AngelList 크롤링 완료: {len(startups)}개 스타트업")
        return startups
    
    async def crawl_crunchbase_ecosystem(self, search_queries: List[str] = None, max_results: int = 30) -> List[Dict]:
        """Crunchbase에서 생태계 정보 크롤링"""
        if search_queries is None:
            search_queries = ["AI startups", "Fintech companies", "HealthTech", "EdTech", "SaaS"]
        
        logger.info("Crunchbase 생태계 정보 크롤링 시작")
        all_data = []
        
        for query in search_queries:
            try:
                logger.info(f"Crunchbase '{query}' 검색 중...")
                
                search_url = f"https://www.crunchbase.com/search/organizations?query={quote(query)}"
                await self.page.goto(search_url, wait_until='networkidle')
                await self.random_delay()
                
                # 검색 결과 대기
                try:
                    await self.page.wait_for_selector('.result-card, .search-result', timeout=15000)
                except:
                    logger.warning(f"'{query}' 검색 결과를 찾을 수 없습니다")
                    continue
                
                results = await self.page.query_selector_all('.result-card, .search-result')
                
                for i, result in enumerate(results[:max_results//len(search_queries)]):
                    try:
                        # 회사명
                        name_elem = await result.query_selector('.result-card__title, .search-result__title')
                        name = await name_elem.text_content() if name_elem else "Unknown"
                        
                        # 설명
                        desc_elem = await result.query_selector('.result-card__description, .search-result__description')
                        description = await desc_elem.text_content() if desc_elem else ""
                        
                        # 위치
                        location_elem = await result.query_selector('.result-card__location, .search-result__location')
                        location = await location_elem.text_content() if location_elem else ""
                        
                        # 펀딩 정보
                        funding_elem = await result.query_selector('.result-card__funding, .search-result__funding')
                        funding = await funding_elem.text_content() if funding_elem else ""
                        
                        # 회사 타입 판별
                        company_type = self._determine_company_type(name, description, query)
                        
                        company_data = {
                            'name': name.strip(),
                            'description': description.strip()[:500],
                            'location': location.strip(),
                            'funding': funding.strip(),
                            'category': query,
                            'source': 'Crunchbase',
                            'type': company_type,
                            'crawled_at': datetime.now().isoformat()
                        }
                        
                        all_data.append(company_data)
                        logger.info(f"Crunchbase 크롤링: {name[:50]}... ({company_type})")
                        
                    except Exception as e:
                        logger.error(f"검색 결과 크롤링 실패: {e}")
                        continue
                
                await self.random_delay(2, 4)
                
            except Exception as e:
                logger.error(f"Crunchbase '{query}' 크롤링 실패: {e}")
                continue
        
        logger.info(f"Crunchbase 크롤링 완료: {len(all_data)}개 항목")
        return all_data
    
    def _determine_company_type(self, name: str, description: str, category: str) -> str:
        """회사 타입을 판별하는 함수"""
        name_lower = name.lower()
        desc_lower = description.lower()
        category_lower = category.lower()
        
        # 투자자 관련 키워드
        investor_keywords = ['venture', 'capital', 'vc', 'investment', 'fund', 'angel', 'investor']
        if any(keyword in name_lower or keyword in desc_lower for keyword in investor_keywords):
            return 'investor'
        
        # 액셀러레이터 관련 키워드
        accelerator_keywords = ['accelerator', 'incubator', 'studio', 'lab']
        if any(keyword in name_lower or keyword in desc_lower for keyword in accelerator_keywords):
            return 'accelerator'
        
        # 코워킹 스페이스 관련 키워드
        coworking_keywords = ['coworking', 'space', 'hub', 'center', 'office']
        if any(keyword in name_lower or keyword in desc_lower for keyword in coworking_keywords):
            return 'coworking_space'
        
        # 기본적으로는 스타트업으로 분류
        return 'startup'
    
    async def crawl_startup_events(self, max_pages: int = 3) -> List[Dict]:
        """스타트업 이벤트 정보 크롤링"""
        logger.info("스타트업 이벤트 정보 크롤링 시작")
        events = []
        
        # Eventbrite 스타트업 이벤트 검색
        try:
            search_url = "https://www.eventbrite.com/d/search/?q=startup"
            await self.page.goto(search_url, wait_until='networkidle')
            await self.random_delay()
            
            # 이벤트 카드 대기
            try:
                await self.page.wait_for_selector('[data-testid="event-card"], .eds-event-card', timeout=15000)
            except:
                logger.warning("Eventbrite 이벤트를 찾을 수 없습니다")
                return events
            
            event_cards = await self.page.query_selector_all('[data-testid="event-card"], .eds-event-card')
            
            for i, card in enumerate(event_cards[:20]):
                try:
                    # 이벤트명
                    title_elem = await card.query_selector('h3, .eds-event-card__title')
                    title = await title_elem.text_content() if title_elem else "Unknown Event"
                    
                    # 날짜
                    date_elem = await card.query_selector('[class*="date"], .eds-event-card__date')
                    date = await date_elem.text_content() if date_elem else ""
                    
                    # 위치
                    location_elem = await card.query_selector('[class*="location"], .eds-event-card__location')
                    location = await location_elem.text_content() if location_elem else ""
                    
                    # 링크
                    link_elem = await card.query_selector('a')
                    link = await link_elem.get_attribute('href') if link_elem else ""
                    
                    event_data = {
                        'name': title.strip(),
                        'date': date.strip(),
                        'location': location.strip(),
                        'website': f"https://www.eventbrite.com{link}" if link.startswith('/') else link,
                        'source': 'Eventbrite',
                        'type': 'event',
                        'crawled_at': datetime.now().isoformat()
                    }
                    
                    events.append(event_data)
                    logger.info(f"이벤트 크롤링: {title[:50]}...")
                    
                except Exception as e:
                    logger.error(f"이벤트 카드 크롤링 실패: {e}")
                    continue
                
        except Exception as e:
            logger.error(f"Eventbrite 크롤링 실패: {e}")
        
        logger.info(f"이벤트 크롤링 완료: {len(events)}개 이벤트")
        return events
    
    async def crawl_all_sources(self) -> Dict[str, Any]:
        """모든 소스에서 데이터 크롤링"""
        logger.info("전체 생태계 데이터 크롤링 시작")
        
        # 1. TechCrunch 스타트업 정보
        techcrunch_startups = await self.crawl_techcrunch_startups()
        self.ecosystem_data['startups'].extend(techcrunch_startups)
        
        # 2. AngelList 스타트업 정보
        angel_list_startups = await self.crawl_angel_list()
        self.ecosystem_data['startups'].extend(angel_list_startups)
        
        # 3. Crunchbase 생태계 정보
        crunchbase_data = await self.crawl_crunchbase_ecosystem()
        
        # 데이터 타입별로 분류
        for item in crunchbase_data:
            if item['type'] == 'startup':
                self.ecosystem_data['startups'].append(item)
            elif item['type'] == 'investor':
                self.ecosystem_data['investors'].append(item)
            elif item['type'] == 'accelerator':
                self.ecosystem_data['accelerators'].append(item)
            elif item['type'] == 'coworking_space':
                self.ecosystem_data['coworking_spaces'].append(item)
        
        # 4. 스타트업 이벤트 정보
        events = await self.crawl_startup_events()
        self.ecosystem_data['events'].extend(events)
        
        # 중복 제거
        self._remove_duplicates()
        
        # 통계 정보 추가
        self._add_statistics()
        
        logger.info("전체 생태계 데이터 크롤링 완료")
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
            filename = f"ecosystem_data_{timestamp}.json"
        
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
    logger.info("🚀 스타트업 생태계 탐색 크롤러 시작")
    
    async with EcosystemCrawler() as crawler:
        try:
            # 전체 소스에서 데이터 크롤링
            ecosystem_data = await crawler.crawl_all_sources()
            
            # 데이터 저장
            filename = crawler.save_data()
            
            if filename:
                logger.info(f"✅ 크롤링 완료! 데이터 저장됨: {filename}")
                
                # 결과 요약 출력
                stats = ecosystem_data.get('statistics', {})
                logger.info(f"📊 크롤링 결과 요약:")
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
