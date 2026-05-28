import { useMemo, useState } from 'react'
import { Button, Card, Form, Input, InputNumber, Modal, Select, Space, Table, Tag, Typography, message } from 'antd'
import dayjs from 'dayjs'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { useApiQuery } from '@/hooks/useApiQuery'
import { documentsApi } from '@/api/documents'
import { pipelineApi } from '@/api/pipeline'

const { Title, Text } = Typography

const STATUS_COLORS: Record<string, string> = {
  draft: 'default',
  approval_pending: 'gold',
  pending_approval: 'gold',
  approved: 'green',
  sent: 'blue',
  negotiation: 'purple',
  accepted: 'green',
  rejected: 'red',
  expired: 'volcano',
  withdrawn: 'orange',
  revoked: 'red',
}

export default function OfferManagement() {
  const queryClient = useQueryClient()
  const [createOpen, setCreateOpen] = useState(false)
  const [approvalOpen, setApprovalOpen] = useState(false)
  const [negotiationOpen, setNegotiationOpen] = useState(false)
  const [activeOffer, setActiveOffer] = useState<any | null>(null)
  const [createForm] = Form.useForm()
  const [approvalForm] = Form.useForm()
  const [negotiationForm] = Form.useForm()

  const { data: offersData, isLoading } = useApiQuery(['company-offers'], () => documentsApi.listOffers())
  const { data: applicationsData } = useApiQuery(['company-offer-applications'], () => pipelineApi.listApplications())

  const offers = (offersData as any)?.offers || (offersData as any)?.data?.offers || []
  const applications = (applicationsData as any)?.applications || (applicationsData as any)?.data?.applications || []

  const applicationOptions = useMemo(() => {
    return applications.map((app: any) => ({
      value: app.id,
      label: `${app.candidate_name || app.candidate_id} • ${app.status || 'applied'}`,
      candidate_id: app.candidate_id,
      requisition_id: app.requisition_id,
    }))
  }, [applications])

  const createMutation = useMutation({
    mutationFn: (payload: any) => documentsApi.createOffer(payload),
    onSuccess: () => {
      message.success('Offer created')
      setCreateOpen(false)
      createForm.resetFields()
      queryClient.invalidateQueries({ queryKey: ['company-offers'] })
    },
    onError: (err: any) => message.error(err?.response?.data?.message || 'Failed to create offer'),
  })

  const submitApprovalMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: any }) => documentsApi.submitOfferApproval(id, payload),
    onSuccess: () => {
      message.success('Approval flow submitted')
      setApprovalOpen(false)
      approvalForm.resetFields()
      queryClient.invalidateQueries({ queryKey: ['company-offers'] })
    },
  })

  const approveMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: any }) => documentsApi.approveOffer(id, payload),
    onSuccess: () => {
      message.success('Approval decision recorded')
      queryClient.invalidateQueries({ queryKey: ['company-offers'] })
    },
  })

  const negotiateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: any }) => documentsApi.negotiateOffer(id, payload),
    onSuccess: () => {
      message.success('Negotiation updated')
      setNegotiationOpen(false)
      negotiationForm.resetFields()
      queryClient.invalidateQueries({ queryKey: ['company-offers'] })
    },
  })

  const sendMutation = useMutation({
    mutationFn: (id: string) => documentsApi.sendOffer(id),
    onSuccess: () => {
      message.success('Offer sent')
      queryClient.invalidateQueries({ queryKey: ['company-offers'] })
    },
  })

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <Title level={4} className="!m-0">Company Offer Management</Title>
          <Text className="text-slate-500">Create, approve, negotiate, and track offer responses.</Text>
        </div>
        <Button type="primary" onClick={() => setCreateOpen(true)}>Create Offer</Button>
      </div>

      <Card>
        <Table
          rowKey="id"
          loading={isLoading}
          dataSource={offers}
          pagination={{ pageSize: 10 }}
          columns={[
            { title: 'Offer', render: (_, row: any) => <div><div className="font-semibold">{row.title || 'Offer Letter'}</div><div className="text-xs text-slate-500">{row.id}</div></div> },
            { title: 'Candidate', dataIndex: 'candidate_id' },
            { title: 'Salary', render: (_, row: any) => `${row.currency || 'INR'} ${row.offered_salary || '-'}` },
            { title: 'Joining', render: (_, row: any) => row.joining_date ? dayjs(row.joining_date).format('YYYY-MM-DD') : '-' },
            { title: 'Status', dataIndex: 'status', render: (value: string) => <Tag color={STATUS_COLORS[value] || 'default'}>{value}</Tag> },
            {
              title: 'Actions',
              render: (_, row: any) => (
                <Space>
                  <Button size="small" onClick={() => { setActiveOffer(row); setApprovalOpen(true) }}>Approval</Button>
                  <Button size="small" onClick={() => { setActiveOffer(row); setNegotiationOpen(true) }}>Negotiate</Button>
                  <Button size="small" onClick={() => sendMutation.mutate(row.id)} loading={sendMutation.isPending}>Send</Button>
                  <Button size="small" onClick={() => approveMutation.mutate({ id: row.id, payload: { approval_role: 'hiring_manager' } })} loading={approveMutation.isPending}>Approve</Button>
                </Space>
              ),
            },
          ]}
        />
      </Card>

      <Modal title="Create Offer" open={createOpen} onCancel={() => setCreateOpen(false)} onOk={() => createForm.submit()} confirmLoading={createMutation.isPending} destroyOnHidden>
        <Form
          form={createForm}
          layout="vertical"
          onFinish={(values) => {
            const app = applicationOptions.find((item: any) => item.value === values.application_id)
            createMutation.mutate({
              application_id: values.application_id,
              candidate_id: app?.candidate_id,
              title: values.title || 'Offer Letter',
              offered_salary: values.offered_salary,
              currency: values.currency,
              joining_date: values.joining_date,
              expires_at: values.expires_at,
              metadata: {
                offer_context: {
                  job_id: app?.requisition_id,
                  location: values.location,
                  employment_type: values.employment_type,
                  notes: values.notes || '',
                },
              },
            })
          }}
        >
          <Form.Item name="application_id" label="Application" rules={[{ required: true }]}><Select showSearch optionFilterProp="label" options={applicationOptions} /></Form.Item>
          <Form.Item name="title" label="Title"><Input /></Form.Item>
          <Form.Item name="offered_salary" label="Salary" rules={[{ required: true }]}><InputNumber className="w-full" min={1} /></Form.Item>
          <Form.Item name="currency" label="Currency" initialValue="INR" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="joining_date" label="Joining Date (YYYY-MM-DD)" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="expires_at" label="Expiry (ISO DateTime)"><Input /></Form.Item>
          <Form.Item name="location" label="Location"><Input /></Form.Item>
          <Form.Item name="employment_type" label="Employment Type"><Input /></Form.Item>
          <Form.Item name="notes" label="Notes"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>

      <Modal title="Offer Approval Flow" open={approvalOpen} onCancel={() => setApprovalOpen(false)} onOk={() => approvalForm.submit()} confirmLoading={submitApprovalMutation.isPending} destroyOnHidden>
        <Form
          form={approvalForm}
          layout="vertical"
          initialValues={{ mode: 'single', roles: ['hiring_manager'] }}
          onFinish={(values) => {
            if (!activeOffer) return
            submitApprovalMutation.mutate({
              id: activeOffer.id,
              payload: { mode: values.mode, roles: values.roles, required_approvals: values.required_approvals },
            })
          }}
        >
          <Form.Item name="mode" label="Mode" rules={[{ required: true }]}><Select options={[{ value: 'none', label: 'No Approval' }, { value: 'single', label: 'Single Approval' }, { value: 'multi', label: 'Multi Approval' }]} /></Form.Item>
          <Form.Item name="roles" label="Approval Roles"><Select mode="multiple" options={[{ value: 'hiring_manager', label: 'Hiring Manager' }, { value: 'finance', label: 'Finance' }, { value: 'hr', label: 'HR' }]} /></Form.Item>
          <Form.Item name="required_approvals" label="Required Approvals"><InputNumber className="w-full" min={0} /></Form.Item>
        </Form>
      </Modal>

      <Modal title="Offer Negotiation" open={negotiationOpen} onCancel={() => setNegotiationOpen(false)} onOk={() => negotiationForm.submit()} confirmLoading={negotiateMutation.isPending} destroyOnHidden>
        <Form
          form={negotiationForm}
          layout="vertical"
          initialValues={{ negotiation_round: 1 }}
          onFinish={(values) => {
            if (!activeOffer) return
            negotiateMutation.mutate({
              id: activeOffer.id,
              payload: {
                counter_salary: values.counter_salary,
                notes: values.notes,
                negotiation_round: values.negotiation_round,
              },
            })
          }}
        >
          <Form.Item name="counter_salary" label="Counter Salary"><InputNumber className="w-full" min={1} /></Form.Item>
          <Form.Item name="negotiation_round" label="Negotiation Round"><InputNumber className="w-full" min={1} /></Form.Item>
          <Form.Item name="notes" label="Notes"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
