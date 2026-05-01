import React from 'react'
import { Button, Popover, Checkbox, Radio, Divider, Space, Typography } from 'antd'
import { Settings2, Columns, Layout as LayoutIcon, Maximize2, Minimize2 } from 'lucide-react'
import { useUserPreferences } from '@/hooks/useUserPreferences'

const { Text } = Typography

interface ColumnOption {
  id: string
  label: string
}

interface SectionOption {
  id: string
  label: string
}

interface CustomizeViewProps {
  pageId: string
  columns?: ColumnOption[]
  sections?: SectionOption[]
}

export const CustomizeView: React.FC<CustomizeViewProps> = ({
  pageId,
  columns = [],
  sections = [],
}) => {
  const { pages, toggleColumn, toggleSection, setDensity } = useUserPreferences()
  const prefs = pages[pageId] || { hiddenColumns: [], hiddenSections: [], density: 'comfortable' }

  const content = (
    <div className="w-64 p-1">
      <div className="mb-4">
        <Text className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-2 px-2">Display Density</Text>
        <Radio.Group 
          value={prefs.density} 
          onChange={(e) => setDensity(pageId, e.target.value)}
          size="small"
          className="w-full px-2"
        >
          <Space direction="vertical" className="w-full">
            <Radio value="comfortable" className="text-xs font-medium">
              <div className="flex items-center gap-2">
                <Maximize2 size={14} className="text-slate-400" />
                Comfortable
              </div>
            </Radio>
            <Radio value="compact" className="text-xs font-medium">
              <div className="flex items-center gap-2">
                <Minimize2 size={14} className="text-slate-400" />
                Compact
              </div>
            </Radio>
          </Space>
        </Radio.Group>
      </div>

      {columns.length > 0 && (
        <>
          <Divider className="my-3" />
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-2 px-2">
              <Columns size={12} className="text-slate-400" />
              <Text className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Visible Columns</Text>
            </div>
            <div className="max-h-48 overflow-y-auto px-2">
              <Space direction="vertical" className="w-full">
                {columns.map((col) => (
                  <Checkbox
                    key={col.id}
                    checked={!prefs.hiddenColumns.includes(col.id)}
                    onChange={() => toggleColumn(pageId, col.id)}
                    className="text-xs font-medium"
                  >
                    {col.label}
                  </Checkbox>
                ))}
              </Space>
            </div>
          </div>
        </>
      )}

      {sections.length > 0 && (
        <>
          <Divider className="my-3" />
          <div className="mb-2">
            <div className="flex items-center gap-2 mb-2 px-2">
              <LayoutIcon size={12} className="text-slate-400" />
              <Text className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Page Sections</Text>
            </div>
            <div className="px-2">
              <Space direction="vertical" className="w-full">
                {sections.map((sec) => (
                  <Checkbox
                    key={sec.id}
                    checked={!prefs.hiddenSections.includes(sec.id)}
                    onChange={() => toggleSection(pageId, sec.id)}
                    className="text-xs font-medium"
                  >
                    {sec.label}
                  </Checkbox>
                ))}
              </Space>
            </div>
          </div>
        </>
      )}
    </div>
  )

  return (
    <Popover
      content={content}
      title={<div className="px-2 py-1 text-xs font-bold text-slate-700">Customize View</div>}
      trigger="click"
      placement="bottomRight"
      arrow={false}
      overlayClassName="customize-view-popover"
    >
      <Button 
        type="text" 
        icon={<Settings2 size={16} />}
        className="flex items-center gap-2 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg h-9 font-medium text-xs transition-all"
      >
        Customize View
      </Button>
    </Popover>
  )
}
