import React, { useState, useEffect } from 'react'
import {
  Table, Button, Input, Tag, Avatar, Typography,
  Card, Modal, Tabs, Spin, Form, DatePicker, InputNumber,
  Segmented, Badge, message, Row, Col, Select, AutoComplete, Checkbox
} from 'antd'
import {
  Plus, Clock,
  Import, LayoutGrid, List as ListIcon,
  Phone, Mail, UserPlus,
  TrendingUp, Search, RefreshCw, ChevronRight,
  Briefcase, Calendar, ArrowUpRight, ChevronLeft, Link,
  Info, X, Edit, CheckCircle
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useQueryClient } from '@tanstack/react-query'
import { candidatesApi } from '@/api/candidates'
import { pipelineApi } from '@/api/pipeline'
import { organisationApi } from '@/api/organisation'
import type { Candidate } from '@/types'
import { cn } from '@/utils/cn'
import http from '@/utils/http'
import { useNavigate } from 'react-router-dom'
import { CURRENCIES } from '@/utils/locale'
import CandidateInteractionDrawer from '@/components/CandidateInteractionDrawer'
import CandidateQuickView from './CandidateQuickView'
import { formatStatusLabel, getStatusStyle } from '@/utils/status'
import { getSalaryConfig, formatSalaryLabel, formatSalaryDisplay } from '@/utils/salary'
import PhoneInput, { getPhoneValidationRule, formatPhoneDisplay } from '@/components/common/PhoneInput'

dayjs.extend(relativeTime)
const { Text, Title } = Typography

// ─── Constants ────────────────────────────────────────────────────────────────

const SOURCE_COLORS: Record<string, string> = {
  linkedin: 'blue',
  referral: 'purple',
  direct: 'default',
  agency: 'orange',
  passport: 'green',
  self: 'cyan',
}

const CRM_STAGES = [
  { key: 'new_lead', label: 'New Lead', icon: '🆕' },
  { key: 'nurturing', label: 'Nurturing', icon: '💬' },
  { key: 'in_process', label: 'In Process', icon: '⚡' },
  { key: 'offer_stage', label: 'Offer Stage', icon: '🔥' },
  { key: 'placed', label: 'Placed', icon: '✅' },
  { key: 'lost', label: 'Lost', icon: '❌' },
]

// ─── Sub-components ─────────────────────────────────────────────────────────

function AddCandidateChooser({
  open, onClose, onQuickAdd, onDetailedAdd
}: {
  open: boolean
  onClose: () => void
  onQuickAdd: () => void
  onDetailedAdd: () => void
}) {
  return (
    <Modal
      open={open}
      onCancel={onClose}
      footer={null}
      width={460}
      title={
        <span className="font-bold text-slate-900">
          How do you want to add this candidate?
        </span>
      }
      destroyOnClose
    >
      <div className="py-2 space-y-3">
        <button
          onClick={() => { onClose(); onQuickAdd() }}
          className="w-full text-left p-4 rounded-xl border-2 border-slate-100 hover:border-indigo-200 hover:bg-indigo-50/30 transition-all group cursor-pointer"
        >
          <div className="flex items-start gap-4">
            <div className="h-10 w-10 rounded-xl bg-indigo-50 flex items-center justify-center shrink-0 group-hover:bg-indigo-100 transition-colors">
              <UserPlus className="h-5 w-5 text-indigo-600" />
            </div>
            <div>
              <p className="font-bold text-slate-900 mb-1 m-0">
                Quick Add
              </p>
              <p className="text-sm text-slate-500 leading-relaxed m-0">
                Add basic details only. Send a link for the candidate
                to complete their own profile.
              </p>
              <p className="text-xs text-indigo-500 font-bold mt-1 m-0">
                Best for: sourcing calls, WhatsApp leads, fast intake
              </p>
            </div>
          </div>
        </button>

        <button
          onClick={() => { onClose(); onDetailedAdd() }}
          className="w-full text-left p-4 rounded-xl border-2 border-slate-100 hover:border-indigo-200 hover:bg-indigo-50/30 transition-all group cursor-pointer"
        >
          <div className="flex items-start gap-4">
            <div className="h-10 w-10 rounded-xl bg-slate-100 flex items-center justify-center shrink-0 group-hover:bg-slate-200 transition-colors">
              <Clock className="h-5 w-5 text-slate-600" />
            </div>
            <div>
              <p className="font-bold text-slate-900 mb-1 m-0">
                Detailed Add
              </p>
              <p className="text-sm text-slate-500 leading-relaxed m-0">
                Fill complete profile now from resume or
                during a screening call.
              </p>
              <p className="text-xs text-slate-400 font-bold mt-1 m-0">
                Best for: resume in hand, screening calls,
                agency database entry
              </p>
            </div>
          </div>
        </button>
      </div>
    </Modal>
  )
}

