'use client'

import { useState, useEffect, useMemo } from 'react'
import StartupIdeaAnalyzer from '@/components/StartupIdeaAnalyzer'

export default function StartupIdeaPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">창업 아이템 발굴</h1>
              <p className="text-sm text-gray-600 mt-1">시장 조사 기반 아이템 발굴 및 경쟁사 분석</p>
            </div>
            <a 
              href="/explore"
              className="text-blue-600 hover:text-blue-700 text-sm font-medium"
            >
              지도 탐색 →
            </a>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <StartupIdeaAnalyzer />
      </main>
    </div>
  )
}
