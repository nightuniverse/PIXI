'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import ProjectCanvas from './ProjectCanvas'
import DocumentCanvas, { DocumentCardData } from './DocumentCanvas'
import { projectManager, Project } from '@/utils/projectManager'
import { extractDocumentFromResponse } from '@/utils/documentExtractor'
import { 
  PaperAirplaneIcon, 
  SparklesIcon,
  ChartBarIcon,
  ArrowPathIcon,
  ShareIcon,
  DocumentArrowDownIcon,
  FolderIcon,
  PaperClipIcon,
  XMarkIcon
} from '@heroicons/react/24/outline'

type Phase = 'idea' | 'research' | 'solution' | 'mvp' | 'launch'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  phase?: Phase
  timestamp: Date
}

interface ProjectState {
  idea?: string
  problem?: string
  targetCustomers?: string[]
  solution?: string
  features?: string[]
  mvpPlan?: string
  launchPlan?: string
}

const phaseConfig = {
  idea: { name: '아이디어', color: 'bg-blue-50 text-blue-700 border-blue-200', dot: 'bg-blue-500' },
  research: { name: '조사', color: 'bg-emerald-50 text-emerald-700 border-emerald-200', dot: 'bg-emerald-500' },
  solution: { name: '솔루션', color: 'bg-purple-50 text-purple-700 border-purple-200', dot: 'bg-purple-500' },
  mvp: { name: 'MVP', color: 'bg-amber-50 text-amber-700 border-amber-200', dot: 'bg-amber-500' },
  launch: { name: '런칭', color: 'bg-rose-50 text-rose-700 border-rose-200', dot: 'bg-rose-500' }
}

