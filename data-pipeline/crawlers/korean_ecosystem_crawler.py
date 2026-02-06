#!/usr/bin/env python3
"""
한국 스타트업 생태계 특화 크롤러
한국의 주요 스타트업 플랫폼과 뉴스 사이트에서 정보를 수집합니다.
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
        logging.FileHandler('korean_ecosystem_crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class KoreanEcosystemCrawler:
    def __init__(self):
        self.session = None
        self.browser = None
        self.page = None
        self.korean_ecosystem_data = {
            'startups': [],
            'investors': [],
            'accelerators': [],
            'coworking_spaces': [],
            'news': [],
            'crawled_at': datetime.now().isoformat()
        }
        
        # User-Agent 목록
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # 크롤링 설정
        self.delay_range = (3, 6)  # 한국 사이트는 더 긴 지연 시간
        
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
    
    async def crawl_platum_startups(self, max_pages: int = 10) -> List[Dict]:
        """플래텀에서 한국 스타트업 정보 크롤링"""
        logger.info("플래텀 한국 스타트업 정보 크롤링 시작")
        startups = []
        
        try:
            for page in range(1, max_pages + 1):
                url = f"https://platum.kr/startup/page/{page}/"
                logger.info(f"플래텀 페이지 {page} 크롤링: {url}")
                
                try:
                    await self.page.goto(url, wait_until='networkidle', timeout=30000)
                    await self.random_delay(2, 4)
                except Exception as e:
                    logger.warning(f"페이지 {page} 로드 실패: {e}")
                    continue
                
                # 기사 목록 대기 - 다양한 셀렉터 시도
                articles = []
                selectors = ['article', '.post-item', '.entry', '.post', 'div[class*="post"]', 'div[class*="article"]']
                for selector in selectors:
                    try:
                        await self.page.wait_for_selector(selector, timeout=10000)
                        articles = await self.page.query_selector_all(selector)
                        if articles:
                            logger.info(f"셀렉터 '{selector}'로 {len(articles)}개 기사 발견")
                            break
                    except:
                        continue
                
                if not articles:
                    logger.warning(f"페이지 {page}에서 기사를 찾을 수 없습니다")
                    if page > 3:  # 처음 몇 페이지는 계속 시도
                        break
                    continue
                
                for article in articles:
                    try:
                        # 제목
                        title_elem = await article.query_selector('h2, h3, .post-title')
                        title = await title_elem.text_content() if title_elem else "No Title"
                        
                        # 링크
                        link_elem = await article.query_selector('a')
                        link = await link_elem.get_attribute('href') if link_elem else ""
                        
                        # 요약
                        excerpt_elem = await article.query_selector('p, .post-excerpt')
                        excerpt = await excerpt_elem.text_content() if excerpt_elem else ""
                        
                        # 카테고리
                        category_elem = await article.query_selector('.category, .post-category')
                        category = await category_elem.text_content() if category_elem else "스타트업"
                        
                        startup_data = {
                            'name': title.strip()[:100],
                            'description': excerpt.strip()[:500],
                            'website': link if link.startswith('http') else f"https://platum.kr{link}",
                            'category': category.strip(),
                            'source': '플래텀',
                            'type': 'startup',
                            'country': '한국',
                            'crawled_at': datetime.now().isoformat()
                        }
                        
                        startups.append(startup_data)
                        logger.info(f"플래텀 크롤링: {title[:50]}...")
                        
                    except Exception as e:
                        logger.error(f"기사 크롤링 실패: {e}")
                        continue
                
                await self.random_delay(4, 7)  # 페이지 간 더 긴 지연
                
        except Exception as e:
            logger.error(f"플래텀 크롤링 실패: {e}")
        
        logger.info(f"플래텀 크롤링 완료: {len(startups)}개 스타트업")
        return startups
    
    async def crawl_techm_startups(self, max_pages: int = 3) -> List[Dict]:
        """테크M에서 한국 스타트업 정보 크롤링"""
        logger.info("테크M 한국 스타트업 정보 크롤링 시작")
        startups = []
        
        try:
            for page in range(1, max_pages + 1):
                url = f"https://www.techm.kr/news/articleList.html?page={page}&sc_section_code=S1N1&view_type=sm"
                logger.info(f"테크M 페이지 {page} 크롤링: {url}")
                
                await self.page.goto(url, wait_until='networkidle')
                await self.random_delay()
                
                # 기사 목록 대기
                try:
                    await self.page.wait_for_selector('.list-block, .article-list', timeout=15000)
                except:
                    logger.warning(f"페이지 {page}에서 기사를 찾을 수 없습니다")
                    break
                
                articles = await self.page.query_selector_all('.list-block, .article-list')
                
                for article in articles:
                    try:
                        # 제목
                        title_elem = await article.query_selector('h3, h4, .list-titles')
                        title = await title_elem.text_content() if title_elem else "No Title"
                        
                        # 링크
                        link_elem = await article.query_selector('a')
                        link = await link_elem.get_attribute('href') if link_elem else ""
                        
                        # 요약
                        excerpt_elem = await article.query_selector('p, .list-summary')
                        excerpt = await excerpt_elem.text_content() if excerpt_elem else ""
                        
                        # 작성자
                        author_elem = await article.query_selector('.byline, .writer')
                        author = await author_elem.text_content() if author_elem else ""
                        
                        startup_data = {
                            'name': title.strip()[:100],
                            'description': excerpt.strip()[:500],
                            'website': link if link.startswith('http') else f"https://www.techm.kr{link}",
                            'category': '스타트업',
                            'author': author.strip(),
                            'source': '테크M',
                            'type': 'startup',
                            'country': '한국',
                            'crawled_at': datetime.now().isoformat()
                        }
                        
                        startups.append(startup_data)
                        logger.info(f"테크M 크롤링: {title[:50]}...")
                        
                    except Exception as e:
                        logger.error(f"기사 크롤링 실패: {e}")
                        continue
                
                await self.random_delay(4, 7)
                
        except Exception as e:
            logger.error(f"테크M 크롤링 실패: {e}")
        
        logger.info(f"테크M 크롤링 완료: {len(startups)}개 스타트업")
        return startups
    
    async def crawl_startup_ranking(self, max_results: int = 50) -> List[Dict]:
        """스타트업 랭킹 사이트에서 정보 크롤링"""
        logger.info("스타트업 랭킹 정보 크롤링 시작")
        startups = []
        
        # 스타트업 랭킹 사이트들
        ranking_sites = [
            "https://www.startupranking.com/country/kr",
            "https://www.startupblink.com/ecosystem/korea"
        ]
        
        for site_url in ranking_sites:
            try:
                logger.info(f"랭킹 사이트 크롤링: {site_url}")
                
                await self.page.goto(site_url, wait_until='networkidle')
                await self.random_delay()
                
                # 랭킹 목록 대기
                try:
                    await self.page.wait_for_selector('.startup-item, .ranking-item, .company-card', timeout=15000)
                except:
                    logger.warning(f"랭킹 목록을 찾을 수 없습니다: {site_url}")
                    continue
                
                startup_items = await self.page.query_selector_all('.startup-item, .ranking-item, .company-card')
                
                for i, item in enumerate(startup_items[:max_results//len(ranking_sites)]):
                    try:
                        # 회사명
                        name_elem = await item.query_selector('h3, h4, .company-name')
                        name = await name_elem.text_content() if name_elem else "Unknown"
                        
                        # 설명
                        desc_elem = await item.query_selector('p, .description')
                        description = await desc_elem.text_content() if desc_elem else ""
                        
                        # 순위
                        rank_elem = await item.query_selector('.rank, .ranking')
                        rank = await rank_elem.text_content() if rank_elem else ""
                        
                        # 위치
                        location_elem = await item.query_selector('.location, .city')
                        location = await location_elem.text_content() if location_elem else "한국"
                        
                        startup_data = {
                            'name': name.strip(),
                            'description': description.strip()[:500],
                            'location': location.strip(),
                            'ranking': rank.strip(),
                            'source': 'Startup Ranking',
                            'type': 'startup',
                            'country': '한국',
                            'crawled_at': datetime.now().isoformat()
                        }
                        
                        startups.append(startup_data)
                        logger.info(f"랭킹 크롤링: {name[:50]}... (순위: {rank})")
                        
                    except Exception as e:
                        logger.error(f"랭킹 항목 크롤링 실패: {e}")
                        continue
                
                await self.random_delay(3, 5)
                
            except Exception as e:
                logger.error(f"랭킹 사이트 크롤링 실패: {e}")
                continue
        
        logger.info(f"랭킹 크롤링 완료: {len(startups)}개 스타트업")
        return startups
    
    async def crawl_korean_accelerators(self) -> List[Dict]:
        """한국 액셀러레이터 정보 크롤링"""
        logger.info("한국 액셀러레이터 정보 크롤링 시작")
        accelerators = []
        
        # 한국 주요 액셀러레이터 정보 (확장)
        korean_accelerators = [
            {
                "name": "더벤처스",
                "description": "한국의 대표적인 벤처캐피탈 및 액셀러레이터",
                "location": "서울",
                "website": "https://www.theventures.co.kr",
                "focus": "IT, 바이오, 게임 등",
                "source": "Manual Data"
            },
            {
                "name": "스마일게이트인베스트먼트",
                "description": "게임 및 IT 분야 투자 전문 액셀러레이터",
                "location": "서울",
                "website": "https://www.smilegate.com",
                "focus": "게임, IT, 엔터테인먼트",
                "source": "Manual Data"
            },
            {
                "name": "네이버 D2SF",
                "description": "네이버의 스타트업 지원 프로그램",
                "location": "성남",
                "website": "https://d2.naver.com",
                "focus": "AI, 빅데이터, 모바일",
                "source": "Manual Data"
            },
            {
                "name": "카카오벤처스",
                "description": "카카오의 벤처캐피탈 및 액셀러레이터",
                "location": "제주",
                "website": "https://ventures.kakao.com",
                "focus": "모바일, 소셜, AI",
                "source": "Manual Data"
            },
            {
                "name": "LG노트",
                "description": "LG의 스타트업 지원 프로그램",
                "location": "서울",
                "website": "https://www.lgnot.com",
                "focus": "IoT, AI, 로봇",
                "source": "Manual Data"
            },
            {
                "name": "스파크랩",
                "description": "네이버의 스타트업 액셀러레이터",
                "location": "성남",
                "website": "https://sparklab.co.kr",
                "focus": "AI, 빅데이터, 모바일",
                "source": "Manual Data"
            },
            {
                "name": "카카오인베스트먼트",
                "description": "카카오의 투자 전담 회사",
                "location": "서울",
                "website": "https://www.kakao.com/investment",
                "focus": "모바일, 소셜, AI, 콘텐츠",
                "source": "Manual Data"
            },
            {
                "name": "네이버 D2SF",
                "description": "네이버의 스타트업 지원 프로그램",
                "location": "성남",
                "website": "https://d2.naver.com",
                "focus": "AI, 빅데이터, 모바일",
                "source": "Manual Data"
            },
            {
                "name": "벤처스퀘어",
                "description": "스타트업 액셀러레이터 및 코워킹 스페이스",
                "location": "서울",
                "website": "https://venturesquare.net",
                "focus": "스타트업, 창업 지원",
                "source": "Manual Data"
            },
            {
                "name": "플러스엑스",
                "description": "LG의 스타트업 액셀러레이터",
                "location": "서울",
                "website": "https://plusx.co.kr",
                "focus": "IoT, AI, 로봇, 스마트홈",
                "source": "Manual Data"
            }
        ]
        
        for acc in korean_accelerators:
            acc['type'] = 'accelerator'
            acc['country'] = '한국'
            acc['crawled_at'] = datetime.now().isoformat()
            accelerators.append(acc)
        
        logger.info(f"한국 액셀러레이터 정보 수집 완료: {len(accelerators)}개")
        return accelerators
    
    async def crawl_korean_coworking_spaces(self) -> List[Dict]:
        """한국 코워킹 스페이스 정보 크롤링"""
        logger.info("한국 코워킹 스페이스 정보 크롤링 시작")
        coworking_spaces = []
        
        # 한국 주요 코워킹 스페이스 정보
        korean_coworking = [
            {
                "name": "위워크",
                "description": "글로벌 코워킹 스페이스 체인",
                "location": "서울 강남구",
                "website": "https://www.wework.com",
                "focus": "스타트업, 프리랜서, 중소기업",
                "source": "Manual Data"
            },
            {
                "name": "스파크플러스",
                "description": "한국의 대표적인 코워킹 스페이스",
                "location": "서울 강남구",
                "website": "https://www.sparkplus.co.kr",
                "focus": "스타트업, 투자사, 액셀러레이터",
                "source": "Manual Data"
            },
            {
                "name": "마루180",
                "description": "서울 창업허브의 대표적인 코워킹 스페이스",
                "location": "서울 마포구",
                "website": "https://maru180.com",
                "focus": "창업, 소셜벤처, 사회혁신",
                "source": "Manual Data"
            },
            {
                "name": "판교테크노밸리",
                "description": "한국의 실리콘밸리라 불리는 IT 클러스터",
                "location": "경기도 성남시",
                "website": "https://www.pangyo.or.kr",
                "focus": "IT, 바이오, 나노기술",
                "source": "Manual Data"
            }
        ]
        
        for space in korean_coworking:
            space['type'] = 'coworking_space'
            space['country'] = '한국'
            space['crawled_at'] = datetime.now().isoformat()
            coworking_spaces.append(space)
        
        logger.info(f"한국 코워킹 스페이스 정보 수집 완료: {len(coworking_spaces)}개")
        return coworking_spaces
    
    async def crawl_manual_startups(self) -> List[Dict]:
        """수동으로 수집한 한국 주요 스타트업 데이터"""
        logger.info("수동 한국 스타트업 데이터 수집 시작")
        
        manual_startups = [
            {
                "name": "카카오",
                "description": "모바일 플랫폼 및 서비스 기업",
                "location": "제주",
                "website": "https://www.kakaocorp.com",
                "category": "플랫폼",
                "source": "Manual Data"
            },
            {
                "name": "네이버",
                "description": "인터넷 포털 및 IT 서비스 기업",
                "location": "성남",
                "website": "https://www.naver.com",
                "category": "플랫폼",
                "source": "Manual Data"
            },
            {
                "name": "쿠팡",
                "description": "이커머스 플랫폼",
                "location": "서울",
                "website": "https://www.coupang.com",
                "category": "이커머스",
                "source": "Manual Data"
            },
            {
                "name": "배달의민족",
                "description": "배달 주문 플랫폼",
                "location": "서울",
                "website": "https://www.baemin.com",
                "category": "배달",
                "source": "Manual Data"
            },
            {
                "name": "토스",
                "description": "핀테크 서비스",
                "location": "서울",
                "website": "https://www.toss.im",
                "category": "핀테크",
                "source": "Manual Data"
            },
            {
                "name": "당근마켓",
                "description": "중고거래 플랫폼",
                "location": "서울",
                "website": "https://www.daangn.com",
                "category": "중고거래",
                "source": "Manual Data"
            },
            {
                "name": "야놀자",
                "description": "여행 및 숙박 예약 플랫폼",
                "location": "서울",
                "website": "https://www.yanolja.com",
                "category": "여행",
                "source": "Manual Data"
            },
            {
                "name": "무신사",
                "description": "패션 이커머스 플랫폼",
                "location": "서울",
                "website": "https://www.musinsa.com",
                "category": "패션",
                "source": "Manual Data"
            },
            {
                "name": "라인",
                "description": "메신저 및 플랫폼 서비스",
                "location": "서울",
                "website": "https://line.me",
                "category": "메신저",
                "source": "Manual Data"
            },
            {
                "name": "스타일쉐어",
                "description": "패션 렌탈 플랫폼",
                "location": "서울",
                "website": "https://www.styleshare.kr",
                "category": "패션",
                "source": "Manual Data"
            }
        ]
        
        for startup in manual_startups:
            startup['type'] = 'startup'
            startup['country'] = '한국'
            startup['crawled_at'] = datetime.now().isoformat()
        
        logger.info(f"수동 한국 스타트업 데이터 수집 완료: {len(manual_startups)}개")
        return manual_startups
    
    async def crawl_all_korean_sources(self) -> Dict[str, Any]:
        """모든 한국 소스에서 데이터 크롤링"""
        logger.info("한국 생태계 전체 데이터 크롤링 시작")
        
        # 1. 플래텀 스타트업 정보
        platum_startups = await self.crawl_platum_startups(max_pages=10)
        self.korean_ecosystem_data['startups'].extend(platum_startups)
        
        # 2. 테크M 스타트업 정보
        techm_startups = await self.crawl_techm_startups()
        self.korean_ecosystem_data['startups'].extend(techm_startups)
        
        # 3. 스타트업 랭킹 정보
        ranking_startups = await self.crawl_startup_ranking()
        self.korean_ecosystem_data['startups'].extend(ranking_startups)
        
        # 4. 수동 스타트업 데이터
        manual_startups = await self.crawl_manual_startups()
        self.korean_ecosystem_data['startups'].extend(manual_startups)
        
        # 5. 한국 액셀러레이터 정보
        korean_accelerators = await self.crawl_korean_accelerators()
        self.korean_ecosystem_data['accelerators'].extend(korean_accelerators)
        
        # 6. 한국 코워킹 스페이스 정보
        korean_coworking = await self.crawl_korean_coworking_spaces()
        self.korean_ecosystem_data['coworking_spaces'].extend(korean_coworking)
        
        # 중복 제거
        self._remove_duplicates()
        
        # 통계 정보 추가
        self._add_statistics()
        
        logger.info("한국 생태계 전체 데이터 크롤링 완료")
        return self.korean_ecosystem_data
    
    def _remove_duplicates(self):
        """중복 데이터 제거"""
        logger.info("중복 데이터 제거 중...")
        
        # 회사명 기반 중복 제거
        seen_names = set()
        unique_startups = []
        
        for startup in self.korean_ecosystem_data['startups']:
            name_normalized = startup['name'].lower().strip()
            if name_normalized not in seen_names:
                seen_names.add(name_normalized)
                unique_startups.append(startup)
        
        self.korean_ecosystem_data['startups'] = unique_startups
        
        logger.info(f"중복 제거 후 스타트업 수: {len(unique_startups)}")
    
    def _add_statistics(self):
        """통계 정보 추가"""
        stats = {
            'total_startups': len(self.korean_ecosystem_data['startups']),
            'total_investors': len(self.korean_ecosystem_data['investors']),
            'total_accelerators': len(self.korean_ecosystem_data['accelerators']),
            'total_coworking_spaces': len(self.korean_ecosystem_data['coworking_spaces']),
            'total_news': len(self.korean_ecosystem_data['news']),
            'total_entities': sum([
                len(self.korean_ecosystem_data['startups']),
                len(self.korean_ecosystem_data['investors']),
                len(self.korean_ecosystem_data['accelerators']),
                len(self.korean_ecosystem_data['coworking_spaces']),
                len(self.korean_ecosystem_data['news'])
            ])
        }
        
        self.korean_ecosystem_data['statistics'] = stats
        logger.info(f"통계 정보 추가 완료: 총 {stats['total_entities']}개 엔티티")
    
    def save_data(self, filename: str = None):
        """데이터를 파일로 저장"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"korean_ecosystem_data_{timestamp}.json"
        
        filepath = f"data/{filename}"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.korean_ecosystem_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"데이터 저장 완료: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"데이터 저장 실패: {e}")
            return None

