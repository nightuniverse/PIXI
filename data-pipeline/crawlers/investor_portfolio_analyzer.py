#!/usr/bin/env python3
"""
투자자 포트폴리오 분석기
더브이씨(THE VC) 투자자 상세 페이지에서 포트폴리오 정보를 크롤링하고 투자 성향을 분석합니다.
"""

import json
import logging
import re
import time
from collections import Counter
from datetime import datetime
from typing import Dict, List, Any, Optional

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

BASE_URL = "https://thevc.kr"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# 투자 단계 매핑
INVESTMENT_STAGES = {
    "Seed": "시드",
    "Pre-A": "Pre-A",
    "Series A": "시리즈A",
    "Series B": "시리즈B",
    "Series C": "시리즈C",
    "Series D": "시리즈D",
    "Pre-IPO": "Pre-IPO",
}

# 카테고리 키워드 매핑 (포트폴리오 회사 설명/카테고리에서 추출)
CATEGORY_KEYWORDS = {
    "AI": ["AI", "인공지능", "머신러닝", "딥러닝", "ML", "머신러닝", "딥러닝", "AI 플랫폼", "AI 솔루션"],
    "헬스케어": ["헬스케어", "의료", "바이오", "제약", "진단", "치료", "의료기기", "헬스", "건강"],
    "핀테크": ["핀테크", "금융", "결제", "송금", "대출", "보험", "투자", "은행", "금융서비스"],
    "이커머스": ["이커머스", "커머스", "쇼핑", "마켓플레이스", "온라인쇼핑", "전자상거래", "배송"],
    "게임": ["게임", "모바일게임", "콘솔게임", "게임플랫폼", "게임개발"],
    "교육": ["교육", "에듀테크", "온라인교육", "학습", "튜터링", "교육플랫폼"],
    "모빌리티": ["모빌리티", "교통", "택시", "배달", "물류", "운송", "자율주행"],
    "엔터테인먼트": ["엔터테인먼트", "콘텐츠", "영상", "음악", "스트리밍", "미디어"],
    "SaaS": ["SaaS", "소프트웨어", "클라우드", "B2B", "기업용소프트웨어"],
    "IoT": ["IoT", "사물인터넷", "스마트홈", "센서", "하드웨어"],
}


def extract_portfolio_from_page(html: str) -> List[Dict[str, Any]]:
    """HTML에서 포트폴리오 회사 정보 추출"""
    portfolio = []
    
    # 포트폴리오 회사 링크 패턴 찾기 (thevc.kr/회사명 형태)
    # 테이블이나 리스트에서 포트폴리오 회사 링크 추출
    portfolio_patterns = [
        r'href=["\'](?:https://thevc\.kr/)?([a-zA-Z0-9_-]+)["\']',  # 일반 링크
        r'thevc\.kr/([a-zA-Z0-9_-]+)',  # URL 직접 매칭
    ]
    
    seen_slugs = set()
    for pattern in portfolio_patterns:
        for m in re.finditer(pattern, html):
            slug = m.group(1) if m.lastindex else m.group(0)
            if slug in seen_slugs or len(slug) < 3:
                continue
            # 제외할 슬러그들
            skip_slugs = {"browse", "discussions", "pricing", "guide", "thevc", "icons", "login", "signup"}
            if slug.lower() in skip_slugs:
                continue
            seen_slugs.add(slug)
            portfolio.append({
                "slug": slug,
                "name": slug.replace("-", " ").title()[:100],
                "url": f"{BASE_URL}/{slug}",
            })
    
    return portfolio


def analyze_investment_tendency(portfolio: List[Dict[str, Any]], html: str) -> Dict[str, Any]:
    """포트폴리오를 분석하여 투자 성향 추출"""
    if not portfolio:
        return {
            "investment_focus": [],
            "preferred_stages": [],
            "portfolio_count": 0,
        }
    
    # HTML에서 투자 단계 정보 추출 (테이블이나 텍스트에서)
    stages_found = []
    for stage_en, stage_ko in INVESTMENT_STAGES.items():
        if stage_en.lower() in html.lower() or stage_ko in html:
            stages_found.append(stage_ko)
    
    # 카테고리 분석 (HTML 텍스트에서 키워드 매칭)
    category_counts = Counter()
    html_lower = html.lower()
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in html_lower:
                category_counts[category] += html_lower.count(keyword.lower())
    
    # 상위 3개 카테고리 선택
    top_categories = [cat for cat, _ in category_counts.most_common(3)]
    
    return {
        "investment_focus": top_categories if top_categories else ["다양"],
        "preferred_stages": list(set(stages_found))[:5] if stages_found else [],
        "portfolio_count": len(portfolio),
    }


def fetch_investor_portfolio_playwright(slug: str) -> Optional[Dict[str, Any]]:
    """Playwright로 투자자 상세 페이지에서 포트폴리오 정보 크롤링"""
    if not sync_playwright:
        logger.warning("Playwright가 설치되지 않았습니다. 포트폴리오 크롤링을 건너뜁니다.")
        return None
    
    url = f"{BASE_URL}/{slug}"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers({"User-Agent": USER_AGENT})
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            time.sleep(1)  # SPA 렌더링 대기 (최소화)
            
            html = page.content()
            browser.close()
            
            portfolio = extract_portfolio_from_page(html)
            tendency = analyze_investment_tendency(portfolio, html)
            
            return {
                "portfolio": portfolio,
                "investment_tendency": tendency,
                "crawled_at": datetime.now().isoformat(),
            }
    except Exception as e:
        logger.warning(f"포트폴리오 크롤링 실패 {slug}: {e}")
        return None


def analyze_investors_portfolio(investors: List[Dict[str, Any]], max_analyze: int = 50) -> List[Dict[str, Any]]:
    """투자자 목록에서 포트폴리오 정보를 분석하여 투자 성향 추가"""
    logger.info(f"투자자 포트폴리오 분석 시작 (최대 {max_analyze}건)")
    
    analyzed = []
    for i, investor in enumerate(investors[:max_analyze]):
        slug = investor.get("slug") or investor.get("name", "").lower().replace(" ", "-")
        if not slug:
            continue
        
        logger.info(f"[{i+1}/{min(len(investors), max_analyze)}] {investor.get('name', slug)} 포트폴리오 분석 중...")
        
        portfolio_data = fetch_investor_portfolio_playwright(slug)
        if portfolio_data:
            investor.update({
                "portfolio": portfolio_data.get("portfolio", []),
                "investment_focus": portfolio_data.get("investment_tendency", {}).get("investment_focus", []),
                "preferred_stages": portfolio_data.get("investment_tendency", {}).get("preferred_stages", []),
                "portfolio_count": portfolio_data.get("investment_tendency", {}).get("portfolio_count", 0),
            })
            logger.info(f"  → 포트폴리오 {investor.get('portfolio_count', 0)}개, 성향: {', '.join(investor.get('investment_focus', []))}")
        else:
            investor.update({
                "portfolio": [],
                "investment_focus": [],
                "preferred_stages": [],
                "portfolio_count": 0,
            })
        
        analyzed.append(investor)
        time.sleep(0.5)  # 요청 간격 (최소화)
    
    logger.info(f"포트폴리오 분석 완료: {len(analyzed)}건")
    return analyzed


if __name__ == "__main__":
    # 테스트: 샘플 투자자 포트폴리오 분석
    test_investors = [
        {"slug": "levit", "name": "Levit", "type": "investor"},
        {"slug": "stonebridgeventures", "name": "스톤브릿지벤처스", "type": "investor"},
    ]
    
    result = analyze_investors_portfolio(test_investors, max_analyze=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))