export default function AICofounderChat() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [projectId, setProjectId] = useState<string | null>(null)
  const [projectName, setProjectName] = useState<string>('새 프로젝트')
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [currentPhase, setCurrentPhase] = useState<Phase>('idea')
  const [projectState, setProjectState] = useState<ProjectState>({})
  const [loading, setLoading] = useState(false)
  const [projectStarted, setProjectStarted] = useState(false)
  const [showCanvas, setShowCanvas] = useState(false)
  const [showShareModal, setShowShareModal] = useState(false)
  const [documents, setDocuments] = useState<DocumentCardData[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // 프로젝트 ID 초기화
  useEffect(() => {
    const idFromUrl = searchParams.get('project')
    const currentId = projectManager.getCurrentProjectId()
    
    if (idFromUrl) {
      setProjectId(idFromUrl)
      projectManager.setCurrentProjectId(idFromUrl)
    } else if (currentId) {
      setProjectId(currentId)
    } else {
      // 새 프로젝트 생성
      const newProject = projectManager.createProject('새 프로젝트')
      setProjectId(newProject.id)
      setProjectName(newProject.name)
      router.replace(`/cofounder?project=${newProject.id}`)
    }
  }, [searchParams, router])

  // 프로젝트 로드
  useEffect(() => {
    if (!projectId) return

    const project = projectManager.getProject(projectId)
    if (project) {
      setProjectName(project.name)
      setCurrentPhase(project.currentPhase as Phase)
      setProjectState(project.projectState || {})
      
      if (project.messages && project.messages.length > 0) {
        setMessages(project.messages.map((m: any) => ({
          ...m,
          timestamp: new Date(m.timestamp)
        })))
        setProjectStarted(true)
      }
      
      // 문서 로드
      if (project.projectState?.documents) {
        setDocuments(project.projectState.documents)
      }
    } else {
      // 프로젝트가 없으면 새로 생성
      const newProject = projectManager.createProject('새 프로젝트')
      setProjectId(newProject.id)
      setProjectName(newProject.name)
      router.replace(`/cofounder?project=${newProject.id}`)
    }
  }, [projectId, router])

  // 공유 링크 처리
  useEffect(() => {
    const isShare = searchParams.get('share')
    if (isShare === 'true' && projectId) {
      // 읽기 전용 모드로 표시하거나 특별한 UI 표시
      console.log('공유된 프로젝트:', projectId)
    }
  }, [searchParams, projectId])

  // 프로젝트 저장
  const saveProject = useCallback(() => {
    if (!projectId) return

    const project: Project = {
      id: projectId,
      name: projectName,
      createdAt: projectManager.getProject(projectId)?.createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      currentPhase,
      projectState: {
        ...projectState,
        documents: documents
      },
      messages: messages.map(m => ({
        ...m,
        timestamp: m.timestamp.toISOString()
      }))
    }

    projectManager.saveProject(project)
  }, [projectId, projectName, currentPhase, projectState, messages, documents])

  // 프로젝트 상태 변경 시 자동 저장
  useEffect(() => {
    if (projectStarted && projectId) {
      saveProject()
    }
  }, [projectState, messages, currentPhase, documents, projectStarted, projectId, saveProject])

  // 문서 업데이트 핸들러
  const handleUpdateDocument = (id: string, updates: Partial<DocumentCardData>) => {
    setDocuments(prev => prev.map(doc => doc.id === id ? { ...doc, ...updates } : doc))
  }

  // 문서 삭제 핸들러
  const handleDeleteDocument = (id: string) => {
    setDocuments(prev => prev.filter(doc => doc.id !== id))
  }

  // 체크리스트 항목 체크 핸들러
  const handleCheckItem = (cardId: string, itemId: string, checked: boolean) => {
    setDocuments(prev => prev.map(doc => {
      if (doc.id === cardId && doc.checklist) {
        return {
          ...doc,
          checklist: doc.checklist.map(item =>
            item.id === itemId ? { ...item, checked } : item
          )
        }
      }
      return doc
    }))
  }

  // 프로젝트 이름 변경
  const handleRenameProject = () => {
    const newName = prompt('프로젝트 이름을 입력하세요:', projectName)
    if (newName && newName.trim() && projectId) {
      setProjectName(newName.trim())
      projectManager.updateProjectName(projectId, newName.trim())
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // 텍스트 영역 자동 높이 조절
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`
    }
  }, [input])

  // 초기 환영 메시지
  useEffect(() => {
    if (!projectStarted) {
      const welcomeMessage: Message = {
        id: 'welcome',
        role: 'assistant',
        content: `안녕하세요! 저는 당신의 AI 공동창업자입니다.

우리는 함께 5단계 프로세스를 통해 아이디어를 실제 제품으로 만들어갈 것입니다:

**1. 아이디어 단계** - 문제를 발견하고 아이디어를 구체화합니다
**2. 조사 단계** - 실제 시장 데이터와 사용자 니즈를 조사합니다
**3. 솔루션 단계** - 문제에 맞는 최적의 솔루션을 설계합니다
**4. MVP 단계** - 최소 기능 제품을 계획하고 구축합니다
**5. 런칭 단계** - 제품을 출시하고 성장 전략을 수립합니다

어떻게 시작하시겠어요?`,
        phase: 'idea',
        timestamp: new Date()
      }
      setMessages([welcomeMessage])
    }
  }, [projectStarted])

  const sendMessage = async (userMessage?: string) => {
    const messageToSend = userMessage || input
    if (!messageToSend.trim() || loading) return

    // 사용자 메시지 추가
    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: messageToSend,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)
    setProjectStarted(true)

    // 프로젝트 자동 저장
    if (projectId) {
      saveProject()
    }

    try {
      // 백엔드 API 호출
      const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
      
      let response: Response
      try {
        response = await fetch(`${apiUrl}/api/v1/cofounder/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: messageToSend,
            current_phase: currentPhase,
            project_state: projectState,
            conversation_history: messages.slice(-10).map(m => ({
              role: m.role,
              content: m.content
            }))
          })
        })
      } catch (fetchError) {
        // 네트워크 오류 (서버에 연결할 수 없음)
        throw new Error(`백엔드 서버에 연결할 수 없습니다.\n\n**해결 방법:**\n\n1. 백엔드 서버를 시작하세요:\n   \`\`\`bash\n   cd backend\n   source venv/bin/activate\n   uvicorn main:app --reload --host 0.0.0.0 --port 8000\n   \`\`\`\n\n2. 서버가 http://localhost:8000 에서 실행 중인지 확인하세요\n\n3. 브라우저 콘솔(F12)에서 자세한 오류를 확인하세요`)
      }

      if (!response.ok) {
        // 응답 본문에서 에러 메시지 추출 시도
        let errorMessage = `서버 오류 (${response.status})`
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail || errorData.message || errorMessage
        } catch {
          // JSON 파싱 실패 시 기본 메시지 사용
        }
        
        // 500 오류는 서버 내부 오류
        if (response.status >= 500) {
          throw new Error(`서버 내부 오류: ${errorMessage}\n\n백엔드 서버 로그를 확인하세요.`)
        }
        
        throw new Error(errorMessage)
      }

      const data = await response.json()
      
      // 디버깅: 응답 데이터 확인
      console.log('백엔드 응답:', data)
      console.log('프로젝트 상태:', data.project_state)
      console.log('문서 데이터:', data.project_state?.documents)
      
      // 응답 데이터 검증
      if (!data.response) {
        throw new Error('서버 응답 형식이 올바르지 않습니다.')
      }
      
      // AI 응답 추가
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response,
        phase: data.next_phase || currentPhase,
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, assistantMsg])
      
      // 프로젝트 상태 업데이트
      if (data.project_state) {
        // documents를 별도로 처리
        const { documents: stateDocuments, ...restState } = data.project_state
        
        setProjectState(prev => ({ ...prev, ...restState }))
        
        // 백엔드에서 생성된 문서가 있으면 사용 (같은 id면 업데이트, 없으면 추가)
        if (stateDocuments && Array.isArray(stateDocuments) && stateDocuments.length > 0) {
          setDocuments(prev => {
            const byId = new Map(prev.map(d => [d.id, d]))
            stateDocuments.forEach((doc: DocumentCardData) => {
              byId.set(doc.id, { ...byId.get(doc.id), ...doc })
            })
            return Array.from(byId.values())
          })
        }
      }
      
      // 백엔드에서 문서가 생성되지 않았을 경우, 프론트엔드에서 추출 시도
      if (!data.project_state?.documents || data.project_state.documents.length === 0) {
        const documentHint = extractDocumentFromResponse(data.response)
        if (documentHint) {
          const newDoc: DocumentCardData = {
            id: `doc_${Date.now()}`,
            title: documentHint.title || '계획',
            section: documentHint.section,
            checklist: documentHint.checklist || [],
            x: Math.random() * 300 + 50,
            y: Math.random() * 200 + 50
          }
          setDocuments(prev => {
            // 중복 방지
            const exists = prev.some(doc => doc.title === newDoc.title && doc.section === newDoc.section)
            return exists ? prev : [...prev, newDoc]
          })
        }
      }
      
      // 단계 업데이트
      if (data.next_phase && data.next_phase !== currentPhase) {
        setCurrentPhase(data.next_phase)
      }

      // 프로젝트 자동 저장
      if (projectId) {
        saveProject()
      }
    } catch (error) {
      console.error('메시지 전송 오류:', error)
      
      // 에러 타입별 메시지 처리
      let errorMessage = '알 수 없는 오류가 발생했습니다.'
      let helpMessage = ''
      
      if (error instanceof TypeError && error.message.includes('fetch')) {
        // 네트워크 오류 (서버가 실행되지 않음)
        errorMessage = '백엔드 서버에 연결할 수 없습니다.'
        helpMessage = `**해결 방법:**\n\n1. 백엔드 서버를 시작하세요:\n   \`\`\`bash\n   cd backend\n   source venv/bin/activate  # 또는 venv\\Scripts\\activate (Windows)\n   uvicorn main:app --reload\n   \`\`\`\n\n2. 서버가 http://localhost:8000 에서 실행 중인지 확인하세요\n\n3. 브라우저 콘솔(F12)에서 자세한 오류를 확인하세요`
      } else if (error instanceof Error) {
        errorMessage = error.message
        if (errorMessage.includes('서버 오류') || errorMessage.includes('500')) {
          helpMessage = `**해결 방법:**\n\n1. 백엔드 서버 로그를 확인하세요\n2. OPENAI_API_KEY가 .env 파일에 설정되어 있는지 확인하세요\n3. 백엔드 서버를 재시작해보세요`
        } else if (errorMessage.includes('404')) {
          helpMessage = `**해결 방법:**\n\n1. API 엔드포인트가 올바른지 확인하세요\n2. 백엔드 서버가 최신 버전인지 확인하세요`
        }
      }
      
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `⚠️ **오류 발생**\n\n${errorMessage}\n\n${helpMessage || '브라우저 콘솔(F12)에서 자세한 오류를 확인하세요.'}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const phases: Phase[] = ['idea', 'research', 'solution', 'mvp', 'launch']
  const currentPhaseIndex = phases.indexOf(currentPhase)

  // 프로젝트 공유
  const handleShare = () => {
    if (!projectId) return
    
    const shareUrl = `${window.location.origin}/cofounder?project=${projectId}&share=true`
    navigator.clipboard.writeText(shareUrl).then(() => {
      alert('공유 링크가 클립보드에 복사되었습니다!')
    }).catch(() => {
      // 클립보드 API 실패 시 수동 복사
      const textarea = document.createElement('textarea')
      textarea.value = shareUrl
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
      alert('공유 링크가 클립보드에 복사되었습니다!')
    })
    setShowShareModal(false)
  }

  // 데이터 내보내기
  const handleExport = () => {
    if (!projectId) return

    const project = projectManager.getProject(projectId)
    if (!project) return

    // JSON 내보내기
    const dataStr = JSON.stringify({
      project: {
        id: project.id,
        name: project.name,
        createdAt: project.createdAt,
        updatedAt: project.updatedAt,
        currentPhase: project.currentPhase,
        projectState: project.projectState,
        messages: project.messages
      }
    }, null, 2)

    const blob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${project.name || 'project'}_${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  // 검증 페이지 생성
  const handleCreateValidationPage = () => {
    if (!projectState.problem && !projectState.solution) {
      alert('문제와 솔루션이 정의되어야 검증 페이지를 생성할 수 있습니다.')
      return
    }

    const validationData = {
      problem: projectState.problem,
      solution: projectState.solution,
      targetCustomers: projectState.targetCustomers || [],
      projectName: projectName
    }

    // 검증 페이지로 이동 (새 페이지 생성)
    const validationPageUrl = `/validation?data=${encodeURIComponent(JSON.stringify(validationData))}`
    window.open(validationPageUrl, '_blank')
  }

  return (
    <div className="flex flex-col w-full min-w-0 h-[calc(100vh-65px)] bg-white rounded-none border-0 border-b border-gray-200 overflow-hidden relative">
      {/* 헤더 - 전체 너비 */}
      <div className="flex-shrink-0 w-full px-4 sm:px-6 py-3 border-b border-gray-200 bg-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-md bg-gray-900 flex items-center justify-center">
              <SparklesIcon className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 
                className="text-base font-semibold text-gray-900 cursor-pointer hover:text-gray-700"
                onClick={handleRenameProject}
                title="클릭하여 이름 변경"
              >
                {projectName}
              </h2>
              <p className="text-xs text-gray-500">단계별로 함께 만들어갑니다</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {/* 진행 단계 표시 */}
            <div className="flex items-center gap-1 px-3 py-1.5 rounded-md bg-gray-50 border border-gray-200">
              {phases.map((phase, idx) => (
                <div key={phase} className="flex items-center">
                  <div className={`w-1.5 h-1.5 rounded-full transition-all duration-300 ${
                    idx < currentPhaseIndex ? phaseConfig[phase].dot :
                    idx === currentPhaseIndex ? `${phaseConfig[phase].dot} animate-pulse` :
                    'bg-gray-300'
                  }`} />
                  {idx < phases.length - 1 && (
                    <div className={`w-5 h-0.5 mx-1 transition-all duration-300 ${
                      idx < currentPhaseIndex ? phaseConfig[phase].dot : 'bg-gray-200'
                    }`} />
                  )}
                </div>
              ))}
            </div>
            
            {/* 현재 단계 배지 */}
            <div className={`px-2.5 py-1 rounded-md text-xs font-medium border ${phaseConfig[currentPhase].color}`}>
              {phaseConfig[currentPhase].name}
            </div>

            {/* 프로젝트 목록 버튼 */}
            <button
              onClick={() => router.push('/projects')}
              className="p-2 rounded-md hover:bg-gray-100 transition-colors text-gray-600 hover:text-gray-900"
              title="프로젝트 목록"
            >
              <FolderIcon className="w-4 h-4" />
            </button>
            
            {/* 공유 버튼 */}
            {projectStarted && (
              <button
                onClick={() => setShowShareModal(true)}
                className="p-2 rounded-md hover:bg-gray-100 transition-colors text-gray-600 hover:text-gray-900"
                title="프로젝트 공유"
              >
                <ShareIcon className="w-4 h-4" />
              </button>
            )}
            
            {/* 내보내기 버튼 */}
            {projectStarted && (
              <button
                onClick={handleExport}
                className="p-2 rounded-md hover:bg-gray-100 transition-colors text-gray-600 hover:text-gray-900"
                title="데이터 내보내기"
              >
                <DocumentArrowDownIcon className="w-4 h-4" />
              </button>
            )}

            {/* 캔버스 토글 버튼 */}
            {projectStarted && (
              <button
                onClick={() => setShowCanvas(!showCanvas)}
                className="p-2 rounded-md hover:bg-gray-100 transition-colors text-gray-600 hover:text-gray-900"
                title="프로젝트 캔버스"
              >
                <ChartBarIcon className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 본문: 왼쪽 채팅 목록 | 오른쪽 문서 (채팅이 왼쪽 빈 자리를 쓰고, 나머지는 문서) */}
      <div className="flex flex-1 min-h-0 w-full">
        {/* 왼쪽 - 채팅 목록 (너비 넉넉히, 오류/긴 메시지도 보기 편하게) */}
        <div className="flex flex-col w-[560px] min-w-[420px] max-w-[50vw] flex-shrink-0 border-r border-gray-200 bg-[#faf9f7]">
          <div className="flex-shrink-0 px-3 py-2 border-b border-gray-200 bg-white">
            <span className="text-xs font-medium text-gray-500">채팅</span>
          </div>

        {/* 메시지 영역 */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.map((message, idx) => (
          <div
            key={message.id}
            className={`flex gap-4 animate-in fade-in slide-in-from-bottom-2 duration-300 ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
            style={{ animationDelay: `${idx * 50}ms` }}
          >
            {message.role === 'assistant' && (
              <div className="w-8 h-8 rounded-md bg-gray-900 flex items-center justify-center flex-shrink-0 mt-1">
                <SparklesIcon className="w-4 h-4 text-white" />
              </div>
            )}
            
            <div className={`max-w-full rounded-lg px-3 py-2 ${
              message.role === 'user'
                ? 'bg-gray-900 text-white'
                : 'bg-gray-50 text-gray-900 border border-gray-200'
            }`}>
              {message.phase && message.role === 'assistant' && (
                <div className="mb-2">
                  <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-medium border ${phaseConfig[message.phase].color}`}>
                    <div className={`w-1.5 h-1.5 rounded-full ${phaseConfig[message.phase].dot}`} />
                    {phaseConfig[message.phase].name} 단계
                  </span>
                </div>
              )}
              <div className={`text-sm leading-relaxed whitespace-pre-wrap ${
                message.role === 'user' ? 'text-white' : 'text-gray-900'
              }`}>
                {message.content}
              </div>
            </div>

            {message.role === 'user' && (
              <div className="w-8 h-8 rounded-md bg-gray-200 flex items-center justify-center flex-shrink-0 mt-1">
                <div className="w-5 h-5 rounded-full bg-gray-400" />
              </div>
            )}
          </div>
        ))}
        
        {loading && (
          <div className="flex gap-4 animate-in fade-in">
            <div className="w-8 h-8 rounded-md bg-gray-900 flex items-center justify-center flex-shrink-0">
              <SparklesIcon className="w-4 h-4 text-white" />
            </div>
            <div className="bg-gray-50 rounded-lg px-4 py-3 border border-gray-200">
              <div className="flex gap-1.5">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

        {/* 입력 필드 */}
        <div className="border-t border-gray-200 bg-white p-3">
          {/* 빠른 액션 버튼 */}
          {currentPhase === 'idea' && !projectStarted && (
            <div className="mb-3 flex flex-wrap gap-2">
              {[
                { text: '아이디어가 있어요', icon: '💡' },
                { text: '아이디어를 찾고 있어요', icon: '🔍' },
                { text: '문제를 발견했어요', icon: '⚠️' }
              ].map((action) => (
                <button
                  key={action.text}
                  onClick={() => sendMessage(action.text)}
                  className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-50 hover:bg-gray-100 rounded-md border border-gray-200 transition-all duration-150 hover:border-gray-300"
                >
                  <span>{action.icon}</span>
                  <span>{action.text}</span>
                </button>
              ))}
            </div>
          )}
          <div className="flex items-end gap-2">
            <button className="p-2 rounded-md hover:bg-gray-100 text-gray-600">
              <PaperClipIcon className="w-4 h-4" />
            </button>
            <div className="flex-1 relative">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Reply..."
                className="w-full px-3 py-2 pr-10 text-sm text-gray-900 bg-white border border-gray-200 rounded-md focus:outline-none focus:border-gray-900 resize-none transition-all duration-150 placeholder:text-gray-400"
                rows={1}
                disabled={loading}
              />
            </div>
            <button
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
              className="p-2 bg-[#d97757] hover:bg-[#c4694a] text-white rounded-md transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center min-w-[36px] h-[36px]"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <PaperAirplaneIcon className="w-4 h-4" />
              )}
            </button>
          </div>

          {/* 액션 버튼들 */}
          {projectStarted && (
            <div className="mt-3 flex items-center justify-between">
              <div className="flex gap-2">
                {(projectState.problem || projectState.solution) && (
                  <button
                    onClick={handleCreateValidationPage}
                    className="inline-flex items-center gap-1.5 text-xs text-gray-600 hover:text-gray-900 transition-colors px-3 py-1.5 rounded-md hover:bg-gray-50 border border-gray-200"
                  >
                    검증 페이지 생성
                  </button>
                )}
              </div>
              <button
                onClick={() => {
                  if (confirm('프로젝트를 초기화하시겠습니까? 모든 대화 기록과 프로젝트 상태가 삭제됩니다.')) {
                    setMessages([])
                    setProjectState({})
                    setCurrentPhase('idea')
                    setProjectStarted(false)
                    setShowCanvas(false)
                    if (projectId) {
                      saveProject()
                    }
                  }
                }}
                className="inline-flex items-center gap-1.5 text-xs text-gray-500 hover:text-red-600 transition-colors px-2 py-1 rounded-md hover:bg-red-50"
              >
                <ArrowPathIcon className="w-3.5 h-3.5" />
                프로젝트 초기화
              </button>
            </div>
          )}
        </div>
      </div>

        {/* 오른쪽 - 문서가 적히는 공간 (남는 너비 전부 사용) */}
        <div className="flex-1 min-w-0 relative bg-[#faf9f7]">
          <DocumentCanvas
            documents={documents}
            onUpdateDocument={handleUpdateDocument}
            onDeleteDocument={handleDeleteDocument}
            onCheckItem={handleCheckItem}
          />
        </div>
      </div>

      {/* 프로젝트 캔버스 (기존 기능 유지) */}
      {showCanvas && (
        <div className="absolute inset-0 z-30 bg-white">
          <ProjectCanvas 
            projectState={projectState} 
            currentPhase={currentPhase}
            onClose={() => setShowCanvas(false)}
          />
        </div>
      )}

      {/* 공유 모달 */}
      {showShareModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">프로젝트 공유</h3>
            <p className="text-sm text-gray-600 mb-4">
              아래 링크를 복사하여 다른 사람과 프로젝트를 공유할 수 있습니다.
            </p>
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                readOnly
                value={projectId ? `${window.location.origin}/cofounder?project=${projectId}` : ''}
                className="flex-1 px-4 py-2 border-2 border-gray-200 rounded-md text-sm text-gray-900 bg-white focus:outline-none focus:border-gray-900"
              />
              <button
                onClick={handleShare}
                className="px-4 py-2 bg-gray-900 hover:bg-gray-800 text-white rounded-md text-sm font-medium transition-colors"
              >
                복사
              </button>
            </div>
            <button
              onClick={() => setShowShareModal(false)}
              className="w-full px-4 py-2 border-2 border-gray-200 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
            >
              닫기
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
