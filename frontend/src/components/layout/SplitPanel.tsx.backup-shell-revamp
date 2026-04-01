import React from 'react'

interface SplitPanelProps {
  listContent: React.ReactNode
  compressedList: React.ReactNode
  detailContent: React.ReactNode
  isDetailOpen: boolean
}

export const SplitPanel = ({ listContent, compressedList, detailContent, isDetailOpen }: SplitPanelProps) => {
  return (
    <div style={{ display: 'flex', height: '100%', overflow: 'hidden' }}>
      {/* Left - List Panel */}
      <div style={{
        width: isDetailOpen ? '20%' : '100%',
        transition: 'width 0.3s ease',
        borderRight: isDetailOpen ? '1px solid #e2e8f0' : 'none',
        overflowY: 'auto',
        flexShrink: 0,
        minWidth: isDetailOpen ? 250 : 'unset'
      }}>
        {isDetailOpen ? compressedList : listContent}
      </div>

      {/* Right - Detail Panel */}
      {isDetailOpen && (
        <div style={{
          width: '80%',
          overflowY: 'auto',
          background: 'white',
          animation: 'slideIn 0.3s ease'
        }}>
          {detailContent}
        </div>
      )}
    </div>
  )
}
