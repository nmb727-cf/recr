import { Link, useParams } from 'react-router-dom'
import { Card, Space, Tag, Typography } from 'antd'

import VisibilityShellPage from '@/components/demo/VisibilityShellPage'
import { hdcDemoSections } from '@/data/uiVisibilityDemo'

const { Title, Text } = Typography

const sections = [
  { key: 'overview', label: 'Decision Dashboard' },
  { key: 'committee', label: 'Committee' },
  { key: 'comparison', label: 'Candidate Comparison' },
  { key: 'approvals', label: 'Decision Approval' },
  { key: 'offer-intelligence', label: 'Offer Intelligence' },
  { key: 'compensation', label: 'Compensation' },
  { key: 'negotiation', label: 'Negotiation' },
  { key: 'offer-release', label: 'Offer Release' },
  { key: 'offer-acceptance', label: 'Offer Acceptance' },
  { key: 'joining', label: 'Joining Tracking' },
] as const

export default function HiringDecisionWorkspace() {
  const { section } = useParams<{ section?: string }>()
  const activeSection = section && hdcDemoSections[section] ? section : 'overview'
  const config = hdcDemoSections[activeSection]

  return (
    <div className="space-y-6">
      <Card className="mx-auto mt-6 max-w-[1500px] rounded-3xl border border-slate-200 shadow-sm">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <Text className="text-[11px] font-black uppercase tracking-[0.24em] text-slate-400">Hiring Decision Command Center</Text>
            <Title level={3} className="!mb-1 !mt-2">
              Visible HDC Navigation
            </Title>
            <Text className="text-slate-500">
              Every major HDC area is routed and inspectable, even where the backend is still architecture-first.
            </Text>
          </div>
          <Space size={[8, 8]} wrap>
            {sections.map((item) => (
              <Link key={item.key} to={item.key === 'overview' ? '/hiring-decisions' : `/hiring-decisions/${item.key}`}>
                <Tag color={item.key === activeSection ? 'blue' : 'default'} className="cursor-pointer rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-wider">
                  {item.label}
                </Tag>
              </Link>
            ))}
          </Space>
        </div>
      </Card>

      <VisibilityShellPage config={config} />
    </div>
  )
}
