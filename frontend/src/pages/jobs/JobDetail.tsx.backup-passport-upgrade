import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Button, Card, Descriptions, Tag,
  Typography, Spin, Empty, Tabs, Table, Avatar,
  Modal, Form, Select, InputNumber, DatePicker, Input,
  message, Divider, Timeline, Space, Dropdown, Progress, Badge, Tooltip
} from 'antd'
import {
  ArrowLeft, Edit, Briefcase,
  Activity, Plus, Users, ShieldCheck, Clock, ExternalLink,
  DollarSign, CheckCircle, Calendar, MoreVertical,
  Scale, Receipt, Zap
} from 'lucide-react'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
dayjs.extend(relativeTime)
import { useTranslation } from 'react-i18next'
import { useApiQuery } from '@/hooks/useApiQuery'
import { requisitionsApi } from '@/api/jobs'
import { pipelineApi } from '@/api/pipeline'
import { interviewsApi } from '@/api/interviews'
import { agenciesApi } from '@/api/agencies'
import { candidatesApi } from '@/api/candidates'
import type { 
  JobRequisition, RequisitionStatus, Application, Candidate, 
  PlacementStatus, CommissionStatus, CommissionBasisType 
} from '@/types'
import { cn } from '@/utils/cn'
import JobTrackingView from './JobTrackingView'
import JobInterviewsTab from './JobInterviewsTab'
import { MetricCard, JobCommandCenterView } from './JobCommandCenterView'
import { useAuthStore } from '@/store/authStore'

const { Text, Paragraph, Title } = Typography

const STATUS_CONFIG: Record<RequisitionStatus, { label: string, color: string, dot: string }> = {
  draft: { label: 'Draft', color: 'bg-slate-100 text-slate-700', dot: 'bg-slate-400' },
  pending_approval: { label: 'Pending', color: 'bg-amber-50 text-amber-700', dot: 'bg-amber-400' },
  approved: { label: 'Approved', color: 'bg-blue-50 text-blue-700', dot: 'bg-blue-400' },
  active: { label: 'Active', color: 'bg-emerald-50 text-emerald-700', dot: 'bg-emerald-500' },
  paused: { label: 'Paused', color: 'bg-amber-100 text-amber-600', dot: 'bg-amber-500' },
  in_guarantee_period: { label: 'Guarantee', color: 'bg-purple-50 text-purple-700', dot: 'bg-purple-500' },
  closed: { label: 'Closed', color: 'bg-rose-50 text-rose-700', dot: 'bg-rose-400' },
  cancelled: { label: 'Cancelled', color: 'bg-slate-100 text-slate-500', dot: 'bg-slate-300' },
}

// ── Modals ──────────────────────────────────────────────────────────