function QuickAddModal({
  open, onClose, onSuccess
}: {
  open: boolean
  onClose: () => void
  onSuccess: () => void
}) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  const { data: orgData } = useApiQuery(
    ['org_profile'],
    () => organisationApi.getProfile()
  )
  const countryCode = (orgData as any)?.data?.organisation?.country_code || 'IN'
  const salaryConfig = getSalaryConfig(countryCode)

  const handleClose = () => {
    form.resetFields()
    onClose()
  }

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      await candidatesApi.create({
        first_name: values.first_name,
        last_name: values.last_name,
        email: values.email || '',
        phone: values.phone_field ? `${values.phone_field.country_code}:${values.phone_field.phone_number}` : '',
        phone_country_code: values.phone_field?.country_code || 'IN',
        phone_number: values.phone_field?.phone_number || '',
        current_company: values.current_company || '',
        current_title: values.current_title || '',
        current_ctc: values.current_ctc,
        expected_salary_min: values.expected_salary_min,
        resume_url: values.resume_url || '',
        source: 'company',
        entry_type: 'manual',
        metadata: values.resume_url 
          ? { resume_public_url: values.resume_url } 
          : undefined,
      } as any)
      message.success('Candidate saved successfully')
      form.resetFields()
      onSuccess()
    } catch (err: any) {
      console.error('[QuickAdd] error:', err)
      const errData = err?.response?.data
      if (err?.response?.status === 409) {
        message.warning(
          errData?.message || 'Candidate already exists'
        )
        return
      }
      const fieldErrors = errData?.errors
      if (fieldErrors) {
        form.setFields(
          Object.entries(fieldErrors).map(([field, msgs]) => ({
            name: field,
            errors: Array.isArray(msgs) ? msgs : [msgs as string],
          }))
        )
      }
      message.error(errData?.message || 'Failed to add candidate')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      open={open}
      onCancel={handleClose}
      onOk={() => form.submit()}
      okText="Save Candidate"
      okButtonProps={{ style: { background: '#4F46E5' } }}
      confirmLoading={loading}
      width={500}
      title={
        <span className="font-bold text-slate-900">
          Quick Add Candidate
        </span>
      }
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        className="mt-4"
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.preventDefault()
            form.submit()
          }
        }}
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="first_name"
              label="First Name"
              rules={[{ required: true, message: 'Required' }]}
            >
              <Input placeholder="Jane" className="h-10 rounded-xl" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="last_name"
              label="Last Name"
              rules={[{ required: true, message: 'Required' }]}
            >
              <Input placeholder="Doe" className="h-10 rounded-xl" />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="email"
              label="Email"
              rules={[{ type: 'email', message: 'Invalid email' }]}
            >
              <Input
                type="email"
                placeholder="jane@example.com"
                className="h-10 rounded-xl"
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="phone_field"
              label="Phone"
              rules={[getPhoneValidationRule()]}
            >
              <PhoneInput placeholder="Phone number" />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="current_title" label="Current Title">
              <Input placeholder="Senior Engineer" 
                     className="h-10 rounded-xl" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="current_company" label="Current Company">
              <Input placeholder="Acme Corp" 
                     className="h-10 rounded-xl" />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="current_ctc"
              label={formatSalaryLabel(salaryConfig, 'Current Salary')}
            >
              <InputNumber
                min={0}
                className="w-full h-10 rounded-xl flex items-center"
                placeholder={salaryConfig.placeholder}
                addonBefore={salaryConfig.symbol}
                addonAfter={salaryConfig.unit}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="expected_salary_min"
              label={formatSalaryLabel(salaryConfig, 'Expected Salary')}
            >
              <InputNumber
                min={0}
                className="w-full h-10 rounded-xl flex items-center"
                placeholder={salaryConfig.placeholder}
                addonBefore={salaryConfig.symbol}
                addonAfter={salaryConfig.unit}
              />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item name="resume_url" label="Resume URL (Optional)">
          <Input
            placeholder="https://drive.google.com/..."
            className="h-10 rounded-xl"
          />
        </Form.Item>
      </Form>
    </Modal>
  )
}


function InviteLinkModal({
  open,
  onClose,
}: {
  open: boolean
  onClose: () => void
}) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [generatedLink, setGeneratedLink] = useState<string | null>(null)

  const handleGenerate = async () => {
    setLoading(true)
    try {
      const values = form.getFieldsValue()
      const res = await candidatesApi.createInviteLink({
        expires_days: values.expires_days || 30,
        max_uses: values.max_uses || null,
        job_id: values.job_id || undefined,
      })
      const token = (res as any)?.data?.data?.link?.token
      if (token) {
        const url = `${window.location.origin}/apply/${token}`
        setGeneratedLink(url)
      }
    } catch (err: any) {
      message.error('Failed to generate link')
      console.error('[InviteLink]', err)
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setGeneratedLink(null)
    form.resetFields()
    onClose()
  }

  return (
    <Modal
      open={open}
      onCancel={handleClose}
      footer={null}
      width={480}
      title={
        <div className="flex items-center gap-2">
          <Link className="h-4 w-4 text-indigo-500" />
          <span className="font-bold">Generate Invite Link</span>
        </div>
      }
      destroyOnClose
    >
      {!generatedLink ? (
        <div className="py-2">
          <p className="text-sm text-slate-500 mb-4">
            Generate a branded link to send to candidates. 
            When they open it, they see your company name 
            and fill in their own details.
          </p>
          <Form form={form} layout="vertical"
            initialValues={{ expires_days: 30 }}>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="expires_days" 
                           label="Expires after (days)">
                  <Select options={[
                    { value: 7, label: '7 days' },
                    { value: 14, label: '14 days' },
                    { value: 30, label: '30 days' },
                    { value: 60, label: '60 days' },
                    { value: 90, label: '90 days' },
                  ]} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="max_uses" 
                           label="Max uses (optional)">
                  <InputNumber min={1} className="w-full"
                    placeholder="Unlimited" />
                </Form.Item>
              </Col>
            </Row>
          </Form>
          <Button
            type="primary"
            block
            loading={loading}
            className="h-10 rounded-xl font-bold"
            style={{ background: '#4F46E5' }}
            onClick={handleGenerate}
          >
            Generate Link
          </Button>
        </div>
      ) : (
        <div className="py-2 space-y-4">
          <div className="flex items-center justify-center">
            <div className="h-14 w-14 bg-green-50 rounded-full 
                           flex items-center justify-center">
              <CheckCircle className="h-7 w-7 text-green-500" />
            </div>
          </div>
          <div className="text-center">
            <p className="font-bold text-slate-900 text-lg m-0">
              Link Generated!
            </p>
            <p className="text-sm text-slate-500 mt-1 m-0">
              Share this link with your candidate. 
              They will see your company name and fill 
              in their details.
            </p>
          </div>
          <div className="bg-slate-50 rounded-xl p-3 
                         border border-slate-200">
            <p className="text-xs font-bold text-slate-400 
                          uppercase mb-2">
              Invite Link
            </p>
            <div className="flex items-center gap-2">
              <code className="text-xs text-slate-600 flex-1 
                               break-all leading-relaxed">
                {generatedLink}
              </code>
              <Button
                type="primary"
                size="small"
                style={{ background: '#4F46E5' }}
                onClick={() => {
                  navigator.clipboard.writeText(generatedLink || '')
                  message.success('Copied!')
                }}
              >
                Copy
              </Button>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Button block onClick={() => setGeneratedLink(null)}>
              Generate Another
            </Button>
            <Button block type="primary"
              style={{ background: '#4F46E5' }}
              onClick={handleClose}>
              Done
            </Button>
          </div>
        </div>
      )}
    </Modal>
  )
}


