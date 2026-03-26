import { useState } from 'react'
import {
  Table, Button, Typography, Tag, Space, Drawer, Form,
  Input, InputNumber, Select, message, Card, Divider, Checkbox, DatePicker, Upload, Collapse
} from 'antd'
import { 
  PlusOutlined, 
  StopOutlined, 
  CheckCircleOutlined, 
  EyeOutlined, 
  InboxOutlined,
  UploadOutlined,
  FileTextOutlined,
  CheckCircleFilled,
  BellOutlined,
  CheckOutlined,
  CloseOutlined,
  ClockCircleOutlined,
  InfoCircleOutlined,
  EditOutlined
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useQueryClient } from '@tanstack/react-query'
import { agenciesApi } from '@/api/agencies'
import { StandardSplitView } from '@/components/layout/StandardSplitView'
import { cn } from '@/utils/cn'
import PaymentTermsField from '@/components/agencies/PaymentTermsField'
import PhoneInput, { formatPhoneDisplay, getPhoneValidationRule, PhoneValue } from '@/components/common/PhoneInput'

const { Title, Text } = Typography
const { Option } = Select

interface AgencyRelationship {
  id: string
  agency_tenant_id: string | null
  company_tenant_id: string
  agency_name: string
  company_name: string
  status: 'pending' | 'active' | 'suspended' | 'terminated'
  commission_percentage: number | null
  commission_type: 'percentage' | 'fixed' | 'milestone'
  created_at: string
  contract_start_date?: string
  contract_end_date?: string
  sla_submission_hours?: number
  sla_feedback_hours?: number
  notes?: string
  contact_person_name?: string
  contact_email?: string
  contact_phone?: string
  contact_country_code?: string
  contact_phone_number?: string
  industry?: string
  contract_file_url?: string
  recruitment_policy_url?: string
  payment_terms?: string[]
  payment_schedule?: Array<{
    trigger: 'on_joining' | 'days_after_joining'
    days?: number
    percentage: number
  }>
  invited_by?: 'company' | 'agency'
  invited_via?: string
  connection_type?: 'full_full' | 'agency_guest' | 'client_guest' | 'email_tracking' | 'offline'
  guest_portal_id?: string
  their_ats_url?: string
  last_activity_at?: string
  // guest portal invite tracking (returned from API when connection_type=agency_guest)
  invite_status?: 'pending' | 'active' | 'expired'
  portal_url?: string
  // Candidate Retention Fields
  retention_enabled?: boolean
  retention_days?: number
  retention_start_type?: 'submission_date' | 'rejection_date' | 'last_activity'
  retention_scope?: 'job_only' | 'view_only' | 'limited_access'
  retention_post_expiry?: 'shared' | 'company_use' | 'consent_required'
  replacement_guarantee_enabled?: boolean
  guarantee_period_days?: number
  guarantee_start_type?: 'joining_date' | 'offer_acceptance_date' | 'first_working_day'
  guarantee_resolution_type?: 'replacement_only' | 'refund_only' | 'replacement_or_refund' | 'no_guarantee'
  refund_mode?: 'full_refund' | 'partial_refund' | 'pro_rated_refund' | ''
  refund_percentage?: number | null
  replacement_attempt_limit?: '1' | '2' | 'unlimited'
  guarantee_notes?: string
}

function getAgencyDisplayName(r: AgencyRelationship): string {
  if (!r.agency_tenant_id || r.agency_name === 'Unknown Agency' || !r.agency_name) {
    if (r.contact_person_name) return r.contact_person_name
    if (r.contact_email) return r.contact_email.split('@')[0]
    return 'Unnamed Agency'
  }
  return r.agency_name
}

function getConnectionBadge(r: AgencyRelationship) {
  const type = r.connection_type || 'full_full'
  if (type === 'agency_guest') {
    if (r.status === 'active') return { color: 'blue', label: 'Portal Active' }
    if (r.status === 'pending') return { color: 'gold', label: 'Invite Pending' }
    return { color: 'red', label: 'Invite Expired' }
  }
  if (r.status === 'active') return { color: 'green', label: 'Connected' }
  if (r.status === 'pending') return { color: 'gold', label: 'Pending' }
  if (r.status === 'suspended') return { color: 'orange', label: 'Suspended' }
  return { color: 'default', label: r.status }
}

const INDUSTRY_OPTIONS = [
  'Technology', 'Finance', 'Healthcare', 'Manufacturing',
  'Retail', 'Education', 'Consulting', 'Real Estate', 'Other'
]
const GUARANTEE_PERIOD_OPTIONS = [
  { value: 15, label: '15 Days' },
  { value: 30, label: '30 Days' },
  { value: 45, label: '45 Days' },
  { value: 60, label: '60 Days' },
  { value: 90, label: '90 Days' },
  { value: 'custom', label: 'Custom' },
]

function resolveGuaranteeDays(values: any): number {
  if (values.guarantee_period_days === 'custom') {
    return Number(values.guarantee_custom_days || 0)
  }
  return Number(values.guarantee_period_days || 0)
}

