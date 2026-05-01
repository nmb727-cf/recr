import { useEffect, useState } from 'react'
import { Button, Card, Col, Descriptions, Form, Input, InputNumber, Row, Space, Switch, Tag, Typography } from 'antd'
import { useParams } from 'react-router-dom'

import { useApiQuery } from '@/hooks/useApiQuery'
import { masterAdminApi } from '@/api/masterAdmin'

const { Title } = Typography

export default function MasterAdminTenantDetail() {
  const { id } = useParams<{ id: string }>()
  const [reason, setReason] = useState('')

  const { data, refetch } = useApiQuery(
    ['master-admin', 'tenant', id],
    () => masterAdminApi.getTenant(id as string),
    { enabled: !!id }
  )

  const tenant = (data as any)?.data?.data?.tenant
  const featureFlags = tenant?.feature_flags || {}
  const limits = tenant?.limits || {}

  const [featureForm] = Form.useForm()
  const [limitForm] = Form.useForm()

  useEffect(() => {
    featureForm.setFieldsValue(featureFlags)
    limitForm.setFieldsValue(limits)
  }, [featureFlags, limits, featureForm, limitForm])

  if (!tenant) {
    return <Card loading />
  }

  const refresh = async () => {
    await refetch()
  }

  return (
    <div className="space-y-4">
      <Title level={3} style={{ marginBottom: 0 }}>Tenant Detail</Title>
      <Card>
        <Descriptions bordered column={2} size="small">
          <Descriptions.Item label="Name">{tenant.name}</Descriptions.Item>
          <Descriptions.Item label="Type">{tenant.tenant_type}</Descriptions.Item>
          <Descriptions.Item label="Status"><Tag>{tenant.status}</Tag></Descriptions.Item>
          <Descriptions.Item label="Verification"><Tag>{tenant.verification_state}</Tag></Descriptions.Item>
          <Descriptions.Item label="Schema">{tenant.schema_name}</Descriptions.Item>
          <Descriptions.Item label="Created">{tenant.created_at ? new Date(tenant.created_at).toLocaleString() : '-'}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="Tenant Actions">
        <Space wrap>
          <Button onClick={async () => { await masterAdminApi.verifyTenant(tenant.id); await refresh() }}>Verify</Button>
          <Button danger onClick={async () => { await masterAdminApi.suspendTenant(tenant.id, reason); await refresh() }}>Suspend</Button>
          <Button type="primary" onClick={async () => { await masterAdminApi.reactivateTenant(tenant.id, reason); await refresh() }}>Reactivate</Button>
          <Button danger type="primary" onClick={async () => { await masterAdminApi.deactivateTenant(tenant.id, reason); await refresh() }}>Deactivate</Button>
          <Input
            placeholder="Action reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            style={{ width: 300 }}
          />
        </Space>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="Feature Flags">
            <Form form={featureForm} layout="vertical" onFinish={async (values) => { await masterAdminApi.updateTenantFeatureFlags(tenant.id, values); await refresh() }}>
              {Object.keys(featureFlags).length === 0 ? (
                <Typography.Text type="secondary">No feature flags configured.</Typography.Text>
              ) : (
                Object.keys(featureFlags).map((key) => (
                  <Form.Item key={key} name={key} label={key} valuePropName="checked">
                    <Switch />
                  </Form.Item>
                ))
              )}
              <Button htmlType="submit" type="primary">Save Feature Flags</Button>
            </Form>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Usage Limits">
            <Form form={limitForm} layout="vertical" onFinish={async (values) => { await masterAdminApi.updateTenantLimits(tenant.id, values); await refresh() }}>
              <Form.Item label="User Limit" name="user_limit"><InputNumber min={1} style={{ width: '100%' }} /></Form.Item>
              <Form.Item label="Job Limit" name="job_limit"><InputNumber min={1} style={{ width: '100%' }} /></Form.Item>
              <Form.Item label="Candidate Limit" name="candidate_limit"><InputNumber min={1} style={{ width: '100%' }} /></Form.Item>
              <Button htmlType="submit" type="primary">Save Limits</Button>
            </Form>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
