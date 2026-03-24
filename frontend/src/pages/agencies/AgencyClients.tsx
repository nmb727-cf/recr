import { useState } from 'react'
import {
  Table, Button, Typography, Tag, Space, Drawer, Form,
  Input, InputNumber, Select, message, Card, Divider,
  Dropdown, DatePicker, Checkbox
} from 'antd'
import { 
  CheckOutlined, 
  CloseOutlined, 
  EyeOutlined, 
  PlusOutlined,
  CheckCircleFilled,
  MailOutlined,
  LinkOutlined,
  SendOutlined,
  MoreOutlined,
  InfoCircleOutlined,
  EditOutlined,
  FileTextOutlined
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useQueryClient } from '@tanstack/react-query'
import { agenciesApi } from '@/api/agencies'
import { useAuth } from '@/hooks/useAuth'
import { StandardSplitView } from '@/components/layout/StandardSplitView'
import { cn } from '@/utils/cn'
import PaymentTermsField from '@/components/agencies/PaymentTermsField'
import PhoneInput, { formatPhoneDisplay, getPhoneValidationRule, PhoneValue } from '@/components/common/PhoneInput'

dayjs.extend(relativeTime)

const { Title, Text } = Typography
const { Option } = Select

interface AgencyRelationship {
  id: string
  agency_tenant_id: string
  company_tenant_id: string
  agency_name: string
  company_name: string
  status: 'pending' | 'active' | 'suspended' | 'terminated'
  commission_percentage: number
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
  email_tracking_id?: string
  their_ats_url?: string
  last_activity_at?: string
}

const INDUSTRY_OPTIONS = [
  'Technology', 'Finance', 'Healthcare', 'Manufacturing', 'Retail', 
  'Energy', 'Education', 'Construction', 'Logistics', 'Real Estate', 
  'Consulting', 'Other'
]

function getClientDisplayName(r: AgencyRelationship): string {
  if (!r.company_tenant_id || r.company_name === 'Unknown Company' || !r.company_name) {
    if (r.contact_person_name) return r.contact_person_name
    if (r.contact_email) return r.contact_email.split('@')[0]
    return 'Unnamed Client'
  }
  return r.company_name
}

function getConnectionBadge(r: AgencyRelationship) {
  const type = r.connection_type || 'full_full'
  if (type === 'client_guest') {
    if (r.status === 'active') return { color: 'blue', label: 'Portal Active' }
    if (r.status === 'pending') return { color: 'gold', label: 'Invite Pending' }
    return { color: 'red', label: 'Invite Expired' }
  }
  if (type === 'email_tracking') return { color: 'purple', label: 'Email Tracking' }
  if (type === 'offline') return { color: 'default', label: 'Offline' }
  if (r.status === 'active') return { color: 'green', label: 'Connected' }
  if (r.status === 'pending') return { color: 'gold', label: 'Pending' }
  if (r.status === 'suspended') return { color: 'orange', label: 'Suspended' }
  return { color: 'default', label: r.status }
}