function PlacementModal({
  open,
  application,
  onClose,
  onSuccess,
}: {
  open: boolean
  application: Application | null
  onClose: () => void
  onSuccess: () => void
}) {
  const { t } = useTranslation('jobs')
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (application && open) {
      form.setFieldsValue({
        placement_status: application.placement_status || 'pending_join',
        expected_joining_date: application.expected_joining_date ? dayjs(application.expected_joining_date) : (application.joining_date ? dayjs(application.joining_date) : null),
        joined_at: application.joined_at ? dayjs(application.joined_at) : null,
        placement_confirmed_at: application.placement_confirmed_at ? dayjs(application.placement_confirmed_at) : null,
        note: application.placement_notes || '',
      })
    }
  }, [application, open, form])

  const onFinish = async (values: any) => {
    if (!application) return
    setLoading(true)
    try {
      await pipelineApi.updatePlacement(application.id, {
        ...values,
        expected_joining_date: values.expected_joining_date?.format('YYYY-MM-DD'),
        joined_at: values.joined_at?.format('YYYY-MM-DD'),
        placement_confirmed_at: values.placement_confirmed_at?.format('YYYY-MM-DD'),
      })
      message.success('Placement status updated')
      onSuccess()
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to update placement')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title="Update Placement Status"
      open={open}
      onCancel={onClose}
      onOk={() => form.submit()}
      confirmLoading={loading}
      className="rounded-3xl overflow-hidden"
    >
      <Form form={form} layout="vertical" onFinish={onFinish}>
        <Form.Item name="placement_status" label="Status" rules={[{ required: true }]}>
          <Select>
            <Select.Option value="pending_join">Pending Join</Select.Option>
            <Select.Option value="joined">Joined</Select.Option>
            <Select.Option value="placement_confirmed">Placement Confirmed</Select.Option>
            <Select.Option value="cancelled">Cancelled</Select.Option>
            <Select.Option value="not_applicable">Not Applicable</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item
          noStyle
          shouldUpdate={(prevValues, currentValues) => prevValues.placement_status !== currentValues.placement_status}
        >
          {({ getFieldValue }) => {
            const status = getFieldValue('placement_status')
            return (
              <>
                {(status === 'pending_join' || status === 'joined' || status === 'placement_confirmed') && (
                  <Form.Item name="expected_joining_date" label="Expected Joining Date">
                    <DatePicker className="w-full" />
                  </Form.Item>
                )}
                {(status === 'joined' || status === 'placement_confirmed') && (
                  <Form.Item name="joined_at" label="Actual Joined Date">
                    <DatePicker className="w-full" />
                  </Form.Item>
                )}
                {status === 'placement_confirmed' && (
                  <Form.Item name="placement_confirmed_at" label="Placement Confirmed Date">
                    <DatePicker className="w-full" />
                  </Form.Item>
                )}
              </>
            )
          }}
        </Form.Item>

        <Form.Item name="note" label={t('fields.special_instructions')}>
          <Input.TextArea rows={3} placeholder={t('placeholders.special_instructions')} />
        </Form.Item>
      </Form>
    </Modal>
  )
}

