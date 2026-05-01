import { useEffect } from 'react'
import { Button, Card, Form, Input, Space, Table, Typography } from 'antd'

import { useApiQuery } from '@/hooks/useApiQuery'
import { masterAdminApi } from '@/api/masterAdmin'

const { Title, Text } = Typography

export default function MasterAdminSettings() {
  const { data, refetch, isLoading } = useApiQuery(
    ['master-admin', 'platform-settings'],
    () => masterAdminApi.listPlatformSettings()
  )
  const settings = (data as any)?.data?.data?.settings || []
  const [form] = Form.useForm()

  useEffect(() => {
    const initial: Record<string, string> = {}
    settings.forEach((row: any) => {
      initial[row.key] = JSON.stringify(row.value_json || {}, null, 2)
    })
    form.setFieldsValue(initial)
  }, [settings, form])

  return (
    <div className="space-y-4">
      <Title level={3} style={{ marginBottom: 0 }}>Platform Settings</Title>
      <Text type="secondary">Safe operational settings for platform-level governance.</Text>

      <Card>
        <Form
          form={form}
          layout="vertical"
          onFinish={async (values) => {
            const payload = settings.map((row: any) => ({
              key: row.key,
              value_json: JSON.parse(values[row.key] || '{}'),
            }))
            await masterAdminApi.updatePlatformSettings(payload)
            await refetch()
          }}
        >
          <Table
            loading={isLoading}
            rowKey="key"
            pagination={false}
            dataSource={settings}
            columns={[
              { title: 'Key', dataIndex: 'key' },
              { title: 'Category', dataIndex: 'category' },
              { title: 'Description', dataIndex: 'description' },
              {
                title: 'Value',
                render: (_: any, row: any) => (
                  <Form.Item
                    name={row.key}
                    style={{ marginBottom: 0 }}
                    rules={[
                      {
                        validator: async (_, value) => {
                          try {
                            JSON.parse(value || '{}')
                          } catch {
                            throw new Error('Invalid JSON')
                          }
                        },
                      },
                    ]}
                  >
                    <Input.TextArea rows={4} disabled={!row.is_editable} />
                  </Form.Item>
                ),
              },
            ]}
          />

          <Space style={{ marginTop: 16 }}>
            <Button type="primary" htmlType="submit">Save Platform Settings</Button>
            <Button onClick={() => refetch()}>Refresh</Button>
          </Space>
        </Form>
      </Card>
    </div>
  )
}
