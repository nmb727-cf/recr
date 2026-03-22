import { useState } from 'react'
import {
  Table, Button, Typography, Tag, Space, Drawer, Form,
  Input, InputNumber, Select, message, Card, Divider, Checkbox, DatePicker, Upload, Empty
} from 'antd'
import { 
  CheckOutlined, 
  CloseOutlined, 
  EyeOutlined, 
  PlusOutlined,
  SearchOutlined,
  UploadOutlined,
  FileTextOutlined,
  InboxOutlined,
  CheckCircleFilled,
  CloseCircleFilled
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
  
  // New fields
  contact_person_name?: string
  contact_email?: string
  contact_phone?: string
  industry?: string
  contract_file_url?: string
  recruitment_policy_url?: string
  payment_terms?: string[]
  invited_by?: 'company' | 'agency'
  invited_via?: string
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

export default function AgencyClients() {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [addClientDrawerOpen, setAddClientDrawerOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  
  const [searchQuery, setSearchQuery] = useState('')
  const [searchLoading, setSearchLoading] = useState(false)
  const [foundTenant, setFoundTenant] = useState<{
    tenant_id: string
    name: string
    tenant_type: string
    industry: string
    email: string
  } | null>(null)
  const [searchError, setSearchError] = useState<string | null>(null)

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
      message.warning('Enter an email or phone number')
      return
    }
    setSearchLoading(true)
    setFoundTenant(null)
    setSearchError(null)
    try {
      const res = await agenciesApi.lookup(searchQuery)
      const tenant = res.data.data
      setFoundTenant(tenant)
      form.setFieldsValue({ 
        industry: tenant.industry || undefined 
      })
    } catch (err: any) {
      const msg = err.response?.data?.message || 'Not found'
      setSearchError(msg)
    } finally {
      setSearchLoading(false)
    }
  }

  const handleSubmit = async (values: any) => {
    if (!foundTenant) return
    try {
      setSubmitting(true)
      await agenciesApi.createRelationship({
        company_tenant_id: foundTenant.tenant_id,
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
      setAddClientDrawerOpen(false)
      setFoundTenant(null)
      setSearchQuery('')
      setSearchError(null)
      form.resetFields()
      queryClient.invalidateQueries({ queryKey: ['agency-client-relationships'] })
    } catch (err: any) {
      console.error('[AgencyClients] invite error:', err)
      message.error(err.response?.data?.message || 'Failed to send invitation')
    } finally {
      setSubmitting(false)
    }
  }

  const handleAccept = async (id: string) => {
    try {
      await agenciesApi.acceptRelationship(id)
      message.success('Client accepted')
      queryClient.invalidateQueries({ queryKey: ['agency-client-relationships'] })
    } catch (err) {
      console.error('[AgencyClients] Accept error:', err)
      message.error('Failed to accept client')
    }
  }

  const handleDecline = async (id: string) => {
    try {
      await agenciesApi.suspendRelationship(id)
      message.success('Invitation declined')
      queryClient.invalidateQueries({ queryKey: ['agency-client-relationships'] })
    } catch (err) {
      console.error('[AgencyClients] Decline error:', err)
      message.error('Failed to decline invitation')
    }
  }

  const columns: ColumnsType<AgencyRelationship> = [
    {
      title: 'Company Name',
      dataIndex: 'company_name',
      key: 'company_name',
      render: (text) => <span className="font-bold text-[#111827]">{text}</span>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusMap: Record<string, "success" | "warning" | "error" | "default"> = {
          active: 'success',
          pending: 'warning',
          suspended: 'error',
          terminated: 'default'
        }
        return <Tag color={statusMap[status] || 'default'}>{status?.toUpperCase() || 'UNKNOWN'}</Tag>
      }
    },
    {
      title: 'Commission %',
      dataIndex: 'commission_percentage',
      key: 'commission_percentage',
      render: (val, record) => `${val}${record.commission_type === 'percentage' ? '%' : ''}`,
    },
    {
      title: 'Connected since',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => dayjs(date).format('MMM D, YYYY'),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Button
          type="text"
          icon={<EyeOutlined />}
          onClick={(e) => {
            e.stopPropagation()
            setSelectedId(record.id)
          }}
        >
          View Details
        </Button>
      ),
    },
  ]

  const listContent = (
    <div className="p-6 h-full flex flex-col bg-white">
      <div className="flex justify-between items-center mb-6">
        <Title level={4} style={{ margin: 0, fontFamily: 'Outfit', fontWeight: 700, fontSize: 20 }}>My Clients</Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setAddClientDrawerOpen(true)}
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
              components={{
                header: {
                  cell: (props: any) => (
                    <th {...props} style={{ ...props.style, backgroundColor: 'transparent', color: '#9A3412', fontWeight: 600, fontSize: 11, textTransform: 'uppercase' }} />
                  )
                }
              }}
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
            locale={{ 
              emptyText: (
                <div className="py-12 flex flex-col items-center justify-center text-slate-400">
                  <InboxOutlined style={{ fontSize: 48 }} />
                  <p className="mt-4 text-sm font-medium">No active clients yet</p>
                  <p className="text-xs">Connect with companies to start receiving job assignments.</p>
                </div>
              )
            }}
          />
        </div>
      </div>
    </div>
  )

  const detailContent = selectedRelationship && (
    <div className="h-full flex flex-col bg-white border-l border-[#F3F4F6]">
      <div className="p-6 border-b border-slate-100 flex justify-between items-center">
        <div>
          <Title level={4} style={{ margin: 0, color: '#111827', fontWeight: 700 }}>{selectedRelationship?.company_name || 'N/A'}</Title>
          <div className="mt-1 flex items-center gap-2">
            <Tag color={
              selectedRelationship?.status === 'active' ? 'success' :
              selectedRelationship?.status === 'pending' ? 'warning' : 
              selectedRelationship?.status === 'suspended' ? 'error' : 'default'
            }>
              {selectedRelationship?.status?.toUpperCase() || 'UNKNOWN'}
            </Tag>
            <Text type="secondary" className="text-[12px]">Partner since {selectedRelationship?.created_at ? dayjs(selectedRelationship.created_at).format('MMM YYYY') : 'N/A'}</Text>
          </div>
        </div>
        <Button type="text" onClick={() => setSelectedId(null)}>Close</Button>
      </div>

      <div className="p-6 overflow-y-auto flex-1">
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
                  <div className="text-[14px] font-semibold text-[#111827]">{selectedRelationship?.contact_phone || 'N/A'}</div>
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
                  selectedRelationship.payment_terms.map(term => (
                    <Tag key={term} className="bg-slate-50 border-slate-200 text-slate-600 rounded-md m-0">{term}</Tag>
                  ))
                ) : <span className="text-slate-400 italic text-[13px]">No terms specified</span>}
              </Space>
            </div>
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
                  {selectedRelationship?.contract_start_date ? dayjs(selectedRelationship.contract_start_date).format('MMM D, YYYY') : 'Not set'}
                </div>
              </div>
              <div>
                <div className="text-[12px] text-slate-500">Contract End</div>
                <div className="text-[14px] font-semibold text-[#111827]">
                  {selectedRelationship?.contract_end_date ? dayjs(selectedRelationship.contract_end_date).format('MMM D, YYYY') : 'Not set'}
                </div>
              </div>
            </div>
          </section>

          <Divider style={{ margin: 0 }} />

          <section>
            <div className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider mb-2">Legal Documents</div>
            <div className="space-y-2">
              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100">
                <div className="flex items-center gap-2">
                  <FileTextOutlined className="text-blue-500" />
                  <span className="text-[13px] font-medium text-slate-700">Service Agreement</span>
                </div>
                {selectedRelationship?.contract_file_url ? (
                  <Button type="link" size="small" href={selectedRelationship.contract_file_url} target="_blank">View</Button>
                ) : <span className="text-[11px] text-slate-400">Not uploaded</span>}
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100">
                <div className="flex items-center gap-2">
                  <FileTextOutlined className="text-blue-500" />
                  <span className="text-[13px] font-medium text-slate-700">Compliance Doc</span>
                </div>
                {selectedRelationship?.recruitment_policy_url ? (
                  <Button type="link" size="small" href={selectedRelationship.recruitment_policy_url} target="_blank">View</Button>
                ) : <span className="text-[11px] text-slate-400">Not uploaded</span>}
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

          {selectedRelationship?.status === 'pending' && selectedRelationship?.invited_by === 'company' && (
            <div className="pt-6 border-t border-slate-100">
               <Space direction="vertical" className="w-full">
                <Button
                  type="primary"
                  block
                  icon={<CheckOutlined />}
                  onClick={() => handleAccept(selectedRelationship.id)}
                  className="bg-green-600 border-green-600 h-10 rounded-lg font-medium shadow-sm"
                >
                  Accept Client Invitation
                </Button>
                <Button
                  danger
                  block
                  icon={<CloseOutlined />}
                  onClick={() => handleDecline(selectedRelationship.id)}
                  className="h-10 rounded-lg font-medium"
                >
                  Decline Invitation
                </Button>
              </Space>
            </div>
          )}
        </div>
      </div>
    </div>
  )

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
        title={<span className="font-bold font-['Outfit'] text-lg">Add Client</span>}
        width={560}
        onClose={() => {
          setAddClientDrawerOpen(false)
          setFoundTenant(null)
          setSearchQuery('')
          setSearchError(null)
          form.resetFields()
        }}
        open={addClientDrawerOpen}
        extra={
          <Space>
            <Button onClick={() => setAddClientDrawerOpen(false)}>Cancel</Button>
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
            <Text strong className="block mb-3">Find Client</Text>
            
            <Input.Search
              placeholder="Email or phone number"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value)
                setFoundTenant(null)
                setSearchError(null)
              }}
              onSearch={handleSearch}
              enterButton={<Button loading={searchLoading}>Search</Button>}
              onPressEnter={handleSearch}
            />

            {/* Found result */}
            {foundTenant && (
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

            {/* Not found error */}
            {searchError && (
              <div className="mt-3 p-3 bg-red-50 border border-red-200 
                              rounded-lg flex items-center gap-2">
                <CloseCircleFilled className="text-red-500" />
                <Text type="danger" className="text-sm">{searchError}</Text>
              </div>
            )}
          </div>

          {foundTenant && (
            <div className="animate-in fade-in slide-in-from-top-2 duration-300">
              <div className="p-4 border border-slate-100 rounded-xl">
                <Title level={5} className="!mb-4">Contract Details</Title>

                <div className="grid grid-cols-2 gap-4">
                  <Form.Item name="contact_person_name" label="Contact Person">
                    <Input placeholder="Full name" />
                  </Form.Item>
                  <Form.Item name="industry" label="Industry">
                    <Select placeholder="Select industry">
                      {INDUSTRY_OPTIONS.map(opt => <Option key={opt} value={opt}>{opt}</Option>)}
                    </Select>
                  </Form.Item>
                </div>

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

                <Button
                  type="primary"
                  htmlType="submit"
                  loading={submitting}
                  block
                  style={{ height: 44, background: '#4F46E5' }}
                  className="mt-4"
                >
                  Send Invitation to {foundTenant?.name || 'Client'}
                </Button>
              </div>
            </div>
          )}
        </Form>
      </Drawer>
    </>
  )
}
