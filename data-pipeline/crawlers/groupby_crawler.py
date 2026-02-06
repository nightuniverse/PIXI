#!/usr/bin/env python3
"""
그룹바이(groupby.kr) 스타트업 채용 플랫폼 크롤러
채용 공고 페이지에서 스타트업 목록을 수집합니다. (requests + BeautifulSoup, Playwright 불필요)
"""

import json
import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("groupby_crawler.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

BASE_URL = "https://groupby.kr"
POSITIONS_URL = "https://groupby.kr/positions"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# 위치 -> (lat, lon) 한글
LOCATION_COORDS = {
    "서울": (37.5665, 126.9780),
    "서울 강남구": (37.4979, 127.0276),
    "서울 서초구": (37.4837, 127.0324),
    "서울 마포구": (37.5663, 126.9019),
    "서울 구로구": (37.4954, 126.8874),
    "서울 강서구": (37.5509, 126.8495),
    "서울 관악구": (37.4784, 126.9516),
    "원격근무": (37.5665, 126.9780),
    "신규기업": (37.5665, 126.9780),
}


def _normalize_location(raw: str) -> str:
    """상세 주소에서 도/시/구 수준으로 정규화 (좌표 매핑용)."""
    if not raw or not raw.strip():
        return ""
    s = raw.strip()
    # 서울특별시 -> 서울, 경기도 -> 경기
    s = re.sub(r"서울특별시\s*", "서울 ", s)
    s = re.sub(r"경기도\s*", "경기 ", s)
    s = re.sub(r"부산광역시\s*", "부산 ", s)
    s = re.sub(r"인천광역시\s*", "인천 ", s)
    s = re.sub(r"대구광역시\s*", "대구 ", s)
    s = re.sub(r"대전광역시\s*", "대전 ", s)
    s = re.sub(r"광주광역시\s*", "광주 ", s)
    s = re.sub(r"울산광역시\s*", "울산 ", s)
    s = re.sub(r"세종특별자치시\s*", "세종 ", s)
    s = re.sub(r"제주특별자치도\s*", "제주 ", s)
    # 상세 주소(동/로/길 등) 제거하고 "서울 OO구", "경기 OO시" 형태만 유지 (앞 2~3단어)
    parts = s.split()
    if len(parts) >= 2:
        # "서울 서초구" 또는 "경기 용인시", "서울 강남구 테헤란로" -> "서울 서초구"
        return " ".join(parts[:2]).strip()
    return s.strip()[:50]


def fetch_startup_detail(session: requests.Session, startup_id: str) -> Dict[str, Any]:
    """스타트업 상세 페이지에서 회사명·위치 추출 (한 번의 요청으로 둘 다)."""
    url = f"{BASE_URL}/startups/{startup_id}"
    result: Dict[str, Any] = {"name": "", "location": ""}
    try:
        r = session.get(url, timeout=10)
        r.raise_for_status()
        html = r.text

        # 회사명: <title>회사명 채용 | 그룹바이</title>
        m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I)
        if m:
            title = m.group(1).strip()
            if " 채용 " in title and "그룹바이" in title:
                name = title.split(" 채용 ")[0].strip()
                if name and len(name) <= 50:
                    result["name"] = name
        if not result["name"]:
            m = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
            if m:
                title = m.group(1).strip()
                if " 채용 " in title:
                    result["name"] = title.split(" 채용 ")[0].strip()[:50]

        # 위치: "위치" 라벨 다음 span에 오는 텍스트 (예: >위치</span></div><span ...>서울 서초구</span>)
        loc_raw = None
        loc_m = re.search(r">위치</span></div><span[^>]*>([^<]+)</span>", html)
        if loc_m:
            loc_raw = loc_m.group(1).strip()
        if not loc_raw:
            loc_m = re.search(r"위치\s*[\n\r]+([^\n<]+)", html)
            if loc_m:
                loc_raw = loc_m.group(1).strip()
        if not loc_raw:
            loc_m = re.search(r"(서울\s*[가-힣]+구|경기\s*[가-힣]+시|원격근무|신규기업)", html)
            if loc_m:
                loc_raw = loc_m.group(1).strip()
        if loc_raw and "그룹바이" not in loc_raw and len(loc_raw) < 200:
            result["location"] = _normalize_location(loc_raw)
    except Exception as e:
        logger.debug("상세 페이지 로드 실패 %s: %s", url, e)
    return result


def get_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    })
    return s


def fetch_positions_page(session: requests.Session, page: int = 1) -> str:
    """채용 공고 페이지 HTML 가져오기"""
    url = POSITIONS_URL if page <= 1 else f"{POSITIONS_URL}?page={page}"
    try:
        r = session.get(url, timeout=15)
        r.raise_for_status()
        return r.text
    except Exception as e:
        logger.warning("페이지 로드 실패 %s: %s", url, e)
        return ""


