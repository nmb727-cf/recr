import React from 'react'
import { Button } from 'antd'
import { CloseOutlined } from '@ant-design/icons'

interface DetailPanelHeaderProps {
  title: React.ReactNode
  tags?: React.ReactNode
  actions?: React.ReactNode
  onClose: () => void
}

export const DetailPanelHeader = ({ title, tags, actions, onClose }: DetailPanelHeaderProps) => (
  <div style={{
    padding: '20px 24px',
    borderBottom: '1px solid #e2e8f0',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    position: 'sticky',
    top: 0,
    background: 'white',
    zIndex: 10
  }}>
    <div>
      <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>{title}</h2>
      <div style={{ display: 'flex', gap: 8, marginTop: 8, flexWrap: 'wrap' }}>
        {tags}
      </div>
    </div>
    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
      {actions}
      <Button onClick={onClose} icon={<CloseOutlined />} />
    </div>
  </div>
)