export default function AgencyClients() {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [addClientDrawerOpen, setAddClientDrawerOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  
  const [searchQuery, setSearchQuery] = useState('')
  const [searchLoading, setSearchLoading] = useState(false)
  const [lookupResult, setLookupResult] = useState<any>(null)
  
  const [addPath, setAddPath] = useState<'email' | 'offline' | 'portal' | null>(null)
  const [successData, setSuccessData] = useState<any>(null)

  const [editDrawerOpen, setEditDrawerOpen] = useState(false)
  const [editingRelationship, setEditingRelationship] = useState<AgencyRelationship | null>(null)
  const [editForm] = Form.useForm()
  const [editSubmitting, setEditSubmitting] = useState(false)

  const [form] = Form.useForm()

  const { data, isLoading } = useApiQuery(
    ['agency-client-relationships'],
    () => agenciesApi.listClientRelationships()
  )

  const relationshipsData = (data as any)?.clients ?? []
  const relationships = (Array.isArray(relationshipsData) ? relationshipsData : []) as AgencyRelationship[]

  const pendingInvites = relationships.filter(
    r => r?.status === 'pending' && r?.agency_tenant_id === user?.tenant_id && r?.invited_by === 'company'
  )

  const activeClients = relationships.filter(r => r?.status !== 'pending' || r?.invited_by === 'agency')

  const selectedRelationship = relationships.find(r => r.id === selectedId)

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      message.warning('Enter an email address')
      return
    }
    setSearchLoading(true)
    setLookupResult(null)
    setAddPath(null)
    try {
      const res = await agenciesApi.lookup(searchQuery)
      setLookupResult(res.data.data)
      form.setFieldsValue({ contact_email: searchQuery })
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Search failed')
    } finally {
      setSearchLoading(false)
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      setSubmitting(true)
      const payload = {
        contact_person_name: values.contact_person_name,
        contact_email: values.contact_email || searchQuery,
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
      }

      if (lookupResult?.found) {
        await agenciesApi.createRelationship({
          company_tenant_id: lookupResult.tenant_id,
          ...payload
        })
      } else {
        if (addPath === 'email') {
          await agenciesApi.createEmailTracking({
            client_name: values.company_name,
            contact_name: values.contact_person_name, // Backend expects contact_name
            ...payload
          })
        } else if (addPath === 'offline') {
          await agenciesApi.createOfflineClient({
            client_name: values.company_name,
            contact_name: values.contact_person_name,
            their_ats_url: values.their_ats_url,
            receive_via_email: true,
            ...payload
          })
        } else if (addPath === 'portal') {
          await agenciesApi.createGuestPortal({
            portal_type: 'client_guest',
            name: values.company_name,
            contact_name: values.contact_person_name,
            invite_message: values.invite_message,
            ...payload
          })
        }
      }
      
      setSuccessData({
        name: values.company_name || lookupResult?.name,
        path: addPath,
        email: values.contact_email || searchQuery,
      })
      queryClient.invalidateQueries({ queryKey: ['agency-client-relationships'] })
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Action failed')
    } finally {
      setSubmitting(false)
    }
  }

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
      commission_percentage: rel.commission_percentage ?? null,
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
      })
      message.success('Client details updated')
      setEditDrawerOpen(false)
      setEditingRelationship(null)
      editForm.resetFields()
      queryClient.invalidateQueries({ queryKey: ['agency-client-relationships'] })
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to update')
    } finally {
      setEditSubmitting(false)
    }
  }

  const handleAccept = async (id: string) => {
    try {
      await agenciesApi.acceptRelationship(id)
      message.success('Client accepted')
      queryClient.invalidateQueries({ queryKey: ['agency-client-relationships'] })
    } catch (err) {
      message.error('Failed to accept client')
    }
  }

  const handleDecline = async (id: string) => {
    try {
      await agenciesApi.suspendRelationship(id)
      message.success('Invitation declined')
      queryClient.invalidateQueries({ queryKey: ['agency-client-relationships'] })
    } catch (err) {
      message.error('Failed to decline invitation')
    }
  }

  const columns: ColumnsType<AgencyRelationship> = [
    {
      title: 'Client',
      key: 'client',
      render: (_, record) => {
        const name = getClientDisplayName(record)
        return (
          <div>
            <div className="font-semibold text-[#111827] text-[14px]">{name}</div>
            <div className="text-[12px] text-slate-400 mt-0.5">
              {record.contact_email || '—'}
            </div>
          </div>
        )
      }
    },
    {
      title: 'Connection',
      key: 'connection',
      render: (_, record) => {
        const badge = getConnectionBadge(record)
        return <Tag color={badge.color}>{badge.label}</Tag>
      }
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
      }
    },
    {
      title: 'Since',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => (
        <span className="text-[13px] text-slate-500">
          {dayjs(date).format('MMM D, YYYY')}
        </span>
      )
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
      )
    },
  ]

  const listContent = (
    <div className="p-6 h-full flex flex-col bg-white">
      <div className="flex justify-between items-center mb-6">
        <Title level={4} style={{ margin: 0, fontFamily: 'Outfit', fontWeight: 700, fontSize: 20 }}>My Clients</Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setAddClientDrawerOpen(true)
            setSuccessData(null)
            setLookupResult(null)
            setSearchQuery('')
            form.resetFields()
          }}
          className="bg-[#4F46E5] hover:bg-[#3730A3] border-none h-10 px-6 rounded-lg font-semibold"
        >
          Add Client
        </Button>
      </div>

      <div className="flex-1 overflow-auto space-y-6">
        {pendingInvites.length > 0 && (
          <Card
            title={<span className="font-bold text-slate-800">Pending Invitations</span>}
            className="border-orange-100 bg-orange-50/20 rounded-xl overflow-hidden"
            bodyStyle={{ padding: 0 }}
          >
            <Table
              dataSource={pendingInvites}
              pagination={false}
              rowKey="id"
              columns={[
                { title: 'Company', dataIndex: 'company_name', render: (t) => <b className="text-[#111827]">{t}</b> },
                { title: 'Invited', dataIndex: 'created_at', render: (d) => dayjs(d).fromNow() },
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
                        className="bg-green-600 border-green-600 rounded-md"
                      >
                        Accept
                      </Button>
                      <Button
                        danger
                        size="small"
                        icon={<CloseOutlined />}
                        onClick={() => handleDecline(r.id)}
                        className="rounded-md"
                      >
                        Decline
                      </Button>
                    </Space>
                  )
                }
              ]}
            />
          </Card>
        )}

        <div className="border border-slate-100 rounded-xl shadow-sm overflow-hidden bg-white">
          <Table
            dataSource={activeClients}
            columns={columns}
            rowKey="id"
            loading={isLoading}
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
          />
        </div>
      </div>
    </div>
  )

  const detailContent = selectedRelationship && (
    <div className="h-full flex flex-col bg-white border-l border-[#F3F4F6]">
      <div className="p-6 border-b border-slate-100 flex justify-between items-start">
        <div className="flex-1 min-w-0">
          <Title level={4} style={{ margin: 0, color: '#111827', fontWeight: 700 }}>
            {getClientDisplayName(selectedRelationship)}
          </Title>
          <div className="mt-1 flex items-center gap-2 flex-wrap">
            <Tag color={getConnectionBadge(selectedRelationship).color}>
              {getConnectionBadge(selectedRelationship).label}
            </Tag>
            <Text type="secondary" className="text-[12px]">
              Added {dayjs(selectedRelationship.created_at).format('MMM D, YYYY')}
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
        {selectedRelationship.connection_type === 'client_guest' && selectedRelationship.status === 'pending' && (
          <div className="mb-6 p-4 bg-amber-50 rounded-xl border border-amber-100 flex gap-3">
            <InfoCircleOutlined className="text-amber-500 mt-1" />
            <div>
              <div className="text-[13px] font-bold text-amber-900">Invite Pending</div>
              <div className="text-[12px] text-amber-700 mt-0.5">
                The client hasn't accepted the portal invitation yet. You can still submit candidates.
              </div>
            </div>
          </div>
        )}

        <div className="space-y-6">
          <section>
            <div className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider mb-2">Company Contact</div>
            <div className="space-y-3">
              <div>
                <div className="text-[12px] text-slate-500">Point of Contact</div>
                <div className="text-[14px] font-semibold text-[#111827]">{selectedRelationship?.contact_person_name || 'N/A'}</div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-[12px] text-slate-500">Email</div>
                  <div className="text-[14px] font-semibold text-[#111827]">{selectedRelationship?.contact_email || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-[12px] text-slate-500">Phone</div>
                  <div className="text-[14px] font-semibold text-[#111827]">
                    {selectedRelationship?.contact_phone_number
                      ? formatPhoneDisplay(selectedRelationship.contact_country_code || 'IN', selectedRelationship.contact_phone_number)
                      : selectedRelationship?.contact_phone || '—'}
                  </div>
                </div>
              </div>
              <div>
                <div className="text-[12px] text-slate-500">Industry</div>
                <div className="text-[14px] font-semibold text-[#111827]">{selectedRelationship?.industry || 'N/A'}</div>
              </div>
            </div>
          </section>

          <Divider style={{ margin: 0 }} />

          <section>
            <div className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider mb-2">Fee Structure</div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-[12px] text-slate-500">Commission</div>
                <div className="text-[14px] font-semibold text-[#111827]">
                  {selectedRelationship?.commission_percentage ?? '0'}
                  {selectedRelationship?.commission_type === 'percentage' ? '%' : ' Fixed'}
                </div>
              </div>
              <div>
                <div className="text-[12px] text-slate-500">Billing Type</div>
                <div className="text-[14px] font-semibold text-[#111827] capitalize">{selectedRelationship?.commission_type || 'N/A'}</div>
              </div>
            </div>
            <div className="mt-3">
              <div className="text-[12px] text-slate-500 mb-1">Payment Terms</div>
              <Space wrap size={[4, 4]}>
                {Array.isArray(selectedRelationship?.payment_terms) && selectedRelationship.payment_terms.length > 0 ? (
                  selectedRelationship.payment_terms.filter(t => t !== 'custom').map(term => (
                    <Tag key={term} className="bg-slate-50 border-slate-200 text-slate-600 rounded-md m-0">{term}</Tag>
                  ))
                ) : <span className="text-slate-400 italic text-[13px]">No standard terms specified</span>}
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

          <section>
            <div className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider mb-2">Performance Targets</div>
            <div className="grid grid-cols-2 gap-4 mb-3">
              <div>
                <div className="text-[12px] text-slate-500">Target Submission</div>
                <div className="text-[14px] font-semibold text-[#111827]">{selectedRelationship?.sla_submission_hours || 48}h</div>
              </div>
              <div>
                <div className="text-[12px] text-slate-500">Feedback Expectation</div>
                <div className="text-[14px] font-semibold text-[#111827]">{selectedRelationship?.sla_feedback_hours || 72}h</div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-[12px] text-slate-500">Contract Start</div>
                <div className="text-[14px] font-semibold text-[#111827]">
                  {selectedRelationship?.contract_start_date ? dayjs(selectedRelationship.contract_start_date).format('MMM D, YYYY') : '—'}
                </div>
              </div>
              <div>
                <div className="text-[12px] text-slate-500">Contract End</div>
                <div className="text-[14px] font-semibold text-[#111827]">
                  {selectedRelationship?.contract_end_date ? dayjs(selectedRelationship.contract_end_date).format('MMM D, YYYY') : '—'}
                </div>
              </div>
            </div>
          </section>

          <Divider style={{ margin: 0 }} />

          <section>
            <div className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider mb-2">Collaboration Notes</div>
            <div className="p-3 bg-slate-50 rounded-lg text-slate-600 text-[13px] leading-relaxed italic">
              {selectedRelationship?.notes || 'No notes shared for this client relationship.'}
            </div>
          </section>
        </div>
      </div>
    </div>
  )

  const contractDetailsFields = (
    <>
      <Divider titlePlacement="left" plain><span className="text-[12px] text-slate-400 font-medium">Contract Details (Optional)</span></Divider>
      
      <Form.Item name="industry" label="Industry">
        <Select placeholder="Select industry">
          {INDUSTRY_OPTIONS.map(opt => <Option key={opt} value={opt}>{opt}</Option>)}
        </Select>
      </Form.Item>

      <div className="grid grid-cols-2 gap-4">
        <Form.Item name="commission_percentage" label="Commission">
          <InputNumber className="w-full" placeholder="20" />
        </Form.Item>
        <Form.Item name="commission_type" label="Type" initialValue="percentage">
          <Select>
            <Option value="percentage">Percentage (%)</Option>
            <Option value="fixed">Fixed Amount</Option>
          </Select>
        </Form.Item>
      </div>

      <Form.Item name="payment_terms_field" label="Payment Terms">
        <PaymentTermsField />
      </Form.Item>

      <div className="grid grid-cols-2 gap-4">
        <Form.Item name="sla_submission_hours" label="SLA Submission (hrs)" initialValue={48}>
          <InputNumber className="w-full" />
        </Form.Item>
        <Form.Item name="sla_feedback_hours" label="SLA Feedback (hrs)" initialValue={72}>
          <InputNumber className="w-full" />
        </Form.Item>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Form.Item name="contract_start_date" label="Start Date">
          <DatePicker className="w-full" />
        </Form.Item>
        <Form.Item name="contract_end_date" label="End Date">
          <DatePicker className="w-full" />
        </Form.Item>
      </div>

      <Form.Item name="notes" label="Internal Notes">
        <Input.TextArea rows={2} />
      </Form.Item>
    </>
  )

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
        title={<span className="font-bold font-['Outfit'] text-lg">Add Client</span>}
        width={560}
        onClose={() => setAddClientDrawerOpen(false)}
        open={addClientDrawerOpen}
        footer={null}
      >
        {!successData ? (
          <div className="space-y-6">
            <div>
              <Text className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider block mb-2">Search by email</Text>
              <div className="flex gap-2">
                <Input 
                  placeholder="client@company.com" 
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  onPressEnter={handleSearch}
                  className="h-10 rounded-lg"
                />
                <Button 
                  type="primary" 
                  onClick={handleSearch} 
                  loading={searchLoading}
                  className="bg-[#4F46E5] h-10 px-6 rounded-lg"
                >
                  Search
                </Button>
              </div>
            </div>

            {lookupResult && (
              <div className="space-y-6 animate-in fade-in slide-in-from-top-4 duration-300">
                {lookupResult.found ? (
                  <Card className="border-green-100 bg-green-50/30 rounded-xl">
                    <div className="flex items-start gap-3">
                      <CheckCircleFilled className="text-green-500 mt-1" />
                      <div className="flex-1">
                        <Text strong className="block text-lg">{lookupResult.name}</Text>
                        <Text type="secondary">{lookupResult.tenant_type} · {lookupResult.email}</Text>
                        
                        <Form form={form} layout="vertical" onFinish={handleSubmit} className="mt-4">
                          <Form.Item name="contact_person_name" label="Contact Person Name" rules={[{ required: true }]}>
                            <Input placeholder="John Doe" />
                          </Form.Item>
                          <Form.Item name="contact_email" label="Contact Email" rules={[{ required: true, message: "Email is required" }, { type: "email", message: "Enter a valid email address" }]} initialValue={lookupResult.email}>
                            <Input />
                          </Form.Item>
                          <Form.Item
                            name="contact_phone_field"
                            label="Contact Phone"
                            rules={[{ required: true, message: 'Phone is required' }, getPhoneValidationRule()]}
                          >
                            <PhoneInput placeholder="Phone number" />
                          </Form.Item>
                          
                          {contractDetailsFields}

                          <Button 
                            type="primary" 
                            htmlType="submit"
                            block 
                            className="mt-4 bg-[#4F46E5] h-10 rounded-lg"
                            loading={submitting}
                          >
                            Send Connection Request
                          </Button>
                        </Form>
                      </div>
                    </div>
                  </Card>
                ) : (
                  <>
                    <Card className="border-blue-100 bg-blue-50/30 rounded-xl py-3">
                      <Space>
                        <InfoCircleOutlined className="text-blue-500" />
                        <Text strong>Not on RecruitOS yet</Text>
                      </Space>
                    </Card>

                    <div className="space-y-3">
                      <Text className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider block">Choose connection path</Text>
                      
                      <div 
                        className={cn(
                          "border rounded-xl p-4 cursor-pointer transition-all",
                          addPath === 'email' ? "border-[#4F46E5] bg-[#EEF2FF]" : "border-slate-200 hover:border-[#4F46E5] hover:bg-[#EEF2FF]"
                        )}
                        onClick={() => setAddPath('email')}
                      >
                        <div className="flex items-center gap-3">
                          <MailOutlined className={cn("text-xl", addPath === 'email' ? "text-[#4F46E5]" : "text-slate-400")} />
                          <div>
                            <Text strong className="block">They email us requirements</Text>
                            <Text type="secondary" className="text-xs">Auto-detect job requirements from their emails</Text>
                          </div>
                        </div>
                      </div>

                      <div 
                        className={cn(
                          "border rounded-xl p-4 cursor-pointer transition-all",
                          addPath === 'offline' ? "border-[#4F46E5] bg-[#EEF2FF]" : "border-slate-200 hover:border-[#4F46E5] hover:bg-[#EEF2FF]"
                        )}
                        onClick={() => setAddPath('offline')}
                      >
                        <div className="flex items-center gap-3">
                          <LinkOutlined className={cn("text-xl", addPath === 'offline' ? "text-[#4F46E5]" : "text-slate-400")} />
                          <div>
                            <Text strong className="block">They have their own ATS or portal</Text>
                            <Text type="secondary" className="text-xs">Track this client manually, no invite needed</Text>
                          </div>
                        </div>
                      </div>

                      <div 
                        className={cn(
                          "border rounded-xl p-4 cursor-pointer transition-all",
                          addPath === 'portal' ? "border-[#4F46E5] bg-[#EEF2FF]" : "border-slate-200 hover:border-[#4F46E5] hover:bg-[#EEF2FF]"
                        )}
                        onClick={() => setAddPath('portal')}
                      >
                        <div className="flex items-center gap-3">
                          <SendOutlined className={cn("text-xl", addPath === 'portal' ? "text-[#4F46E5]" : "text-slate-400")} />
                          <div>
                            <Text strong className="block">Invite them to a free client portal</Text>
                            <Text type="secondary" className="text-xs">Give them visibility into submissions and pipeline</Text>
                          </div>
                        </div>
                      </div>
                    </div>

                    {addPath && (
                      <Form 
                        form={form} 
                        layout="vertical" 
                        onFinish={handleSubmit}
                        className="animate-in fade-in slide-in-from-top-2 duration-300 pt-4"
                      >
                        <Form.Item name="company_name" label="Company Name" rules={[{ required: true }]}>
                          <Input placeholder="Acme Corp" />
                        </Form.Item>
                        
                        <Form.Item name="contact_person_name" label="Contact Person Name" rules={[{ required: true }]}>
                          <Input placeholder="John Doe" />
                        </Form.Item>
                        
                        <Form.Item name="contact_email" label="Contact Email" rules={[{ required: true, message: "Email is required" }, { type: "email", message: "Enter a valid email address" }]} initialValue={searchQuery}>
                          <Input />
                        </Form.Item>
                        
                        <Form.Item
                          name="contact_phone_field"
                          label="Contact Phone"
                          rules={[{ required: true, message: 'Phone is required' }, getPhoneValidationRule()]}
                        >
                          <PhoneInput placeholder="Phone number" />
                        </Form.Item>

                        {addPath === 'email' && (
                          <Form.Item label="Email Domain" tooltip="We'll monitor emails from this domain">
                            <Input value={`@${searchQuery.split('@')[1] || searchQuery}`} readOnly className="bg-slate-50" />
                          </Form.Item>
                        )}

                        {addPath === 'offline' && (
                          <Form.Item name="their_ats_url" label="Their portal or ATS URL">
                            <Input placeholder="https://jobs.acme.com" />
                          </Form.Item>
                        )}

                        {addPath === 'portal' && (
                          <>
                            <Form.Item name="invite_message" label="Invite Message" initialValue={`Hi, we use RecruitOS to manage your hiring requirements. Here's a free portal to track candidates we submit to you.`}>
                              <Input.TextArea rows={4} />
                            </Form.Item>
                            <div className="p-3 bg-amber-50 rounded-lg flex gap-2 mb-6">
                              <InfoCircleOutlined className="text-amber-500 mt-1" />
                              <Text className="text-xs text-amber-700">They can ignore this invite. You can still work with them normally.</Text>
                            </div>
                          </>
                        )}

                        {contractDetailsFields}

                        <Button 
                          type="primary" 
                          htmlType="submit" 
                          block 
                          loading={submitting}
                          className="bg-[#4F46E5] h-12 rounded-lg text-lg font-semibold"
                        >
                          {addPath === 'email' ? 'Set Up Email Tracking' : 
                           addPath === 'offline' ? 'Save as Offline Client' : 'Send Invite'}
                        </Button>
                      </Form>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-12 px-6 animate-in zoom-in duration-300">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckOutlined className="text-3xl text-green-600" />
            </div>
            <Title level={3}>{successData.name} added</Title>
            
            <div className="bg-slate-50 rounded-xl p-6 my-8 text-left">
              {successData.path === 'email' && (
                <Text>We'll auto-detect requirements from <b>@{successData.email.split('@')[1] || successData.email}</b></Text>
              )}
              {successData.path === 'offline' && (
                <Text>Added as offline client. You can invite them later.</Text>
              )}
              {successData.path === 'portal' && (
                <div className="space-y-2">
                  <Text className="block">Invite sent to <b>{successData.email}</b></Text>
                  <Text className="block">Status: <Tag color="warning">Invite Pending</Tag></Text>
                  <Text type="secondary" className="text-xs block mt-4 italic">You can start assigning jobs right away.</Text>
                </div>
              )}
              {!successData.path && (
                <Text>Connection request sent to <b>{successData.email}</b></Text>
              )}
            </div>

            <Button 
              type="primary" 
              block 
              onClick={() => {
                setAddClientDrawerOpen(false)
                queryClient.invalidateQueries({ queryKey: ['agency-client-relationships'] })
              }}
              className="bg-[#4F46E5] h-12 rounded-xl text-lg font-semibold"
            >
              Go to Client List
            </Button>
          </div>
        )}
      </Drawer>

      <Drawer
        title={<span className="font-bold font-['Outfit'] text-lg">Edit Client Details</span>}
        width={500}
        onClose={() => setEditDrawerOpen(false)}
        open={editDrawerOpen}
        footer={null}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleEditSubmit}
          className="space-y-4"
        >
          <Form.Item name="contact_person_name" label="Contact Person Name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          
          <Form.Item name="contact_email" label="Contact Email" rules={[{ required: true, message: "Email is required" }, { type: "email", message: "Enter a valid email address" }]}>
            <Input />
          </Form.Item>
          
          <Form.Item
            name="contact_phone_field"
            label="Contact Phone"
            rules={[getPhoneValidationRule()]}
          >
            <PhoneInput placeholder="Phone number" />
          </Form.Item>

          <Form.Item name="industry" label="Industry">
            <Select placeholder="Select industry">
              {INDUSTRY_OPTIONS.map(opt => <Option key={opt} value={opt}>{opt}</Option>)}
            </Select>
          </Form.Item>

          <Divider titlePlacement="left" plain><span className="text-[12px] text-slate-400 font-medium">Contract Terms</span></Divider>

          <div className="grid grid-cols-2 gap-4">
            <Form.Item name="commission_percentage" label="Commission">
              <InputNumber className="w-full" />
            </Form.Item>
            <Form.Item name="commission_type" label="Type">
              <Select>
                <Option value="percentage">Percentage (%)</Option>
                <Option value="fixed">Fixed Amount</Option>
              </Select>
            </Form.Item>
          </div>

          <Form.Item name="payment_terms_field" label="Payment Terms">
            <PaymentTermsField />
          </Form.Item>

          <div className="grid grid-cols-2 gap-4">
            <Form.Item name="sla_submission_hours" label="SLA Submission (hrs)">
              <InputNumber className="w-full" />
            </Form.Item>
            <Form.Item name="sla_feedback_hours" label="SLA Feedback (hrs)">
              <InputNumber className="w-full" />
            </Form.Item>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Form.Item name="contract_start_date" label="Start Date">
              <DatePicker className="w-full" />
            </Form.Item>
            <Form.Item name="contract_end_date" label="End Date">
              <DatePicker className="w-full" />
            </Form.Item>
          </div>

          <Form.Item name="notes" label="Internal Notes">
            <Input.TextArea rows={4} />
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
        </Form>
      </Drawer>
    </>
  )
}
