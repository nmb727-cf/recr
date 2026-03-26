/**
 * Candidate Onboarding — /onboarding
 * =====================================
 * Used by all three entry flows after the candidate has an authenticated account:
 *
 *   Source 1 (recruiter-added): Recruiter added the candidate via Quick/Detailed
 *     Add and sent a claim link.  After claiming via /candidate/claim/:token the
 *     candidate lands here with their profile PRE-FILLED from the recruiter's data.
 *
 *   Source 2 (apply-link form): Candidate filled a public apply form and created
 *     an account.  Onboarding prefills from the form submission data.
 *
 *   Source 3 (direct signup): Candidate signed up independently.  Form starts
 *     blank unless a matching candidate record was auto-linked during signup.
 *
 * PREFILL SOURCES (priority order):
 *   1. TalentPassport  — candidate's own profile store (most authoritative)
 *   2. LinkedCandidate — Candidate record added by recruiter (fills gaps)
 *   3. CustomUser      — auth record (name, email, phone, timezone)
 *
 * SAVE RULES:
 *   • Passport PUT: backend uses append-safe merge (empty strings never erase existing)
 *   • List fields (skills, languages): backend unions with existing values
 *   • Candidate PATCH: availability_status, nationality, work_authorization
 *   • Phone is always sent in E.164 format
 *   • On error: stay on same step, show exact field-level errors
 */

import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Steps, Card, Form, Input, Button, Row, Col, Select,
  Switch, InputNumber, Typography, Spin, Alert, Tag,
} from 'antd'
import {
  UserOutlined,
  SolutionOutlined,
  FileTextOutlined,
  ArrowRightOutlined,
  ArrowLeftOutlined,
  LinkOutlined,
  CheckCircleFilled,
  InfoCircleOutlined,
  ClockCircleOutlined,
  LoadingOutlined,
} from '@ant-design/icons'
import { useAuth } from '@/hooks/useAuth'
import { authApi } from '@/api/auth'
import { passportApi, type LinkedCandidateData } from '@/api/passport'
import type { Passport } from '@/types'
import { COUNTRIES, TIMEZONES } from '@/utils/locale'
import PhoneInput, {
  getPhoneValidationRule,
  getCombinedPhone,
  type PhoneValue,
} from '@/components/common/PhoneInput'
import {
  LANGUAGE_OPTIONS,
  AVAILABILITY_STATUS_OPTIONS,
  WORK_MODE_OPTIONS,
} from '@/constants/candidateFields'

const { Title, Text } = Typography

const ONBOARDING_THRESHOLD = 40

// ── Utility: union two string arrays (deduplicated, order preserved) ──────────
function unionLists(a: string[] = [], b: string[] = []): string[] {
  const seen = new Set(a.map((x) => x.toLowerCase()))
  const result = [...a]
  for (const item of b) {
    if (item && !seen.has(item.toLowerCase())) {
      result.push(item)
      seen.add(item.toLowerCase())
    }
  }
  return result
}

// ── Utility: pick first non-empty value ───────────────────────────────────────
function firstVal<T>(...values: (T | undefined | null | '')[]): T | undefined {
  for (const v of values) {
    if (v !== undefined && v !== null && v !== '') return v as T
  }
  return undefined
}

// ── Utility: flatten DRF serializer errors to readable messages ───────────────
function flattenErrors(errors: Record<string, unknown>): string {
  return Object.entries(errors)
    .map(([field, msgs]) => {
      const text = Array.isArray(msgs) ? msgs.join(', ') : String(msgs)
      return `${field}: ${text}`
    })
    .join(' | ')
}

// ── Parse the stored phone number, stripping any "CC:" prefix ────────────────
function parseStoredPhone(u: any): string {
  const dedicated = u?.phone_number
  if (dedicated) return dedicated
  const raw = u?.phone || ''
  const match = raw.match(/^[A-Z]{2,3}:(.+)$/)
  return match ? match[1] : raw
}

// ── Prefill source label (shown on field when prefilled) ──────────────────────
type PrefillSource = 'passport' | 'candidate' | 'user' | null

interface PrefillMeta {
  [field: string]: PrefillSource
}

