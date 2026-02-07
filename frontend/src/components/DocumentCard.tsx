'use client'

import React, { useState, useEffect } from 'react'
import { XMarkIcon, ChevronUpIcon, ArrowsPointingOutIcon } from '@heroicons/react/24/outline'

interface ChecklistItem {
  id: string
  text: string
  checked: boolean
}

interface DocumentCardProps {
  id: string
  title: string
  section?: string
  checklist?: ChecklistItem[]
  content?: string
  x?: number
  y?: number
  onUpdate?: (id: string, updates: Partial<DocumentCardProps>) => void
  onDelete?: (id: string) => void
  onCheckItem?: (cardId: string, itemId: string, checked: boolean) => void
}

export default function DocumentCard({
  id,
  title,
  section,
  checklist = [],
  content,
  x = 0,
  y = 0,
  onUpdate,
  onDelete,
  onCheckItem
}: DocumentCardProps) {
  const [isMinimized, setIsMinimized] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [position, setPosition] = useState({ x, y })

  const handleMouseDown = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('button, input')) return
    
    setIsDragging(true)
    setDragStart({
      x: e.clientX - position.x,
      y: e.clientY - position.y
    })
  }

  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging) return
    
    setPosition({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    })
  }

  const handleMouseUp = () => {
    if (isDragging) {
      setIsDragging(false)
      if (onUpdate) {
        onUpdate(id, { x: position.x, y: position.y })
      }
    }
  }

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      return () => {
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isDragging, dragStart])

  return (
    <div
      className={`absolute bg-white rounded-lg border border-gray-200 shadow-lg ${
        isDragging ? 'cursor-grabbing' : 'cursor-grab'
      }`}
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        width: '400px',
        minHeight: isMinimized ? 'auto' : '200px'
      }}
      onMouseDown={handleMouseDown}
    >
      {/* 헤더 */}
      <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-b border-gray-200 rounded-t-lg">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded-full bg-gray-900 flex items-center justify-center">
            <div className="w-2 h-2 bg-white rounded-sm"></div>
          </div>
          <span className="text-sm font-medium text-gray-700">{title}</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-1 rounded hover:bg-gray-200 transition-colors"
          >
            {isMinimized ? (
              <ArrowsPointingOutIcon className="w-4 h-4 text-gray-600" />
            ) : (
              <ChevronUpIcon className="w-4 h-4 text-gray-600" />
            )}
          </button>
          {onDelete && (
            <button
              onClick={() => onDelete(id)}
              className="p-1 rounded hover:bg-gray-200 transition-colors"
            >
              <XMarkIcon className="w-4 h-4 text-gray-600" />
            </button>
          )}
        </div>
      </div>

      {/* 내용 */}
      {!isMinimized && (
        <div className="p-4">
          {section && (
            <p className="text-xs text-gray-500 mb-3 font-medium">{section}</p>
          )}
          
          {checklist.length > 0 && (
            <div className="space-y-2">
              {checklist.map((item) => (
                <label
                  key={item.id}
                  className="flex items-start gap-2 cursor-pointer group"
                >
                  <input
                    type="checkbox"
                    checked={item.checked}
                    onChange={(e) => {
                      if (onCheckItem) {
                        onCheckItem(id, item.id, e.target.checked)
                      }
                    }}
                    className="mt-0.5 w-4 h-4 rounded border-gray-300 text-gray-900 focus:ring-gray-900 cursor-pointer"
                  />
                  <span className={`text-sm text-gray-700 flex-1 ${
                    item.checked ? 'line-through text-gray-400' : ''
                  }`}>
                    {item.text}
                  </span>
                </label>
              ))}
            </div>
          )}

          {content && (
            <div className="mt-3 pt-3 border-t border-gray-200">
              <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">{content}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

