#!/usr/bin/env python3
"""
더브이씨(THE VC, thevc.kr) 투자자 목록 크롤러
한국 벤처캐피탈·액셀러레이터·사모펀드 등 투자자 정보 수집.
"""

import json
import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Any

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

BASE_URL = "https://thevc.kr"
INVESTORS_URL = "https://thevc.kr/browse/investors"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# 목록 페이지에서 제외할 경로 (사이트 내부 링크)
SKIP_SLUGS = {
    "browse", "discussions", "pricing", "guide", "thevc",
    "icons", "login", "signup", "api", "static", "nuxt",
    "seller-note", "discussions", "pricing", "gsventures",
}

# 투자자 목록에서 제외할 스타트업 slug (투자도 하지만 본질적으로는 스타트업)
# 더브이씨 투자자 탐색 페이지에 스타트업이 포함될 수 있음 (투자 집행을 하는 경우)
STARTUP_SLUGS = {
    "danggeunmarket",  # 당근마켓 - 투자도 하지만 본질적으로는 스타트업
    "levit",  # 레브잇 - 스타트업
    "soribada",  # 소리바다 - 중소기업 (스타트업으로 분류)
    "marpple",  # 마플코퍼레이션 - 스타트업
    "teamblind",  # 팀블라인드 - 스타트업
    "illimistherapeutics",  # 일리미스테라퓨틱스 - 바이오 중소기업 (투자 유치만, 투자 집행 없음)
    # 필요시 추가 스타트업 slug를 여기에 추가
}


def _clean_investor_name(raw: str) -> str:
    """링크 텍스트에서 회사명만 추출 (비상장, 상장, N회 등 제거)"""
    if not raw or not raw.strip():
        return ""
    s = raw.strip()
    # 접미사 제거: 비상장, 상장, 1회, 2회 등
    s = re.sub(r"비상장$", "", s)
    s = re.sub(r"상장$", "", s)
    s = re.sub(r"\d+회$", "", s)
    s = re.sub(r"운영$", "", s)
    return s.strip()[:100]


def fetch_investors_page() -> str:
    """투자자 탐색 페이지 HTML 가져오기 (requests). SPA면 빈 테이블일 수 있음."""
    try:
        r = requests.get(
            INVESTORS_URL,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
            },
            timeout=15,
        )
        r.raise_for_status()
        return r.text
    except Exception as e:
        logger.warning("페이지 로드 실패 %s: %s", INVESTORS_URL, e)
        return ""