function AddCandidateModal({
  open, onClose, onSuccess
}: {
  open: boolean
  onClose: () => void
  onSuccess: () => void
}) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [offerInHand, setOfferInHand] = useState(false)
  const queryClient = useQueryClient()

  // Skills search state
  const [skillOptions, setSkillOptions] = useState<{value: string, label: string}[]>([])
  const [skillSearching, setSkillSearching] = useState(false)

  const handleSkillSearch = async (q: string) => {
    if (!q || q.length < 1) return
    setSkillSearching(true)
    try {
      const res = await candidatesApi.searchSkills(q)
      const skills = (res as any)?.data?.data?.skills || []
      setSkillOptions(
        skills.map((s: any) => ({
          value: s.name,
          label: s.name,
          category: s.category
        }))
      )
    } catch {
      setSkillOptions([])
    } finally {
      setSkillSearching(false)
    }
  }

  // Location search state
  const [locationOptions, setLocationOptions] = useState<{value: string}[]>([])

  const handleLocationSearch = async (q: string) => {
    if (!q || q.length < 2) return
    try {
      const res = await candidatesApi.searchLocations(q)
      const locs = (res as any)?.data?.data?.locations || []
      setLocationOptions(locs.map((l: string) => ({ value: l })))
    } catch {
      setLocationOptions([])
    }
  }

  const { data: orgData } = useApiQuery(
    ['org_profile'],
    () => organisationApi.getProfile()
  )
  const countryCode = (orgData as any)?.data?.organisation?.country_code || 'IN'
  const salaryConfig = getSalaryConfig(countryCode)

  useEffect(() => {
    if (open && orgData) {
      const settings = (orgData as any)?.data?.organisation?.settings || {}
      if (settings.default_currency) {
        form.setFieldsValue({ salary_currency: settings.default_currency })
      }
    }
  }, [open, form, orgData])

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      const payload = {
        first_name: (values.first_name || '').trim(),
        last_name: (values.last_name || '').trim(),
        email: (values.email || '').trim(),
        phone: values.phone_field ? `${values.phone_field.country_code}:${values.phone_field.phone_number}` : '',
        phone_country_code: values.phone_field?.country_code || 'IN',
        phone_number: values.phone_field?.phone_number || '',
        linkedin_url: (values.linkedin_url || '').trim(),
        current_title: (values.current_title || '').trim(),
        current_company: (values.current_company || '').trim(),
        current_location_city: (values.location || '').trim(),
        experience_years: values.experience_years ?? undefined,
        relevant_experience_years: values.relevant_experience_years ?? undefined,
        highest_education: values.highest_education || '',
        graduation_year: values.graduation_year || null,
        nationality: values.nationality || '',
        work_authorization: values.work_authorization || '',
        languages: Array.isArray(values.languages) 
          ? values.languages : [],
        skills: Array.isArray(values.skills) 
          ? values.skills 
          : (values.skills || '').split(',').map((s: string) => s.trim()).filter(Boolean),
        source: values.source || 'company',
        entry_type: 'manual',
        salary_currency: values.salary_currency || 'INR',
        current_ctc: values.current_ctc ?? undefined,
        expected_salary_min: values.expected_salary_min ?? undefined,
        expected_salary_max: values.expected_salary_max ?? undefined,
        offer_in_hand: values.offer_in_hand === 'yes',
        offer_in_hand_amount: values.offer_in_hand === 'yes'
          ? (values.offer_in_hand_amount ?? undefined)
          : undefined,
        counter_offer: values.counter_offer ?? undefined,
        notice_period_days: values.notice_period_days ?? undefined,
        availability_status: values.availability_status || undefined,
        availability_date: values.available_from
          ? values.available_from.format('YYYY-MM-DD')
          : undefined,
        last_working_day: values.last_working_day
          ? values.last_working_day.format('YYYY-MM-DD')
          : undefined,
        work_mode_preference: values.work_mode_preference || 'any',
        relocation_willing: values.relocation_willing || 'maybe',
        preferred_locations: Array.isArray(values.preferred_locations)
          ? values.preferred_locations : [],
        fitment_score: values.fitment_score ?? undefined,
        metadata: {
          ...(values.resume_url ? { resume_public_url: values.resume_url } : {}),
          ...(values.portfolio_url ? { portfolio_url: values.portfolio_url } : {}),
          ...(values.github_url ? { github_url: values.github_url } : {}),
          ...(values.tags ? { tags: values.tags } : {}),
          ...(values.recruiter_rating ? { recruiter_rating: values.recruiter_rating } : {}),
          ...(values.do_not_contact ? { do_not_contact: values.do_not_contact } : {}),
        },
      }

      const res = await candidatesApi.create(payload)
      const candidateId = res?.data?.data?.candidate?.id

      if (candidateId && values.notes?.trim()) {
        await candidatesApi.addNote(candidateId, {
          note_text: values.notes.trim(),
          note_type: 'general',
        }).catch(() => {})
      }

      message.success('Candidate added successfully')
      form.resetFields()
      setOfferInHand(false)
      queryClient.invalidateQueries({ queryKey: ['candidates'] })
      onSuccess()
    } catch (err: any) {
      console.error('[DetailedAdd] error:', err)
      const errData = err?.response?.data
      if (err?.response?.status === 409) {
        message.warning(errData?.message || 'Candidate already exists')
        return
      }
      const fieldErrors = errData?.errors
      if (fieldErrors) {
        form.setFields(
          Object.entries(fieldErrors).map(([field, msgs]) => ({
            name: field,
            errors: Array.isArray(msgs) ? msgs : [msgs as string],
          }))
        )
      }
      message.error(errData?.message || 'Failed to add candidate')
    } finally {
      setLoading(false)
    }
  }

  const tabItems = [
    {
      key: 'basic',
      label: 'Basic Info',
      forceRender: true,
      children: (
        <div className="pt-4">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="first_name"
                label="First Name"
                rules={[{ required: true }]}
              >
                <Input placeholder="Jane" className="h-10 rounded-xl" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="last_name"
                label="Last Name"
                rules={[{ required: true }]}
              >
                <Input placeholder="Doe" className="h-10 rounded-xl" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="email"
                label="Email"
                rules={[{ type: 'email' }]}
              >
                <Input
                  type="email"
                  placeholder="jane@example.com"
                  className="h-10 rounded-xl"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="phone_field"
                label="Phone"
                rules={[getPhoneValidationRule()]}
              >
                <PhoneInput placeholder="Phone number" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="linkedin_url" label="LinkedIn">
            <Input
              placeholder="linkedin.com/in/..."
              className="h-10 rounded-xl"
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="current_title" label="Current Title">
                <Input
                  placeholder="Senior Engineer"
                  className="h-10 rounded-xl"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="current_company" label="Current Company">
                <Input
                  placeholder="Infosys Ltd"
                  className="h-10 rounded-xl"
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={24}>
              <Form.Item name="location" label="Location / Preferred">
                <AutoComplete
                  options={locationOptions}
                  onSearch={handleLocationSearch}
                  placeholder="Start typing city name..."
                  className="w-full"
                >
                  <Input className="h-10 rounded-xl" />
                </AutoComplete>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="experience_years"
                label="Total Exp (Yrs)"
              >
                <InputNumber
                  min={0} step={0.5}
                  className="w-full h-10 rounded-xl flex items-center"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="relevant_experience_years"
                label="Relevant Exp (Yrs)"
              >
                <InputNumber
                  min={0} step={0.5}
                  className="w-full h-10 rounded-xl flex items-center"
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="skills" label="Skills">
            <Select
              mode="tags"
              placeholder="Search or type a skill..."
              filterOption={false}
              onSearch={handleSkillSearch}
              loading={skillSearching}
              options={skillOptions}
              tokenSeparators={[',']}
              style={{ width: '100%' }}
            />
          </Form.Item>

          <Form.Item name="languages" label="Languages">
            <Select mode="tags" placeholder="Add languages..."
              options={[
                'English','Hindi','Tamil','Telugu','Kannada',
                'Marathi','Bengali','Gujarati','Punjabi',
                'Malayalam','Arabic','French','German',
                'Spanish','Mandarin'
              ].map(l => ({ value: l, label: l }))}
              tokenSeparators={[',']}
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="nationality" label="Nationality">
                <Input placeholder="e.g. Indian" 
                       className="h-10 rounded-xl" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="work_authorization" 
                         label="Work Authorization">
                <Select options={[
                  { value: 'citizen', label: 'Citizen' },
                  { value: 'permanent_resident', 
                    label: 'Permanent Resident' },
                  { value: 'work_visa', label: 'Work Visa' },
                  { value: 'need_sponsorship', 
                    label: 'Needs Sponsorship' },
                ]} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="highest_education" 
                         label="Highest Education">
                <Select options={[
                  { value: 'high_school', label: 'High School' },
                  { value: 'diploma', label: 'Diploma' },
                  { value: 'bachelor', label: "Bachelor's" },
                  { value: 'master', label: "Master's" },
                  { value: 'phd', label: 'PhD' },
                  { value: 'other', label: 'Other' },
                ]} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="graduation_year" 
                         label="Graduation Year">
                <InputNumber min={1970} max={2030} 
                  placeholder="2020"
                  className="w-full h-10 rounded-xl flex items-center" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="relocation_willing" 
                         label="Willing to Relocate">
                <Select options={[
                  { value: 'yes', label: 'Yes' },
                  { value: 'no', label: 'No' },
                  { value: 'maybe', label: 'Maybe' },
                ]} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="preferred_locations" 
                         label="Preferred Locations">
                <Select mode="tags" 
                  placeholder="Add cities..."
                  tokenSeparators={[',']} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={24}>
              <Form.Item name="source" label="Source">
                <Select
                  className="h-10"
                  options={[
                    { value: 'company', label: 'Direct Sourcing' },
                    { value: 'linkedin', label: 'LinkedIn' },
                    { value: 'referral', label: 'Referral' },
                    { value: 'job_board', label: 'Job Board' },
                    { value: 'agency', label: 'Agency' },
                  ]}
                />
              </Form.Item>
            </Col>
          </Row>
        </div>
      ),
    },
    {
      key: 'compensation',
      label: 'Compensation & Availability',
      forceRender: true,
      children: (
        <div className="pt-4">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="current_ctc"
                label={formatSalaryLabel(salaryConfig, 'Current Salary')}
              >
                <InputNumber
                  min={0}
                  className="w-full h-10 rounded-xl flex items-center"
                  placeholder={salaryConfig.placeholder}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="expected_salary_min"
                label={formatSalaryLabel(salaryConfig, 'Expected Salary')}
              >
                <InputNumber
                  min={0}
                  className="w-full h-10 rounded-xl flex items-center"
                  placeholder={salaryConfig.placeholder}
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="offer_in_hand"
                label="Offer in Hand?"
              >
                <Select
                  className="h-10"
                  onChange={(val) => setOfferInHand(val === 'yes')}
                  options={[
                    { value: 'no', label: 'No' },
                    { value: 'yes', label: 'Yes' },
                  ]}
                />
              </Form.Item>
            </Col>
            {offerInHand && (
              <Col span={12}>
                <Form.Item
                  name="offer_in_hand_amount"
                  label={formatSalaryLabel(salaryConfig, 'Offer Amount')}
                >
                  <InputNumber
                    min={0}
                    className="w-full h-10 rounded-xl flex items-center"
                    placeholder={salaryConfig.placeholder}
                  />
                </Form.Item>
              </Col>
            )}
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="counter_offer"
                label={formatSalaryLabel(salaryConfig, 'Counter Offer')}
              >
                <InputNumber
                  min={0}
                  className="w-full h-10 rounded-xl flex items-center"
                  placeholder={salaryConfig.placeholder}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="notice_period_days"
                label="Notice Period (Days)"
              >
                <Select
                  className="h-10"
                  options={[
                    { value: 0, label: 'Immediate' },
                    { value: 15, label: '15 Days' },
                    { value: 30, label: '30 Days' },
                    { value: 45, label: '45 Days' },
                    { value: 60, label: '60 Days' },
                    { value: 90, label: '90 Days' },
                  ]}
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="availability_status"
                label="Availability Status"
              >
                <Select
                  className="h-10"
                  options={[
                    { value: 'available_now', label: 'Available Now' },
                    { value: 'notice_period', label: 'Serving Notice' },
                    { value: 'open_to_offers', label: 'Open to Offers' },
                    { value: 'not_looking', label: 'Not Looking' },
                  ]}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="work_mode_preference"
                label="Work Mode Preference"
              >
                <Select
                  className="h-10"
                  options={[
                    { value: 'any', label: 'Any' },
                    { value: 'remote', label: 'Remote Only' },
                    { value: 'hybrid', label: 'Hybrid' },
                    { value: 'onsite', label: 'On-site Only' },
                  ]}
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="last_working_day"
                label="Last Working Day"
              >
                <DatePicker className="w-full h-10 rounded-xl" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="available_from"
                label="Available From Date"
              >
                <DatePicker className="w-full h-10 rounded-xl" />
              </Form.Item>
            </Col>
          </Row>
        </div>
      ),
    },
    {
      key: 'documents',
      label: 'Documents & Notes',
      forceRender: true,
      children: (
        <div className="pt-4">
          <Form.Item
            name="resume_url"
            label="Resume Public URL"
          >
            <Input
              placeholder="https://drive.google.com/..."
              className="h-10 rounded-xl"
              prefix={<Link size={14} className="text-slate-400" />}
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="portfolio_url" label="Portfolio URL">
                <Input placeholder="https://portfolio.com"
                       className="h-10 rounded-xl" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="github_url" label="GitHub URL">
                <Input placeholder="https://github.com/username"
                       className="h-10 rounded-xl" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="recruiter_rating" label="Recruiter Rating">
            <Select placeholder="Rate this candidate" options={[
              { value: 1, label: '★ Poor' },
              { value: 2, label: '★★ Below Average' },
              { value: 3, label: '★★★ Average' },
              { value: 4, label: '★★★★ Good' },
              { value: 5, label: '★★★★★ Excellent' },
            ]} />
          </Form.Item>

          <Form.Item name="do_not_contact" valuePropName="checked">
            <Checkbox>
              Do not contact — candidate has opted out
            </Checkbox>
          </Form.Item>

          <Form.Item name="tags" label="Tags (comma separated)">
            <Input
              placeholder="senior, backend, available"
              className="h-10 rounded-xl"
            />
          </Form.Item>

          <Form.Item name="notes" label="Recruiter Notes">
            <Input.TextArea
              rows={5}
              placeholder="Add screening notes, call summary, or any context about this candidate..."
              className="rounded-xl"
            />
          </Form.Item>
        </div>
      ),
    },
  ]

  return (
    <Modal
      title={
        <span className="text-lg font-bold text-slate-900">
          Add Candidate - Full Profile
        </span>
      }
      open={open}
      onCancel={() => {
        onClose()
        form.resetFields()
        setOfferInHand(false)
      }}
      onOk={() => form.submit()}
      okText="Save Candidate"
      okButtonProps={{ style: { background: '#4F46E5' } }}
      confirmLoading={loading}
      width={860}
      style={{ top: 20 }}
      styles={{ body: { maxHeight: '75vh', overflowY: 'auto' } }}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        initialValues={{
          source: 'company',
          salary_currency: 'INR',
          offer_in_hand: 'no',
          work_mode_preference: 'any',
          fitment_score: 70,
        }}
      >
        <Tabs items={tabItems} />
      </Form>
    </Modal>
  )
}

