import React, { useEffect, useMemo, useState } from 'react'
import { Card, Table, Tag, Typography, Button, Modal, DatePicker, Select, Form, message, Spin, Input, Alert, Space, Popconfirm, Divider } from 'antd'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { hdcApi } from '@/api/hdc'
import { candidatesApi } from '@/api/candidates'
import { pipelineApi } from '@/api/pipeline'
import { Briefcase, ShieldAlert, User, FileCheck, Send } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import dayjs from 'dayjs'
import { useNavigate, useSearchParams } from 'react-router-dom'

const { Text } = Typography

const STATUS_COLORS: Record<string, string> = {
  pending: 'blue',
  in_progress: 'processing',
  documents_pending: 'orange',
  completed: 'green',
  handed_off: 'purple',
  joined: 'green',
  postponed: 'gold',
  withdrawn: 'red',
  no_show: 'volcano',
}

export default function JoiningTracking() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedCase, setSelectedCase] = useState<any>(null)
  const [checklist, setChecklist] = useState<any[]>([])
  const [form] = Form.useForm()
  const [checklistForm] = Form.useForm()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const user = useAuthStore(state => state.user)

  const isGovernanceUser = ['super_admin', 'tenant_admin', 'hr_manager'].includes(user?.role || '')

  const { data: joiningData, isLoading: loadingJoining, isError } = useApiQuery(
    ['hdc-joining-cases'],
    () => hdcApi.listJoiningCases()
  )
  const { data: candidatesData } = useApiQuery(['candidates-list'], () => candidatesApi.list())
  const { data: applicationsData } = useApiQuery(['pipeline-applications'], () => pipelineApi.listApplications())

  const updateMutation = useMutation({
    mutationFn: ({ id, values }: any) => hdcApi.updateJoiningCase(id, values),
    onSuccess: () => {
      message.success('Onboarding updated')
      setIsModalOpen(false)
      setSelectedCase(null)
      form.resetFields()
      checklistForm.resetFields()
      queryClient.invalidateQueries({ queryKey: ['hdc-joining-cases'] })
    },
    onError: () => message.error('Failed to update onboarding case'),
  })

  const confirmMutation = useMutation({
    mutationFn: (id: string) => hdcApi.confirmJoining(id),
    onSuccess: () => {
      message.success('Joining confirmed')
      queryClient.invalidateQueries({ queryKey: ['hdc-joining-cases'] })
    },
    onError: () => message.error('Failed to confirm joining'),
  })

  const checklistMutation = useMutation({
    mutationFn: ({ id, payload }: any) => hdcApi.upsertJoiningChecklistItem(id, payload),
    onSuccess: () => {
      message.success('Checklist item saved')
      checklistForm.resetFields()
      queryClient.invalidateQueries({ queryKey: ['hdc-joining-cases'] })
    },
    onError: () => message.error('Failed to save checklist item'),
  })

  const handoffMutation = useMutation({
    mutationFn: (id: string) => hdcApi.prepareOnboardingHandoff(id),
    onSuccess: () => {
      message.success('HRMS handoff payload prepared')
      queryClient.invalidateQueries({ queryKey: ['hdc-joining-cases'] })
    },
    onError: () => message.error('Failed to prepare handoff payload'),
  })

  const joiningCases = (joiningData as any)?.data || (Array.isArray(joiningData) ? joiningData : [])
  const applicationIdFromUrl = searchParams.get('applicationId')
  const filteredJoiningCases = applicationIdFromUrl
    ? joiningCases.filter((j: any) => j.application_id === applicationIdFromUrl)
    : joiningCases
  const candidates = (candidatesData as any)?.candidates || (candidatesData as any)?.data?.candidates || []
  const applications = (applicationsData as any)?.applications || (applicationsData as any)?.data?.applications || []
  const appById = new Map<string, any>(applications.map((app: any) => [app.id, app]))
  const candidateById = new Map<string, any>(candidates.map((c: any) => [c.id, c]))

  const candidateName = (applicationId: string) =>
    candidateById.get(appById.get(applicationId)?.candidate_id)?.full_name || 'Hiring Candidate'

  const openModal = (record: any) => {
    setSelectedCase(record)
    setChecklist(Array.isArray(record?.metadata?.checklist) ? record.metadata.checklist : [])
    form.setFieldsValue({
      status: record.status,
      joining_date: record.joining_date ? dayjs(record.joining_date) : null,
      notes: record.handoff_notes,
      assigned_hr_id: record.assigned_hr_id || undefined,
    })
    setIsModalOpen(true)
  }

  const handleUpdate = (values: any) => {
    if (!selectedCase) return
    updateMutation.mutate({
      id: selectedCase.id,
      values: {
        status: values.status,
        joining_date: values.joining_date?.format('YYYY-MM-DD'),
        handoff_notes: values.notes,
        assigned_hr_id: values.assigned_hr_id || null,
        metadata: {
          ...(selectedCase.metadata || {}),
          checklist,
        },
      },
    })
  }

  useEffect(() => {
    const joiningId = searchParams.get('joiningId')
    if (!joiningId || !joiningCases.length) return
    const target = joiningCases.find((item: any) => item.id === joiningId)
    if (target) {
      openModal(target)
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev)
        next.delete('joiningId')
        return next
      }, { replace: true })
    }
  }, [joiningCases, searchParams, setSearchParams])

  const columns = useMemo(() => [
    {
      title: 'Candidate',
      dataIndex: 'application_id',
      key: 'candidate',
      render: (applicationId: string) => (
        <Space>
          <User size={14} className="text-slate-400" />
          <Text strong className="text-sm">{candidateName(applicationId)}</Text>
        </Space>
      )
    },
    {
      title: 'Onboarding Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={STATUS_COLORS[status] || 'default'} className="rounded-md font-black text-[9px] uppercase border-none px-2">
          {status}
        </Tag>
      ),
    },
    {
      title: 'Documents',
      key: 'documents',
      render: (_: any, record: any) => {
        const count = Object.keys(record?.metadata?.documents || {}).length
        return count > 0 ? <Tag color="cyan">{count} received</Tag> : <Text className="text-xs text-slate-400">Pending</Text>
      },
    },
    {
      title: 'Handoff',
      key: 'handoff',
      render: (_: any, record: any) => {
        const handoffStatus = record?.metadata?.hrms_handoff?.status || 'pending'
        return <Tag color={handoffStatus === 'acknowledged' ? 'green' : handoffStatus === 'ready' ? 'blue' : handoffStatus === 'rejected' ? 'red' : 'default'}>{handoffStatus}</Tag>
      },
    },
    {
      title: 'Action',
      key: 'action',
      align: 'right' as const,
      render: (_: any, record: any) => (
        <Space>
          <Button size="small" onClick={() => openModal(record)} className="rounded-lg h-7 text-[10px] font-bold uppercase tracking-widest">
            Manage
          </Button>
          <Popconfirm
            title="Confirm Candidate Joining"
            description="Finalize this hiring outcome?"
            onConfirm={() => confirmMutation.mutate(record.id)}
            okText="Yes, Joined"
            cancelText="Cancel"
            disabled={record.status === 'joined' || !isGovernanceUser}
          >
            <Button
              size="small"
              type="primary"
              disabled={record.status === 'joined' || !isGovernanceUser}
              loading={confirmMutation.isPending}
              className="rounded-lg h-7 text-[10px] font-bold uppercase tracking-widest"
            >
              Confirm
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ], [candidateName, confirmMutation.isPending, isGovernanceUser])

  if (isError) {
    return <Alert type="error" message="Failed to load onboarding cases. Please refresh." showIcon className="my-4" />
  }

  return (
    <div className="space-y-6">
      <Card
        className="rounded-[2.5rem] border-slate-200 shadow-sm"
        title={
          <div className="flex items-center gap-2 py-2">
            <div className="p-2 bg-blue-50 rounded-xl text-blue-600"><Briefcase size={18} /></div>
            <div>
              <div className="text-[10px] font-black uppercase tracking-widest text-slate-400 leading-none mb-1">Company Onboarding</div>
              <div className="text-base font-black text-slate-800 leading-none">Onboarding + Handoff Tracking</div>
            </div>
          </div>
        }
      >
        {loadingJoining ? (
          <div className="py-20 text-center"><Spin tip="Loading onboarding status..." /></div>
        ) : (
          <div className="overflow-x-auto">
            <Table
              columns={columns}
              dataSource={filteredJoiningCases}
              rowKey="id"
              pagination={{ pageSize: 10, size: 'small' }}
              locale={{
                emptyText: (
                  <div className="py-16 text-center flex flex-col items-center gap-4">
                    <Briefcase size={48} className="text-slate-100" />
                    <div>
                      <Text className="block font-black text-slate-400 uppercase tracking-widest text-[10px]">No onboarding cases found</Text>
                      {applicationIdFromUrl && (
                        <Button type="link" size="small" className="text-[10px] font-black uppercase mt-2 text-indigo-500" onClick={() => navigate('/hiring-decisions/joining')}>
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

      <Modal
        title={`Manage Onboarding: ${selectedCase ? candidateName(selectedCase.application_id) : ''}`}
        open={isModalOpen}
        onCancel={() => { setIsModalOpen(false); setSelectedCase(null); form.resetFields(); checklistForm.resetFields() }}
        onOk={() => form.submit()}
        confirmLoading={updateMutation.isPending}
        width={780}
      >
        {!isGovernanceUser && (
          <Alert
            type="info"
            showIcon
            icon={<ShieldAlert size={14} />}
            message="Limited access"
            description="Only HR Managers or Admins can finalize joining confirmation."
            className="rounded-xl border-blue-100 mb-4"
          />
        )}

        <Form form={form} layout="vertical" onFinish={handleUpdate}>
          <Form.Item name="status" label="Onboarding Status" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="pending">Pending</Select.Option>
              <Select.Option value="in_progress">In Progress</Select.Option>
              <Select.Option value="documents_pending">Documents Pending</Select.Option>
              <Select.Option value="completed">Completed</Select.Option>
              <Select.Option value="handed_off">Handed Off</Select.Option>
              <Select.Option value="joined">Joined</Select.Option>
              <Select.Option value="postponed">Postponed</Select.Option>
              <Select.Option value="withdrawn">Withdrawn</Select.Option>
              <Select.Option value="no_show">No Show</Select.Option>
            </Select>
          </Form.Item>
          <Space className="w-full" size={12}>
            <Form.Item name="joining_date" label="Joining Date" className="!mb-0">
              <DatePicker />
            </Form.Item>
            <Form.Item name="assigned_hr_id" label="Assigned HR (User ID)" className="!mb-0">
              <Input placeholder="UUID" style={{ width: 280 }} />
            </Form.Item>
          </Space>
          <Form.Item name="notes" label="HR Notes" className="mt-4">
            <Input.TextArea rows={3} placeholder="Access, induction, welcome kit notes..." />
          </Form.Item>
        </Form>

        <Divider />

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Text strong>Onboarding Checklist</Text>
            <Button
              size="small"
              icon={<Send size={12} />}
              loading={handoffMutation.isPending}
              onClick={() => selectedCase && handoffMutation.mutate(selectedCase.id)}
            >
              Prepare HRMS Handoff
            </Button>
          </div>

          {checklist.length === 0 && (
            <Text className="text-xs text-slate-500">No checklist items yet. Add one below.</Text>
          )}

          {checklist.map((item, idx) => (
            <div key={`${item.task_id || item.task_name}-${idx}`} className="rounded-lg border border-slate-200 p-3 flex items-center justify-between gap-3">
              <div>
                <Text strong className="block">{item.task_name}</Text>
                <Text className="text-xs text-slate-500">Assigned: {item.assigned_to || 'Unassigned'} {item.due_date ? `| Due: ${item.due_date}` : ''}</Text>
              </div>
              <Tag color={item.status === 'completed' ? 'green' : item.status === 'in_progress' ? 'blue' : 'default'}>{item.status}</Tag>
            </div>
          ))}

          <Form
            form={checklistForm}
            layout="inline"
            onFinish={(values) => {
              if (!selectedCase) return
              checklistMutation.mutate({
                id: selectedCase.id,
                payload: {
                  task_name: values.task_name,
                  assigned_to: values.assigned_to || '',
                  due_date: values.due_date ? dayjs(values.due_date).format('YYYY-MM-DD') : null,
                  status: values.status || 'pending',
                },
              })
              const newItem = {
                task_name: values.task_name,
                assigned_to: values.assigned_to || '',
                due_date: values.due_date ? dayjs(values.due_date).format('YYYY-MM-DD') : null,
                status: values.status || 'pending',
              }
              setChecklist((prev) => [...prev, newItem])
            }}
          >
            <Form.Item name="task_name" rules={[{ required: true, message: 'Task required' }]}>
              <Input placeholder="Task name" />
            </Form.Item>
            <Form.Item name="assigned_to">
              <Input placeholder="Assigned to" />
            </Form.Item>
            <Form.Item name="due_date">
              <DatePicker />
            </Form.Item>
            <Form.Item name="status" initialValue="pending">
              <Select style={{ width: 130 }}>
                <Select.Option value="pending">Pending</Select.Option>
                <Select.Option value="in_progress">In Progress</Select.Option>
                <Select.Option value="completed">Completed</Select.Option>
              </Select>
            </Form.Item>
            <Form.Item>
              <Button type="dashed" htmlType="submit" loading={checklistMutation.isPending}>Add</Button>
            </Form.Item>
          </Form>
        </div>

        {selectedCase?.metadata?.documents && Object.keys(selectedCase.metadata.documents).length > 0 && (
          <>
            <Divider />
            <div>
              <Text strong className="flex items-center gap-2"><FileCheck size={14} /> Document Status</Text>
              <div className="mt-2 space-y-2">
                {Object.entries(selectedCase.metadata.documents).map(([docType, info]: any) => (
                  <div key={docType} className="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2">
                    <Text>{docType}</Text>
                    <Tag color={String(info?.status || '').toLowerCase() === 'uploaded' ? 'green' : 'default'}>{info?.status || 'pending'}</Tag>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </Modal>
    </div>
  )
}
