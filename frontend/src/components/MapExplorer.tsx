'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'

type FilterType = 'all' | 'startup' | 'investor' | 'accelerator' | 'coworking_space'

// Mapbox 액세스 토큰 설정 (실제 사용 시 환경변수로 관리)
mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || 'your-mapbox-token-here'

interface Entity {
  id: number
  name: string
  type: string
  lat: number
  lon: number
  description?: string
  country?: string
  city?: string
  domains?: string[]
  last_funding_round?: string
  is_hiring?: boolean
  investment_focus?: string[]
  preferred_stages?: string[]
  portfolio_count?: number
}

interface Cluster {
  lat: number
  lon: number
  count: number
  entities: Entity[]
}

export default function MapExplorer() {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<mapboxgl.Map | null>(null)
  /** moveend 등 이벤트에서 항상 최신 클러스터 목록을 참조하기 위한 ref */
  const clustersRef = useRef<Cluster[]>([])
  /** 전체 클러스터(타입 필터 전) - loadClusters에서 타입 필터 적용용 */
  const allClustersRef = useRef<Cluster[]>([])
  /** 현재 필터 타입 - loadClusters에서 항상 적용 */
  const filterTypeRef = useRef<FilterType>('all')
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null)
  const [clusters, setClusters] = useState<Cluster[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)
  const [isUsingMockData, setIsUsingMockData] = useState(false)
  const [filterType, setFilterType] = useState<FilterType>('all')

  const filterClustersByType = (data: Cluster[], type: FilterType): Cluster[] => {
    if (type === 'all') return data
    return data
      .map(c => ({
        ...c,
        entities: c.entities.filter(e => e.type === type),
        count: 0
      }))
      .map(c => ({ ...c, count: c.entities.length }))
      .filter(c => c.entities.length > 0)
  }

  const filteredClusters = useMemo(
    () => filterClustersByType(clusters, filterType),
    [clusters, filterType]
  )

  useEffect(() => {
    allClustersRef.current = clusters
  }, [clusters])

  useEffect(() => {
    filterTypeRef.current = filterType
  }, [filterType])

  useEffect(() => {
    clustersRef.current = filteredClusters
    if (!isLoading && map.current) updateMapMarkers(filteredClusters)
  }, [filteredClusters, filterType, isLoading])

  // 필터 변경 시, 선택된 엔티티가 현재 필터 타입과 다르면 선택 해제 (사이드바에 안 맞는 항목 안 보이게)
  useEffect(() => {
    if (filterType === 'all' || !selectedEntity) return
    // 타입이 정확히 일치하지 않으면 선택 해제
    if (selectedEntity.type !== filterType) {
      setSelectedEntity(null)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterType])

  useEffect(() => {
    if (!mapContainer.current) return

    // 지도 초기화 - 더 깔끔한 스타일 사용
    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/light-v11', // 깔끔한 라이트 스타일
      center: [0, 20], // 전 세계 중심
      zoom: 2,
      maxZoom: 18,
      minZoom: 1
    })

    // 네비게이션 컨트롤 추가
    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right')

    // 줌 컨트롤 추가
    map.current.addControl(new mapboxgl.FullscreenControl(), 'top-right')

    // 지도 로드 완료 후 초기 데이터 로드
    map.current.on('load', () => {
      setIsLoading(false)
      loadMapData()
    })

    // 지도 이동 시 데이터 업데이트
    map.current.on('moveend', () => {
      if (map.current) {
        const bounds = map.current.getBounds()
        loadClusters(bounds)
      }
    })

    // 클린업
    return () => {
      if (map.current) {
        map.current.remove()
      }
    }
  }, [])

  const loadMapData = async () => {
    try {
      // 실제 크롤링된 데이터 로드
      console.log('실제 크롤링 데이터를 로드합니다.')
      
      const response = await fetch('/data/koreanEcosystemData.json', {
        cache: 'no-cache'
      })
      if (!response.ok) {
        throw new Error('데이터 로드 실패')
      }
      
      const data = await response.json()
      
      // 모든 엔티티를 클러스터 형태로 변환
      const allEntities: Entity[] = [
        ...data.startups.map((s: any, idx: number) => ({
          id: s.id || idx + 1,
          name: s.name,
          type: s.type || 'startup',
          lat: s.lat || 37.5665,
          lon: s.lon || 126.9780,
          description: s.description,
          country: s.country || '한국',
          city: s.location,
          domains: s.category ? [s.category] : [],
          is_hiring: false
        })),
        ...data.accelerators.map((a: any, idx: number) => ({
          id: a.id || idx + 100,
          name: a.name,
          type: a.type || 'accelerator',
          lat: a.lat || 37.5665,
          lon: a.lon || 126.9780,
          description: a.description,
          country: a.country || '한국',
          city: a.location,
          domains: a.focus ? [a.focus] : [],
          is_hiring: false
        })),
        ...data.coworking_spaces.map((c: any, idx: number) => ({
          id: c.id || idx + 200,
          name: c.name,
          type: c.type || 'coworking_space',
          lat: c.lat || 37.5665,
          lon: c.lon || 126.9780,
          description: c.description,
          country: c.country || '한국',
          city: c.location,
          domains: c.focus ? [c.focus] : [],
          is_hiring: false
        })),
        ...(data.investors || []).map((inv: any, idx: number) => ({
          id: inv.id || idx + 300,
          name: inv.name,
          type: inv.type || 'investor',
          lat: inv.lat || 37.5665,
          lon: inv.lon || 126.9780,
          description: inv.description,
          country: inv.country || '한국',
          city: inv.location,
          domains: inv.category ? [inv.category] : [],
          is_hiring: false,
          investment_focus: inv.investment_focus || [],
          preferred_stages: inv.preferred_stages || [],
          portfolio_count: inv.portfolio_count || 0
        }))
      ]
      
      // 같은 좌표는 하나의 클러스터로 묶음 (단, 투자자/액셀러레이터는 좌표가 분산되어 있으므로 개별 마커로 표시)
      const coordToEntities = new Map<string, Entity[]>()
      const key = (lat: number, lon: number) => `${lat.toFixed(5)}_${lon.toFixed(5)}`
      allEntities.forEach(entity => {
        const k = key(entity.lat, entity.lon)
        const list = coordToEntities.get(k) ?? []
        list.push(entity)
        coordToEntities.set(k, list)
      })
      const clusters: Cluster[] = Array.from(coordToEntities.entries()).map(([, entities]) => {
        // 투자자나 액셀러레이터는 같은 좌표에 있어도 개별 마커로 표시 (필터링 시 구분을 위해)
        // 단, 같은 타입끼리만 묶음
        const typeGroups = new Map<string, Entity[]>()
        entities.forEach(e => {
          const type = e.type || 'startup'
          if (!typeGroups.has(type)) typeGroups.set(type, [])
          typeGroups.get(type)!.push(e)
        })
        
        // 여러 타입이 섞여있으면 각 타입별로 클러스터 분리
        if (typeGroups.size > 1) {
          return Array.from(typeGroups.entries()).map(([, typeEntities]) => ({
            lat: typeEntities[0].lat,
            lon: typeEntities[0].lon,
            count: typeEntities.length,
            entities: typeEntities
          }))
        }
        
        // 같은 타입만 있으면 하나의 클러스터로
        return {
          lat: entities[0].lat,
          lon: entities[0].lon,
          count: entities.length,
          entities
        }
      }).flat()
      
      setClusters(clusters)
      
      // 마커는 useEffect에서 filteredClusters 기준으로 갱신됨
      
      // 한국 중심으로 지도 이동 (서울 기준, 줌 7로 전국이 보이도록)
      map.current?.flyTo({
        center: [126.9780, 37.5665],
        zoom: 7
      })
      
      setIsUsingMockData(false)
      setApiError(null)
      
      console.log(`✅ ${clusters.length}개 엔티티 로드 완료`)
      
    } catch (error) {
      console.error('지도 데이터 로드 실패:', error)
      const mockData = generateMockData()
      setClusters(mockData)
      setIsUsingMockData(true)
      const isNetworkError =
        error instanceof TypeError && (error.message === 'Failed to fetch' || (error as Error).message?.includes('fetch'))
      setApiError(
        isNetworkError
          ? '사이트에 연결할 수 없습니다. 로컬에서는 터미널에서 "cd frontend && npm run dev" 실행 후 http://localhost:3000/explore 로 접속해 주세요.'
          : '실제 데이터를 불러오는데 실패했습니다. 임시 데이터를 표시합니다.'
      )
    }
  }

  const loadClusters = (bounds: mapboxgl.LngLatBounds) => {
    if (!map.current) return
    try {
      // 전체 클러스터에 현재 필터 타입 적용 후, 화면 bounds로 한 번 더 필터 (moveend 시에도 타입 필터 유지)
      const full = allClustersRef.current
      const typeFiltered = filterClustersByType(full, filterTypeRef.current)
      const inBounds = typeFiltered.filter(cluster =>
        cluster.lat >= bounds.getSouth() &&
        cluster.lat <= bounds.getNorth() &&
        cluster.lon >= bounds.getWest() &&
        cluster.lon <= bounds.getEast()
      )
      updateMapMarkers(inBounds)
    } catch (error) {
      console.error('클러스터 데이터 로드 실패:', error)
    }
  }

  // API 응답 데이터를 클러스터 형태로 변환하는 함수
  const transformApiDataToClusters = (apiData: any): Cluster[] => {
    try {
      // API 응답 구조에 따라 데이터 변환
      if (apiData.entities && Array.isArray(apiData.entities)) {
        // 엔티티 배열이 있는 경우
        return apiData.entities.map((entity: any) => ({
          lat: entity.latitude || entity.lat || 0,
          lon: entity.longitude || entity.lon || 0,
          count: 1,
          entities: [{
            id: entity.id,
            name: entity.name,
            type: entity.type || 'startup',
            lat: entity.latitude || entity.lat || 0,
            lon: entity.longitude || entity.lon || 0,
            description: entity.description,
            country: entity.country,
            city: entity.city,
            domains: entity.domains || [],
            last_funding_round: entity.last_funding_round,
            is_hiring: entity.is_hiring || false
          }]
        }))
      } else if (apiData.clusters && Array.isArray(apiData.clusters)) {
        // 클러스터 배열이 있는 경우
        return apiData.clusters.map((cluster: any) => ({
          lat: cluster.lat || cluster.latitude || 0,
          lon: cluster.lon || cluster.longitude || 0,
          count: cluster.count || 1,
          entities: cluster.entities || []
        }))
      } else {
        // 기타 형태의 데이터
        console.warn('알 수 없는 API 응답 구조:', apiData)
        return generateMockData()
      }
    } catch (error) {
      console.error('API 데이터 변환 실패:', error)
      return generateMockData()
    }
  }

  // 검색 기능 추가
  const searchStartups = async (query: string) => {
    if (!query.trim()) {
      // 검색어가 없으면 전체 데이터 다시 로드
      loadMapData()
      return
    }
    
    setIsSearching(true)
    try {
      // 현재 클러스터 데이터에서 검색
      const searchResults = clusters.filter(cluster => {
        if (cluster.count === 1) {
          const entity = cluster.entities[0]
          return entity.name.toLowerCase().includes(query.toLowerCase()) ||
                 entity.description?.toLowerCase().includes(query.toLowerCase()) ||
                 entity.city?.toLowerCase().includes(query.toLowerCase()) ||
                 entity.domains?.some(domain => domain.toLowerCase().includes(query.toLowerCase()))
        }
        return false
      })
      
      if (searchResults.length > 0) {
        setClusters(searchResults)
        updateMapMarkers(searchResults)
        
        // 검색 결과가 있으면 첫 번째 결과로 지도 이동
        const firstCluster = searchResults[0]
        map.current?.flyTo({
          center: [firstCluster.lon, firstCluster.lat],
          zoom: 10
        })
        
        setApiError(`"${query}" 검색 결과: ${searchResults.length}개 발견`)
      } else {
        // 검색 결과가 없으면 메시지 표시
        setApiError(`"${query}" 검색 결과가 없습니다.`)
      }
      
    } catch (error) {
      console.error('검색 실패:', error)
      setApiError('검색 중 오류가 발생했습니다.')
    } finally {
      setIsSearching(false)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    searchStartups(searchQuery)
  }

  const getMarkerColor = (type: string): string => {
    switch (type) {
      case 'startup':
        return '#3B82F6' // 파란색
      case 'investor':
        return '#10B981' // 초록색
      case 'accelerator':
        return '#8B5CF6' // 보라색
      case 'space':
      case 'coworking_space':
        return '#F59E0B' // 주황색
      case 'event':
        return '#EF4444' // 빨간색
      default:
        return '#6B7280' // 회색
    }
  }

  const getMarkerIcon = (type: string): string => {
    switch (type) {
      case 'startup':
        return '🏢'
      case 'investor':
        return '💰'
      case 'accelerator':
        return '🚀'
      case 'space':
      case 'coworking_space':
        return '🏢'
      case 'event':
        return '📅'
      default:
        return '📍'
    }
  }

  const addMarkersToMap = (data: Cluster[]) => {
    if (!map.current) return

    data.forEach(cluster => {
      // 클러스터 마커 생성 - 더 깔끔한 디자인
      const el = document.createElement('div')
      el.className = 'cluster-marker'
      
      if (cluster.count === 1) {
        // 단일 회사 마커
        const entity = cluster.entities[0]
        const color = getMarkerColor(entity.type)
        const icon = getMarkerIcon(entity.type)
        
        el.innerHTML = `
          <div class="marker-single" style="
            background: ${color};
            color: white;
            border-radius: 50%;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            cursor: pointer;
            transition: transform 0.2s;
          " onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">
            ${icon}
          </div>
        `
      } else {
        // 클러스터 마커 (숫자 없이 표시)
        const entity = cluster.entities[0]
        const color = getMarkerColor(entity.type)
        const icon = getMarkerIcon(entity.type)
        el.innerHTML = `
          <div class="marker-cluster" style="
            background: ${color};
            color: white;
            border-radius: 50%;
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            cursor: pointer;
            transition: transform 0.2s;
          " onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">
            ${icon}
          </div>
        `
      }
      
      // 마커 클릭 이벤트
      el.addEventListener('click', () => {
        setSelectedEntity(cluster.entities[0])
        if (cluster.count > 1) {
          map.current?.flyTo({
            center: [cluster.lon, cluster.lat],
            zoom: Math.min((map.current?.getZoom() ?? 7) + 2, 18)
          })
        }
      })

      // 지도에 마커 추가
      new mapboxgl.Marker(el)
        .setLngLat([cluster.lon, cluster.lat])
        .addTo(map.current)
    })
  }

  const updateMapMarkers = (data: Cluster[]) => {
    if (!map.current) return

    // 기존 마커 제거
    const markers = document.querySelectorAll('.mapboxgl-marker')
    markers.forEach(marker => marker.remove())

    // 새 마커 추가
    addMarkersToMap(data)
  }

  const generateMockData = (): Cluster[] => {
    return [
      // 한국 스타트업
      {
        lat: 37.5665,
        lon: 127.7669,
        count: 1,
        entities: [{
          id: 1,
          name: "Kakao",
          type: "startup",
          lat: 37.5665,
          lon: 127.7669,
          description: "한국의 대표적인 인터넷 기업으로 AI, 모빌리티, 핀테크 등 다양한 분야에서 혁신적인 서비스를 제공합니다.",
          country: "Korea",
          city: "Seoul",
          domains: ["AI", "Mobility", "Fintech", "Platform"],
          last_funding_round: "Series D",
          is_hiring: true
        }]
      },
      {
        lat: 37.5665,
        lon: 126.978,
        count: 1,
        entities: [{
          id: 2,
          name: "LG Chem",
          type: "startup",
          lat: 37.5665,
          lon: 126.978,
          description: "LG화학의 생명과학 사업부로 바이오의약품, 세포치료제 등 혁신적인 의료 솔루션을 개발합니다.",
          country: "Korea",
          city: "Seoul",
          domains: ["Biotech", "Healthcare", "Pharma", "Cell Therapy"],
          last_funding_round: "Corporate",
          is_hiring: false
        }]
      },
      {
        lat: 37.5665,
        lon: 127.001,
        count: 1,
        entities: [{
          id: 3,
          name: "Naver",
          type: "startup",
          lat: 37.5665,
          lon: 127.001,
          description: "한국의 대표적인 인터넷 기업으로 검색, AI, 클라우드, 로봇 등 다양한 기술 분야에서 혁신을 이끌고 있습니다.",
          country: "Korea",
          city: "Seoul",
          domains: ["AI", "Search", "Cloud", "Robotics", "Platform"],
          last_funding_round: "IPO",
          is_hiring: true
        }]
      },
      
      // 미국 스타트업
      {
        lat: 37.7749,
        lon: -122.4194,
        count: 1,
        entities: [{
          id: 4,
          name: "Uber",
          type: "startup",
          lat: 37.7749,
          lon: -122.4194,
          description: "글로벌 모빌리티 플랫폼으로 자율주행, 전기차, 배송 등 다양한 모빌리티 서비스를 제공합니다.",
          country: "USA",
          city: "San Francisco",
          domains: ["Mobility", "AI", "Autonomous Driving", "Logistics"],
          last_funding_round: "IPO",
          is_hiring: false
        }]
      },
      {
        lat: 40.7128,
        lon: -74.0060,
        count: 1,
        entities: [{
          id: 5,
          name: "WeWork",
          type: "space",
          lat: 40.7128,
          lon: -74.0060,
          description: "공유 오피스 공간을 제공하는 글로벌 기업으로 유연한 근무 환경과 커뮤니티를 만들어갑니다.",
          country: "USA",
          city: "New York",
          domains: ["Real Estate", "PropTech", "Coworking", "Community"],
          last_funding_round: "Series G",
          is_hiring: true
        }]
      },
      {
        lat: 42.3601,
        lon: -71.0589,
        count: 1,
        entities: [{
          id: 6,
          name: "Whoop",
          type: "startup",
          lat: 42.3601,
          lon: -71.0589,
          description: "피트니스 및 회복 추적 웨어러블을 제공하는 기업으로 운동 성과와 신체 회복 상태를 정확하게 측정합니다.",
          country: "USA",
          city: "Boston",
          domains: ["HealthTech", "Wearables", "Fitness", "Biometrics"],
          last_funding_round: "Series F",
          is_hiring: true
        }]
      },
      {
        lat: 37.3382,
        lon: -121.8863,
        count: 1,
        entities: [{
          id: 7,
          name: "Apple",
          type: "startup",
          lat: 37.3382,
          lon: -121.8863,
          description: "혁신적인 하드웨어와 소프트웨어를 만드는 글로벌 테크 기업으로 AI, AR, 헬스케어 등 다양한 분야에서 혁신을 이끌고 있습니다.",
          country: "USA",
          city: "Cupertino",
          domains: ["Hardware", "Software", "AI", "AR/VR", "Healthcare"],
          last_funding_round: "Corporate",
          is_hiring: true
        }]
      },
      
      // 유럽 스타트업
      {
        lat: 48.823,
        lon: 2.27,
        count: 1,
        entities: [{
          id: 8,
          name: "Withings",
          type: "startup",
          lat: 48.823,
          lon: 2.27,
          description: "스마트 헬스 디바이스를 제공하는 프랑스 기업으로 체중계, 혈압계, 수면 추적기 등을 통해 건강을 모니터링합니다.",
          country: "France",
          city: "Paris",
          domains: ["HealthTech", "IoT", "Wearables", "Digital Health"],
          last_funding_round: "Series B",
          is_hiring: false
        }]
      },
      {
        lat: 60.1699,
        lon: 24.9384,
        count: 1,
        entities: [{
          id: 9,
          name: "Oura",
          type: "startup",
          lat: 60.1699,
          lon: 24.9384,
          description: "스마트 링 기반 건강 추적 기술을 제공하는 핀란드 기업으로 수면, 회복, 활동을 정확하게 측정합니다.",
          country: "Finland",
          city: "Helsinki",
          domains: ["HealthTech", "Wearables", "Sleep", "Biometrics"],
          last_funding_round: "Series C",
          is_hiring: true
        }]
      },
      {
        lat: 52.5200,
        lon: 13.4050,
        count: 1,
        entities: [{
          id: 10,
          name: "N26",
          type: "startup",
          lat: 52.5200,
          lon: 13.4050,
          description: "유럽의 디지털 뱅킹 플랫폼으로 모바일 우선의 은행 서비스를 제공하며 금융 혁신을 이끌고 있습니다.",
          country: "Germany",
          city: "Berlin",
          domains: ["Fintech", "Digital Banking", "Mobile", "Financial Services"],
          last_funding_round: "Series E",
          is_hiring: true
        }]
      },
      
      // 아시아 스타트업
      {
        lat: 35.6895,
        lon: 139.6917,
        count: 1,
        entities: [{
          id: 11,
          name: "Takeda",
          type: "startup",
          lat: 35.6895,
          lon: 139.6917,
          description: "일본 최대 제약회사로 혁신적인 의약품 개발과 글로벌 헬스케어 솔루션을 제공합니다.",
          country: "Japan",
          city: "Tokyo",
          domains: ["Pharma", "Biotech", "Healthcare", "Drug Development"],
          last_funding_round: "Corporate",
          is_hiring: true
        }]
      },
      {
        lat: 39.9042,
        lon: 116.4074,
        count: 1,
        entities: [{
          id: 12,
          name: "Xiaomi",
          type: "startup",
          lat: 39.9042,
          lon: 116.4074,
          description: "스마트폰과 IoT 기기를 만드는 중국 기업으로 AI, 자동차, 로봇 등 다양한 분야에서 혁신을 이끌고 있습니다.",
          country: "China",
          city: "Beijing",
          domains: ["Hardware", "IoT", "AI", "Automotive", "Robotics"],
          last_funding_round: "IPO",
          is_hiring: false
        }]
      },
      {
        lat: 22.3193,
        lon: 114.1694,
        count: 1,
        entities: [{
          id: 13,
          name: "SenseTime",
          type: "startup",
          lat: 22.3193,
          lon: 114.1694,
          description: "AI 컴퓨터 비전 기술을 전문으로 하는 홍콩 기업으로 얼굴 인식, 자율주행, 스마트 시티 등 다양한 분야에 AI를 적용합니다.",
          country: "Hong Kong",
          city: "Hong Kong",
          domains: ["AI", "Computer Vision", "Autonomous Driving", "Smart City"],
          last_funding_round: "Series D",
          is_hiring: true
        }]
      },
      
      // 호주 스타트업
      {
        lat: -33.8688,
        lon: 151.2093,
        count: 1,
        entities: [{
          id: 14,
          name: "Canva",
          type: "startup",
          lat: -33.8688,
          lon: 151.2093,
          description: "온라인 디자인 플랫폼을 제공하는 호주 기업으로 누구나 쉽게 전문적인 디자인을 만들 수 있도록 도와줍니다.",
          country: "Australia",
          city: "Sydney",
          domains: ["Design", "SaaS", "Creative Tools", "Platform"],
          last_funding_round: "Series H",
          is_hiring: true
        }]
      }
    ]
  }

  return (
    <div className="relative h-screen">
      {/* 지도 컨테이너 */}
      <div ref={mapContainer} className="w-full h-full" />

      {/* 위치 안내: 정확한 주소가 없으면 도시 중심으로 표시됨 */}
      {!isLoading && !isUsingMockData && (
        <div className="absolute bottom-6 left-4 bg-white/90 backdrop-blur text-gray-600 text-xs rounded-lg shadow px-3 py-2 z-10 max-w-xs">
          📍 위치는 제공된 지역(도시) 정보 기준이며, 정확한 주소가 없으면 도시 중심에 표시됩니다.
        </div>
      )}
      
      {/* 로딩 오버레이 */}
      {isLoading && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10">
          <div className="text-center">
            <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-xl text-gray-600">지도를 로딩 중입니다...</p>
          </div>
        </div>
      )}

      {/* API 에러 메시지 */}
      {apiError && (
        <div className="absolute top-4 left-4 bg-blue-50 border border-blue-200 rounded-lg shadow-lg p-4 max-w-md z-20">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">정보</h3>
              <div className="mt-2 text-sm text-blue-700">
                <p>{apiError}</p>
                {isUsingMockData && (
                  <p className="mt-2 text-xs">
                    💡 현재 임시 데이터를 표시하고 있습니다. 백엔드 서버가 정상화되면 실제 데이터를 불러옵니다.
                  </p>
                )}
              </div>
              <div className="mt-4">
                <button
                  type="button"
                  onClick={() => {
                    setApiError(null)
                    setIsUsingMockData(false)
                    loadMapData()
                  }}
                  className="bg-blue-50 text-blue-800 border border-blue-200 rounded-md px-3 py-2 text-sm font-medium hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  새로고침
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Mock 데이터 사용 안내 */}
      {isUsingMockData && !apiError && (
        <div className="absolute top-4 left-4 bg-blue-50 border border-blue-200 rounded-lg shadow-lg p-4 max-w-md z-20">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">임시 데이터 사용 중</h3>
              <div className="mt-2 text-sm text-blue-700">
                <p>백엔드 서버가 실행되지 않아 임시 데이터를 표시합니다.</p>
                <p className="mt-1 text-xs">실제 데이터를 보려면 백엔드 서버를 실행하세요.</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 선택된 엔티티 정보 - 더 깔끔한 디자인 */}
      {selectedEntity && (
        <div className="absolute top-4 left-4 bg-white rounded-lg shadow-xl p-6 max-w-sm z-20 border border-gray-200">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h3 className="text-xl font-bold text-gray-900 mb-1">{selectedEntity.name}</h3>
              <p className="text-sm text-gray-500">{selectedEntity.city}, {selectedEntity.country}</p>
            </div>
            <button
              onClick={() => setSelectedEntity(null)}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <div className="space-y-4">
            {selectedEntity.description && (
              <div>
                <p className="text-sm text-gray-700 leading-relaxed">{selectedEntity.description}</p>
              </div>
            )}
            
            {selectedEntity.domains && selectedEntity.domains.length > 0 && (
              <div>
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">도메인</span>
                <div className="mt-2 flex flex-wrap gap-2">
                  {selectedEntity.domains.map((domain, index) => (
                    <span
                      key={index}
                      className="inline-block bg-blue-100 text-blue-800 text-xs px-3 py-1 rounded-full font-medium"
                    >
                      {domain}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* 투자자 정보: 투자 성향 및 선호 단계 */}
            {selectedEntity.type === 'investor' && (
              <>
                {selectedEntity.investment_focus && selectedEntity.investment_focus.length > 0 && (
                  <div>
                    <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">투자 성향</span>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {selectedEntity.investment_focus.map((focus, index) => (
                        <span
                          key={index}
                          className="inline-block bg-green-100 text-green-800 text-xs px-3 py-1 rounded-full font-medium"
                        >
                          {focus}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {selectedEntity.preferred_stages && selectedEntity.preferred_stages.length > 0 && (
                  <div>
                    <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">선호 투자 단계</span>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {selectedEntity.preferred_stages.map((stage, index) => (
                        <span
                          key={index}
                          className="inline-block bg-purple-100 text-purple-800 text-xs px-3 py-1 rounded-full font-medium"
                        >
                          {stage}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {selectedEntity.portfolio_count && selectedEntity.portfolio_count > 0 && (
                  <div>
                    <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">포트폴리오</span>
                    <p className="text-sm font-medium text-gray-900 mt-1">{selectedEntity.portfolio_count}개 회사</p>
                  </div>
                )}
              </>
            )}
            
            <div className="grid grid-cols-2 gap-4 pt-2 border-t border-gray-100">
              {selectedEntity.last_funding_round && (
                <div>
                  <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">최근 펀딩</span>
                  <p className="text-sm font-medium text-gray-900 mt-1">{selectedEntity.last_funding_round}</p>
                </div>
              )}
              
              <div>
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">채용 중</span>
                <p className={`text-sm font-medium mt-1 ${selectedEntity.is_hiring ? 'text-green-600' : 'text-red-600'}`}>
                  {selectedEntity.is_hiring ? '예' : '아니오'}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 지도 컨트롤 - 더 깔끔한 디자인 */}
      <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-xl p-4 z-20 border border-gray-200">
        <div className="space-y-3">
          <button
            onClick={() => map.current?.flyTo({ center: [127.7669, 37.5665], zoom: 8 })}
            className="block w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            🇰🇷 서울
          </button>
          <button
            onClick={() => map.current?.flyTo({ center: [-122.4194, 37.7749], zoom: 8 })}
            className="block w-full bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            🇺🇸 샌프란시스코
          </button>
          <button
            onClick={() => map.current?.flyTo({ center: [-74.0060, 40.7128], zoom: 8 })}
            className="block w-full bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            🇺🇸 뉴욕
          </button>
          <button
            onClick={() => map.current?.flyTo({ center: [0, 20], zoom: 2 })}
            className="block w-full bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            🌍 전 세계
          </button>
        </div>
      </div>

      {/* 검색 폼, 필터, 범례 */}
      <div className="absolute top-4 right-4 bg-white rounded-lg shadow-xl p-4 z-20 border border-gray-200">
        {/* 검색 폼 */}
        <form onSubmit={handleSearch} className="flex items-center mb-4">
          <input
            type="text"
            placeholder="스타트업 검색 (예: AI, Fintech, HealthTech)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 mr-2 text-sm flex-1 min-w-48"
            disabled={isSearching}
          />
          <button
            type="submit"
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            disabled={isSearching}
          >
            {isSearching ? '검색 중...' : '🔍'}
          </button>
        </form>

        {/* 타입별 필터: 클릭 시 해당 타입만 지도에 표시 */}
        <div className="border-t border-gray-100 pt-3 pb-3">
          <h4 className="text-sm font-semibold text-gray-900 mb-2">표시</h4>
          <div className="flex flex-wrap gap-1.5">
            {([
              { value: 'all' as const, label: '전체' },
              { value: 'startup' as const, label: '스타트업' },
              { value: 'investor' as const, label: '투자자' },
              { value: 'accelerator' as const, label: '액셀러레이터' },
              { value: 'coworking_space' as const, label: '코워킹' }
            ]).map(({ value, label }) => (
              <button
                key={value}
                type="button"
                onClick={() => setFilterType(value)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  filterType === value
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
        
        {/* 범례 */}
        <div className="border-t border-gray-100 pt-3">
          <h4 className="text-sm font-semibold text-gray-900 mb-3">범례</h4>
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-blue-500 rounded-full"></div>
              <span className="text-xs text-gray-600">스타트업</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-green-500 rounded-full"></div>
              <span className="text-xs text-gray-600">투자자</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-purple-500 rounded-full"></div>
              <span className="text-xs text-gray-600">액셀러레이터</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-orange-500 rounded-full"></div>
              <span className="text-xs text-gray-600">코워킹/공간</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-red-500 rounded-full"></div>
              <span className="text-xs text-gray-600">이벤트</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
