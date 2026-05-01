import React, { useEffect, useMemo, useState } from 'react'
import { Card, Table, Tag, Typography, Button, Modal, Form, Input, Select, message, Spin, Alert, Popconfirm, Space } from 'antd'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { hdcApi } from '@/api/hdc'
import { requisitionsApi } from '@/api/jobs'
import { candidatesApi } from '@/api/candidates'
import { pipelineApi } from '@/api/pipeline'
import { organisationApi } from '@/api/organisation'
import { CheckCircle2, XCircle, RotateCcw, ShieldCheck, Plus, User, Info } from 'lucide-react'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { useSearchParams } from 'react-router-dom'

dayjs.extend(relativeTime)
const { Text } = Typography

export default function DecisionApproval() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedCase, setSelectedCase] = useState<any>(null)
  const [form] = Form.useForm()
  const [reviewForm] = Form.useForm()
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const applicationIdFromUrl = searchParams.get('applicationId')

  // ─── Data Fetching ───
  const { data: approvalsData, isLoading: loadingApprovals, isError } = useApiQuery(
    ['hdc-approvals-list'],
    () => hdcApi.listApprovals()
  )
  const { data: jobsData } = useApiQuery(['jobs-list'], () => requisitionsApi.list({ status: 'active' }))
  const { data: candidatesData } = useApiQuery(['candidates-list'], () => candidatesApi.list())
  const { data: applicationsData } = useApiQuery(['pipeline-applications'], () => pipelineApi.listApplications())
  const { data: usersData } = useApiQuery(['org-users'], () => organisationApi.listUsers())

  // ─── Mutations ───
  const createMutation = useMutation({
    mutationFn: (values: any) => hdcApi.createApproval(values),
    onSuccess: () => {
      message.success('Approval request initialized')
      setIsModalOpen(false)
      form.resetFields()
      queryClient.invalidateQueries({ queryKey: ['hdc-approvals-list'] })
    },
    onError: () => message.error('Failed to create approval request'),
  })

  const approveMutation = useMutation({
    mutationFn: ({ id, values }: any) => hdcApi.approveForOffer(id, values),
    onSuccess: () => {
      message.success('Approved for offer')
      setSelectedCase(null)
      reviewForm.resetFields()
      queryClient.invalidateQueries({ queryKey: ['hdc-approvals-list'] })
    },
    onError: () => message.error('Failed to approve'),
  })

  const rejectMutation = useMutation({
    mutationFn: ({ id, values }: any) => hdcApi.rejectCandidate(id, values),
    onSuccess: () => {
      message.warning('Candidate rejected')
      setSelectedCase(null)
      reviewForm.resetFields()
      queryClient.invalidateQueries({ queryKey: ['hdc-approvals-list'] })
    },
    onError: () => message.error('Failed to record rejection'),
  })

  // ─── Transformation ───
  const approvalsRaw = (approvalsData as any)?.data || (Array.isArray(approvalsData) ? approvalsData : [])
  const approvals = applicationIdFromUrl 
    ? approvalsRaw.filter((a: any) => a.application_id === applicationIdFromUrl)
    : approvalsRaw

  const jobs = (jobsData as any)?.requisitions || (jobsData as any)?.data?.requisitions || []
  const candidates = (candidatesData as any)?.candidates || (candidatesData as any)?.data?.candidates || []
  const applications = (applicationsData as any)?.applications || (applicationsData as any)?.data?.applications || []
  const users = (usersData as any)?.users || (usersData as any)?.data?.users || []
  const selectedJobId = Form.useWatch('job_id', form)

  const candidateById = useMemo(() => new Map(candidates.map((c: any) => [c.id, c])), [candidates])
  const jobById = useMemo(() => new Map(jobs.map((j: any) => [j.id, j])), [jobs])
  const userById = useMemo(() => new Map(users.map((u: any) => [u.id, u])), [users])

  useEffect(() => {
    if (isModalOpen && applicationIdFromUrl) {
      const app = applications.find((a: any) => a.id === applicationIdFromUrl)
      if (app) form.setFieldsValue({ requisition_id: app.requisition_id, application_id: app.id })
    }
  }, [isModalOpen, applicationIdFromUrl, applications, form])

  const applicationsForSelectedJob = useMemo(
    () => applications.filter((a: any) => !selectedJobId || a.requisition_id === selectedJobId),
    [applications, selectedJobId]
  )

  const columns = [
    {
      title: 'Candidate',
      key: 'candidate',
      render: (_: any, record: any) => {
        const app = applications.find(a => a.id === record.application_id)
        const candidate = candidateById.get(app?.candidate_id || record.candidate_id)
        return (
          <Space>
            <User size={14} className="text-slate-400" />
            <Text strong className="text-sm">{candidate?.full_name || 'Candidate'}</Text>
          </Space>
        )
      }
    },
    {
      title: 'Job',
      dataIndex: 'requisition_id',
      key: 'job',
      render: (id: string) => <Text className="text-xs text-slate-500 font-medium">{jobById.get(id)?.title || 'Position'}</Text>
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'pending' ? 'orange' : status === 'approved' ? 'green' : 'red'} className="rounded-md font-black text-[9px] uppercase border-none px-2">
          {status}
        </Tag>
      ),
    },
    {
      title: 'Approver',
      dataIndex: 'approver_id',
      key: 'approver',
      render: (id: string) => <Text className="text-xs text-slate-500">{userById.get(id)?.first_name} {userById.get(id)?.last_name}</Text>
    },
    {
      title: 'Action',
      key: 'action',
      align: 'right' as const,
      render: (_: any, record: any) => (
        <Button
          size="small"
          type="primary"
          onClick={() => { setSelectedCase(record); reviewForm.resetFields() }}
          disabled={record.status !== 'pending'}
          className="rounded-lg h-7 text-[10px] font-bold uppercase tracking-widest"
        >
          Review
        </Button>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <Card
        className="rounded-[2.5rem] border-slate-200 shadow-sm"
        title={
          <div className="flex items-center gap-2 py-2">
            <div className="p-2 bg-blue-50 rounded-xl text-blue-600"><ShieldCheck size={18} /></div>
            <div>
              <div className="text-[10px] font-black uppercase tracking-widest text-slate-400 leading-none mb-1">Executive Governance</div>
              <div className="text-base font-black text-slate-800 leading-none">Decision Approvals</div>
            </div>
          </div>
        }
        extra={
          <Button type="primary" icon={<Plus size={16} />} onClick={() => setIsModalOpen(true)} className="rounded-xl h-10 font-bold uppercase text-[11px] tracking-widest">
            New Approval Request
          </Button>
        }
      >
        {loadingApprovals ? (
          <div className="py-20 text-center"><Spin tip="Loading approvals..." /></div>
        ) : (
          <div className="overflow-x-auto">
            <Table
              columns={columns}
              dataSource={approvals}
              rowKey="id"
              pagination={{ pageSize: 10, size: 'small' }}
              locale={{ emptyText: <EmptyState title="No pending approvals" /> }}
            />
          </div>
        )}
      </Card>

      {/* ─── Create Modal ─── */}
      <Modal
        title={<div className="flex items-center gap-2 font-black uppercase tracking-tight"><Plus size={18} /> <span>New Approval Request</span></div>}
        open={isModalOpen}
        onCancel={() => { setIsModalOpen(false); form.resetFields() }}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending}
        className="rounded-3xl"
      >
        <Form form={form} layout="vertical" onFinish={createMutation.mutate}>
          <Form.Item name="requisition_id" label={<span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Job Requisition</span>} rules={[{ required: true }]}>
            <Select placeholder="Select position..." showSearch optionFilterProp="children">
              {jobs.map((j: any) => (
                <Select.Option key={j.id} value={j.id}>{j.title} ({j.job_ref_id})</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="application_id" label={<span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Finalist Candidate</span>} rules={[{ required: true }]}>
            <Select placeholder="Select candidate application..." showSearch optionFilterProp="children">
              {applicationsForSelectedJob.map((app: any) => {
                const candidate = candidateById.get(app.candidate_id)
                return <Select.Option key={app.id} value={app.id}>{candidate?.full_name || 'Candidate'}</Select.Option>
              })}
            </Select>
          </Form.Item>
          <Form.Item name="approver_id" label={<span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Assign Approver</span>} rules={[{ required: true }]}>
            <Select placeholder="Select executive approver...">
              {users.filter(u => ['super_admin', 'tenant_admin', 'hiring_manager'].includes(u.role)).map((u: any) => (
                <Select.Option key={u.id} value={u.id}>{u.first_name} {u.last_name} ({u.role?.replace(/_/g, ' ')})</Select.Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* ─── Review Modal ─── */}
      <Modal
        title={<div className="flex items-center gap-2 font-black uppercase tracking-tight"><ShieldCheck size={18} className="text-blue-500" /> <span>Final Review</span></div>}
        open={!!selectedCase}
        onCancel={() => setSelectedCase(null)}
        footer={[
          <Button key="back" onClick={() => setSelectedCase(null)} className="rounded-xl">Cancel</Button>,
          <Button key="reject" danger icon={<XCircle size={14} />} onClick={() => reviewForm.submit()} className="rounded-xl">Reject</Button>,
          <Popconfirm key="approve" title="Approve this hiring decision?" onConfirm={() => approveMutation.mutate({ id: selectedCase.id, values: reviewForm.getFieldsValue() })}>
             <Button type="primary" icon={<CheckCircle2 size={14} />} className="rounded-xl">Approve for Offer</Button>
          </Popconfirm>
        ]}
      >
        <div className="space-y-4 py-4">
          <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100 flex items-start gap-3">
             <Info size={16} className="text-blue-500 mt-0.5" />
             <div>
               <Text className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Approval Context</Text>
               <Text className="text-xs text-slate-600">Reviewing finalist for <b>{jobById.get(selectedCase?.requisition_id)?.title}</b>. Approval will authorize the recruitment team to model compensation and release the offer letter.</Text>
             </div>
          </div>
          <Form form={reviewForm} layout="vertical" onFinish={(v) => rejectMutation.mutate({ id: selectedCase.id, values: v })}>
            <Form.Item name="comments" label={<span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Review Comments</span>}>
              <Input.TextArea rows={4} placeholder="Add your justification or feedback..." className="rounded-xl" />
            </Form.Item>
          </Form>
        </div>
      </Modal>
    </div>
  )
}

function EmptyState({ title }: { title: string }) {
  return (
    <div className="py-16 text-center flex flex-col items-center gap-4">
      <ShieldCheck size={48} className="text-slate-100" />
      <Text className="block font-bold text-slate-400 uppercase tracking-widest text-[10px]">{title}</Text>
    </div>
  )
}
