import { useState } from 'react'
import {
  Table, Button, Typography, Tag, Space, Drawer, Form,
  Input, message, Card, Divider, Dropdown
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
  InfoCircleOutlined
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

  connection_type?: 'full_full' | 'agency_guest' | 'client_guest' | 'email_tracking' | 'offline'
  guest_portal_id?: string
  email_tracking_id?: string
  their_ats_url?: string
  last_activity_at?: string
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
      if (!res.data.data.found) {
        // Pre-fill slug if not found
        form.setFieldsValue({ slug: res.data.data.suggested_slug })
      }
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Search failed')
    } finally {
      setSearchLoading(false)
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      setSubmitting(true)
      if (lookupResult?.found) {
        // Scenario 1: Both full tenants
        await agenciesApi.createRelationship({
          company_tenant_id: lookupResult.tenant_id,
          contact_email: lookupResult.email,
          ...values
        })
      } else {
        // Scenario 3: Branching paths
        if (addPath === 'email') {
          await agenciesApi.createEmailTracking({
            client_name: values.company_name,
            contact_email: searchQuery,
            contact_name: values.contact_name,
            notes: values.notes
          })
        } else if (addPath === 'offline') {
          await agenciesApi.createOfflineClient({
            client_name: values.company_name,
            contact_email: searchQuery,
            contact_name: values.contact_name,
            contact_phone: values.contact_phone,
            their_ats_url: values.their_ats_url,
            notes: values.notes,
            receive_via_email: true
          })
        } else if (addPath === 'portal') {
          await agenciesApi.createGuestPortal({
            portal_type: 'client_guest',
            name: values.company_name,
            contact_email: searchQuery,
            contact_name: values.contact_name,
            contact_phone: values.contact_phone,
            invite_message: values.invite_message,
            slug: values.slug
          })
        }
      }
      
      setSuccessData({
        name: values.company_name || lookupResult?.name,
        path: addPath,
        email: searchQuery,
        slug: values.slug
      })
      queryClient.invalidateQueries({ queryKey: ['agency-client-relationships'] })
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Action failed')
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
        let dotColor = '#CBD5E1' // Gray
        if (record.connection_type === 'full_full' || (record.connection_type === 'client_guest' && record.status === 'active')) {
          dotColor = '#10B981' // Green
        } else if (record.status === 'pending') {
          dotColor = '#F59E0B' // Yellow
        } else if (record.connection_type === 'email_tracking') {
          dotColor = '#6366F1' // Indigo
        } else if (record.connection_type === 'offline') {
          dotColor = '#64748B' // Slate
        }

        return (
          <Space>
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: dotColor }} />
            <Text strong className="text-[#111827]">{record.company_name || 'Unnamed Client'}</Text>
          </Space>
        )
      }
    },
    {
      title: 'Connection',
      key: 'connection',
      render: (_, record) => {
        const type = record.connection_type || 'full_full'
        if (type === 'full_full') return <Tag color="green">Connected</Tag>
        if (type === 'client_guest') {
          if (record.status === 'active') return <Tag color="blue">Portal Active</Tag>
          if (record.status === 'pending') return <Tag color="warning">Invite Pending</Tag>
          return <Tag color="error">Invite Expired</Tag>
        }
        if (type === 'email_tracking') return <Tag color="indigo">Email Tracking</Tag>
        if (type === 'offline') return <Tag color="default">Offline</Tag>
        return <Tag>{type}</Tag>
      }
    },
    {
      title: 'Contact Email',
      dataIndex: 'contact_email',
      key: 'contact_email',
      render: (email) => email || '—'
    },
    {
      title: 'Jobs',
      key: 'jobs',
      render: () => '—'
    },
    {
      title: '',
      key: 'actions',
      width: 50,
      render: (_, record) => (
        <Dropdown
          menu={{
            items: [
              { key: 'view', label: 'View Profile', icon: <EyeOutlined /> },
              { key: 'assign', label: 'Assign Job', icon: <PlusOutlined />, disabled: record.status !== 'active' },
              { key: 'message', label: 'Message', icon: <MailOutlined />, disabled: record.status !== 'active' },
            ],
            onClick: ({ key }) => {
              if (key === 'view') setSelectedId(record.id)
            }
          }}
          trigger={['click']}
        >
          <Button type="text" icon={<MoreOutlined />} onClick={e => e.stopPropagation()} />
        </Dropdown>
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
          onClick={() => {
            setAddClientDrawerOpen(true)
            setSuccessData(null)
            setLookupResult(null)
            setSearchQuery('')
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
        onClose={() => setAddClientDrawerOpen(false)}
        open={addClientDrawerOpen}
        footer={null}
      >
        {!successData ? (
          <div className="space-y-6">
            {/* Section A: Search */}
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
                      <div>
                        <Text strong className="block text-lg">{lookupResult.name}</Text>
                        <Text type="secondary">{lookupResult.tenant_type} · {lookupResult.email}</Text>
                        <Button 
                          type="primary" 
                          block 
                          className="mt-4 bg-[#4F46E5] h-10 rounded-lg"
                          onClick={() => handleSubmit({})}
                          loading={submitting}
                        >
                          Send Connection Request
                        </Button>
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
                      
                      {/* Path 1: Email Tracking */}
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

                      {/* Path 2: Offline */}
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

                      {/* Path 3: Guest Portal */}
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

                    {/* Conditional Form Fields */}
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
                        <div className="grid grid-cols-2 gap-4">
                          <Form.Item name="contact_name" label="Contact Name">
                            <Input placeholder="John Doe" />
                          </Form.Item>
                          {addPath !== 'email' && (
                            <Form.Item name="contact_phone" label="Contact Phone">
                              <Input placeholder="+1..." />
                            </Form.Item>
                          )}
                        </div>

                        {addPath === 'email' && (
                          <Form.Item label="Email Domain" tooltip="We'll monitor emails from this domain">
                            <Input value={`@${searchQuery.split('@')[1]}`} readOnly className="bg-slate-50" />
                          </Form.Item>
                        )}

                        {addPath === 'offline' && (
                          <Form.Item name="their_ats_url" label="Their portal or ATS URL">
                            <Input placeholder="https://jobs.acme.com" />
                          </Form.Item>
                        )}

                        {addPath === 'portal' && (
                          <>
                            <Form.Item name="slug" label="Portal URL" rules={[{ required: true }]}>
                              <Input addonAfter=".recruitos.com" placeholder="acme-corp" />
                            </Form.Item>
                            <Form.Item name="invite_message" label="Invite Message" initialValue={`Hi, we use RecruitOS to manage your hiring requirements. Here's a free portal to track candidates we submit to you.`}>
                              <Input.TextArea rows={4} />
                            </Form.Item>
                            <div className="p-3 bg-amber-50 rounded-lg flex gap-2 mb-6">
                              <InfoCircleOutlined className="text-amber-500 mt-1" />
                              <Text className="text-xs text-amber-700">They can ignore this invite. You can still work with them normally.</Text>
                            </div>
                          </>
                        )}

                        <Form.Item name="notes" label="Internal Notes">
                          <Input.TextArea rows={2} />
                        </Form.Item>

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
          /* Success State */
          <div className="text-center py-12 px-6 animate-in zoom-in duration-300">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckOutlined className="text-3xl text-green-600" />
            </div>
            <Title level={3}>{successData.name} added</Title>
            
            <div className="bg-slate-50 rounded-xl p-6 my-8 text-left">
              {successData.path === 'email' && (
                <Text>We'll auto-detect requirements from <b>@{successData.email.split('@')[1]}</b></Text>
              )}
              {successData.path === 'offline' && (
                <Text>Added as offline client. You can invite them later.</Text>
              )}
              {successData.path === 'portal' && (
                <div className="space-y-2">
                  <Text className="block">Invite sent to <b>{successData.email}</b></Text>
                  <Text className="block">Portal: <b>{successData.slug}.recruitos.com</b></Text>
                  <Text className="block">Status: <Tag color="warning">Invite Pending</Tag></Text>
                  <Text type="secondary" className="text-xs block mt-4 italic">You can start assigning jobs right away.</Text>
                </div>
              )}
            </div>

            <Button 
              type="primary" 
              block 
              onClick={() => setAddClientDrawerOpen(false)}
              className="bg-[#4F46E5] h-12 rounded-xl text-lg font-semibold"
            >
              Go to Client List
            </Button>
          </div>
        )}
      </Drawer>
    </>
  )
}