def extract_startup_ids_from_html(html: str) -> List[str]:
    """HTML 전체에서 /startups/숫자 ID만 정규식으로 추출 (최대한 많이)"""
    ids = re.findall(r"/startups/(\d+)", html)
    return list(dict.fromkeys(ids))  # 순서 유지하면서 중복 제거


def extract_startups_from_html(html: str) -> List[Dict[str, Any]]:
    """HTML에서 스타트업 ID 추출 후, 이름은 상세 페이지에서 가져옴."""
    startup_ids = extract_startup_ids_from_html(html)
    startups = []
    for sid in startup_ids:
        link = f"{BASE_URL}/startups/{sid}"
        startups.append({
            "id": sid,
            "name": "",  # 상세 페이지에서 채움
            "website": link,
            "source": "그룹바이",
            "type": "startup",
            "country": "한국",
            "crawled_at": datetime.now().isoformat(),
        })
    return startups


def fetch_startup_ids_with_playwright(max_scroll: int = 25) -> List[str]:
    """Playwright로 채용 공고 페이지 스크롤 후 로드되는 모든 스타트업 ID 수집 (선택)"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return []

    ids = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({"User-Agent": USER_AGENT})
        try:
            page.goto(POSITIONS_URL, wait_until="networkidle", timeout=20000)
            time.sleep(2)
            for _ in range(max_scroll):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(0.8)
            html = page.content()
            ids = list(dict.fromkeys(re.findall(r"/startups/(\d+)", html)))
            browser.close()
        except Exception as e:
            logger.warning("Playwright 스크롤 실패: %s", e)
            try:
                browser.close()
            except Exception:
                pass
    return ids


def crawl_groupby(max_startups: int = 450, fetch_detail: bool = True, use_playwright: bool = True) -> List[Dict[str, Any]]:
    """그룹바이 채용 공고에서 스타트업 목록 수집 (다중 페이지 + 스크롤로 최대한 수집)"""
    logger.info("그룹바이(groupby.kr) 크롤링 시작 (목표 %d건)", max_startups)

    session = get_session()
    startup_ids = []
    seen_ids = set()

    # 1) requests로 여러 페이지에서 ID 추출 (page=1,2,3,...)
    for page in range(1, 11):
        html = fetch_positions_page(session, page)
        if not html:
            break
        ids = extract_startup_ids_from_html(html)
        added = 0
        for i in ids:
            if i not in seen_ids:
                seen_ids.add(i)
                startup_ids.append(i)
                added += 1
        if added == 0 and page > 1:
            break
        logger.info("채용 공고 페이지 %d: %d개 ID (누적 %d)", page, added, len(startup_ids))
        time.sleep(0.5)
        if len(startup_ids) >= max_startups:
            break

    # 2) Playwright로 1페이지 스크롤해 추가 ID 수집 (SPA 로드분)
    if use_playwright and len(startup_ids) < max_startups:
        try:
            more_ids = fetch_startup_ids_with_playwright(max_scroll=60)
            if more_ids:
                before = len(startup_ids)
                for i in more_ids:
                    if i not in seen_ids:
                        seen_ids.add(i)
                        startup_ids.append(i)
                logger.info("Playwright 스크롤 후 추가 %d개 ID (총 %d개)", len(startup_ids) - before, len(startup_ids))
        except Exception as e:
            logger.warning("Playwright 건너뜀: %s", e)

    all_startups = [
        {
            "id": sid,
            "name": "",
            "website": f"{BASE_URL}/startups/{sid}",
            "source": "그룹바이",
            "type": "startup",
            "country": "한국",
            "crawled_at": datetime.now().isoformat(),
        }
        for sid in startup_ids[:max_startups]
    ]

    # 상세 페이지에서 회사명·위치 조회
    if fetch_detail and all_startups:
        logger.info("상세 페이지에서 회사명·위치 조회 중...")
        for s in all_startups:
            detail = fetch_startup_detail(session, s["id"])
            if detail.get("name"):
                s["name"] = detail["name"]
            else:
                s["name"] = f"스타트업_{s['id']}"
            if detail.get("location"):
                s["location"] = detail["location"]
            logger.info("  [그룹바이] %s%s", s["name"], f" @ {s.get('location')}" if s.get("location") else "")
            time.sleep(0.6)

    logger.info("그룹바이 크롤링 완료: %d개 스타트업", len(all_startups))
    return all_startups


def run_groupby_crawler() -> List[Dict[str, Any]]:
    """크롤러 실행 후 스타트업 리스트 반환 (최대 450건, 위치 포함)"""
    return crawl_groupby(max_startups=450)


if __name__ == "__main__":
    result = run_groupby_crawler()
    out_path = "data/groupby_startups.json"
    import os
    os.makedirs("data", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"startups": result, "crawled_at": datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
    logger.info("저장: %s (%d건)", out_path, len(result))
