import React, { useMemo, useState, useEffect } from 'react'
import { Card, Table, Tag, Typography, Button, Modal, Form, Input, Select, message, Space, Switch, Spin, Alert } from 'antd'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { hdcApi } from '@/api/hdc'
import { requisitionsApi } from '@/api/jobs'
import { candidatesApi } from '@/api/candidates'
import { pipelineApi } from '@/api/pipeline'
import { Layers, Plus, Zap } from 'lucide-react'
import { useNavigate, useSearchParams } from 'react-router-dom'

const { Text, Title } = Typography

export default function CandidateComparison() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [form] = Form.useForm()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  // ─── Data Fetching ───
  const { data: comparisonsData, isLoading: loadingComparisons, isError } = useApiQuery(
    ['hdc-comparisons'],
    () => hdcApi.listComparisons()
  )
  const { data: jobsData } = useApiQuery(['jobs-list'], () => requisitionsApi.list({ status: 'active' }))
  const { data: candidatesData } = useApiQuery(['candidates-list'], () => candidatesApi.list())
  const { data: applicationsData } = useApiQuery(['pipeline-applications'], () => pipelineApi.listApplications())

  // ─── Mutations ───
  const createMutation = useMutation({
    mutationFn: (values: any) => hdcApi.createComparison(values),
    onSuccess: () => {
      message.success('Comparison set created')
      setIsModalOpen(false)
      form.resetFields()
      queryClient.invalidateQueries({ queryKey: ['hdc-comparisons'] })
    },
    onError: () => message.error('Failed to create comparison'),
  })

  const freezeMutation = useMutation({
    mutationFn: (id: string) => hdcApi.freezeComparison(id),
    onSuccess: () => {
      message.success('Comparison frozen and locked')
      queryClient.invalidateQueries({ queryKey: ['hdc-comparisons'] })
    },
    onError: () => message.error('Failed to freeze comparison'),
  })

  const comparisons = (comparisonsData as any)?.data || (Array.isArray(comparisonsData) ? comparisonsData : [])
  const jobs = (jobsData as any)?.requisitions || (jobsData as any)?.data?.requisitions || []
  const candidates = (candidatesData as any)?.candidates || (candidatesData as any)?.data?.candidates || []
  const applications = (applicationsData as any)?.applications || (applicationsData as any)?.data?.applications || []
  const selectedJobId = Form.useWatch('job_id', form)
  const applicationIdFromUrl = searchParams.get('applicationId')

  useEffect(() => {
    if (isModalOpen && applicationIdFromUrl) {
      const app = applications.find((a: any) => a.id === applicationIdFromUrl)
      if (app) {
        form.setFieldsValue({
          job_id: app.requisition_id,
          finalist_application_ids: [app.id]
        })
      }
    }
  }, [isModalOpen, applicationIdFromUrl, applications, form])
  const candidateById = useMemo(
    () => new Map<string, any>(candidates.map((c: any) => [c.id, c])),
    [candidates]
  )
  const applicationOptions = useMemo(
    () => applications.filter((a: any) => !selectedJobId || a.requisition_id === selectedJobId),
    [applications, selectedJobId]
  )

  const handleCreate = (values: any) => {
    const selectedApps = applications.filter((a: any) => values.finalist_application_ids?.includes(a.id))
    const candidateIds = [...new Set(selectedApps.map((a: any) => a.candidate_id))]
    if (!candidateIds.length) {
      message.error('Please select valid candidate applications.')
      return
    }
    createMutation.mutate({
      name: values.name,
      requisition_id: values.job_id,
      candidate_ids: candidateIds,
      weights_enabled: values.weights_enabled ?? false,
      status: 'active',
    })
  }

  const columns = [
    { title: 'Comparison Set', dataIndex: 'name', key: 'name' },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'frozen' ? 'cyan' : 'blue'}>{status?.toUpperCase()}</Tag>
      ),
    },
    {
      title: 'Candidates',
      dataIndex: 'candidates',
      key: 'candidates',
      render: (list: any[]) => <Text className="text-xs">{list?.length || 0} Finalists</Text>,
    },
    {
      title: 'Weights',
      dataIndex: 'weights_enabled',
      key: 'weights',
      render: (enabled: boolean) =>
        enabled ? <Tag color="purple">Weighted</Tag> : <Text className="text-xs text-slate-400">Standard</Text>,
    },
    {
      title: 'Action',
      key: 'action',
      render: (_: any, record: any) => (
        <Space>
          <Button
            size="small"
            type="link"
            onClick={() => setSearchParams({ comparisonId: record.id })}
          >
            Compare Matrix
          </Button>
          <Button
            size="small"
            onClick={() => freezeMutation.mutate(record.id)}
            disabled={record.status === 'frozen'}
            loading={freezeMutation.isPending}
          >
            Freeze
          </Button>
        </Space>
      ),
    },
  ]

  const activeComparisonId = searchParams.get('comparisonId')
  const activeComparison = comparisons.find((c: any) => c.id === activeComparisonId)

  if (activeComparison) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Button icon={<Layers size={14} />} onClick={() => setSearchParams({})}>Back to Sets</Button>
          <Title level={4} className="!m-0">{activeComparison.name}</Title>
          <Tag color={activeComparison.status === 'frozen' ? 'cyan' : 'blue'}>{activeComparison.status?.toUpperCase()}</Tag>
        </div>

        <Card className="rounded-[2rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
          <Table
            pagination={false}
            columns={[
              { title: 'Evaluation Parameter', dataIndex: 'metric', key: 'metric', fixed: 'left', width: 200, render: (t) => <Text strong>{t}</Text> },
              ...(activeComparison.candidates || []).map((cand: any) => ({
                title: candidateById.get(cand.candidate_id)?.full_name || 'Candidate',
                key: cand.id,
                align: 'center' as const,
                render: () => <div className="py-4">
                  <div className="text-2xl font-black text-slate-800">{cand.score || '0.0'}</div>
                  <Text className="text-[10px] text-slate-400 font-bold uppercase">Weighted Score</Text>
                </div>
              }))
            ]}
            dataSource={[
              { key: '1', metric: 'Technical Fit' },
              { key: '2', metric: 'Leadership' },
              { key: '3', metric: 'Culture Score' },
              { key: '4', metric: 'Experience' },
              { key: '5', metric: 'Expected CTC' },
            ]}
          />
        </Card>
      </div>
    )
  }

  if (isError) {
    return <Alert type="error" message="Failed to load comparisons. Please refresh." showIcon className="my-4" />
  }

  return (
    <div className="space-y-6">
      <Card
        className="rounded-3xl border-slate-200 shadow-sm"
        title={
          <div className="flex items-center gap-2">
            <Layers className="h-5 w-5 text-indigo-500" />
            <span>Candidate Comparison Engine</span>
          </div>
        }
        extra={
          <Button type="primary" icon={<Plus size={16} />} onClick={() => setIsModalOpen(true)}>
            New Comparison
          </Button>
        }
      >
        {loadingComparisons ? (
          <div className="py-12 text-center"><Spin /></div>
        ) : (
          <Table
            columns={columns}
            dataSource={comparisons}
            rowKey="id"
            locale={{ emptyText: <EmptyState title="No comparison sets created" /> }}
          />
        )}
      </Card>

      <Modal
        title="Create Comparison Set"
        open={isModalOpen}
        onCancel={() => { setIsModalOpen(false); form.resetFields() }}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="Set Name" rules={[{ required: true }]}>
            <Input placeholder="e.g. Frontend Finalists - April Batch" />
          </Form.Item>
          <Form.Item name="job_id" label="Reference Job" rules={[{ required: true }]}>
            <Select placeholder="Choose job context..." showSearch optionFilterProp="children">
              {jobs.map((j: any) => (
                <Select.Option key={j.id} value={j.id}>{j.title}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="finalist_application_ids" label="Add Finalists" rules={[{ required: true }]}>
            <Select mode="multiple" placeholder="Select applications to compare...">
              {applicationOptions.map((app: any) => (
                <Select.Option key={app.id} value={app.id}>
                  {candidateById.get(app.candidate_id)?.full_name || 'Candidate'}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <div className="p-4 bg-indigo-50 rounded-2xl border border-indigo-100 mb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Zap size={16} className="text-indigo-600" />
                <Text className="text-xs font-bold text-indigo-900 uppercase">Weighted Comparison</Text>
              </div>
              <Form.Item name="weights_enabled" valuePropName="checked" noStyle initialValue={false}>
                <Switch size="small" />
              </Form.Item>
            </div>
            <Text className="mt-1 block text-[10px] text-indigo-600">
              Apply custom scoring weights to technical skills, culture fit, and notice period.
            </Text>
          </div>
        </Form>
      </Modal>
    </div>
  )
}

function EmptyState({ title }: { title: string }) {
  return (
    <div className="py-8 text-center">
      <Layers className="mx-auto h-12 w-12 text-slate-200" />
      <Text className="mt-2 block font-bold text-slate-400">{title}</Text>
    </div>
  )
}
