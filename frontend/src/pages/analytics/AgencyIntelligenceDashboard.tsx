import { Alert, Avatar, Card, Empty, Progress, Spin, Statistic, Table, Tag, Typography } from 'antd'
import { Activity, AlertTriangle, ArrowRightLeft, Building2, ShieldAlert, Users } from 'lucide-react'

import { agenciesApi } from '@/api/agencies'
import { useApiQuery } from '@/hooks/useApiQuery'

const { Title, Text } = Typography

function scoreColor(value: number) {
  if (value >= 75) return '#059669'
  if (value >= 55) return '#d97706'
  return '#dc2626'
}

export default function AgencyIntelligenceDashboard() {
  const { data, isLoading, error } = useApiQuery(
    ['agency-intelligence-dashboard'],
    () => agenciesApi.getDashboardIntelligence(),
    { retry: false, refetchOnWindowFocus: false, staleTime: 60_000 },
  )

  const intelligence = (data as any)?.intelligence ?? (data as any)?.data?.intelligence

  if (isLoading) {
    return (
      <div className="flex h-[70vh] items-center justify-center">
        <Spin size="large" tip="Loading agency intelligence..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="mx-auto max-w-[1440px] p-8">
        <Alert
          type="error"
          showIcon
          message="Agency Intelligence could not be loaded."
          description={(error as { message?: string })?.message || 'The dashboard endpoint failed.'}
        />
      </div>
    )
  }

  if (!intelligence) {
    return (
      <div className="mx-auto max-w-[1440px] p-8">
        <Empty description="No agency intelligence data available yet" />
      </div>
    )
  }

  const { overview, performance, distribution, risks, comparison, pipeline } = intelligence

  return (
    <div className="mx-auto flex max-w-[1560px] flex-col gap-6 p-8">
      <div className="flex items-end justify-between gap-4">
        <div>
          <Text className="text-[11px] font-black uppercase tracking-[0.24em] text-slate-400">Analytics / Intelligence / Hiring</Text>
          <Title level={2} className="!mb-1 !mt-2">Agency Intelligence</Title>
          <Text className="text-slate-500">Performance scoring, distribution guidance, risk detection, and agency contribution from real tenant data.</Text>
        </div>
        <Tag className="rounded-full border-slate-200 bg-white px-4 py-1 text-[11px] font-semibold uppercase tracking-wider text-slate-700">
          Live Data
        </Tag>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3 xl:grid-cols-6">
        {[
          { label: 'Connected Agencies', value: overview.connected_agencies, icon: <Building2 size={18} className="text-indigo-600" /> },
          { label: 'Active Agencies', value: overview.active_agencies, icon: <Users size={18} className="text-emerald-600" /> },
          { label: 'Agency Submissions', value: overview.agency_submissions, icon: <ArrowRightLeft size={18} className="text-blue-600" /> },
          { label: 'Agency Hires', value: overview.agency_hires, icon: <Activity size={18} className="text-violet-600" /> },
          { label: 'Weak Agencies', value: overview.weak_agencies, icon: <ShieldAlert size={18} className="text-amber-600" /> },
          { label: 'Avg Score', value: overview.average_agency_score, icon: <AlertTriangle size={18} className="text-rose-600" /> },
        ].map((item) => (
          <Card key={item.label} className="rounded-3xl border border-slate-200 shadow-sm">
            <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-50">{item.icon}</div>
            <Statistic
              title={<span className="text-[10px] font-black uppercase tracking-[0.12em] text-slate-400">{item.label}</span>}
              value={item.value}
              valueStyle={{ fontWeight: 900, color: '#0f172a' }}
            />
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1.55fr)_minmax(360px,0.9fr)]">
        <Card
          className="rounded-3xl border border-slate-200 shadow-sm"
          title={<span className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-600">Performance</span>}
        >
          <Table
            rowKey="agency_tenant_id"
            pagination={{ pageSize: 8, hideOnSinglePage: true }}
            dataSource={performance}
            columns={[
              {
                title: 'Agency',
                dataIndex: 'agency_name',
                render: (value: string) => (
                  <div className="flex items-center gap-3">
                    <Avatar className="bg-slate-100 text-slate-700">{value?.charAt(0) || 'A'}</Avatar>
                    <Text strong>{value}</Text>
                  </div>
                ),
              },
              {
                title: 'Tier',
                dataIndex: 'tier',
                render: (value: string) => <Tag>{String(value || 'standard').replace(/_/g, ' ')}</Tag>,
              },
              {
                title: 'Submissions',
                dataIndex: ['metrics', 'total_submissions'],
              },
              {
                title: 'Hire Rate',
                dataIndex: ['metrics', 'hire_rate'],
                render: (value: number) => <Text style={{ color: scoreColor(value) }}>{Number(value || 0).toFixed(1)}%</Text>,
              },
              {
                title: 'Response',
                dataIndex: ['metrics', 'response_time_hours'],
                render: (value: number) => `${Number(value || 0).toFixed(1)}h`,
              },
              {
                title: 'Score',
                dataIndex: 'score',
                render: (value: number) => <Progress percent={Math.round(value || 0)} size="small" strokeColor={scoreColor(Number(value || 0))} showInfo={false} />,
              },
            ]}
          />
        </Card>

        <Card
          className="rounded-3xl border border-slate-200 shadow-sm"
          title={<span className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-600">Distribution</span>}
        >
          <div className="space-y-4">
            <div>
              <Text className="mb-2 block text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Best Agencies</Text>
              <div className="space-y-2">
                {distribution.best_agencies?.length ? distribution.best_agencies.slice(0, 4).map((item: any) => (
                  <div key={item.agency_tenant_id} className="rounded-2xl border border-emerald-100 bg-emerald-50/60 p-3">
                    <div className="flex items-center justify-between gap-4">
                      <Text strong>{item.agency_name}</Text>
                      <Tag color="green">{Number(item.score || 0).toFixed(1)}</Tag>
                    </div>
                    <Text className="text-xs text-slate-500">{item.metrics.total_submissions} submissions, {Number(item.metrics.hire_rate || 0).toFixed(1)}% hire rate</Text>
                  </div>
                )) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No recommendations yet" />}
              </div>
            </div>

            <div>
              <Text className="mb-2 block text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Load Balancing</Text>
              <div className="space-y-2">
                {distribution.load_balancing?.length ? distribution.load_balancing.slice(0, 4).map((item: any) => (
                  <div key={item.agency_tenant_id} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 p-3">
                    <div>
                      <Text strong>{item.agency_name}</Text>
                      <div className="text-xs text-slate-500">{item.active_assignments} active assignments</div>
                    </div>
                    <Tag color={item.load_state === 'balanced' ? 'green' : 'gold'}>{item.load_state}</Tag>
                  </div>
                )) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No load data yet" />}
              </div>
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card
          className="rounded-3xl border border-slate-200 shadow-sm"
          title={<span className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-600">Risks</span>}
        >
          {risks?.length ? (
            <div className="space-y-3">
              {risks.map((item: any) => (
                <div key={item.agency_tenant_id} className="rounded-2xl border border-rose-100 bg-rose-50/60 p-4">
                  <div className="mb-2 flex items-center justify-between gap-4">
                    <Text strong>{item.agency_name}</Text>
                    <Tag color="red">{Number(item.score || 0).toFixed(1)}</Tag>
                  </div>
                  <div className="space-y-1">
                    {item.risks.map((risk: any, index: number) => (
                      <Text key={`${item.agency_tenant_id}-${index}`} className="block text-sm text-slate-600">
                        {risk.message}
                      </Text>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <Empty description="No agency risks detected right now" />
          )}
        </Card>

        <Card
          className="rounded-3xl border border-slate-200 shadow-sm"
          title={<span className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-600">Comparison</span>}
        >
          <Table
            rowKey="agency_tenant_id"
            pagination={false}
            dataSource={comparison}
            columns={[
              { title: 'Agency', dataIndex: 'agency_name' },
              { title: 'Score', dataIndex: 'score', render: (value: number) => Number(value || 0).toFixed(1) },
              { title: 'Gap vs Leader', dataIndex: 'score_gap_vs_leader', render: (value: number) => Number(value || 0).toFixed(1) },
              { title: 'Coverage', dataIndex: 'job_coverage', render: (value: number) => `${Number(value || 0).toFixed(1)}%` },
              { title: 'Success', dataIndex: 'hire_rate', render: (value: number) => `${Number(value || 0).toFixed(1)}%` },
            ]}
          />
        </Card>
      </div>

      <Card
        className="rounded-3xl border border-slate-200 shadow-sm"
        title={<span className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-600">Pipeline Integration</span>}
      >
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
          <Table
            rowKey="agency_tenant_id"
            pagination={false}
            dataSource={pipeline.agency_contribution}
            columns={[
              { title: 'Agency', dataIndex: 'agency_name' },
              { title: 'Submissions', dataIndex: 'submissions' },
              { title: 'Shortlist Rate', dataIndex: 'shortlist_rate', render: (value: number) => `${Number(value || 0).toFixed(1)}%` },
              { title: 'Success Rate', dataIndex: 'success_rate', render: (value: number) => `${Number(value || 0).toFixed(1)}%` },
              { title: 'Score', dataIndex: 'score', render: (value: number) => `${Number(value || 0).toFixed(1)}` },
            ]}
          />
          <div className="space-y-4 rounded-3xl border border-slate-200 bg-slate-50 p-5">
            <div>
              <Text className="block text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Candidate Source Intelligence</Text>
              <Title level={4} className="!mb-1 !mt-2">{Number(pipeline.candidate_source_intelligence.agency_share || 0).toFixed(1)}% agency share</Title>
              <Text className="text-slate-500">Across {pipeline.candidate_source_intelligence.total_candidates} total pipeline candidates.</Text>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4">
              <div className="mb-2 flex items-center justify-between">
                <Text>Agency sourced</Text>
                <Text strong>{Number(pipeline.candidate_source_intelligence.agency_share || 0).toFixed(1)}%</Text>
              </div>
              <Progress percent={Math.round(Number(pipeline.candidate_source_intelligence.agency_share || 0))} strokeColor="#2563eb" showInfo={false} />
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4">
              <div className="mb-2 flex items-center justify-between">
                <Text>Direct sourced</Text>
                <Text strong>{Number(pipeline.candidate_source_intelligence.direct_share || 0).toFixed(1)}%</Text>
              </div>
              <Progress percent={Math.round(Number(pipeline.candidate_source_intelligence.direct_share || 0))} strokeColor="#64748b" showInfo={false} />
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}