const FullCandidateList = ({ candidates, onSelect, selectedCandidateId, isLoading }: any) => {
  const columns: ColumnsType<Candidate> = [
    {
      title: 'Candidate Name',
      key: 'name',
      render: (_, record) => (
        <div className="flex items-center gap-3">
          <Avatar size={36} className="bg-blue-50 text-blue-600 font-bold border-none">
            {record.first_name?.charAt(0).toUpperCase()}{record.last_name?.charAt(0).toUpperCase()}
          </Avatar>
          <div className="min-w-0">
            <Text className="block font-bold text-slate-900 leading-tight truncate">{record.first_name} {record.last_name}</Text>
            <Text className="text-[11px] text-slate-400 font-medium truncate">{record.email}</Text>
          </div>
        </div>
      ),
    },
    {
      title: 'Current Role',
      key: 'role',
      render: (_, record) => (
        <div className="min-w-0">
          <Text className="block font-bold text-slate-700 text-xs truncate">{record.current_title || '—'}</Text>
          <Text className="text-[11px] text-slate-400 font-medium truncate uppercase tracking-wider">{record.current_company || '—'}</Text>
        </div>
      ),
    },
    {
      title: 'Experience',
      dataIndex: 'experience_years',
      key: 'exp',
      width: 100,
      render: (exp) => <Text className="font-bold text-slate-600">{exp || 0} Yrs</Text>
    },
    {
      title: 'Source',
      dataIndex: 'source',
      key: 'source',
      width: 120,
      render: (source: string) => (
        <Tag color={SOURCE_COLORS[source?.toLowerCase()] || 'default'} className="m-0 border-none font-bold text-[10px] uppercase rounded-full px-2">
          {source || 'Other'}
        </Tag>
      )
    },
    {
      title: 'Status',
      key: 'status',
      width: 120,
      render: (_, record: any) => {
        if (record.profile_status === 'draft') {
          return (
            <Tag color="warning" className="m-0 border-none font-bold text-[10px] uppercase px-2 rounded-full">
              Draft
            </Tag>
          )
        }
        if (record.profile_status === 'claimed') {
          return (
            <Tag color="success" className="m-0 border-none font-bold text-[10px] uppercase px-2 rounded-full">
              Claimed
            </Tag>
          )
        }
        return (
          <Tag
            color={record.is_actively_looking ? 'success' : 'default'}
            className="m-0 border-none font-bold text-[10px] uppercase px-2 rounded-full"
          >
            {record.is_actively_looking ? 'Active' : 'Passive'}
          </Tag>
        )
      }
    },
    {
      title: 'Updated At',
      dataIndex: 'updated_at',
      key: 'updated',
      width: 120,
      render: (d) => <span className="text-slate-400 text-[11px] font-bold uppercase tracking-wider">{dayjs(d).format('MMM D, YYYY')}</span>
    },
    {
      title: '',
      key: 'actions',
      width: 80,
      align: 'right',
      render: (_, record) => (
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button
            size="small"
            type="text"
            icon={<Edit className="h-3.5 w-3.5 text-slate-500" />}
            onClick={(e) => {
              e.stopPropagation()
              onSelect(record)  // select candidate first
              // small delay to let panel open then trigger edit
              setTimeout(() => {
                // dispatch custom event to trigger edit mode
                window.dispatchEvent(
                  new CustomEvent('candidate-edit', { 
                    detail: { id: record.id } 
                  })
                )
              }, 100)
            }}
            className="h-7 w-7 flex items-center justify-center rounded-lg"
          />
          <ChevronRight className="h-4 w-4 text-slate-300" />
        </div>
      )
    }
  ]

  return (
    <Table<Candidate>
      columns={columns}
      dataSource={candidates}
      rowKey="id"
      loading={isLoading}
      onRow={(record) => ({
        onClick: () => onSelect(record),
        className: cn(
          "cursor-pointer transition-all duration-200 group",
          record.id === selectedCandidateId ? "bg-blue-50 hover:bg-blue-50" : "hover:bg-slate-50"
        ),
      })}
      pagination={{ pageSize: 15, hideOnSinglePage: true }}
      className="modern-table"
    />
  )
}

