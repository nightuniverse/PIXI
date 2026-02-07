/**
 * AI 응답에서 문서 정보를 추출하는 유틸리티
 */

interface DocumentHint {
  title?: string
  section?: string
  checklist?: Array<{ id: string; text: string; checked: boolean }>
}

export function extractDocumentFromResponse(response: string): DocumentHint | null {
  // 경쟁사 분석이나 시장 조사 관련 키워드 확인
  const researchKeywords = ['경쟁사', '시장', '조사', '분석', '비교', '경쟁', '시장 규모', '차별화']
  const hasResearchContent = researchKeywords.some(keyword => response.includes(keyword))
  
  // 체크리스트 패턴 찾기
  const checklistPattern = /(?:체크리스트|할 일|작업|단계|항목|분석|조사)[\s:]*\n?([\s\S]*?)(?:\n\n|\n$|$)/i
  const checklistMatch = response.match(checklistPattern)
  
  // 제목 패턴 찾기 (마크다운 헤더 포함)
  const titlePatterns = [
    /(?:제목|계획|문서|분석|조사)[\s:]*\n?([^\n]+)/i,
    /##\s*([^\n]+)/,
    /#\s*([^\n]+)/,
  ]
  
  let titleMatch = null
  for (const pattern of titlePatterns) {
    titleMatch = response.match(pattern)
    if (titleMatch) break
  }
  
  // 섹션 패턴 찾기
  const sectionPatterns = [
    /(?:섹션|단계|영역|카테고리)[\s:]*\n?([^\n]+)/i,
    /###\s*([^\n]+)/,
  ]
  
  let sectionMatch = null
  for (const pattern of sectionPatterns) {
    sectionMatch = response.match(pattern)
    if (sectionMatch) break
  }
  
  // 번호가 매겨진 목록 또는 체크박스 패턴 찾기
  const listItemPattern = /(?:^|\n)[\s]*[-•*]\s*([^\n]+)/g
  const numberedPattern = /(?:^|\n)[\s]*\d+[\.\)]\s*([^\n]+)/g
  const checkboxPattern = /(?:^|\n)[\s]*(?:□|☐|✓|✔|☑)\s*([^\n]+)/g
  
  let checklist: Array<{ id: string; text: string; checked: boolean }> = []
  
  // 체크리스트 항목 추출
  if (checklistMatch) {
    const items = checklistMatch[1].match(listItemPattern) || 
                  checklistMatch[1].match(numberedPattern) || 
                  checklistMatch[1].match(checkboxPattern) || []
    checklist = items.map((item, idx) => ({
      id: `item_${Date.now()}_${idx}`,
      text: item.replace(/^[\s]*[-•*\d\.\)□☐✓✔☑]\s*/, '').trim(),
      checked: false
    }))
  } else {
    // 전체 응답에서 목록 항목 찾기
    const allItems = response.match(listItemPattern) || 
                     response.match(numberedPattern) || 
                     response.match(checkboxPattern) || []
    if (allItems.length >= 2) {
      checklist = allItems.slice(0, 10).map((item, idx) => ({
        id: `item_${Date.now()}_${idx}`,
        text: item.replace(/^[\s]*[-•*\d\.\)□☐✓✔☑]\s*/, '').trim(),
        checked: false
      }))
    }
  }
  
  // 경쟁사 분석이나 시장 조사 관련 내용이 있으면 문서 생성
  if (hasResearchContent) {
    // 제목이 없으면 키워드 기반으로 생성
    let title = '계획'
    if (titleMatch) {
      title = titleMatch[1].trim().replace(/^#+\s*/, '')
    } else if (response.includes('경쟁사')) {
      title = '경쟁사 분석'
    } else if (response.includes('시장')) {
      title = '시장 조사'
    } else if (response.includes('분석')) {
      title = '시장 분석'
    }
    
    // 체크리스트가 없으면 기본 항목 생성
    if (checklist.length === 0 && hasResearchContent) {
      if (response.includes('경쟁사')) {
        checklist = [
          { id: `item_${Date.now()}_1`, text: '경쟁사 데이터 수집', checked: false },
          { id: `item_${Date.now()}_2`, text: '경쟁사 강점/약점 분석', checked: false },
          { id: `item_${Date.now()}_3`, text: '차별화 포인트 도출', checked: false }
        ]
      } else if (response.includes('시장')) {
        checklist = [
          { id: `item_${Date.now()}_1`, text: '시장 규모 조사', checked: false },
          { id: `item_${Date.now()}_2`, text: '시장 성장률 분석', checked: false },
          { id: `item_${Date.now()}_3`, text: '시장 기회 도출', checked: false }
        ]
      }
    }
    
    return {
      title,
      section: sectionMatch ? sectionMatch[1].trim().replace(/^#+\s*/, '') : '초기 조사',
      checklist: checklist.length > 0 ? checklist : undefined
    }
  }
  
  // 일반적인 문서 생성 조건
  if (checklist.length > 0 || titleMatch) {
    return {
      title: titleMatch ? titleMatch[1].trim().replace(/^#+\s*/, '') : '계획',
      section: sectionMatch ? sectionMatch[1].trim().replace(/^#+\s*/, '') : undefined,
      checklist: checklist.length > 0 ? checklist : undefined
    }
  }
  
  return null
}
