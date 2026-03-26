import { useEffect, useMemo, useState } from 'react'
import { Alert, Form, Input, InputNumber, Modal, Select, Steps, Tag, Typography, message } from 'antd'
import { CheckCircle2, Copy, FileText, FileUp, IdCard, Link2, PlusSquare, ShieldCheck } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { candidatesApi } from '@/api/candidates'
import { organisationApi } from '@/api/organisation'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useAuthStore } from '@/store/authStore'
import http from '@/utils/http'
import { COUNTRIES, CURRENCIES } from '@/utils/locale'
import { getSalaryConfig } from '@/utils/salary'
import {
  WORK_AUTHORIZATION_OPTIONS,
  SOURCE_OPTIONS,
  LANGUAGE_OPTIONS,
  TAG_OPTIONS,
} from '@/constants/candidateFields'

const { Text } = Typography

type SourceSurface = 'database' | 'active_work'
type TenantType = 'company' | 'agency'

type EntryMethod =
  | 'quick_add'
  | 'detailed_add'
  | 'invite_candidate'
  | 'upload_resume'
  | 'import_passport'
  | 'agency_submit'

type NextAction =
  | 'save_to_database_only'
  | 'add_to_active_work'
  | 'match_to_jobs'
  | 'send_info_request_link'
  | 'assign_to_recruiter'
  | 'keep_in_nurture_pool'

interface Props {
  open: boolean
  onClose: () => void
  sourceSurface: SourceSurface
  onCompleted?: () => void
  mode?: 'add' | 'edit'
  candidateId?: string
  initialCandidate?: Record<string, any> | null
}

const METHOD_CONFIG: Array<{
  key: EntryMethod
  label: string
  icon: JSX.Element
  supportedTenants: TenantType[]
  implemented: boolean
}> = [
  { key: 'quick_add', label: 'Quick Add', icon: <PlusSquare size={15} />, supportedTenants: ['company', 'agency'], implemented: true },
  { key: 'detailed_add', label: 'Detailed Add', icon: <FileText size={15} />, supportedTenants: ['company', 'agency'], implemented: true },
  { key: 'invite_candidate', label: 'Invite Link', icon: <Link2 size={15} />, supportedTenants: ['company', 'agency'], implemented: true },
  { key: 'upload_resume', label: 'Resume Upload', icon: <FileUp size={15} />, supportedTenants: ['company', 'agency'], implemented: false },
  { key: 'import_passport', label: 'Passport Import', icon: <IdCard size={15} />, supportedTenants: ['company', 'agency'], implemented: false },
  { key: 'agency_submit', label: 'Agency Submit', icon: <ShieldCheck size={15} />, supportedTenants: ['agency'], implemented: false },
]

const ACTION_LABELS: Record<NextAction, string> = {
  save_to_database_only: 'Save to database only',
  add_to_active_work: 'Add to active work',
  match_to_jobs: 'Match to jobs',
  send_info_request_link: 'Send info request link',
  assign_to_recruiter: 'Assign to recruiter',
  keep_in_nurture_pool: 'Keep in nurture pool',
}

function tenantTypeFromRole(role?: string): TenantType {
  return role?.startsWith('agency_') ? 'agency' : 'company'
}

function actionsForContext(sourceSurface: SourceSurface, method: EntryMethod): NextAction[] {
  if (method === 'invite_candidate') return ['send_info_request_link']
  if (method === 'upload_resume' || method === 'import_passport') return ['save_to_database_only', 'add_to_active_work']
  if (sourceSurface === 'active_work') {
    return ['add_to_active_work', 'save_to_database_only', 'match_to_jobs', 'assign_to_recruiter', 'keep_in_nurture_pool']
  }
  return ['save_to_database_only', 'add_to_active_work', 'match_to_jobs', 'send_info_request_link', 'assign_to_recruiter', 'keep_in_nurture_pool']
}

function defaultAction(sourceSurface: SourceSurface, method: EntryMethod): NextAction {
  if (method === 'invite_candidate') return 'send_info_request_link'
  if (method === 'upload_resume' || method === 'import_passport') return 'save_to_database_only'
  return sourceSurface === 'active_work' ? 'add_to_active_work' : 'save_to_database_only'
}