const CompressedCandidateList = ({ candidates, onSelect, selectedCandidateId }: any) => {
  return (
    <div className="flex flex-col h-full overflow-y-auto bg-white border-r border-slate-200">
      <div className="p-4 border-b border-slate-100 flex items-center justify-between sticky top-0 bg-white z-10">
        <Text className="font-bold text-slate-900">Candidates</Text>
        <Badge count={candidates.length} showZero style={{ backgroundColor: '#f1f5f9', color: '#64748b', boxShadow: 'none' }} />
      </div>
      {candidates.map((item: any) => (
        <div 
          key={item.id}
          onClick={() => onSelect(item)}
          className={cn(
            "p-4 border-b border-slate-50 cursor-pointer transition-all border-l-4",
            item.id === selectedCandidateId 
              ? "bg-blue-50/50 border-l-blue-600" 
              : "bg-white border-l-transparent hover:bg-slate-50"
          )}
        >
          <div className="flex items-center gap-3">
             <Avatar size={32} className="bg-slate-100 text-slate-600 font-bold border-none shrink-0">
                {item.first_name?.charAt(0)}{item.last_name?.charAt(0)}
             </Avatar>
             <div className="min-w-0">
                <p className="m-0 font-bold text-slate-900 text-sm leading-tight truncate">
                  {item.first_name} {item.last_name}
                </p>
                <Text className="text-[10px] text-slate-400 font-medium truncate uppercase tracking-tight">
                  {item.current_title || 'No Title'}
                </Text>
             </div>
          </div>
        </div>
      ))}
    </div>
  )
}

