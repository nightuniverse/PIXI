'use client'

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeftIcon } from '@heroicons/react/24/outline'

interface ValidationData {
  problem?: string
  solution?: string
  targetCustomers?: string[]
  projectName?: string
}

export default function ValidationPage() {
  const searchParams = useSearchParams()
  const [data, setData] = useState<ValidationData | null>(null)
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)

  useEffect(() => {
    const dataParam = searchParams.get('data')
    if (dataParam) {
      try {
        setData(JSON.parse(decodeURIComponent(dataParam)))
      } catch (e) {
        console.error('데이터 파싱 오류:', e)
      }
    }
  }, [searchParams])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // 실제로는 백엔드 API로 전송
    setSubmitted(true)
    setTimeout(() => {
      alert('감사합니다! 곧 연락드리겠습니다.')
    }, 500)
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">데이터를 불러올 수 없습니다.</p>
          <Link href="/cofounder" className="text-blue-600 hover:text-blue-700 mt-4 inline-block">
            AI 공동창업자로 돌아가기
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <header className="bg-white border-b border-gray-100">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <Link
            href="/cofounder"
            className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeftIcon className="w-4 h-4" />
            AI 공동창업자로 돌아가기
          </Link>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            {data.projectName || '새로운 제품'}에 관심이 있으신가요?
          </h1>
          <p className="text-xl text-gray-600">
            출시 알림을 받고 초기 사용자가 되어주세요
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8 mb-8">
          {/* 문제 */}
          {data.problem && (
            <div className="mb-8">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">해결하려는 문제</h2>
              <p className="text-gray-700 leading-relaxed">{data.problem}</p>
            </div>
          )}

          {/* 솔루션 */}
          {data.solution && (
            <div className="mb-8">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">우리의 솔루션</h2>
              <p className="text-gray-700 leading-relaxed">{data.solution}</p>
            </div>
          )}

          {/* 타겟 고객 */}
          {data.targetCustomers && data.targetCustomers.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-3">타겟 고객</h2>
              <ul className="space-y-2">
                {data.targetCustomers.map((customer, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-gray-700">
                    <span className="text-blue-500 mt-1">•</span>
                    <span>{customer}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* 이메일 수집 폼 */}
        {!submitted ? (
          <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4 text-center">
              출시 알림 받기
            </h2>
            <p className="text-gray-600 text-center mb-6">
              이메일을 남기시면 제품이 출시되는 즉시 알려드리겠습니다
            </p>
            <form onSubmit={handleSubmit} className="max-w-md mx-auto">
              <div className="flex gap-3">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your@email.com"
                  required
                  className="flex-1 px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                />
                <button
                  type="submit"
                  className="px-6 py-3 bg-gray-900 hover:bg-gray-800 text-white rounded-xl font-medium transition-colors"
                >
                  알림 받기
                </button>
              </div>
            </form>
          </div>
        ) : (
          <div className="bg-green-50 border border-green-200 rounded-2xl p-8 text-center">
            <div className="text-4xl mb-4">✅</div>
            <h3 className="text-xl font-semibold text-green-900 mb-2">감사합니다!</h3>
            <p className="text-green-700">출시 시 알려드리겠습니다.</p>
          </div>
        )}
      </main>
    </div>
  )
}
