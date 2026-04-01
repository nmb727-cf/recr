import {
  Card, Row, Col, Statistic, Tabs, Typography, Spin, Empty, DatePicker, Select, Button, Space,
} from 'antd'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, AreaChart, Area, FunnelChart, Funnel, LabelList,
} from 'recharts'
import {
  FileTextOutlined, TeamOutlined, ApartmentOutlined, CalendarOutlined,
} from '@ant-design/icons'
import { useApiQuery } from '@/hooks/useApiQuery'
import { analyticsApi } from '@/api/analytics'
import { useState } from 'react'
import dayjs from 'dayjs'

const { Title, Text } = Typography

const COLORS = ['#1890ff', '#2f54eb', '#722ed1', '#eb2f96', '#fa541c', '#faad14', '#52c41a', '#13c2c2']
const PIE_COLORS = ['#1890ff', '#52c41a', '#faad14', '#ff4d4f', '#722ed1', '#13c2c2']

// ─── Overview Tab ─────────────────────────────────────────────────────────────

function OverviewTab() {
  const { data, isLoading } = useApiQuery(['analytics', 'dashboard'], () => analyticsApi.dashboard())
  const d = data as {
    jobs?: { total: number; active: number; this_month: number }
    candidates?: { total: number; new_this_month: number }
    applications?: { total: number; by_status: { status: string; count: number }[] }
    interviews?: { scheduled: number; completed: number }
  } | undefined

  if (isLoading) return <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>
  if (!d) return <Empty />

  const stats = [
    { title: 'Total Jobs', value: d.jobs?.total ?? 0, icon: <FileTextOutlined />, color: '#1890ff' },
    { title: 'Total Candidates', value: d.candidates?.total ?? 0, icon: <TeamOutlined />, color: '#52c41a' },
    { title: 'Total Applications', value: d.applications?.total ?? 0, icon: <ApartmentOutlined />, color: '#faad14' },
    { title: 'Scheduled Interviews', value: d.interviews?.scheduled ?? 0, icon: <CalendarOutlined />, color: '#722ed1' },
  ]

  // Transform applications by_status for the chart: {status, count} → {name, value}
  const appsByStatus = (d.applications?.by_status ?? []).map((s) => ({
    name: s.status.replace(/_/g, ' '),
    value: s.count,
  }))

  return (
    <div>
      <Row gutter={16}>
        {stats.map((s, i) => (
          <Col xs={24} sm={12} lg={6} key={i}>
            <Card bordered={false} style={{ borderRadius: 12, marginBottom: 16 }}>
              <Statistic
                title={<span style={{ color: '#8c8c8c' }}>{s.title}</span>}
                value={s.value}
                prefix={s.icon}
                valueStyle={{ color: s.color, fontWeight: 700 }}
              />
            </Card>
          </Col>
        ))}
      </Row>

      {appsByStatus.length > 0 && (
        <Card title="Applications by Status" bordered={false} style={{ borderRadius: 12, marginTop: 8 }}>
          <div style={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={appsByStatus}>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#1890ff" stopOpacity={0.1} />
                    <stop offset="95%" stopColor="#1890ff" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12 }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Area type="monotone" dataKey="value" stroke="#1890ff" fillOpacity={1} fill="url(#colorValue)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}
    </div>
  )
}

// ─── Recruitment Tab ──────────────────────────────────────────────────────────

function RecruitmentTab() {
  const { data, isLoading } = useApiQuery(['analytics', 'recruitment'], () => analyticsApi.recruitment())
  const d = data as {
    funnel?: {
      total_applications: number
      shortlisted: number
      interviewed: number
      offered: number
      joined: number
      rejected: number
      shortlist_rate: number
      offer_rate: number
      join_rate: number
    }
    by_source?: { source: string; count: number }[]
  } | undefined

  if (isLoading) return <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>
  if (!d) return <Empty />

  // Transform funnel object → array for Recharts FunnelChart
  const funnelData = d.funnel
    ? [
        { name: 'Applications', value: d.funnel.total_applications },
        { name: 'Shortlisted', value: d.funnel.shortlisted },
        { name: 'Interviewed', value: d.funnel.interviewed },
        { name: 'Offered', value: d.funnel.offered },
        { name: 'Joined', value: d.funnel.joined },
      ].filter((item) => item.value >= 0)
    : []

  // Transform by_source: {source, count} → {name, value}
  const sourceData = (d.by_source ?? []).map((s) => ({
    name: s.source || 'Unknown',
    value: s.count,
  }))

  const funnel = d.funnel

  return (
    <div>
      {/* Funnel KPI row */}
      {funnel && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          {[
            { label: 'Total Applications', value: funnel.total_applications },
            { label: 'Shortlist Rate', value: `${funnel.shortlist_rate}%` },
            { label: 'Offer Rate', value: `${funnel.offer_rate}%` },
            { label: 'Join Rate', value: `${funnel.join_rate}%` },
          ].map((kpi, i) => (
            <Col xs={12} sm={6} key={i}>
              <Card bordered={false} style={{ borderRadius: 12, textAlign: 'center' }}>
                <div style={{ fontSize: 24, fontWeight: 700, color: COLORS[i] }}>{kpi.value}</div>
                <div style={{ fontSize: 12, color: '#8c8c8c', marginTop: 4 }}>{kpi.label}</div>
              </Card>
            </Col>
          ))}
        </Row>
      )}

      <Row gutter={16}>
        {/* Funnel chart */}
        <Col xs={24} lg={funnelData.length > 0 ? 14 : 24}>
          <Card title="Recruitment Funnel" bordered={false} style={{ borderRadius: 12 }}>
            {funnelData.length === 0 ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No application data yet" style={{ padding: '40px 0' }} />
            ) : (
              <div style={{ height: 360, display: 'flex', justifyContent: 'center' }}>
                <ResponsiveContainer width="90%" height="100%">
                  <FunnelChart>
                    <Tooltip formatter={(value) => [value, 'Count']} />
                    <Funnel dataKey="value" data={funnelData} isAnimationActive>
                      <LabelList position="right" fill="#595959" stroke="none" dataKey="name" style={{ fontSize: 13 }} />
                      {funnelData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Funnel>
                  </FunnelChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>
        </Col>

        {/* Source breakdown */}
        {sourceData.length > 0 && (
          <Col xs={24} lg={10}>
            <Card title="Applications by Source" bordered={false} style={{ borderRadius: 12 }}>
              <div style={{ height: 360 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={sourceData}
                      innerRadius={65}
                      outerRadius={95}
                      paddingAngle={4}
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                      labelLine={false}
                    >
                      {sourceData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </Col>
        )}
      </Row>
    </div>
  )
}

// ─── Pipeline Tab ─────────────────────────────────────────────────────────────

function PipelineTab() {
  const { data, isLoading } = useApiQuery(['analytics', 'pipeline'], () => analyticsApi.pipeline())
  const d = data as {
    by_status?: { status: string; count: number }[]
    top_jobs_by_applications?: { requisition_id: string; count: number }[]
    stale_applications?: number
  } | undefined

  if (isLoading) return <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>
  if (!d) return <Empty />

  // Transform {status, count} → {name, value}
  const byStatus = (d.by_status ?? []).map((s) => ({
    name: s.status.replace(/_/g, ' '),
    value: s.count,
  }))

  return (
    <div>
      {d.stale_applications !== undefined && (
        <Card bordered={false} style={{ borderRadius: 12, marginBottom: 16 }}>
          <Statistic
            title={<span style={{ color: '#8c8c8c' }}>Stale Applications (&gt;7 days inactive)</span>}
            value={d.stale_applications}
            valueStyle={{ color: '#faad14', fontWeight: 700 }}
          />
        </Card>
      )}

      <Card title="Applications by Status" bordered={false} style={{ borderRadius: 12 }}>
        {byStatus.length === 0 ? (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No pipeline data yet" style={{ padding: '40px 0' }} />
        ) : (
          <div style={{ height: 360 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={byStatus} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" horizontal={false} vertical={true} />
                <XAxis type="number" axisLine={false} tickLine={false} tick={{ fontSize: 12 }} />
                <YAxis
                  dataKey="name"
                  type="category"
                  axisLine={false}
                  tickLine={false}
                  width={160}
                  tick={{ fontSize: 12 }}
                />
                <Tooltip />
                <Bar dataKey="value" fill="#1890ff" radius={[0, 4, 4, 0]} barSize={28}>
                  {byStatus.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </Card>
    </div>
  )
}

// ─── Interviews Tab ───────────────────────────────────────────────────────────

function InterviewsTab() {
  const { data, isLoading } = useApiQuery(['analytics', 'interviews'], () => analyticsApi.interviews())
  const d = data as {
    by_status?: { status: string; count: number }[]
    by_type?: { interview_type: string; count: number }[]
    average_score?: number | null
  } | undefined

  if (isLoading) return <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>
  if (!d) return <Empty />

  // Transform {status, count} → {name, value}
  const byStatus = (d.by_status ?? []).map((s) => ({
    name: s.status.replace(/_/g, ' '),
    value: s.count,
  }))

  // Transform {interview_type, count} → {name, value}
  const byType = (d.by_type ?? []).map((s) => ({
    name: s.interview_type.replace(/_/g, ' '),
    value: s.count,
  }))

  return (
    <div>
      {d.average_score != null && (
        <Card bordered={false} style={{ borderRadius: 12, marginBottom: 16 }}>
          <Statistic
            title={<span style={{ color: '#8c8c8c' }}>Average Interview Score</span>}
            value={d.average_score}
            precision={1}
            suffix="/ 10"
            valueStyle={{ color: '#52c41a', fontWeight: 700 }}
          />
        </Card>
      )}

      <Row gutter={16}>
        <Col xs={24} lg={12}>
          <Card title="By Interview Type" bordered={false} style={{ borderRadius: 12 }}>
            {byType.length === 0 ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No interview data yet" style={{ padding: '40px 0' }} />
            ) : (
              <div style={{ height: 320 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={byType} outerRadius={100} dataKey="value" label={({ name }) => name} labelLine>
                      {byType.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="By Status" bordered={false} style={{ borderRadius: 12 }}>
            {byStatus.length === 0 ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No interview data yet" style={{ padding: '40px 0' }} />
            ) : (
              <div style={{ height: 320 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={byStatus}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12 }} />
                    <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="value" fill="#52c41a" radius={[4, 4, 0, 0]} barSize={36}>
                      {byStatus.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}

function InterviewIntelligenceTab() {
  const [range, setRange] = useState<any>(null)
  const [typeFilter, setTypeFilter] = useState<string | undefined>(undefined)
  const params = {
    start_date: range?.[0] ? dayjs(range[0]).format('YYYY-MM-DD') : undefined,
    end_date: range?.[1] ? dayjs(range[1]).format('YYYY-MM-DD') : undefined,
    interview_type: typeFilter,
  }

  const { data, isLoading, refetch } = useApiQuery(
    ['analytics', 'interviews', 'intelligence', params.start_date, params.end_date, params.interview_type],
    () => analyticsApi.interviewIntelligence(params),
  )
  const d = data as any

  if (isLoading) return <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>
  if (!d) return <Empty />

  const funnelData = [
    { name: 'Applied', value: d.funnel?.applied || 0 },
    { name: 'Prequalified', value: d.funnel?.prequalified || 0 },
    { name: 'Interviewed', value: d.funnel?.interviewed || 0 },
    { name: 'Shortlisted', value: d.funnel?.shortlisted || 0 },
    { name: 'Offer', value: d.funnel?.offer || 0 },
    { name: 'Hired', value: d.funnel?.hired || 0 },
  ]

  const conversionData = [
    { name: 'Applied→Prequalified', value: d.conversion?.applied_to_prequalified || 0 },
    { name: 'Prequalified→Interviewed', value: d.conversion?.prequalified_to_interviewed || 0 },
    { name: 'Interviewed→Shortlisted', value: d.conversion?.interviewed_to_shortlisted || 0 },
    { name: 'Shortlisted→Offer', value: d.conversion?.shortlisted_to_offer || 0 },
    { name: 'Offer→Hired', value: d.conversion?.offer_to_hired || 0 },
  ]

  const interviewerData = d.interviewer_analytics || []
  const typeData = d.interview_type_analytics || []
  const dropOffData = [
    { name: 'No Show', value: d.candidate_drop_off?.no_show || 0 },
    { name: 'Incomplete', value: d.candidate_drop_off?.incomplete_interview || 0 },
    { name: 'Rejected', value: d.candidate_drop_off?.rejected_after_stage || 0 },
  ]

  return (
    <div>
      <Card bordered={false} style={{ borderRadius: 12, marginBottom: 16 }}>
        <Space wrap>
          <DatePicker.RangePicker value={range} onChange={setRange} />
          <Select
            allowClear
            placeholder="Interview type"
            style={{ width: 220 }}
            value={typeFilter}
            onChange={setTypeFilter}
            options={(typeData || []).map((r: any) => ({ value: r.interview_type, label: r.interview_type }))}
          />
          <Button onClick={() => refetch()}>Apply Filters</Button>
        </Space>
      </Card>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={8}><Card bordered={false}><Statistic title="Interview Success Rate" value={d.conversion?.interview_success_rate || 0} suffix="%" /></Card></Col>
        <Col xs={12} sm={8}><Card bordered={false}><Statistic title="Rejection Rate" value={d.conversion?.rejection_rate || 0} suffix="%" /></Card></Col>
        <Col xs={24} sm={8}><Card bordered={false}><Statistic title="Avg Time to Interview (hrs)" value={d.time_analytics?.time_to_interview_hours || 0} /></Card></Col>
      </Row>

      <Row gutter={16}>
        <Col xs={24} lg={12}>
          <Card title="Interview Funnel" bordered={false} style={{ borderRadius: 12, marginBottom: 16 }}>
            <div style={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={funnelData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#1890ff" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Stage Conversion %" bordered={false} style={{ borderRadius: 12, marginBottom: 16 }}>
            <div style={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={conversionData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Area dataKey="value" stroke="#52c41a" fill="#b7eb8f" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col xs={24} lg={12}>
          <Card title="Interviewer Performance" bordered={false} style={{ borderRadius: 12, marginBottom: 16 }}>
            <div style={{ height: 320 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={interviewerData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="interviewer_id" tickFormatter={(v) => String(v).slice(0, 6)} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="pass_rate" fill="#52c41a" />
                  <Bar dataKey="reject_rate" fill="#ff4d4f" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Interview Type Success" bordered={false} style={{ borderRadius: 12, marginBottom: 16 }}>
            <div style={{ height: 320 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={typeData} dataKey="success_rate" nameKey="interview_type" outerRadius={110} label>
                    {typeData.map((_: any, index: number) => (
                      <Cell key={`type-cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>
      </Row>

      <Card title="Candidate Drop-Off" bordered={false} style={{ borderRadius: 12 }}>
        <div style={{ height: 260 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={dropOffData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#faad14" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  )
}

// ─── Main Analytics Page ──────────────────────────────────────────────────────

export default function Analytics() {
  return (
    <div>
      <Row align="middle" style={{ marginBottom: 20 }}>
        <Col>
          <Title level={4} style={{ margin: 0 }}>Analytics Dashboard</Title>
          <Text type="secondary" style={{ fontSize: 13 }}>Recruitment performance overview</Text>
        </Col>
      </Row>

      <Tabs
        defaultActiveKey="overview"
        items={[
          { key: 'overview', label: 'Overview', children: <OverviewTab /> },
          { key: 'recruitment', label: 'Recruitment', children: <RecruitmentTab /> },
          { key: 'pipeline', label: 'Pipeline', children: <PipelineTab /> },
          { key: 'interviews', label: 'Interviews', children: <InterviewsTab /> },
          { key: 'interview-intelligence', label: 'Interview Intelligence', children: <InterviewIntelligenceTab /> },
        ]}
      />
    </div>
  )
}
