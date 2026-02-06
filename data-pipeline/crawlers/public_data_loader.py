#!/usr/bin/env python3
"""
공공데이터포털(data.go.kr) CSV 로더
data/ 폴더에 넣은 CSV를 읽어 스타트업/뉴스 항목으로 변환.
다운로드: https://www.data.go.kr/data/15122759/fileData.do (K-STARTUP 창업소식)
"""

import csv
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_csv_dir(data_dir: str = "data", pattern: str = "K_STARTUP") -> List[Dict[str, Any]]:
    """data 디렉터리에서 K-STARTUP 등 CSV 파일 찾아 로드"""
    items = []
    if not os.path.isdir(data_dir):
        return items

    for name in os.listdir(data_dir):
        if not name.endswith(".csv") or pattern.lower() not in name.lower():
            continue
        path = os.path.join(data_dir, name)
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    title = (row.get("게시물 제목") or row.get("제목") or "").strip()
                    url = (row.get("인터넷주소(URL)") or row.get("URL") or "").strip()
                    content = (row.get("내용") or row.get("내용") or "").strip()[:500]
                    date = (row.get("게시물 등록일자") or row.get("등록일자") or "").strip()
                    if not title:
                        continue
                    items.append({
                        "name": title[:200],
                        "description": content,
                        "website": url or "#",
                        "category": "창업소식",
                        "source": "K-STARTUP(공공데이터)",
                        "type": "startup",
                        "country": "한국",
                        "location": "서울",  # 공공데이터에는 주소 없음, 지도 표시용 기본값
                        "published": date,
                        "crawled_at": datetime.now().isoformat(),
                    })
            logger.info("공공데이터 CSV 로드: %s (%d건)", name, len(items))
        except Exception as e:
            logger.warning("CSV 로드 실패 %s: %s", name, e)

    return items


def merge_into_ecosystem(public_items: List[Dict], existing_data: Dict[str, Any]) -> Dict[str, Any]:
    """공공데이터 항목을 기존 생태계 데이터에 병합 (중복 제목 제외)"""
    existing_titles = {s.get("name", "").lower() for s in existing_data.get("startups", [])}
    added = 0
    for item in public_items:
        if item.get("name", "").lower() in existing_titles:
            continue
        existing_data["startups"].append(item)
        existing_titles.add(item.get("name", "").lower())
        added += 1
    if added:
        stats = existing_data.get("statistics", {})
        stats["total_startups"] = len(existing_data["startups"])
        stats["total_entities"] = (
            len(existing_data["startups"])
            + len(existing_data.get("accelerators", []))
            + len(existing_data.get("coworking_spaces", []))
        )
        logger.info("공공데이터 %d건 병합", added)
    return existing_data
