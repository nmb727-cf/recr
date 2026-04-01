import { useState } from 'react'
import { Alert, Button, Card, Form, Input, Select, Space, Switch, Table, Tag, Typography, message } from 'antd'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { interviewsApi } from '@/api/interviews'

const { Title } = Typography

const EXECUTION_MODE_OPTIONS = [
  { value: 'native', label: 'native' },
  { value: 'third_party', label: 'third_party' },
  { value: 'external_manual', label: 'external_manual' },
]

export default function InterviewIntegrations() {
  const qc = useQueryClient()
  const [connectionForm] = Form.useForm()
  const [mappingForm] = Form.useForm()
  const [editingConnection, setEditingConnection] = useState<any | null>(null)

  const providersQ = useQuery({
    queryKey: ['interview_integration_providers'],
    queryFn: async () => (await interviewsApi.listIntegrationProviders()).data?.data?.providers || [],
  })

  const connectionsQ = useQuery({
    queryKey: ['interview_tenant_provider_connections'],
    queryFn: async () => (await interviewsApi.listTenantProviderConnections()).data?.data?.connections || [],
  })

  const mappingsQ = useQuery({
    queryKey: ['interview_execution_mappings'],
    queryFn: async () => (await interviewsApi.listExecutionMappings()).data?.data?.mappings || [],
  })

  const toggleProviderM = useMutation({
    mutationFn: async ({ id, is_active }: { id: string; is_active: boolean }) =>
      interviewsApi.updateIntegrationProvider(id, { is_active }),
    onSuccess: () => {
      message.success('Provider status updated')
      qc.invalidateQueries({ queryKey: ['interview_integration_providers'] })
    },
    onError: () => message.error('Failed to update provider'),
  })

  const saveConnectionM = useMutation({
    mutationFn: async (payload: any) => {
      if (editingConnection?.id) return interviewsApi.updateTenantProviderConnection(editingConnection.id, payload)
      return interviewsApi.saveTenantProviderConnection(payload)
    },
    onSuccess: () => {
      message.success('Tenant provider config saved')
      setEditingConnection(null)
      connectionForm.resetFields()
      qc.invalidateQueries({ queryKey: ['interview_tenant_provider_connections'] })
    },
    onError: () => message.error('Failed to save tenant provider config'),
  })

  const saveMappingM = useMutation({
    mutationFn: async (payload: any) => interviewsApi.createExecutionMapping(payload),
    onSuccess: () => {
      message.success('Execution mapping saved')
      mappingForm.resetFields()
      qc.invalidateQueries({ queryKey: ['interview_execution_mappings'] })
    },
    onError: () => message.error('Failed to save execution mapping'),
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Title level={4} className="!m-0">Interview Integration Engine</Title>
        <Tag color="blue">ICC-INTEGRATION-ENGINE-01</Tag>
      </div>

      <Alert
        type="info"
        showIcon
        message="Provider architecture is ready for native, third-party and external manual execution. Live OAuth/provider calls are intentionally deferred."
      />

      <Card title="Provider Registry">
        <Table
          rowKey="id"
          size="small"
          loading={providersQ.isLoading}
          dataSource={providersQ.data || []}
          pagination={false}
          columns={[
            { title: 'Provider', dataIndex: 'name' },
            { title: 'Code', dataIndex: 'code', render: (v) => <Tag>{v}</Tag> },
            { title: 'Type', dataIndex: 'provider_type' },
            { title: 'Tenant Configurable', dataIndex: 'tenant_configurable', render: (v) => (v ? 'Yes' : 'No') },
            {
              title: 'Active',
              render: (_, row: any) => (
                <Switch
                  checked={!!row.is_active}
                  onChange={(checked) => toggleProviderM.mutate({ id: row.id, is_active: checked })}
                />
              ),
            },
          ]}
        />
      </Card>

      <Card title="Tenant Provider Configuration">
        <Form
          form={connectionForm}
          layout="vertical"
          onFinish={(values) => {
            let auth_data = {}
            let config_data = {}
            try {
              auth_data = values.auth_data_json ? JSON.parse(values.auth_data_json) : {}
            } catch {
              message.error('Auth JSON invalid')
              return
            }
            try {
              config_data = values.config_data_json ? JSON.parse(values.config_data_json) : {}
            } catch {
              message.error('Config JSON invalid')
              return
            }
            saveConnectionM.mutate({
              provider_id: values.provider_id,
              auth_data,
              config_data,
              is_enabled: !!values.is_enabled,
              connection_status: values.connection_status || 'configured',
            })
          }}
        >
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <Form.Item name="provider_id" label="Provider" rules={[{ required: true }]}>
              <Select
                options={(providersQ.data || []).map((p: any) => ({ value: p.id, label: `${p.name} (${p.code})` }))}
              />
            </Form.Item>
            <Form.Item name="connection_status" label="Status" initialValue="configured">
              <Select options={[{ value: 'configured', label: 'configured' }, { value: 'connected', label: 'connected' }, { value: 'error', label: 'error' }]} />
            </Form.Item>
            <Form.Item name="is_enabled" label="Enabled" valuePropName="checked" initialValue={true}>
              <Switch />
            </Form.Item>
            <Form.Item label=" ">
              <Button type="primary" htmlType="submit" loading={saveConnectionM.isPending} block>
                Save Connection
              </Button>
            </Form.Item>
            <Form.Item name="auth_data_json" label="Auth Data Shell (JSON)" className="md:col-span-2">
              <Input.TextArea rows={3} placeholder='{"access_token":"","refresh_token":"","expires_at":""}' />
            </Form.Item>
            <Form.Item name="config_data_json" label="Config Data Shell (JSON)" className="md:col-span-2">
              <Input.TextArea rows={3} placeholder='{"account_email":"","calendar_id":"","webhook_url":""}' />
            </Form.Item>
          </div>
        </Form>

        <Table
          className="mt-3"
          rowKey="id"
          size="small"
          loading={connectionsQ.isLoading}
          dataSource={connectionsQ.data || []}
          pagination={false}
          columns={[
            { title: 'Provider', render: (_, r: any) => r.provider?.name || '-' },
            { title: 'Code', render: (_, r: any) => <Tag>{r.provider?.code || '-'}</Tag> },
            { title: 'Status', dataIndex: 'connection_status' },
            { title: 'Enabled', dataIndex: 'is_enabled', render: (v) => (v ? 'Yes' : 'No') },
            {
              title: 'Actions',
              render: (_, r: any) => (
                <Button
                  size="small"
                  onClick={() => {
                    setEditingConnection(r)
                    connectionForm.setFieldsValue({
                      provider_id: r.provider?.id,
                      connection_status: r.connection_status,
                      is_enabled: r.is_enabled,
                      auth_data_json: JSON.stringify(r.auth_data || {}, null, 2),
                      config_data_json: JSON.stringify(r.config_data || {}, null, 2),
                    })
                  }}
                >
                  Edit
                </Button>
              ),
            },
          ]}
        />
      </Card>

      <Card title="Interview Execution Mapping">
        <Form
          form={mappingForm}
          layout="vertical"
          onFinish={(values) => {
            saveMappingM.mutate({
              interview_type: values.interview_type,
              stage_code: values.stage_code || '',
              execution_mode: values.execution_mode,
              provider_code: values.provider_code || '',
              is_active: true,
            })
          }}
        >
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            <Form.Item name="interview_type" label="Interview Type" rules={[{ required: true }]}>
              <Input placeholder="technical_interview / panel / ai_screening" />
            </Form.Item>
            <Form.Item name="stage_code" label="Stage Code (optional)">
              <Input placeholder="screening / round_2 / final" />
            </Form.Item>
            <Form.Item name="execution_mode" label="Execution Mode" rules={[{ required: true }]} initialValue="native">
              <Select options={EXECUTION_MODE_OPTIONS} />
            </Form.Item>
            <Form.Item name="provider_code" label="Provider Code">
              <Input placeholder="zoom / google_meet / microsoft_teams" />
            </Form.Item>
            <Form.Item label=" ">
              <Button type="primary" htmlType="submit" loading={saveMappingM.isPending} block>Save Mapping</Button>
            </Form.Item>
          </div>
        </Form>

        <Table
          rowKey="id"
          size="small"
          loading={mappingsQ.isLoading}
          dataSource={mappingsQ.data || []}
          pagination={false}
          columns={[
            { title: 'Interview Type', dataIndex: 'interview_type' },
            { title: 'Stage', dataIndex: 'stage_code', render: (v) => v || 'default' },
            { title: 'Execution Mode', dataIndex: 'execution_mode', render: (v) => <Tag color={v === 'native' ? 'green' : v === 'third_party' ? 'blue' : 'orange'}>{v}</Tag> },
            { title: 'Provider', dataIndex: 'provider_code', render: (v) => v || '-' },
            { title: 'Active', dataIndex: 'is_active', render: (v) => (v ? 'Yes' : 'No') },
          ]}
        />
      </Card>

      <Card title="External Manual Tracking">
        <p className="text-slate-600 mb-0">
          Interviews mapped to <b>external_manual</b> remain fully trackable in-system for scheduling state, feedback, and decision workflow.
        </p>
      </Card>
    </div>
  )
}

