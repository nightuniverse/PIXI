'use client'

import { useState, useEffect, useMemo } from 'react'

interface Entity {
  id: number
  name: string
  description?: string
  category?: string
  type: string
  website?: string
  location?: string
  country?: string
}

interface MarketAnalysis {
  totalCompanies: number
  byStage: Record<string, number>
  byLocation: Record<string, number>
  topCompanies: Entity[]
  marketGaps: string[]
  differentiationPoints: string[]
}

export default function StartupIdeaAnalyzer() {
  const [data, setData] = useState<{ startups: Entity[] } | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [userIdea, setUserIdea] = useState<string>('')
  const [analysis, setAnalysis] = useState<MarketAnalysis | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // 데이터 로드
    fetch('/data/koreanEcosystemData.json')
      .then(res => res.json())
      .then(json => {
        setData(json)
        setLoading(false)
      })
      .catch(err => {
        console.error('데이터 로드 실패:', err)
        setLoading(false)
      })
  }, [])

  // 카테고리 목록 추출
  const categories = useMemo(() => {
    if (!data?.startups) return []
    const cats = new Set<string>()
    
    // 실제 카테고리 추출
    data.startups.forEach(startup => {
      if (startup.category && 
          startup.category !== '스타트업' && 
          startup.name.length < 100) {
        cats.add(startup.category)
      }
    })
    
    // 키워드 기반 카테고리 추가 (검색 가능한 카테고리)
    const keywordCategories = [
      'SaaS', 'AI', '핀테크', '이커머스', '헬스케어', '생명공학', 
      '교육', '엔터테인먼트', '로봇', '블록체인', '모빌리티', '부동산', '음식'
    ]
    keywordCategories.forEach(kw => cats.add(kw))
    
    return Array.from(cats).sort()
  }, [data])

  // 시장 분석 수행
  const analyzeMarket = () => {
    if (!data?.startups || !selectedCategory) return

    const categoryLower = selectedCategory.toLowerCase()
    
    // 키워드 매핑 (카테고리 -> 검색 키워드)
    const keywordMap: Record<string, string[]> = {
      'saas': ['saas', '소프트웨어', '소프트웨어서비스', '소프트웨어 서비스', 's/w', 'sw', '플랫폼', '클라우드', '서비스', '솔루션'],
      'ai': ['ai', '인공지능', '머신러닝', '딥러닝', 'ml', 'deep learning', '에이전트'],
      '핀테크': ['핀테크', 'fintech', '금융', '결제', '은행', '투자', '토스'],
      '이커머스': ['이커머스', 'ecommerce', '전자상거래', '쇼핑', '온라인쇼핑', '쿠팡'],
      '헬스케어': ['헬스케어', 'healthcare', '의료', '건강', '병원', '치료', '의약'],
      '생명공학': ['생명공학', '바이오', 'bio', 'biotech', '제약', '의약', '바이오테크', '생명', '의료기기'],
      '교육': ['교육', 'education', '에듀', '학습', '온라인교육', 'e-learning', '강의'],
      '엔터테인먼트': ['엔터테인먼트', 'entertainment', '게임', '콘텐츠', '미디어'],
      '로봇': ['로봇', 'robot', 'robotics', '자동화'],
      '블록체인': ['블록체인', 'blockchain', '암호화폐', 'crypto', 'nft'],
      '모빌리티': ['모빌리티', 'mobility', '교통', '택시', '자율주행', '전기차'],
      '부동산': ['부동산', 'real estate', '임대', '매매'],
      '음식': ['음식', 'food', '배달', '레스토랑', '식품']
    }

    // 사용자 아이디어에서 키워드 추출
    const ideaKeywords: string[] = []
    if (userIdea) {
      const ideaLower = userIdea.toLowerCase()
      // 아이디어에서 주요 키워드 추출
      Object.values(keywordMap).flat().forEach(kw => {
        if (ideaLower.includes(kw.toLowerCase())) {
          ideaKeywords.push(kw)
        }
      })
      // 생명공학 관련 특별 처리
      if (ideaLower.includes('생명') || ideaLower.includes('바이오') || ideaLower.includes('bio')) {
        ideaKeywords.push('생명공학', '바이오', 'bio', 'biotech')
      }
    }

    // 검색 키워드 추출 (카테고리 + 아이디어 키워드)
    const searchKeywords = [
      ...(keywordMap[categoryLower] || [categoryLower]),
      ...ideaKeywords
    ]

    // 필터링: 뉴스 기사 제외 (제목이 너무 긴 것들)
    const filtered = data.startups.filter(s => {
      // 뉴스 기사 제외 (제목이 80자 이상이거나 특정 패턴 포함)
      const isNews = s.name.length > 80 || 
                     s.name.includes('실증') || 
                     s.name.includes('선정') ||
                     s.name.includes('공식') ||
                     s.name.includes('전화성의') ||
                     s.name.includes('모닝커피') ||
                     s.name.includes('...') ||
                     s.name.includes('더 읽기')
      
      if (isNews) return false

      // 카테고리 매칭
      const catMatch = s.category?.toLowerCase() === categoryLower
      
      // 키워드 매칭 (name, description에서)
      const nameLower = (s.name || '').toLowerCase()
      const descLower = (s.description || '').toLowerCase()
      
      const keywordMatch = searchKeywords.some(kw => 
        nameLower.includes(kw.toLowerCase()) || 
        descLower.includes(kw.toLowerCase())
      )

      return catMatch || keywordMatch
    })

    // 투자 단계별 분포 (description에서 추출)
    const byStage: Record<string, number> = {}
    filtered.forEach(s => {
      const desc = (s.description || s.name || '').toLowerCase()
      let matched = false
      
      if (desc.includes('series a') || desc.includes('시리즈 a') || desc.includes('series-a')) {
        byStage['Series A'] = (byStage['Series A'] || 0) + 1
        matched = true
      }
      if (desc.includes('series b') || desc.includes('시리즈 b') || desc.includes('series-b')) {
        byStage['Series B'] = (byStage['Series B'] || 0) + 1
        matched = true
      }
      if (desc.includes('series c') || desc.includes('시리즈 c') || desc.includes('series-c')) {
        byStage['Series C'] = (byStage['Series C'] || 0) + 1
        matched = true
      }
      if (desc.includes('seed') || desc.includes('시드') || desc.includes('프리시드')) {
        byStage['Seed'] = (byStage['Seed'] || 0) + 1
        matched = true
      }
      if (desc.includes('ipo') || desc.includes('상장')) {
        byStage['IPO'] = (byStage['IPO'] || 0) + 1
        matched = true
      }
      
      if (!matched) {
        byStage['기타'] = (byStage['기타'] || 0) + 1
      }
    })

    // 지역별 분포
    const byLocation: Record<string, number> = {}
    filtered.forEach(s => {
      const loc = s.location || '기타'
      byLocation[loc] = (byLocation[loc] || 0) + 1
    })

    // 주요 회사 (최대 10개)
    const topCompanies = filtered.slice(0, 10)

    // 시장 공백 분석
    const marketGaps = analyzeMarketGaps(filtered, selectedCategory)
    
    // 차별화 포인트 제안
    const differentiationPoints = suggestDifferentiation(filtered, selectedCategory, userIdea)

    // 데이터가 없어도 분석 결과는 표시 (시장 기회와 차별화 포인트는 항상 제공)
    setAnalysis({
      totalCompanies: filtered.length,
      byStage: filtered.length > 0 ? byStage : {},
      byLocation: filtered.length > 0 ? byLocation : {},
      topCompanies,
      marketGaps,
      differentiationPoints
    })
  }

  // 시장 공백 분석
  const analyzeMarketGaps = (companies: Entity[], category: string): string[] => {
    const gaps: string[] = []
    
    if (companies.length === 0) {
      return ['이 카테고리는 아직 시장이 형성되지 않았습니다. 선도 진입 기회가 있습니다!']
    }

    // 지역별 공백
    const locations = new Set(companies.map(c => c.location).filter(Boolean))
    if (locations.size < 3 && companies.length >= 5) {
      const mainLocations = Array.from(locations).slice(0, 3)
      gaps.push(`지역 다양성 부족: 대부분 ${mainLocations.join(', ')}에 집중되어 있습니다. 다른 지역 진출 기회가 있습니다.`)
    }

    // 서비스 유형 분석
    const descriptions = companies.map(c => (c.description || c.name || '').toLowerCase()).filter(Boolean)
    
    // 기술 키워드 분석
    const techKeywords = ['ai', '인공지능', '블록체인', 'iot', '빅데이터', '클라우드', '머신러닝']
    const hasTech = descriptions.some(d => techKeywords.some(kw => d.includes(kw)))
    
    if (!hasTech && companies.length >= 3) {
      gaps.push(`기술 혁신 기회: ${category} 분야에 AI/블록체인 등 최신 기술을 접목할 수 있는 기회가 있습니다.`)
    }

    // B2B vs B2C 분석
    const b2bKeywords = ['b2b', '기업', 'enterprise', '비즈니스', '사업자']
    const b2cKeywords = ['b2c', '소비자', 'consumer', '개인', '일반']
    
    const b2bCount = descriptions.filter(d => b2bKeywords.some(kw => d.includes(kw))).length
    const b2cCount = descriptions.filter(d => b2cKeywords.some(kw => d.includes(kw))).length

    if (b2bCount === 0 && b2cCount > 0 && companies.length >= 3) {
      gaps.push('B2B 시장 진입 기회: 현재 대부분 B2C 서비스입니다. 기업용 솔루션으로 차별화할 수 있습니다.')
    } else if (b2cCount === 0 && b2bCount > 0 && companies.length >= 3) {
      gaps.push('B2C 시장 진입 기회: 현재 대부분 B2B 서비스입니다. 개인 사용자 대상 서비스로 진입할 수 있습니다.')
    }

    // 가격대 분석
    if (companies.length >= 5) {
      gaps.push('가격 전략 차별화: 프리미엄 또는 가격 경쟁력 있는 모델로 시장에 진입할 수 있습니다.')
    }

    // 니치 마켓 기회
    if (companies.length < 5) {
      gaps.push('니치 마켓 기회: 시장이 작아 경쟁이 적습니다. 특정 타겟에 집중하면 성공 가능성이 높습니다.')
    } else if (companies.length >= 10) {
      gaps.push('성숙한 시장: 경쟁이 치열합니다. 강력한 차별화와 명확한 타겟팅이 필수입니다.')
    }

    return gaps.length > 0 ? gaps : ['시장 분석을 위해 더 많은 데이터가 필요합니다.']
  }

  // 차별화 포인트 제안
  const suggestDifferentiation = (companies: Entity[], category: string, userIdea: string): string[] => {
    const points: string[] = []
    
    // 기술 기반 차별화
    const techKeywords = ['ai', '인공지능', '블록체인', 'iot', '빅데이터', '클라우드', '머신러닝']
    const descriptions = companies.map(c => (c.description || c.name || '').toLowerCase())
    const hasTech = descriptions.some(d => techKeywords.some(kw => d.includes(kw)))
    
    if (!hasTech && companies.length > 0) {
      points.push(`기술 기반 혁신: ${category} 분야에 AI/블록체인 등 최신 기술을 접목하여 차별화할 수 있습니다.`)
    } else if (hasTech) {
      points.push('기술 고도화: 기존 기술을 더 발전시켜 성능과 효율성을 극대화')
    }

    // 사용자 경험 차별화
    points.push('사용자 경험 개선: 기존 서비스의 불편함을 해결하는 직관적이고 간편한 UX/UI 제공')

    // 가격 전략
    if (companies.length >= 5) {
      points.push('가격 전략 차별화: 프리미엄 모델 또는 가격 경쟁력 있는 모델로 시장 포지셔닝')
    }

    // 타겟 고객 세분화
    if (userIdea) {
      const ideaLower = userIdea.toLowerCase()
      if (ideaLower.includes('ai') || ideaLower.includes('인공지능')) {
        points.push('AI 기반 자동화: 반복적인 작업을 AI로 자동화하여 효율성 극대화')
      }
      if (ideaLower.includes('모바일') || ideaLower.includes('앱')) {
        points.push('모바일 퍼스트: 모바일 환경에 최적화된 경험 제공')
      }
      points.push(`타겟 고객 특화: "${userIdea}"에 특화된 맞춤형 솔루션 제공`)
    } else {
      points.push('타겟 고객 세분화: 특정 니즈를 가진 소규모 타겟 그룹에 집중하여 깊이 있는 서비스 제공')
    }

    // 지역 특화
    const locations = new Set(companies.map(c => c.location).filter(Boolean))
    if (locations.size < 3) {
      points.push('지역 특화: 특정 지역/도시의 로컬 니즈에 맞춘 서비스로 차별화')
    }

    // 데이터 기반 인사이트
    if (companies.length >= 3) {
      points.push('데이터 기반 의사결정: 사용자 데이터를 분석하여 개인화된 경험 제공')
    }

    // 파트너십 전략
    points.push('전략적 파트너십: 기존 플랫폼이나 서비스와의 연계를 통한 시너지 창출')

    // 지속가능성
    points.push('지속가능성: 환경/사회적 가치를 추구하는 ESG 경영으로 브랜드 차별화')

    return points
  }

  useEffect(() => {
    if (selectedCategory && data?.startups) {
      analyzeMarket()
    } else {
      // 카테고리가 없으면 분석 초기화
      setAnalysis(null)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCategory, data, userIdea])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* 입력 섹션 */}
      <div className="bg-white rounded-xl shadow-lg p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">아이템 입력</h2>
        
        <div className="space-y-6">
          {/* 카테고리 선택 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              관심 카테고리 선택
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
              style={{ color: '#111827' }}
            >
              <option value="" style={{ color: '#111827' }}>카테고리를 선택하세요</option>
              {categories.map(cat => (
                <option key={cat} value={cat} style={{ color: '#111827' }}>{cat}</option>
              ))}
            </select>
          </div>

          {/* 아이디어 입력 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              아이디어 설명 (선택사항)
            </label>
            <textarea
              value={userIdea}
              onChange={(e) => setUserIdea(e.target.value)}
              placeholder="예: AI 기반 개인 맞춤형 헬스케어 서비스"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 h-24 text-gray-900 bg-white"
            />
          </div>
        </div>
      </div>

      {/* 분석 결과 */}
      {selectedCategory && analysis && (
        <div className="space-y-6">
          {/* 시장 개요 */}
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">시장 분석</h2>
            
            <div className="grid md:grid-cols-3 gap-6 mb-6">
              <div className="bg-blue-50 rounded-lg p-6">
                <div className="text-3xl font-bold text-blue-600 mb-2">
                  {analysis.totalCompanies}
                </div>
                <div className="text-sm text-gray-600">전체 회사 수</div>
              </div>
              
              <div className="bg-green-50 rounded-lg p-6">
                <div className="text-3xl font-bold text-green-600 mb-2">
                  {Object.keys(analysis.byStage).length}
                </div>
                <div className="text-sm text-gray-600">투자 단계 다양성</div>
              </div>
              
              <div className="bg-purple-50 rounded-lg p-6">
                <div className="text-3xl font-bold text-purple-600 mb-2">
                  {Object.keys(analysis.byLocation).length}
                </div>
                <div className="text-sm text-gray-600">활성 지역 수</div>
              </div>
            </div>

            {/* 지역별 분포 */}
            {Object.keys(analysis.byLocation).length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">지역별 분포</h3>
                <div className="space-y-2">
                  {Object.entries(analysis.byLocation)
                    .sort(([, a], [, b]) => b - a)
                    .slice(0, 5)
                    .map(([location, count]) => (
                      <div key={location} className="flex items-center justify-between">
                        <span className="text-gray-700">{location}</span>
                        <div className="flex items-center space-x-2">
                          <div className="w-32 bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full" 
                              style={{ width: `${(count / analysis.totalCompanies) * 100}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium text-gray-900 w-8 text-right">{count}</span>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </div>

          {/* 경쟁사 분석 */}
          {analysis.topCompanies.length > 0 && (
            <div className="bg-white rounded-xl shadow-lg p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">주요 경쟁사</h2>
              
              <div className="grid md:grid-cols-2 gap-4">
                {analysis.topCompanies.map((company, idx) => (
                  <div 
                    key={company.id || idx}
                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900 mb-1">{company.name}</h3>
                        {company.description && (
                          <p className="text-sm text-gray-600 line-clamp-2">{company.description}</p>
                        )}
                        {company.location && (
                          <p className="text-xs text-gray-500 mt-2">📍 {company.location}</p>
                        )}
                      </div>
                      {company.website && (
                        <a
                          href={company.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="ml-2 text-blue-600 hover:text-blue-700"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 시장 공백 */}
          {analysis.marketGaps.length > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center">
                <span className="mr-2">💡</span>
                시장 기회
              </h2>
              <ul className="space-y-3">
                {analysis.marketGaps.map((gap, idx) => (
                  <li key={idx} className="flex items-start">
                    <span className="text-yellow-600 mr-2">•</span>
                    <span className="text-gray-700">{gap}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 차별화 포인트 */}
          <div className="bg-green-50 border border-green-200 rounded-xl p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center">
              <span className="mr-2">🚀</span>
              차별화 전략
            </h2>
            <ul className="space-y-3">
              {analysis.differentiationPoints.map((point, idx) => (
                <li key={idx} className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span className="text-gray-700">{point}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* 안내 메시지 */}
      {!selectedCategory && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-8 text-center">
          <p className="text-gray-700">
            위에서 카테고리를 선택하면 시장 분석이 시작됩니다.
          </p>
        </div>
      )}

      {/* 분석 결과가 없을 때 (카테고리는 선택했지만 데이터가 없는 경우) */}
      {selectedCategory && !analysis && !loading && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-8 text-center">
          <p className="text-gray-700 mb-2">
            "{selectedCategory}" 카테고리에 대한 데이터를 찾지 못했습니다.
          </p>
          <p className="text-sm text-gray-600">
            다른 카테고리를 선택하거나, 아이디어 설명에 더 구체적인 키워드를 입력해보세요.
          </p>
        </div>
      )}
    </div>
  )
}
