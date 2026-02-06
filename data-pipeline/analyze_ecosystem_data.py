#!/usr/bin/env python3
"""
스타트업 생태계 데이터 분석 및 시각화 스크립트
수집된 데이터를 분석하고 인사이트를 도출합니다.
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from typing import Dict, List, Any
import os

# 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

class EcosystemDataAnalyzer:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.merged_data = None
        self.global_data = None
        self.korean_data = None
        
    def load_latest_data(self):
        """최신 통합 데이터 로드"""
        try:
            # 가장 최근 파일 찾기
            files = [f for f in os.listdir(self.data_dir) if f.startswith('merged_ecosystem_data')]
            if not files:
                print("통합 데이터 파일을 찾을 수 없습니다.")
                return False
            
            latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(self.data_dir, x)))
            filepath = os.path.join(self.data_dir, latest_file)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                self.merged_data = json.load(f)
            
            self.global_data = self.merged_data.get('global_ecosystem', {})
            self.korean_data = self.merged_data.get('korean_ecosystem', {})
            
            print(f"✅ 데이터 로드 완료: {latest_file}")
            return True
            
        except Exception as e:
            print(f"❌ 데이터 로드 실패: {e}")
            return False
    
    def analyze_ecosystem_composition(self):
        """생태계 구성 분석"""
        print("\n🔍 생태계 구성 분석")
        print("=" * 50)
        
        if not self.merged_data:
            print("데이터가 로드되지 않았습니다.")
            return
        
        # 전체 통계
        merged_stats = self.merged_data.get('merged_statistics', {})
        
        print(f"🌍 전체 생태계:")
        print(f"   - 고유 스타트업: {merged_stats.get('total_unique_startups', 0):,}개")
        print(f"   - 고유 투자자: {merged_stats.get('total_unique_investors', 0):,}개")
        print(f"   - 고유 액셀러레이터: {merged_stats.get('total_unique_accelerators', 0):,}개")
        print(f"   - 고유 코워킹 스페이스: {merged_stats.get('total_unique_coworking_spaces', 0):,}개")
        print(f"   - 고유 이벤트: {merged_stats.get('total_unique_events', 0):,}개")
        
        # 한국 생태계 통계
        korean_stats = self.korean_data.get('statistics', {})
        print(f"\n🇰🇷 한국 생태계:")
        print(f"   - 스타트업: {korean_stats.get('total_startups', 0):,}개")
        print(f"   - 투자자: {korean_stats.get('total_investors', 0):,}개")
        print(f"   - 액셀러레이터: {korean_stats.get('total_accelerators', 0):,}개")
        print(f"   - 코워킹 스페이스: {korean_stats.get('total_coworking_spaces', 0):,}개")
        print(f"   - 뉴스: {korean_stats.get('total_news', 0):,}개")
    
    def analyze_startup_categories(self):
        """스타트업 카테고리 분석"""
        print("\n📊 스타트업 카테고리 분석")
        print("=" * 50)
        
        if not self.merged_data:
            return
        
        # 모든 스타트업 데이터 수집
        all_startups = []
        
        # 글로벌 스타트업
        global_startups = self.global_data.get('startups', [])
        for startup in global_startups:
            startup['ecosystem'] = 'Global'
            all_startups.append(startup)
        
        # 한국 스타트업
        korean_startups = self.korean_data.get('startups', [])
        for startup in korean_startups:
            startup['ecosystem'] = 'Korean'
            all_startups.append(startup)
        
        if not all_startups:
            print("분석할 스타트업 데이터가 없습니다.")
            return
        
        # 카테고리별 분류
        categories = {}
        for startup in all_startups:
            category = startup.get('category', 'Unknown')
            if category not in categories:
                categories[category] = {'count': 0, 'startups': []}
            categories[category]['count'] += 1
            categories[category]['startups'].append(startup['name'])
        
        # 결과 출력
        for category, data in categories.items():
            print(f"\n📁 {category}: {data['count']}개")
            for startup_name in data['startups'][:5]:  # 상위 5개만
                print(f"   - {startup_name}")
            if len(data['startups']) > 5:
                print(f"   ... 및 {len(data['startups']) - 5}개 더")
    
    def analyze_geographic_distribution(self):
        """지리적 분포 분석"""
        print("\n🌍 지리적 분포 분석")
        print("=" * 50)
        
        if not self.merged_data:
            return
        
        # 모든 엔티티의 위치 정보 수집
        locations = {}
        
        # 글로벌 데이터
        for entity_type in ['startups', 'investors', 'accelerators', 'coworking_spaces']:
            entities = self.global_data.get(entity_type, [])
            for entity in entities:
                location = entity.get('location', 'Unknown')
                if location not in locations:
                    locations[location] = {'count': 0, 'types': set()}
                locations[location]['count'] += 1
                locations[location]['types'].add(entity_type)
        
        # 한국 데이터
        for entity_type in ['startups', 'investors', 'accelerators', 'coworking_spaces']:
            entities = self.korean_data.get(entity_type, [])
            for entity in entities:
                location = entity.get('location', 'Unknown')
                if location not in locations:
                    locations[location] = {'count': 0, 'types': set()}
                locations[location]['count'] += 1
                locations[location]['types'].add(entity_type)
        
        # 결과 출력
        sorted_locations = sorted(locations.items(), key=lambda x: x[1]['count'], reverse=True)
        
        for location, data in sorted_locations[:10]:  # 상위 10개
            types_str = ', '.join(sorted(data['types']))
            print(f"📍 {location}: {data['count']}개 ({types_str})")
    
    def create_visualizations(self):
        """데이터 시각화 생성"""
        print("\n📈 데이터 시각화 생성 중...")
        
        if not self.merged_data:
            print("시각화할 데이터가 없습니다.")
            return
        
        # 1. 생태계 구성 파이 차트
        self._create_ecosystem_pie_chart()
        
        # 2. 한국 vs 글로벌 비교 차트
        self._create_comparison_chart()
        
        # 3. 시간별 크롤링 결과
        self._create_timeline_chart()
        
        print("✅ 시각화 완료! charts/ 디렉토리를 확인하세요.")
    
    def _create_ecosystem_pie_chart(self):
        """생태계 구성 파이 차트"""
        try:
            # 한국 생태계 데이터
            korean_stats = self.korean_data.get('statistics', {})
            
            labels = ['스타트업', '투자자', '액셀러레이터', '코워킹 스페이스', '뉴스']
            sizes = [
                korean_stats.get('total_startups', 0),
                korean_stats.get('total_investors', 0),
                korean_stats.get('total_accelerators', 0),
                korean_stats.get('total_coworking_spaces', 0),
                korean_stats.get('total_news', 0)
            ]
            
            # 0이 아닌 값만 필터링
            filtered_labels = [label for label, size in zip(labels, sizes) if size > 0]
            filtered_sizes = [size for size in sizes if size > 0]
            
            if not filtered_sizes:
                return
            
            plt.figure(figsize=(10, 8))
            plt.pie(filtered_sizes, labels=filtered_labels, autopct='%1.1f%%', startangle=90)
            plt.title('🇰🇷 한국 스타트업 생태계 구성', fontsize=16, pad=20)
            plt.axis('equal')
            
            # charts 디렉토리 생성
            os.makedirs('charts', exist_ok=True)
            plt.savefig('charts/korean_ecosystem_composition.png', dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            print(f"파이 차트 생성 실패: {e}")
    
    def _create_comparison_chart(self):
        """한국 vs 글로벌 비교 차트"""
        try:
            # 데이터 준비
            categories = ['스타트업', '투자자', '액셀러레이터', '코워킹 스페이스']
            
            korean_counts = [
                self.korean_data.get('statistics', {}).get('total_startups', 0),
                self.korean_data.get('statistics', {}).get('total_investors', 0),
                self.korean_data.get('statistics', {}).get('total_accelerators', 0),
                self.korean_data.get('statistics', {}).get('total_coworking_spaces', 0)
            ]
            
            global_counts = [
                self.global_data.get('statistics', {}).get('total_startups', 0),
                self.global_data.get('statistics', {}).get('total_investors', 0),
                self.global_data.get('statistics', {}).get('total_accelerators', 0),
                self.global_data.get('statistics', {}).get('total_coworking_spaces', 0)
            ]
            
            # 차트 생성
            x = range(len(categories))
            width = 0.35
            
            plt.figure(figsize=(12, 8))
            plt.bar([i - width/2 for i in x], korean_counts, width, label='🇰🇷 한국', color='skyblue')
            plt.bar([i + width/2 for i in x], global_counts, width, label='🌍 글로벌', color='lightcoral')
            
            plt.xlabel('엔티티 유형', fontsize=12)
            plt.ylabel('개수', fontsize=12)
            plt.title('한국 vs 글로벌 생태계 비교', fontsize=16, pad=20)
            plt.xticks(x, categories)
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # 값 표시
            for i, (kr, gl) in enumerate(zip(korean_counts, global_counts)):
                plt.text(i - width/2, kr + 0.1, str(kr), ha='center', va='bottom')
                plt.text(i + width/2, gl + 0.1, str(gl), ha='center', va='bottom')
            
            plt.tight_layout()
            plt.savefig('charts/ecosystem_comparison.png', dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            print(f"비교 차트 생성 실패: {e}")
    
    def _create_timeline_chart(self):
        """시간별 크롤링 결과 차트"""
        try:
            # 크롤링 시간 데이터 수집
            timeline_data = []
            
            # 글로벌 데이터
            global_time = self.global_data.get('crawled_at')
            if global_time:
                timeline_data.append(('글로벌', global_time, 0))
            
            # 한국 데이터
            korean_time = self.korean_data.get('crawled_at')
            if korean_time:
                korean_stats = self.korean_data.get('statistics', {})
                total_entities = korean_stats.get('total_entities', 0)
                timeline_data.append(('한국', korean_time, total_entities))
            
            if not timeline_data:
                return
            
            # 시간 파싱
            times = []
            labels = []
            counts = []
            
            for label, time_str, count in timeline_data:
                try:
                    dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    times.append(dt)
                    labels.append(label)
                    counts.append(count)
                except:
                    continue
            
            if not times:
                return
            
            # 차트 생성
            plt.figure(figsize=(10, 6))
            plt.plot(times, counts, marker='o', linewidth=2, markersize=8)
            
            for i, (time, count, label) in enumerate(zip(times, counts, labels)):
                plt.annotate(f'{label}\n{count}개', 
                           (time, count), 
                           textcoords="offset points", 
                           xytext=(0,10), 
                           ha='center')
            
            plt.title('📊 시간별 크롤링 결과', fontsize=16, pad=20)
            plt.xlabel('시간', fontsize=12)
            plt.ylabel('수집된 엔티티 수', fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            plt.savefig('charts/crawling_timeline.png', dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            print(f"타임라인 차트 생성 실패: {e}")
    
    def generate_insights_report(self):
        """인사이트 리포트 생성"""
        print("\n💡 생태계 인사이트 리포트")
        print("=" * 50)
        
        if not self.merged_data:
            print("데이터가 로드되지 않았습니다.")
            return
        
        # 한국 생태계 분석
        korean_stats = self.korean_data.get('statistics', {})
        korean_startups = self.korean_data.get('startups', [])
        korean_accelerators = self.korean_data.get('accelerators', [])
        korean_coworking = self.korean_data.get('coworking_spaces', [])
        
        print("🇰🇷 한국 스타트업 생태계 특징:")
        
        # 액셀러레이터 분석
        if korean_accelerators:
            print(f"   • {len(korean_accelerators)}개의 주요 액셀러레이터가 활동 중")
            focus_areas = set()
            for acc in korean_accelerators:
                focus = acc.get('focus', '')
                if focus:
                    focus_areas.update([area.strip() for area in focus.split(',')])
            
            if focus_areas:
                print(f"   • 주요 투자 분야: {', '.join(sorted(focus_areas))}")
        
        # 코워킹 스페이스 분석
        if korean_coworking:
            print(f"   • {len(korean_coworking)}개의 주요 코워킹 스페이스 운영 중")
            locations = set()
            for space in korean_coworking:
                location = space.get('location', '')
                if location:
                    locations.add(location)
            
            if locations:
                print(f"   • 주요 운영 지역: {', '.join(sorted(locations))}")
        
        # 스타트업 분석
        if korean_startups:
            print(f"   • {len(korean_startups)}개의 스타트업 정보 수집됨")
            sources = set()
            for startup in korean_startups:
                source = startup.get('source', '')
                if source:
                    sources.add(source)
            
            if sources:
                print(f"   • 정보 소스: {', '.join(sorted(sources))}")
        
        # 글로벌 생태계 분석
        global_stats = self.global_data.get('statistics', {})
        global_entities = global_stats.get('total_entities', 0)
        
        print(f"\n🌍 글로벌 생태계 현황:")
        print(f"   • 수집된 엔티티: {global_entities}개")
        
        if global_entities == 0:
            print("   • 현재 글로벌 데이터 수집이 제한적임")
            print("   • 웹사이트 차단 및 접근 제한으로 인한 제약")
        
        # 개선 제안
        print(f"\n🚀 개선 제안:")
        print("   • 한국 생태계 데이터는 안정적으로 수집되고 있음")
        print("   • 글로벌 데이터 수집을 위한 대안 방법 모색 필요")
        print("   • API 기반 데이터 수집 및 협력 파트너십 고려")
        print("   • 정기적인 데이터 업데이트 및 품질 관리 필요")
    
    def save_analysis_report(self):
        """분석 리포트를 파일로 저장"""
        try:
            # 리포트 내용 생성
            report = {
                'analysis_timestamp': datetime.now().isoformat(),
                'data_source': 'merged_ecosystem_data',
                'summary': {
                    'total_unique_startups': self.merged_data.get('merged_statistics', {}).get('total_unique_startups', 0),
                    'total_unique_investors': self.merged_data.get('merged_statistics', {}).get('total_unique_investors', 0),
                    'total_unique_accelerators': self.merged_data.get('merged_statistics', {}).get('total_unique_accelerators', 0),
                    'total_unique_coworking_spaces': self.merged_data.get('merged_statistics', {}).get('total_unique_coworking_spaces', 0),
                    'total_unique_events': self.merged_data.get('merged_statistics', {}).get('total_unique_events', 0)
                },
                'korean_ecosystem': self.korean_data.get('statistics', {}),
                'global_ecosystem': self.global_data.get('statistics', {}),
                'analysis_notes': [
                    "한국 생태계 데이터는 안정적으로 수집됨",
                    "글로벌 데이터 수집은 웹사이트 차단으로 제한적",
                    "액셀러레이터와 코워킹 스페이스 정보가 풍부함",
                    "정기적인 데이터 업데이트 필요"
                ]
            }
            
            # 파일 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_report_{timestamp}.json"
            filepath = os.path.join(self.data_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 분석 리포트 저장 완료: {filename}")
            return filepath
            
        except Exception as e:
            print(f"❌ 분석 리포트 저장 실패: {e}")
            return None

def main():
    """메인 함수"""
    print("🔍 스타트업 생태계 데이터 분석 시작")
    print("=" * 60)
    
    # 분석기 초기화
    analyzer = EcosystemDataAnalyzer()
    
    # 데이터 로드
    if not analyzer.load_latest_data():
        print("데이터 로드에 실패했습니다. 크롤링을 먼저 실행하세요.")
        return
    
    # 1. 생태계 구성 분석
    analyzer.analyze_ecosystem_composition()
    
    # 2. 스타트업 카테고리 분석
    analyzer.analyze_startup_categories()
    
    # 3. 지리적 분포 분석
    analyzer.analyze_geographic_distribution()
    
    # 4. 시각화 생성
    analyzer.create_visualizations()
    
    # 5. 인사이트 리포트 생성
    analyzer.generate_insights_report()
    
    # 6. 분석 리포트 저장
    analyzer.save_analysis_report()
    
    print("\n" + "=" * 60)
    print("🎉 생태계 데이터 분석 완료!")
    print("📊 차트 파일: charts/ 디렉토리")
    print("📋 분석 리포트: data/ 디렉토리")

if __name__ == "__main__":
    main()
