'use client'

import { useState, useRef, useEffect } from 'react'
import { HandRaisedIcon, ClockIcon, MinusIcon, PlusIcon } from '@heroicons/react/24/outline'
import DocumentCard from './DocumentCard'

export interface DocumentCardData {
  id: string
  title: string
  section?: string
  checklist?: Array<{ id: string; text: string; checked: boolean }>
  content?: string
  x: number
  y: number
}

interface DocumentCanvasProps {
  documents: DocumentCardData[]
  onUpdateDocument: (id: string, updates: Partial<DocumentCardData>) => void
  onDeleteDocument: (id: string) => void
  onCheckItem: (cardId: string, itemId: string, checked: boolean) => void
}

export default function DocumentCanvas({
  documents,
  onUpdateDocument,
  onDeleteDocument,
  onCheckItem
}: DocumentCanvasProps) {
  const [zoom, setZoom] = useState(100)
  const [isPanning, setIsPanning] = useState(false)
  const [panStart, setPanStart] = useState({ x: 0, y: 0 })
  const [offset, setOffset] = useState({ x: 0, y: 0 })
  const canvasRef = useRef<HTMLDivElement>(null)

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev + 10, 200))
  }

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev - 10, 50))
  }

  const handlePanStart = (e: React.MouseEvent) => {
    setIsPanning(true)
    setPanStart({
      x: e.clientX - offset.x,
      y: e.clientY - offset.y
    })
  }

  const handlePanMove = (e: MouseEvent) => {
    if (!isPanning) return
    setOffset({
      x: e.clientX - panStart.x,
      y: e.clientY - panStart.y
    })
  }

  const handlePanEnd = () => {
    setIsPanning(false)
  }

  useEffect(() => {
    if (isPanning) {
      document.addEventListener('mousemove', handlePanMove)
      document.addEventListener('mouseup', handlePanEnd)
      return () => {
        document.removeEventListener('mousemove', handlePanMove)
        document.removeEventListener('mouseup', handlePanEnd)
      }
    }
  }, [isPanning, panStart])

  return (
    <div className="relative w-full h-full bg-[#faf9f7] overflow-hidden">
      {/* 점 패턴 배경 */}
      <div 
        className="absolute inset-0 bg-[radial-gradient(circle,_#d4d4d4_1px,_transparent_1px)] bg-[size:20px_20px] opacity-30"
        style={{
          transform: `scale(${zoom / 100}) translate(${offset.x / (zoom / 100)}px, ${offset.y / (zoom / 100)}px)`,
          transformOrigin: '0 0'
        }}
      />

      {/* 문서 카드들 */}
      <div
        ref={canvasRef}
        className="absolute inset-0"
        style={{
          transform: `scale(${zoom / 100}) translate(${offset.x / (zoom / 100)}px, ${offset.y / (zoom / 100)}px)`,
          transformOrigin: '0 0'
        }}
      >
        {documents.map((doc) => (
          <DocumentCard
            key={doc.id}
            {...doc}
            onUpdate={onUpdateDocument}
            onDelete={onDeleteDocument}
            onCheckItem={onCheckItem}
          />
        ))}
      </div>

      {/* 하단 컨트롤 */}
      <div className="absolute bottom-4 right-4 flex items-center gap-2">
        {/* 패닝 도구 */}
        <button
          onMouseDown={handlePanStart}
          className={`p-2 rounded-md bg-white border border-gray-200 shadow-sm hover:bg-gray-50 transition-colors ${
            isPanning ? 'bg-gray-100' : ''
          }`}
          title="캔버스 이동"
        >
          <HandRaisedIcon className="w-4 h-4 text-gray-600" />
        </button>

        {/* 히스토리 (향후 구현) */}
        <button
          className="p-2 rounded-md bg-white border border-gray-200 shadow-sm hover:bg-gray-50 transition-colors"
          title="히스토리"
        >
          <ClockIcon className="w-4 h-4 text-gray-600" />
        </button>

        {/* 줌 컨트롤 */}
        <div className="flex items-center gap-2 px-2 py-1 bg-white border border-gray-200 rounded-md shadow-sm">
          <button
            onClick={handleZoomOut}
            className="p-1 rounded hover:bg-gray-100 transition-colors"
            disabled={zoom <= 50}
          >
            <MinusIcon className="w-4 h-4 text-gray-600" />
          </button>
          <span className="text-xs font-medium text-gray-700 min-w-[3rem] text-center">
            {zoom}%
          </span>
          <button
            onClick={handleZoomIn}
            className="p-1 rounded hover:bg-gray-100 transition-colors"
            disabled={zoom >= 200}
          >
            <PlusIcon className="w-4 h-4 text-gray-600" />
          </button>
        </div>
      </div>
    </div>
  )
}
