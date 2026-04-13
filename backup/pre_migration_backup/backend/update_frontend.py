import sys

content = r"""import { useState } from 'react'
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
  industry?: string
  contract_file_url?: string
  recruitment_policy_url?: string
  payment_terms?: string[]
  invited_by?: 'company' | 'agency'
  invited_via?: string
  connection_type?: 'full_full' | 'agency_guest' | 'client_guest' | 'email_tracking' | 'offline'
  guest_portal_id?: string
  their_ats_url?: string
  last_activity_at?: string
  // guest portal invite tracking (returned from API when connection_type=agency_guest)
  invite_status?: 'pending' | 'active' | 'expired'
  portal_url?: string
}

function getAgencyDisplayName(r: AgencyRelationship): string {
  // For guest portals, agency_name comes back as "Unknown Agency"
  // Use contact info as the display name instead
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

const PAYMENT_TERM_OPTIONS = [
  'Full payment after candidate joins',
  'Full payment after 3 months retention',
  'Full payment after 6 months retention',
  '25% on joining + 75% after 3 months',
  '50% on joining + 50% after 3 months',
  'Custom terms'
]

const INDUSTRY_OPTIONS = [
  'Technology', 'Finance', 'Healthcare', 'Manufacturing',
  'Retail', 'Education', 'Consulting', 'Real Estate', 'Other'
]

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
      contact_phone: rel.contact_phone || '',
      industry: rel.industry || undefined,
      commission_percentage: rel.commission_percentage ?? 10,
      commission_type: rel.commission_type || 'percentage',
      payment_terms: rel.payment_terms || [],
      sla_submission_hours: rel.sla_submission_hours || 48,
      sla_feedback_hours: rel.sla_feedback_hours || 72,
      contract_start_date: rel.contract_start_date ? dayjs(rel.contract_start_date) : null,
      contract_end_date: rel.contract_end_date ? dayjs(rel.contract_end_date) : null,
      notes: rel.notes || '',
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
        contact_phone: values.contact_phone,
        industry: values.industry,
        commission_percentage: values.commission_percentage,
        commission_type: values.commission_type,
        payment_terms: values.payment_terms || [],
        sla_submission_hours: values.sla_submission_hours,
        sla_feedback_hours: values.sla_feedback_hours,
        contract_start_date: values.contract_start_date?.format('YYYY-MM-DD') || null,
        contract_end_date: values.contract_end_date?.format('YYYY-MM-DD') || null,
        notes: values.notes,
      })
      message.success('Agency details updated')
      setEditDrawerOpen(false)
      setEditingRelationship(null)
      editForm.resetFields()
      queryClient.invalidateQueries({ queryKey: ['agency-relationships'] })
      // Refresh selected panel if open
      if (selectedId === editingRelationship.id) {
        queryClient.invalidateQueries({ queryKey: ['agency-relationships'] })
      }
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
      console.error('[CompanyAgencies] accept error:', err)
      message.error(err.response?.data?.message || 'Failed to accept')
    }
  }

  const handleDecline = async (id: string) => {
    try {
      await agenciesApi.suspendRelationship(id)
      message.success('Invitation declined')
      queryClient.invalidateQueries({ queryKey: ['agency-relationships'] })
    } catch (err: any) {
      console.error('[CompanyAgencies] decline error:', err)
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
      if (result.found) {
        form.setFieldsValue({ 
          industry: result.industry || undefined 
        })
      } else {
        form.setFieldsValue({
          slug: result.suggested_slug
        })
      }
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
      if (foundTenant.found) {
        // Full tenant or existing guest portal
        await agenciesApi.createRelationship({
          agency_tenant_id: foundTenant.tenant_id,
          contact_person_name: values.contact_person_name || '',
          contact_email: foundTenant.email,
          industry: values.industry || '',
          commission_percentage: values.commission_percentage,
          commission_type: values.commission_type,
          payment_terms: values.payment_terms || [],
          sla_submission_hours: values.sla_submission_hours || 48,
          sla_feedback_hours: values.sla_feedback_hours || 72,
          contract_start_date: values.contract_start_date?.format('YYYY-MM-DD') || null,
          contract_end_date: values.contract_end_date?.format('YYYY-MM-DD') || null,
          notes: values.notes || '',
        })
        message.success(`Invitation sent to ${foundTenant.name}`)
      } else {
        // Create Guest Portal + store contract details on relationship
        await agenciesApi.createGuestPortal({
          portal_type: 'agency_guest',
          name: values.agency_name,
          contact_email: searchQuery,
          contact_name: values.contact_person_name || '',
          contact_phone: values.contact_phone || '',
          invite_message: values.invite_message || '',
          slug: values.slug,
          // Contract details passed through to relationship
          commission_percentage: values.commission_percentage || null,
          commission_type: values.commission_type || 'percentage',
          payment_terms: values.payment_terms || [],
          sla_submission_hours: values.sla_submission_hours || 48,
          sla_feedback_hours: values.sla_feedback_hours || 72,
          contract_start_date: values.contract_start_date?.format('YYYY-MM-DD') || null,
          contract_end_date: values.contract_end_date?.format('YYYY-MM-DD') || null,
          notes: values.notes || '',
        })
        message.success(`Guest portal created for ${values.agency_name}. Invite sent to ${searchQuery}.`)
      }
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
      message.success(`Relationship ${action}ed`)
      queryClient.invalidateQueries({ queryKey: ['agency-relationships'] })
    } catch (err) {
      console.error(`[CompanyAgencies] ${action} error:`, err)
      message.error(`Failed to ${action} relationship`)
    }
  }

  const columns: ColumnsType<AgencyRelationship> = [
    {
      title: 'Agency',
      key: 'agency',
      render: (_, record) => {
        const name = getAgencyDisplayName(record)
        const badge = getConnectionBadge(record)
        const isGuest = record.connection_type === 'agency_guest'
        return (
          <div>
            <div className="font-semibold text-[#111827] text-[14px]">{name}</div>
            <div className="text-[12px] text-slate-400 mt-0.5">
              {isGuest
                ? record.contact_email || 'Guest Portal'
                : record.contact_email || '—'}
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
        <span className="text-[13px] text-slate-600">
          {record.contact_person_name || '—'}
        </span>
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
          onClick={() => setInviteDrawerOpen(true)}
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
                  ? `${r.commission_percentage}% (${r.commission_type})`
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
            {isGuest && selectedRelationship.contact_email && (
              <div className="mt-2 text-[12px] text-slate-400">
                Portal invite sent to: <span className="font-medium text-slate-600">{selectedRelationship.contact_email}</span>
              </div>
            )}
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
                      {selectedRelationship.contact_phone || '—'}
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
                    ? selectedRelationship.payment_terms.map(term => (
                        <Tag key={term} className="bg-slate-50 border-slate-200 text-slate-600 rounded-md m-0 text-[12px]">
                          {term}
                        </Tag>
                      ))
                    : <span className="text-slate-400 italic text-[13px]">Not specified</span>}
                </Space>
              </div>
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
        leftOpenWidthClass="w-full lg:w-[calc(100%-360px)]"
        rightOpenWidthClass="w-[360px]"
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
        extra={
          <Space>
            <Button onClick={() => setInviteDrawerOpen(false)}>Cancel</Button>
            <Button 
              type="primary" 
              onClick={() => form.submit()} 
              loading={submitting}
              disabled={!foundTenant}
              className="bg-[#4F46E5]"
            >
              Send Invitation
            </Button>
          </Space>
        }
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
            payment_terms: ['Full payment after candidate joins'],
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
                <div>
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
                  <>
                    <Form.Item name="agency_name" label="Agency Name" rules={[{ required: true, message: 'Agency name is required' }]}>
                      <Input placeholder="e.g. Acme Recruiting" />
                    </Form.Item>

                    <div className="grid grid-cols-2 gap-4">
                      <Form.Item name="contact_person_name" label="Contact Person">
                        <Input placeholder="Full name" />
                      </Form.Item>
                      <Form.Item name="contact_phone" label="Contact Phone">
                        <Input placeholder="+91..." />
                      </Form.Item>
                    </div>

                    <Form.Item
                      name="slug"
                      label="Portal URL"
                      rules={[{ required: true, message: 'Portal URL is required' }]}
                      extra={<span className="text-[11px] text-slate-400">Will be accessible at slug.recruitos.com</span>}
                    >
                      <Input addonAfter=".recruitos.com" placeholder="acme-agency" />
                    </Form.Item>

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

                    <Divider className="my-4">
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

                    <Form.Item name="payment_terms" label="Payment Terms">
                      <Checkbox.Group className="flex flex-col gap-2">
                        {PAYMENT_TERM_OPTIONS.map(opt => (
                          <Checkbox key={opt} value={opt}>{opt}</Checkbox>
                        ))}
                      </Checkbox.Group>
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
                  </>
                )}

                {foundTenant.found && (
                  <>
                    <Divider className="my-4" />

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

                    <Form.Item name="payment_terms" label="Payment Terms">
                      <Checkbox.Group className="flex flex-col gap-2">
                        {PAYMENT_TERM_OPTIONS.map(opt => (
                          <Checkbox key={opt} value={opt}>{opt}</Checkbox>
                        ))}
                      </Checkbox.Group>
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

                    <div className="grid grid-cols-2 gap-4">
                      <Form.Item label="Contract File">
                        <Upload disabled>
                          <Button icon={<UploadOutlined />} disabled block>File upload coming soon</Button>
                        </Upload>
                      </Form.Item>
                      <Form.Item label="Recruitment Policy">
                        <Upload disabled>
                          <Button icon={<UploadOutlined />} disabled block>File upload coming soon</Button>
                        </Upload>
                      </Form.Item>
                    </div>

                    <Form.Item name="notes" label="Notes">
                      <Input.TextArea rows={3} placeholder="Add terms or personalized message..." />
                    </Form.Item>
                  </>
                )}

                <Button
                  type="primary"
                  htmlType="submit"
                  loading={submitting}
                  block
                  style={{ height: 44, background: '#4F46E5' }}
                  className="mt-4"
                >
                  {foundTenant.found ? `Send Invitation to ${foundTenant.name}` : 'Create Portal & Send Invite'}
                </Button>
              </div>
            </div>
          )}
        </Form>
      </Drawer>

      {/* ── Edit Relationship Drawer ─────────────────────── */}
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
        extra={
          <Space>
            <Button onClick={() => setEditDrawerOpen(false)}>Cancel</Button>
            <Button
              type="primary"
              onClick={() => editForm.submit()}
              loading={editSubmitting}
              className="bg-[#4F46E5]"
            >
              Save Changes
            </Button>
          </Space>
        }
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

            <Form.Item name="contact_person_name" label="Contact Person">
              <Input placeholder="Full name" />
            </Form.Item>

            <div className="grid grid-cols-2 gap-4">
              <Form.Item name="contact_email" label="Contact Email">
                <Input placeholder="email@agency.com" />
              </Form.Item>
              <Form.Item name="contact_phone" label="Contact Phone">
                <Input placeholder="+91..." />
              </Form.Item>
            </div>

            <Form.Item name="industry" label="Industry">
              <Select placeholder="Select industry" allowClear>
                {INDUSTRY_OPTIONS.map(opt => <Option key={opt} value={opt}>{opt}</Option>)}
              </Select>
            </Form.Item>

            <Divider className="my-4">
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

            <Form.Item name="payment_terms" label="Payment Terms">
              <Checkbox.Group className="flex flex-col gap-2">
                {PAYMENT_TERM_OPTIONS.map(opt => (
                  <Checkbox key={opt} value={opt}>{opt}</Checkbox>
                ))}
              </Checkbox.Group>
            </Form.Item>

            <Divider className="my-4">
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
          </div>
        </Form>
      </Drawer>
    </>
  )
}
"""

with open('/home/nirav/projects/SaaS_Project/frontend/src/pages/agencies/CompanyAgencies.tsx', 'w') as f:
    f.write(content)
