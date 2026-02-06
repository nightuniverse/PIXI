#!/usr/bin/env python3
"""
RSS 기반 스타트업 생태계 크롤러
Playwright 없이 RSS 피드만으로 수집. 안정적이고 빠름.
"""

import json
import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Any
from urllib.parse import urljoin

import feedparser
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("rss_ecosystem_crawler.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# RSS 피드 목록 (한국 스타트업/창업 뉴스)
RSS_FEEDS = [
    ("https://platum.kr/startup/feed", "플래텀", "startup"),
    ("https://platum.kr/investment/feed", "플래텀", "startup"),
    ("https://platum.kr/feed", "플래텀", "startup"),
    ("https://feeds.feedburner.com/technm", "테크M", "startup"),  # 테크M RSS 있을 경우
]

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch_rss_feed(url: str, timeout: int = 15) -> feedparser.FeedParserDict:
    """RSS 피드 한 개 가져오기"""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml, text/xml"},
            timeout=timeout,
        )
        resp.raise_for_status()
        return feedparser.parse(resp.content)
    except Exception as e:
        logger.warning("RSS 피드 로드 실패 %s: %s", url, e)
        return feedparser.parse("")


def extract_title_and_link(entry) -> tuple:
    """엔트리에서 제목과 링크 추출"""
    title = (entry.get("title") or "").strip()
    link = entry.get("link") or ""
    if not link and entry.get("links"):
        link = entry["links"][0].get("href", "")
    return title, link


def extract_summary(entry) -> str:
    """요약/설명 추출"""
    summary = entry.get("summary") or entry.get("description") or ""
    if isinstance(summary, str):
        # HTML 태그 제거
        summary = re.sub(r"<[^>]+>", "", summary).strip()
        return summary[:500]
    return ""


def crawl_rss_sources(max_entries_per_feed: int = 50) -> List[Dict[str, Any]]:
    """모든 RSS 소스에서 스타트업/뉴스 항목 수집"""
    all_startups = []
    seen_links = set()

    for feed_url, source_name, _ in RSS_FEEDS:
        logger.info("RSS 수집 중: %s (%s)", source_name, feed_url)
        time.sleep(1)  # 요청 간격
        feed = fetch_rss_feed(feed_url)

        if not feed.entries:
            logger.warning("항목 없음: %s", feed_url)
            continue

        count = 0
        for entry in feed.entries[:max_entries_per_feed]:
            title, link = extract_title_and_link(entry)
            if not title or not link:
                continue
            if link in seen_links:
                continue
            seen_links.add(link)

            summary = extract_summary(entry)
            published = entry.get("published") or entry.get("updated") or ""

            item = {
                "name": title[:200],
                "description": summary,
                "website": link,
                "category": "스타트업",
                "source": source_name,
                "type": "startup",
                "country": "한국",
                "published": published,
                "crawled_at": datetime.now().isoformat(),
            }
            all_startups.append(item)
            count += 1
            logger.info("  [%s] %s", source_name, title[:50])

        logger.info("RSS 수집 완료 %s: %d건", source_name, count)

    return all_startups


