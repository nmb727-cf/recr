import { Button, Card, Result } from 'antd'
import { useNavigate } from 'react-router-dom'

export default function CandidateInterviewBlocked() {
  const navigate = useNavigate()
  return (
    <Card>
      <Result
        status="403"
        title="Interview Access Blocked"
        subTitle="This interview session is blocked due to security policy (session lock, invalid token, or attempt restriction)."
        extra={<Button type="primary" onClick={() => navigate('/candidate/interviews')}>Back to Interviews</Button>}
      />
    </Card>
  )
}

