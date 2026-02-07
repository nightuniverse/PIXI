'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { ArrowUpIcon, LightBulbIcon } from '@heroicons/react/24/outline'
import { projectManager, Project } from '@/utils/projectManager'

export default function Home() {
  const router = useRouter()
  const [projects, setProjects] = useState<Project[]>([])
  const [mounted, setMounted] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const [privacyMode, setPrivacyMode] = useState(false)

  // 클라이언트에서만 프로젝트 로드 (Hydration 오류 방지)
  useEffect(() => {
    setMounted(true)
    const allProjects = projectManager.getAllProjects()
    setProjects(allProjects)
  }, [])

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    
    if (!inputValue.trim()) return

    // 새 프로젝트 생성하고 AI 공동창업자 페이지로 이동
    const newProject = projectManager.createProject(inputValue.trim().substring(0, 50))
    router.push(`/cofounder?project=${newProject.id}`)
  }

  const handleBrainstorm = () => {
    // 브레인스토밍 모드로 시작
    const newProject = projectManager.createProject('아이디어 브레인스토밍')
    router.push(`/cofounder?project=${newProject.id}&mode=brainstorm`)
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <main className="min-h-screen bg-white relative overflow-hidden">
      {/* Figma 스타일 그리드 배경 */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#f5f5f5_1px,transparent_1px),linear-gradient(to_bottom,#f5f5f5_1px,transparent_1px)] bg-[size:16px_16px] opacity-50" />
      
      {/* 헤더 */}
      <header className="relative z-10 border-b border-gray-200 bg-white/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-8 py-4 flex justify-between items-center">
          {/* 로고 영역 */}
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gray-900 rounded flex items-center justify-center">
              <span className="text-white text-sm font-bold">P</span>
            </div>
            <span className="text-gray-900 font-semibold text-lg">PIXI</span>
          </div>
          
          {/* 네비게이션 */}
          <nav className="flex items-center gap-8">
            <Link 
              href="/pricing" 
              className="text-gray-600 hover:text-gray-900 text-sm font-medium transition-colors"
            >
              가격
            </Link>
            <Link 
              href="/signin" 
              className="text-gray-600 hover:text-gray-900 text-sm font-medium transition-colors"
            >
              로그인
            </Link>
            <Link 
              href="/signup"
              className="bg-gray-900 hover:bg-gray-800 text-white px-4 py-2 rounded-md text-sm font-medium transition-all shadow-sm"
            >
              시작하기
            </Link>
          </nav>
        </div>
      </header>

      {/* 히어로 섹션 */}
      <section className="relative z-10 max-w-5xl mx-auto px-8 pt-20 pb-32">
        <div className="text-center">
          {/* 태그 */}
          <div className="inline-flex items-center gap-2 mb-8 px-3 py-1.5 bg-gray-100 rounded-md">
            <div className="w-1.5 h-1.5 bg-gray-600 rounded-full"></div>
            <span className="text-gray-700 text-xs font-medium tracking-wide uppercase">
              AI 공동창업자
            </span>
          </div>

          {/* 메인 헤드라인 */}
          <h1 className="text-6xl md:text-7xl lg:text-8xl font-semibold text-gray-900 mb-6 leading-[1.1] tracking-tight">
            사람들이 정말<br />원하는 것을 만드세요
          </h1>

          {/* 서브헤드라인 */}
          <p className="text-xl text-gray-500 mb-16 max-w-2xl mx-auto font-normal">
            AI와 함께 제품을 연구하고 계획하세요
          </p>

          {/* 입력 필드 - Figma 스타일 */}
          <form onSubmit={handleSubmit} className="relative mb-8">
            <div className="relative bg-white rounded-lg border-2 border-gray-200 hover:border-gray-300 focus-within:border-gray-900 transition-all shadow-sm">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="예: 식단 관리 앱을 만들고 싶어요..."
                className="w-full px-5 py-4 pr-14 text-base text-gray-900 placeholder-gray-400 resize-none focus:outline-none bg-transparent min-h-[140px] font-normal"
                rows={4}
              />
              <button
                type="submit"
                disabled={!inputValue.trim()}
                className={`absolute bottom-4 right-4 w-9 h-9 rounded-md flex items-center justify-center transition-all ${
                  inputValue.trim()
                    ? 'bg-gray-900 hover:bg-gray-800 text-white shadow-sm hover:shadow cursor-pointer'
                    : 'bg-gray-100 text-gray-300 cursor-not-allowed'
                }`}
              >
                <ArrowUpIcon className="w-4 h-4" />
              </button>
            </div>
          </form>

          {/* 하단 컨트롤 - Figma 스타일 */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-8">
            {/* 아이디어 떠올리기 버튼 */}
            <button
              onClick={handleBrainstorm}
              className="flex items-center gap-2 px-4 py-2.5 bg-white hover:bg-gray-50 text-gray-700 rounded-md text-sm font-medium transition-all border border-gray-200 hover:border-gray-300 shadow-sm"
            >
              <LightBulbIcon className="w-4 h-4" />
              아이디어 떠올리기
            </button>

            {/* 비공개 모드 토글 */}
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-600 font-normal">비공개 모드</span>
              <button
                onClick={() => setPrivacyMode(!privacyMode)}
                className={`relative w-11 h-6 rounded-full transition-all ${
                  privacyMode ? 'bg-gray-900' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform shadow-sm ${
                    privacyMode ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 최근 프로젝트 섹션 */}
      {mounted && projects.length > 0 && (
        <section className="relative z-10 pb-20 border-t border-gray-100">
          <div className="max-w-5xl mx-auto px-8 pt-12">
            <div className="text-center mb-6">
              <p className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-6">
                최근 프로젝트
              </p>
              <div className="flex flex-wrap gap-2 justify-center">
                {projects.slice(0, 5).map((project) => (
                  <Link
                    key={project.id}
                    href={`/cofounder?project=${project.id}`}
                    className="px-3 py-1.5 bg-gray-50 hover:bg-gray-100 text-gray-700 rounded-md text-sm transition-all border border-gray-200 hover:border-gray-300 font-medium"
                  >
                    {project.name}
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </section>
      )}
    </main>
  )
}
