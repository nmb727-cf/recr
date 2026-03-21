import {
  Button, Col, Descriptions, Row, Space, Steps, Tag,
  Typography, Spin, message, Empty, Modal, Input, Divider,
} from 'antd'
import {
  SendOutlined, CheckOutlined, CloseOutlined,
  GlobalOutlined, CopyOutlined, TeamOutlined,
} from '@ant-design/icons'
import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useApiQuery } from '@/hooks/useApiQuery'
import { requisitionsApi } from '@/api/jobs'
import { pipelineApi } from '@/api/pipeline'
import { useNavigate } from 'react-router-dom'
import type { JobRequisition, JobStage } from '@/types'

const { Title, Text, Paragraph } = Typography

const STAGE_STATUS_MAP: Record<string, number> = {
  draft: 0,
  pending_approval: 1,
  approved: 2,
  active: 3,
  closed: 4,
}

export default function JobDetailPanel({ jobId, onActionSuccess }: { jobId: string, onActionSuccess?: () => void }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [rejectModalOpen, setRejectModalOpen] = useState(false)
  const [rejectReason, setRejectReason] = useState('')

  const { data, isLoading } = useApiQuery(
    ['requisition', jobId],
    () => requisitionsApi.get(jobId)
  )

  const { data: pipelineData } = useApiQuery(
    ['pipeline', 'count', jobId],
    () => pipelineApi.getPipeline(jobId),
    { enabled: !!jobId }
  )

  const requisition = (data as { requisition: JobRequisition; stages: JobStage[] } | undefined)?.requisition
  const totalApplications = (pipelineData as any)?.total_applications ?? 0

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['requisition', jobId] })
    queryClient.invalidateQueries({ queryKey: ['requisitions'] })
    if (onActionSuccess) onActionSuccess()
  }

  const doAction = async (
    label: string,
    fn: () => Promise<unknown>
  ) => {
    setActionLoading(label)
    try {
      await fn()
      message.success(`${label} successful`)
      invalidate()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message
      message.error(msg ?? `${label} failed`)
    } finally {
      setActionLoading(null)
    }
  }

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
        <Spin />
      </div>
    )
  }

  if (!requisition) {
    return <Empty description="Job not found" />
  }

  const statusStep = STAGE_STATUS_MAP[requisition.status] ?? 0

  return (
    <div>
      {/* ── Actions ──────────────────────────────────────────────────────── */}
      <Space wrap style={{ marginBottom: 20 }}>
        {/* Clone always available */}
        <Button
          icon={<CopyOutlined />}
          loading={actionLoading === 'Clone'}
          onClick={() => doAction('Clone', () => requisitionsApi.clone(requisition.id))}
        >
          Clone
        </Button>

        {requisition.status === 'draft' && (
          <Button
            type="primary"
            icon={<SendOutlined />}
            loading={actionLoading === 'Submit'}
            onClick={() => doAction('Submit', () => requisitionsApi.submitForApproval(requisition.id))}
          >
            Submit for Approval
          </Button>
        )}

        {requisition.status === 'pending_approval' && (
          <>
            <Button
              danger
              icon={<CloseOutlined />}
              loading={actionLoading === 'Reject'}
              onClick={() => setRejectModalOpen(true)}
            >
              Reject
            </Button>
            <Button
              type="primary"
              icon={<CheckOutlined />}
              loading={actionLoading === 'Approve'}
              onClick={() => doAction('Approve', () => requisitionsApi.approve(requisition.id))}
            >
              Approve
            </Button>
          </>
        )}

        {requisition.status === 'approved' && (
          <Button
            type="primary"
            icon={<GlobalOutlined />}
            loading={actionLoading === 'Publish'}
            onClick={() => doAction('Publish', () => requisitionsApi.publish(requisition.id))}
          >
            Publish Job
          </Button>
        )}

        {requisition.status === 'active' && (
          <Button
            icon={<TeamOutlined />}
            onClick={() => navigate(`/pipeline?job=${requisition.id}`)}
          >
            View Pipeline
          </Button>
        )}
      </Space>

      <Divider style={{ margin: '0 0 20px' }} />

      <Row gutter={16}>
        <Col span={24}>
          <div style={{ marginBottom: 20 }}>
            <Title level={5}>Status</Title>
            <Steps
              current={statusStep}
              size="small"
              items={[
                { title: 'Draft' },
                { title: 'Pending' },
                { title: 'Approved' },
                { title: 'Active' },
                { title: 'Closed' },
              ]}
            />
          </div>

          <Descriptions column={1} size="small" labelStyle={{ color: '#8c8c8c', fontWeight: 500, width: 120 }}>
            <Descriptions.Item label="Job Type">
              {requisition.job_type.replace(/_/g, ' ')}
            </Descriptions.Item>
            <Descriptions.Item label="Work Mode">{requisition.work_mode}</Descriptions.Item>
            <Descriptions.Item label="Experience">
              {requisition.experience_min}–{requisition.experience_max} years
            </Descriptions.Item>
            <Descriptions.Item label="Headcount">{requisition.headcount}</Descriptions.Item>
            {requisition.salary_visible && (
              <Descriptions.Item label="Salary Range">
                {requisition.salary_currency} {Number(requisition.salary_min).toLocaleString()} –{' '}
                {Number(requisition.salary_max).toLocaleString()}
              </Descriptions.Item>
            )}
            <Descriptions.Item label="Applications">
              <Text strong>{totalApplications}</Text>
            </Descriptions.Item>
          </Descriptions>

          <Divider />

          {requisition.skills_required?.length > 0 && (
            <div style={{ marginBottom: 20 }}>
              <Title level={5}>Skills Required</Title>
              <Space size={[8, 8]} wrap>
                {requisition.skills_required.map((s) => (
                  <Tag key={s} color="blue">{s}</Tag>
                ))}
              </Space>
            </div>
          )}

          {requisition.description && (
            <div style={{ marginBottom: 20 }}>
              <Title level={5}>Description</Title>
              <Paragraph style={{ whiteSpace: 'pre-wrap', margin: 0, color: '#595959' }}>
                {requisition.description}
              </Paragraph>
            </div>
          )}

          {requisition.requirements && (
            <div style={{ marginBottom: 20 }}>
              <Title level={5}>Requirements</Title>
              <Paragraph style={{ whiteSpace: 'pre-wrap', margin: 0, color: '#595959' }}>
                {requisition.requirements}
              </Paragraph>
            </div>
          )}
        </Col>
      </Row>

      {/* ── Reject modal ─────────────────────────────────────────────────── */}
      <Modal
        title="Reject Requisition"
        open={rejectModalOpen}
        onCancel={() => setRejectModalOpen(false)}
        onOk={async () => {
          await doAction('Reject', () => requisitionsApi.reject(requisition.id, rejectReason))
          setRejectModalOpen(false)
          setRejectReason('')
        }}
        okText="Reject"
        okButtonProps={{ danger: true, loading: actionLoading === 'Reject' }}
      >
        <Text type="secondary">Provide an optional reason for rejection:</Text>
        <Input.TextArea
          style={{ marginTop: 12 }}
          rows={3}
          value={rejectReason}
          onChange={(e) => setRejectReason(e.target.value)}
          placeholder="e.g. Budget not approved yet"
        />
      </Modal>
    </div>
  )
}
