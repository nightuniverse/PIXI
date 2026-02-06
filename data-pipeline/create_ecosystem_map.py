#!/usr/bin/env python3
"""
스타트업 생태계 데이터 지도 시각화 스크립트
수집된 데이터를 인터랙티브 지도에 표시합니다.
"""

import json
import folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import time
import os
from typing import Dict, List, Any, Optional
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EcosystemMapCreator:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.merged_data = None
        self.geolocator = Nominatim(user_agent="startup_ecosystem_mapper")
        
        # 한국 주요 도시 좌표 (기본값)
        self.korean_cities = {
            "서울": [37.5665, 126.9780],
            "성남": [37.4449, 127.1389],
            "제주": [33.4996, 126.5312],
            "부산": [35.1796, 129.0756],
            "대구": [35.8714, 128.6014],
            "인천": [37.4563, 126.7052],
            "광주": [35.1595, 126.8526],
            "대전": [36.3504, 127.3845],
            "울산": [35.5384, 129.3114]
        }
        
        # 한국 구/군 좌표
        self.korean_districts = {
            "서울 강남구": [37.5172, 127.0473],
            "서울 마포구": [37.5635, 126.9080],
            "서울 서초구": [37.4837, 127.0324],
            "서울 종로구": [37.5735, 126.9789],
            "경기도 성남시": [37.4449, 127.1389]
        }
    
    def load_latest_data(self) -> bool:
        """최신 통합 데이터 로드"""
        try:
            # 가장 최근 파일 찾기
            files = [f for f in os.listdir(self.data_dir) if f.startswith('merged_ecosystem_data')]
            if not files:
                logger.error("통합 데이터 파일을 찾을 수 없습니다.")
                return False
            
            latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(self.data_dir, x)))
            filepath = os.path.join(self.data_dir, latest_file)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                self.merged_data = json.load(f)
            
            logger.info(f"✅ 데이터 로드 완료: {latest_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 데이터 로드 실패: {e}")
            return False
    
    def get_coordinates(self, location: str) -> Optional[List[float]]:
        """위치 정보를 좌표로 변환"""
        if not location or location == "Unknown":
            return None
        
        # 한국 도시/구/군 기본 좌표 확인
        if location in self.korean_districts:
            return self.korean_districts[location]
        elif location in self.korean_cities:
            return self.korean_cities[location]
        
        # 도시명만 추출 (상세 주소 제거)
        city_name = location.split(',')[0].strip()
        if city_name in self.korean_cities:
            return self.korean_cities[city_name]
        
        # Geocoding 시도
        try:
            logger.info(f"Geocoding 시도: {location}")
            location_obj = self.geolocator.geocode(location, timeout=10)
            if location_obj:
                return [location_obj.latitude, location_obj.longitude]
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            logger.warning(f"Geocoding 실패: {location} - {e}")
        except Exception as e:
            logger.warning(f"Geocoding 오류: {location} - {e}")
        
        return None
    
    def create_ecosystem_map(self) -> folium.Map:
        """생태계 지도 생성"""
        # 한국 중심으로 지도 생성
        center_lat, center_lng = 36.5, 127.5
        ecosystem_map = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=7,
            tiles='OpenStreetMap'
        )
        
        # 한국 경계선 추가
        folium.GeoJson(
            'https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2018/json/skorea-provinces-2018-geo.json',
            name='한국 경계',
            style_function=lambda x: {
                'fillColor': 'transparent',
                'color': 'blue',
                'weight': 2,
                'fillOpacity': 0.1
            }
        ).add_to(ecosystem_map)
        
        return ecosystem_map
    
    def add_startups_to_map(self, map_obj: folium.Map):
        """스타트업을 지도에 추가"""
        if not self.merged_data:
            return
        
        startups = []
        
        # 글로벌 스타트업
        global_startups = self.merged_data.get('global_ecosystem', {}).get('startups', [])
        for startup in global_startups:
            startup['ecosystem'] = 'Global'
            startups.append(startup)
        
        # 한국 스타트업
        korean_startups = self.merged_data.get('korean_ecosystem', {}).get('startups', [])
        for startup in korean_startups:
            startup['ecosystem'] = 'Korean'
            startups.append(startup)
        
        if not startups:
            logger.info("지도에 추가할 스타트업이 없습니다.")
            return
        
        # 스타트업 마커 추가
        for startup in startups:
            location = startup.get('location', '')
            if not location:
                continue
            
            coords = self.get_coordinates(location)
            if not coords:
                continue
            
            # 팝업 내용 생성
            popup_content = f"""
            <div style="width: 250px;">
                <h4 style="margin: 0 0 10px 0; color: #2c3e50;">🚀 {startup['name']}</h4>
                <p style="margin: 5px 0; font-size: 12px;"><strong>설명:</strong> {startup.get('description', 'N/A')[:100]}...</p>
                <p style="margin: 5px 0; font-size: 12px;"><strong>카테고리:</strong> {startup.get('category', 'N/A')}</p>
                <p style="margin: 5px 0; font-size: 12px;"><strong>소스:</strong> {startup.get('source', 'N/A')}</p>
                <p style="margin: 5px 0; font-size: 12px;"><strong>생태계:</strong> {startup.get('ecosystem', 'N/A')}</p>
                <p style="margin: 5px 0; font-size: 12px;"><strong>웹사이트:</strong> <a href="{startup.get('website', '#')}" target="_blank">링크</a></p>
            </div>
            """
            
            # 마커 색상 설정
            if startup.get('ecosystem') == 'Korean':
                icon_color = 'red'
                icon_prefix = '🇰🇷'
            else:
                icon_color = 'blue'
                icon_prefix = '🌍'
            
            folium.Marker(
                location=coords,
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=f"{icon_prefix} {startup['name']}",
                icon=folium.Icon(color=icon_color, icon='info-sign')
            ).add_to(map_obj)
            
            time.sleep(0.1)  # Geocoding API 제한 방지
        
        logger.info(f"✅ {len(startups)}개 스타트업을 지도에 추가했습니다.")
    
    def add_accelerators_to_map(self, map_obj: folium.Map):
        """액셀러레이터를 지도에 추가"""
        if not self.merged_data:
            return
        
        accelerators = self.merged_data.get('korean_ecosystem', {}).get('accelerators', [])
        
        if not accelerators:
            logger.info("지도에 추가할 액셀러레이터가 없습니다.")
            return
        
        # 액셀러레이터 마커 추가
        for accelerator in accelerators:
            location = accelerator.get('location', '')
            if not location:
                continue
            
            coords = self.get_coordinates(location)
            if not coords:
                continue
            
            # 팝업 내용 생성
            popup_content = f"""
            <div style="width: 250px;">
                <h4 style="margin: 0 0 10px 0; color: #27ae60;">🚀 {accelerator['name']}</h4>
                <p style="margin: 5px 0; font-size: 12px;"><strong>설명:</strong> {accelerator.get('description', 'N/A')[:100]}...</p>
                <p style="margin: 5px 0; font-size: 12px;"><strong>위치:</strong> {accelerator.get('location', 'N/A')}</p>
                <p style="margin: 5px 0; font-size: 12px;"><strong>집중 분야:</strong> {accelerator.get('focus', 'N/A')}</p>
                <p style="margin: 5px 0; font-size: 12px;"><strong>웹사이트:</strong> <a href="{accelerator.get('website', '#')}" target="_blank">링크</a></p>
            </div>
            """
            
            folium.Marker(
                location=coords,
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=f"🚀 {accelerator['name']}",
                icon=folium.Icon(color='green', icon='rocket')
            ).add_to(map_obj)
            
            time.sleep(0.1)
        
        logger.info(f"✅ {len(accelerators)}개 액셀러레이터를 지도에 추가했습니다.")
    
    def add_coworking_spaces_to_map(self, map_obj: folium.Map):
        """코워킹 스페이스를 지도에 추가"""
        if not self.merged_data:
            return
        
        coworking_spaces = self.merged_data.get('korean_ecosystem', {}).get('coworking_spaces', [])
        
        if not coworking_spaces:
            logger.info("지도에 추가할 코워킹 스페이스가 없습니다.")
            return
        
        # 코워킹 스페이스 마커 추가
        for space in coworking_spaces:
            location = space.get('location', '')
            if not location:
                continue
            
            coords = self.get_coordinates(location)
            if not coords:
                continue
            
            # 팝업 내용 생성
            popup_content = f"""
            <div style="width: 250px;">
                <h4 style="margin: 0 0 10px 0; color: #8e44ad;">🏢 {space['name']}</h4>
                <p style="margin: 5px 0; font-size: 12px;"><strong>설명:</strong> {space.get('description', 'N/A')[:100]}...</p>
                <p style="margin: 5px 0; font-size: 12px;"><strong>위치:</strong> {space.get('location', 'N/A')}</p>
                <p style="margin: 5px 0; font-size: 12px;"><strong>집중 분야:</strong> {space.get('focus', 'N/A')}</p>
                <p style="margin: 5px 0; font-size: 12px;"><strong>웹사이트:</strong> <a href="{space.get('website', '#')}" target="_blank">링크</a></p>
            </div>
            """
            
            folium.Marker(
                location=coords,
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=f"🏢 {space['name']}",
                icon=folium.Icon(color='purple', icon='building')
            ).add_to(map_obj)
            
            time.sleep(0.1)
        
        logger.info(f"✅ {len(coworking_spaces)}개 코워킹 스페이스를 지도에 추가했습니다.")
    
    def add_legend_to_map(self, map_obj: folium.Map):
        """지도에 범례 추가"""
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 200px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><strong>생태계 구성요소</strong></p>
        <p>🚀 <span style="color:red;">빨간색</span> - 한국 스타트업</p>
        <p>🌍 <span style="color:blue;">파란색</span> - 글로벌 스타트업</p>
        <p>🚀 <span style="color:green;">초록색</span> - 액셀러레이터</p>
        <p>🏢 <span style="color:purple;">보라색</span> - 코워킹 스페이스</p>
        </div>
        '''
        map_obj.get_root().html.add_child(folium.Element(legend_html))
    
    def save_maps(self):
        """지도 파일들을 저장"""
        if not self.merged_data:
            logger.error("데이터가 로드되지 않았습니다.")
            return
        
        # maps 디렉토리 생성
        os.makedirs('maps', exist_ok=True)
        
        # 1. 기본 생태계 지도 생성
        logger.info("기본 생태계 지도 생성 중...")
        basic_map = self.create_ecosystem_map()
        self.add_startups_to_map(basic_map)
        self.add_accelerators_to_map(basic_map)
        self.add_coworking_spaces_to_map(basic_map)
        self.add_legend_to_map(basic_map)
        
        basic_map.save('maps/ecosystem_basic_map.html')
        logger.info("✅ 기본 생태계 지도 저장 완료: maps/ecosystem_basic_map.html")
        
        # 2. 한국 전용 지도 생성
        logger.info("한국 생태계 전용 지도 생성 중...")
        korea_map = folium.Map(
            location=[36.5, 127.5],
            zoom_start=8,
            tiles='OpenStreetMap'
        )
        
        # 한국 경계선 추가
        folium.GeoJson(
            'https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2018/json/skorea-provinces-2018-geo.json',
            name='한국 경계',
            style_function=lambda x: {
                'fillColor': 'transparent',
                'color': 'blue',
                'weight': 2,
                'fillOpacity': 0.1
            }
        ).add_to(korea_map)
        
        # 한국 데이터만 추가
        self._add_korean_data_to_map(korea_map)
        
        korea_map.save('maps/korean_ecosystem_map.html')
        logger.info("✅ 한국 생태계 전용 지도 저장 완료: maps/korean_ecosystem_map.html")
        
        # 3. 서울 상세 지도 생성
        logger.info("서울 상세 생태계 지도 생성 중...")
        seoul_map = folium.Map(
            location=[37.5665, 126.9780],
            zoom_start=11,
            tiles='OpenStreetMap'
        )
        
        # 서울 경계선 추가
        folium.GeoJson(
            'https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2018/json/skorea-municipalities-2018-geo.json',
            name='서울 경계',
            style_function=lambda x: {
                'fillColor': 'transparent',
                'color': 'red',
                'weight': 2,
                'fillOpacity': 0.1
            }
        ).add_to(seoul_map)
        
        # 서울 데이터만 추가
        self._add_seoul_data_to_map(seoul_map)
        
        seoul_map.save('maps/seoul_ecosystem_map.html')
        logger.info("✅ 서울 상세 생태계 지도 저장 완료: maps/seoul_ecosystem_map.html")
        
        logger.info("🎉 모든 지도 생성 완료!")
    
    def _add_korean_data_to_map(self, map_obj: folium.Map):
        """한국 데이터만 지도에 추가"""
        if not self.merged_data:
            return
        
        korean_data = self.merged_data.get('korean_ecosystem', {})
        
        # 스타트업 추가
        startups = korean_data.get('startups', [])
        for startup in startups:
            location = startup.get('location', '')
            if not location:
                continue
            
            coords = self.get_coordinates(location)
            if not coords:
                continue
            
            popup_content = f"""
            <div style="width: 250px;">
                <h4 style="margin: 0 0 10px 0; color: #e74c3c;">🚀 {startup['name']}</h4>
                <p style="margin: 5px 0; font-size: 12px;"><strong>설명:</strong> {startup.get('description', 'N/A')[:100]}...</p>
                <p style="margin: 5px 0; font-size: 12px;"><strong>카테고리:</strong> {startup.get('category', 'N/A')}</p>
            </div>
            """
            
            folium.Marker(
                location=coords,
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=f"🚀 {startup['name']}",
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(map_obj)
        
        # 액셀러레이터 추가
        accelerators = korean_data.get('accelerators', [])
        for accelerator in accelerators:
            location = accelerator.get('location', '')
            if not location:
                continue
            
            coords = self.get_coordinates(location)
            if not coords:
                continue
            
            popup_content = f"""
            <div style="width: 250px;">
                <h4 style="margin: 0 0 10px 0; color: #27ae60;">🚀 {accelerator['name']}</h4>
                <p style="margin: 5px 0; font-size: 12px;"><strong>집중 분야:</strong> {accelerator.get('focus', 'N/A')}</p>
            </div>
            """
            
            folium.Marker(
                location=coords,
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=f"🚀 {accelerator['name']}",
                icon=folium.Icon(color='green', icon='rocket')
            ).add_to(map_obj)
        
        # 코워킹 스페이스 추가
        coworking_spaces = korean_data.get('coworking_spaces', [])
        for space in coworking_spaces:
            location = space.get('location', '')
            if not location:
                continue
            
            coords = self.get_coordinates(location)
            if not coords:
                continue
            
            popup_content = f"""
            <div style="width: 250px;">
                <h4 style="margin: 0 0 10px 0; color: #8e44ad;">🏢 {space['name']}</h4>
                <p style="margin: 5px 0; font-size: 12px;"><strong>집중 분야:</strong> {space.get('focus', 'N/A')}</p>
            </div>
            """
            
            folium.Marker(
                location=coords,
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=f"🏢 {space['name']}",
                icon=folium.Icon(color='purple', icon='building')
            ).add_to(map_obj)
    
    def _add_seoul_data_to_map(self, map_obj: folium.Map):
        """서울 데이터만 지도에 추가"""
        if not self.merged_data:
            return
        
        korean_data = self.merged_data.get('korean_ecosystem', {})
        
        # 서울에 위치한 데이터만 필터링
        seoul_keywords = ['서울', '강남구', '마포구', '서초구', '종로구']
        
        # 액셀러레이터 추가
        accelerators = korean_data.get('accelerators', [])
        for accelerator in accelerators:
            location = accelerator.get('location', '')
            if not location or not any(keyword in location for keyword in seoul_keywords):
                continue
            
            coords = self.get_coordinates(location)
            if not coords:
                continue
            
            popup_content = f"""
            <div style="width: 250px;">
                <h4 style="margin: 0 0 10px 0; color: #27ae60;">🚀 {accelerator['name']}</h4>
                <p style="margin: 5px 0; font-size: 12px;"><strong>위치:</strong> {accelerator.get('location', 'N/A')}</p>
                <p style="margin: 5px 0; font-size: 12px;"><strong>집중 분야:</strong> {accelerator.get('focus', 'N/A')}</p>
            </div>
            """
            
            folium.Marker(
                location=coords,
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=f"🚀 {accelerator['name']}",
                icon=folium.Icon(color='green', icon='rocket')
            ).add_to(map_obj)
        
        # 코워킹 스페이스 추가
        coworking_spaces = korean_data.get('coworking_spaces', [])
        for space in coworking_spaces:
            location = space.get('location', '')
            if not location or not any(keyword in location for keyword in seoul_keywords):
                continue
            
            coords = self.get_coordinates(location)
            if not coords:
                continue
            
            popup_content = f"""
            <div style="width: 250px;">
                <h4 style="margin: 0 0 10px 0; color: #8e44ad;">🏢 {space['name']}</h4>
                <p style="margin: 5px 0; font-size: 12px;"><strong>위치:</strong> {space.get('location', 'N/A')}</p>
                <p style="margin: 5px 0; font-size: 12px;"><strong>집중 분야:</strong> {space.get('focus', 'N/A')}</p>
            </div>
            """
            
            folium.Marker(
                location=coords,
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=f"🏢 {space['name']}",
                icon=folium.Icon(color='purple', icon='building')
            ).add_to(map_obj)

def main():
    """메인 함수"""
    print("🗺️ 스타트업 생태계 지도 생성 시작")
    print("=" * 60)
    
    # 지도 생성기 초기화
    map_creator = EcosystemMapCreator()
    
    # 데이터 로드
    if not map_creator.load_latest_data():
        print("데이터 로드에 실패했습니다. 크롤링을 먼저 실행하세요.")
        return
    
    # 지도 생성 및 저장
    map_creator.save_maps()
    
    print("\n" + "=" * 60)
    print("🎉 생태계 지도 생성 완료!")
    print("📁 생성된 지도 파일:")
    print("   - maps/ecosystem_basic_map.html (기본 생태계 지도)")
    print("   - maps/korean_ecosystem_map.html (한국 생태계 전용 지도)")
    print("   - maps/seoul_ecosystem_map.html (서울 상세 생태계 지도)")
    print("\n🌐 웹 브라우저에서 HTML 파일을 열어 지도를 확인하세요!")

if __name__ == "__main__":
    main()