def fetch_investors_page_playwright(scroll_to_load_all: bool = False, max_scrolls: int = 80) -> str:
    """Playwright로 렌더링 후 HTML 반환 (SPA 대응). scroll_to_load_all=True면 스크롤하며 전량 로드."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return ""
    html = ""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers({"User-Agent": USER_AGENT})
            page.goto(INVESTORS_URL, wait_until="networkidle", timeout=30000)
            time.sleep(3)
            if scroll_to_load_all:
                last_height = 0
                for _ in range(max_scrolls):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(0.8)
                    new_height = page.evaluate("document.body.scrollHeight")
                    if new_height == last_height:
                        time.sleep(1)
                        break
                    last_height = new_height
                time.sleep(2)
            html = page.content()
            browser.close()
    except Exception as e:
        logger.warning("Playwright 로드 실패: %s", e)
    return html


def extract_investors_from_html(html: str) -> List[Dict[str, Any]]:
    """
    HTML에서 투자자 링크 추출.
    패턴: [회사명](https://thevc.kr/slug), 또는 href="/slug", href="https://thevc.kr/slug"
    """
    seen_slugs = set()
    investors = []
    slug_to_name = {}

    # 1) 마크다운 스타일: ](https://thevc.kr/slug)
    for m in re.finditer(r"\]\((https://thevc\.kr/([a-zA-Z0-9_-]+))\)", html):
        url, slug = m.group(1), m.group(2)
        if slug.lower() in SKIP_SLUGS or slug.lower() in STARTUP_SLUGS:
            continue
        if slug in seen_slugs:
            continue
        start = m.start()
        bracket = html.rfind("[", 0, start)
        link_text = ""
        if bracket != -1:
            link_text = html[bracket + 1 : start].strip()
            if link_text.startswith("!"):
                continue
        name = _clean_investor_name(link_text) or slug
        seen_slugs.add(slug)
        slug_to_name[slug] = name
        investors.append({
            "slug": slug,
            "name": name,
            "website": url,
            "source": "더브이씨",
            "type": "investor",
            "country": "한국",
            "location": "서울",
            "crawled_at": datetime.now().isoformat(),
        })

    # 2) href="/slug" 또는 href="https://thevc.kr/slug" (아직 안 본 slug만)
    for m in re.finditer(r'href=["\'](?:https://thevc\.kr/)?([a-zA-Z0-9_-]+)["\']', html):
        slug = m.group(1)
        if slug.lower() in SKIP_SLUGS or slug.lower() in STARTUP_SLUGS or slug in seen_slugs:
            continue
        if "/" in slug or len(slug) < 3 or slug.startswith("_"):
            continue
        seen_slugs.add(slug)
        url = f"{BASE_URL}/{slug}"
        investors.append({
            "slug": slug,
            "name": slug_to_name.get(slug) or slug.replace("-", " ").title()[:80],
            "website": url,
            "source": "더브이씨",
            "type": "investor",
            "country": "한국",
            "location": "서울",
            "crawled_at": datetime.now().isoformat(),
        })

    # 3) SPA에서 "/slug" 형태로 들어간 경로 (따옴표 안 문자열)
    for m in re.finditer(r'["\']/([a-z][a-z0-9-]{2,45})["\']', html):
        slug = m.group(1)
        if slug in seen_slugs or slug.lower() in SKIP_SLUGS or slug.lower() in STARTUP_SLUGS:
            continue
        if " " in slug or slug.startswith("_"):
            continue
        seen_slugs.add(slug)
        url = f"{BASE_URL}/{slug}"
        investors.append({
            "slug": slug,
            "name": slug_to_name.get(slug) or slug.replace("-", " ").title()[:80],
            "website": url,
            "source": "더브이씨",
            "type": "investor",
            "country": "한국",
            "location": "서울",
            "crawled_at": datetime.now().isoformat(),
        })

    return investors


def fetch_investor_detail(session: requests.Session, slug: str) -> Dict[str, Any]:
    """투자자 상세 페이지에서 이름·분류 등 보강 (선택)"""
    url = f"{BASE_URL}/{slug}"
    result = {"name": "", "focus": ""}
    try:
        r = session.get(url, timeout=10)
        r.raise_for_status()
        html = r.text
        # <title>회사명 | THE VC</title>
        m = re.search(r"<title[^>]*>([^<|]+)", html)
        if m:
            title = m.group(1).strip()
            if "THE VC" in html and title:
                result["name"] = title.strip()[:100]
    except Exception as e:
        logger.debug("상세 로드 실패 %s: %s", url, e)
    return result


def crawl_thevc(
    max_investors: int = 300,
    fetch_detail: bool = False,
    use_playwright: bool = True,
    bulk_mode: bool = False,
) -> List[Dict[str, Any]]:
    """더브이씨 투자자 목록 크롤링 (SPA라서 Playwright 권장). bulk_mode=True면 스크롤로 전량 수집."""
    logger.info("더브이씨(THE VC) 투자자 크롤링 시작 (목표 %s건)", "전체" if bulk_mode else max_investors)

    html = fetch_investors_page()
    investors = extract_investors_from_html(html)
    if use_playwright and (len(investors) < 10 or bulk_mode):
        logger.info("Playwright로 재요청%s...", " (스크롤 전량 로드)" if bulk_mode else "")
        html = fetch_investors_page_playwright(scroll_to_load_all=bulk_mode)
        if html:
            investors = extract_investors_from_html(html)
    if not html and not investors:
        return []

    logger.info("목록에서 %d개 투자자 링크 추출", len(investors))

    if not bulk_mode:
        investors = investors[:max_investors]

    if fetch_detail and investors:
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})
        for inv in investors[:50]:  # 상세는 최대 50건만
            detail = fetch_investor_detail(session, inv["slug"])
            if detail.get("name"):
                inv["name"] = detail["name"]
            time.sleep(0.4)

    logger.info("더브이씨 크롤링 완료: %d개 투자자", len(investors))
    return investors


def run_thevc_crawler(max_investors: int = 300, bulk_mode: bool = False) -> List[Dict[str, Any]]:
    """크롤러 실행 후 투자자 리스트 반환. bulk_mode=True면 스크롤로 전량 수집(수천 건)."""
    return crawl_thevc(max_investors=max_investors, fetch_detail=False, bulk_mode=bulk_mode)


if __name__ == "__main__":
    result = run_thevc_crawler()
    out_path = "data/thevc_investors.json"
    import os
    os.makedirs("data", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"investors": result, "crawled_at": datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
    logger.info("저장: %s (%d건)", out_path, len(result))