export default function Onboarding() {
  const navigate = useNavigate()
  const { user, fetchMe } = useAuth()

  const [currentStep, setCurrentStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [initialising, setInitialising] = useState(true)  // true while fetching prefill data

  const [passport, setPassport] = useState<Passport | null>(null)
  const [linkedCandidate, setLinkedCandidate] = useState<LinkedCandidateData | null>(null)
  const [prefillMeta, setPrefillMeta] = useState<PrefillMeta>({})

  // Step-level error state — shown in an Alert above the submit button
  const [stepError, setStepError] = useState<string | null>(null)

  const [form] = Form.useForm()
  const step2FormRef = useRef<ReturnType<typeof Form.useForm>[0]>()

  // ── Initial data fetch ──────────────────────────────────────────────────────
  useEffect(() => {
    let cancelled = false

    const init = async () => {
      setInitialising(true)

      // Fetch passport and linked candidate in parallel
      const [passportResult, candidateResult] = await Promise.allSettled([
        passportApi.get(),
        passportApi.getLinkedCandidate(),
      ])

      if (cancelled) return

      let p: Passport | null = null
      let c: LinkedCandidateData | null = null

      if (passportResult.status === 'fulfilled') {
        p = passportResult.value.data.data.passport
        setPassport(p)
        // Already done with onboarding
        if (p && p.completeness_score >= ONBOARDING_THRESHOLD) {
          navigate('/dashboard')
          return
        }
      }

      if (
        candidateResult.status === 'fulfilled' &&
        !candidateResult.value.data.data.no_candidate
      ) {
        c = candidateResult.value.data.data.candidate
        setLinkedCandidate(c)
      }

      // Build prefill metadata so we can show users where data came from
      const meta: PrefillMeta = {}
      const textFields = [
        'current_title', 'current_company', 'current_location_city',
        'current_location_country', 'experience_years', 'linkedin_url',
      ]
      for (const field of textFields) {
        const passportVal = (p as any)?.[field]
        const candidateVal = (c as any)?.[field]
        if (passportVal) meta[field] = 'passport'
        else if (candidateVal) meta[field] = 'candidate'
      }
      for (const listField of ['skills', 'languages']) {
        const passportList = (p as any)?.[listField] || []
        const candidateList = (c as any)?.[listField] || []
        if (passportList.length && candidateList.length) meta[listField] = 'passport'
        else if (passportList.length) meta[listField] = 'passport'
        else if (candidateList.length) meta[listField] = 'candidate'
      }
      setPrefillMeta(meta)

      setInitialising(false)
    }

    init()
    return () => { cancelled = true }
  }, [navigate])

  // ── Derived prefill values (recomputed when passport or candidate changes) ──
  // Step 0: Basic info
  const step0Values = {
    first_name: firstVal(user?.first_name, linkedCandidate?.first_name) ?? '',
    last_name:  firstVal(user?.last_name,  linkedCandidate?.last_name)  ?? '',
    phone_field: {
      country_code: (user as any)?.phone_country_code
        || linkedCandidate?.phone_country_code
        || 'IN',
      phone_number: parseStoredPhone(user) || linkedCandidate?.phone_number || '',
    } as PhoneValue,
    timezone: (user as any)?.timezone
      || Intl.DateTimeFormat().resolvedOptions().timeZone
      || 'UTC',
    current_title:   firstVal((passport as any)?.current_title, linkedCandidate?.current_title),
    current_company: firstVal((passport as any)?.current_company, linkedCandidate?.current_company),
    current_location_city:
      firstVal((passport as any)?.current_location_city, linkedCandidate?.current_location_city),
    current_location_country:
      firstVal((passport as any)?.current_location_country, linkedCandidate?.current_location_country),
    experience_years:
      firstVal((passport as any)?.experience_years, linkedCandidate?.experience_years),
    linkedin_url:
      firstVal((passport as any)?.linkedin_url, linkedCandidate?.linkedin_url) ?? '',
  }

  // Step 1: Skills & preferences
  const mergedSkills   = unionLists((passport as any)?.skills,    linkedCandidate?.skills)
  const mergedLanguages = unionLists((passport as any)?.languages, linkedCandidate?.languages)
  const step1Values = {
    skills:           mergedSkills,
    languages:        mergedLanguages,
    is_actively_looking:
      firstVal((passport as any)?.is_actively_looking, linkedCandidate?.is_actively_looking)
        ?? true,
    preferred_work_mode:
      firstVal((passport as any)?.preferred_work_mode, linkedCandidate?.work_mode_preference)
        ?? 'any',
    availability_status:
      firstVal(linkedCandidate?.availability_status) ?? '',
    notice_period_days:
      firstVal((passport as any)?.notice_period_days, linkedCandidate?.notice_period_days),
    salary_currency:
      firstVal((passport as any)?.salary_currency, linkedCandidate?.salary_currency) ?? 'USD',
    expected_salary_min:
      firstVal((passport as any)?.expected_salary_min, linkedCandidate?.expected_salary_min),
    expected_salary_max:
      firstVal((passport as any)?.expected_salary_max, linkedCandidate?.expected_salary_max),
  }

  // Step 2: Resume — prefill CV URL if already on file
  const step2Values = {
    current_cv_url:
      firstVal((passport as any)?.current_cv_url, linkedCandidate?.resume_url) ?? '',
  }

  // ── Step handlers ───────────────────────────────────────────────────────────

  const handleStep1 = async (values: any) => {
    setStepError(null)
    setLoading(true)
    try {
      const phoneE164 = values.phone_field
        ? getCombinedPhone(
            values.phone_field.country_code,
            values.phone_field.phone_number
          )
        : ''

      // 1a. Update user account (name, phone, timezone)
      await authApi.updateMe({
        first_name: values.first_name,
        last_name: values.last_name,
        phone: phoneE164,
        phone_country_code: values.phone_field?.country_code || 'IN',
        phone_number: values.phone_field?.phone_number || '',
        timezone: values.timezone,
      })

      // 1b. Update passport (append-safe — backend skips empty strings)
      // Only send non-empty values to avoid inadvertently blanking existing data.
      const passportPayload: Record<string, unknown> = {}
      if (values.current_title)           passportPayload.current_title = values.current_title
      if (values.current_company)         passportPayload.current_company = values.current_company
      if (values.current_location_city)   passportPayload.current_location_city = values.current_location_city
      if (values.current_location_country) passportPayload.current_location_country = values.current_location_country
      if (values.experience_years != null) passportPayload.experience_years = values.experience_years
      if (values.linkedin_url)            passportPayload.linkedin_url = values.linkedin_url

      const res = await passportApi.update(passportPayload as any)
      const updated = res.data.data.passport
      setPassport(updated)

      await fetchMe()
      setCurrentStep(1)
    } catch (err: any) {
      const data = err.response?.data
      const detail =
        data?.errors ? flattenErrors(data.errors)
        : data?.message || err.message
        || 'Failed to save basic info'
      setStepError(detail)
      // Stay on step 0 — do not advance
    } finally {
      setLoading(false)
    }
  }

  const handleStep2 = async (values: any) => {
    setStepError(null)
    setLoading(true)
    try {
      // 2a. Passport: skills, languages, work preferences, salary
      //     List fields are union-merged server-side; sending current form values is safe.
      const passportPayload: Record<string, unknown> = {
        skills:              Array.isArray(values.skills)    ? values.skills    : [],
        languages:           Array.isArray(values.languages) ? values.languages : [],
        is_actively_looking: values.is_actively_looking !== false,
        preferred_work_mode: values.preferred_work_mode || 'any',
        notice_period_days:  values.notice_period_days ?? null,
        salary_currency:     values.salary_currency || 'USD',
      }
      if (values.expected_salary_min != null)
        passportPayload.expected_salary_min = values.expected_salary_min
      if (values.expected_salary_max != null)
        passportPayload.expected_salary_max = values.expected_salary_max

      const res = await passportApi.update(passportPayload as any)
      setPassport(res.data.data.passport)

      // 2b. Candidate model fields (availability_status lives on Candidate, not Passport)
      //     Use append semantics — backend skips empty values.
      const candidatePayload: Record<string, unknown> = {}
      if (values.availability_status) candidatePayload.availability_status = values.availability_status
      if (values.preferred_work_mode) candidatePayload.work_mode_preference = values.preferred_work_mode
      if (values.is_actively_looking !== undefined)
        candidatePayload.is_actively_looking = values.is_actively_looking
      if (values.notice_period_days != null)
        candidatePayload.notice_period_days = values.notice_period_days

      // Fire-and-forget — failure here is non-blocking
      passportApi.updateLinkedCandidate(candidatePayload).catch(() => {})

      setCurrentStep(2)
    } catch (err: any) {
      const data = err.response?.data
      const detail =
        data?.errors ? flattenErrors(data.errors)
        : data?.message || err.message
        || 'Failed to save preferences'
      setStepError(detail)
      // Stay on step 1
    } finally {
      setLoading(false)
    }
  }

  const handleStep3 = async (values: any) => {
    setStepError(null)
    setLoading(true)
    try {
      // Only update cv_url if the user actually typed something
      if (values.current_cv_url) {
        const res = await passportApi.update({ current_cv_url: values.current_cv_url } as any)
        setPassport(res.data.data.passport)
      }
      finishOnboarding()
    } catch (err: any) {
      const data = err.response?.data
      const detail =
        data?.errors ? flattenErrors(data.errors)
        : data?.message || err.message
        || 'Failed to save resume link'
      setStepError(detail)
      // Stay on step 2
    } finally {
      setLoading(false)
    }
  }

  const finishOnboarding = () => {
    sessionStorage.setItem('onboarding_just_completed', '1')
    navigate('/dashboard', { replace: true })
  }

  const skipStep3 = () => finishOnboarding()

  // ── Country change handler (auto-set currency) ──────────────────────────────
  const onCountryChange = (val: string) => {
    const country = COUNTRIES.find((c) => c.code === val || c.name === val)
    if (country) form.setFieldsValue({ salary_currency: country.currency })
  }

  const steps = [
    { title: 'Basic Info',         icon: <UserOutlined /> },
    { title: 'Skills & Preferences', icon: <SolutionOutlined /> },
    { title: 'Resume',             icon: <FileTextOutlined /> },
  ]

  // ── Prefill badge (shown on fields pre-populated from existing data) ─────────
  const PrefillBadge = ({ field }: { field: string }) => {
    const src = prefillMeta[field]
    if (!src) return null
    const labels: Record<PrefillSource & string, string> = {
      passport: 'From passport',
      candidate: 'From your profile',
      user: 'From account',
    }
    return (
      <Tag color="blue" className="text-[10px] ml-1 font-medium rounded-full">
        {labels[src]}
      </Tag>
    )
  }

  // ── Loading state while fetching initial data ─────────────────────────────
  if (initialising) {
    return (
      <div className="w-full flex flex-col items-center justify-center py-24 gap-4">
        <Spin indicator={<LoadingOutlined style={{ fontSize: 32 }} spin />} />
        <Text className="text-slate-400 text-sm">Loading your profile…</Text>
      </div>
    )
  }

  return (
    <div className="w-full">
      <Steps current={currentStep} items={steps} className="mb-8" />

      <Card bordered={false} className="shadow-soft-lg rounded-3xl p-2 border border-slate-100">

        {/* ── Step 0: Basic Info ──────────────────────────────────────────── */}
        {currentStep === 0 && (
          <Form
            form={form}
            layout="vertical"
            initialValues={step0Values}
            onFinish={handleStep1}
            requiredMark={false}
            className="p-4"
          >
            {stepError && (
              <Alert
                type="error"
                message={stepError}
                closable
                onClose={() => setStepError(null)}
                className="mb-4 rounded-xl"
              />
            )}

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="first_name"
                  label="First Name"
                  rules={[{ required: true, message: 'First name is required' }]}
                >
                  <Input placeholder="John" className="h-11 rounded-xl" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="last_name"
                  label="Last Name"
                  rules={[{ required: true, message: 'Last name is required' }]}
                >
                  <Input placeholder="Doe" className="h-11 rounded-xl" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="phone_field"
                  label="Phone Number"
                  rules={[
                    {
                      validator: (_: any, value: PhoneValue) => {
                        if (!value?.phone_number?.trim()) {
                          return Promise.reject(new Error('Phone number is required'))
                        }
                        return Promise.resolve()
                      },
                    },
                    getPhoneValidationRule(),
                  ]}
                >
                  <PhoneInput placeholder="Phone number" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="timezone"
                  label="Preferred Timezone"
                  rules={[{ required: true }]}
                >
                  <Select
                    showSearch
                    optionFilterProp="label"
                    suffixIcon={<ClockCircleOutlined />}
                    options={TIMEZONES}
                    className="h-11"
                  />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="current_title"
                  label={
                    <span>
                      Current Job Title
                      <PrefillBadge field="current_title" />
                    </span>
                  }
                >
                  <Input placeholder="Senior Engineer" className="h-11 rounded-xl" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="current_company"
                  label={
                    <span>
                      Current Company
                      <PrefillBadge field="current_company" />
                    </span>
                  }
                >
                  <Input placeholder="Acme Corp" className="h-11 rounded-xl" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="current_location_city"
                  label={
                    <span>
                      City
                      <PrefillBadge field="current_location_city" />
                    </span>
                  }
                >
                  <Input placeholder="Mumbai" className="h-11 rounded-xl" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="current_location_country"
                  label={
                    <span>
                      Country
                      <PrefillBadge field="current_location_country" />
                    </span>
                  }
                >
                  <Select
                    showSearch
                    placeholder="Select country"
                    className="h-11"
                    onChange={onCountryChange}
                    options={COUNTRIES.map((c) => ({ value: c.code, label: c.name }))}
                  />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item
              name="experience_years"
              label={
                <span>
                  Total Years of Experience
                  <PrefillBadge field="experience_years" />
                </span>
              }
            >
              <InputNumber
                min={0}
                max={50}
                step={0.5}
                className="w-full h-11 rounded-xl flex items-center"
              />
            </Form.Item>

            <Form.Item
              name="linkedin_url"
              label={
                <span>
                  LinkedIn Profile URL
                  <PrefillBadge field="linkedin_url" />
                </span>
              }
              rules={[{ type: 'url', message: 'Please enter a valid URL' }]}
            >
              <Input
                prefix={<LinkOutlined className="text-slate-300" />}
                placeholder="https://linkedin.com/in/yourname"
                className="h-11 rounded-xl"
              />
            </Form.Item>

            <Button
              type="primary"
              htmlType="submit"
              block
              size="large"
              loading={loading}
              className="mt-4 rounded-xl font-bold h-12 bg-blue-600 border-none shadow-soft-sm"
            >
              Save & Continue <ArrowRightOutlined />
            </Button>
          </Form>
        )}

        {/* ── Step 1: Skills & Preferences ───────────────────────────────── */}
        {currentStep === 1 && (
          <Form
            layout="vertical"
            initialValues={step1Values}
            onFinish={handleStep2}
            requiredMark={false}
            className="p-4"
          >
            {stepError && (
              <Alert
                type="error"
                message={stepError}
                closable
                onClose={() => setStepError(null)}
                className="mb-4 rounded-xl"
              />
            )}

            <Form.Item
              name="skills"
              label={
                <span>
                  Key Skills
                  <PrefillBadge field="skills" />
                  {mergedSkills.length > 0 && (
                    <span className="text-slate-400 text-xs ml-1">
                      ({mergedSkills.length} already added — you can add more)
                    </span>
                  )}
                </span>
              }
              rules={[{ required: true, message: 'Please add at least one skill' }]}
            >
              <Select
                mode="tags"
                placeholder="Type a skill and press enter (e.g. React, Python)"
                className="min-h-[44px] rounded-xl"
                tokenSeparators={[',']}
              />
            </Form.Item>

            <Form.Item
              name="languages"
              label={
                <span>
                  Languages Spoken
                  <PrefillBadge field="languages" />
                </span>
              }
            >
              <Select
                mode="tags"
                placeholder="Add languages (e.g. English, Hindi)"
                className="min-h-[44px] rounded-xl"
                options={LANGUAGE_OPTIONS.map((l) => ({ value: l, label: l }))}
                tokenSeparators={[',']}
              />
            </Form.Item>

            <div className="bg-slate-50 p-5 rounded-2xl mb-6 border border-slate-100">
              <Row gutter={24} align="middle">
                <Col span={14}>
                  <Text className="font-bold text-slate-700 block">Actively looking for jobs</Text>
                  <Text className="text-xs text-slate-400">Your profile will be visible to recruiters</Text>
                </Col>
                <Col span={10} className="text-right">
                  <Form.Item name="is_actively_looking" valuePropName="checked" className="m-0">
                    <Switch className="bg-slate-300" />
                  </Form.Item>
                </Col>
              </Row>
            </div>

            <Form.Item name="preferred_work_mode" label="Preferred Work Mode">
              <Select className="h-11" options={WORK_MODE_OPTIONS} />
            </Form.Item>

            <Form.Item name="availability_status" label="Availability Status">
              <Select
                className="h-11"
                placeholder="What's your current availability?"
                options={AVAILABILITY_STATUS_OPTIONS}
                allowClear
              />
            </Form.Item>

            <Form.Item name="notice_period_days" label="Notice Period (Days)">
              <InputNumber
                min={0}
                max={180}
                className="w-full h-11 rounded-xl flex items-center"
              />
            </Form.Item>

            <Row gutter={12}>
              <Col span={6}>
                <Form.Item name="salary_currency" label="Currency">
                  <Input placeholder="USD" className="h-11 rounded-xl uppercase" />
                </Form.Item>
              </Col>
              <Col span={9}>
                <Form.Item name="expected_salary_min" label="Min. Annual Salary">
                  <InputNumber
                    min={0}
                    className="w-full h-11 rounded-xl flex items-center"
                    placeholder="Min"
                  />
                </Form.Item>
              </Col>
              <Col span={9}>
                <Form.Item name="expected_salary_max" label="Max. Annual Salary">
                  <InputNumber
                    min={0}
                    className="w-full h-11 rounded-xl flex items-center"
                    placeholder="Max"
                  />
                </Form.Item>
              </Col>
            </Row>

            <div className="flex gap-3 mt-6">
              <Button
                block
                size="large"
                onClick={() => { setStepError(null); setCurrentStep(0) }}
                className="h-12 rounded-xl font-bold border-slate-200 text-slate-600"
              >
                <ArrowLeftOutlined /> Back
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                block
                size="large"
                loading={loading}
                className="h-12 rounded-xl font-bold bg-blue-600 border-none shadow-soft-sm"
              >
                Save & Continue <ArrowRightOutlined />
              </Button>
            </div>
          </Form>
        )}

        {/* ── Step 2: Resume ─────────────────────────────────────────────── */}
        {currentStep === 2 && (
          <div className="text-center p-6">
            <div className="mb-10">
              <div className="h-20 w-20 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-soft-sm">
                <FileTextOutlined style={{ fontSize: 32 }} />
              </div>
              <Title level={3} className="!mb-2 tracking-tight">Your Resume</Title>
              <Text className="text-slate-500 font-medium block mb-2">
                Help us understand your background better
              </Text>

              <div className="max-w-md mx-auto bg-amber-50 p-4 rounded-2xl border border-amber-100 flex items-start gap-3 text-left mt-6">
                <InfoCircleOutlined className="text-amber-500 mt-0.5" />
                <div className="text-xs text-amber-700 leading-relaxed">
                  <strong>Phase 1 Note:</strong> Direct file upload is coming soon. For now,
                  please provide a public link to your resume (e.g. from Google Drive, Dropbox,
                  or a portfolio site).
                </div>
              </div>
            </div>

            {stepError && (
              <Alert
                type="error"
                message={stepError}
                closable
                onClose={() => setStepError(null)}
                className="mb-4 rounded-xl max-w-md mx-auto text-left"
              />
            )}

            <Form
              layout="vertical"
              initialValues={step2Values}
              onFinish={handleStep3}
              className="max-w-md mx-auto"
            >
              <Form.Item
                name="current_cv_url"
                label={
                  <span className="text-slate-400 font-bold text-[10px] uppercase tracking-widest">
                    Public Resume URL (Optional)
                    {step2Values.current_cv_url && (
                      <Tag color="blue" className="ml-1 text-[10px] rounded-full">
                        Already on file
                      </Tag>
                    )}
                  </span>
                }
                rules={[{ type: 'url', message: 'Please enter a valid URL' }]}
              >
                <Input
                  prefix={<LinkOutlined className="text-slate-300" />}
                  placeholder="https://..."
                  className="h-12 rounded-xl"
                />
              </Form.Item>

              <div className="flex flex-col gap-3 mt-8">
                <Button
                  type="primary"
                  htmlType="submit"
                  block
                  size="large"
                  loading={loading}
                  className="h-12 rounded-xl font-bold bg-slate-900 border-none shadow-soft-md"
                >
                  Finish & View Dashboard
                </Button>
                <Button
                  type="text"
                  block
                  onClick={skipStep3}
                  className="text-slate-400 font-bold"
                >
                  Skip this for now
                </Button>
                <Button
                  type="text"
                  size="small"
                  onClick={() => { setStepError(null); setCurrentStep(1) }}
                  className="text-slate-300"
                >
                  <ArrowLeftOutlined /> Back
                </Button>
              </div>
            </Form>

            {passport && (
              <div className="mt-12 p-6 bg-slate-50 rounded-3xl border border-slate-100 text-left">
                <div className="flex justify-between items-center mb-3">
                  <Text className="font-bold text-slate-500 text-xs uppercase tracking-widest">
                    Profile Completion
                  </Text>
                  <Text className="text-xs font-bold text-blue-600">
                    {passport.completeness_score}%
                  </Text>
                </div>
                <div className="h-2.5 w-full bg-slate-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-600 transition-all duration-700 ease-out"
                    style={{ width: `${passport.completeness_score}%` }}
                  />
                </div>
                {passport.completeness_score >= ONBOARDING_THRESHOLD && (
                  <div className="mt-4 flex items-center gap-2 text-emerald-600">
                    <CheckCircleFilled />
                    <span className="text-xs font-bold uppercase tracking-tight">
                      Minimum requirements met
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  )
}
