#!/usr/bin/env python3
"""
고급 스타트업 정보 크롤링 시스템
여러 사이트에서 풍부한 스타트업 데이터를 수집합니다.
"""

import asyncio
import json
import logging
import time
import random
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse, quote

import aiohttp
import pandas as pd
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('advanced_crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AdvancedStartupCrawler:
    def __init__(self):
        self.session = None
        self.browser = None
        self.page = None
        self.startups_data = []
        
        # User-Agent 목록 (차단 방지)
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        self.page = await self.browser.new_page()
        
        # User-Agent 설정
        await self.page.set_extra_http_headers({
            'User-Agent': random.choice(self.user_agents)
        })
        
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def random_delay(self, min_delay=1, max_delay=3):
        """랜덤 지연으로 차단 방지"""
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)
    
    async def crawl_crunchbase_advanced(self, search_queries: List[str] = None, max_results: int = 30) -> List[Dict]:
        """Crunchbase에서 고급 스타트업 정보 크롤링"""
        if search_queries is None:
            search_queries = ["AI startups", "Fintech", "HealthTech", "EdTech"]
        
        logger.info(f"Crunchbase 고급 크롤링 시작: {search_queries}")
        all_startups = []
        
        for query in search_queries:
            try:
                logger.info(f"'{query}' 검색 중...")
                
                # 검색 URL 구성
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
                logger.info(f"'{query}'에서 {len(results)}개 결과 발견")
                
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
                        
                        # 산업 분야
                        industry_elem = await result.query_selector('.result-card__industry, .search-result__industry')
                        industry = await industry_elem.text_content() if industry_elem else query
                        
                        startup_data = {
                            'name': name.strip(),
                            'description': description.strip(),
                            'location': location.strip(),
                            'funding': funding.strip(),
                            'industry': industry.strip(),
                            'search_query': query,
                            'source': 'Crunchbase',
                            'crawled_at': datetime.now().isoformat()
                        }
                        
                        all_startups.append(startup_data)
                        logger.info(f"✅ {name[:30]}... ({query})")
                        
                    except Exception as e:
                        logger.error(f"개별 결과 크롤링 실패: {e}")
                        continue
                    
                    await self.random_delay(0.5, 1.5)
                
                await self.random_delay(2, 4)
                
            except Exception as e:
                logger.error(f"'{query}' 크롤링 실패: {e}")
                continue
        
        logger.info(f"Crunchbase 고급 크롤링 완료: {len(all_startups)}개 스타트업")
        return all_startups
    
    async def crawl_angel_list_advanced(self, search_queries: List[str] = None, max_results: int = 30) -> List[Dict]:
        """AngelList에서 고급 스타트업 정보 크롤링"""
        if search_queries is None:
            search_queries = ["AI", "Fintech", "Health", "Education"]
        
        logger.info(f"AngelList 고급 크롤링 시작: {search_queries}")
        all_startups = []
        
        for query in search_queries:
            try:
                logger.info(f"'{query}' 검색 중...")
                
                # 검색 URL 구성
                search_url = f"https://angel.co/companies?keywords={quote(query)}"
                await self.page.goto(search_url, wait_until='networkidle')
                await self.random_delay()
                
                # 검색 결과 대기
                try:
                    await self.page.wait_for_selector('.company, .company-card', timeout=15000)
                except:
                    logger.warning(f"'{query}' 검색 결과를 찾을 수 없습니다")
                    continue
                
                results = await self.page.query_selector_all('.company, .company-card')
                logger.info(f"'{query}'에서 {len(results)}개 결과 발견")
                
                for i, result in enumerate(results[:max_results//len(search_queries)]):
                    try:
                        # 회사명
                        name_elem = await result.query_selector('.company-name, .company-card__name')
                        name = await name_elem.text_content() if name_elem else "Unknown"
                        
                        # 설명
                        desc_elem = await result.query_selector('.company-description, .company-card__description')
                        description = await desc_elem.text_content() if desc_elem else ""
                        
                        # 위치
                        location_elem = await result.query_selector('.company-location, .company-card__location')
                        location = await location_elem.text_content() if location_elem else ""
                        
                        # 태그
                        tags_elem = await result.query_selector_all('.company-tags .tag, .company-card__tags .tag')
                        tags = []
                        for tag in tags_elem:
                            tag_text = await tag.text_content()
                            if tag_text:
                                tags.append(tag_text.strip())
                        
                        # 펀딩 단계
                        stage_elem = await result.query_selector('.company-stage, .company-card__stage')
                        stage = await stage_elem.text_content() if stage_elem else ""
                        
                        startup_data = {
                            'name': name.strip(),
                            'description': description.strip(),
                            'location': location.strip(),
                            'tags': tags,
                            'stage': stage.strip(),
                            'search_query': query,
                            'source': 'AngelList',
                            'crawled_at': datetime.now().isoformat()
                        }
                        
                        all_startups.append(startup_data)
                        logger.info(f"✅ {name[:30]}... ({query})")
                        
                    except Exception as e:
                        logger.error(f"개별 결과 크롤링 실패: {e}")
                        continue
                    
                    await self.random_delay(0.5, 1.5)
                
                await self.random_delay(2, 4)
                
            except Exception as e:
                logger.error(f"'{query}' 크롤링 실패: {e}")
                continue
        
        logger.info(f"AngelList 고급 크롤링 완료: {len(all_startups)}개 스타트업")
        return all_startups
    
    async def crawl_startup_blink_advanced(self, max_results: int = 50) -> List[Dict]:
        """StartupBlink에서 글로벌 스타트업 랭킹 크롤링"""
        logger.info("StartupBlink 고급 크롤링 시작")
        
        try:
            # StartupBlink 메인 페이지로 이동
            await self.page.goto("https://www.startupblink.com/", wait_until='networkidle')
            await self.random_delay()
            
            # 글로벌 랭킹 섹션 대기
            try:
                await self.page.wait_for_selector('.ranking-item, .startup-item', timeout=15000)
            except:
                logger.warning("StartupBlink 랭킹 섹션을 찾을 수 없습니다")
                return []
            
            results = await self.page.query_selector_all('.ranking-item, .startup-item')
            logger.info(f"StartupBlink에서 {len(results)}개 결과 발견")
            
            startups = []
            for i, result in enumerate(results[:max_results]):
                try:
                    # 회사명
                    name_elem = await result.query_selector('.company-name, .startup-name')
                    name = await name_elem.text_content() if name_elem else "Unknown"
                    
                    # 랭킹
                    rank_elem = await result.query_selector('.ranking-number, .startup-rank')
                    rank = await rank_elem.text_content() if rank_elem else ""
                    
                    # 위치
                    location_elem = await result.query_selector('.company-location, .startup-location')
                    location = await location_elem.text_content() if location_elem else ""
                    
                    # 점수
                    score_elem = await result.query_selector('.company-score, .startup-score')
                    score = await score_elem.text_content() if score_elem else ""
                    
                    # 카테고리
                    category_elem = await result.query_selector('.company-category, .startup-category')
                    category = await category_elem.text_content() if category_elem else ""
                    
                    startup_data = {
                        'name': name.strip(),
                        'rank': rank.strip(),
                        'location': location.strip(),
                        'score': score.strip(),
                        'category': category.strip(),
                        'source': 'StartupBlink',
                        'crawled_at': datetime.now().isoformat()
                    }
                    
                    startups.append(startup_data)
                    logger.info(f"✅ {name[:30]}... (랭킹: {rank})")
                    
                except Exception as e:
                    logger.error(f"개별 결과 크롤링 실패: {e}")
                    continue
                
                await self.random_delay(0.5, 1.5)
            
            logger.info(f"StartupBlink 고급 크롤링 완료: {len(startups)}개 스타트업")
            return startups
            
        except Exception as e:
            logger.error(f"StartupBlink 고급 크롤링 실패: {e}")
            return []
    
    async def crawl_techcrunch_advanced(self, max_results: int = 40) -> List[Dict]:
        """TechCrunch에서 스타트업 뉴스 크롤링"""
        logger.info("TechCrunch 고급 크롤링 시작")
        
        try:
            # TechCrunch 스타트업 섹션
            await self.page.goto("https://techcrunch.com/category/startups/", wait_until='networkidle')
            await self.random_delay()
            
            # 기사 대기
            try:
                await self.page.wait_for_selector('article, .post-block', timeout=15000)
            except:
                logger.warning("TechCrunch 기사를 찾을 수 없습니다")
                return []
            
            articles = await self.page.query_selector_all('article, .post-block')
            logger.info(f"TechCrunch에서 {len(articles)}개 기사 발견")
            
            startups = []
            for i, article in enumerate(articles[:max_results]):
                try:
                    # 제목
                    title_elem = await article.query_selector('h2, .post-block__title, .post-title')
                    title = await title_elem.text_content() if title_elem else "No Title"
                    
                    # 링크
                    link_elem = await article.query_selector('a[href*="/"]')
                    link = await link_elem.get_attribute('href') if link_elem else ""
                    if link and not link.startswith('http'):
                        link = f"https://techcrunch.com{link}"
                    
                    # 요약
                    excerpt_elem = await article.query_selector('.post-block__content, .post-excerpt, p')
                    excerpt = await excerpt_elem.text_content() if excerpt_elem else ""
                    
                    # 작성자
                    author_elem = await article.query_selector('.river-byline__authors, .post-author, .author')
                    author = await author_elem.text_content() if author_elem else "Unknown"
                    
                    # 시간
                    time_elem = await article.query_selector('time, .post-date, .date')
                    publish_time = await time_elem.text_content() if time_elem else ""
                    
                    startup_data = {
                        'title': title.strip(),
                        'link': link,
                        'excerpt': excerpt.strip(),
                        'author': author.strip(),
                        'publish_time': publish_time.strip(),
                        'source': 'TechCrunch',
                        'crawled_at': datetime.now().isoformat()
                    }
                    
                    startups.append(startup_data)
                    logger.info(f"✅ {title[:40]}...")
                    
                except Exception as e:
                    logger.error(f"개별 기사 크롤링 실패: {e}")
                    continue
                
                await self.random_delay(0.5, 1.5)
            
            logger.info(f"TechCrunch 고급 크롤링 완료: {len(startups)}개 기사")
            return startups
            
        except Exception as e:
            logger.error(f"TechCrunch 고급 크롤링 실패: {e}")
            return []
    
    async def crawl_startup_compass(self, max_results: int = 30) -> List[Dict]:
        """Startup Compass에서 스타트업 정보 크롤링"""
        logger.info("Startup Compass 크롤링 시작")
        
        try:
            # Startup Compass 메인 페이지
            await self.page.goto("https://startupcompass.co/", wait_until='networkidle')
            await self.random_delay()
            
            # 스타트업 목록 대기
            try:
                await self.page.wait_for_selector('.startup-item, .company-card', timeout=15000)
            except:
                logger.warning("Startup Compass 스타트업 목록을 찾을 수 없습니다")
                return []
            
            results = await self.page.query_selector_all('.startup-item, .company-card')
            logger.info(f"Startup Compass에서 {len(results)}개 결과 발견")
            
            startups = []
            for i, result in enumerate(results[:max_results]):
                try:
                    # 회사명
                    name_elem = await result.query_selector('.startup-name, .company-name')
                    name = await name_elem.text_content() if name_elem else "Unknown"
                    
                    # 설명
                    desc_elem = await result.query_selector('.startup-description, .company-description')
                    description = await desc_elem.text_content() if desc_elem else ""
                    
                    # 위치
                    location_elem = await result.query_selector('.startup-location, .company-location')
                    location = await location_elem.text_content() if location_elem else ""
                    
                    # 산업
                    industry_elem = await result.query_selector('.startup-industry, .company-industry')
                    industry = await industry_elem.text_content() if industry_elem else ""
                    
                    startup_data = {
                        'name': name.strip(),
                        'description': description.strip(),
                        'location': location.strip(),
                        'industry': industry.strip(),
                        'source': 'Startup Compass',
                        'crawled_at': datetime.now().isoformat()
                    }
                    
                    startups.append(startup_data)
                    logger.info(f"✅ {name[:30]}...")
                    
                except Exception as e:
                    logger.error(f"개별 결과 크롤링 실패: {e}")
                    continue
                
                await self.random_delay(0.5, 1.5)
            
            logger.info(f"Startup Compass 크롤링 완료: {len(startups)}개 스타트업")
            return startups
            
        except Exception as e:
            logger.error(f"Startup Compass 크롤링 실패: {e}")
            return []
    
    async def save_data(self, data: List[Dict], filename: str):
        """크롤링한 데이터를 JSON 파일로 저장"""
        filepath = f"data/{filename}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"데이터 저장 완료: {filepath}")
        
        # CSV로도 저장
        df = pd.DataFrame(data)
        csv_filepath = filepath.replace('.json', '.csv')
        df.to_csv(csv_filepath, index=False, encoding='utf-8')
        logger.info(f"CSV 저장 완료: {csv_filepath}")
    
    async def run_advanced_crawling(self):
        """전체 고급 크롤링 프로세스 실행"""
        logger.info("고급 스타트업 크롤링 시작")
        
        all_startups = []
        
        # 1. Crunchbase 고급 크롤링
        logger.info("=" * 50)
        crunchbase_data = await self.crawl_crunchbase_advanced(
            ["AI startups", "Fintech", "HealthTech", "EdTech", "SaaS"], 
            40
        )
        all_startups.extend(crunchbase_data)
        await self.save_data(crunchbase_data, "crunchbase_advanced.json")
        
        # 2. AngelList 고급 크롤링
        logger.info("=" * 50)
        angel_list_data = await self.crawl_angel_list_advanced(
            ["AI", "Fintech", "Health", "Education", "Enterprise"], 
            40
        )
        all_startups.extend(angel_list_data)
        await self.save_data(angel_list_data, "angel_list_advanced.json")
        
        # 3. StartupBlink 고급 크롤링
        logger.info("=" * 50)
        startup_blink_data = await self.crawl_startup_blink_advanced(40)
        all_startups.extend(startup_blink_data)
        await self.save_data(startup_blink_data, "startup_blink_advanced.json")
        
        # 4. TechCrunch 고급 크롤링
        logger.info("=" * 50)
        techcrunch_data = await self.crawl_techcrunch_advanced(40)
        all_startups.extend(techcrunch_data)
        await self.save_data(techcrunch_data, "techcrunch_advanced.json")
        
        # 5. Startup Compass 크롤링
        logger.info("=" * 50)
        startup_compass_data = await self.crawl_startup_compass(30)
        all_startups.extend(startup_compass_data)
        await self.save_data(startup_compass_data, "startup_compass.json")
        
        # 전체 데이터 저장
        await self.save_data(all_startups, "all_startups_advanced.json")
        
        # 통계 정보
        sources = {}
        for startup in all_startups:
            source = startup.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
        
        logger.info("=" * 50)
        logger.info(f"🎯 전체 고급 크롤링 완료: {len(all_startups)}개 스타트업")
        logger.info("📊 소스별 통계:")
        for source, count in sources.items():
            logger.info(f"   {source}: {count}개")
        
        return all_startups

async def main():
    """메인 함수"""
    async with AdvancedStartupCrawler() as crawler:
        await crawler.run_advanced_crawling()

if __name__ == "__main__":
    asyncio.run(main())
