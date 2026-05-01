import React, { useEffect, useMemo, useState } from 'react'
import { Card, Table, Tag, Typography, Button, Modal, Form, Input, Select, message, Spin, Alert, Space } from 'antd'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { hdcApi } from '@/api/hdc'
import { requisitionsApi } from '@/api/jobs'
import { candidatesApi } from '@/api/candidates'
import { pipelineApi } from '@/api/pipeline'
import { organisationApi } from '@/api/organisation'
import { Users, Gavel, Plus } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'

const { Text } = Typography

export default function HiringCommittee() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [voteModal, setVoteModal] = useState<any>(null)
  const [form] = Form.useForm()
  const [voteForm] = Form.useForm()
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const applicationIdFromUrl = searchParams.get('applicationId')

  // ─── Data Fetching ───
  const { data: committeesData, isLoading: loadingCommittees, isError } = useApiQuery(
    ['hdc-committees'],
    () => hdcApi.listCommittees()
  )
  const { data: jobsData } = useApiQuery(['jobs-list'], () => requisitionsApi.list({ status: 'active' }))
  const { data: candidatesData } = useApiQuery(['candidates-list'], () => candidatesApi.list())
  const { data: applicationsData } = useApiQuery(['pipeline-applications'], () => pipelineApi.listApplications())
  const { data: usersData } = useApiQuery(['org-users'], () => organisationApi.listUsers())

  // ─── Mutations ───
  const createMutation = useMutation({
    mutationFn: (values: any) => hdcApi.createCommittee(values),
    onSuccess: () => {
      message.success('Committee case initialized')
      setIsModalOpen(false)
      form.resetFields()
      queryClient.invalidateQueries({ queryKey: ['hdc-committees'] })
    },
    onError: () => message.error('Failed to create committee'),
  })

  const voteMutation = useMutation({
    mutationFn: ({ id, values }: any) => hdcApi.submitVote(id, values),
    onSuccess: () => {
      message.success('Vote recorded')
      setVoteModal(null)
      voteForm.resetFields()
      queryClient.invalidateQueries({ queryKey: ['hdc-committees'] })
    },
    onError: () => message.error('Failed to submit vote'),
  })

  const committeesRaw = (committeesData as any)?.data || (Array.isArray(committeesData) ? committeesData : [])
  const committees = applicationIdFromUrl 
    ? committeesRaw.filter((c: any) => c.application_id === applicationIdFromUrl)
    : committeesRaw

  const jobs = (jobsData as any)?.requisitions || (jobsData as any)?.data?.requisitions || []
  const candidates = (candidatesData as any)?.candidates || (candidatesData as any)?.data?.candidates || []
  const applications = (applicationsData as any)?.applications || (applicationsData as any)?.data?.applications || []
  const users = (usersData as any)?.users || (usersData as any)?.data?.users || []
  const selectedJobId = Form.useWatch('job_id', form)

  const candidateById = useMemo(
    () => new Map<string, any>(candidates.map((c: any) => [c.id, c])),
    [candidates]
  )

  useEffect(() => {
    if (isModalOpen && applicationIdFromUrl) {
      const app = applications.find((a: any) => a.id === applicationIdFromUrl)
      if (app) {
        form.setFieldsValue({
          job_id: app.requisition_id,
          application_id: app.id
        })
      }
    }
  }, [isModalOpen, applicationIdFromUrl, applications, form])

  const applicationsForSelectedJob = useMemo(
    () => applications.filter((a: any) => !selectedJobId || a.requisition_id === selectedJobId),
    [applications, selectedJobId]
  )

  useEffect(() => {
    const committeeId = searchParams.get('committeeId')
    if (!committeeId || !committees.length) return
    const target = committees.find((c: any) => c.id === committeeId)
    if (target) {
      setVoteModal(target)
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev)
        next.delete('committeeId')
        return next
      }, { replace: true })
    }
  }, [committees, searchParams, setSearchParams])

  const handleCreate = (values: any) => {
    const selectedApplication = applications.find((a: any) => a.id === values.application_id)
    if (!selectedApplication) {
      message.error('Please select a valid candidate application.')
      return
    }
    createMutation.mutate({
      name: values.name,
      requisition_id: selectedApplication.requisition_id,
      candidate_id: selectedApplication.candidate_id,
      application_id: selectedApplication.id,
      mode: values.mode,
      member_ids: values.member_ids || [],
      status: 'voting',
      quorum_required: values.quorum_required ? parseInt(values.quorum_required) : Math.max((values.member_ids || []).length, 1),
    })
  }

  const columns = [
    { title: 'Committee', dataIndex: 'name', key: 'name' },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'escalated' ? 'red' : status === 'completed' ? 'green' : 'blue'}>
          {status?.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Mode',
      dataIndex: 'mode',
      key: 'mode',
      render: (mode: string) => <Text className="text-xs font-bold text-slate-500 uppercase">{mode}</Text>,
    },
    {
      title: 'Quorum',
      dataIndex: 'quorum_required',
      key: 'quorum',
      render: (q: number, record: any) => (
        <Text className="text-xs">{record.members?.filter((m: any) => m.has_voted).length || 0} / {q || '—'}</Text>
      ),
    },
    {
      title: 'Action',
      key: 'action',
      render: (_: any, record: any) => (
        <Button
          size="small"
          type="primary"
          icon={<Gavel className="h-3 w-3" />}
          onClick={() => setVoteModal(record)}
          disabled={record.status === 'completed'}
        >
          Vote
        </Button>
      ),
    },
  ]

  if (isError) {
    return <Alert type="error" message="Failed to load committees. Please refresh." showIcon className="my-4" />
  }

  const isApplicationInactive = applicationIdFromUrl && committees.length > 0 && ['rejected', 'withdrawn', 'cancelled'].includes(committees[0].status?.toLowerCase())

  return (
    <div className="space-y-6">
      {isApplicationInactive && (
        <Alert
          type="warning"
          message="Inactive Committee Case"
          description="This committee review is for an application that is no longer active. Voting is restricted."
          showIcon
          className="rounded-2xl"
        />
      )}
      <Card
        className="rounded-3xl border-slate-200 shadow-sm"
        title={
          <div className="flex items-center gap-2">
            <Users className="h-5 w-5 text-blue-500" />
            <span>Operational Hiring Committees</span>
          </div>
        }
        extra={
          <Button type="primary" icon={<Plus size={16} />} onClick={() => setIsModalOpen(true)}>
            New Committee
          </Button>
        }
      >
        {loadingCommittees ? (
          <div className="py-12 text-center"><Spin /></div>
        ) : (
          <Table
            columns={columns}
            dataSource={committees}
            rowKey="id"
            locale={{ emptyText: <EmptyState title="No active committees" /> }}
          />
        )}
      </Card>

      {/* ─── Create Modal ─── */}
      <Modal
        title="Initialize Hiring Committee"
        open={isModalOpen}
        onCancel={() => { setIsModalOpen(false); form.resetFields() }}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="Committee Name" rules={[{ required: true }]}>
            <Input placeholder="e.g. Senior Backend Review" />
          </Form.Item>
          <Form.Item name="job_id" label="Job Requisition" rules={[{ required: true }]}>
            <Select placeholder="Select job..." showSearch optionFilterProp="children">
              {jobs.map((j: any) => (
                <Select.Option key={j.id} value={j.id}>{j.title} ({j.job_ref_id})</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="application_id" label="Candidate Application" rules={[{ required: true }]}>
            <Select placeholder="Select finalist application..." showSearch optionFilterProp="children">
              {applicationsForSelectedJob.map((app: any) => {
                const candidate = candidateById.get(app.candidate_id)
                const job = jobs.find((j: any) => j.id === app.requisition_id)
                return (
                  <Select.Option key={app.id} value={app.id}>
                    {candidate?.full_name || 'Candidate'} {job ? `• ${job.title}` : ''}
                  </Select.Option>
                )
              })}
            </Select>
          </Form.Item>
          <Form.Item name="quorum_required" label="Quorum Required">
            <Input type="number" min={1} placeholder="e.g. 2" />
          </Form.Item>
          <Form.Item name="mode" label="Review Mode" initialValue="Standard">
            <Select>
              <Select.Option value="Standard">Standard (Majority)</Select.Option>
              <Select.Option value="Weighted">Weighted Panel</Select.Option>
              <Select.Option value="Leadership">Leadership Override</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="member_ids" label="Assign Members">
            <Select mode="multiple" placeholder="Select panel members...">
              {users.map((u: any) => (
                <Select.Option key={u.id} value={u.id}>{u.first_name} {u.last_name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* ─── Vote Modal ─── */}
      <Modal
        title={`Submit Vote: ${voteModal?.name}`}
        open={!!voteModal}
        onCancel={() => { setVoteModal(null); voteForm.resetFields() }}
        onOk={() => voteForm.submit()}
        confirmLoading={voteMutation.isPending}
      >
        <Form
          form={voteForm}
          layout="vertical"
          onFinish={(v) => voteMutation.mutate({ id: voteModal.id, values: v })}
        >
          <Form.Item name="vote" label="Your Decision" rules={[{ required: true }]}>
            <Select placeholder="Choose outcome...">
              <Select.Option value="hire">Hire</Select.Option>
              <Select.Option value="reject">Reject</Select.Option>
              <Select.Option value="hold">Hold / More evidence</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="notes" label="Review Notes">
            <Input.TextArea rows={4} placeholder="Explain your rationale..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

function EmptyState({ title }: { title: string }) {
  return (
    <div className="py-8 text-center">
      <Users className="mx-auto h-12 w-12 text-slate-200" />
      <Text className="mt-2 block font-bold text-slate-400">{title}</Text>
    </div>
  )
}