function CommissionModal({
  open,
  application,
  onClose,
  onSuccess,
}: {
  open: boolean
  application: Application | null
  onClose: () => void
  onSuccess: () => void
}) {
  const { t } = useTranslation('jobs')
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (application && open) {
      form.setFieldsValue({
        commission_applicable: application.commission_applicable ?? (application.is_agency_submission),
        commission_basis_type: application.commission_basis_type || 'inherited_from_relationship',
        commission_value: application.commission_value || 0,
        expected_commission_amount: application.expected_commission_amount || 0,
        commission_currency: application.commission_currency || application.offer_currency || 'INR',
        commission_status: application.commission_status || 'pending_calculation',
        commission_rule_source: application.commission_rule_source || '',
        commission_notes: application.commission_notes || '',
      })
    }
  }, [application, open, form])

  const onFinish = async (values: any) => {
    if (!application) return
    setLoading(true)
    try {
      await pipelineApi.updateCommission(application.id, values)
      message.success('Commission status updated')
      onSuccess()
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to update commission')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title="Update Commission Details"
      open={open}
      onCancel={onClose}
      onOk={() => form.submit()}
      confirmLoading={loading}
      className="rounded-3xl overflow-hidden"
    >
      <Form form={form} layout="vertical" onFinish={onFinish}>
        <Form.Item name="commission_applicable" label="Commission Applicable?">
          <Select>
            <Select.Option value={true}>Yes — Applicable</Select.Option>
            <Select.Option value={false}>No — Not Applicable</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item
          noStyle
          shouldUpdate={(prevValues, currentValues) => prevValues.commission_applicable !== currentValues.commission_applicable}
        >
          {({ getFieldValue }) => {
            const applicable = getFieldValue('commission_applicable')
            if (!applicable) return null
            return (
              <>
                <Form.Item name="commission_basis_type" label={t('summary.commission_foundation')} rules={[{ required: true }]}>
                  <Select>
                    <Select.Option value="inherited_from_relationship">Inherited from Relationship</Select.Option>
                    <Select.Option value="custom_job_rule">Custom Job Rule</Select.Option>
                    <Select.Option value="percentage">Percentage (%)</Select.Option>
                    <Select.Option value="fixed">Fixed Amount</Select.Option>
                    <Select.Option value="milestone">Milestone Based</Select.Option>
                  </Select>
                </Form.Item>

                <div className="grid grid-cols-2 gap-4">
                  <Form.Item name="commission_value" label={t('summary.calculated')}>
                    <InputNumber className="w-full" placeholder="e.g. 15 for 15%" />
                  </Form.Item>
                  <Form.Item name="expected_commission_amount" label={t('summary.awaiting_payment')}>
                    <InputNumber className="w-full" />
                  </Form.Item>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <Form.Item name="commission_currency" label={t('form.currency')}>
                    <Select>
                      <Select.Option value="INR">INR</Select.Option>
                      <Select.Option value="USD">USD</Select.Option>
                      <Select.Option value="GBP">GBP</Select.Option>
                      <Select.Option value="EUR">EUR</Select.Option>
                    </Select>
                  </Form.Item>
                  <Form.Item name="commission_status" label={t('fields.status')} rules={[{ required: true }]}>
                    <Select>
                      <Select.Option value="pending_calculation">Pending Calculation</Select.Option>
                      <Select.Option value="calculated">Calculated</Select.Option>
                      <Select.Option value="awaiting_payment_tracking">Awaiting Payment Tracking</Select.Option>
                      <Select.Option value="cancelled">Cancelled</Select.Option>
                    </Select>
                  </Form.Item>
                </div>

                <Form.Item name="commission_rule_source" label="Rule Source Reference">
                  <Input placeholder="e.g. Master Service Agreement 2024" />
                </Form.Item>
              </>
            )
          }}
        </Form.Item>

        <Form.Item name="commission_notes" label={t('fields.special_instructions')}>
          <Input.TextArea rows={3} placeholder={t('placeholders.special_instructions')} />
        </Form.Item>
      </Form>
    </Modal>
  )
}

