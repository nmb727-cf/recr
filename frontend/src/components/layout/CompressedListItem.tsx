import { Tag } from 'antd'

interface CompressedListItemProps {
  title: string
  subtitle?: string
  status?: string
  statusColor?: string
  isSelected: boolean
  onClick: () => void
}

export const CompressedListItem = ({ title, subtitle, status, statusColor, isSelected, onClick }: CompressedListItemProps) => (
  <div
    onClick={onClick}
    style={{
      padding: '12px 16px',
      borderBottom: '1px solid #f0f0f0',
      cursor: 'pointer',
      background: isSelected ? '#eff6ff' : 'white',
      borderLeft: isSelected ? '3px solid #2563eb' : '3px solid transparent',
      transition: 'all 0.15s ease'
    }}
  >
    <p style={{
      margin: 0,
      fontWeight: 600,
      fontSize: 13,
      whiteSpace: 'nowrap',
      overflow: 'hidden',
      textOverflow: 'ellipsis'
    }}>{title}</p>
    {subtitle && (
      <p style={{ margin: '2px 0 0', fontSize: 11, color: '#888',
                  whiteSpace: 'nowrap', overflow: 'hidden', 
                  textOverflow: 'ellipsis' }}>
        {subtitle}
      </p>
    )}
    {status && <Tag color={statusColor} style={{ fontSize: 10, padding: '0 4px', marginTop: 4 }}>{status}</Tag>}
  </div>
)
