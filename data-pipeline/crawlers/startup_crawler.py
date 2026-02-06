#!/usr/bin/env python3
"""
스타트업 정보 크롤링 스크립트
Crunchbase, LinkedIn, AngelList 등에서 스타트업 정보를 수집합니다.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import aiohttp
import pandas as pd
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StartupCrawler:
    def __init__(self):
        self.session = None
        self.browser = None
        self.page = None
        self.startups_data = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def crawl_crunchbase(self, search_query: str = "AI startups", max_results: int = 50) -> List[Dict]:
        """Crunchbase에서 스타트업 정보 크롤링"""
        logger.info(f"Crunchbase에서 '{search_query}' 검색 결과 크롤링 시작")
        
        try:
            # Crunchbase 검색 페이지로 이동
            search_url = f"https://www.crunchbase.com/search/organizations?query={search_query}"
            await self.page.goto(search_url, wait_until='networkidle')
            
            # 검색 결과 대기
            await self.page.wait_for_selector('.result-card', timeout=10000)
            
            startups = []
            results = await self.page.query_selector_all('.result-card')
            
            for i, result in enumerate(results[:max_results]):
                try:
                    # 회사명
                    name_elem = await result.query_selector('.result-card__title')
                    name = await name_elem.text_content() if name_elem else "Unknown"
                    
                    # 설명
                    desc_elem = await result.query_selector('.result-card__description')
                    description = await desc_elem.text_content() if desc_elem else ""
                    
                    # 위치
                    location_elem = await result.query_selector('.result-card__location')
                    location = await location_elem.text_content() if location_elem else ""
                    
                    # 펀딩 정보
                    funding_elem = await result.query_selector('.result-card__funding')
                    funding = await funding_elem.text_content() if funding_elem else ""
                    
                    startup_data = {
                        'name': name.strip(),
                        'description': description.strip(),
                        'location': location.strip(),
                        'funding': funding.strip(),
                        'source': 'Crunchbase',
                        'crawled_at': datetime.now().isoformat()
                    }
                    
                    startups.append(startup_data)
                    logger.info(f"크롤링 완료: {name}")
                    
                except Exception as e:
                    logger.error(f"개별 결과 크롤링 실패: {e}")
                    continue
                
                # 요청 간격 조절
                await asyncio.sleep(1)
            
            logger.info(f"Crunchbase 크롤링 완료: {len(startups)}개 스타트업")
            return startups
            
        except Exception as e:
            logger.error(f"Crunchbase 크롤링 실패: {e}")
            return []
    
    async def crawl_angel_list(self, search_query: str = "AI", max_results: int = 50) -> List[Dict]:
        """AngelList에서 스타트업 정보 크롤링"""
        logger.info(f"AngelList에서 '{search_query}' 검색 결과 크롤링 시작")
        
        try:
            # AngelList 검색 페이지로 이동
            search_url = f"https://angel.co/companies?keywords={search_query}"
            await self.page.goto(search_url, wait_until='networkidle')
            
            # 검색 결과 대기
            await self.page.wait_for_selector('.company', timeout=10000)
            
            startups = []
            results = await self.page.query_selector_all('.company')
            
            for i, result in enumerate(results[:max_results]):
                try:
                    # 회사명
                    name_elem = await result.query_selector('.company-name')
                    name = await name_elem.text_content() if name_elem else "Unknown"
                    
                    # 설명
                    desc_elem = await result.query_selector('.company-description')
                    description = await desc_elem.text_content() if desc_elem else ""
                    
                    # 위치
                    location_elem = await result.query_selector('.company-location')
                    location = await location_elem.text_content() if location_elem else ""
                    
                    # 태그
                    tags_elem = await result.query_selector_all('.company-tags .tag')
                    tags = []
                    for tag in tags_elem:
                        tag_text = await tag.text_content()
                        if tag_text:
                            tags.append(tag_text.strip())
                    
                    startup_data = {
                        'name': name.strip(),
                        'description': description.strip(),
                        'location': location.strip(),
                        'tags': tags,
                        'source': 'AngelList',
                        'crawled_at': datetime.now().isoformat()
                    }
                    
                    startups.append(startup_data)
                    logger.info(f"크롤링 완료: {name}")
                    
                except Exception as e:
                    logger.error(f"개별 결과 크롤링 실패: {e}")
                    continue
                
                # 요청 간격 조절
                await asyncio.sleep(1)
            
            logger.info(f"AngelList 크롤링 완료: {len(startups)}개 스타트업")
            return startups
            
        except Exception as e:
            logger.error(f"AngelList 크롤링 실패: {e}")
            return []
    
    async def crawl_startup_blink(self, max_results: int = 50) -> List[Dict]:
        """StartupBlink에서 글로벌 스타트업 랭킹 크롤링"""
        logger.info("StartupBlink에서 글로벌 스타트업 랭킹 크롤링 시작")
        
        try:
            # StartupBlink 메인 페이지로 이동
            await self.page.goto("https://www.startupblink.com/", wait_until='networkidle')
            
            # 글로벌 랭킹 섹션 대기
            await self.page.wait_for_selector('.ranking-item', timeout=10000)
            
            startups = []
            results = await self.page.query_selector_all('.ranking-item')
            
            for i, result in enumerate(results[:max_results]):
                try:
                    # 회사명
                    name_elem = await result.query_selector('.company-name')
                    name = await name_elem.text_content() if name_elem else "Unknown"
                    
                    # 랭킹
                    rank_elem = await result.query_selector('.ranking-number')
                    rank = await rank_elem.text_content() if rank_elem else ""
                    
                    # 위치
                    location_elem = await result.query_selector('.company-location')
                    location = await location_elem.text_content() if location_elem else ""
                    
                    # 점수
                    score_elem = await result.query_selector('.company-score')
                    score = await score_elem.text_content() if score_elem else ""
                    
                    startup_data = {
                        'name': name.strip(),
                        'rank': rank.strip(),
                        'location': location.strip(),
                        'score': score.strip(),
                        'source': 'StartupBlink',
                        'crawled_at': datetime.now().isoformat()
                    }
                    
                    startups.append(startup_data)
                    logger.info(f"크롤링 완료: {name} (랭킹: {rank})")
                    
                except Exception as e:
                    logger.error(f"개별 결과 크롤링 실패: {e}")
                    continue
                
                # 요청 간격 조절
                await asyncio.sleep(1)
            
            logger.info(f"StartupBlink 크롤링 완료: {len(startups)}개 스타트업")
            return startups
            
        except Exception as e:
            logger.error(f"StartupBlink 크롤링 실패: {e}")
            return []
    
    async def save_data(self, data: List[Dict], filename: str):
        """크롤링한 데이터를 JSON 파일로 저장"""
        filepath = f"data-pipeline/data/{filename}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"데이터 저장 완료: {filepath}")
        
        # CSV로도 저장
        df = pd.DataFrame(data)
        csv_filepath = filepath.replace('.json', '.csv')
        df.to_csv(csv_filepath, index=False, encoding='utf-8')
        logger.info(f"CSV 저장 완료: {csv_filepath}")
    
    async def run_crawling(self):
        """전체 크롤링 프로세스 실행"""
        logger.info("스타트업 크롤링 시작")
        
        all_startups = []
        
        # 1. Crunchbase 크롤링
        crunchbase_data = await self.crawl_crunchbase("AI startups", 20)
        all_startups.extend(crunchbase_data)
        await self.save_data(crunchbase_data, "crunchbase_startups.json")
        
        # 2. AngelList 크롤링
        angel_list_data = await self.crawl_angel_list("AI", 20)
        all_startups.extend(angel_list_data)
        await self.save_data(angel_list_data, "angel_list_startups.json")
        
        # 3. StartupBlink 크롤링
        startup_blink_data = await self.crawl_startup_blink(20)
        all_startups.extend(startup_blink_data)
        await self.save_data(startup_blink_data, "startup_blink_startups.json")
        
        # 전체 데이터 저장
        await self.save_data(all_startups, "all_startups_combined.json")
        
        logger.info(f"전체 크롤링 완료: {len(all_startups)}개 스타트업")
        return all_startups

async def main():
    """메인 함수"""
    async with StartupCrawler() as crawler:
        await crawler.run_crawling()

if __name__ == "__main__":
    asyncio.run(main())
