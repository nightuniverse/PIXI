#!/usr/bin/env python3
"""
투자자·액셀러레이터 대량 크롤링 후 지도용 JSON 생성
- 더브이씨(THE VC) 투자자 전량 수집 (스크롤)
- 액셀러레이터 확장 목록 병합
- 완료 후 export_for_frontend → frontend/public/data/koreanEcosystemData.json 갱신 → 지도에 표시

실행: cd data-pipeline && python run_bulk_crawler.py
"""

import json
import logging
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# 대량 크롤용 액셀러레이터/벤처캐피탈 확장 목록 (한국 주요 기관)
BULK_ACCELERATORS = [
    {"name": "더벤처스", "description": "한국 대표 벤처캐피탈", "location": "서울", "website": "https://www.theventures.co.kr", "focus": "IT, 바이오, 게임", "source": "Bulk Data"},
    {"name": "스마일게이트인베스트먼트", "description": "게임/IT 투자", "location": "서울", "website": "https://www.smilegate.com", "focus": "게임, IT", "source": "Bulk Data"},
    {"name": "네이버 D2SF", "description": "네이버 스타트업 지원", "location": "성남", "website": "https://d2.naver.com", "focus": "AI, 빅데이터", "source": "Bulk Data"},
    {"name": "카카오벤처스", "description": "카카오 벤처캐피탈", "location": "제주", "website": "https://ventures.kakao.com", "focus": "모바일, AI", "source": "Bulk Data"},
    {"name": "LG노트", "description": "LG 스타트업 지원", "location": "서울", "website": "https://www.lgnot.com", "focus": "IoT, AI", "source": "Bulk Data"},
    {"name": "스파크랩", "description": "네이버 액셀러레이터", "location": "성남", "website": "https://sparklab.co.kr", "focus": "AI, 모바일", "source": "Bulk Data"},
    {"name": "벤처스퀘어", "description": "액셀러레이터/코워킹", "location": "서울", "website": "https://venturesquare.net", "focus": "창업 지원", "source": "Bulk Data"},
    {"name": "플러스엑스", "description": "LG 액셀러레이터", "location": "서울", "website": "https://plusx.co.kr", "focus": "IoT, AI", "source": "Bulk Data"},
    {"name": "은행권청년창업재단(D·CAM)", "description": "은행권 청년창업 지원", "location": "서울", "website": "https://www.dcamp.kr", "focus": "팁스, 시드", "source": "Bulk Data"},
    {"name": "블루포인트파트너스", "description": "액셀러레이터, 팁스 운영", "location": "서울", "website": "https://www.bluepointpartners.co.kr", "focus": "시드, Pre-A", "source": "Bulk Data"},
    {"name": "스톤브릿지벤처스", "description": "벤처캐피탈", "location": "서울", "website": "https://www.stonebridgevc.com", "focus": "성장투자", "source": "Bulk Data"},
    {"name": "포스코홀딩스", "description": "대기업 벤처투자", "location": "서울", "website": "https://www.poscoholdings.com", "focus": "팁스, 스타트업", "source": "Bulk Data"},
    {"name": "엘에이치벤처스", "description": "LH 벤처캐피탈", "location": "서울", "website": "https://www.lhventures.co.kr", "focus": "부동산·건설 테크", "source": "Bulk Data"},
    {"name": "한국산업기술진흥원", "description": "산업기술 창업 지원", "location": "서울", "website": "https://www.kiat.or.kr", "focus": "기술창업", "source": "Bulk Data"},
    {"name": "중소벤처기업부 창업진흥원", "description": "창업 생태계 지원", "location": "서울", "website": "https://www.kised.or.kr", "focus": "창업교육, 액셀러레이터", "source": "Bulk Data"},
    {"name": "티엔엔벤처스", "description": "벤처캐피탈", "location": "서울", "website": "https://www.tnnvc.com", "focus": "IT, 헬스케어", "source": "Bulk Data"},
    {"name": "파트너스인베스트먼트", "description": "벤처캐피탈", "location": "서울", "website": "https://www.partnersinv.com", "focus": "성장투자", "source": "Bulk Data"},
    {"name": "인터베스트", "description": "벤처캐피탈", "location": "서울", "website": "https://www.intervest.co.kr", "focus": "IT, 바이오", "source": "Bulk Data"},
    {"name": "LB인베스트먼트", "description": "벤처캐피탈", "location": "서울", "website": "https://www.lbinv.co.kr", "focus": "성장투자", "source": "Bulk Data"},
    {"name": "미래에셋벤처스", "description": "미래에셋 벤처투자", "location": "서울", "website": "https://www.miraeassetventures.com", "focus": "금융테크, IT", "source": "Bulk Data"},
    {"name": "솔로몬투자자문", "description": "벤처·사모투자", "location": "서울", "website": "https://www.solomon.co.kr", "focus": "성장·매출", "source": "Bulk Data"},
    {"name": "부릉", "description": "모빌리티·물류 투자", "location": "서울", "website": "https://www.burung.co.kr", "focus": "모빌리티", "source": "Bulk Data"},
    {"name": "코리아크레딧뷰로", "description": "금융·신용 데이터", "location": "서울", "website": "https://www.kcb.co.kr", "focus": "핀테크", "source": "Bulk Data"},
    {"name": "한국벤처캐피탈", "description": "모태펀드·벤처투자", "location": "서울", "website": "https://www.kvca.or.kr", "focus": "생태계", "source": "Bulk Data"},
    {"name": "고려대학교 창업스튜디오", "description": "대학 창업 지원", "location": "서울", "website": "https://startup.korea.ac.kr", "focus": "대학창업", "source": "Bulk Data"},
    {"name": "연세대학교 창업교육원", "description": "대학 창업 지원", "location": "서울", "website": "https://startup.yonsei.ac.kr", "focus": "대학창업", "source": "Bulk Data"},
    {"name": "서울대학교 창업지원", "description": "대학 창업 지원", "location": "서울", "website": "https://startup.snu.ac.kr", "focus": "대학창업", "source": "Bulk Data"},
    {"name": "KAIST 창업원", "description": "대학 창업 지원", "location": "대전", "website": "https://startup.kaist.ac.kr", "focus": "테크창업", "source": "Bulk Data"},
    {"name": "POSTECH 창업지원", "description": "대학 창업 지원", "location": "포항", "website": "https://startup.postech.ac.kr", "focus": "테크창업", "source": "Bulk Data"},
    {"name": "경기창조경제혁신센터", "description": "지역 창업 허브", "location": "경기 성남시", "website": "https://www.gcck.or.kr", "focus": "지역창업", "source": "Bulk Data"},
    {"name": "서울창업허브", "description": "서울시 창업 지원", "location": "서울", "website": "https://www.seoulstartuphub.org", "focus": "시드, 액셀러레이팅", "source": "Bulk Data"},
    {"name": "부산창업허브", "description": "부산시 창업 지원", "location": "부산", "website": "https://www.busanstartuphub.kr", "focus": "지역창업", "source": "Bulk Data"},
    {"name": "인천창업허브", "description": "인천시 창업 지원", "location": "인천", "website": "https://www.icstartup.kr", "focus": "지역창업", "source": "Bulk Data"},
    {"name": "대전창업허브", "description": "대전시 창업 지원", "location": "대전", "website": "https://www.djstartup.kr", "focus": "지역창업", "source": "Bulk Data"},
    {"name": "광주창업허브", "description": "광주시 창업 지원", "location": "광주", "website": "https://www.gjstartup.kr", "focus": "지역창업", "source": "Bulk Data"},
    {"name": "엠와이소셜컴퍼니", "description": "액셀러레이터, 팁스 운영", "location": "서울", "website": "https://www.mysocialcompany.kr", "focus": "시드, Pre-A", "source": "Bulk Data"},
    {"name": "아이비엑스파트너스", "description": "사모투자회사", "location": "서울", "website": "https://www.ibxpartners.co.kr", "focus": "성장투자", "source": "Bulk Data"},
    {"name": "오티엄캐피탈", "description": "사모투자회사", "location": "서울", "website": "https://www.otiumcapital.com", "focus": "성장·매출", "source": "Bulk Data"},
    {"name": "벡터기술투자", "description": "벤처캐피탈", "location": "서울", "website": "https://www.vectorti.co.kr", "focus": "테크", "source": "Bulk Data"},
    {"name": "아시아투지캐피탈", "description": "벤처캐피탈", "location": "서울", "website": "https://www.asia2g.com", "focus": "성장투자", "source": "Bulk Data"},
    {"name": "엘에프인베스트먼트", "description": "기업벤처캐피탈", "location": "서울", "website": "https://www.lfinvestment.co.kr", "focus": "기업VC", "source": "Bulk Data"},
]


