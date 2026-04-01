import { Button, Card, Result } from 'antd'
import { useNavigate } from 'react-router-dom'

export default function CandidateInterviewExpired() {
  const navigate = useNavigate()
  return (
    <Card>
      <Result
        status="warning"
        title="Interview Link Expired"
        subTitle="Your interview access window has expired. Please contact your recruiter for a reschedule."
        extra={<Button type="primary" onClick={() => navigate('/candidate/interviews')}>Back to Interviews</Button>}
      />
    </Card>
  )
}

