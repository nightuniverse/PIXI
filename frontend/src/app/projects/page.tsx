'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { 
  PlusIcon, 
  TrashIcon, 
  ArrowRightIcon,
  DocumentDuplicateIcon,
  ArrowLeftIcon
} from '@heroicons/react/24/outline'
import { projectManager, Project } from '@/utils/projectManager'

export default function ProjectsPage() {
  const router = useRouter()
  const [projects, setProjects] = useState<Project[]>([])
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    loadProjects()
  }, [])

  const loadProjects = () => {
    if (typeof window === 'undefined') return // SSR 방지
    
    const allProjects = projectManager.getAllProjects()
    // 최신순으로 정렬
    setProjects(allProjects.sort((a, b) => 
      new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
    ))
  }

  const handleCreateProject = () => {
    if (!newProjectName.trim()) {
      alert('프로젝트 이름을 입력해주세요.')
      return
    }

    const project = projectManager.createProject(newProjectName.trim())
    setShowCreateModal(false)
    setNewProjectName('')
    router.push(`/cofounder?project=${project.id}`)
  }

  const handleDeleteProject = (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (confirm('프로젝트를 삭제하시겠습니까? 모든 데이터가 영구적으로 삭제됩니다.')) {
      projectManager.deleteProject(id)
      loadProjects()
    }
  }

  const handleSelectProject = (id: string) => {
    projectManager.setCurrentProjectId(id)
    router.push(`/cofounder?project=${id}`)
  }

  const getPhaseName = (phase: string) => {
    const names: Record<string, string> = {
      idea: '아이디어',
      research: '조사',
      solution: '솔루션',
      mvp: 'MVP',
      launch: '런칭'
    }
    return names[phase] || phase
  }

  const getPhaseColor = (phase: string) => {
    const colors: Record<string, string> = {
      idea: 'bg-blue-100 text-blue-700',
      research: 'bg-emerald-100 text-emerald-700',
      solution: 'bg-purple-100 text-purple-700',
      mvp: 'bg-amber-100 text-amber-700',
      launch: 'bg-rose-100 text-rose-700'
    }
    return colors[phase] || 'bg-gray-100 text-gray-700'
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white border-b border-gray-100 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                href="/"
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors text-gray-600 hover:text-gray-900"
              >
                <ArrowLeftIcon className="w-5 h-5" />
              </Link>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">내 프로젝트</h1>
                <p className="text-sm text-gray-500 mt-0.5">프로젝트를 관리하고 계속 작업하세요</p>
              </div>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-gray-900 hover:bg-gray-800 text-white rounded-lg font-medium transition-colors"
            >
              <PlusIcon className="w-5 h-5" />
              새 프로젝트
            </button>
          </div>
        </div>
      </header>

      {/* 메인 콘텐츠 */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {!mounted ? (
          <div className="text-center py-20">
            <div className="w-8 h-8 border-2 border-gray-300 border-t-gray-900 rounded-full animate-spin mx-auto"></div>
          </div>
        ) : projects.length === 0 ? (
          <div className="text-center py-20">
            <div className="w-20 h-20 rounded-2xl bg-gray-100 flex items-center justify-center mx-auto mb-4">
              <DocumentDuplicateIcon className="w-10 h-10 text-gray-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">프로젝트가 없습니다</h3>
            <p className="text-sm text-gray-500 mb-6">새 프로젝트를 만들어 시작하세요</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 px-6 py-3 bg-gray-900 hover:bg-gray-800 text-white rounded-lg font-medium transition-colors"
            >
              <PlusIcon className="w-5 h-5" />
              첫 프로젝트 만들기
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((project) => (
              <div
                key={project.id}
                onClick={() => handleSelectProject(project.id)}
                className="bg-white rounded-xl border border-gray-200 p-6 hover:border-gray-300 hover:shadow-md transition-all cursor-pointer group"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-1 group-hover:text-gray-700">
                      {project.name}
                    </h3>
                    <p className="text-xs text-gray-500">
                      {new Date(project.updatedAt).toLocaleDateString('ko-KR')} 업데이트
                    </p>
                  </div>
                  <button
                    onClick={(e) => handleDeleteProject(project.id, e)}
                    className="p-2 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-600 transition-colors opacity-0 group-hover:opacity-100"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                </div>

                <div className="flex items-center justify-between">
                  <span className={`px-2 py-1 rounded-md text-xs font-medium ${getPhaseColor(project.currentPhase)}`}>
                    {getPhaseName(project.currentPhase)}
                  </span>
                  <div className="flex items-center gap-1 text-sm text-gray-500">
                    <span>{project.messages?.length || 0}개 메시지</span>
                    <ArrowRightIcon className="w-4 h-4" />
                  </div>
                </div>

                {project.projectState?.idea && (
                  <div className="mt-4 pt-4 border-t border-gray-100">
                    <p className="text-xs text-gray-500 mb-1">아이디어</p>
                    <p className="text-sm text-gray-700 line-clamp-2">{project.projectState.idea}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>

      {/* 새 프로젝트 생성 모달 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">새 프로젝트 만들기</h3>
            <input
              type="text"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleCreateProject()}
              placeholder="프로젝트 이름을 입력하세요"
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              autoFocus
            />
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowCreateModal(false)
                  setNewProjectName('')
                }}
                className="flex-1 px-4 py-2 border border-gray-200 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
              >
                취소
              </button>
              <button
                onClick={handleCreateProject}
                className="flex-1 px-4 py-2 bg-gray-900 hover:bg-gray-800 text-white rounded-lg transition-colors"
              >
                만들기
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
