#!/usr/bin/env python3
"""
생성된 생태계 지도 파일들을 미리보기하는 스크립트
"""

import os
import webbrowser
import time

def preview_maps():
    """생성된 지도 파일들을 미리보기"""
    print("🗺️ 스타트업 생태계 지도 미리보기")
    print("=" * 50)
    
    maps_dir = "maps"
    
    if not os.path.exists(maps_dir):
        print("❌ maps 디렉토리를 찾을 수 없습니다.")
        return
    
    # 생성된 지도 파일들 확인
    map_files = []
    for file in os.listdir(maps_dir):
        if file.endswith('.html'):
            filepath = os.path.join(maps_dir, file)
            file_size = os.path.getsize(filepath) / (1024 * 1024)  # MB
            map_files.append((file, filepath, file_size))
    
    if not map_files:
        print("❌ 지도 파일을 찾을 수 없습니다.")
        return
    
    print(f"📁 발견된 지도 파일: {len(map_files)}개")
    print()
    
    # 지도 파일 정보 출력
    for i, (filename, filepath, file_size) in enumerate(map_files, 1):
        print(f"{i}. {filename}")
        print(f"   📍 경로: {filepath}")
        print(f"   📊 크기: {file_size:.1f} MB")
        print()
    
    # 사용자 선택
    while True:
        try:
            choice = input("미리보기할 지도 번호를 선택하세요 (1-{}): ".format(len(map_files)))
            choice = int(choice)
            
            if 1 <= choice <= len(map_files):
                selected_file = map_files[choice - 1]
                break
            else:
                print("❌ 유효하지 않은 번호입니다. 다시 선택해주세요.")
        except ValueError:
            print("❌ 숫자를 입력해주세요.")
    
    # 선택된 지도 파일 열기
    filename, filepath, file_size = selected_file
    print(f"\n🌐 {filename} 지도를 브라우저에서 열고 있습니다...")
    
    # 절대 경로로 변환
    abs_filepath = os.path.abspath(filepath)
    
    try:
        # 브라우저에서 지도 열기
        webbrowser.open(f"file://{abs_filepath}")
        print(f"✅ {filename} 지도가 브라우저에서 열렸습니다!")
        print(f"📍 파일 경로: {abs_filepath}")
        
        # 지도 설명
        if "basic" in filename.lower():
            print("\n📋 이 지도는 전체 생태계 데이터를 보여줍니다:")
            print("   - 🚀 스타트업 (빨간색: 한국, 파란색: 글로벌)")
            print("   - 🚀 액셀러레이터 (초록색)")
            print("   - 🏢 코워킹 스페이스 (보라색)")
            print("   - 한국 경계선 포함")
            
        elif "korean" in filename.lower():
            print("\n📋 이 지도는 한국 생태계 데이터만 보여줍니다:")
            print("   - 🚀 한국 스타트업 (빨간색)")
            print("   - 🚀 한국 액셀러레이터 (초록색)")
            print("   - 🏢 한국 코워킹 스페이스 (보라색)")
            print("   - 한국 경계선 포함")
            
        elif "seoul" in filename.lower():
            print("\n📋 이 지도는 서울 지역 생태계 데이터를 상세히 보여줍니다:")
            print("   - 🚀 서울 액셀러레이터 (초록색)")
            print("   - 🏢 서울 코워킹 스페이스 (보라색)")
            print("   - 서울 시 경계선 포함")
            print("   - 확대된 서울 지역 뷰")
        
        print("\n💡 지도 사용 팁:")
        print("   - 마커를 클릭하면 상세 정보 팝업이 나타납니다")
        print("   - 마우스 휠로 확대/축소할 수 있습니다")
        print("   - 마우스 드래그로 지도를 이동할 수 있습니다")
        print("   - 우측 상단의 범례를 참고하세요")
        
    except Exception as e:
        print(f"❌ 지도를 열 수 없습니다: {e}")
        print(f"수동으로 파일을 열어주세요: {abs_filepath}")

def show_map_statistics():
    """지도 통계 정보 표시"""
    print("\n📊 지도 통계 정보")
    print("=" * 50)
    
    maps_dir = "maps"
    
    if not os.path.exists(maps_dir):
        return
    
    # 지도 파일 통계
    html_files = [f for f in os.listdir(maps_dir) if f.endswith('.html')]
    total_size = sum(os.path.getsize(os.path.join(maps_dir, f)) for f in html_files)
    
    print(f"📁 총 지도 파일 수: {len(html_files)}개")
    print(f"📊 총 파일 크기: {total_size / (1024 * 1024):.1f} MB")
    
    # 각 지도 파일별 크기
    for file in html_files:
        filepath = os.path.join(maps_dir, file)
        file_size = os.path.getsize(filepath) / (1024 * 1024)
        print(f"   - {file}: {file_size:.1f} MB")
    
    print(f"\n💾 지도 파일들은 {maps_dir}/ 디렉토리에 저장되어 있습니다.")
    print("🌐 웹 브라우저에서 HTML 파일을 열어 인터랙티브 지도를 확인할 수 있습니다.")

def main():
    """메인 함수"""
    print("🗺️ 스타트업 생태계 지도 미리보기 시스템")
    print("=" * 60)
    
    # 지도 통계 표시
    show_map_statistics()
    
    print("\n" + "=" * 60)
    
    # 지도 미리보기
    preview_maps()
    
    print("\n" + "=" * 60)
    print("🎉 지도 미리보기 완료!")
    print("💡 다른 지도도 확인하고 싶다면 스크립트를 다시 실행하세요.")

if __name__ == "__main__":
    main()
