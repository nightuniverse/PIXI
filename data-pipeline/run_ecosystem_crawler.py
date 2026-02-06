#!/usr/bin/env python3
"""
스타트업 생태계 탐색 통합 크롤러 실행 스크립트
전체 생태계와 한국 생태계 데이터를 수집합니다.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ecosystem_crawler_run.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def run_global_ecosystem_crawler():
    """전체 생태계 크롤러 실행"""
    logger.info("🌍 전체 생태계 크롤러 실행 시작")
    
    try:
        from crawlers.ecosystem_crawler import EcosystemCrawler
        
        async with EcosystemCrawler() as crawler:
            ecosystem_data = await crawler.crawl_all_sources()
            filename = crawler.save_data()
            
            if filename:
                logger.info(f"✅ 전체 생태계 크롤링 완료: {filename}")
                return ecosystem_data
            else:
                logger.error("❌ 전체 생태계 데이터 저장 실패")
                return None
                
    except Exception as e:
        logger.error(f"전체 생태계 크롤러 실행 실패: {e}")
        return None

async def run_korean_ecosystem_crawler():
    """한국 생태계 크롤러 실행"""
    logger.info("🇰🇷 한국 생태계 크롤러 실행 시작")
    
    try:
        from crawlers.korean_ecosystem_crawler import KoreanEcosystemCrawler
        
        async with KoreanEcosystemCrawler() as crawler:
            korean_ecosystem_data = await crawler.crawl_all_korean_sources()
            filename = crawler.save_data()
            
            if filename:
                logger.info(f"✅ 한국 생태계 크롤링 완료: {filename}")
                return korean_ecosystem_data
            else:
                logger.error("❌ 한국 생태계 데이터 저장 실패")
                return None
                
    except Exception as e:
        logger.error(f"한국 생태계 크롤러 실행 실패: {e}")
        return None

def merge_ecosystem_data(global_data: Dict[str, Any], korean_data: Dict[str, Any]) -> Dict[str, Any]:
    """전체 생태계와 한국 생태계 데이터 통합"""
    logger.info("🔄 생태계 데이터 통합 시작")
    
    merged_data = {
        'global_ecosystem': global_data,
        'korean_ecosystem': korean_data,
        'merged_at': datetime.now().isoformat()
    }
    
    # 통합 통계 계산
    if global_data and korean_data:
        global_stats = global_data.get('statistics', {})
        korean_stats = korean_data.get('statistics', {})
        
        merged_stats = {
            'global_total_entities': global_stats.get('total_entities', 0),
            'korean_total_entities': korean_stats.get('total_entities', 0),
            'total_unique_startups': len(set(
                [s['name'].lower() for s in global_data.get('startups', [])] +
                [s['name'].lower() for s in korean_data.get('startups', [])]
            )),
            'total_unique_investors': len(set(
                [i['name'].lower() for i in global_data.get('investors', [])] +
                [i['name'].lower() for i in korean_data.get('investors', [])]
            )),
            'total_unique_accelerators': len(set(
                [a['name'].lower() for a in global_data.get('accelerators', [])] +
                [a['name'].lower() for a in korean_data.get('accelerators', [])]
            )),
            'total_unique_coworking_spaces': len(set(
                [c['name'].lower() for c in global_data.get('coworking_spaces', [])] +
                [c['name'].lower() for c in korean_data.get('coworking_spaces', [])]
            )),
            'total_unique_events': len(set(
                [e['name'].lower() for e in global_data.get('events', [])] +
                [e['name'].lower() for e in korean_data.get('events', [])]
            ))
        }
        
        merged_data['merged_statistics'] = merged_stats
        logger.info(f"통합 통계 계산 완료: 총 {merged_stats['total_unique_startups']}개 고유 스타트업")
    
    return merged_data

def save_merged_data(merged_data: Dict[str, Any], filename: str = None):
    """통합 데이터를 파일로 저장"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"merged_ecosystem_data_{timestamp}.json"
    
    filepath = f"data/{filename}"
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"통합 데이터 저장 완료: {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"통합 데이터 저장 실패: {e}")
        return None

