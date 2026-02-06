#!/usr/bin/env python3
"""
투자자 포트폴리오 분석 및 투자 성향 추출
더브이씨(THE VC)에서 각 투자자의 포트폴리오를 크롤링하고 투자 성향을 분석하여 데이터에 추가합니다.

실행: cd data-pipeline && python analyze_investor_portfolios.py
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


def main():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    latest_path = os.path.join(data_dir, "korean_ecosystem_data_latest.json")
    
    if not os.path.isfile(latest_path):
        logger.error("최신 데이터 없음. 먼저 run_bulk_crawler.py 를 실행하세요.")
        return 1
    
    # 기존 데이터 로드
    with open(latest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    investors = data.get("investors", [])
    if not investors:
        logger.warning("분석할 투자자 데이터가 없습니다.")
        return 1
    
    logger.info(f"투자자 포트폴리오 분석 시작: {len(investors)}건")
    
    # 포트폴리오 분석 (최대 50건, 시간 절약을 위해)
    try:
        from crawlers.investor_portfolio_analyzer import analyze_investors_portfolio
        
        # 이미 분석된 투자자는 제외 (portfolio_count가 있으면 이미 분석됨)
        to_analyze = [inv for inv in investors if not inv.get("portfolio_count", 0)]
        already_analyzed = [inv for inv in investors if inv.get("portfolio_count", 0)]
        
        logger.info(f"이미 분석됨: {len(already_analyzed)}건, 분석 필요: {len(to_analyze)}건")
        
        if to_analyze:
            # 시간 절약을 위해 최대 20건만 분석 (필요시 늘릴 수 있음)
            analyzed = analyze_investors_portfolio(to_analyze, max_analyze=min(20, len(to_analyze)))
            
            # 분석 결과를 기존 데이터에 반영
            investor_map = {inv.get("slug") or inv.get("name", "").lower(): inv for inv in investors}
            for inv in analyzed:
                slug = inv.get("slug") or inv.get("name", "").lower()
                if slug in investor_map:
                    investor_map[slug].update({
                        "portfolio": inv.get("portfolio", []),
                        "investment_focus": inv.get("investment_focus", []),
                        "preferred_stages": inv.get("preferred_stages", []),
                        "portfolio_count": inv.get("portfolio_count", 0),
                    })
            
            data["investors"] = list(investor_map.values())
        else:
            logger.info("모든 투자자가 이미 분석되었습니다.")
    
    except Exception as e:
        logger.error(f"포트폴리오 분석 실패: {e}", exc_info=True)
        return 1
    
    # 분석 결과 저장
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    analyzed_path = os.path.join(data_dir, f"korean_ecosystem_data_analyzed_{ts}.json")
    with open(analyzed_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"분석 결과 저장: {analyzed_path}")
    
    # 최신 데이터도 업데이트
    with open(analyzed_path, "r", encoding="utf-8") as f:
        with open(latest_path, "w", encoding="utf-8") as g:
            g.write(f.read())
    logger.info(f"최신 데이터 업데이트: {latest_path}")
    
    # 프론트엔드용 JSON 생성
    try:
        from export_for_frontend import main as export_main
        export_main()
        logger.info("프론트엔드 데이터 갱신 완료")
    except Exception as e:
        logger.warning(f"프론트엔드 내보내기 건너뜀: {e}")
    
    # 분석 결과 요약
    analyzed_investors = [inv for inv in data.get("investors", []) if inv.get("portfolio_count", 0) > 0]
    logger.info(f"\n=== 분석 결과 요약 ===")
    logger.info(f"포트폴리오 분석 완료: {len(analyzed_investors)}건")
    
    # 투자 성향 통계
    focus_counter = {}
    for inv in analyzed_investors:
        for focus in inv.get("investment_focus", []):
            focus_counter[focus] = focus_counter.get(focus, 0) + 1
    
    logger.info(f"\n주요 투자 성향:")
    for focus, count in sorted(focus_counter.items(), key=lambda x: x[1], reverse=True)[:10]:
        logger.info(f"  {focus}: {count}개 투자자")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
