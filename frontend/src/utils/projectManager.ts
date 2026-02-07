/**
 * 프로젝트 관리 유틸리티
 * 다중 프로젝트 저장, 로드, 삭제 기능
 */

export interface Project {
  id: string
  name: string
  createdAt: string
  updatedAt: string
  currentPhase: string
  projectState: any
  messages: any[]
}

const PROJECTS_KEY = 'pixi_projects'
const CURRENT_PROJECT_KEY = 'pixi_current_project_id'

export const projectManager = {
  // 모든 프로젝트 가져오기
  getAllProjects(): Project[] {
    if (typeof window === 'undefined') return [] // SSR 방지
    
    try {
      const projectsJson = localStorage.getItem(PROJECTS_KEY)
      if (!projectsJson) return []
      return JSON.parse(projectsJson)
    } catch (e) {
      console.error('프로젝트 목록 로드 실패:', e)
      return []
    }
  },

  // 프로젝트 저장
  saveProject(project: Project): void {
    if (typeof window === 'undefined') return // SSR 방지
    
    const projects = this.getAllProjects()
    const existingIndex = projects.findIndex(p => p.id === project.id)
    
    if (existingIndex >= 0) {
      projects[existingIndex] = project
    } else {
      projects.push(project)
    }
    
    localStorage.setItem(PROJECTS_KEY, JSON.stringify(projects))
  },

  // 프로젝트 가져오기
  getProject(id: string): Project | null {
    if (typeof window === 'undefined') return null // SSR 방지
    
    const projects = this.getAllProjects()
    return projects.find(p => p.id === id) || null
  },

  // 프로젝트 삭제
  deleteProject(id: string): void {
    if (typeof window === 'undefined') return // SSR 방지
    
    const projects = this.getAllProjects()
    const filtered = projects.filter(p => p.id !== id)
    localStorage.setItem(PROJECTS_KEY, JSON.stringify(filtered))
    
    // 현재 프로젝트가 삭제된 경우
    if (this.getCurrentProjectId() === id) {
      localStorage.removeItem(CURRENT_PROJECT_KEY)
    }
  },

  // 현재 프로젝트 ID 가져오기
  getCurrentProjectId(): string | null {
    if (typeof window === 'undefined') return null // SSR 방지
    return localStorage.getItem(CURRENT_PROJECT_KEY)
  },

  // 현재 프로젝트 ID 설정
  setCurrentProjectId(id: string): void {
    if (typeof window === 'undefined') return // SSR 방지
    localStorage.setItem(CURRENT_PROJECT_KEY, id)
  },

  // 새 프로젝트 생성
  createProject(name: string): Project {
    if (typeof window === 'undefined') {
      // SSR에서는 더미 프로젝트 반환 (실제로는 사용되지 않음)
      return {
        id: 'temp',
        name,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        currentPhase: 'idea',
        projectState: {},
        messages: []
      }
    }
    
    const id = `project_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const now = new Date().toISOString()
    
    const project: Project = {
      id,
      name,
      createdAt: now,
      updatedAt: now,
      currentPhase: 'idea',
      projectState: {},
      messages: []
    }
    
    this.saveProject(project)
    this.setCurrentProjectId(id)
    return project
  },

  // 프로젝트 이름 업데이트
  updateProjectName(id: string, name: string): void {
    if (typeof window === 'undefined') return // SSR 방지
    
    const project = this.getProject(id)
    if (project) {
      project.name = name
      project.updatedAt = new Date().toISOString()
      this.saveProject(project)
    }
  }
}
