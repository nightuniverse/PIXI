#!/usr/bin/env python3
"""
크롤링 결과를 프론트엔드용 JSON으로 변환 (lat/lon 추가)
실행: python export_for_frontend.py
출력: frontend/public/data/koreanEcosystemData.json
"""

import json
import os
import re

# 위치 -> (lat, lon) 기본값 (한국) — 그룹바이 등 크롤링에서 나오는 지역 보강
LOCATION_COORDS = {
    "서울": (37.5665, 126.9780),
    "서울 강남구": (37.4979, 127.0276),
    "서울 서초구": (37.4837, 127.0324),
    "서울 마포구": (37.5663, 126.9019),
    "서울 구로구": (37.4954, 126.8874),
    "서울 강서구": (37.5509, 126.8495),
    "서울 관악구": (37.4784, 126.9516),
    "서울 금천구": (37.4563, 126.8956),
    "서울 중구": (37.5636, 126.9976),
    "서울 동대문구": (37.5744, 127.0396),
    "서울 영등포구": (37.5264, 126.8962),
    "서울 종로구": (37.5735, 126.9788),
    "서울 성동구": (37.5634, 127.0371),
    "서울 광진구": (37.5385, 127.0822),
    "서울 용산구": (37.5384, 126.9654),
    "서울 송파구": (37.5145, 127.1059),
    "서울 강동구": (37.5301, 127.1238),
    "성남": (37.3594, 127.1053),
    "경기 성남시": (37.3594, 127.1053),
    "경기도 성남시": (37.3594, 127.1053),
    "경기 용인시": (37.2411, 127.1776),
    "경기 평택시": (36.9921, 127.1129),
    "경기 부천시": (37.5034, 126.7660),
    "경기 고양시": (37.6584, 126.8320),
    "경기 안양시": (37.3943, 126.9568),
    "경기": (37.4138, 127.5183),
    "대전 유성구": (36.3624, 127.3565),
    "강원 고성군": (38.3809, 128.4675),
    "제주": (33.4996, 126.5312),
    "부산": (35.1796, 129.0756),
    "인천": (37.4563, 126.7052),
    "대구": (35.8714, 128.6014),
    "대전": (36.3504, 127.3845),
    "광주": (35.1595, 126.8526),
    "광주 북구": (35.1742, 126.9120),
    "포항": (36.0190, 129.3435),
    "원격근무": (37.5665, 126.9780),
    "신규기업": (37.5665, 126.9780),
    "한국": (37.5665, 126.9780),
}
DEFAULT_COORD = (37.5665, 126.9780)


def get_coord(location: str) -> tuple:
    if not location:
        return DEFAULT_COORD
    loc = (location or "").strip()
    return LOCATION_COORDS.get(loc) or LOCATION_COORDS.get(loc.split()[0]) or DEFAULT_COORD


def entity_to_frontend(item: dict, idx: int, id_offset: int) -> dict:
    lat, lon = get_coord(item.get("location") or item.get("city"))
    name = (item.get("name") or "").strip()
    # HTML 엔티티 제거
    name = re.sub(r"&#\d+;", "", name)
    
    # 투자자/액셀러레이터가 같은 좌표에 몰리지 않도록 인덱스 기반으로 약간 분산
    entity_type = item.get("type") or "startup"
    if entity_type in ("investor", "accelerator"):
        # 서울 주요 구별 좌표를 순환 배치 (강남구, 서초구, 마포구, 종로구, 중구, 영등포구, 송파구, 강동구)
        seoul_districts = [
            (37.4979, 127.0276),  # 강남구
            (37.4837, 127.0324),  # 서초구
            (37.5663, 126.9019),  # 마포구
            (37.5735, 126.9788),  # 종로구
            (37.5636, 126.9976),  # 중구
            (37.5264, 126.8962),  # 영등포구
            (37.5145, 127.1059),  # 송파구
            (37.5301, 127.1238),  # 강동구
        ]
        # location이 "서울"만 있거나 기본 좌표와 같으면 분산 배치
        if (lat, lon) == DEFAULT_COORD or (item.get("location") or "").strip() == "서울":
            district_idx = idx % len(seoul_districts)
            lat, lon = seoul_districts[district_idx]
    
    # category 설정: 타입에 따라 기본값 다르게
    category = item.get("category") or item.get("focus") or ""
    if not category:
        if entity_type == "investor":
            category = "투자자"
        elif entity_type == "accelerator":
            category = "액셀러레이터"
        elif entity_type == "coworking_space":
            category = "코워킹"
        else:
            category = "스타트업"
    
    result = {
        "id": id_offset + idx,
        "name": name[:200],
        "description": (item.get("description") or "")[:500],
        "website": item.get("website") or "",
        "category": category,
        "source": item.get("source") or "",
        "type": entity_type,
        "country": item.get("country") or "한국",
        "location": item.get("location") or item.get("city") or "서울",
        "lat": lat,
        "lon": lon,
    }
    
    # 투자자인 경우 포트폴리오 정보 추가
    if entity_type == "investor":
        if item.get("investment_focus"):
            result["investment_focus"] = item.get("investment_focus", [])
        if item.get("preferred_stages"):
            result["preferred_stages"] = item.get("preferred_stages", [])
        if item.get("portfolio_count", 0) > 0:
            result["portfolio_count"] = item.get("portfolio_count", 0)
    
    return result


def main():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    latest_path = os.path.join(data_dir, "korean_ecosystem_data_latest.json")
    if not os.path.isfile(latest_path):
        print("최신 데이터 없음. 먼저 run_rss_crawler.py 를 실행하세요.")
        return 1

    with open(latest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    out = {"startups": [], "accelerators": [], "coworking_spaces": [], "investors": []}

    for i, s in enumerate(data.get("startups", [])):
        out["startups"].append(entity_to_frontend(s, i, 1))

    for i, a in enumerate(data.get("accelerators", [])):
        out["accelerators"].append(entity_to_frontend(a, i, 101))

    for i, c in enumerate(data.get("coworking_spaces", [])):
        out["coworking_spaces"].append(entity_to_frontend(c, i, 201))

    for i, inv in enumerate(data.get("investors", [])):
        out["investors"].append(entity_to_frontend(inv, i, 301))

    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "data")
    os.makedirs(frontend_dir, exist_ok=True)
    out_path = os.path.join(frontend_dir, "koreanEcosystemData.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("저장 완료:", out_path)
    print("스타트업:", len(out["startups"]), "액셀러레이터:", len(out["accelerators"]), "코워킹:", len(out["coworking_spaces"]), "투자자:", len(out["investors"]))
    return 0


if __name__ == "__main__":
    exit(main())
