import React, { useState, useEffect } from 'react'
import { Card, Table, Tag, Typography, Button, Modal, Form, Input, Select, message, Spin, Alert, Space } from 'antd'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { hdcApi } from '@/api/hdc'
import { candidatesApi } from '@/api/candidates'
import { pipelineApi } from '@/api/pipeline'
import { MessageSquare, Handshake, Plus, User } from 'lucide-react'

import { useNavigate, useSearchParams } from 'react-router-dom'

const { Text } = Typography

export default function Negotiation() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [roundModal, setRoundModal] = useState<any>(null)
  const [form] = Form.useForm()
  const [roundForm] = Form.useForm()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const applicationIdFromUrl = searchParams.get('applicationId')

  const handleCreate = (values: any) => {
    createMutation.mutate({
      application_id: values.application_id,
      status: 'active',
    })
  }

  const { data: negotiationsData, isLoading: loadingNegotiations, isError } = useApiQuery(
    ['hdc-negotiations'],
    () => hdcApi.listNegotiations()
  )
  const { data: candidatesData } = useApiQuery(['candidates-list'], () => candidatesApi.list())
  const { data: applicationsData } = useApiQuery(['pipeline-applications'], () => pipelineApi.listApplications())

  // ─── Mutations ───
  const createMutation = useMutation({
    mutationFn: (values: any) => hdcApi.createNegotiation(values),
    onSuccess: () => {
      message.success('Negotiation case opened')
      setIsModalOpen(false)
      form.resetFields()
      queryClient.invalidateQueries({ queryKey: ['hdc-negotiations'] })
    },
    onError: () => message.error('Failed to open negotiation case'),
  })

  const addRoundMutation = useMutation({
    mutationFn: ({ id, values }: any) => hdcApi.addNegotiationRound(id, values),
    onSuccess: () => {
      message.success('Round recorded')
      setRoundModal(null)
      roundForm.resetFields()
      queryClient.invalidateQueries({ queryKey: ['hdc-negotiations'] })
    },
    onError: () => message.error('Failed to record negotiation round'),
  })

  const negotiationsRaw = (negotiationsData as any)?.data || (Array.isArray(negotiationsData) ? negotiationsData : [])
  const negotiations = applicationIdFromUrl 
    ? negotiationsRaw.filter((n: any) => n.application_id === applicationIdFromUrl)
    : negotiationsRaw

  const candidates = (candidatesData as any)?.candidates || (candidatesData as any)?.data?.candidates || []
  const applications = (applicationsData as any)?.applications || (applicationsData as any)?.data?.applications || []
  const appById = new Map<string, any>(applications.map((app: any) => [app.id, app]))
  const candidateById = new Map<string, any>(candidates.map((c: any) => [c.id, c]))

  useEffect(() => {
    if (isModalOpen && applicationIdFromUrl) {
      form.setFieldsValue({
        application_id: applicationIdFromUrl
      })
    }
  }, [isModalOpen, applicationIdFromUrl, form])

  const columns = [
    {
      title: 'Candidate',
      dataIndex: 'application_id',
      key: 'candidate',
      render: (applicationId: string) => (
        <Space>
           <User size={14} className="text-slate-400" />
           <Text strong className="text-sm">
             {candidateById.get(appById.get(applicationId)?.candidate_id)?.full_name || 'Hiring Candidate'}
           </Text>
        </Space>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'agreed' ? 'green' : status === 'failed' ? 'red' : 'blue'} className="rounded-md font-black text-[9px] uppercase border-none px-2">
          {status}
        </Tag>
      ),
    },
    { 
      title: 'Round', 
      dataIndex: 'current_round', 
      key: 'round',
      render: (r: number) => <Text className="text-xs font-black text-slate-400">ROUND {r}</Text>
    },
    {
      title: 'Action',
      key: 'action',
      align: 'right' as const,
      render: (_: any, record: any) => (
        <Button
          size="small"
          type="primary"
          icon={<MessageSquare className="h-3 w-3" />}
          onClick={() => { setRoundModal(record); roundForm.resetFields() }}
          disabled={record.status === 'agreed' || record.status === 'closed' || record.status === 'failed'}
          className="rounded-lg h-7 text-[10px] font-bold uppercase tracking-widest"
        >
          Add Round
        </Button>
      ),
    },
  ]

  if (isError) {
    return <Alert type="error" message="Failed to load negotiations. Please refresh." showIcon className="my-4" />
  }

  return (
    <div className="space-y-6">
      <Card
        className="rounded-[2.5rem] border-slate-200 shadow-sm"
        title={
          <div className="flex items-center gap-2 py-2">
            <div className="p-2 bg-indigo-50 rounded-xl text-indigo-600"><Handshake size={18} /></div>
            <div>
              <div className="text-[10px] font-black uppercase tracking-widest text-slate-400 leading-none mb-1">Package Negotiation</div>
              <div className="text-base font-black text-slate-800 leading-none">Counter-Offer Tracking</div>
            </div>
          </div>
        }
        extra={
          <Button type="primary" icon={<Plus size={16} />} onClick={() => setIsModalOpen(true)} className="rounded-xl h-10 font-bold uppercase text-[11px] tracking-widest">
            Open New Case
          </Button>
        }
      >
        {loadingNegotiations ? (
          <div className="py-20 text-center"><Spin tip="Loading negotiation history..." /></div>
        ) : (
          <div className="overflow-x-auto">
            <Table
              columns={columns}
              dataSource={negotiations}
              rowKey="id"
              pagination={{ pageSize: 5, size: 'small' }}
              locale={{ 
                emptyText: (
                  <div className="py-16 text-center flex flex-col items-center gap-4">
                    <Handshake size={48} className="text-slate-100" />
                    <div>
                      <Text className="block font-black text-slate-400 uppercase tracking-widest text-[10px]">No active negotiations found</Text>
                      {applicationIdFromUrl && (
                         <Button 
                          type="link" 
                          size="small" 
                          className="text-[10px] font-black uppercase mt-2 text-indigo-500"
                          onClick={() => navigate('/hiring-decisions/negotiation')}
                        >
                          View All Cases
                        </Button>
                      )}
                    </div>
                  </div>
                )
              }}
            />
          </div>
        )}
      </Card>

      {/* ─── Open Case Modal ─── */}
      <Modal
        title="Open Negotiation Case"
        open={isModalOpen}
        onCancel={() => { setIsModalOpen(false); form.resetFields() }}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="application_id" label="Finalist Application" rules={[{ required: true }]}>
            <Select placeholder="Select finalist application..." showSearch optionFilterProp="children">
              {applications.map((app: any) => (
                <Select.Option key={app.id} value={app.id}>
                  {candidateById.get(app.candidate_id)?.full_name || 'Candidate'}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Text className="text-xs text-slate-400">
            Opening a case allows tracking candidate asks and company counter-offers across multiple rounds.
          </Text>
        </Form>
      </Modal>

      {/* ─── Record Round Modal ─── */}
      <Modal
        title="Record Negotiation Round"
        open={!!roundModal}
        onCancel={() => { setRoundModal(null); roundForm.resetFields() }}
        onOk={() => roundForm.submit()}
        confirmLoading={addRoundMutation.isPending}
      >
        <Form
          form={roundForm}
          layout="vertical"
          onFinish={(v) => addRoundMutation.mutate({ id: roundModal.id, values: v })}
        >
          <Form.Item name="candidate_ask" label="Candidate Ask (Detailed)">
            <Input.TextArea rows={3} placeholder="e.g. Higher fixed, remote days..." />
          </Form.Item>
          <Form.Item name="company_counter" label="Company Counter">
            <Input.TextArea rows={3} placeholder="e.g. Maxed fixed, joining bonus added..." />
          </Form.Item>
          <Form.Item name="outcome" label="Outcome" initialValue="active" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="active">Active (Round Continues)</Select.Option>
              <Select.Option value="agreed">Agreed (Package Locked)</Select.Option>
              <Select.Option value="failed">Failed (Candidate Declined)</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

function EmptyState({ title }: { title: string }) {
  return (
    <div className="py-8 text-center">
      <Handshake className="mx-auto h-12 w-12 text-slate-200" />
      <Text className="mt-2 block font-bold text-slate-400">{title}</Text>
    </div>
  )
}
