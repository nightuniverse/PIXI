'use client'

import { useState } from 'react'
import { XMarkIcon, ArrowsPointingOutIcon, ArrowsPointingInIcon } from '@heroicons/react/24/outline'

interface ProjectState {
  idea?: string
  problem?: string
  targetCustomers?: string[]
  solution?: string
  features?: string[]
  mvpPlan?: string
  launchPlan?: string
}

interface ProjectCanvasProps {
  projectState: ProjectState
  currentPhase: string
  onClose?: () => void
}

const phaseConfig = {
  idea: { name: '아이디어', icon: '💡', color: 'bg-blue-500' },
  research: { name: '조사', icon: '🔍', color: 'bg-emerald-500' },
  solution: { name: '솔루션', icon: '🎯', color: 'bg-purple-500' },
  mvp: { name: 'MVP', icon: '🚀', color: 'bg-amber-500' },
  launch: { name: '런칭', icon: '🎉', color: 'bg-rose-500' }
}

export default function ProjectCanvas({ projectState, currentPhase, onClose }: ProjectCanvasProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const phases = ['idea', 'research', 'solution', 'mvp', 'launch'] as const
  const currentPhaseIndex = phases.indexOf(currentPhase as typeof phases[number])

  const hasContent = projectState.idea || projectState.problem || projectState.solution

  return (
    <div className={`bg-white rounded-2xl shadow-2xl border border-gray-100 transition-all duration-300 ${
      isExpanded ? 'fixed inset-4 z-50' : 'relative h-full'
    }`}>
      {/* 헤더 */}
      <div className="px-6 py-4 border-b border-gray-100 bg-white rounded-t-2xl">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">프로젝트 캔버스</h3>
            <p className="text-sm text-gray-500 mt-0.5">아이디어를 시각화하고 정리하세요</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors text-gray-600 hover:text-gray-900"
              title={isExpanded ? '축소' : '확대'}
            >
              {isExpanded ? (
                <ArrowsPointingInIcon className="w-5 h-5" />
              ) : (
                <ArrowsPointingOutIcon className="w-5 h-5" />
              )}
            </button>
            {onClose && (
              <button
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors text-gray-600 hover:text-gray-900"
                title="닫기"
              >
                <XMarkIcon className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 진행 단계 표시 */}
      <div className="px-6 py-4 border-b border-gray-100 bg-gray-50/50">
        <div className="flex items-center justify-between">
          {phases.map((phase, idx) => {
            const config = phaseConfig[phase]
            const isCompleted = idx < currentPhaseIndex
            const isCurrent = idx === currentPhaseIndex
            const isPending = idx > currentPhaseIndex

            return (
              <div key={phase} className="flex items-center flex-1">
                <div className="flex flex-col items-center flex-1">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-lg transition-all duration-300 ${
                    isCompleted ? `${config.color} text-white shadow-sm` :
                    isCurrent ? `${config.color} text-white shadow-md animate-pulse` :
                    'bg-gray-200 text-gray-400'
                  }`}>
                    {config.icon}
                  </div>
                  <span className={`text-xs mt-2 font-medium transition-colors ${
                    isCompleted || isCurrent ? 'text-gray-900' : 'text-gray-400'
                  }`}>
                    {config.name}
                  </span>
                </div>
                {idx < phases.length - 1 && (
                  <div className={`h-0.5 flex-1 mx-3 transition-all duration-300 ${
                    isCompleted ? config.color : 'bg-gray-200'
                  }`} />
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* 캔버스 내용 */}
      <div className="p-6 overflow-y-auto" style={{ maxHeight: isExpanded ? 'calc(100vh - 280px)' : '600px' }}>
        {hasContent ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 아이디어 */}
            {projectState.idea && (
              <div className="group p-5 bg-blue-50 rounded-xl border border-blue-100 hover:border-blue-200 transition-all duration-200 hover:shadow-sm">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-8 h-8 rounded-lg bg-blue-500 flex items-center justify-center text-white text-lg">
                    💡
                  </div>
                  <h4 className="font-semibold text-blue-900">아이디어</h4>
                </div>
                <p className="text-sm text-gray-700 leading-relaxed">{projectState.idea}</p>
              </div>
            )}

            {/* 문제 */}
            {projectState.problem && (
              <div className="group p-5 bg-red-50 rounded-xl border border-red-100 hover:border-red-200 transition-all duration-200 hover:shadow-sm">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-8 h-8 rounded-lg bg-red-500 flex items-center justify-center text-white text-lg">
                    ⚠️
                  </div>
                  <h4 className="font-semibold text-red-900">문제</h4>
                </div>
                <p className="text-sm text-gray-700 leading-relaxed">{projectState.problem}</p>
              </div>
            )}

            {/* 타겟 고객 */}
            {projectState.targetCustomers && projectState.targetCustomers.length > 0 && (
              <div className="group p-5 bg-emerald-50 rounded-xl border border-emerald-100 hover:border-emerald-200 transition-all duration-200 hover:shadow-sm">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center text-white text-lg">
                    👥
                  </div>
                  <h4 className="font-semibold text-emerald-900">타겟 고객</h4>
                </div>
                <ul className="space-y-2">
                  {projectState.targetCustomers.map((customer, idx) => (
                    <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                      <span className="text-emerald-500 mt-0.5">•</span>
                      <span>{customer}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* 솔루션 */}
            {projectState.solution && (
              <div className="group p-5 bg-purple-50 rounded-xl border border-purple-100 hover:border-purple-200 transition-all duration-200 hover:shadow-sm">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-8 h-8 rounded-lg bg-purple-500 flex items-center justify-center text-white text-lg">
                    🎯
                  </div>
                  <h4 className="font-semibold text-purple-900">솔루션</h4>
                </div>
                <p className="text-sm text-gray-700 leading-relaxed">{projectState.solution}</p>
              </div>
            )}

            {/* 기능 */}
            {projectState.features && projectState.features.length > 0 && (
              <div className="group p-5 bg-amber-50 rounded-xl border border-amber-100 hover:border-amber-200 transition-all duration-200 hover:shadow-sm">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-8 h-8 rounded-lg bg-amber-500 flex items-center justify-center text-white text-lg">
                    ⚙️
                  </div>
                  <h4 className="font-semibold text-amber-900">주요 기능</h4>
                </div>
                <ul className="space-y-2">
                  {projectState.features.map((feature, idx) => (
                    <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                      <span className="text-amber-500 mt-0.5">•</span>
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* MVP 계획 */}
            {projectState.mvpPlan && (
              <div className="group p-5 bg-yellow-50 rounded-xl border border-yellow-100 hover:border-yellow-200 transition-all duration-200 hover:shadow-sm">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-8 h-8 rounded-lg bg-yellow-500 flex items-center justify-center text-white text-lg">
                    🚀
                  </div>
                  <h4 className="font-semibold text-yellow-900">MVP 계획</h4>
                </div>
                <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{projectState.mvpPlan}</p>
              </div>
            )}

            {/* 런칭 계획 */}
            {projectState.launchPlan && (
              <div className="group p-5 bg-rose-50 rounded-xl border border-rose-100 hover:border-rose-200 transition-all duration-200 hover:shadow-sm">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-8 h-8 rounded-lg bg-rose-500 flex items-center justify-center text-white text-lg">
                    🎉
                  </div>
                  <h4 className="font-semibold text-rose-900">런칭 계획</h4>
                </div>
                <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{projectState.launchPlan}</p>
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-20 h-20 rounded-2xl bg-gray-100 flex items-center justify-center mb-4">
              <span className="text-4xl">📋</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">프로젝트 정보가 없습니다</h3>
            <p className="text-sm text-gray-500 max-w-sm">
              AI와 대화하면서 프로젝트 정보가 자동으로 채워집니다
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