def main():
    os.makedirs("data", exist_ok=True)

    logger.info("=== 투자자·액셀러레이터 대량 크롤링 시작 ===")

    # 1) RSS 기반 스타트업 + 기본 액셀러레이터/코워킹
    from crawlers.rss_ecosystem_crawler import run_rss_crawler, save_data
    from crawlers.public_data_loader import load_csv_dir, merge_into_ecosystem

    data = run_rss_crawler()

    # 2) 그룹바이 스타트업 병합
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
            logger.info("그룹바이 %d건 병합", len(groupby_list))
    except Exception as e:
        logger.warning("그룹바이 크롤러 건너뜀: %s", e)

    # 3) 공공데이터 CSV 병합
    public_items = load_csv_dir("data", pattern="K_STARTUP")
    if public_items:
        data = merge_into_ecosystem(public_items, data)

    # 4) 더브이씨 투자자 전량 크롤 (스크롤로 대량 수집)
    data.setdefault("investors", [])
    try:
        from crawlers.thevc_crawler import run_thevc_crawler
        thevc_list = run_thevc_crawler(bulk_mode=True)
        if thevc_list:
            existing_inv = {(i.get("website") or "").strip() for i in data.get("investors", [])}
            for inv in thevc_list:
                if (inv.get("website") or "").strip() not in existing_inv:
                    data["investors"].append(inv)
                    existing_inv.add((inv.get("website") or "").strip())
            logger.info("더브이씨 투자자 대량 병합: %d건", len(thevc_list))
    except Exception as e:
        logger.warning("더브이씨 크롤러 건너뜀: %s", e)

    # 5) 액셀러레이터 확장 목록 병합 (이름 기준 중복 제외)
    existing_acc_names = {a.get("name", "").strip().lower() for a in data.get("accelerators", [])}
    for a in BULK_ACCELERATORS:
        entry = dict(a)
        entry["type"] = "accelerator"
        entry["country"] = "한국"
        entry["crawled_at"] = datetime.now().isoformat()
        if (entry.get("name") or "").strip().lower() not in existing_acc_names:
            data["accelerators"].append(entry)
            existing_acc_names.add((entry.get("name") or "").strip().lower())
    logger.info("액셀러레이터 확장 병합: 총 %d건", len(data["accelerators"]))

    # 통계 갱신
    if data.get("statistics") is not None:
        data["statistics"]["total_investors"] = len(data.get("investors", []))
        data["statistics"]["total_accelerators"] = len(data.get("accelerators", []))
        data["statistics"]["total_entities"] = (
            len(data["startups"]) + len(data.get("accelerators", []))
            + len(data.get("coworking_spaces", [])) + len(data.get("investors", []))
        )

    # 6) data-pipeline/data 에 저장
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    path = save_data(data, dir_path=data_dir)
    latest_path = os.path.join(data_dir, "korean_ecosystem_data_latest.json")
    with open(path, "r", encoding="utf-8") as f:
        with open(latest_path, "w", encoding="utf-8") as g:
            g.write(f.read())
    logger.info("최신 데이터 복사: %s", latest_path)

    # 7) 프론트엔드용 JSON 생성 → 지도에 표시
    try:
        from export_for_frontend import main as export_main
        export_main()
    except Exception as e:
        logger.warning("프론트엔드 내보내기 건너뜀: %s", e)

    stats = data.get("statistics", {})
    logger.info(
        "✅ 대량 크롤링 완료 - 스타트업 %d, 액셀러레이터 %d, 코워킹 %d, 투자자 %d (총 %d)",
        stats.get("total_startups", 0),
        stats.get("total_accelerators", 0),
        stats.get("total_coworking_spaces", 0),
        stats.get("total_investors", 0),
        stats.get("total_entities", 0),
    )
    logger.info("지도 데이터: frontend/public/data/koreanEcosystemData.json 갱신됨. 브라우저에서 /explore 새로고침하면 반영됩니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
