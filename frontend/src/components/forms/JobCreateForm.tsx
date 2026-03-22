import { Form, Input, Button, Row, Col, Select, InputNumber, message, Checkbox, DatePicker, Tag, Typography } from 'antd'
import { requisitionsApi } from '@/api/jobs'
import { organisationApi } from '@/api/organisation'
import { agenciesApi } from '@/api/agencies'
import { useState, useEffect } from 'react'
import { CURRENCIES } from '@/utils/locale'
import { useApiQuery } from '@/hooks/useApiQuery'
import dayjs from 'dayjs'
import type { JobRequisition } from '@/types'

const { Text } = Typography

interface JobCreateFormProps {
  onSuccess: (requisition?: JobRequisition) => void
  initialValues?: JobRequisition | null
}

export default function JobCreateForm({ onSuccess, initialValues }: JobCreateFormProps) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [selectedAgencyIds, setSelectedAgencyIds] = useState<string[]>([])
  const [useAgencies, setUseAgencies] = useState(false)

  const isEditMode = !!initialValues?.id

  const { data: usersData } = useApiQuery(
    ['org-users', 'job-form'],
    () => organisationApi.listUsers()
  )
  const { data: departmentsData } = useApiQuery(
    ['org-departments', 'job-form'],
    () => organisationApi.listDepartments()
  )
  const { data: availableAgenciesData } = useApiQuery(
    ['agencies-available', 'job-form'],
    () => agenciesApi.listAvailableAgencies()
  )
  const { data: relationshipsData } = useApiQuery(
    ['agencies-relationships', 'job-form'],
    () => agenciesApi.listRelationships()
  )
  const { data: existingAssignmentsData } = useApiQuery(
    ['job-agency-assignments', initialValues?.id],
    () => agenciesApi.listAssignments({ requisition_id: initialValues?.id }),
    { enabled: !!initialValues?.id }
  )

  const users = ((usersData as any)?.users ?? []) as Array<any>
  const departments = ((departmentsData as any)?.departments ?? []) as Array<any>
  const availableAgencies = ((availableAgenciesData as any)?.agencies ?? []) as Array<any>
  const linkedRelationships = ((relationshipsData as any)?.relationships ?? []) as Array<any>
  const existingAssignments = ((existingAssignmentsData as any)?.assignments ?? []) as Array<any>

  const agencyOptionsMap = new Map<string, string>()
  availableAgencies.forEach((a: any) => {
    if (!a?.agency_tenant_id) return
    agencyOptionsMap.set(a.agency_tenant_id, a?.name || `Agency ${String(a.agency_tenant_id).slice(0, 8)}`)
  })
  linkedRelationships.forEach((r: any) => {
    const agencyId = r?.agency_tenant_id
    if (!agencyId || agencyOptionsMap.has(agencyId)) return
    agencyOptionsMap.set(agencyId, r?.agency?.name || r?.agency_name || `Agency ${String(agencyId).slice(0, 8)}`)
  })
  const agencyOptions = Array.from(agencyOptionsMap.entries()).map(([value, label]) => ({ value, label }))

  useEffect(() => {
    if (!initialValues) return
    const metadata = (initialValues.metadata || {}) as Record<string, any>
    const assignedAgencies = existingAssignments
      .map((a: any) => a?.agency_tenant_id)
      .filter(Boolean)

    form.setFieldsValue({
      ...initialValues,
      job_owner_id: metadata.job_owner_id,
      internal_recruiter_ids: Array.isArray(metadata.internal_recruiter_ids) ? metadata.internal_recruiter_ids : [],
      agency_tenant_ids: assignedAgencies,
      use_agencies: assignedAgencies.length > 0,
      agency_max_submissions: 10,
      agency_deadline: dayjs().add(30, 'day'),
    })
    setSelectedAgencyIds(assignedAgencies)
    setUseAgencies(assignedAgencies.length > 0)
  }, [existingAssignments, form, initialValues])

  useEffect(() => {
    if (initialValues) return
    const fetchOrgDefaults = async () => {
      try {
        const res = await organisationApi.getProfile()
        const settings = ((res.data.data.organisation as any)?.settings || {}) as Record<string, any>
        if (settings.default_currency) {
          form.setFieldsValue({ salary_currency: settings.default_currency })
        }
      } catch (err) {
        // Fallback to USD or keep default
      }
    }
    fetchOrgDefaults()
  }, [form, initialValues])

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      const metadata: Record<string, unknown> = {
        ...(((initialValues?.metadata || {}) as Record<string, unknown>) || {}),
      }
      if (values.job_owner_id) {
        metadata.job_owner_id = values.job_owner_id
      }
      if (Array.isArray(values.internal_recruiter_ids)) {
        metadata.internal_recruiter_ids = values.internal_recruiter_ids
      }

      const payload = {
        ...values,
        metadata,
      }
      delete (payload as any).job_owner_id
      delete (payload as any).internal_recruiter_ids
      delete (payload as any).use_agencies
      delete (payload as any).agency_tenant_ids
      delete (payload as any).agency_max_submissions
      delete (payload as any).agency_deadline

      const res = isEditMode
        ? await requisitionsApi.update(initialValues!.id, payload)
        : await requisitionsApi.create(payload)
      const requisition = (res as any)?.data?.data?.requisition as JobRequisition | undefined
      const requisitionId = requisition?.id || initialValues?.id

      if (values.use_agencies && requisitionId && selectedAgencyIds.length > 0) {
        const existingAgencyIds = new Set(
          existingAssignments.map((a: any) => a?.agency_tenant_id).filter(Boolean)
        )
        const newAgencyIds = selectedAgencyIds.filter((id) => !existingAgencyIds.has(id))
        const assignmentDeadline = values.agency_deadline
          ? dayjs(values.agency_deadline).format('YYYY-MM-DD')
          : dayjs().add(30, 'day').format('YYYY-MM-DD')
        for (const agencyId of newAgencyIds) {
          await agenciesApi.createAssignment({
            agency_tenant_id: agencyId,
            requisition_id: requisitionId,
            max_submissions: Number(values.agency_max_submissions) || 10,
            deadline: assignmentDeadline,
          })
        }
      }

      message.success(isEditMode ? 'Job updated successfully' : 'Job created successfully')
      onSuccess(requisition)
    } catch (err: any) {
      message.error(err.response?.data?.message || (isEditMode ? 'Failed to update job' : 'Failed to create job'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={onFinish}
      initialValues={{
        job_type: 'full_time',
        work_mode: 'hybrid',
        priority: 'medium',
        headcount: 1,
        salary_currency: 'USD',
        agency_max_submissions: 10,
        agency_deadline: dayjs().add(30, 'day'),
      }}
    >
      <Form.Item name="title" label="Job Title" rules={[{ required: true }]}>
        <Input placeholder="e.g. Senior Software Engineer" />
      </Form.Item>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item name="job_type" label="Job Type" rules={[{ required: true }]}>
            <Select options={[
              { value: 'full_time', label: 'Full Time' },
              { value: 'part_time', label: 'Part Time' },
              { value: 'contract', label: 'Contract' },
              { value: 'internship', label: 'Internship' },
            ]} />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="work_mode" label="Work Mode" rules={[{ required: true }]}>
            <Select options={[
              { value: 'remote', label: 'Remote' },
              { value: 'onsite', label: 'On-site' },
              { value: 'hybrid', label: 'Hybrid' },
            ]} />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item name="priority" label="Priority">
            <Select options={[
              { value: 'low', label: 'Low' },
              { value: 'medium', label: 'Medium' },
              { value: 'high', label: 'High' },
              { value: 'urgent', label: 'Urgent' },
            ]} />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="headcount" label="Headcount">
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item name="job_owner_id" label="Job Owner">
            <Select
              showSearch
              allowClear
              placeholder="Select owner"
              options={users.map((u: any) => ({
                value: u.id,
                label: u.full_name || u.email || `User ${String(u.id || '').slice(0, 8)}`,
              }))}
            />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="internal_recruiter_ids" label="Internal Recruiters">
            <Select
              mode="multiple"
              allowClear
              placeholder="Select recruiters"
              options={users.map((u: any) => ({
                value: u.id,
                label: u.full_name || u.email || `User ${String(u.id || '').slice(0, 8)}`,
              }))}
            />
          </Form.Item>
        </Col>
      </Row>

      <Form.Item name="department_id" label="Internal Team / Department">
        <Select
          allowClear
          placeholder="Select department"
          options={departments.map((d: any) => ({
            value: d.id,
            label: d.name || `Department ${String(d.id || '').slice(0, 8)}`,
          }))}
        />
      </Form.Item>
      <Text type="secondary" className="block -mt-4 mb-4 text-xs">
        Owner and recruiter selections are stored in requisition metadata for Phase 1.
      </Text>

      <Row gutter={16}>
        <Col span={8}>
          <Form.Item name="salary_currency" label="Currency" rules={[{ required: true }]}>
            <Select 
              showSearch
              options={CURRENCIES.map(c => ({ value: c.code, label: `${c.code} (${c.symbol})` }))} 
            />
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item name="salary_min" label="Min Salary">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item name="salary_max" label="Max Salary">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
      </Row>

      <Form.Item name="description" label="Description">
        <Input.TextArea rows={4} placeholder="Describe the role..." />
      </Form.Item>

      <Form.Item name="requirements" label="Requirements">
        <Input.TextArea rows={4} placeholder="List requirements..." />
      </Form.Item>

      <Form.Item name="skills_required" label="Skills (comma separated)">
        <Select mode="tags" placeholder="e.g. React, Python" />
      </Form.Item>

      <Form.Item name="use_agencies" valuePropName="checked" className="mb-2">
        <Checkbox
          checked={useAgencies}
          onChange={(e) => {
            setUseAgencies(e.target.checked)
            if (!e.target.checked) {
              setSelectedAgencyIds([])
              form.setFieldValue('agency_tenant_ids', [])
            }
          }}
        >
          Use agencies for this job
        </Checkbox>
      </Form.Item>

      {useAgencies && (
        <>
          <Form.Item name="agency_tenant_ids" label="Select Agencies">
            <Select
              mode="multiple"
              showSearch
              allowClear
              placeholder="Select one or more agencies"
              options={agencyOptions}
              value={selectedAgencyIds}
              onChange={(vals) => setSelectedAgencyIds(vals)}
            />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="agency_max_submissions" label="Max submissions per agency">
                <InputNumber min={1} max={100} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="agency_deadline" label="Agency submission deadline">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <div className="mb-4 rounded-lg border border-slate-200 bg-slate-50 p-3">
            <Text className="text-xs font-semibold text-slate-600">Selected agencies</Text>
            <div className="mt-2 flex flex-wrap gap-2">
              {selectedAgencyIds.length === 0 && (
                <Text type="secondary" className="text-xs">No agencies selected</Text>
              )}
              {selectedAgencyIds.map((agencyId) => (
                <Tag
                  key={agencyId}
                  closable
                  onClose={() => {
                    const next = selectedAgencyIds.filter((id) => id !== agencyId)
                    setSelectedAgencyIds(next)
                    form.setFieldValue('agency_tenant_ids', next)
                  }}
                  className="m-0 rounded-full px-2 py-0.5"
                >
                  {agencyOptionsMap.get(agencyId) || `Agency ${agencyId.slice(0, 8)}`}
                </Tag>
              ))}
            </div>
          </div>
        </>
      )}

      <div className="flex justify-end gap-3 mt-6">
        <Button onClick={() => form.resetFields()}>Reset</Button>
        <Button type="primary" htmlType="submit" loading={loading} className="bg-blue-600">
          {isEditMode ? 'Save Job Changes' : 'Create Job Requisition'}
        </Button>
      </div>
    </Form>
  )
}
