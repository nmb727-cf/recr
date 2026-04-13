import { useEffect, useMemo, useState } from 'react'
import {
  Table, Tag, Button, Typography, Card, Tabs, Spin, Badge,
  Input, Modal, Form, InputNumber, DatePicker, Select, message, Space, Row, Col
} from 'antd'
import {
  Plus, X, RefreshCw, ChevronRight, Mail, Phone, Search, BriefcaseIcon, ChevronLeft
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useQueryClient } from '@tanstack/react-query'
import { agenciesApi } from '@/api/agencies'
import { requisitionsApi } from '@/api/jobs'
import type { AgencyRelationship, AgencyAssignment, AgencyStatus, AgencyTier, JobRequisition } from '@/types'
import { cn } from '@/utils/cn'
import { StandardSplitView } from '@/components/layout/StandardSplitView'
import { formatStatusLabel, getStatusStyle } from '@/utils/status'
import { useAuth } from '@/hooks/useAuth'
import { readKnownAgencies } from '@/utils/companyOnboarding'

const { Title, Text } = Typography

// ─── Constants ────────────────────────────────────────────────────────────────

const TIER_COLOR: Record<AgencyTier, string> = {
  bronze: 'orange',
  silver: 'blue',
  gold: 'gold',
  platinum: 'purple',
}

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

function normalizeAgencyTenantId(value: unknown): string | null {
  if (value === null || value === undefined) return null
  const raw = String(value).trim()
  if (!raw) return null
  if (UUID_RE.test(raw)) return raw
  if (!/^\d+$/.test(raw)) return null
  try {
    const hex = BigInt(raw).toString(16).padStart(32, '0')
    return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
  } catch {
    return null
  }
}

// ─── Modals ──────────────────────────────────────────────────────────────────