async def main():
    """메인 함수"""
    logger.info("🇰🇷 한국 스타트업 생태계 탐색 크롤러 시작")
    
    async with KoreanEcosystemCrawler() as crawler:
        try:
            # 전체 한국 소스에서 데이터 크롤링
            korean_ecosystem_data = await crawler.crawl_all_korean_sources()
            
            # 데이터 저장
            filename = crawler.save_data()
            
            if filename:
                logger.info(f"✅ 한국 생태계 크롤링 완료! 데이터 저장됨: {filename}")
                
                # 결과 요약 출력
                stats = korean_ecosystem_data.get('statistics', {})
                logger.info(f"📊 한국 생태계 크롤링 결과 요약:")
                logger.info(f"   - 스타트업: {stats.get('total_startups', 0)}개")
                logger.info(f"   - 투자자: {stats.get('total_investors', 0)}개")
                logger.info(f"   - 액셀러레이터: {stats.get('total_accelerators', 0)}개")
                logger.info(f"   - 코워킹 스페이스: {stats.get('total_coworking_spaces', 0)}개")
                logger.info(f"   - 뉴스: {stats.get('total_news', 0)}개")
                logger.info(f"   - 총 엔티티: {stats.get('total_entities', 0)}개")
            else:
                logger.error("❌ 데이터 저장 실패")
                
        except Exception as e:
            logger.error(f"크롤링 중 오류 발생: {e}")

if __name__ == "__main__":
    asyncio.run(main())
