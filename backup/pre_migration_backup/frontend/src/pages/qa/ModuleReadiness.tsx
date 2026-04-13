import React from 'react'
import { Card, Table, Typography, Tag, Statistic, Row, Col, List, Empty } from 'antd'
import { qaApi } from '@/api/qaApi'
import { useApiQuery } from '@/hooks/useApiQuery'
import { CheckCircle2, AlertTriangle, ShieldAlert, Activity } from 'lucide-react'

const { Title, Text } = Typography

function getStatusColor(status: string) {
  if (!status) return 'default'
  if (status.includes('production')) return 'green'
  if (status.includes('workflow')) return 'blue'
  if (status.includes('integration')) return 'cyan'
  if (status.includes('functional')) return 'geekblue'
  if (status.includes('in_development')) return 'orange'
  return 'default'
}

export default function ModuleReadiness() {
  const { data: modulesData, isLoading: modulesLoading } = useApiQuery(['qa_modules'], qaApi.getModules)
  const { data: blockersData, isLoading: blockersLoading } = useApiQuery(['qa_blockers'], qaApi.getBlockers)
  const { data: scenariosData, isLoading: scenariosLoading } = useApiQuery(['qa_scenarios'], qaApi.getScenarios)

  const modules = Array.isArray(modulesData) ? modulesData : modulesData?.data || []
  const blockers = Array.isArray(blockersData) ? blockersData : blockersData?.data || []
  const scenarios = Array.isArray(scenariosData) ? scenariosData : scenariosData?.data || []

  const workflowReadyCount = modules.filter(m => ['workflow_ready', 'production_ready'].includes(m.final_status)).length
  const prodReadyCount = modules.filter(m => m.final_status === 'production_ready').length
  const blockersCount = blockers.length

  const moduleColumns = [
    { title: 'Module', dataIndex: 'module_key', render: (v: string) => <Text strong>{v}</Text> },
    { title: 'Functional', dataIndex: 'functional_score', render: (v: number) => `${v}%` },
    { title: 'Integration', dataIndex: 'integration_score', render: (v: number) => `${v}%` },
    { title: 'Workflow', dataIndex: 'workflow_score', render: (v: number) => `${v}%` },
    { title: 'Overall', dataIndex: 'overall_score', render: (v: number) => `${v}%` },
    { title: 'Status', dataIndex: 'final_status', render: (v: string) => <Tag color={getStatusColor(v)}>{v?.replace('_', ' ').toUpperCase()}</Tag> },
    { title: 'Blockers', dataIndex: 'blockers_count', render: (v: number) => v > 0 ? <Tag color="red">{v}</Tag> : <Tag color="green">0</Tag> }
  ]

  const scenarioColumns = [
    { title: 'Scenario', dataIndex: 'scenario_name' },
    { title: 'Status', dataIndex: 'status', render: (v: string) => <Tag color={v === 'passed' ? 'green' : 'red'}>{v?.toUpperCase()}</Tag> },
    { title: 'Failed Step', dataIndex: 'failed_step', render: (v: string) => v || '—' }
  ]

  return (
    <div className="mx-auto flex max-w-[1560px] flex-col gap-6 p-6">
      <div className="flex flex-col gap-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <Title level={2} className="!m-0">Automated Module Readiness</Title>
        <Text className="text-slate-500">Live QA validation and tracking of module maturity for orchestrations.</Text>
      </div>

      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card className="rounded-3xl border-slate-200 shadow-sm">
            <Statistic title="Total Modules Tested" value={modules.length} prefix={<Activity size={16} className="text-indigo-500" />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="rounded-3xl border-slate-200 shadow-sm">
            <Statistic title="Workflow Ready" value={workflowReadyCount} prefix={<CheckCircle2 size={16} className="text-emerald-500" />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="rounded-3xl border-slate-200 shadow-sm">
            <Statistic title="Production Ready" value={prodReadyCount} prefix={<CheckCircle2 size={16} className="text-blue-500" />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="rounded-3xl border-slate-200 shadow-sm">
            <Statistic title="Active Blockers" value={blockersCount} prefix={<ShieldAlert size={16} className="text-rose-500" />} />
          </Card>
        </Col>
      </Row>

      <Card title="Module Readiness Matrix" className="rounded-3xl border-slate-200 shadow-sm" bodyStyle={{ padding: 0 }}>
        <Table dataSource={modules} columns={moduleColumns} rowKey="id" pagination={false} loading={modulesLoading} />
      </Card>

      <Row gutter={[24, 24]}>
        <Col xs={24} xl={12}>
          <Card title="End-to-End Results" className="rounded-3xl border-slate-200 shadow-sm h-full" bodyStyle={{ padding: 0 }}>
            <Table dataSource={scenarios} columns={scenarioColumns} rowKey="id" pagination={false} loading={scenariosLoading} />
          </Card>
        </Col>
        <Col xs={24} xl={12}>
          <Card title="Blocker Register" className="rounded-3xl border-slate-200 shadow-sm h-full">
            {blockersLoading ? <div className="p-4"><Text>Loading...</Text></div> : (
              blockers.length === 0 ? <Empty description="No active blockers!" /> : (
                <List
                  dataSource={blockers}
                  renderItem={(b: any) => (
                    <List.Item className="border-b border-slate-100 last:border-0 p-4 flex-col items-start gap-2">
                      <div className="flex justify-between w-full">
                        <Text strong>{b.title}</Text>
                        <Tag color={b.severity === 'critical' ? 'red' : 'orange'}>{b.severity?.toUpperCase()}</Tag>
                      </div>
                      <Text type="secondary" className="text-xs">Module: {b.module_key}</Text>
                      <Text className="text-sm mt-1">{b.description}</Text>
                      {b.recommended_fix && (
                        <div className="mt-2 bg-slate-50 p-2 rounded-lg text-xs border border-slate-200 w-full">
                          <strong>Fix:</strong> {b.recommended_fix}
                        </div>
                      )}
                    </List.Item>
                  )}
                />
              )
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}