function AssignAgencyModal({
  open,
  jobId,
  onClose,
  onSuccess,
}: {
  open: boolean
  jobId: string
  onClose: () => void
  onSuccess: () => void
}) {
  const { t } = useTranslation('jobs')
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const { data: relationshipsData } = useApiQuery(['agency-relationships'], () => agenciesApi.listRelationships())
  const relationships = (relationshipsData as any)?.relationships || []

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      await agenciesApi.createAssignment({
        requisition_id: jobId,
        agency_tenant_id: values.agency_id,
        max_submissions: values.max_submissions,
        deadline: values.deadline?.format('YYYY-MM-DD'),
        notes: values.notes,
      })
      message.success('Agency assigned to job')
      form.resetFields()
      onSuccess()
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to assign agency')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title={t('actions.assign_agency')}
      open={open}
      onCancel={onClose}
      onOk={() => form.submit()}
      confirmLoading={loading}
    >
      <Form form={form} layout="vertical" onFinish={onFinish}>
        <Form.Item name="agency_id" label={t('form.select_agencies')} rules={[{ required: true }]}>
          <Select placeholder={t('placeholders.select_agency')}>
            {relationships.map((rel: any) => (
              <Select.Option key={rel.agency_id} value={rel.agency_id}>
                {rel.agency_name}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>
        <div className="grid grid-cols-2 gap-4">
          <Form.Item name="max_submissions" label={t('form.agency_max_submissions')} initialValue={10}>
             <InputNumber min={1} className="w-full" />
          </Form.Item>
          <Form.Item name="deadline" label={t('form.agency_deadline')}>
             <DatePicker className="w-full" disabledDate={d => d && d < dayjs().startOf('day')} />
          </Form.Item>
        </div>
        <Form.Item name="notes" label={t('fields.special_instructions')}>
          <Input.TextArea rows={3} placeholder={t('placeholders.special_instructions')} />
        </Form.Item>
      </Form>
    </Modal>
  )
}

// ── Tab Components ─────────────────────────────────────────────────────────


function OverviewTab({ requisition }: { requisition: JobRequisition }) {
  const { t } = useTranslation('jobs')
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card title={<span className="text-[10px] font-black uppercase tracking-widest text-slate-500">{t('form.description')}</span>} bordered={false} className="shadow-soft-sm rounded-3xl">
            <Paragraph className="text-slate-600 whitespace-pre-wrap text-sm leading-relaxed">
              {requisition.description}
            </Paragraph>
            {requisition.requirements && (
              <>
                <Divider className="my-6 border-slate-50" />
                <Title level={5} className="!text-[10px] font-black uppercase tracking-widest text-slate-400 mb-4">{t('form.requirements')}</Title>
                <Paragraph className="text-slate-600 whitespace-pre-wrap text-sm leading-relaxed">
                  {requisition.requirements}
                </Paragraph>
              </>
            )}
            <div className="mt-8 flex flex-wrap gap-2">
              {(requisition.skills_required || []).map(skill => (
                <Tag key={skill} className="m-0 border-none bg-indigo-50/50 text-indigo-600 font-black text-[10px] uppercase rounded-lg px-3 py-1">
                  {skill}
                </Tag>
              ))}
            </div>
          </Card>
        </div>
        <div className="space-y-6">
           <Card title={<span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Key Details</span>} bordered={false} className="shadow-soft-sm rounded-3xl">
            <Descriptions column={1} size="small">
              <Descriptions.Item label={t('fields.department')}>{requisition.department_id || 'Not Specified'}</Descriptions.Item>
              <Descriptions.Item label={t('fields.location')}>{requisition.location_id || 'Remote'}</Descriptions.Item>
              <Descriptions.Item label={t('form.job_type')}><Tag className="capitalize m-0 border-none bg-slate-100 text-slate-600 font-black text-[9px] uppercase px-2">{requisition.job_type.replace('_', ' ')}</Tag></Descriptions.Item>
              <Descriptions.Item label={t('form.work_mode')}><Tag className="capitalize m-0 border-none bg-slate-100 text-slate-600 font-black text-[9px] uppercase px-2">{requisition.work_mode}</Tag></Descriptions.Item>
            </Descriptions>
          </Card>
        </div>
      </div>
    </div>
  )
}

function OffersTab({ jobId, isOwner }: { jobId: string, isOwner: boolean }) {
  const { t } = useTranslation('jobs')
  const [placementModalOpen, setPlacementModalOpen] = useState(false)
  const [commissionModalOpen, setCommissionModalOpen] = useState(false)
  const [selectedApp, setSelectedApp] = useState<Application | null>(null)

  const { data: pipelineData, isLoading: pipelineLoading, refetch } = useApiQuery(
    ['job-offers', jobId],
    () => pipelineApi.listApplications({ requisition_id: jobId })
  )

  const { data: candidatesData } = useApiQuery(
    ['candidates', 'all'],
    () => candidatesApi.list()
  )

  const candidateMap = new Map<string, Candidate>(
    ((candidatesData as any)?.candidates ?? []).map((c: any) => [c.id, c])
  )

  const allApplications = (pipelineData as any)?.applications ?? []
  
  const offerApplications = allApplications.filter((app: any) => 
    (['offer_extended', 'offer_accepted', 'joined', 'placement_confirmed', 'placement_cancelled', 'rejected', 'withdrawn'].includes(app.status) 
    && (app.offer_amount || app.placement_status || app.commission_applicable)) || app.status === 'offer_extended'
  )

  const stats = {
    total: offerApplications.length,
    offer_accepted: offerApplications.filter((a: any) => a.status === 'offer_accepted').length,
    pending_join: offerApplications.filter((a: any) => a.placement_status === 'pending_join').length,
    joined: offerApplications.filter((a: any) => a.placement_status === 'joined' || a.status === 'joined').length,
    placed: offerApplications.filter((a: any) => a.placement_status === 'placement_confirmed' || a.status === 'placement_confirmed').length,
    agency_placements: offerApplications.filter((a: any) => a.is_agency_submission && (a.status === 'joined' || a.status === 'placement_confirmed' || a.placement_status === 'joined')).length,
    comm_applicable: offerApplications.filter((a: any) => a.commission_applicable).length,
    comm_calculated: offerApplications.filter((a: any) => a.commission_status === 'calculated').length,
    comm_awaiting_payment: offerApplications.filter((a: any) => a.commission_status === 'awaiting_payment_tracking').length,
  }

  const columns = [
    {
      title: t('fields.candidate_name'),
      key: 'candidate',
      render: (_: any, app: any) => {
        const candidate = candidateMap.get(app.candidate_id)
        return (
          <div className="flex items-center gap-3">
            <Avatar className="bg-slate-50 text-slate-600 font-black border-none shrink-0">
              {candidate?.full_name?.charAt(0) || 'C'}
            </Avatar>
            <div className="min-w-0">
              <Text className="block font-black text-slate-800 text-xs leading-tight">
                {candidate?.full_name || 'Loading...'}
              </Text>
              <Text className="text-[10px] text-slate-400 font-bold uppercase tracking-tight">
                {candidate?.current_title || 'No Title'}
              </Text>
            </div>
          </div>
        )
      }
    },
    {
      title: t('fields.status'),
      dataIndex: 'status',
      key: 'status',
      render: (s: string) => {
        const configs: Record<string, { label: string, color: string }> = {
          offer_extended: { label: 'Offer Sent', color: 'blue' },
          offer_accepted: { label: 'Offer Accepted', color: 'green' },
          joined: { label: 'Joined', color: 'cyan' },
          placement_confirmed: { label: 'Placed', color: 'purple' },
          rejected: { label: 'Offer Rejected', color: 'red' },
          withdrawn: { label: 'Offer Withdrawn', color: 'orange' }
        }
        const conf = configs[s] || { label: s.replace('_', ' '), color: 'default' }
        return (
          <Tag color={conf.color} className="m-0 border-none font-black text-[9px] uppercase px-2 py-0.5 rounded-full">
            {conf.label}
          </Tag>
        )
      }
    },
    {
      title: t('summary.joined'),
      key: 'joining_dates',
      render: (_: any, app: Application) => (
        <div className="flex flex-col gap-0.5">
          {app.expected_joining_date && (
            <div className="flex items-center gap-1.5 text-[10px] font-black text-slate-400 uppercase tracking-tight">
              <Calendar size={10} className="text-slate-300" />
              Exp: {dayjs(app.expected_joining_date).format('MMM D, YY')}
            </div>
          )}
          {app.joined_at && (
            <div className="flex items-center gap-1.5 text-[10px] font-black text-emerald-600 uppercase tracking-tight">
              <CheckCircle size={10} className="text-emerald-500" />
              {dayjs(app.joined_at).format('MMM D, YY')}
            </div>
          )}
        </div>
      )
    },
    {
      title: 'Commission',
      key: 'commission',
      render: (_: any, app: Application) => {
        if (!app.commission_applicable) return <Text className="text-[10px] text-slate-300 font-black uppercase tracking-tight">N/A</Text>
        return (
          <div className="flex flex-col gap-0.5">
            <div className="flex items-center gap-1.5">
              <Text className="text-[10px] font-black text-slate-800">
                {app.commission_currency} {app.expected_commission_amount?.toLocaleString()}
              </Text>
              <Tag className="m-0 border-none bg-indigo-50 text-indigo-600 font-black text-[8px] uppercase px-1 rounded">
                {app.commission_basis_type === 'percentage' ? `${app.commission_value}%` : app.commission_basis_type?.replace('_', ' ')}
              </Tag>
            </div>
            <Tag 
              color={app.commission_status === 'awaiting_payment_tracking' ? 'orange' : app.commission_status === 'calculated' ? 'green' : 'default'}
              className="m-0 border-none font-black text-[8px] uppercase px-1.5 rounded-full w-fit"
            >
              {app.commission_status?.replace('_', ' ')}
            </Tag>
          </div>
        )
      }
    },
    {
      title: '',
      key: 'actions',
      align: 'right' as const,
      render: (_: any, app: Application) => (
        <Dropdown
          menu={{
            items: [
              {
                key: 'update_placement',
                label: 'Update Placement Status',
                icon: <Activity size={14} />,
                disabled: !isOwner,
                onClick: () => {
                  setSelectedApp(app)
                  setPlacementModalOpen(true)
                }
              },
              {
                key: 'update_commission',
                label: 'Commission Details',
                icon: <DollarSign size={14} />,
                disabled: !isOwner,
                onClick: () => {
                  setSelectedApp(app)
                  setCommissionModalOpen(true)
                }
              },
              { type: 'divider' },
              {
                key: 'view_details',
                label: 'View Details',
                icon: <ExternalLink size={14} />,
              }
            ]
          }}
          trigger={['click']}
        >
          <Button type="text" size="small" icon={<MoreVertical size={14} className="text-slate-400" />} />
        </Dropdown>
      )
    }
  ]

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">{t('summary.placement_summary')}</span>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: t('summary.offer'), value: stats.offer_accepted, icon: CheckCircle, color: 'emerald' },
            { label: t('offer_summary.joining_pending'), value: stats.pending_join, icon: Clock, color: 'amber' },
            { label: t('offer_summary.joined'), value: stats.joined, icon: Users, color: 'cyan' },
            { label: 'Confirmed', value: stats.placed, icon: ShieldCheck, color: 'purple' },
          ].map(s => (
            <Card key={s.label} className="shadow-soft-sm border-none bg-white rounded-3xl border border-slate-100">
              <div className="flex items-start justify-between mb-2">
                <div className={`p-2 rounded-xl bg-${s.color}-50 text-${s.color}-600 border border-${s.color}-100 shadow-sm`}>
                  <s.icon size={16} />
                </div>
              </div>
              <Text className="text-[10px] font-black uppercase tracking-widest text-slate-400 block mb-1">{s.label}</Text>
              <Title level={3} className="!m-0 !font-black text-slate-800">{s.value}</Title>
            </Card>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">{t('summary.commission_foundation')}</span>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: t('summary.agency_placements'), value: stats.agency_placements, icon: Scale, color: 'blue' },
            { label: t('summary.commission_applicable'), value: stats.comm_applicable, icon: DollarSign, color: 'indigo' },
            { label: t('summary.calculated'), value: stats.comm_calculated, icon: Receipt, color: 'green' },
            { label: t('summary.awaiting_payment'), value: stats.comm_awaiting_payment, icon: Clock, color: 'orange' },
          ].map(s => (
            <Card key={s.label} className="shadow-soft-sm border-none bg-slate-50/50 rounded-3xl border border-slate-100">
              <div className="flex items-start justify-between mb-2">
                <div className={`p-2 rounded-xl bg-${s.color}-50 text-${s.color}-600 border border-${s.color}-100 shadow-sm`}>
                  <s.icon size={16} />
                </div>
              </div>
              <Text className="text-[10px] font-black uppercase tracking-widest text-slate-400 block mb-1">{s.label}</Text>
              <Title level={3} className="!m-0 !font-black text-slate-800">{s.value}</Title>
            </Card>
          ))}
        </div>
      </div>

      <Card 
        title={
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Candidate Placement & Commission</span>
          </div>
        }
        bordered={false} 
        className="shadow-soft-sm overflow-hidden rounded-3xl border border-slate-100" 
        bodyStyle={{ padding: 0 }}
      >
        <Table 
          dataSource={offerApplications} 
          columns={columns} 
          rowKey="id" 
          loading={pipelineLoading}
          pagination={false}
          className="modern-table"
          size="small"
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No candidate placements found" /> }}
        />
      </Card>

      <PlacementModal 
        open={placementModalOpen}
        application={selectedApp}
        onClose={() => setPlacementModalOpen(false)}
        onSuccess={() => {
          setPlacementModalOpen(false)
          refetch()
        }}
      />

      <CommissionModal 
        open={commissionModalOpen}
        application={selectedApp}
        onClose={() => setCommissionModalOpen(false)}
        onSuccess={() => {
          setCommissionModalOpen(false)
          refetch()
        }}
      />
    </div>
  )
}