// SOURCE_OPTIONS, LANGUAGE_OPTIONS, TAG_OPTIONS imported from @/constants/candidateFields

function moneyMultiplier(countryCode: string): number {
  const code = String(countryCode || '').toUpperCase()
  if (code === 'IN') return 100000
  if (['US', 'GB', 'AU', 'SG', 'CA'].includes(code)) return 1000
  return 1
}

export default function AddCandidateWorkflowModal({
  open,
  onClose,
  sourceSurface,
  onCompleted,
  mode = 'add',
  candidateId,
  initialCandidate,
}: Props) {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()
  const role = useAuthStore((s) => s.user?.role)
  const tenantType = tenantTypeFromRole(role)
  const [skillOptions, setSkillOptions] = useState<Array<{ label: string; value: string }>>([])

  const [step, setStep] = useState(0)
  const [method, setMethod] = useState<EntryMethod>(mode === 'edit' ? 'detailed_add' : 'quick_add')
  const [nextAction, setNextAction] = useState<NextAction>(defaultAction(sourceSurface, 'quick_add'))
  const [generatedInviteLink, setGeneratedInviteLink] = useState('')

  const { data: orgProfileData } = useApiQuery(
    ['org_profile', 'candidate_workflow'],
    () => organisationApi.getProfile(),
    { enabled: open },
  )
  const { data: orgUsersData } = useApiQuery(
    ['org_users', 'candidate_workflow'],
    () => organisationApi.listUsers(),
    { enabled: open },
  )

  const organisation = (orgProfileData as any)?.organisation || {}
  const orgCountryCode = organisation?.country_code || 'IN'
  const defaultCurrency =
    organisation?.settings?.default_currency ||
    CURRENCIES.find((c) => c.code === organisation?.currency)?.code ||
    CURRENCIES.find((c) => c.code === 'INR')?.code ||
    'INR'
  const salaryConfig = getSalaryConfig(orgCountryCode)
  const salaryMultiplier = moneyMultiplier(orgCountryCode)
  const assignableUsers = (((orgUsersData as any)?.users || []) as Array<any>).filter((u) => u?.is_active !== false)
  const assignableUserOptions = assignableUsers.map((u) => ({
    label: u?.full_name || [u?.first_name, u?.last_name].filter(Boolean).join(' ') || u?.email || u?.id,
    value: u?.id,
  }))

  const visibleMethods = useMemo(
    () => METHOD_CONFIG.filter((m) => m.supportedTenants.includes(tenantType)),
    [tenantType],
  )
  const selectedMethodConfig = METHOD_CONFIG.find((m) => m.key === method)
  const methodImplemented = selectedMethodConfig?.implemented === true
  const isEditMode = mode === 'edit'
  const availableActions = actionsForContext(sourceSurface, method)
  const noticePeriodApplicable = Form.useWatch('notice_period_applicable', form)
  const offerInHand = Form.useWatch('offer_in_hand', form)

  useEffect(() => {
    if (!open) return
    setStep(0)
    setGeneratedInviteLink('')
    const firstVisible = isEditMode ? 'detailed_add' : (visibleMethods[0]?.key || 'quick_add')
    setMethod(firstVisible)
    setNextAction(defaultAction(sourceSurface, firstVisible))
    form.resetFields()
    if (isEditMode && initialCandidate) {
      const metadata = initialCandidate?.metadata || {}
      const noticeApplicable = Boolean(
        initialCandidate.notice_period_days ||
        initialCandidate.last_working_day,
      )
      form.setFieldsValue({
        first_name: initialCandidate.first_name || '',
        last_name: initialCandidate.last_name || '',
        email: initialCandidate.email || '',
        phone: initialCandidate.phone || '',
        linkedin_url: initialCandidate.linkedin_url || '',
        current_title: initialCandidate.current_title || '',
        current_company: initialCandidate.current_company || '',
        current_location_city: initialCandidate.current_location_city || '',
        current_location_country: initialCandidate.current_location_country || '',
        experience_years: initialCandidate.experience_years ?? undefined,
        expected_salary_min: fromStoredMoney(initialCandidate.expected_salary_min),
        expected_salary_max: fromStoredMoney(initialCandidate.expected_salary_max),
        salary_currency: initialCandidate.salary_currency || defaultCurrency,
        notice_period_applicable: noticeApplicable,
        notice_period_days: noticeApplicable ? (initialCandidate.notice_period_days ?? undefined) : undefined,
        last_working_day: initialCandidate.last_working_day || undefined,
        availability_date: initialCandidate.availability_date || undefined,
        is_actively_looking: initialCandidate.is_actively_looking !== false,
        source: initialCandidate.source || '',
        source_detail: initialCandidate.source_detail || '',
        tags: Array.isArray(initialCandidate.tags) ? initialCandidate.tags : [],
        skills: Array.isArray(initialCandidate.skills) ? initialCandidate.skills : [],
        languages: Array.isArray(initialCandidate.languages) ? initialCandidate.languages : [],
        nationality: initialCandidate.nationality || '',
        work_authorization: initialCandidate.work_authorization || '',
        visa_status: metadata.visa_status || '',
        pr_status: metadata.pr_status || '',
        offer_in_hand: Boolean(initialCandidate.offer_in_hand),
        offer_in_hand_amount: fromStoredMoney(initialCandidate.offer_in_hand_amount),
        offer_currency: metadata.offer_currency || initialCandidate.salary_currency || defaultCurrency,
        assigned_to: initialCandidate.assigned_to || undefined,
        owner_user_id: initialCandidate.owner_user_id || undefined,
        notes: metadata.internal_note || '',
        resume_url: initialCandidate.resume_url || initialCandidate?.metadata?.resume_public_url || '',
      })
      return
    }
    form.setFieldsValue({
      salary_currency: defaultCurrency,
      offer_currency: defaultCurrency,
      notice_period_applicable: false,
      offer_in_hand: false,
      source: 'company',
      tags: [],
      skills: [],
      languages: [],
    })
  }, [open, form, sourceSurface, visibleMethods, isEditMode, initialCandidate, defaultCurrency, salaryMultiplier])

  useEffect(() => {
    setNextAction(defaultAction(sourceSurface, method))
  }, [sourceSurface, method])

  useEffect(() => {
    if (noticePeriodApplicable === false) {
      form.setFieldsValue({ notice_period_days: undefined, last_working_day: undefined })
    }
  }, [noticePeriodApplicable, form])

  useEffect(() => {
    if (offerInHand === false) {
      form.setFieldsValue({ offer_in_hand_amount: undefined })
    }
  }, [offerInHand, form])

  const createCandidateMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => candidatesApi.create(payload),
  })

  const createInviteMutation = useMutation({
    mutationFn: (payload: { expires_days?: number; max_uses?: number }) => candidatesApi.createInviteLink(payload),
  })

  const skillSuggestMutation = useMutation({
    mutationFn: async (q: string) => {
      const response: any = await candidatesApi.searchSkills(q)
      const payload = response?.data?.data || response?.data || {}
      const values: any[] = payload?.skills || payload?.results || payload?.items || []
      const normalized = values
        .map((item) => (typeof item === 'string' ? item : (item?.name || item?.label || item?.value || '')))
        .filter(Boolean)
      return Array.from(new Set(normalized))
    },
    onSuccess: (skills) => {
      setSkillOptions(skills.map((skill) => ({ label: skill, value: skill })))
    },
  })

  const fromStoredMoney = (value?: number | string | null) => {
    if (value === null || value === undefined || value === '') return undefined
    const numeric = Number(value)
    if (!Number.isFinite(numeric)) return undefined
    return Number((numeric / salaryMultiplier).toFixed(2))
  }

  const toStoredMoney = (value?: number | string | null) => {
    if (value === null || value === undefined || value === '') return undefined
    const numeric = Number(value)
    if (!Number.isFinite(numeric)) return undefined
    return Number((numeric * salaryMultiplier).toFixed(2))
  }

  // Quick Add: identity + enough professional context to be useful in sourcing
  const quickAddFields = ['first_name', 'last_name', 'email', 'phone', 'current_title', 'resume_url']
  const detailedFields = [
    'first_name', 'last_name', 'email', 'phone', 'linkedin_url',
    'current_title', 'current_company', 'current_location_city', 'current_location_country',
    'experience_years', 'expected_salary_min', 'expected_salary_max', 'salary_currency',
    'notice_period_applicable', 'notice_period_days', 'last_working_day', 'availability_date', 'is_actively_looking',
    'offer_in_hand', 'offer_in_hand_amount', 'offer_currency',
    'source', 'source_detail', 'tags', 'skills', 'languages',
    'nationality', 'work_authorization', 'visa_status', 'pr_status',
    'assigned_to', 'owner_user_id', 'resume_url', 'notes',
  ]
  const inviteFields = ['invite_expires_days', 'invite_max_uses', 'invite_message']

  const validateMethodFields = async () => {
    if (method === 'quick_add') {
      await form.validateFields(quickAddFields)
      const email = String(form.getFieldValue('email') || '').trim()
      const phone = String(form.getFieldValue('phone') || '').trim()
      if (!email && !phone) throw new Error('Provide phone or email')
      return
    }
    if (method === 'detailed_add') {
      await form.validateFields(detailedFields)
      const email = String(form.getFieldValue('email') || '').trim()
      const phone = String(form.getFieldValue('phone') || '').trim()
      if (!email && !phone) throw new Error('Provide phone or email')
      if (form.getFieldValue('notice_period_applicable') && !form.getFieldValue('last_working_day')) {
        throw new Error('Last working day is required when notice period is applicable')
      }
      if (form.getFieldValue('offer_in_hand') && !form.getFieldValue('offer_in_hand_amount')) {
        throw new Error('Offer amount is required when offer in hand is marked yes')
      }
      return
    }
    if (method === 'invite_candidate') {
      await form.validateFields(inviteFields)
    }
  }

  const runCandidateCreate = async () => {
    const values = form.getFieldsValue(true)
    const tags = Array.isArray(values.tags) ? values.tags.filter(Boolean) : []
    const skills = Array.isArray(values.skills) ? values.skills.filter(Boolean) : []
    const languages = Array.isArray(values.languages) ? values.languages.filter(Boolean) : []
    const salaryCurrency = values.salary_currency || defaultCurrency
    const offerCurrency = values.offer_currency || salaryCurrency
    const metadata: Record<string, unknown> = {
      ...((isEditMode ? initialCandidate?.metadata : {}) || {}),
      visa_status: values.visa_status || '',
      pr_status: values.pr_status || '',
      offer_currency: offerCurrency,
    }
    if (values.notes) {
      metadata.internal_note = values.notes
    }
    const payload: Record<string, unknown> = {
      entry_method: method,
      next_action: nextAction,
      first_name: values.first_name,
      last_name: values.last_name,
      email: values.email || '',
      phone: values.phone || '',
      linkedin_url: values.linkedin_url || '',
      current_title: values.current_title || '',
      current_company: values.current_company || '',
      experience_years: values.experience_years || undefined,
      current_location_city: values.current_location_city || '',
      current_location_country: values.current_location_country || '',
      nationality: values.nationality || '',
      work_authorization: values.work_authorization || '',
      source: values.source || 'company',
      source_detail: values.source_detail || '',
      resume_url: values.resume_url || '',
      skills,
      tags,
      languages,
      expected_salary_min: toStoredMoney(values.expected_salary_min),
      expected_salary_max: toStoredMoney(values.expected_salary_max),
      salary_currency: salaryCurrency,
      notice_period_days: values.notice_period_applicable ? (values.notice_period_days || undefined) : undefined,
      last_working_day: values.notice_period_applicable ? (values.last_working_day || undefined) : undefined,
      availability_date: values.availability_date || undefined,
      is_actively_looking: values.is_actively_looking !== false,
      offer_in_hand: values.offer_in_hand === true,
      offer_in_hand_amount: values.offer_in_hand ? toStoredMoney(values.offer_in_hand_amount) : undefined,
      assigned_to: values.assigned_to || undefined,
      owner_user_id: values.owner_user_id || undefined,
      metadata,
      send_invite: nextAction === 'send_info_request_link',
    }

    if (isEditMode && candidateId) {
      await candidatesApi.update(candidateId, payload)
      message.success('Candidate updated')
      onCompleted?.()
      onClose()
      return
    }

    const response: any = await createCandidateMutation.mutateAsync(payload)
    const createdId = response?.data?.data?.candidate?.id || response?.data?.candidate?.id
    if (!isEditMode && nextAction === 'add_to_active_work' && createdId) {
      await http.post(`/candidates/${createdId}/engagements/`, { stage: 'new_lead' })
    }

    message.success('Candidate added')
    onCompleted?.()
    onClose()
  }

  const runInviteCreate = async () => {
    const values = form.getFieldsValue(true)
    const response: any = await createInviteMutation.mutateAsync({
      expires_days: values.invite_expires_days || 7,
      max_uses: values.invite_max_uses || 1,
    })
    const linkPayload = response?.data?.data?.link || {}
    const token = linkPayload?.token
    const inviteUrl = linkPayload?.url
      ? `${window.location.origin}${linkPayload.url}`
      : (token ? `${window.location.origin}/apply/${token}/` : '')
    setGeneratedInviteLink(inviteUrl)
    if (inviteUrl) {
      message.success('Invite link generated')
    } else {
      message.warning('Invite generated but link was not returned by API')
    }
    queryClient.invalidateQueries({ queryKey: ['invite-links'] })
    onCompleted?.()
  }

  const submitFinal = async () => {
    if (!methodImplemented) return
    try {
      if (method === 'invite_candidate') {
        await runInviteCreate()
      } else {
        await runCandidateCreate()
      }
    } catch (err: any) {
      message.error(err?.response?.data?.message || err?.message || 'Unable to complete add candidate flow')
    }
  }

  const goNext = async () => {
    if (isEditMode) {
      try {
        await validateMethodFields()
        await submitFinal()
      } catch (err: any) {
        message.error(err?.message || 'Please complete required fields')
      }
      return
    }
    if (step === 0) {
      if (!methodImplemented) {
        message.info('This method is coming soon')
        return
      }
      setStep(1)
      return
    }
    if (step === 1) {
      try {
        await validateMethodFields()
        setStep(2)
      } catch (err: any) {
        message.error(err?.message || 'Please complete required fields')
      }
      return
    }
    await submitFinal()
  }

  const busy = createCandidateMutation.isPending || createInviteMutation.isPending
  const primaryText = isEditMode
    ? 'Save Candidate'
    : (step < 2 ? 'Next' : method === 'invite_candidate' ? 'Generate Invite Link' : 'Create Candidate')

  return (
    <Modal
      open={open}
      onCancel={onClose}
      title="Add Candidate"
      width={860}
      footer={[
        <button
          key="back"
          onClick={() => (step === 0 ? onClose() : setStep(step - 1))}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
        >
          {step === 0 ? 'Cancel' : 'Back'}
        </button>,
        <button
          key="next"
          onClick={goNext}
          disabled={busy}
          className="rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-700 disabled:opacity-60"
        >
          {busy ? 'Please wait...' : primaryText}
        </button>,
      ]}
      destroyOnClose
    >
      <div className="space-y-4 pt-2">
        <Steps
          current={step}
          size="small"
          items={isEditMode ? [{ title: 'Detailed Candidate Form' }] : [
            { title: 'Choose Method' },
            { title: 'Method Form' },
            { title: 'Next Action' },
          ]}
        />

        {!isEditMode && step === 0 && (
          <div className="grid grid-cols-2 gap-3">
            {visibleMethods.map((m) => {
              const active = method === m.key
              return (
                <button
                  key={m.key}
                  onClick={() => m.implemented && setMethod(m.key)}
                  disabled={!m.implemented}
                  className={`rounded-xl border p-3 text-left transition ${
                    active ? 'border-indigo-300 bg-indigo-50' : 'border-slate-200 bg-white'
                  } ${m.implemented ? 'hover:border-indigo-300' : 'opacity-65 cursor-not-allowed'}`}
                >
                  <div className="flex items-center justify-between">
                    <span className="inline-flex items-center gap-2 text-sm font-semibold text-slate-800">
                      {m.icon}
                      {m.label}
                    </span>
                    {!m.implemented && <Tag color="default">Coming soon</Tag>}
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    {m.key === 'quick_add' && 'Fast intake for calls, WhatsApp leads, and quick sourcing.'}
                    {m.key === 'detailed_add' && 'Full recruiter-driven candidate entry for enterprise workflows.'}
                    {m.key === 'invite_candidate' && 'Generate an invite link for candidate self-service profile completion.'}
                    {m.key === 'upload_resume' && 'Upload and parse resume before final review and save.'}
                    {m.key === 'import_passport' && 'Import candidate data from passport token/link and review.'}
                    {m.key === 'agency_submit' && 'Agency-side candidate submission flow.'}
                  </p>
                </button>
              )
            })}
          </div>
        )}

        {(isEditMode || step >= 1) && (
          <Form form={form} layout="vertical" initialValues={{ invite_expires_days: 7, invite_max_uses: 1 }} className="pt-1">
            {method === 'quick_add' && (
              <>
                <Alert type="info" showIcon message="Quick Add captures minimum identity + title. Remaining fields can be filled later via Detailed Add or by the candidate." />
                {/* Quick Add canonical fields: first_name, last_name, email, phone, current_title, source, resume_url */}
                <div className="mt-3 grid grid-cols-2 gap-3">
                  <Form.Item name="first_name" label="First Name" rules={[{ required: true }]}><Input /></Form.Item>
                  <Form.Item name="last_name" label="Last Name" rules={[{ required: true }]}><Input /></Form.Item>
                  <Form.Item name="phone" label="Phone"><Input /></Form.Item>
                  <Form.Item name="email" label="Email"><Input /></Form.Item>
                  <Form.Item name="current_title" label="Current Title">
                    <Input placeholder="e.g. Senior Engineer" />
                  </Form.Item>
                  <Form.Item name="source" label="Source">
                    <Select options={SOURCE_OPTIONS} />
                  </Form.Item>
                  <Form.Item name="resume_url" label="Resume Link" className="col-span-2">
                    <Input placeholder="https://drive.google.com/..." />
                  </Form.Item>
                </div>
              </>
            )}

            {method === 'detailed_add' && (
              <div className="space-y-3">
                <Alert type="info" showIcon message="Detailed form is schema-aligned. Skills/tags/languages are controlled selectors and will integrate with master data progressively." />
                <div className="rounded-lg border border-slate-200 p-3">
                  <p className="mb-2 text-xs font-bold uppercase text-slate-500">Basic Info</p>
                  <div className="grid grid-cols-2 gap-3">
                    <Form.Item name="first_name" label="First Name" rules={[{ required: true }]}><Input /></Form.Item>
                    <Form.Item name="last_name" label="Last Name" rules={[{ required: true }]}><Input /></Form.Item>
                    <Form.Item name="email" label="Email"><Input /></Form.Item>
                    <Form.Item name="phone" label="Phone"><Input /></Form.Item>
                    <Form.Item name="linkedin_url" label="LinkedIn URL"><Input /></Form.Item>
                    <Form.Item name="nationality" label="Nationality">
                      <Select
                        allowClear
                        showSearch
                        options={COUNTRIES.map((c) => ({ label: c.name, value: c.name }))}
                        optionFilterProp="label"
                      />
                    </Form.Item>
                    <Form.Item name="work_authorization" label="Work Authorization Status">
                      {/* Canonical options from @/constants/candidateFields */}
                      <Select allowClear options={WORK_AUTHORIZATION_OPTIONS} />
                    </Form.Item>
                    <Form.Item name="visa_status" label="Visa Status">
                      <Input placeholder="Optional" />
                    </Form.Item>
                    <Form.Item name="pr_status" label="PR Status">
                      <Input placeholder="Optional" />
                    </Form.Item>
                  </div>
                </div>
                <div className="rounded-lg border border-slate-200 p-3">
                  <p className="mb-2 text-xs font-bold uppercase text-slate-500">Professional</p>
                  <div className="grid grid-cols-2 gap-3">
                    <Form.Item name="current_title" label="Current Title"><Input /></Form.Item>
                    <Form.Item name="current_company" label="Current Company"><Input /></Form.Item>
                    <Form.Item name="current_location_city" label="Current City"><Input /></Form.Item>
                    <Form.Item name="current_location_country" label="Current Country">
                      <Select
                        allowClear
                        showSearch
                        options={COUNTRIES.map((c) => ({ label: c.name, value: c.name }))}
                        optionFilterProp="label"
                      />
                    </Form.Item>
                    <Form.Item name="experience_years" label="Experience (Years)"><InputNumber min={0} className="w-full" /></Form.Item>
                    <Form.Item name="source" label="Source">
                      <Select options={SOURCE_OPTIONS} />
                    </Form.Item>
                    <Form.Item name="source_detail" label="Source Detail (optional)">
                      <Input placeholder="Sub-source / campaign / referrer" />
                    </Form.Item>
                    <Form.Item name="tags" label="Tags">
                      <Select mode="tags" options={TAG_OPTIONS.map((t) => ({ label: t, value: t }))} tokenSeparators={[',']} />
                    </Form.Item>
                    <Form.Item name="skills" label="Skills">
                      <Select
                        mode="tags"
                        showSearch
                        filterOption={false}
                        options={skillOptions}
                        tokenSeparators={[',']}
                        onSearch={(q) => {
                          if (q && q.length >= 2) {
                            skillSuggestMutation.mutate(q)
                          }
                        }}
                        placeholder="Type to search skills or add custom"
                      />
                    </Form.Item>
                    <Form.Item name="languages" label="Languages">
                      <Select
                        mode="tags"
                        options={LANGUAGE_OPTIONS.map((l) => ({ label: l, value: l }))}
                        tokenSeparators={[',']}
                      />
                    </Form.Item>
                  </div>
                </div>
                <div className="rounded-lg border border-slate-200 p-3">
                  <p className="mb-2 text-xs font-bold uppercase text-slate-500">Compensation & Availability</p>
                  <div className="grid grid-cols-2 gap-3">
                    <Form.Item
                      name="expected_salary_min"
                      label={`Expected Salary Min (${salaryConfig.symbol}${salaryConfig.unit})`}
                    >
                      <InputNumber className="w-full" min={0} placeholder={salaryConfig.placeholder} />
                    </Form.Item>
                    <Form.Item
                      name="expected_salary_max"
                      label={`Expected Salary Max (${salaryConfig.symbol}${salaryConfig.unit})`}
                    >
                      <InputNumber className="w-full" min={0} placeholder={salaryConfig.placeholder} />
                    </Form.Item>
                    <Form.Item name="salary_currency" label="Salary Currency">
                      <Select options={CURRENCIES.map((c) => ({ value: c.code, label: `${c.code} (${c.symbol})` }))} />
                    </Form.Item>
                    <Form.Item name="notice_period_applicable" label="Notice Period Applicable">
                      <Select
                        options={[
                          { value: true, label: 'Yes' },
                          { value: false, label: 'No' },
                        ]}
                      />
                    </Form.Item>
                    {noticePeriodApplicable && (
                      <>
                        <Form.Item name="notice_period_days" label="Notice Period Days">
                          <InputNumber min={0} className="w-full" />
                        </Form.Item>
                        <Form.Item
                          name="last_working_day"
                          label="Last Working Day"
                          rules={[{ required: true, message: 'Last working day is required when notice period applies' }]}
                        >
                          <Input placeholder="YYYY-MM-DD" />
                        </Form.Item>
                      </>
                    )}
                    <Form.Item name="availability_date" label="Availability Date"><Input placeholder="YYYY-MM-DD" /></Form.Item>
                    <Form.Item name="is_actively_looking" label="Actively Looking">
                      <Select
                        options={[
                          { value: true, label: 'Yes' },
                          { value: false, label: 'No' },
                        ]}
                      />
                    </Form.Item>
                    <Form.Item name="offer_in_hand" label="Offer In Hand">
                      <Select
                        options={[
                          { value: true, label: 'Yes' },
                          { value: false, label: 'No' },
                        ]}
                      />
                    </Form.Item>
                    {offerInHand && (
                      <>
                        <Form.Item name="offer_in_hand_amount" label={`Offer Amount (${salaryConfig.symbol}${salaryConfig.unit})`}>
                          <InputNumber min={0} className="w-full" />
                        </Form.Item>
                        <Form.Item name="offer_currency" label="Offer Currency">
                          <Select options={CURRENCIES.map((c) => ({ value: c.code, label: `${c.code} (${c.symbol})` }))} />
                        </Form.Item>
                      </>
                    )}
                  </div>
                </div>
                <div className="rounded-lg border border-slate-200 p-3">
                  <p className="mb-2 text-xs font-bold uppercase text-slate-500">Documents</p>
                  <div className="grid grid-cols-2 gap-3">
                    <Form.Item name="resume_url" label="Resume URL"><Input placeholder="https://..." /></Form.Item>
                  </div>
                </div>
                <div className="rounded-lg border border-slate-200 p-3">
                  <p className="mb-2 text-xs font-bold uppercase text-slate-500">Notes / Internal Context</p>
                  <div className="grid grid-cols-2 gap-3">
                    <Form.Item name="assigned_to" label="Assign To">
                      <Select
                        allowClear
                        showSearch
                        options={assignableUserOptions}
                        optionFilterProp="label"
                        placeholder={assignableUserOptions.length ? 'Select recruiter' : 'No users found'}
                      />
                    </Form.Item>
                    <Form.Item name="owner_user_id" label="Owner">
                      <Select
                        allowClear
                        showSearch
                        options={assignableUserOptions}
                        optionFilterProp="label"
                        placeholder={assignableUserOptions.length ? 'Select owner' : 'No users found'}
                      />
                    </Form.Item>
                  </div>
                  <Form.Item name="notes" label="Internal Notes"><Input.TextArea rows={3} /></Form.Item>
                </div>
              </div>
            )}

            {method === 'invite_candidate' && (
              <div className="space-y-3">
                <Alert type="info" showIcon message="Generate invite link, then copy or send for candidate self-service profile completion." />
                <div className="grid grid-cols-2 gap-3">
                  <Form.Item name="invite_expires_days" label="Expiry (days)">
                    <InputNumber min={1} max={90} className="w-full" />
                  </Form.Item>
                  <Form.Item name="invite_max_uses" label="Max Uses">
                    <InputNumber min={1} max={100} className="w-full" />
                  </Form.Item>
                </div>
                <Form.Item name="invite_message" label="Optional Message">
                  <Input.TextArea rows={3} placeholder="Add a short message for candidate outreach" />
                </Form.Item>
                {generatedInviteLink && (
                  <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3">
                    <div className="flex items-center gap-2 text-emerald-700">
                      <CheckCircle2 size={14} />
                      <Text strong>Invite link generated</Text>
                    </div>
                    <p className="mt-1 break-all text-xs text-slate-700">{generatedInviteLink}</p>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(generatedInviteLink)
                        message.success('Invite link copied')
                      }}
                      className="mt-2 inline-flex items-center gap-1 rounded-md border border-emerald-300 bg-white px-2.5 py-1 text-xs font-semibold text-emerald-700 hover:bg-emerald-100"
                    >
                      <Copy size={12} />
                      Copy Link
                    </button>
                  </div>
                )}
              </div>
            )}

            {(method === 'upload_resume' || method === 'import_passport' || method === 'agency_submit') && (
              <Alert type="warning" showIcon message="This method is coming soon and currently disabled." />
            )}
          </Form>
        )}

        {!isEditMode && step === 2 && (
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs font-bold uppercase text-slate-500">What Happens Next?</p>
            <div className="mt-2 space-y-1.5">
              {availableActions.map((a) => (
                <label key={a} className="flex cursor-pointer items-center gap-2 rounded-md border border-transparent px-2 py-1 hover:bg-white">
                  <input
                    type="radio"
                    name="next_action"
                    value={a}
                    checked={nextAction === a}
                    onChange={() => setNextAction(a)}
                  />
                  <span className="text-sm text-slate-700">{ACTION_LABELS[a]}</span>
                </label>
              ))}
            </div>
            {method === 'invite_candidate' && (
              <p className="mt-2 text-xs text-slate-500">
                Invite Link flow prioritizes generating and sharing link for candidate self-service.
              </p>
            )}
          </div>
        )}
      </div>
    </Modal>
  )
}