# 수동 액셀러레이터 / 코워킹 (Playwright 없이 사용)
MANUAL_ACCELERATORS = [
    {"name": "더벤처스", "description": "한국 대표 벤처캐피탈", "location": "서울", "website": "https://www.theventures.co.kr", "focus": "IT, 바이오, 게임", "source": "Manual Data"},
    {"name": "스마일게이트인베스트먼트", "description": "게임/IT 투자", "location": "서울", "website": "https://www.smilegate.com", "focus": "게임, IT", "source": "Manual Data"},
    {"name": "네이버 D2SF", "description": "네이버 스타트업 지원", "location": "성남", "website": "https://d2.naver.com", "focus": "AI, 빅데이터", "source": "Manual Data"},
    {"name": "카카오벤처스", "description": "카카오 벤처캐피탈", "location": "제주", "website": "https://ventures.kakao.com", "focus": "모바일, AI", "source": "Manual Data"},
    {"name": "LG노트", "description": "LG 스타트업 지원", "location": "서울", "website": "https://www.lgnot.com", "focus": "IoT, AI", "source": "Manual Data"},
    {"name": "스파크랩", "description": "네이버 액셀러레이터", "location": "성남", "website": "https://sparklab.co.kr", "focus": "AI, 모바일", "source": "Manual Data"},
    {"name": "벤처스퀘어", "description": "액셀러레이터/코워킹", "location": "서울", "website": "https://venturesquare.net", "focus": "창업 지원", "source": "Manual Data"},
    {"name": "플러스엑스", "description": "LG 액셀러레이터", "location": "서울", "website": "https://plusx.co.kr", "focus": "IoT, AI", "source": "Manual Data"},
]
MANUAL_COWORKING = [
    {"name": "위워크", "description": "글로벌 코워킹", "location": "서울 강남구", "website": "https://www.wework.com", "focus": "스타트업", "source": "Manual Data"},
    {"name": "스파크플러스", "description": "대표 코워킹", "location": "서울 강남구", "website": "https://www.sparkplus.co.kr", "focus": "스타트업", "source": "Manual Data"},
    {"name": "마루180", "description": "창업허브 코워킹", "location": "서울 마포구", "website": "https://maru180.com", "focus": "창업", "source": "Manual Data"},
    {"name": "판교테크노밸리", "description": "IT 클러스터", "location": "경기 성남시", "website": "https://www.pangyo.or.kr", "focus": "IT, 바이오", "source": "Manual Data"},
]


def run_rss_crawler() -> Dict[str, Any]:
    """RSS 크롤러 실행 후 한국 생태계 데이터 구조로 반환"""
    logger.info("RSS 기반 한국 스타트업 크롤러 시작")

    startups = crawl_rss_sources(max_entries_per_feed=150)

    acc = []
    for a in MANUAL_ACCELERATORS:
        a = dict(a)
        a["type"] = "accelerator"
        a["country"] = "한국"
        a["crawled_at"] = datetime.now().isoformat()
        acc.append(a)

    cow = []
    for c in MANUAL_COWORKING:
        c = dict(c)
        c["type"] = "coworking_space"
        c["country"] = "한국"
        c["crawled_at"] = datetime.now().isoformat()
        cow.append(c)

    # 수동 스타트업 일부 (RSS와 중복 제거용으로 이름만 참고)
    manual_startups = [
        {"name": "카카오", "description": "모바일 플랫폼", "location": "제주", "website": "https://www.kakaocorp.com", "category": "플랫폼", "source": "Manual Data"},
        {"name": "네이버", "description": "인터넷 포털", "location": "성남", "website": "https://www.naver.com", "category": "플랫폼", "source": "Manual Data"},
        {"name": "쿠팡", "description": "이커머스", "location": "서울", "website": "https://www.coupang.com", "category": "이커머스", "source": "Manual Data"},
        {"name": "토스", "description": "핀테크", "location": "서울", "website": "https://www.toss.im", "category": "핀테크", "source": "Manual Data"},
        {"name": "당근마켓", "description": "중고거래", "location": "서울", "website": "https://www.daangn.com", "category": "중고거래", "source": "Manual Data"},
    ]
    for s in manual_startups:
        s["type"] = "startup"
        s["country"] = "한국"
        s["crawled_at"] = datetime.now().isoformat()

    # 수동 스타트업은 이름 중복 없을 때만 추가
    startup_names = {x["name"].lower() for x in startups}
    for s in manual_startups:
        if s["name"].lower() not in startup_names:
            startups.append(s)
            startup_names.add(s["name"].lower())

    data = {
        "startups": startups,
        "investors": [],
        "accelerators": acc,
        "coworking_spaces": cow,
        "news": [],
        "crawled_at": datetime.now().isoformat(),
        "statistics": {
            "total_startups": len(startups),
            "total_investors": 0,
            "total_accelerators": len(acc),
            "total_coworking_spaces": len(cow),
            "total_news": 0,
            "total_entities": len(startups) + len(acc) + len(cow),
        },
    }

    logger.info("RSS 크롤링 완료: 스타트업 %d, 액셀러레이터 %d, 코워킹 %d", len(startups), len(acc), len(cow))
    return data


def save_data(data: Dict[str, Any], dir_path: str = "data") -> str:
    """data 디렉토리에 JSON 저장"""
    import os
    os.makedirs(dir_path, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(dir_path, f"korean_ecosystem_data_rss_{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("저장 완료: %s", path)
    return path


if __name__ == "__main__":
    result = run_rss_crawler()
    save_data(result)