// ─── Main CandidatesList ──────────────────────────────────────────────────────

export default function CandidatesList() {
  const [view, setView] = useState<'pool' | 'crm'>('pool')
  const [search, setSearch] = useState('')
  const [sourceFilter, setSourceFilter] = useState<string>('')
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null)
  const [addModalOpen, setAddModalOpen] = useState(false)
  const [chooserOpen, setChooserOpen] = useState(false)
  const [quickAddOpen, setQuickAddOpen] = useState(false)
  const [docUrl, setDocUrl] = useState<string | null>(null)
  const [inviteLinkOpen, setInviteLinkOpen] = useState(false)

  // Interactions (CRM drawer)
  const [interactionCandidate, setInteractionCandidate] = useState<any>(null)
  const [interactionType] = useState<string>('note')

  // Modals
  const [importModal, setImportModal] = useState(false)
  const [importToken, setImportToken] = useState('')
  const [addNoteModal, setAddNoteModal] = useState(false)
  const [scheduleModal, setScheduleModal] = useState(false)
  
  const { data, isLoading, refetch } = useApiQuery(
    ['candidates', search, sourceFilter],
    () => candidatesApi.list({ 
      search: search || undefined,
      source: sourceFilter || undefined
    })
  )

  const { data: pipelineData, isLoading: pipelineLoading } = useApiQuery(
    ['crm-pipeline'],
    () => candidatesApi.crmPipeline()
  )

  const candidates = (data as any)?.candidates ?? []
  const crmData = (pipelineData as any) || {}

  const handleDragEnd = async (result: any) => {
    const { source, destination, draggableId } = result
    if (!destination || (source.droppableId === destination.droppableId)) return
    
    try {
      await http.put(`/crm/pipeline/${draggableId}/move/`, { status: destination.droppableId })
      message.success('Candidate moved')
      refetch()
    } catch {
      message.error('Failed to move candidate')
    }
  }

  return (
    <div className="h-[calc(100vh-100px)] flex flex-col -m-6">
      {/* Header & View Switcher */}
      {!selectedCandidate && (
        <div className="p-6 pb-0 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 tracking-tight leading-none">Candidates</h1>
            <p className="text-slate-500 mt-2 font-medium">Your centralized talent database and recruitment CRM.</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Segmented
              value={view}
              onChange={(v: any) => setView(v)}
              className="p-1 bg-slate-100 rounded-xl"
              options={[
                { label: 'Talent Pool', value: 'pool', icon: <ListIcon className="h-4 w-4" /> },
                { label: 'CRM Kanban', value: 'crm', icon: <LayoutGrid className="h-4 w-4" /> },
              ]}
            />
            <Button icon={<Import className="h-4 w-4" />} className="h-10 rounded-xl font-bold" onClick={() => setImportModal(true)}>Import</Button>
            <Button
              icon={<Link className="h-4 w-4" />}
              className="h-10 rounded-xl font-bold"
              onClick={() => setInviteLinkOpen(true)}
            >
              Invite Link
            </Button>
            <Button 
              type="primary" 
              icon={<Plus className="h-4 w-4" />} 
              className="h-10 rounded-xl font-bold bg-blue-600 border-none shadow-soft-md px-6"
              onClick={() => setChooserOpen(true)}
            >
              Add Candidate
            </Button>
          </div>
        </div>
      )}

      {/* Toolbar / Filters */}
      {view === 'pool' && !selectedCandidate && (
        <div className="p-6 pb-4">
          <Card bordered={false} className="shadow-soft-sm bg-white/50 backdrop-blur-sm" styles={{ body: { padding: '12px' } }}>
            <Row gutter={[12, 12]} align="middle">
              <Col xs={24} md={12}>
                <Input
                  prefix={<Search className="h-4 w-4 text-slate-400 mr-2" />}
                  placeholder="Search candidates by name, email, skills..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="h-10 text-sm border-slate-200 rounded-xl"
                  allowClear
                />
              </Col>
              <Col xs={12} md={6}>
                <Select
                  className="w-full h-10"
                  placeholder="Filter by Source"
                  value={sourceFilter}
                  onChange={setSourceFilter}
                  allowClear
                  options={[
                    { value: 'linkedin', label: 'LinkedIn' },
                    { value: 'agency', label: 'Agency' },
                    { value: 'referral', label: 'Referral' },
                    { value: 'passport', label: 'Talent Passport' },
                  ]}
                />
              </Col>
              <Col xs={12} md={6}>
                <Button
                  icon={<RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />}
                  onClick={() => refetch()}
                  className="w-full h-10 flex items-center justify-center rounded-xl border-slate-200 font-bold"
                >
                  Refresh
                </Button>
              </Col>
            </Row>
          </Card>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden">
        {view === 'pool' ? (
          <div className="flex-1 overflow-hidden flex h-full">
            {/* Panel 1: List */}
            <div className={cn(
              "h-full overflow-y-auto bg-white border-r border-slate-200 transition-all duration-300",
              selectedCandidate ? "w-[20%] min-w-[200px]" : "w-full"
            )}>
              {selectedCandidate 
                ? (
                  <CompressedCandidateList
                    candidates={candidates}
                    selectedCandidateId={selectedCandidate?.id}
                    onSelect={setSelectedCandidate}
                  />
                )
                : (
                  <div className="p-6 pt-0 h-full overflow-y-auto">
                    <Tabs
                      defaultActiveKey="database"
                      className="modern-tabs mb-6"
                      items={[
                        {
                          key: 'database',
                          label: 'Candidate Database',
                          children: (
                            <Card bordered={false} className="shadow-soft-sm overflow-hidden p-0 border border-slate-100">
                              <FullCandidateList
                                candidates={candidates}
                                onSelect={setSelectedCandidate}
                                isLoading={isLoading}
                              />
                            </Card>
                          ),
                        },
                      ]}
                    />
                  </div>
                )
              }
            </div>

            {/* Panel 2: Quick View */}
            {selectedCandidate && (
              <div className={cn(
                "h-full overflow-y-auto bg-white border-r border-slate-200 transition-all duration-300",
                docUrl ? "w-[40%]" : "w-[80%]"
              )}>
                <CandidateQuickView
                  candidateId={selectedCandidate.id}
                  onClose={() => {
                    setSelectedCandidate(null)
                    setDocUrl(null)
                  }}
                  onOpenFullView={() => {
                    console.log('full view', selectedCandidate.id)
                  }}
                  onDocOpen={(url) => setDocUrl(url)}
                />
              </div>
            )}

            {/* Panel 3: Doc Viewer */}
            {selectedCandidate && docUrl && (
              <div className="w-[40%] h-full bg-white flex flex-col border-l border-slate-200">
                <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
                  <span className="font-bold text-slate-700 text-sm">
                    Document Preview
                  </span>
                  <Button
                    type="text"
                    size="small"
                    icon={<X className="h-4 w-4" />}
                    onClick={() => setDocUrl(null)}
                  />
                </div>
                <div className="flex-1 overflow-hidden">
                  <iframe
                    src={docUrl}
                    width="100%"
                    height="100%"
                    style={{ border: 'none' }}
                    title="Document Preview"
                  />
                </div>
                <div className="p-3 border-t border-slate-100 text-center">
                  <Button
                    size="small"
                    onClick={() => window.open(docUrl, '_blank')}
                  >
                    Open in New Tab
                  </Button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="p-6 h-full overflow-hidden">
            {pipelineLoading ? <div className="h-full flex items-center justify-center"><Spin size="large" /></div> : (
              <DragDropContext onDragEnd={handleDragEnd}>
                <div className="flex gap-6 h-full overflow-x-auto pb-4 items-start scrollbar-hide">
                  {CRM_STAGES.map((stage) => (
                    <div key={stage.key} className="flex flex-col w-72 shrink-0 h-full bg-slate-50/50 rounded-2xl border border-slate-200 shadow-soft-sm">
                      <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-slate-100">
                        <div className="flex items-center gap-2">
                          <span className="text-sm">{stage.icon}</span>
                          <span className="font-bold text-slate-900 text-sm tracking-tight">{stage.label}</span>
                        </div>
                        <Badge count={crmData[stage.key]?.length || 0} style={{ backgroundColor: '#f1f5f9', color: '#64748b', boxShadow: 'none', border: '1px solid #e2e8f0' }} />
                      </div>
                      <Droppable droppableId={stage.key}>
                        {(provided, snapshot) => (
                          <div
                            ref={provided.innerRef}
                            {...provided.droppableProps}
                            className={cn("flex-1 p-3 overflow-y-auto", snapshot.isDraggingOver ? "bg-blue-50/30" : "")}
                          >
                            {crmData[stage.key]?.length > 0 ? crmData[stage.key].map((cand: any, i: number) => (
                              <Draggable key={cand.id} draggableId={cand.id} index={i}>
                                {(p) => (
                                  <div ref={p.innerRef} {...p.draggableProps} {...p.dragHandleProps} className="mb-3">
                                    <Card bordered={false} className="shadow-soft-sm rounded-xl" styles={{ body: { padding: '12px' } }}>
                                      <Text className="block font-bold text-slate-800 text-xs mb-1 truncate">{cand.full_name}</Text>
                                      <Text className="text-[10px] text-slate-400 block truncate">{cand.current_title}</Text>
                                    </Card>
                                  </div>
                                )}
                              </Draggable>
                            )) : (
                              <div className="h-24 flex items-center justify-center border-2 border-dashed border-slate-200 rounded-2xl">
                                <span className="text-[10px] font-bold text-slate-300 uppercase tracking-widest">No candidates</span>
                              </div>
                            )}
                            {provided.placeholder}
                          </div>
                        )}
                      </Droppable>
                    </div>
                  ))}
                </div>
              </DragDropContext>
            )}
          </div>
        )}
      </div>

      {/* ── Drawers & Modals ──────────────────────────────────────────────── */}

      <CandidateInteractionDrawer
        candidate={interactionCandidate}
        initialType={interactionType}
        onClose={() => setInteractionCandidate(null)}
      />

      <AddCandidateModal
        open={addModalOpen}
        onClose={() => setAddModalOpen(false)}
        onSuccess={() => {
          setAddModalOpen(false)
          refetch()
        }}
      />

      <AddCandidateChooser
        open={chooserOpen}
        onClose={() => setChooserOpen(false)}
        onQuickAdd={() => setQuickAddOpen(true)}
        onDetailedAdd={() => setAddModalOpen(true)}
      />

      <QuickAddModal
        open={quickAddOpen}
        onClose={() => setQuickAddOpen(false)}
        onSuccess={() => {
          setQuickAddOpen(false)
          refetch()
        }}
      />

      <InviteLinkModal
        open={inviteLinkOpen}
        onClose={() => setInviteLinkOpen(false)}
      />

      {selectedCandidate && (
        <Modal
          title={<span className="font-bold text-slate-900">Add Note</span>}
          open={addNoteModal}
          onCancel={() => setAddNoteModal(false)}
          onOk={() => message.info('Note added')}
          destroyOnClose
        >
          <Input.TextArea rows={4} placeholder="Write your note here..." className="mt-4 rounded-xl" />
        </Modal>
      )}

      {selectedCandidate && (
        <ScheduleInterviewModal
          candidateId={selectedCandidate.id}
          open={scheduleModal}
          onClose={() => setScheduleModal(false)}
        />
      )}

      <Modal
        title={<span className="text-lg font-bold text-slate-900">Import from Passport</span>}
        open={importModal}
        onCancel={() => setImportModal(false)}
        onOk={() => message.info('Passport imported')}
        okText="Import Profile"
      >
        <p className="text-slate-500 mb-4 text-sm font-medium">Enter share token.</p>
        <Input placeholder="PAS-XXXX-XXXX" className="h-11 rounded-xl" value={importToken} onChange={e => setImportToken(e.target.value)} />
      </Modal>
    </div>
  )
}

function ScheduleInterviewModal({ candidateId, open, onClose }: any) {
  return (
    <Modal title="Schedule Interview" open={open} onCancel={onClose} onOk={() => { message.success('Scheduled'); onClose(); }}>
      <p className="text-sm text-slate-500">Scheduling interface for candidate {candidateId.substring(0,8)}</p>
    </Modal>
  )
}