function InviteAgencyModal({
  open,
  companyTenantId,
  onClose,
  onSuccess,
}: {
  open: boolean
  companyTenantId?: string
  onClose: () => void
  onSuccess: () => void
}) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const { data: availableData, isLoading: availableLoading, refetch: refetchAvailable } = useApiQuery(
    ['agencies-link-options'],
    () => agenciesApi.listAvailableAgencies(),
    { enabled: open }
  )
  const { data: linkedData, isLoading: linkedLoading, refetch: refetchLinked } = useApiQuery(
    ['agencies-link-options-linked'],
    () => agenciesApi.listRelationships(),
    { enabled: open }
  )
  const [knownAgencies, setKnownAgencies] = useState(() => readKnownAgencies())

  useEffect(() => {
    if (!open) return
    refetchAvailable()
    refetchLinked()
    setKnownAgencies(readKnownAgencies())
  }, [open, refetchAvailable, refetchLinked])

  const availableAgencies = (
    (availableData as any)?.agencies ??
    (availableData as any)?.data?.agencies ??
    []
  ) as any[]
  const linkedAgencies = (
    (linkedData as any)?.relationships ??
    (linkedData as any)?.data?.relationships ??
    []
  ) as any[]

  const agencyOptions = useMemo(
    () => {
      const entries = (
        [
          ...availableAgencies.map((agency: any) => {
            const normalizedId = normalizeAgencyTenantId(agency?.agency_tenant_id)
            if (!normalizedId) return null
            const label = agency?.name || `Agency ${normalizedId.slice(0, 8)}`
            return [normalizedId, { value: normalizedId, label }] as const
          }),
          ...linkedAgencies.map((rel: any) => {
            const normalizedId = normalizeAgencyTenantId(rel?.agency_tenant_id || rel?.agency_id)
            if (!normalizedId) return null
            const label = rel?.agency?.name || rel?.agency_name || `Agency ${normalizedId.slice(0, 8)}`
            return [normalizedId, { value: normalizedId, label }] as const
          }),
          ...knownAgencies
            .map((agency) => {
              const normalizedId = normalizeAgencyTenantId(agency.agency_tenant_id)
              if (!normalizedId) return null
              return [normalizedId, { value: normalizedId, label: agency.name }] as const
            }),
        ]
          .filter(Boolean)
      ) as Array<readonly [string, { value: string; label: string }]>

      return Array.from(new Map(entries).values())
    },
    [availableAgencies, linkedAgencies, knownAgencies]
  )

  const onFinish = async (values: any) => {
    if (!companyTenantId) {
      message.error('Unable to resolve company tenant id')
      return
    }
    const agencyTenantId = normalizeAgencyTenantId(values.agency_tenant_id)
    if (!agencyTenantId) {
      message.error('Selected agency is invalid. Please reselect.')
      return
    }

    setLoading(true)
    try {
      await agenciesApi.createRelationship({
        agency_tenant_id: agencyTenantId,
        company_tenant_id: companyTenantId,
        tier: values.tier || 'standard',
        commission_percentage: values.commission_percentage,
        commission_type: 'percentage',
        notes: values.notes ? String(values.notes).trim() : undefined,
      })
      message.success('Agency relationship created')
      form.resetFields()
      onSuccess()
    } catch (err: any) {
      const errorMsg = err?.response?.data?.message || 'Failed to create relationship'
      const fieldErrors = err?.response?.data?.errors
      if (fieldErrors && typeof fieldErrors === 'object') {
        const formErrors = Object.entries(fieldErrors).map(([name, msgs]: [string, any]) => ({
          name,
          errors: Array.isArray(msgs) ? msgs : [String(msgs)],
        }))
        form.setFields(formErrors)
        const first = Object.values(fieldErrors)[0]
        const firstMsg = Array.isArray(first) ? first[0] : String(first)
        message.error(firstMsg || errorMsg)
      } else {
        message.error(errorMsg)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title={<span className="text-lg font-bold text-slate-900">Link Agency</span>}
      open={open}
      onCancel={onClose}
      onOk={() => form.submit()}
      okText="Link Agency"
      confirmLoading={loading}
      destroyOnClose
    >
      <Form form={form} layout="vertical" onFinish={onFinish} className="mt-4">
        <Form.Item name="agency_tenant_id" label="Select Agency" rules={[{ required: true, message: 'Select an agency' }]}>
          <Select
            showSearch
            optionFilterProp="label"
            placeholder="Choose agency"
            loading={availableLoading || linkedLoading}
            options={agencyOptions}
            notFoundContent={(availableLoading || linkedLoading) ? 'Loading agencies...' : 'No agencies available'}
            className="h-10"
          />
        </Form.Item>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="commission_percentage" label="Commission %" initialValue={15}>
              <InputNumber min={1} max={100} className="w-full h-10 rounded-xl" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="tier" label="Partnership Tier" initialValue="standard">
              <Select className="h-10" options={[
                { value: 'preferred', label: 'Preferred' },
                { value: 'standard', label: 'Standard' },
                { value: 'probation', label: 'Probation' },
                { value: 'blacklisted', label: 'Blacklisted' },
              ]} />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item name="notes" label="Notes (Optional)">
          <Input.TextArea rows={3} placeholder="Context about this partnership..." />
        </Form.Item>
      </Form>
    </Modal>
  )
}

function AssignJobModal({
  open,
  agencyId,
  onClose,
  onSuccess,
}: {
  open: boolean
  agencyId: string
  onClose: () => void
  onSuccess: () => void
}) {
  const [form] = Form.useForm()
  const [submitting, setSubmitting] = useState(false)

  const { data: jobsData, isLoading: jobsLoading } = useApiQuery(
    ['requisitions-active'],
    () => requisitionsApi.list({ status: 'active' }),
    { enabled: open }
  )

  const jobs: JobRequisition[] = (
    (jobsData as any)?.requisitions ??
    (jobsData as any)?.data?.requisitions ??
    []
  ) as JobRequisition[]

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setSubmitting(true)
      await agenciesApi.createAssignment({
        agency_tenant_id: agencyId,
        requisition_id: values.requisition_id,
        max_submissions: values.max_submissions,
        deadline: values.deadline.format('YYYY-MM-DD'),
        notes: values.notes,
      })
      message.success('Job assigned successfully')
      form.resetFields()
      onSuccess()
    } catch (err: any) {
      if (err?.errorFields) return
      message.error(err?.response?.data?.message || 'Failed to assign job')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal
      title={<span className="font-bold text-slate-900">Assign Job to Agency</span>}
      open={open}
      onCancel={onClose}
      onOk={handleSubmit}
      okText="Assign Job"
      confirmLoading={submitting}
      okButtonProps={{ className: 'bg-blue-600 border-none font-bold' }}
      width={520}
      destroyOnClose
    >
      <Form form={form} layout="vertical" className="mt-4">
        <Form.Item name="requisition_id" label="Job Requisition" rules={[{ required: true, message: 'Select a job' }]}>
          <Select
            placeholder="Select active job..."
            loading={jobsLoading}
            showSearch
            options={jobs.map(j => ({ value: j.id, label: j.title }))}
            className="h-10"
          />
        </Form.Item>
        <div className="grid grid-cols-2 gap-4">
          <Form.Item name="max_submissions" label="Max Submissions" rules={[{ required: true }]} initialValue={5}>
            <InputNumber min={1} max={100} className="w-full h-10" />
          </Form.Item>
          <Form.Item name="deadline" label="Deadline" rules={[{ required: true, message: 'Set a deadline' }]}>
            <DatePicker className="w-full h-10" disabledDate={d => d.isBefore(dayjs())} />
          </Form.Item>
        </div>
        <Form.Item name="notes" label="Notes">
          <Input.TextArea rows={3} placeholder="Instructions..." />
        </Form.Item>
      </Form>
    </Modal>
  )
}

