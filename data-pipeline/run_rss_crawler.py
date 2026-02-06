#!/usr/bin/env python3
"""
RSS 전용 크롤러 실행 (Playwright 불필요)
실패 가능성이 낮고 빠르게 동작합니다.
"""

import json
import logging
import os
import sys

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def main():
    from crawlers.rss_ecosystem_crawler import run_rss_crawler, save_data
    from crawlers.public_data_loader import load_csv_dir, merge_into_ecosystem

    os.makedirs("data", exist_ok=True)

    logger.info("📡 RSS 기반 크롤링 시작 (Playwright 미사용)")
    data = run_rss_crawler()

    # 그룹바이(groupby.kr) 스타트업 채용 목록 병합
    try:
        from crawlers.groupby_crawler import run_groupby_crawler
        groupby_list = run_groupby_crawler()
        if groupby_list:
            existing_names = {s.get("name", "").lower() for s in data.get("startups", [])}
            for s in groupby_list:
                if (s.get("name") or "").lower() not in existing_names:
                    data["startups"].append(s)
                    existing_names.add((s.get("name") or "").lower())
            data["statistics"]["total_startups"] = len(data["startups"])
            data["statistics"]["total_entities"] = (
                len(data["startups"]) + len(data.get("accelerators", [])) + len(data.get("coworking_spaces", []))
            )
            logger.info("그룹바이 %d건 병합", len(groupby_list))
    except Exception as e:
        logger.warning("그룹바이 크롤러 건너뜀: %s", e)

    # data/ 폴더에 K-STARTUP 등 CSV가 있으면 병합
    public_items = load_csv_dir("data", pattern="K_STARTUP")
    if public_items:
        data = merge_into_ecosystem(public_items, data)

    # 더브이씨(THE VC) 투자자 목록 병합
    data.setdefault("investors", [])
    try:
        from crawlers.thevc_crawler import run_thevc_crawler
        thevc_list = run_thevc_crawler()
        if thevc_list:
            existing_inv = {(i.get("website") or "").strip() for i in data.get("investors", [])}
            for inv in thevc_list:
                if (inv.get("website") or "").strip() not in existing_inv:
                    data["investors"].append(inv)
                    existing_inv.add((inv.get("website") or "").strip())
            logger.info("더브이씨 투자자 %d건 병합", len(thevc_list))
    except Exception as e:
        logger.warning("더브이씨 크롤러 건너뜀: %s", e)

    if data.get("statistics") is not None:
        data["statistics"]["total_investors"] = len(data.get("investors", []))
        data["statistics"]["total_entities"] = (
            len(data["startups"]) + len(data.get("accelerators", []))
            + len(data.get("coworking_spaces", [])) + len(data.get("investors", []))
        )

    # export_for_frontend가 읽는 data-pipeline/data 에 저장
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    path = save_data(data, dir_path=data_dir)
    # 프론트엔드에서 참조하기 쉬우도록 최신 파일 복사
    latest_path = os.path.join(data_dir, "korean_ecosystem_data_latest.json")
    with open(path, "r", encoding="utf-8") as f:
        with open(latest_path, "w", encoding="utf-8") as g:
            g.write(f.read())
    logger.info("최신 데이터 복사: %s", latest_path)

    # 프론트엔드용 JSON 생성 (lat/lon 포함)
    try:
        from export_for_frontend import main as export_main
        export_main()
    except Exception as e:
        logger.warning("프론트엔드 내보내기 건너뜀: %s", e)

    stats = data.get("statistics", {})
    logger.info(
        "✅ 완료 - 스타트업 %d, 액셀러레이터 %d, 코워킹 %d, 투자자 %d (총 %d)",
        stats.get("total_startups", 0),
        stats.get("total_accelerators", 0),
        stats.get("total_coworking_spaces", 0),
        stats.get("total_investors", 0),
        stats.get("total_entities", 0),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
