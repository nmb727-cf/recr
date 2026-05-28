import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Typography, Button, Space, Divider, Descriptions, Tag, Spin, message, Result } from 'antd'
import { 
  CheckCircleOutlined, 
  SafetyCertificateOutlined, 
  PercentageOutlined, 
  ClockCircleOutlined,
  GlobalOutlined
} from '@ant-design/icons'
import http from '@/utils/http'

const { Title, Text, Paragraph } = Typography

export default function PortalAcceptPage() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [portalData, setPortalData] = useState<any>(null)
  const [accepting, setAccepting] = useState(false)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    fetchPortalDetails()
  }, [token])

  const fetchPortalDetails = async () => {
    try {
      const response = await http.get(`/agencies/portal/accept/${token}/`)
      setPortalData(response.data.data)
    } catch (err: any) {
      setError(err?.response?.data?.message || 'Invalid or expired invitation token.')
    } finally {
      setLoading(false)
    }
  }

  const handleAccept = async () => {
    setAccepting(true)
    try {
      await http.post(`/agencies/portal/accept/${token}/`)
      setSuccess(true)
      message.success('Partnership activated successfully')
    } catch (err: any) {
      message.error(err?.response?.data?.message || 'Failed to accept invitation')
    } finally {
      setAccepting(false)
    }
  }

  if (loading) return <div className="h-screen flex items-center justify-center"><Spin size="large" tip="Verifying invitation..." /></div>

  if (error) return (
    <div className="h-screen flex items-center justify-center p-4">
      <Result
        status="error"
        title="Invitation Error"
        subTitle={error}
        extra={<Button type="primary" onClick={() => navigate('/login')}>Return to Login</Button>}
      />
    </div>
  )

  if (success) return (
    <div className="h-screen flex items-center justify-center p-4">
      <Result
        status="success"
        title="Partnership Active!"
        subTitle={`You are now successfully connected with ${portalData?.portal_name}. You can now start collaborating on jobs and candidates.`}
        extra={[
          <Button type="primary" key="dash" onClick={() => navigate('/dashboard')}>
            Go to Dashboard
          </Button>
        ]}
      />
    </div>
  )

  const { terms, portal_name, portal_type } = portalData

  return (
    <div className="min-h-screen bg-slate-50 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-2xl mb-4">
            <SafetyCertificateOutlined className="text-blue-600 text-3xl" />
          </div>
          <Title level={2}>Partnership Invitation</Title>
          <Paragraph type="secondary">
            <Text strong>{portal_name}</Text> has invited you to collaborate as a 
            <Tag color="blue" className="ml-2">{portal_type === 'agency_guest' ? 'Agency Partner' : 'Client Partner'}</Tag>
          </Paragraph>
        </div>

        <Card bordered={false} className="shadow-lg rounded-3xl overflow-hidden">
          <div className="p-8">
            <Title level={4} className="mb-6">Review Service Terms</Title>
            
            <Descriptions column={1} bordered size="small" className="bg-white">
              <Descriptions.Item label={<span><PercentageOutlined className="mr-2" /> Commission</span>}>
                <Text strong>{terms.commission_percentage}%</Text> ({terms.commission_type})
              </Descriptions.Item>
              <Descriptions.Item label={<span><ClockCircleOutlined className="mr-2" /> Submission SLA</span>}>
                <Text strong>{terms.sla_submission_hours} Hours</Text>
              </Descriptions.Item>
              <Descriptions.Item label={<span><CheckCircleOutlined className="mr-2" /> Feedback SLA</span>}>
                <Text strong>{terms.sla_feedback_hours} Hours</Text>
              </Descriptions.Item>
              <Descriptions.Item label={<span><GlobalOutlined className="mr-2" /> Candidate Retention</span>}>
                <Text strong>{terms.retention_days} Days</Text>
              </Descriptions.Item>
              <Descriptions.Item label={<span><SafetyCertificateOutlined className="mr-2" /> Replacement Guarantee</span>}>
                <Text strong>{terms.replacement_guarantee_days} Days</Text>
              </Descriptions.Item>
            </Descriptions>

            <div className="mt-8 bg-blue-50 p-6 rounded-2xl border border-blue-100">
              <Text type="secondary" className="text-sm italic">
                "By clicking 'Accept & Join', you agree to the service terms listed above. 
                These terms will be legally bound and snapshotted for all future placements under this partnership."
              </Text>
            </div>
          </div>

          <div className="bg-slate-50 p-8 flex gap-4 border-t border-slate-100">
            <Button size="large" className="flex-1 rounded-xl" onClick={() => navigate('/login')}>
              Decline
            </Button>
            <Button 
              type="primary" 
              size="large" 
              className="flex-1 rounded-xl bg-blue-600 border-none shadow-md"
              loading={accepting}
              onClick={handleAccept}
            >
              Accept & Join
            </Button>
          </div>
        </Card>
      </div>
    </div>
  )
}
