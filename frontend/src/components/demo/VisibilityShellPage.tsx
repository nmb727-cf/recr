import { Card, Space, Table, Tag, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useMemo } from 'react'

import type { DemoSectionConfig } from '@/data/uiVisibilityDemo'

const { Title, Text, Paragraph } = Typography

const toneClasses: Record<string, string> = {
  blue: 'bg-blue-50 text-blue-700 border-blue-100',
  green: 'bg-emerald-50 text-emerald-700 border-emerald-100',
  amber: 'bg-amber-50 text-amber-700 border-amber-100',
  red: 'bg-rose-50 text-rose-700 border-rose-100',
  slate: 'bg-slate-100 text-slate-700 border-slate-200',
  violet: 'bg-violet-50 text-violet-700 border-violet-100',
}

export default function VisibilityShellPage({ config }: { config: DemoSectionConfig }) {
  const columns = useMemo<ColumnsType<Record<string, string | number>>>(
    () =>
      config.columns.map((column) => ({
        title: column.title,
        dataIndex: column.key,
        key: column.key,
        render: (value: string | number) => {
          if (typeof value === 'string' && /ready|approved|accepted|joined|closed|frozen/i.test(value)) {
            return <Tag color="green">{value}</Tag>
          }
          if (typeof value === 'string' && /pending|review|warning|queued|paused/i.test(value)) {
            return <Tag color="gold">{value}</Tag>
          }
          if (typeof value === 'string' && /blocked|failed|critical|rejected|expired|escalated/i.test(value)) {
            return <Tag color="red">{value}</Tag>
          }
          return <span>{String(value)}</span>
        },
      })),
    [config.columns],
  )

  return (
    <div className="mx-auto flex max-w-[1500px] flex-col gap-6 p-6">
      <div className="flex flex-col gap-3 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <Text className="text-[11px] font-black uppercase tracking-[0.28em] text-slate-400">{config.context}</Text>
        <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <Title level={2} className="!mb-1 !mt-0">
              {config.title}
            </Title>
            <Paragraph className="!mb-0 max-w-3xl text-slate-500">{config.subtitle}</Paragraph>
          </div>
          <Tag className="w-fit rounded-full border-blue-100 bg-blue-50 px-4 py-1 text-[11px] font-semibold uppercase tracking-wider text-blue-700">
            Demo visibility enabled
          </Tag>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {config.metrics.map((metric) => (
          <Card key={metric.label} className="rounded-2xl border border-slate-200 shadow-sm">
            <Space direction="vertical" size={4}>
              <Text className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-400">{metric.label}</Text>
              <Text className="text-3xl font-black text-slate-900">{metric.value}</Text>
              <Tag className={`w-fit rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-wider ${toneClasses[metric.tone || 'slate']}`}>
                live shell
              </Tag>
            </Space>
          </Card>
        ))}
      </div>

      <Card className="rounded-3xl border border-slate-200 shadow-sm" bodyStyle={{ padding: 0 }}>
        <div className="border-b border-slate-200 px-6 py-4">
          <Title level={4} className="!m-0">
            Seeded Records
          </Title>
          <Text className="text-slate-500">Five realistic demo records are loaded so this section is immediately inspectable.</Text>
        </div>
        <Table
          rowKey={(row) => `${config.title}-${JSON.stringify(row)}`}
          columns={columns}
          dataSource={config.rows}
          pagination={false}
          scroll={{ x: 960 }}
        />
      </Card>

      <Card className="rounded-3xl border border-slate-200 bg-slate-900 text-white shadow-sm">
        <Space direction="vertical" size={8}>
          <Text className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Visibility note</Text>
          <Paragraph className="!mb-0 text-slate-200">{config.callout}</Paragraph>
        </Space>
      </Card>
    </div>
  )
}
