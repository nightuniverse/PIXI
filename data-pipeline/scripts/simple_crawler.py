#!/usr/bin/env python3
"""
간단한 스타트업 정보 크롤링 스크립트 (테스트용)
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime

def crawl_startup_news():
    """TechCrunch에서 스타트업 뉴스 크롤링"""
    print("🚀 TechCrunch에서 스타트업 뉴스 크롤링 시작...")
    
    try:
        # TechCrunch 스타트업 섹션
        url = "https://techcrunch.com/category/startups/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        startups = []
        articles = soup.find_all('article', class_='post-block')
        
        for i, article in enumerate(articles[:10]):  # 상위 10개만
            try:
                # 제목
                title_elem = article.find('h2', class_='post-block__title')
                title = title_elem.get_text(strip=True) if title_elem else "No Title"
                
                # 링크
                link_elem = article.find('a', class_='post-block__title__link')
                link = link_elem['href'] if link_elem else ""
                
                # 요약
                excerpt_elem = article.find('div', class_='post-block__content')
                excerpt = excerpt_elem.get_text(strip=True) if excerpt_elem else ""
                
                # 작성자
                author_elem = article.find('span', class_='river-byline__authors')
                author = author_elem.get_text(strip=True) if author_elem else "Unknown"
                
                # 시간
                time_elem = article.find('time')
                publish_time = time_elem.get_text(strip=True) if time_elem else ""
                
                startup_data = {
                    'title': title,
                    'link': link,
                    'excerpt': excerpt,
                    'author': author,
                    'publish_time': publish_time,
                    'source': 'TechCrunch',
                    'crawled_at': datetime.now().isoformat()
                }
                
                startups.append(startup_data)
                print(f"✅ {title[:50]}...")
                
            except Exception as e:
                print(f"❌ 기사 크롤링 실패: {e}")
                continue
            
            # 요청 간격 조절
            time.sleep(0.5)
        
        # 데이터 저장
        with open('data/techcrunch_startups.json', 'w', encoding='utf-8') as f:
            json.dump(startups, f, ensure_ascii=False, indent=2)
        
        print(f"🎉 TechCrunch 크롤링 완료: {len(startups)}개 기사")
        return startups
        
    except Exception as e:
        print(f"❌ TechCrunch 크롤링 실패: {e}")
        return []

def crawl_startup_directories():
    """스타트업 디렉토리 사이트에서 정보 크롤링"""
    print("📁 스타트업 디렉토리 사이트 크롤링 시작...")
    
    # 간단한 스타트업 정보 (실제 크롤링 대신 샘플 데이터)
    sample_startups = [
        {
            "name": "OpenAI",
            "description": "AI 연구 및 개발 기업",
            "location": "San Francisco, CA",
            "industry": "Artificial Intelligence",
            "founded": "2015",
            "funding": "Series Unknown",
            "source": "Sample Data",
            "crawled_at": datetime.now().isoformat()
        },
        {
            "name": "Stripe",
            "description": "온라인 결제 처리 플랫폼",
            "location": "San Francisco, CA",
            "industry": "Fintech",
            "founded": "2010",
            "funding": "Series Unknown",
            "source": "Sample Data",
            "crawled_at": datetime.now().isoformat()
        },
        {
            "name": "Notion",
            "description": "협업 및 생산성 도구",
            "location": "San Francisco, CA",
            "industry": "Productivity",
            "founded": "2013",
            "funding": "Series Unknown",
            "source": "Sample Data",
            "crawled_at": datetime.now().isoformat()
        }
    ]
    
    # 데이터 저장
    with open('data/sample_startups.json', 'w', encoding='utf-8') as f:
        json.dump(sample_startups, f, ensure_ascii=False, indent=2)
    
    print(f"🎉 샘플 스타트업 데이터 생성 완료: {len(sample_startups)}개")
    return sample_startups

def main():
    """메인 함수"""
    print("🕷️ 스타트업 정보 크롤링 시작")
    print("=" * 50)
    
    # 1. TechCrunch 뉴스 크롤링
    techcrunch_data = crawl_startup_news()
    
    # 2. 샘플 스타트업 데이터 생성
    sample_data = crawl_startup_directories()
    
    # 3. 전체 데이터 통합
    all_data = techcrunch_data + sample_data
    
    # 전체 데이터 저장
    with open('data/all_crawled_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print("=" * 50)
    print(f"🎯 전체 크롤링 완료: {len(all_data)}개 항목")
    print("📁 데이터 저장 위치: data-pipeline/data/")

if __name__ == "__main__":
    main()
