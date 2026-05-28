import { useState } from 'react'
import {
  Button, Drawer, Form, Input, Select, Switch,
  InputNumber, Typography, Card, Space, Row, Col,
  message, Table, Tag, Popconfirm
} from 'antd'
import {
  LinkOutlined,
  CopyOutlined,
  MailOutlined,
  WhatsAppOutlined,
  HistoryOutlined,
  StopOutlined,
  PlusOutlined
} from '@ant-design/icons'
import { QRCodeSVG } from 'qrcode.react'
import dayjs from 'dayjs'
import { useApiQuery } from '@/hooks/useApiQuery'
import { requisitionsApi } from '@/api/jobs'
import { candidatesApi } from '@/api/candidates'
import type { JobRequisition } from '@/types'

const { Title, Text } = Typography
const { TextArea } = Input

export default function InviteLinkGenerator({ requisitionId }: { requisitionId?: string }) {
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [form] = Form.useForm()
  const [generatedLink, setGeneratedLink] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [isSpecificJob, setIsSpecificJob] = useState(!!requisitionId)

  // Fetch active jobs
  const { data: jobsData } = useApiQuery(['active-jobs-invite'], () => 
    requisitionsApi.list({ status: 'active' }),
    { enabled: drawerOpen }
  )
  const jobs = (jobsData as any)?.requisitions ?? []

  // Fetch existing links
  const { data: linksData, refetch: refetchLinks } = useApiQuery(['invite-links'], () => 
    candidatesApi.listInviteLinks()
  )
  const existingLinks = (linksData as any)?.links ?? (linksData as any)?.data?.links ?? []

  const handleGenerate = async (values: any) => {
    setLoading(true)
    try {
      const payload = {
        job_id: isSpecificJob ? (requisitionId || values.requisition_id) : undefined,
        expires_days: Number(values.expires_in || 0) || undefined,
        max_uses: Number(values.max_uses || 0) || undefined,
        form_config: values.custom_message ? { custom_message: values.custom_message } : {},
      }
      const res: any = await candidatesApi.createInviteLink(payload)
      const link = res?.data?.data?.link || {}
      const url = link?.url ? `${window.location.origin}${link.url}` : (link?.token ? `${window.location.origin}/apply/${link.token}/` : '')
      setGeneratedLink(url)
      message.success('Invite link generated successfully!')
      refetchLinks()
    } catch (err: any) {
      message.error('Failed to generate invite link')
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    message.success('Copied to clipboard')
  }

  const columns = [
    { 
      title: 'Created', 
      dataIndex: 'created_at', 
      render: (d: string) => dayjs(d).format('MMM D, YYYY') 
    },
    { 
      title: 'Job', 
      dataIndex: 'job_title', 
      render: (t: string) => t || <Tag color="default">General</Tag> 
    },
    { 
      title: 'Uses', 
      key: 'uses',
      render: (_: any, r: any) => `${r.use_count} / ${r.max_uses || '∞'}`
    },
    { 
      title: 'Expires', 
      dataIndex: 'expires_at', 
      render: (d: string) => d ? dayjs(d).format('MMM D') : 'Never' 
    },
    { 
      title: 'Status', 
      dataIndex: 'status', 
      render: (status: string) => status === 'active' ? <Tag color="green">Active</Tag> : <Tag color="red">Inactive</Tag> 
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, r: any) => (
        <Space>
          <Button size="small" type="text" icon={<CopyOutlined />} onClick={() => copyToClipboard(`${window.location.origin}${r.url}`)} />
          {r.status === 'active' && (
            <Popconfirm
              title="Deactivate this link?"
              onConfirm={async () => {
                try {
                  await candidatesApi.deactivateInviteLink(r.id)
                  message.success('Invite link deactivated')
                  refetchLinks()
                } catch (err: any) {
                  message.error(err?.response?.data?.message || 'Failed to deactivate invite link')
                }
              }}
            >
              <Button size="small" type="text" danger icon={<StopOutlined />} />
            </Popconfirm>
          )}
        </Space>
      )
    }
  ]

  return (
    <div className="space-y-6">
      <Card bordered={false} className="shadow-soft-sm rounded-2xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
              <LinkOutlined style={{ fontSize: 24 }} />
            </div>
            <div>
              <Title level={4} className="!mb-0 text-slate-900">Invite Candidates</Title>
              <Text type="secondary">Generate public apply links for your talent pool or specific jobs.</Text>
            </div>
          </div>
          <Button 
            type="primary" 
            icon={<PlusOutlined />} 
            onClick={() => setDrawerOpen(true)}
            className="h-11 rounded-xl font-bold bg-blue-600 border-none px-6"
          >
            Generate Link
          </Button>
        </div>
      </Card>

      {existingLinks.length > 0 && (
        <Card title={<Space><HistoryOutlined /> <span>Recent Invite Links</span></Space>} bordered={false} className="shadow-soft-sm rounded-2xl overflow-hidden p-0">
          <Table 
            dataSource={existingLinks} 
            columns={columns} 
            rowKey="id" 
            pagination={{ pageSize: 5 }} 
            size="small"
            className="modern-table"
          />
        </Card>
      )}

      <Drawer
        title={<span className="text-xl font-black text-slate-900 tracking-tight">Create Candidate Invite Link</span>}
        open={drawerOpen}
        onClose={() => { setDrawerOpen(false); setGeneratedLink(null); form.resetFields(); }}
        width={480}
        styles={{ body: { padding: '32px 24px' } }}
        destroyOnHidden
      >
        {!generatedLink ? (
          <Form form={form} layout="vertical" onFinish={handleGenerate} requiredMark={false} initialValues={{ expires_in: 30, max_uses: 0 }}>
            <Form.Item label="Link Type" className="mb-6">
              <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100">
                <div className="flex items-center justify-between">
                  <Text strong className="text-slate-700">Link for specific job?</Text>
                  <Switch checked={isSpecificJob} onChange={setIsSpecificJob} disabled={!!requisitionId} />
                </div>
                {isSpecificJob && !requisitionId && (
                  <div className="mt-4">
                    <Form.Item name="requisition_id" rules={[{ required: true, message: 'Please select a job' }]}>
                      <Select
                        placeholder="Select an active job..."
                        className="w-full h-11"
                        options={jobs.map((j: JobRequisition) => ({ value: j.id, label: j.title }))}
                        showSearch
                        optionFilterProp="label"
                      />
                    </Form.Item>
                  </div>
                )}
              </div>
            </Form.Item>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="expires_in" label="Expires in" rules={[{ required: true }]}>
                  <Select className="h-11" options={[
                    { value: 7, label: '7 Days' },
                    { value: 30, label: '30 Days' },
                    { value: 90, label: '90 Days' },
                    { value: 0, label: 'Never' },
                  ]} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="max_uses" label="Max uses (0=∞)">
                  <InputNumber min={0} className="w-full h-11 pt-1" />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item name="custom_message" label="Welcome Message" extra="Shown to candidates at the top of the application form.">
              <TextArea rows={4} placeholder="e.g. We are excited to see your application! Please fill out the form below..." className="rounded-xl border-slate-200" />
            </Form.Item>

            <Button type="primary" htmlType="submit" block size="large" loading={loading} className="h-14 rounded-2xl font-black bg-blue-600 border-none shadow-soft-md mt-4">
              Generate Invite Link
            </Button>
          </Form>
        ) : (
          <div className="space-y-10 py-4 animate-in fade-in zoom-in duration-300">
            <div className="text-center">
              <div className="bg-emerald-50 text-emerald-600 h-16 w-16 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-emerald-100">
                <LinkOutlined style={{ fontSize: 32 }} />
              </div>
              <Title level={3} className="!mb-1">Invite Link Ready</Title>
              <Text type="secondary" className="text-sm">Share this link with your candidates</Text>
            </div>

            <div className="bg-slate-50 p-6 rounded-3xl border-2 border-dashed border-slate-200 text-center flex flex-col items-center gap-6">
              <div className="p-4 bg-white rounded-2xl shadow-soft-sm">
                <QRCodeSVG value={generatedLink} size={160} level="H" />
              </div>
              <div className="w-full">
                <Input.Group compact className="w-full flex">
                  <Input value={generatedLink} readOnly className="h-12 rounded-l-xl font-medium text-slate-600" />
                  <Button icon={<CopyOutlined />} className="h-12 rounded-r-xl font-bold bg-slate-900 text-white border-none px-6" onClick={() => copyToClipboard(generatedLink)}>Copy</Button>
                </Input.Group>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <Button icon={<MailOutlined />} className="h-12 rounded-xl font-bold border-slate-200">Email Link</Button>
              <Button icon={<WhatsAppOutlined />} className="h-12 rounded-xl font-bold border-slate-200 text-emerald-600">WhatsApp</Button>
            </div>

            <Button type="text" block className="font-bold text-slate-400" onClick={() => { setGeneratedLink(null); form.resetFields(); }}>
              Generate Another Link
            </Button>
          </div>
        )}
      </Drawer>
    </div>
  )
}