def generate_summary_report(merged_data: Dict[str, Any]):
    """크롤링 결과 요약 리포트 생성"""
    logger.info("📊 크롤링 결과 요약 리포트 생성")
    
    if not merged_data:
        logger.warning("요약 리포트 생성 실패: 데이터가 없습니다")
        return
    
    global_data = merged_data.get('global_ecosystem', {})
    korean_data = merged_data.get('korean_ecosystem', {})
    merged_stats = merged_data.get('merged_statistics', {})
    
    print("\n" + "="*80)
    print("🚀 스타트업 생태계 탐색 크롤링 결과 요약")
    print("="*80)
    
    if global_data:
        global_stats = global_data.get('statistics', {})
        print(f"\n🌍 전체 생태계 데이터:")
        print(f"   - 스타트업: {global_stats.get('total_startups', 0):,}개")
        print(f"   - 투자자: {global_stats.get('total_investors', 0):,}개")
        print(f"   - 액셀러레이터: {global_stats.get('total_accelerators', 0):,}개")
        print(f"   - 코워킹 스페이스: {global_stats.get('total_coworking_spaces', 0):,}개")
        print(f"   - 이벤트: {global_stats.get('total_events', 0):,}개")
        print(f"   - 총 엔티티: {global_stats.get('total_entities', 0):,}개")
    
    if korean_data:
        korean_stats = korean_data.get('statistics', {})
        print(f"\n🇰🇷 한국 생태계 데이터:")
        print(f"   - 스타트업: {korean_stats.get('total_startups', 0):,}개")
        print(f"   - 투자자: {korean_stats.get('total_investors', 0):,}개")
        print(f"   - 액셀러레이터: {korean_stats.get('total_accelerators', 0):,}개")
        print(f"   - 코워킹 스페이스: {korean_stats.get('total_coworking_spaces', 0):,}개")
        print(f"   - 뉴스: {korean_stats.get('total_news', 0):,}개")
        print(f"   - 총 엔티티: {korean_stats.get('total_entities', 0):,}개")
    
    if merged_stats:
        print(f"\n🔄 통합 데이터 요약:")
        print(f"   - 고유 스타트업: {merged_stats.get('total_unique_startups', 0):,}개")
        print(f"   - 고유 투자자: {merged_stats.get('total_unique_investors', 0):,}개")
        print(f"   - 고유 액셀러레이터: {merged_stats.get('total_unique_accelerators', 0):,}개")
        print(f"   - 고유 코워킹 스페이스: {merged_stats.get('total_unique_coworking_spaces', 0):,}개")
        print(f"   - 고유 이벤트: {merged_stats.get('total_unique_events', 0):,}개")
    
    print(f"\n📅 크롤링 완료 시간: {merged_data.get('merged_at', 'Unknown')}")
    print("="*80)

def run_rss_korean_crawler():
    """RSS 전용 한국 크롤러 (Playwright 불필요, 안정적)"""
    logger.info("📡 RSS 기반 한국 크롤러 실행 (우선 시도)")
    try:
        from crawlers.rss_ecosystem_crawler import run_rss_crawler
        from crawlers.public_data_loader import load_csv_dir, merge_into_ecosystem
        data = run_rss_crawler()
        public_items = load_csv_dir("data", pattern="K_STARTUP")
        if public_items:
            data = merge_into_ecosystem(public_items, data)
        return data
    except Exception as e:
        logger.warning("RSS 크롤러 실패: %s", e)
        return None


async def main():
    """메인 함수"""
    logger.info("🚀 스타트업 생태계 탐색 통합 크롤러 시작")
    
    # 데이터 디렉토리 생성
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    try:
        # 0. RSS 기반 한국 데이터 먼저 (실패 가능성 낮음)
        korean_data = run_rss_korean_crawler()
        if korean_data:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"data/korean_ecosystem_data_{ts}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(korean_data, f, ensure_ascii=False, indent=2)
            with open("data/korean_ecosystem_data_latest.json", "w", encoding="utf-8") as f:
                json.dump(korean_data, f, ensure_ascii=False, indent=2)
            logger.info("RSS 한국 데이터 저장: %s", path)
        
        # 1. 전체 생태계 크롤링 (선택, 실패 시 무시)
        global_data = await run_global_ecosystem_crawler()
        
        # 2. 한국 Playwright 크롤링은 RSS 실패 시에만
        if not korean_data or (korean_data.get("statistics", {}).get("total_startups", 0) < 5):
            korean_playwright = await run_korean_ecosystem_crawler()
            if korean_playwright:
                korean_data = korean_playwright
        else:
            logger.info("한국 데이터는 RSS 결과 사용 (Playwright 생략)")
        
        if not korean_data:
            korean_data = {"startups": [], "accelerators": [], "coworking_spaces": [], "statistics": {}}
        
        # 3. 데이터 통합
        if global_data or korean_data:
            merged_data = merge_ecosystem_data(global_data or {}, korean_data or {})
            
            # 4. 통합 데이터 저장
            merged_filename = save_merged_data(merged_data)
            
            if merged_filename:
                logger.info(f"✅ 통합 데이터 저장 완료: {merged_filename}")
                
                # 5. 요약 리포트 생성
                generate_summary_report(merged_data)
                
                logger.info("🎉 모든 크롤링 작업 완료!")
            else:
                logger.error("❌ 통합 데이터 저장 실패")
        else:
            logger.warning("⚠️ 크롤링된 데이터가 없습니다")
            
    except Exception as e:
        logger.error(f"크롤링 실행 중 오류 발생: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
