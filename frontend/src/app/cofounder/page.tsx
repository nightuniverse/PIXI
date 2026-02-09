'use client'

import AICofounderChat from '@/components/AICofounderChat'
import Link from 'next/link'
import { ArrowLeftIcon, ArrowRightIcon } from '@heroicons/react/24/outline'

export default function CofounderPage() {
  return (
    <div className="min-h-screen bg-white relative overflow-hidden">
      {/* Figma 스타일 그리드 배경 */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#f5f5f5_1px,transparent_1px),linear-gradient(to_bottom,#f5f5f5_1px,transparent_1px)] bg-[size:16px_16px] opacity-50" />
      
      {/* 헤더 */}
      <header className="relative z-10 border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0">
        <div className="w-full max-w-[100vw] px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                href="/"
                className="p-2 rounded-md hover:bg-gray-100 transition-colors text-gray-600 hover:text-gray-900"
              >
                <ArrowLeftIcon className="w-5 h-5" />
              </Link>
              <div>
                <h1 className="text-lg font-semibold text-gray-900">AI 공동창업자</h1>
                <p className="text-sm text-gray-500 mt-0.5">아이디어부터 제품까지, 단계별로 함께 만들어갑니다</p>
              </div>
            </div>
            <div className="flex items-center gap-6">
              <Link
                href="/projects"
                className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
              >
                내 프로젝트
              </Link>
              <Link
                href="/startup-idea"
                className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors inline-flex items-center gap-1"
              >
                아이템 발굴
                <ArrowRightIcon className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </header>
      
      <main className="relative z-10 w-full min-w-0">
        <AICofounderChat />
      </main>
    </div>
  )
}