export default function CompanyAgencies() {
  const queryClient = useQueryClient()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [inviteDrawerOpen, setInviteDrawerOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchLoading, setSearchLoading] = useState(false)
  const [foundTenant, setFoundTenant] = useState<any>(null)
  const [form] = Form.useForm()

  const [editDrawerOpen, setEditDrawerOpen] = useState(false)
  const [editingRelationship, setEditingRelationship] = useState<AgencyRelationship | null>(null)
  const [editForm] = Form.useForm()
  const [editSubmitting, setEditSubmitting] = useState(false)

  const { data, isLoading } = useApiQuery(
    ['agency-relationships'],
    () => agenciesApi.listRelationships()
  )

  const relationshipsData = (
    (data as any)?.relationships ??
    (data as any)?.data?.relationships ??
    []
  )
  const relationships = (Array.isArray(relationshipsData) ? relationshipsData : []) as AgencyRelationship[]

  const pendingFromAgency = relationships.filter(
    r => r.status === 'pending' && r.invited_by === 'agency'
  )

  const pendingSentByUs = relationships.filter(
    r => r.status === 'pending' && r.invited_by === 'company'
  )

  const activeRelationships = relationships.filter(
    r => r.status === 'active' || r.status === 'suspended'
  )

  const selectedRelationship = relationships.find(r => r.id === selectedId)

  const handleEdit = (rel: AgencyRelationship) => {
    setEditingRelationship(rel)
    editForm.setFieldsValue({
      contact_person_name: rel.contact_person_name || '',
      contact_email: rel.contact_email || '',
      contact_phone_field: {
        country_code: rel.contact_country_code || 'IN',
        phone_number: rel.contact_phone_number || rel.contact_phone || '',
      } as PhoneValue,
      industry: rel.industry || undefined,
      commission_percentage: rel.commission_percentage ?? 10,
      commission_type: rel.commission_type || 'percentage',
      payment_terms_field: {
        terms: rel.payment_terms || [],
        schedule: rel.payment_schedule || [],
      },
      sla_submission_hours: rel.sla_submission_hours || 48,
      sla_feedback_hours: rel.sla_feedback_hours || 72,
      contract_start_date: rel.contract_start_date ? dayjs(rel.contract_start_date) : null,
      contract_end_date: rel.contract_end_date ? dayjs(rel.contract_end_date) : null,
      notes: rel.notes || '',
      // Retention
      retention_enabled: rel.retention_enabled || false,
      retention_days: rel.retention_days || 90,
      retention_start_type: rel.retention_start_type || 'submission_date',
      retention_scope: rel.retention_scope || 'job_only',
      retention_post_expiry: rel.retention_post_expiry || 'shared',
      replacement_guarantee_enabled: rel.replacement_guarantee_enabled || false,
      guarantee_period_days: [15, 30, 45, 60, 90].includes(Number(rel.guarantee_period_days))
        ? Number(rel.guarantee_period_days)
        : 'custom',
      guarantee_custom_days: [15, 30, 45, 60, 90].includes(Number(rel.guarantee_period_days))
        ? undefined
        : rel.guarantee_period_days || 30,
      guarantee_start_type: rel.guarantee_start_type || 'joining_date',
      guarantee_resolution_type: rel.guarantee_resolution_type || 'replacement_only',
      refund_mode: rel.refund_mode || '',
      refund_percentage: rel.refund_percentage ?? null,
      replacement_attempt_limit: rel.replacement_attempt_limit || '1',
      guarantee_notes: rel.guarantee_notes || '',
    })
    setEditDrawerOpen(true)
  }

  const handleEditSubmit = async (values: any) => {
    if (!editingRelationship) return
    try {
      setEditSubmitting(true)
      await agenciesApi.updateRelationship(editingRelationship.id, {
        contact_person_name: values.contact_person_name,
        contact_email: values.contact_email,
        contact_phone: values.contact_phone_field
          ? `${values.contact_phone_field.country_code}:${values.contact_phone_field.phone_number}`
          : '',
        contact_country_code: values.contact_phone_field?.country_code || 'IN',
        contact_phone_number: values.contact_phone_field?.phone_number || '',
        industry: values.industry,
        commission_percentage: values.commission_percentage,
        commission_type: values.commission_type,
        payment_terms: values.payment_terms_field?.terms || [],
        payment_schedule: values.payment_terms_field?.schedule || [],
        sla_submission_hours: values.sla_submission_hours,
        sla_feedback_hours: values.sla_feedback_hours,
        contract_start_date: values.contract_start_date?.format('YYYY-MM-DD') || null,
        contract_end_date: values.contract_end_date?.format('YYYY-MM-DD') || null,
        notes: values.notes,
        // Retention
        retention_enabled: values.retention_enabled,
        retention_days: values.retention_days,
        retention_start_type: values.retention_start_type,
        retention_scope: values.retention_scope,
        retention_post_expiry: values.retention_post_expiry,
        replacement_guarantee_enabled: values.replacement_guarantee_enabled,
        guarantee_period_days: resolveGuaranteeDays(values),
        guarantee_start_type: values.guarantee_start_type,
        guarantee_resolution_type: values.guarantee_resolution_type,
        refund_mode: values.refund_mode,
        refund_percentage: values.refund_percentage,
        replacement_attempt_limit: values.replacement_attempt_limit,
        guarantee_notes: values.guarantee_notes,
      })
      message.success('Agency details updated')
      setEditDrawerOpen(false)
      setEditingRelationship(null)
      editForm.resetFields()
      queryClient.invalidateQueries({ queryKey: ['agency-relationships'] })
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to update')
    } finally {
      setEditSubmitting(false)
    }
  }

  const handleAccept = async (id: string) => {
    try {
      await agenciesApi.acceptRelationship(id)
      message.success('Agency accepted successfully')
      queryClient.invalidateQueries({ queryKey: ['agency-relationships'] })
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to accept')
    }
  }

  const handleDecline = async (id: string) => {
    try {
      await agenciesApi.suspendRelationship(id)
      message.success('Invitation declined')
      queryClient.invalidateQueries({ queryKey: ['agency-relationships'] })
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to decline')
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      message.warning('Enter an email address')
      return
    }
    setSearchLoading(true)
    setFoundTenant(null)
    try {
      const res = await agenciesApi.lookup(searchQuery)
      const result = res.data.data
      setFoundTenant(result)
      form.setFieldsValue({ 
        contact_email: result.email || searchQuery,
        industry: result.industry || undefined 
      })
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Search failed')
    } finally {
      setSearchLoading(false)
    }
  }

  const handleSubmit = async (values: any) => {
    if (!foundTenant) return
    try {
      setSubmitting(true)
      const commonPayload = {
        contact_person_name: values.contact_person_name || '',
        contact_email: values.contact_email || foundTenant.email || searchQuery,
        contact_phone: values.contact_phone_field
          ? `${values.contact_phone_field.country_code}:${values.contact_phone_field.phone_number}`
          : '',
        contact_country_code: values.contact_phone_field?.country_code || 'IN',
        contact_phone_number: values.contact_phone_field?.phone_number || '',
        industry: values.industry || '',
        commission_percentage: values.commission_percentage,
        commission_type: values.commission_type || 'percentage',
        payment_terms: values.payment_terms_field?.terms || [],
        payment_schedule: values.payment_terms_field?.schedule || [],
        sla_submission_hours: values.sla_submission_hours || 48,
        sla_feedback_hours: values.sla_feedback_hours || 72,
        contract_start_date: values.contract_start_date?.format('YYYY-MM-DD') || null,
        contract_end_date: values.contract_end_date?.format('YYYY-MM-DD') || null,
        notes: values.notes || '',
        // Retention
        retention_enabled: values.retention_enabled,
        retention_days: values.retention_days,
        retention_start_type: values.retention_start_type,
        retention_scope: values.retention_scope,
        retention_post_expiry: values.retention_post_expiry,
        replacement_guarantee_enabled: values.replacement_guarantee_enabled,
        guarantee_period_days: resolveGuaranteeDays(values),
        guarantee_start_type: values.guarantee_start_type,
        guarantee_resolution_type: values.guarantee_resolution_type,
        refund_mode: values.refund_mode,
        refund_percentage: values.refund_percentage,
        replacement_attempt_limit: values.replacement_attempt_limit,
        guarantee_notes: values.guarantee_notes,
      }

      if (foundTenant.found) {
        await agenciesApi.createRelationship({
          agency_tenant_id: foundTenant.tenant_id,
          ...commonPayload
        })
      } else {
        await agenciesApi.createGuestPortal({
          portal_type: 'agency_guest',
          name: values.agency_name,
          invite_message: values.invite_message || '',
          ...commonPayload
        })
      }
      message.success(`Relationship created`)
      setInviteDrawerOpen(false)
      setFoundTenant(null)
      setSearchQuery('')
      form.resetFields()
      queryClient.invalidateQueries({ queryKey: ['agency-relationships'] })
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to send invitation')
    } finally {
      setSubmitting(false)
    }
  }

  const handleStatusChange = async (id: string, action: 'suspend' | 'reactivate') => {
    try {
      if (action === 'suspend') {
        await agenciesApi.suspendRelationship(id)
      } else {
        await agenciesApi.reactivateRelationship(id)
      }
      message.success(`Relationship updated`)
      queryClient.invalidateQueries({ queryKey: ['agency-relationships'] })
    } catch (err) {
      message.error(`Failed to update relationship`)
    }
  }

  const columns: ColumnsType<AgencyRelationship> = [
    {
      title: 'Agency',
      key: 'agency',
      render: (_, record) => {
        const name = getAgencyDisplayName(record)
        return (
          <div>
            <div className="font-semibold text-[#111827] text-[14px]">{name}</div>
            <div className="text-[12px] text-slate-400 mt-0.5">
              {record.contact_email || '—'}
            </div>
          </div>
        )
      },
    },
    {
      title: 'Connection',
      key: 'connection',
      render: (_, record) => {
        const badge = getConnectionBadge(record)
        return <Tag color={badge.color}>{badge.label}</Tag>
      },
    },
    {
      title: 'Contact',
      key: 'contact',
      render: (_, record) => (
        <div>
          <div className="text-[13px] text-slate-600">{record.contact_person_name || '—'}</div>
          <div className="text-[12px] text-slate-400">
            {record.contact_phone_number
              ? formatPhoneDisplay(record.contact_country_code || 'IN', record.contact_phone_number)
              : record.contact_phone || '—'}
          </div>
        </div>
      ),
    },
    {
      title: 'Commission',
      key: 'commission',
      render: (_, record) => {
        if (!record.commission_percentage) return <span className="text-slate-400">—</span>
        return (
          <span className="text-[13px]">
            {record.commission_percentage}
            {record.commission_type === 'percentage' ? '%' : ' fixed'}
          </span>
        )
      },
    },
    {
      title: 'Since',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => (
        <span className="text-[13px] text-slate-500">
          {dayjs(date).format('MMM D, YYYY')}
        </span>
      ),
    },
    {
      title: '',
      key: 'actions',
      width: 80,
      render: (_, record) => (
        <Button
          type="text"
          size="small"
          icon={<EditOutlined />}
          onClick={(e) => {
            e.stopPropagation()
            handleEdit(record)
          }}
          className="text-slate-400 hover:text-[#4F46E5]"
        />
      ),
    },
  ]

  const listContent = (
    <div className="p-6 h-full flex flex-col bg-white">
      <div className="flex justify-between items-center mb-6">
        <Title level={4} style={{ margin: 0, fontFamily: 'Outfit', fontWeight: 700, fontSize: 20 }}>Agencies</Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setInviteDrawerOpen(true)
            setFoundTenant(null)
            setSearchQuery('')
            form.resetFields()
          }}
          className="bg-[#4F46E5] hover:bg-[#3730A3] border-none h-10 px-6 rounded-lg font-semibold"
        >
          Invite Agency
        </Button>
      </div>

      {pendingFromAgency.length > 0 && (
        <Card
          title={
            <Space>
              <BellOutlined style={{ color: '#F59E0B' }} />
              <span>Agency Invitations</span>
              <Tag color="warning">{pendingFromAgency.length}</Tag>
            </Space>
          }
          className="mb-6"
          styles={{ body: { padding: 0 } }}
        >
          <Table
            dataSource={pendingFromAgency}
            pagination={false}
            rowKey="id"
            size="middle"
            columns={[
              {
                title: 'Agency',
                dataIndex: 'agency_name',
                render: (name) => <Text strong>{name}</Text>
              },
              {
                title: 'Industry',
                dataIndex: 'industry',
                render: (v) => v || '-'
              },
              {
                title: 'Commission',
                render: (_, r) => r.commission_percentage
                  ? `${r.commission_percentage}${r.commission_type === 'percentage' ? '%' : ' fixed'}`
                  : '-'
              },
              {
                title: 'Contact',
                render: (_, r) => r.contact_person_name || r.contact_email || '-'
              },
              {
                title: 'Received',
                dataIndex: 'created_at',
                render: (d) => dayjs(d).format('MMM D, YYYY')
              },
              {
                title: 'Actions',
                key: 'actions',
                render: (_, r) => (
                  <Space>
                    <Button
                      type="primary"
                      size="small"
                      icon={<CheckOutlined />}
                      onClick={() => handleAccept(r.id)}
                      style={{ background: '#10B981', borderColor: '#10B981' }}
                    >
                      Accept
                    </Button>
                    <Button
                      danger
                      size="small"
                      icon={<CloseOutlined />}
                      onClick={() => handleDecline(r.id)}
                    >
                      Decline
                    </Button>
                    <Button
                      type="text"
                      size="small"
                      icon={<EyeOutlined />}
                      onClick={() => setSelectedId(r.id)}
                    >
                      View
                    </Button>
                  </Space>
                )
              }
            ]}
          />
        </Card>
      )}

      {pendingSentByUs.length > 0 && (
        <Collapse
          ghost
          className="mb-6"
          items={[{
            key: '1',
            label: (
              <Space>
                <ClockCircleOutlined style={{ color: '#6B7280' }} />
                <Text type="secondary">
                  Pending Sent ({pendingSentByUs.length})
                </Text>
              </Space>
            ),
            children: (
              <Table
                dataSource={pendingSentByUs}
                pagination={false}
                rowKey="id"
                size="small"
                columns={[
                  {
                    title: 'Agency',
                    dataIndex: 'agency_name',
                    render: (name) => <Text>{name}</Text>
                  },
                  {
                    title: 'Sent via',
                    dataIndex: 'invited_via',
                    render: (v) => v || '-'
                  },
                  {
                    title: 'Sent on',
                    dataIndex: 'created_at',
                    render: (d) => dayjs(d).format('MMM D, YYYY')
                  },
                  {
                    title: '',
                    render: (_, r) => (
                      <Button
                        type="text"
                        danger
                        size="small"
                        onClick={() => handleDecline(r.id)}
                      >
                        Cancel
                      </Button>
                    )
                  }
                ]}
              />
            )
          }]}
        />
      )}

      <div className="flex-1 overflow-auto border border-slate-100 rounded-xl shadow-sm">
        <Table
          dataSource={activeRelationships}
          columns={columns}
          rowKey="id"
          loading={isLoading}
          pagination={{ pageSize: 10 }}
          onRow={(record) => ({
            onClick: () => setSelectedId(record.id),
            className: cn(
              'cursor-pointer transition-all duration-200',
              'hover:bg-[#EEF2FF]',
              selectedId === record.id && 'bg-[#EEF2FF] border-l-[3px] border-l-[#4F46E5]'
            ),
          })}
          components={{
            header: {
              cell: (props: any) => (
                <th {...props} style={{ ...props.style, backgroundColor: '#F9FAFB', color: '#6B7280', fontWeight: 600, fontSize: 12, textTransform: 'uppercase' }} />
              )
            }
          }}
          locale={{
            emptyText: (
              <div className="py-12 flex flex-col items-center justify-center text-slate-400">
                <InboxOutlined style={{ fontSize: 48 }} />
                <p className="mt-4 text-sm font-medium">No agency relationships found</p>
                <p className="text-xs">Invite agencies to start collaborating on jobs.</p>
              </div>
            )
          }}
        />
      </div>
    </div>
  )

  const detailContent = selectedRelationship && (() => {
    const displayName = getAgencyDisplayName(selectedRelationship)
    const badge = getConnectionBadge(selectedRelationship)
    const isGuest = selectedRelationship.connection_type === 'agency_guest'

    return (
      <div className="h-full flex flex-col bg-white border-l border-[#F3F4F6]">
        {/* Header */}
        <div className="p-6 border-b border-slate-100 flex justify-between items-start">
          <div className="flex-1 min-w-0">
            <Title level={4} style={{ margin: 0, color: '#111827', fontWeight: 700 }}>
              {displayName}
            </Title>
            <div className="mt-1 flex items-center gap-2 flex-wrap">
              <Tag color={badge.color}>{badge.label}</Tag>
              {isGuest && (
                <Tag color="purple" className="text-[11px]">Guest Portal</Tag>
              )}
              <Text type="secondary" className="text-[12px]">
                Added {selectedRelationship.created_at ? dayjs(selectedRelationship.created_at).format('MMM D, YYYY') : 'N/A'}
              </Text>
            </div>
          </div>
          <div className="flex items-center gap-1 ml-2 shrink-0">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(selectedRelationship)}
              className="text-slate-400 hover:text-[#4F46E5]"
            >
              Edit
            </Button>
            <Button type="text" size="small" onClick={() => setSelectedId(null)}>
              Close
            </Button>
          </div>
        </div>

        <div className="p-6 overflow-y-auto flex-1">
          <div className="space-y-6">

            {/* Guest Portal Status Banner */}
            {isGuest && selectedRelationship.status === 'pending' && (
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl">
                <div className="text-[12px] font-semibold text-amber-800 mb-1">Invite Pending</div>
                <div className="text-[12px] text-amber-700">
                  Invite sent to {selectedRelationship.contact_email}. Agency hasn't accepted yet.
                  You can still assign jobs to them.
                </div>
                <Button
                  size="small"
                  className="mt-2 border-amber-400 text-amber-700 hover:bg-amber-100"
                  onClick={async () => {
                    if (!selectedRelationship.guest_portal_id) return
                    try {
                      await agenciesApi.resendPortalInvite(selectedRelationship.guest_portal_id)
                      message.success('Invite resent')
                    } catch {
                      message.error('Failed to resend invite')
                    }
                  }}
                >
                  Resend Invite
                </Button>
              </div>
            )}

            {/* Contact Details */}
            <section>
              <div className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider mb-3">
                Contact Details
              </div>
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-[12px] text-slate-500">Contact Person</div>
                    <div className="text-[14px] font-semibold text-[#111827]">
                      {selectedRelationship.contact_person_name || '—'}
                    </div>
                  </div>
                  <div>
                    <div className="text-[12px] text-slate-500">Industry</div>
                    <div className="text-[14px] font-semibold text-[#111827]">
                      {selectedRelationship.industry || '—'}
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-[12px] text-slate-500">Email</div>
                    <div className="text-[14px] font-semibold text-[#111827] break-all">
                      {selectedRelationship.contact_email || '—'}
                    </div>
                  </div>
                  <div>
                    <div className="text-[12px] text-slate-500">Phone</div>
                    <div className="text-[14px] font-semibold text-[#111827]">
                      {selectedRelationship.contact_phone_number
                        ? formatPhoneDisplay(selectedRelationship.contact_country_code || 'IN', selectedRelationship.contact_phone_number)
                        : selectedRelationship.contact_phone || '—'}
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <Divider style={{ margin: 0 }} />

            {/* Financials */}
            <section>
              <div className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider mb-3">
                Fee Structure
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-[12px] text-slate-500">Commission</div>
                  <div className="text-[14px] font-semibold text-[#111827]">
                    {selectedRelationship.commission_percentage
                      ? `${selectedRelationship.commission_percentage}${selectedRelationship.commission_type === 'percentage' ? '%' : ' fixed'}`
                      : '—'}
                  </div>
                </div>
                <div>
                  <div className="text-[12px] text-slate-500">Type</div>
                  <div className="text-[14px] font-semibold text-[#111827] capitalize">
                    {selectedRelationship.commission_type || '—'}
                  </div>
                </div>
              </div>
              <div className="mt-3">
                <div className="text-[12px] text-slate-500 mb-2">Payment Terms</div>
                <Space wrap size={[4, 4]}>
                  {Array.isArray(selectedRelationship.payment_terms) && selectedRelationship.payment_terms.length > 0
                    ? selectedRelationship.payment_terms.filter(t => t !== 'custom').map(term => (
                        <Tag key={term} className="bg-slate-50 border-slate-200 text-slate-600 rounded-md m-0 text-[12px]">
                          {term}
                        </Tag>
                      ))
                    : <span className="text-slate-400 italic text-[13px]">Not specified</span>}
                </Space>
              </div>

              {Array.isArray(selectedRelationship.payment_schedule) && selectedRelationship.payment_schedule.length > 0 && (
                <div className="mt-3">
                  <div className="text-[12px] text-slate-500 mb-2">Payment Schedule</div>
                  <div className="space-y-1">
                    {selectedRelationship.payment_schedule.map((item, i) => (
                      <div key={i} className="text-[13px] text-slate-700 flex gap-2">
                        <span className="font-semibold text-[#4F46E5]">{item.percentage}%</span>
                        <span>
                          {item.trigger === 'on_joining'
                            ? 'on joining date'
                            : `${item.days} days after joining`}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </section>

            <Divider style={{ margin: 0 }} />

            {/* SLAs */}
            <section>
              <div className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider mb-3">
                SLAs & Contract Period
              </div>
              <div className="grid grid-cols-2 gap-4 mb-3">
                <div>
                  <div className="text-[12px] text-slate-500">Submission SLA</div>
                  <div className="text-[14px] font-semibold text-[#111827]">
                    {selectedRelationship.sla_submission_hours || 48}h
                  </div>
                </div>
                <div>
                  <div className="text-[12px] text-slate-500">Feedback SLA</div>
                  <div className="text-[14px] font-semibold text-[#111827]">
                    {selectedRelationship.sla_feedback_hours || 72}h
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-[12px] text-slate-500">Start Date</div>
                  <div className="text-[14px] font-semibold text-[#111827]">
                    {selectedRelationship.contract_start_date
                      ? dayjs(selectedRelationship.contract_start_date).format('MMM D, YYYY')
                      : 'Not set'}
                  </div>
                </div>
                <div>
                  <div className="text-[12px] text-slate-500">End Date</div>
                  <div className="text-[14px] font-semibold text-[#111827]">
                    {selectedRelationship.contract_end_date
                      ? dayjs(selectedRelationship.contract_end_date).format('MMM D, YYYY')
                      : 'Not set'}
                  </div>
                </div>
              </div>
            </section>

            <Divider style={{ margin: 0 }} />

            {/* Documents */}
            <section>
              <div className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider mb-3">
                Documents
              </div>
              <div className="space-y-2">
                {[
                  { label: 'Service Agreement', url: selectedRelationship.contract_file_url },
                  { label: 'Recruitment Policy', url: selectedRelationship.recruitment_policy_url },
                ].map(doc => (
                  <div key={doc.label} className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100">
                    <div className="flex items-center gap-2">
                      <FileTextOutlined className="text-blue-500" />
                      <span className="text-[13px] font-medium text-slate-700">{doc.label}</span>
                    </div>
                    {doc.url
                      ? <Button type="link" size="small" href={doc.url} target="_blank">View</Button>
                      : <span className="text-[11px] text-slate-400">Not uploaded</span>}
                  </div>
                ))}
              </div>
            </section>

            <Divider style={{ margin: 0 }} />

            {/* Candidate Retention */}
            <section>
              <div className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider mb-3">
                Candidate Data Retention
              </div>
              {selectedRelationship.retention_enabled ? (
                <div className="p-4 bg-indigo-50 border border-indigo-100 rounded-xl">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-[11px] text-indigo-400 font-bold uppercase tracking-tight">Period</div>
                      <div className="text-[14px] font-bold text-indigo-900">{selectedRelationship.retention_days} Days</div>
                    </div>
                    <div>
                      <div className="text-[11px] text-indigo-400 font-bold uppercase tracking-tight">Scope</div>
                      <div className="text-[14px] font-bold text-indigo-900 capitalize">{selectedRelationship.retention_scope?.replace(/_/g, ' ') || 'Job Only'}</div>
                    </div>
                  </div>
                  <div className="mt-3 pt-3 border-t border-indigo-100/50">
                    <div className="text-[12px] text-indigo-700 leading-snug">
                      Candidates submitted are protected starting from <span className="font-bold underline">{selectedRelationship.retention_start_type?.replace(/_/g, ' ')}</span>.
                      After expiry, status becomes <span className="font-bold underline">{selectedRelationship.retention_post_expiry?.replace(/_/g, ' ')}</span>.
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-2 p-3 bg-slate-50 rounded-lg text-slate-400 italic text-[13px]">
                  <InfoCircleOutlined className="text-slate-300" />
                  No specific retention terms active for this agency.
                </div>
              )}
            </section>

            <Divider style={{ margin: 0 }} />

            {/* Replacement / Guarantee Clause */}
            <section>
              <div className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider mb-3">
                Replacement / Guarantee Clause
              </div>
              {selectedRelationship.replacement_guarantee_enabled ? (
                <div className="p-4 bg-amber-50 border border-amber-100 rounded-xl">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-[11px] text-amber-500 font-bold uppercase tracking-tight">Period</div>
                      <div className="text-[14px] font-bold text-amber-900">{selectedRelationship.guarantee_period_days || 0} Days</div>
                    </div>
                    <div>
                      <div className="text-[11px] text-amber-500 font-bold uppercase tracking-tight">Resolution</div>
                      <div className="text-[14px] font-bold text-amber-900 capitalize">{selectedRelationship.guarantee_resolution_type?.replace(/_/g, ' ') || 'Replacement Only'}</div>
                    </div>
                  </div>
                  <div className="mt-3 pt-3 border-t border-amber-100/70 text-[12px] text-amber-800 leading-snug">
                    Guarantee starts from <span className="font-bold underline">{selectedRelationship.guarantee_start_type?.replace(/_/g, ' ') || 'joining date'}</span>.
                    {selectedRelationship.refund_mode ? (
                      <> Refund mode: <span className="font-bold underline">{selectedRelationship.refund_mode.replace(/_/g, ' ')}</span>{selectedRelationship.refund_percentage ? ` (${selectedRelationship.refund_percentage}%)` : ''}.</>
                    ) : null}
                  </div>
                  {!!selectedRelationship.guarantee_notes && (
                    <div className="mt-3 text-[12px] text-amber-800 bg-amber-100/60 rounded-lg p-2">
                      {selectedRelationship.guarantee_notes}
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center gap-2 p-3 bg-slate-50 rounded-lg text-slate-400 italic text-[13px]">
                  <InfoCircleOutlined className="text-slate-300" />
                  Replacement / guarantee clause is not active for this agency.
                </div>
              )}
            </section>

            <Divider style={{ margin: 0 }} />

            {/* Notes */}
            <section>
              <div className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider mb-2">Notes</div>
              <div className="p-3 bg-slate-50 rounded-lg text-slate-600 text-[13px] leading-relaxed">
                {selectedRelationship.notes || 'No notes added.'}
              </div>
            </section>

            {/* Actions */}
            <div className="pt-2 space-y-2">
              {selectedRelationship.status === 'active' && (
                <Button
                  danger block
                  icon={<StopOutlined />}
                  onClick={() => handleStatusChange(selectedRelationship.id, 'suspend')}
                  className="h-10 rounded-lg font-medium"
                >
                  Suspend Agency
                </Button>
              )}
              {selectedRelationship.status === 'suspended' && (
                <Button
                  type="primary" block
                  icon={<CheckCircleOutlined />}
                  onClick={() => handleStatusChange(selectedRelationship.id, 'reactivate')}
                  className="bg-[#4F46E5] h-10 rounded-lg font-medium"
                >
                  Reactivate Agency
                </Button>
              )}
            </div>

          </div>
        </div>
      </div>
    )
  })()

  return (
    <>
      <StandardSplitView
        isDetailOpen={!!selectedId}
        fullListContent={listContent}
        compactListContent={listContent}
        detailContent={detailContent}
        leftOpenWidthClass="w-full lg:w-[calc(100%-400px)]"
        rightOpenWidthClass="w-[400px]"
      />

      <Drawer
        title={<span className="font-bold font-['Outfit'] text-lg">Invite Agency</span>}
        width={560}
        onClose={() => {
          setInviteDrawerOpen(false)
          setFoundTenant(null)
          setSearchQuery('')
          form.resetFields()
        }}
        open={inviteDrawerOpen}
        footer={null}
      >
        <Form 
          form={form} 
          layout="vertical" 
          onFinish={handleSubmit}
          initialValues={{ 
            commission_percentage: 10, 
            commission_type: 'percentage',
            sla_submission_hours: 48,
            sla_feedback_hours: 72,
          }}
        >
          <div className="p-4 bg-slate-50 rounded-xl mb-6 border border-slate-100">
            <Text strong className="block mb-3">Find Agency</Text>
            
            <Input.Search
              placeholder="Email or phone number"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value)
                setFoundTenant(null)
              }}
              onSearch={handleSearch}
              enterButton={<Button loading={searchLoading}>Search</Button>}
              onPressEnter={handleSearch}
            />

            {/* Found result */}
            {foundTenant?.found && (
              <div className="mt-3 p-3 bg-green-50 border border-green-200 
                              rounded-lg flex items-center gap-3">
                <CheckCircleFilled className="text-green-500 text-lg" />
                <div className="flex-1">
                  <Text strong className="block">{foundTenant.name}</Text>
                  <Text type="secondary" className="text-xs">
                    {foundTenant.tenant_type} · {foundTenant.email}
                  </Text>
                </div>
              </div>
            )}

            {/* Not found result */}
            {foundTenant && !foundTenant.found && (
              <div className="mt-3 p-3 bg-blue-50 border border-blue-200 
                              rounded-lg flex items-center gap-3">
                <InfoCircleOutlined className="text-blue-400 text-lg" />
                <div>
                  <Text strong className="block">Not on RecruitOS yet</Text>
                  <Text type="secondary" className="text-xs">
                    Create a guest portal to collaborate with this agency.
                  </Text>
                </div>
              </div>
            )}
          </div>

          {foundTenant && (
            <div className="animate-in fade-in slide-in-from-top-2 duration-300">
              <div className="p-4 border border-slate-100 rounded-xl">
                <Title level={5} className="!mb-4">
                  {foundTenant.found ? 'Contract Details' : 'Agency Details'}
                </Title>

                {!foundTenant.found && (
                  <Form.Item name="agency_name" label="Agency Name" rules={[{ required: true, message: 'Agency name is required' }]}>
                    <Input placeholder="e.g. Acme Recruiting" />
                  </Form.Item>
                )}

                <Form.Item name="contact_person_name" label="Contact Person Name" rules={[{ required: true }]}>
                  <Input placeholder="Full name" />
                </Form.Item>

                <Form.Item name="contact_email" label="Contact Email" rules={[{ required: true }]}>
                  <Input />
                </Form.Item>

                <Form.Item
                  name="contact_phone_field"
                  label="Contact Phone"
                  rules={[{ required: true, message: 'Phone is required' }, getPhoneValidationRule()]}
                >
                  <PhoneInput placeholder="Phone number" />
                </Form.Item>

                {!foundTenant.found && (
                  <>
                    <Form.Item
                      name="invite_message"
                      label="Invite Message"
                      initialValue="Hi, we'd like to invite you to our agency portal to collaborate on our open roles."
                    >
                      <Input.TextArea rows={3} />
                    </Form.Item>

                    <div className="p-3 bg-amber-50 rounded-lg flex gap-2 mb-4">
                      <InfoCircleOutlined className="text-amber-500 mt-0.5 shrink-0" />
                      <Text className="text-xs text-amber-700">
                        Agency will receive an invite email. They can accept or ignore it.
                        You can still assign jobs right away.
                      </Text>
                    </div>
                  </>
                )}

                <Divider className="my-4" titlePlacement="left" plain>
                  <span className="text-[11px] text-slate-400 uppercase tracking-wider">Contract Details (Optional)</span>
                </Divider>

                <div className="grid grid-cols-2 gap-4">
                  <Form.Item name="commission_percentage" label="Commission Rate (%)">
                    <InputNumber min={0} max={100} className="w-full" placeholder="10" />
                  </Form.Item>
                  <Form.Item name="commission_type" label="Commission Type">
                    <Select>
                      <Option value="percentage">Percentage of CTC</Option>
                      <Option value="fixed">Fixed Amount per Hire</Option>
                      <Option value="milestone">Milestone Based</Option>
                    </Select>
                  </Form.Item>
                </div>

                <Form.Item name="payment_terms_field" label="Payment Terms">
                  <PaymentTermsField />
                </Form.Item>

                <div className="grid grid-cols-2 gap-4">
                  <Form.Item name="sla_submission_hours" label="Submission SLA (hours)">
                    <InputNumber min={1} className="w-full" />
                  </Form.Item>
                  <Form.Item name="sla_feedback_hours" label="Feedback SLA (hours)">
                    <InputNumber min={1} className="w-full" />
                  </Form.Item>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <Form.Item name="contract_start_date" label="Contract Start Date">
                    <DatePicker className="w-full" />
                  </Form.Item>
                  <Form.Item name="contract_end_date" label="Contract End Date">
                    <DatePicker className="w-full" />
                  </Form.Item>
                </div>

                <Form.Item name="notes" label="Notes">
                  <Input.TextArea rows={2} placeholder="Internal notes about this agency..." />
                </Form.Item>

                <Divider className="my-4" titlePlacement="left" plain>
                  <span className="text-[11px] text-slate-400 uppercase tracking-wider">Candidate Data Retention</span>
                </Divider>

                <Form.Item name="retention_enabled" label="Enable Candidate Data Retention" valuePropName="checked" initialValue={false}>
                  <Checkbox>
                    <span className="text-[13px] text-slate-600">Candidates submitted by agency remain protected during retention period.</span>
                  </Checkbox>
                </Form.Item>

                <Form.Item noStyle dependencies={['retention_enabled']}>
                  {({ getFieldValue }) => getFieldValue('retention_enabled') && (
                    <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 space-y-4 animate-in fade-in slide-in-from-top-1">
                      <Form.Item name="retention_days" label="Retention Period" initialValue={90} rules={[{ required: true }]}>
                        <Select options={[
                          { value: 30, label: '30 Days' },
                          { value: 60, label: '60 Days' },
                          { value: 90, label: '90 Days' },
                          { value: 120, label: '120 Days' },
                          { value: 180, label: '180 Days' },
                        ]} />
                      </Form.Item>

                      <Form.Item name="retention_start_type" label="Retention Start From" initialValue="submission_date">
                        <Select options={[
                          { value: 'submission_date', label: 'Submission Date' },
                          { value: 'rejection_date', label: 'Rejection Date' },
                          { value: 'last_activity', label: 'Last Activity Date' },
                        ]} />
                      </Form.Item>

                      <Form.Item name="retention_scope" label="Usage Scope During Retention" initialValue="job_only">
                        <Select options={[
                          { value: 'job_only', label: 'Job Only (Recommended)' },
                          { value: 'view_only', label: 'View Only' },
                          { value: 'limited_access', label: 'Limited Company Access' },
                        ]} />
                      </Form.Item>

                      <Form.Item name="retention_post_expiry" label="After Retention Expiry" initialValue="shared">
                        <Select options={[
                          { value: 'shared', label: 'Shared Ownership' },
                          { value: 'company_use', label: 'Company Can Use Candidate' },
                          { value: 'consent_required', label: 'Require Candidate Consent' },
                        ]} />
                      </Form.Item>
                    </div>
                  )}
                </Form.Item>

                <Divider className="my-4" titlePlacement="left" plain>
                  <span className="text-[11px] text-slate-400 uppercase tracking-wider">Replacement / Guarantee Clause</span>
                </Divider>

                <Form.Item name="replacement_guarantee_enabled" label="Enable Replacement / Guarantee Clause" valuePropName="checked" initialValue={false}>
                  <Checkbox>
                    <span className="text-[13px] text-slate-600">
                      If an agency-placed candidate leaves during guarantee window, replacement/refund rules apply.
                    </span>
                  </Checkbox>
                </Form.Item>

                <Form.Item noStyle dependencies={['replacement_guarantee_enabled', 'guarantee_period_days', 'guarantee_resolution_type', 'refund_mode']}>
                  {({ getFieldValue }) => getFieldValue('replacement_guarantee_enabled') && (
                    <div className="p-4 bg-amber-50 rounded-xl border border-amber-100 space-y-4 animate-in fade-in slide-in-from-top-1">
                      <Form.Item name="guarantee_period_days" label="Guarantee Period" initialValue={30} rules={[{ required: true }]}>
                        <Select options={GUARANTEE_PERIOD_OPTIONS as any} />
                      </Form.Item>

                      {getFieldValue('guarantee_period_days') === 'custom' && (
                        <Form.Item name="guarantee_custom_days" label="Custom Guarantee Days" rules={[{ required: true, type: 'number', min: 1 }]}>
                          <InputNumber min={1} className="w-full" />
                        </Form.Item>
                      )}

                      <Form.Item name="guarantee_start_type" label="Guarantee Start From" initialValue="joining_date">
                        <Select options={[
                          { value: 'joining_date', label: 'Joining Date' },
                          { value: 'offer_acceptance_date', label: 'Offer Acceptance Date' },
                          { value: 'first_working_day', label: 'First Working Day' },
                        ]} />
                      </Form.Item>

                      <Form.Item name="guarantee_resolution_type" label="Guarantee Resolution Type" initialValue="replacement_only">
                        <Select options={[
                          { value: 'replacement_only', label: 'Replacement Only' },
                          { value: 'refund_only', label: 'Refund Only' },
                          { value: 'replacement_or_refund', label: 'Replacement or Refund' },
                          { value: 'no_guarantee', label: 'No Guarantee' },
                        ]} />
                      </Form.Item>

                      {['refund_only', 'replacement_or_refund'].includes(getFieldValue('guarantee_resolution_type')) && (
                        <>
                          <Form.Item name="refund_mode" label="Refund Mode">
                            <Select options={[
                              { value: 'full_refund', label: 'Full Refund' },
                              { value: 'partial_refund', label: 'Partial Refund' },
                              { value: 'pro_rated_refund', label: 'Pro-rated Refund' },
                            ]} />
                          </Form.Item>
                          {['partial_refund', 'pro_rated_refund'].includes(getFieldValue('refund_mode')) && (
                            <Form.Item name="refund_percentage" label="Refund Percentage">
                              <InputNumber min={1} max={100} className="w-full" addonAfter="%" />
                            </Form.Item>
                          )}
                        </>
                      )}

                      <Form.Item name="replacement_attempt_limit" label="Replacement Attempt Limit" initialValue="1">
                        <Select options={[
                          { value: '1', label: '1' },
                          { value: '2', label: '2' },
                          { value: 'unlimited', label: 'Unlimited' },
                        ]} />
                      </Form.Item>

                      <Form.Item name="guarantee_notes" label="Clause Notes">
                        <Input.TextArea rows={2} placeholder="Define any custom guarantee or exception terms..." />
                      </Form.Item>

                      <div className="text-[12px] text-amber-700 bg-amber-100/70 rounded-lg p-2">
                        If a candidate placed through agency leaves within the guarantee period, company may raise replacement or refund request based on contract terms.
                      </div>
                    </div>
                  )}
                </Form.Item>

                <Button
                  type="primary"
                  htmlType="submit"
                  loading={submitting}
                  block
                  style={{ height: 44, background: '#4F46E5' }}
                  className="mt-6"
                >
                  {foundTenant.found ? `Send Invitation to ${foundTenant.name}` : 'Create Portal & Send Invite'}
                </Button>
              </div>
            </div>
          )}
        </Form>
      </Drawer>

      <Drawer
        title={
          <span className="font-bold font-['Outfit'] text-lg">
            Edit Agency — {editingRelationship ? getAgencyDisplayName(editingRelationship) : ''}
          </span>
        }
        width={520}
        onClose={() => {
          setEditDrawerOpen(false)
          setEditingRelationship(null)
          editForm.resetFields()
        }}
        open={editDrawerOpen}
        footer={null}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleEditSubmit}
        >
          <div className="space-y-1">

            <div className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider mb-4">
              Contact Details
            </div>

            <Form.Item name="contact_person_name" label="Contact Person" rules={[{ required: true }]}>
              <Input placeholder="Full name" />
            </Form.Item>

            <div className="grid grid-cols-2 gap-4">
              <Form.Item name="contact_email" label="Contact Email" rules={[{ required: true }]}>
                <Input placeholder="email@agency.com" />
              </Form.Item>
              <Form.Item
                name="contact_phone_field"
                label="Contact Phone"
                rules={[getPhoneValidationRule()]}
              >
                <PhoneInput placeholder="Phone number" />
              </Form.Item>
            </div>

            <Form.Item name="industry" label="Industry">
              <Select placeholder="Select industry" allowClear>
                {INDUSTRY_OPTIONS.map(opt => <Option key={opt} value={opt}>{opt}</Option>)}
              </Select>
            </Form.Item>

            <Divider className="my-4" titlePlacement="left" plain>
              <span className="text-[11px] text-slate-400 uppercase tracking-wider">Fee Structure</span>
            </Divider>

            <div className="grid grid-cols-2 gap-4">
              <Form.Item name="commission_percentage" label="Commission Rate (%)">
                <InputNumber min={0} max={100} className="w-full" />
              </Form.Item>
              <Form.Item name="commission_type" label="Commission Type">
                <Select>
                  <Option value="percentage">Percentage of CTC</Option>
                  <Option value="fixed">Fixed Amount per Hire</Option>
                  <Option value="milestone">Milestone Based</Option>
                </Select>
              </Form.Item>
            </div>

            <Form.Item name="payment_terms_field" label="Payment Terms">
              <PaymentTermsField />
            </Form.Item>

            <Divider className="my-4" titlePlacement="left" plain>
              <span className="text-[11px] text-slate-400 uppercase tracking-wider">SLAs & Duration</span>
            </Divider>

            <div className="grid grid-cols-2 gap-4">
              <Form.Item name="sla_submission_hours" label="Submission SLA (hours)">
                <InputNumber min={1} className="w-full" />
              </Form.Item>
              <Form.Item name="sla_feedback_hours" label="Feedback SLA (hours)">
                <InputNumber min={1} className="w-full" />
              </Form.Item>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <Form.Item name="contract_start_date" label="Contract Start Date">
                <DatePicker className="w-full" />
              </Form.Item>
              <Form.Item name="contract_end_date" label="Contract End Date">
                <DatePicker className="w-full" />
              </Form.Item>
            </div>

            <Divider className="my-4" />

            <Form.Item name="notes" label="Notes">
              <Input.TextArea rows={3} placeholder="Internal notes..." />
            </Form.Item>

            <Divider className="my-4" titlePlacement="left" plain>
              <span className="text-[11px] text-slate-400 uppercase tracking-wider">Candidate Data Retention</span>
            </Divider>

            <Form.Item name="retention_enabled" label="Enable Candidate Data Retention" valuePropName="checked">
              <Checkbox>
                <span className="text-[13px] text-slate-600">Candidates submitted by agency remain protected during retention period.</span>
              </Checkbox>
            </Form.Item>

            <Form.Item noStyle dependencies={['retention_enabled']}>
              {({ getFieldValue }) => getFieldValue('retention_enabled') && (
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 space-y-4 animate-in fade-in slide-in-from-top-1">
                  <Form.Item name="retention_days" label="Retention Period" rules={[{ required: true }]}>
                    <Select options={[
                      { value: 30, label: '30 Days' },
                      { value: 60, label: '60 Days' },
                      { value: 90, label: '90 Days' },
                      { value: 120, label: '120 Days' },
                      { value: 180, label: '180 Days' },
                    ]} />
                  </Form.Item>

                  <Form.Item name="retention_start_type" label="Retention Start From">
                    <Select options={[
                      { value: 'submission_date', label: 'Submission Date' },
                      { value: 'rejection_date', label: 'Rejection Date' },
                      { value: 'last_activity', label: 'Last Activity Date' },
                    ]} />
                  </Form.Item>

                  <Form.Item name="retention_scope" label="Usage Scope During Retention">
                    <Select options={[
                      { value: 'job_only', label: 'Job Only' },
                      { value: 'view_only', label: 'View Only' },
                      { value: 'limited_access', label: 'Limited Access' },
                    ]} />
                  </Form.Item>

                  <Form.Item name="retention_post_expiry" label="After Retention Expiry">
                    <Select options={[
                      { value: 'shared', label: 'Shared Ownership' },
                      { value: 'company_use', label: 'Company Can Use' },
                      { value: 'consent_required', label: 'Require Consent' },
                    ]} />
                  </Form.Item>
                </div>
              )}
            </Form.Item>

            <Divider className="my-4" titlePlacement="left" plain>
              <span className="text-[11px] text-slate-400 uppercase tracking-wider">Replacement / Guarantee Clause</span>
            </Divider>

            <Form.Item name="replacement_guarantee_enabled" label="Enable Replacement / Guarantee Clause" valuePropName="checked">
              <Checkbox>
                <span className="text-[13px] text-slate-600">
                  If an agency-placed candidate leaves during guarantee window, replacement/refund rules apply.
                </span>
              </Checkbox>
            </Form.Item>

            <Form.Item noStyle dependencies={['replacement_guarantee_enabled', 'guarantee_period_days', 'guarantee_resolution_type', 'refund_mode']}>
              {({ getFieldValue }) => getFieldValue('replacement_guarantee_enabled') && (
                <div className="p-4 bg-amber-50 rounded-xl border border-amber-100 space-y-4 animate-in fade-in slide-in-from-top-1">
                  <Form.Item name="guarantee_period_days" label="Guarantee Period" rules={[{ required: true }]}>
                    <Select options={GUARANTEE_PERIOD_OPTIONS as any} />
                  </Form.Item>

                  {getFieldValue('guarantee_period_days') === 'custom' && (
                    <Form.Item name="guarantee_custom_days" label="Custom Guarantee Days" rules={[{ required: true, type: 'number', min: 1 }]}>
                      <InputNumber min={1} className="w-full" />
                    </Form.Item>
                  )}

                  <Form.Item name="guarantee_start_type" label="Guarantee Start From">
                    <Select options={[
                      { value: 'joining_date', label: 'Joining Date' },
                      { value: 'offer_acceptance_date', label: 'Offer Acceptance Date' },
                      { value: 'first_working_day', label: 'First Working Day' },
                    ]} />
                  </Form.Item>

                  <Form.Item name="guarantee_resolution_type" label="Guarantee Resolution Type">
                    <Select options={[
                      { value: 'replacement_only', label: 'Replacement Only' },
                      { value: 'refund_only', label: 'Refund Only' },
                      { value: 'replacement_or_refund', label: 'Replacement or Refund' },
                      { value: 'no_guarantee', label: 'No Guarantee' },
                    ]} />
                  </Form.Item>

                  {['refund_only', 'replacement_or_refund'].includes(getFieldValue('guarantee_resolution_type')) && (
                    <>
                      <Form.Item name="refund_mode" label="Refund Mode">
                        <Select options={[
                          { value: 'full_refund', label: 'Full Refund' },
                          { value: 'partial_refund', label: 'Partial Refund' },
                          { value: 'pro_rated_refund', label: 'Pro-rated Refund' },
                        ]} />
                      </Form.Item>
                      {['partial_refund', 'pro_rated_refund'].includes(getFieldValue('refund_mode')) && (
                        <Form.Item name="refund_percentage" label="Refund Percentage">
                          <InputNumber min={1} max={100} className="w-full" addonAfter="%" />
                        </Form.Item>
                      )}
                    </>
                  )}

                  <Form.Item name="replacement_attempt_limit" label="Replacement Attempt Limit">
                    <Select options={[
                      { value: '1', label: '1' },
                      { value: '2', label: '2' },
                      { value: 'unlimited', label: 'Unlimited' },
                    ]} />
                  </Form.Item>

                  <Form.Item name="guarantee_notes" label="Clause Notes">
                    <Input.TextArea rows={2} placeholder="Define any custom guarantee or exception terms..." />
                  </Form.Item>
                </div>
              )}
            </Form.Item>

            <div className="flex gap-3 pt-6">
              <Button className="flex-1 h-11 rounded-lg" onClick={() => setEditDrawerOpen(false)}>
                Cancel
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                className="flex-1 h-11 bg-[#4F46E5] rounded-lg"
                loading={editSubmitting}
              >
                Save Changes
              </Button>
            </div>
          </div>
        </Form>
      </Drawer>
    </>
  )
}
