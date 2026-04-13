import { Button, Card, Typography } from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

import JobCreateForm from '@/components/forms/JobCreateForm'
import type { JobRequisition } from '@/types'

const { Title, Text } = Typography

export default function JobCreate() {
  const navigate = useNavigate()

  const handleSuccess = (requisition?: JobRequisition) => {
    if (requisition?.id) {
      navigate(`/jobs/${requisition.id}`)
      return
    }
    navigate('/jobs')
  }

  return (
    <div style={{ maxWidth: 980, margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
        <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate('/jobs')} />
        <div>
          <Title level={4} style={{ margin: 0 }}>Create Job Requisition</Title>
          <Text type="secondary">
            Complete role details, ownership, hiring team and workflow defaults.
          </Text>
        </div>
      </div>

      <Card bordered={false} style={{ borderRadius: 12 }}>
        <JobCreateForm onSuccess={handleSuccess} />
      </Card>
    </div>
  )
}