// ─── Sub-components ─────────────────────────────────────────────────────────

const FullAgencyList = ({ relationships, onSelect, selectedId, isLoading, assignmentCounts }: any) => {
  const columns: ColumnsType<AgencyRelationship> = [
    {
      title: 'Agency Name',
      key: 'name',
      render: (_, r) => (
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0 font-bold border border-blue-100">
            {r.agency?.name?.charAt(0).toUpperCase()}
          </div>
          <Text className="font-bold text-slate-900">{r.agency?.name || 'N/A'}</Text>
        </div>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (s: AgencyStatus) => (
        <Tag color={getStatusStyle(s, 'agency').antColor} className="m-0 border-none font-bold text-[10px] uppercase rounded-full px-2.5 py-0.5">
          {formatStatusLabel(s)}
        </Tag>
      ),
    },
    {
      title: 'Tier',
      dataIndex: 'tier',
      key: 'tier',
      render: (t: AgencyTier) => (
        <Tag color={TIER_COLOR[t] ?? 'default'} className="m-0 border-none font-bold text-[10px] uppercase rounded-full px-2.5 py-0.5">
          {t}
        </Tag>
      ),
    },
    {
      title: 'Active Jobs',
      key: 'active_jobs',
      render: (_, r) => {
        const agencyKey = (r as any).agency_tenant_id || r.agency_id
        const count = assignmentCounts[agencyKey] ?? 0
        return (
          <div className="flex items-center gap-1.5">
            <BriefcaseIcon className="h-3.5 w-3.5 text-slate-400" />
            <span className="font-bold text-slate-700">{count}</span>
          </div>
        )
      }
    },
    {
      title: 'Comm %',
      dataIndex: 'commission_percentage',
      key: 'commission',
      render: (c) => <span className="font-bold text-slate-700">{c}%</span>,
    },
    {
      title: '',
      key: 'actions',
      width: 50,
      align: 'right',
      render: () => <Button type="text" icon={<ChevronRight className="h-4 w-4 text-slate-300" />} />
    }
  ]

  return (
    <Table<AgencyRelationship>
      columns={columns}
      dataSource={relationships}
      rowKey="id"
      loading={isLoading}
      onRow={(record) => ({
        onClick: () => onSelect(record),
        className: cn(
          "cursor-pointer transition-all duration-200",
          record.id === selectedId ? "bg-blue-50 hover:bg-blue-50" : "hover:bg-slate-50"
        ),
      })}
      pagination={{ pageSize: 15, hideOnSinglePage: true }}
      className="modern-table"
    />
  )
}

const CompressedAgencyList = ({ relationships, onSelect, selectedId }: any) => {
  return (
    <div className="flex flex-col h-full overflow-y-auto bg-white border-r border-slate-200">
      <div className="p-4 border-b border-slate-100 flex items-center justify-between sticky top-0 bg-white z-10">
        <Text className="font-bold text-slate-900">Partners</Text>
        <Badge count={relationships.length} showZero style={{ backgroundColor: '#f1f5f9', color: '#64748b', boxShadow: 'none' }} />
      </div>
      {relationships.map((item: any) => (
        <div
          key={item.id}
          onClick={() => onSelect(item)}
          className={cn(
            "p-4 border-b border-slate-50 cursor-pointer transition-all border-l-4",
            item.id === selectedId
              ? "bg-blue-50/50 border-l-blue-600"
              : "bg-white border-l-transparent hover:bg-slate-50"
          )}
        >
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-slate-100 text-slate-500 flex items-center justify-center shrink-0 font-bold text-xs uppercase">
              {item.agency?.name?.charAt(0)}
            </div>
            <div className="min-w-0">
              <p className="m-0 font-bold text-slate-900 text-sm leading-tight truncate">
                {item.agency?.name}
              </p>
              <Tag color={getStatusStyle(item.status as AgencyStatus, 'agency').antColor} className="mt-1 m-0 border-none font-bold text-[8px] uppercase px-1 rounded">
                {formatStatusLabel(item.status)}
              </Tag>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

const AgencyDetailPanel = ({
  relationship,
  onClose,
  onRefresh,
}: {
  relationship: AgencyRelationship
  onClose: () => void
  onRefresh: () => void
}) => {
  const agencyId = (relationship as any).agency_tenant_id || relationship.agency_id
  const queryClient = useQueryClient()
  const [assignOpen, setAssignOpen] = useState(false)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  const { data: assignmentsData, isLoading: assignmentsLoading, refetch: refetchAssignments } = useApiQuery(
    ['agency-assignments', agencyId],
    () => agenciesApi.listAssignments({ agency_id: agencyId }),
    { enabled: !!agencyId }
  )

  const assignments: AgencyAssignment[] = Array.isArray((assignmentsData as any)?.data?.assignments) ? (assignmentsData as any).data.assignments : []

  const activeAssignments = assignments.filter(a => a.status === 'active').length
  const totalSubmissions = assignments.reduce((sum, a) => sum + (a.submissions_count ?? 0), 0)

  const handleActivate = async () => {
    setActionLoading('activate')
    try {
      if (relationship.status === 'pending') {
        await agenciesApi.accept(relationship.id)
      } else {
        await agenciesApi.updateRelationship(relationship.id, { status: 'active' } as any)
      }
      message.success('Agency activated')
      onRefresh()
      queryClient.invalidateQueries({ queryKey: ['agencies'] })
    } catch (err: any) {
      message.error(err?.response?.data?.message || 'Failed to activate')
    } finally {
      setActionLoading(null)
    }
  }

  const handleDeactivate = async () => {
    setActionLoading('deactivate')
    try {
      await agenciesApi.suspend(relationship.id)
      message.success('Agency suspended')
      onRefresh()
      queryClient.invalidateQueries({ queryKey: ['agencies'] })
    } catch {
      message.error('Failed to suspend')
    } finally {
      setActionLoading(null)
    }
  }

  const tabItems = [
    {
      key: 'overview',
      label: 'Overview',
      children: (
        <div className="p-6">
          <div className="grid grid-cols-3 gap-4 mb-8">
            {[
              { label: 'Commission', value: `${relationship.commission_percentage}%` },
              { label: 'Tier', value: relationship.tier, type: 'tag' },
              { label: 'SLA', value: `${relationship.sla_hours || 48}h` },
              { label: 'Active Jobs', value: activeAssignments },
              { label: 'Total Submissions', value: totalSubmissions },
            ].map((stat, i) => (
              <div key={i} className="bg-slate-50/50 rounded-xl p-4 border border-slate-100">
                <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">{stat.label}</Text>
                {stat.type === 'tag' ? (
                  <Tag color={TIER_COLOR[stat.value as AgencyTier]} className="m-0 font-bold uppercase text-[11px] px-2 rounded-full border-none">{stat.value as string}</Tag>
                ) : (
                  <Text className="block font-bold text-slate-700">{stat.value}</Text>
                )}
              </div>
            ))}
          </div>

          <div className="space-y-6">
            <div>
              <Title level={5} className="!text-xs !font-bold !uppercase !tracking-widest !text-slate-400 !mb-4">Agency Contact</Title>
              <div className="flex items-center gap-4 bg-white border border-slate-100 p-4 rounded-2xl shadow-soft-sm">
                <div className="h-10 w-10 rounded-full bg-slate-100 flex items-center justify-center font-bold text-slate-400 text-sm">
                  {relationship.agency?.name?.charAt(0)}
                </div>
                <div>
                  <Text className="block font-bold text-slate-800">{relationship.agency?.name || 'Agency'}</Text>
                  <div className="flex gap-4 mt-1">
                    <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
                      <Mail className="h-3 w-3" /> {relationship.agency?.contact_email || 'N/A'}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )
    },
    {
      key: 'assignments',
      label: `Jobs (${assignments.length})`,
      children: (
        <div className="p-0">
          {assignmentsLoading ? <div className="p-10 text-center"><Spin /></div> : (
            <Table
              dataSource={assignments}
              rowKey="id"
              size="small"
              pagination={false}
              className="modern-table"
              columns={[
                {
                  title: 'Job Position',
                  dataIndex: 'job_title',
                  render: (t) => <Text className="font-bold text-slate-700">{t || 'Unknown Role'}</Text>
                },
                {
                  title: 'Limit',
                  key: 'limit',
                  render: (_, r) => <Text className="font-medium text-slate-500 text-xs">{r.submissions_count} / {r.max_submissions}</Text>
                },
                {
                  title: 'Status',
                  dataIndex: 'status',
                  render: (s) => (
                    <Tag className="m-0 uppercase font-bold text-[9px] rounded-full px-2" color={getStatusStyle(s, 'agency').antColor}>
                      {formatStatusLabel(s)}
                    </Tag>
                  )
                }
              ]}
            />
          )}
        </div>
      )
    }
  ]

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header - Consistent UX */}
      <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between sticky top-0 bg-white/80 backdrop-blur-md z-20">
        <div className="flex items-center gap-4">
          <Button icon={<ChevronLeft className="h-4 w-4" />} onClick={onClose} className="h-8 w-8 flex items-center justify-center rounded-lg border-slate-200" />
          <div>
            <div className="flex items-center gap-3 mb-0.5">
              <Title level={4} className="!m-0 text-slate-900">{relationship.agency?.name}</Title>
              <Tag color={getStatusStyle(relationship.status as AgencyStatus, 'agency').antColor} className="m-0 border-none font-bold text-[9px] uppercase rounded-full px-2 py-0.5">
                {formatStatusLabel(relationship.status)}
              </Tag>
            </div>
            <Text className="text-slate-400 font-medium text-xs uppercase tracking-wider">
              {relationship.tier} Tier Partner
            </Text>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {relationship.status === 'active' ? (
            <Button danger size="small" className="h-8 font-bold px-3 rounded-lg" onClick={handleDeactivate}>Suspend</Button>
          ) : (
            <Button size="small" className="h-8 font-bold px-3 rounded-lg border-emerald-300 text-emerald-600" onClick={handleActivate}>Activate</Button>
          )}
          <Button type="primary" size="small" icon={<Plus className="h-3 w-3" />} onClick={() => setAssignOpen(true)} className="h-8 font-bold px-3 rounded-lg bg-blue-600 border-none shadow-soft-sm">Assign Job</Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        <Tabs
          defaultActiveKey="overview"
          items={tabItems}
          className="detail-tabs"
          tabBarStyle={{ padding: '0 24px', marginBottom: 0, borderBottom: '1px solid #f1f5f9' }}
        />
      </div>

      <AssignJobModal
        open={assignOpen}
        agencyId={agencyId}
        onClose={() => setAssignOpen(false)}
        onSuccess={() => {
          setAssignOpen(false)
          refetchAssignments()
          onRefresh()
        }}
      />
    </div>
  )
}

// ─── Main Agencies Page ───────────────────────────────────────────────────────

export default function AgenciesList() {
  const { user } = useAuth()
  const [selectedRel, setSelectedRel] = useState<AgencyRelationship | null>(null)
  const [search, setSearch] = useState('')
  const [viewTab, setViewTab] = useState('agencies')
  const [inviteModalOpen, setInviteModalOpen] = useState(false)

  const { data, isLoading, refetch } = useApiQuery(['agencies', search], () => agenciesApi.listRelationships({ search: search || undefined }))
  const relationships = (
    (data as any)?.relationships ??
    (data as any)?.data?.relationships ??
    []
  ) as AgencyRelationship[]
  const { data: availableData } = useApiQuery(['agencies-available-main'], () => agenciesApi.listAvailableAgencies())
  const availableAgencies = (
    (availableData as any)?.agencies ??
    (availableData as any)?.data?.agencies ??
    []
  ) as Array<{ agency_tenant_id?: string; name?: string }>
  const agencyNameByTenantId = useMemo(
    () =>
      Object.fromEntries(
        availableAgencies
          .filter((a) => a?.agency_tenant_id && a?.name)
          .map((a) => [String(a.agency_tenant_id), String(a.name)])
      ) as Record<string, string>,
    [availableAgencies]
  )
  const relationshipsResolved = useMemo(
    () =>
      relationships.map((r: any) => {
        const agencyTenantId = String(r?.agency_tenant_id || r?.agency_id || '')
        const resolvedName =
          r?.agency?.name ||
          r?.agency_name ||
          agencyNameByTenantId[agencyTenantId] ||
          'N/A'
        return {
          ...r,
          agency: {
            ...(r?.agency || {}),
            name: resolvedName,
          },
        }
      }) as AgencyRelationship[],
    [relationships, agencyNameByTenantId]
  )

  const { data: assignmentsData, isLoading: assignmentsLoading } = useApiQuery(['agency_assignments_all'], () => agenciesApi.listAssignments())
  const allAssignments = (
    (assignmentsData as any)?.assignments ??
    (assignmentsData as any)?.data?.assignments ??
    []
  ) as AgencyAssignment[]

  const assignmentCounts = allAssignments.reduce<Record<string, number>>((acc, a) => {
    const key = (a as any).agency_tenant_id || a.agency_id
    if (a.status === 'active' && key) acc[key] = (acc[key] ?? 0) + 1
    return acc
  }, {})

  const filtered = search
    ? relationshipsResolved.filter((r: any) => r.agency?.name?.toLowerCase().includes(search.toLowerCase()))
    : relationshipsResolved

  return (
    <div className="h-[calc(100vh-100px)] flex flex-col -m-6 overflow-hidden">
      {/* Top Header */}
      {!selectedRel && (
        <div className="p-6 pb-4 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 tracking-tight leading-none">Agency Partners</h1>
            <p className="text-slate-500 mt-2 font-medium">Manage external recruiting relationships and job assignments.</p>
          </div>
          <div className="flex items-center gap-2">
            <Input
              prefix={<Search className="h-4 w-4 text-slate-400 mr-1" />}
              placeholder="Search agencies..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              allowClear
              className="h-10 w-56 rounded-xl border-slate-200"
            />
            <Button
              icon={<RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />}
              onClick={() => refetch()}
              className="h-10 rounded-xl font-bold border-slate-200"
            />
            <Button
              type="primary"
              icon={<Plus className="h-4 w-4" />}
              className="h-10 rounded-xl font-bold bg-blue-600 border-none shadow-soft-md px-6"
              onClick={() => setInviteModalOpen(true)}
            >
              Link Agency
            </Button>
          </div>
        </div>
      )}

      <StandardSplitView
        isDetailOpen={!!selectedRel}
        compactListContent={
          <CompressedAgencyList
            relationships={relationshipsResolved}
            selectedId={selectedRel?.id}
            onSelect={setSelectedRel}
          />
        }
        fullListContent={
          <div className="p-6 pt-0 h-full overflow-y-auto">
            <Tabs
              activeKey={viewTab}
              onChange={setViewTab}
              className="modern-tabs mb-6"
              items={[
                {
                  key: 'agencies',
                  label: 'Agency Partners',
                  children: (
                    <Card bordered={false} className="shadow-soft-sm overflow-hidden p-0 border border-slate-100">
                      <FullAgencyList
                        relationships={filtered}
                        onSelect={setSelectedRel}
                        selectedId={selectedRel?.id}
                        isLoading={isLoading}
                        assignmentCounts={assignmentCounts}
                      />
                    </Card>
                  ),
                },
                {
                  key: 'assignments',
                  label: 'All Assignments',
                  children: (
                    <Card bordered={false} className="shadow-soft-sm overflow-hidden p-0 border border-slate-100">
                      <Table
                        dataSource={allAssignments}
                        loading={assignmentsLoading}
                        rowKey="id"
                        pagination={{ pageSize: 15 }}
                        className="modern-table"
                        columns={[
                          { title: 'Job Role', dataIndex: 'job_title', key: 'job', render: (t) => <Text className="font-bold text-slate-900">{t}</Text> },
                          { title: 'Agency', dataIndex: 'agency_name', key: 'agency', render: (t) => <Text className="font-medium text-slate-600">{t}</Text> },
                          { title: 'Submissions', key: 'usage', render: (_, r) => <Text className="font-bold text-slate-400 text-xs uppercase">{r.submissions_count} / {r.max_submissions}</Text> },
                          { title: 'Deadline', dataIndex: 'deadline', render: (d) => <Text className="text-slate-400 text-[11px] font-bold uppercase">{dayjs(d).format('MMM D, YYYY')}</Text> },
                          {
                            title: 'Status',
                            dataIndex: 'status',
                            render: (s) => (
                              <Tag className="m-0 border-none rounded-full font-bold text-[10px] uppercase" color={getStatusStyle(s, 'agency').antColor}>
                                {formatStatusLabel(s)}
                              </Tag>
                            ),
                          }
                        ]}
                      />
                    </Card>
                  ),
                },
              ]}
            />
          </div>
        }
        detailContent={
          selectedRel ? (
            <AgencyDetailPanel
              relationship={selectedRel}
              onClose={() => setSelectedRel(null)}
              onRefresh={() => refetch()}
            />
          ) : null
        }
      />

      <InviteAgencyModal
        open={inviteModalOpen}
        companyTenantId={user?.tenant_id}
        onClose={() => setInviteModalOpen(false)}
        onSuccess={() => {
          setInviteModalOpen(false)
          refetch()
        }}
      />
    </div>
  )
}
