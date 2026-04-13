import React, { useState } from 'react'
import { Card, Table, Tag, Typography, Button, Modal, Form, Select, message, Space, Divider, Spin, Alert } from 'antd'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { hdcApi } from '@/api/hdc'
import { candidatesApi } from '@/api/candidates'
import { pipelineApi } from '@/api/pipeline'
import { Banknote, Plus } from 'lucide-react'
import { useNavigate, useSearchParams } from 'react-router-dom'

const { Text } = Typography

export default function Compensation() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [form] = Form.useForm()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const applicationIdFromUrl = searchParams.get('applicationId')

  // ─── Data Fetching ───
  const { data: recommendationsData, isLoading: loadingRecommendations, isError } = useApiQuery(
    ['hdc-offer-recommendations'],
    () => hdcApi.listOfferRecommendations()
  )
  const { data: candidatesData } = useApiQuery(['candidates-list'], () => candidatesApi.list())
  const { data: applicationsData } = useApiQuery(['pipeline-applications'], () => pipelineApi.listApplications())

  // ─── Mutations ───
  const createMutation = useMutation({
    mutationFn: (values: any) => hdcApi.createOfferRecommendation(values),
    onSuccess: () => {
      message.success('Offer recommendation scenario initialized')
      setIsModalOpen(false)
      form.resetFields()
      queryClient.invalidateQueries({ queryKey: ['hdc-offer-recommendations'] })
    },
    onError: () => message.error('Failed to initialize offer package'),
  })

  React.useEffect(() => {
    if (isModalOpen && applicationIdFromUrl) {
      form.setFieldsValue({ application_id: applicationIdFromUrl })
    }
  }, [isModalOpen, applicationIdFromUrl, form])

  let recommendations = (recommendationsData as any)?.data || (Array.isArray(recommendationsData) ? recommendationsData : [])
  if (applicationIdFromUrl) {
    recommendations = recommendations.filter((r: any) => r.application_id === applicationIdFromUrl)
  }
  const candidates = (candidatesData as any)?.candidates || (candidatesData as any)?.data?.candidates || []
  const applications = (applicationsData as any)?.applications || (applicationsData as any)?.data?.applications || []
  const appById = new Map<string, any>(applications.map((app: any) => [app.id, app]))
  const candidateById = new Map<string, any>(candidates.map((c: any) => [c.id, c]))

  const handleCreate = (values: any) => {
    createMutation.mutate({
      application_id: values.application_id,
      status: 'draft',
    })
  }

  const columns = [
    {
      title: 'Candidate',
      dataIndex: 'application_id',
      key: 'candidate',
      render: (applicationId: string) =>
        candidateById.get(appById.get(applicationId)?.candidate_id)?.full_name || 'Hiring Candidate',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'locked' ? 'green' : 'blue'}>{status?.toUpperCase()}</Tag>
      ),
    },
    {
      title: 'Scenarios',
      dataIndex: 'scenarios',
      key: 'scenarios',
      render: (list: any[]) => <Text className="text-xs">{list?.length || 0} Models</Text>,
    },
    {
      title: 'Action',
      key: 'action',
      render: () => (
        <Space>
          <Button
            size="small"
            type="primary"
            onClick={() => navigate('/hiring-decisions/offer-intelligence')}
          >
            Model Package
          </Button>
          <Button
            size="small"
            onClick={() => navigate('/hiring-decisions/approvals')}
          >
            Finance Approval
          </Button>
        </Space>
      ),
    },
  ]

  if (isError) {
    return <Alert type="error" message="Failed to load compensation packages. Please refresh." showIcon className="my-4" />
  }

  return (
    <div className="space-y-6">
      <Card
        className="rounded-3xl border-slate-200 shadow-sm"
        title={
          <div className="flex items-center gap-2">
            <Banknote className="h-5 w-5 text-emerald-500" />
            <span>Compensation Management</span>
          </div>
        }
        extra={
          <Button type="primary" icon={<Plus size={16} />} onClick={() => setIsModalOpen(true)}>
            Create New Package
          </Button>
        }
      >
        {loadingRecommendations ? (
          <div className="py-12 text-center"><Spin /></div>
        ) : (
          <Table
            columns={columns}
            dataSource={recommendations}
            rowKey="id"
            locale={{ emptyText: <EmptyState title="No compensation packages in progress" /> }}
          />
        )}
      </Card>

      <Modal
        title="Initialize Offer Package"
        open={isModalOpen}
        onCancel={() => { setIsModalOpen(false); form.resetFields() }}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="application_id" label="Finalist Application" rules={[{ required: true }]}>
            <Select placeholder="Choose application..." showSearch optionFilterProp="children">
              {applications.map((app: any) => (
                <Select.Option key={app.id} value={app.id}>
                  {candidateById.get(app.candidate_id)?.full_name || 'Candidate'}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Divider className="!text-[10px] uppercase font-bold text-slate-400">
            Next Step
          </Divider>
          <Text className="text-xs text-slate-500">
            After initializing, use <strong>Model Package</strong> to run AI scenario modeling in Offer Intelligence.
          </Text>
        </Form>
      </Modal>
    </div>
  )
}

function EmptyState({ title }: { title: string }) {
  return (
    <div className="py-8 text-center">
      <Banknote className="mx-auto h-12 w-12 text-slate-200" />
      <Text className="mt-2 block font-bold text-slate-400">{title}</Text>
    </div>
  )
}