// ─── Main Job Command Center ──────────────────────────────────────────

export default function JobDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { t } = useTranslation('jobs')
  const [activeTab, setActiveTab] = useState('command_center')
  const [assignAgencyModalOpen, setAssignAgencyModalOpen] = useState(false)
  const user = useAuthStore((s) => s.user)

  const { data, isLoading } = useApiQuery(['requisition', id], () => requisitionsApi.get(id!))
  const { data: pipelineData, refetch: refetchPipeline } = useApiQuery(['job-pipeline-summary', id], () => pipelineApi.listApplications({ requisition_id: id }))

  const requisition = (data as any)?.requisition as JobRequisition
  const applications = (pipelineData as any)?.applications || []
  const isOwner = requisition?.created_by === user?.id

  if (isLoading) return <div className="flex items-center justify-center min-h-[400px]"><Spin size="large" /></div>
  if (!requisition) return <Empty description="Job not found" />

  const config = STATUS_CONFIG[requisition.status] || STATUS_CONFIG.draft

  const stats = {
    total: applications.length,
    submitted: applications.filter((a: any) => a.status === 'applied' || a.status === 'screening').length,
    shortlisted: applications.filter((a: any) => a.status === 'shortlisted').length,
    interview: applications.filter((a: any) => a.status === 'interview').length,
    offer: applications.filter((a: any) => a.status === 'offer_extended' || a.status === 'offer_accepted').length,
    joined: applications.filter((a: any) => a.status === 'joined' || a.placement_status === 'joined').length,
    rejected: applications.filter((a: any) => a.status === 'rejected').length,
  }

  return (
    <div className="space-y-6">
      {/* Navigation & Intelligence Header */}
      <div className="flex flex-col gap-4">
        <Button 
          type="text" 
          icon={<ArrowLeft className="h-4 w-4" />} 
          className="flex items-center gap-2 text-slate-500 font-medium hover:text-slate-900 w-fit p-0"
          onClick={() => navigate('/jobs')}
        >
          {t('page.back_to_jobs')}
        </Button>

        <div className="bg-white p-6 rounded-3xl shadow-soft-sm border border-slate-100">
          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
            {/* Left: Job Intelligence */}
            <div className="flex items-start gap-4 flex-1">
              <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 border border-indigo-100 shadow-sm">
                <Briefcase className="h-7 w-7" />
              </div>
              <div>
                <div className="flex items-center gap-2 mb-2 flex-wrap">
                  <div className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-black uppercase tracking-wider", config.color)}>
                    <span className={cn("h-1.5 w-1.5 rounded-full", config.dot)} />
                    {config.label}
                  </div>
                  <Tag className="m-0 border-none bg-slate-100 text-slate-600 font-black text-[10px] uppercase rounded-full px-2.5">
                    {requisition.priority} {t('fields.priority')}
                  </Tag>
                  <Text className="text-[11px] font-bold text-slate-400 uppercase tracking-tight ml-2">
                    {t('fields.job_id')}: {requisition.job_ref_id || requisition.id.slice(0, 8)}
                  </Text>
                </div>
                <h1 className="text-3xl font-black text-slate-900 tracking-tight leading-tight mb-4">
                  {requisition.title}
                </h1>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-x-8 gap-y-3">
                  <div className="flex flex-col">
                    <Text className="text-[9px] font-black text-slate-400 uppercase tracking-widest">{t('fields.department')}</Text>
                    <Text className="text-xs font-black text-slate-700 truncate">{requisition.department_id || 'General'}</Text>
                  </div>
                  <div className="flex flex-col">
                    <Text className="text-[9px] font-black text-slate-400 uppercase tracking-widest">{t('fields.location')}</Text>
                    <Text className="text-xs font-black text-slate-700 truncate">{requisition.location_id || 'Remote'}</Text>
                  </div>
                  <div className="flex flex-col">
                    <Text className="text-[9px] font-black text-slate-400 uppercase tracking-widest">{t('command_center.open_positions')}</Text>
                    <Text className="text-xs font-black text-slate-700">{requisition.headcount}</Text>
                  </div>
                  <div className="flex flex-col">
                    <Text className="text-[9px] font-black text-slate-400 uppercase tracking-widest">{t('fields.hiring_manager')}</Text>
                    <div className="flex items-center gap-1.5 min-w-0">
                      <Avatar size={14} className="bg-amber-100 text-amber-600 text-[7px] font-black">HM</Avatar>
                      <Text className="text-xs font-black text-slate-700 truncate">Manager Name</Text>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Right: Live Metrics */}
            <div className="flex flex-col items-end gap-4">
              <div className="flex gap-2">
                <Button type="primary" icon={<Edit className="h-4 w-4" />} className="h-9 flex items-center gap-2 font-black text-[10px] uppercase shadow-indigo-200 shadow-lg rounded-xl">
                  {t('actions.edit_job')}
                </Button>
                <Button className="h-9 w-9 p-0 flex items-center justify-center text-slate-400 rounded-xl">
                  <MoreVertical size={16} />
                </Button>
              </div>
              <div className="flex gap-2">
                <MetricCard label={t('candidate_panel.total')} value={stats.total} color="slate" />
                <MetricCard label={t('summary.submitted')} value={stats.submitted} color="blue" />
                <MetricCard label={t('summary.shortlisted')} value={stats.shortlisted} color="indigo" />
                <MetricCard label={t('summary.interview')} value={stats.interview} color="purple" />
                <MetricCard label={t('summary.offer')} value={stats.offer} color="amber" />
                <MetricCard label={t('summary.joined')} value={stats.joined} color="emerald" />
                <MetricCard label={t('command_center.rejected')} value={stats.rejected} color="rose" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs / Command Center Toggle */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        className="modern-tabs-command"
        items={[
          {
            key: 'command_center',
            label: <div className="flex items-center gap-2 font-black text-[10px] uppercase tracking-wider"><Zap size={14} /> {t('command_center.title')}</div>,
            children: <JobCommandCenterView requisition={requisition} applications={applications} onAssignAgency={() => setAssignAgencyModalOpen(true)} />
          },
          {
            key: 'overview',
            label: t('tabs.overview'),
            children: <OverviewTab requisition={requisition} />
          },
          {
            key: 'tracking',
            label: t('tabs.tracking'),
            children: <JobTrackingView jobId={id!} />
          },
          {
            key: 'interviews',
            label: t('tabs.interviews'),
            children: <JobInterviewsTab jobId={id!} />
          },
          {
            key: 'offers',
            label: t('tabs.offers'),
            children: <OffersTab jobId={id!} isOwner={isOwner} />
          }
        ]}
      />

      <AssignAgencyModal 
        open={assignAgencyModalOpen}
        jobId={id!}
        onClose={() => setAssignAgencyModalOpen(false)}
        onSuccess={() => {
          setAssignAgencyModalOpen(false)
          refetchPipeline()
        }}
      />
    </div>
  )
}
