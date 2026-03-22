import { Card, Empty, Typography } from 'antd'

const { Title, Text } = Typography

export default function Leads() {
  return (
    <div className="p-6">
      <Card className="border border-slate-200">
        <div className="py-8">
          <Title level={4} className="!mb-2">Leads</Title>
          <Text className="text-slate-600">
            Leads pipeline is not available in Phase 1 yet.
          </Text>
          <div className="mt-6">
            <Empty description="No leads data available yet" />
          </div>
        </div>
      </Card>
    </div>
  )
}
