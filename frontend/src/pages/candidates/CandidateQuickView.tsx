import React, { useState, useEffect } from 'react'
import {
  Button, Tag, Typography, Avatar,
  Spin, Empty, message, Form, Tabs, Row, Col, DatePicker, InputNumber, Select, Input, Divider, Checkbox
} from 'antd'
import {
  Mail, Phone, MapPin, Briefcase, Clock,
  ArrowRight, FileText, ExternalLink,
  TrendingUp, Calendar, Layers, X, Edit
} from 'lucide-react'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useQueryClient } from '@tanstack/react-query'
import { candidatesApi } from '@/api/candidates'
import { getSalaryConfig, formatSalaryDisplay } from '@/utils/salary'
import { organisationApi } from '@/api/organisation'
import { DEMO_ASSETS } from '@/utils/demo'
import type { CandidateDetail } from '@/types'

dayjs.extend(relativeTime)

const { Text } = Typography

interface CandidateQuickViewProps {
  candidateId: string
  onClose: () => void
  onOpenFullView: () => void
  onDocOpen?: (url: string) => void
  extraActions?: React.ReactNode
}

export default function CandidateQuickView({
  candidateId,
  onClose,
  onOpenFullView,
  onDocOpen,
  extraActions
}: CandidateQuickViewProps) {

  const [editMode, setEditMode] = useState(false)
  const [editForm] = Form.useForm()
  const [saving, setSaving] = useState(false)
  const [offerInHand, setOfferInHand] = useState(false)
  const queryClient = useQueryClient()

  useEffect(() => {
    const handler = (e: CustomEvent) => {
      if (e.detail.id === candidateId) {
        setEditMode(true)
      }
    }
    window.addEventListener('candidate-edit', handler as EventListener)
    return () => window.removeEventListener(
      'candidate-edit', handler as EventListener
    )
  }, [candidateId])

  const { data, isLoading } = useApiQuery(
    ['candidate', 'quick', candidateId],
    () => candidatesApi.get(candidateId)
  )

  const { data: notesData } = useApiQuery(
    ['candidate-notes-quick', candidateId],
    () => candidatesApi.listNotes(candidateId),
    { enabled: !!candidateId }
  )

  const { data: orgData } = useApiQuery(
    ['org_profile'],
    () => organisationApi.getProfile()
  )

  const candidate = (data as any)?.candidate as CandidateDetail
  const notes = (notesData as any)?.notes ?? []
  const lastNote = notes[0]

  const org = (orgData as any)?.organisation || (orgData as any) || {}
  const countryCode = org?.country_code || 'IN'
  const salaryConfig = getSalaryConfig(countryCode)

  const resumeUrl = candidate?.metadata?.resume_public_url || 
    DEMO_ASSETS.resume

  const handleResumeClick = () => {
    if (!resumeUrl) return
    if (onDocOpen) {
      onDocOpen(resumeUrl as string)
    } else {
      window.open(resumeUrl as string, '_blank')
    }
  }

  if (isLoading) return <div className="p-8 text-center"><Spin /></div>
  if (!candidate) return <Empty className="p-8" />

  const expYears = candidate.experience_years
    ? parseFloat(String(candidate.experience_years))
    : null
  const relevantYears = (candidate as any).relevant_experience_years
    ? parseFloat(String((candidate as any).relevant_experience_years))
    : null
  const currentCtc = (candidate as any).current_ctc
    ? parseFloat(String((candidate as any).current_ctc))
    : null
  const expectedCtc = candidate.expected_salary_min
    ? parseFloat(String(candidate.expected_salary_min))
    : null
  const counterOffer = (candidate as any).counter_offer
    ? parseFloat(String((candidate as any).counter_offer))
    : null

  // Format salary value
  const fmtSalary = (val: number | null) => {
    if (val === null) return '—'
    return `${salaryConfig.symbol}${val} ${salaryConfig.unit}`
  }

  if (editMode && candidate) {
    return (
      <div className="flex flex-col h-full bg-white">
        
        {/* Edit header */}
        <div className="flex items-center justify-between px-4 py-2.5
                        border-b border-slate-100 sticky top-0 
                        bg-white z-10 shrink-0">
          <Text className="font-bold text-slate-700 text-sm">
            Edit Candidate
          </Text>
          <Button
            type="text"
            size="small"
            icon={<X className="h-3.5 w-3.5" />}
            onClick={() => setEditMode(false)}
            className="h-7 w-7 rounded-lg"
          />
        </div>

        {/* Edit form — same 3 tabs as AddCandidateModal */}
        <div className="flex-1 overflow-y-auto px-4 py-3">
          <Form
            form={editForm}
            layout="vertical"
            initialValues={{
              first_name: candidate.first_name,
              last_name: candidate.last_name,
              email: candidate.email,
              phone: candidate.phone,
              whatsapp: candidate.whatsapp || '',
              linkedin_url: candidate.linkedin_url,
              current_title: candidate.current_title,
              current_company: candidate.current_company,
              current_location_city: candidate.current_location_city,
              experience_years: candidate.experience_years
                ? parseFloat(String(candidate.experience_years))
                : undefined,
              relevant_experience_years: 
                (candidate as any).relevant_experience_years
                  ? parseFloat(String(
                      (candidate as any).relevant_experience_years
                    ))
                  : undefined,
              skills: Array.isArray(candidate.skills) 
                ? candidate.skills : [],
              languages: Array.isArray(candidate.languages)
                ? candidate.languages : [],
              source: candidate.source,
              nationality: (candidate as any).nationality || '',
              work_authorization: 
                (candidate as any).work_authorization || 'not_specified',
              highest_education: 
                (candidate as any).highest_education || undefined,
              graduation_year: 
                (candidate as any).graduation_year || undefined,
              relocation_willing: 
                (candidate as any).relocation_willing || 'maybe',
              preferred_locations: 
                Array.isArray((candidate as any).preferred_locations)
                  ? (candidate as any).preferred_locations : [],
              current_ctc: (candidate as any).current_ctc
                ? parseFloat(String((candidate as any).current_ctc))
                : undefined,
              expected_salary_min: candidate.expected_salary_min
                ? parseFloat(String(candidate.expected_salary_min))
                : undefined,
              offer_in_hand: (candidate as any).offer_in_hand 
                ? 'yes' : 'no',
              offer_in_hand_amount: 
                (candidate as any).offer_in_hand_amount
                  ? parseFloat(
                      String((candidate as any).offer_in_hand_amount)
                    )
                  : undefined,
              counter_offer: (candidate as any).counter_offer
                ? parseFloat(String((candidate as any).counter_offer))
                : undefined,
              notice_period_days: candidate.notice_period_days,
              availability_status: 
                (candidate as any).availability_status || undefined,
              work_mode_preference: 
                (candidate as any).work_mode_preference || 'any',
              last_working_day: (candidate as any).last_working_day
                ? dayjs((candidate as any).last_working_day)
                : undefined,
              availability_date: candidate.availability_date
                ? dayjs(candidate.availability_date)
                : undefined,
              resume_url: (candidate as any).resume_url ||
                candidate.metadata?.resume_public_url || '',
              portfolio_url: (candidate as any).portfolio_url || '',
              github_url: (candidate as any).github_url || '',
              recruiter_rating: 
                (candidate as any).recruiter_rating || undefined,
              do_not_contact: 
                (candidate as any).do_not_contact || false,
              notes: '',
            }}
          >
            <Tabs
              size="small"
              items={[
                {
                  key: 'basic',
                  label: 'Basic Info',
                  forceRender: true,
                  children: (
                    <div className="space-y-0 pt-2">
                      <Row gutter={12}>
                        <Col span={12}>
                          <Form.Item name="first_name" label="First Name"
                            rules={[{ required: true }]}>
                            <Input size="small" />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item name="last_name" label="Last Name"
                            rules={[{ required: true }]}>
                            <Input size="small" />
                          </Form.Item>
                        </Col>
                      </Row>
                      <Form.Item name="email" label="Email"
                        rules={[{ type: 'email' }]}>
                        <Input size="small" type="email" />
                      </Form.Item>
                      <Row gutter={12}>
                        <Col span={12}>
                          <Form.Item name="phone" label="Phone">
                            <Input size="small" />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item name="whatsapp" label="WhatsApp">
                            <Input size="small" />
                          </Form.Item>
                        </Col>
                      </Row>
                      <Form.Item name="current_title" label="Current Title">
                        <Input size="small" />
                      </Form.Item>
                      <Form.Item name="current_company" 
                                 label="Current Company">
                        <Input size="small" />
                      </Form.Item>
                      <Form.Item name="current_location_city" 
                                 label="Location">
                        <Input size="small" />
                      </Form.Item>
                      <Row gutter={12}>
                        <Col span={12}>
                          <Form.Item name="experience_years" 
                                     label="Total Exp (Yrs)">
                            <InputNumber 
                              size="small" min={0} step={0.5} 
                              className="w-full" />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item name="relevant_experience_years"
                                     label="Relevant Exp (Yrs)">
                            <InputNumber 
                              size="small" min={0} step={0.5}
                              className="w-full" />
                          </Form.Item>
                        </Col>
                      </Row>
                      <Form.Item name="skills" label="Skills">
                        <Select
                          mode="tags"
                          size="small"
                          placeholder="Add skills..."
                          tokenSeparators={[',']}
                        />
                      </Form.Item>
                      <Form.Item name="languages" label="Languages">
                        <Select mode="tags" size="small"
                          placeholder="Add languages..."
                          options={[
                            'English','Hindi','Tamil','Telugu','Kannada',
                            'Marathi','Bengali','Gujarati','Punjabi',
                            'Malayalam','Arabic','French','German',
                            'Spanish','Mandarin'
                          ].map(l => ({ value: l, label: l }))}
                          tokenSeparators={[',']}
                        />
                      </Form.Item>

                      <Row gutter={12}>
                        <Col span={12}>
                          <Form.Item name="nationality" label="Nationality">
                            <Input size="small" placeholder="e.g. Indian" />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item name="work_authorization"
                                     label="Work Auth">
                            <Select size="small" options={[
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

                      <Row gutter={12}>
                        <Col span={12}>
                          <Form.Item name="highest_education"
                                     label="Education">
                            <Select size="small" options={[
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
                                     label="Grad Year">
                            <InputNumber size="small" min={1970} max={2030}
                              placeholder="2020" className="w-full" />
                          </Form.Item>
                        </Col>
                      </Row>

                      <Row gutter={12}>
                        <Col span={12}>
                          <Form.Item name="relocation_willing"
                                     label="Relocate">
                            <Select size="small" options={[
                              { value: 'yes', label: 'Yes' },
                              { value: 'no', label: 'No' },
                              { value: 'maybe', label: 'Maybe' },
                            ]} />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item name="preferred_locations"
                                     label="Preferred Cities">
                            <Select size="small" mode="tags"
                              placeholder="Add cities..."
                              tokenSeparators={[',']} />
                          </Form.Item>
                        </Col>
                      </Row>
                      <Form.Item name="source" label="Source">
                        <Select size="small" options={[
                          { value: 'company', label: 'Direct' },
                          { value: 'linkedin', label: 'LinkedIn' },
                          { value: 'referral', label: 'Referral' },
                          { value: 'job_board', label: 'Job Board' },
                          { value: 'agency', label: 'Agency' },
                        ]} />
                      </Form.Item>
                    </div>
                  ),
                },
                {
                  key: 'compensation',
                  label: 'Compensation',
                  forceRender: true,
                  children: (
                    <div className="pt-2">
                      <Row gutter={12}>
                        <Col span={12}>
                          <Form.Item name="current_ctc"
                            label={`Current (${salaryConfig.unit})`}>
                            <InputNumber size="small" min={0}
                              className="w-full"
                              placeholder={salaryConfig.placeholder} />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item name="expected_salary_min"
                            label={`Expected (${salaryConfig.unit})`}>
                            <InputNumber size="small" min={0}
                              className="w-full"
                              placeholder={salaryConfig.placeholder} />
                          </Form.Item>
                        </Col>
                      </Row>
                      <Row gutter={12}>
                        <Col span={12}>
                          <Form.Item name="offer_in_hand"
                                     label="Offer in Hand?">
                            <Select size="small" options={[
                              { value: 'no', label: 'No' },
                              { value: 'yes', label: 'Yes' },
                            ]} onChange={(v) => setOfferInHand(v === 'yes')} />
                          </Form.Item>
                        </Col>
                        {offerInHand && (
                          <Col span={12}>
                            <Form.Item name="offer_in_hand_amount"
                                       label="Offer Amount">
                              <InputNumber size="small" min={0}
                                className="w-full" />
                            </Form.Item>
                          </Col>
                        )}
                      </Row>
                      <Row gutter={12}>
                        <Col span={12}>
                          <Form.Item name="counter_offer"
                                     label="Counter Offer">
                            <InputNumber size="small" min={0}
                              className="w-full" />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item name="notice_period_days"
                                     label="Notice Period">
                            <Select size="small" options={[
                              { value: 0, label: 'Immediate' },
                              { value: 15, label: '15 days' },
                              { value: 30, label: '30 days' },
                              { value: 45, label: '45 days' },
                              { value: 60, label: '60 days' },
                              { value: 90, label: '90 days' },
                            ]} />
                          </Form.Item>
                        </Col>
                      </Row>
                      <Row gutter={12}>
                        <Col span={12}>
                          <Form.Item name="availability_status"
                                     label="Availability">
                            <Select size="small" options={[
                              { value: 'available_now', 
                                label: 'Available Now' },
                              { value: 'notice_period', 
                                label: 'Serving Notice' },
                              { value: 'open_to_offers', 
                                label: 'Open to Offers' },
                              { value: 'not_looking', 
                                label: 'Not Looking' },
                            ]} />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item name="work_mode_preference"
                                     label="Work Mode">
                            <Select size="small" options={[
                              { value: 'any', label: 'Any' },
                              { value: 'remote', label: 'Remote' },
                              { value: 'hybrid', label: 'Hybrid' },
                              { value: 'onsite', label: 'On-site' },
                            ]} />
                          </Form.Item>
                        </Col>
                      </Row>
                      <Row gutter={12}>
                        <Col span={12}>
                          <Form.Item name="last_working_day"
                                     label="Last Working Day">
                            <DatePicker size="small" 
                              className="w-full" />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item name="availability_date"
                                     label="Available From">
                            <DatePicker size="small"
                              className="w-full" />
                          </Form.Item>
                        </Col>
                      </Row>
                    </div>
                  ),
                },
                {
                  key: 'documents',
                  label: 'Documents',
                  forceRender: true,
                  children: (
                    <div className="pt-2">
                      <Form.Item name="resume_url" label="Resume URL">
                        <Input size="small"
                          placeholder="https://drive.google.com/..." />
                      </Form.Item>
                      <Row gutter={12}>
                        <Col span={12}>
                          <Form.Item name="portfolio_url" label="Portfolio URL">
                            <Input size="small"
                              placeholder="https://portfolio.com" />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item name="github_url" label="GitHub URL">
                            <Input size="small"
                              placeholder="https://github.com/username" />
                          </Form.Item>
                        </Col>
                      </Row>

                      <Form.Item name="recruiter_rating" label="Rating">
                        <Select size="small" options={[
                          { value: 1, label: '★ Poor' },
                          { value: 2, label: '★★ Below Average' },
                          { value: 3, label: '★★★ Average' },
                          { value: 4, label: '★★★★ Good' },
                          { value: 5, label: '★★★★★ Excellent' },
                        ]} />
                      </Form.Item>

                      <Form.Item name="do_not_contact"
                                 valuePropName="checked">
                        <Checkbox>Do not contact</Checkbox>
                      </Form.Item>
                      <Form.Item name="notes" label="Add Note">
                        <Input.TextArea rows={4}
                          placeholder="Add a recruiter note..." />
                      </Form.Item>
                    </div>
                  ),
                },
              ]}
            />
          </Form>
        </div>

        {/* Save / Cancel */}
        <div className="px-4 py-3 border-t border-slate-100 shrink-0">
          <Row gutter={8}>
            <Col span={12}>
              <Button block size="small" className="h-8 rounded-lg"
                onClick={() => {
                  setEditMode(false)
                  editForm.resetFields()
                }}>
                Cancel
              </Button>
            </Col>
            <Col span={12}>
              <Button
                block
                size="small"
                type="primary"
                loading={saving}
                className="h-8 rounded-lg"
                style={{ background: '#4F46E5' }}
                onClick={async () => {
                  try {
                    const values = await editForm.validateFields()
                    setSaving(true)
                    await candidatesApi.update(candidateId, {
                      first_name: values.first_name,
                      last_name: values.last_name,
                      email: values.email,
                      phone: values.phone,
                      whatsapp: values.whatsapp || '',
                      linkedin_url: values.linkedin_url || '',
                      current_title: values.current_title || '',
                      current_company: values.current_company || '',
                      current_location_city: 
                        values.current_location_city || '',
                      experience_years: values.experience_years,
                      relevant_experience_years:
                        values.relevant_experience_years,
                      skills: Array.isArray(values.skills)
                        ? values.skills : [],
                      languages: values.languages || [],
                      nationality: values.nationality || '',
                      work_authorization: values.work_authorization || '',
                      highest_education: values.highest_education || '',
                      graduation_year: values.graduation_year || null,
                      relocation_willing: values.relocation_willing || '',
                      preferred_locations: values.preferred_locations || [],
                      source: values.source,
                      current_ctc: values.current_ctc,
                      expected_salary_min: values.expected_salary_min,
                      offer_in_hand: values.offer_in_hand === 'yes',
                      offer_in_hand_amount: values.offer_in_hand === 'yes'
                        ? values.offer_in_hand_amount : null,
                      counter_offer: values.counter_offer,
                      notice_period_days: values.notice_period_days,
                      availability_status: values.availability_status,
                      work_mode_preference: values.work_mode_preference,
                      last_working_day: values.last_working_day
                        ? values.last_working_day.format('YYYY-MM-DD')
                        : null,
                      availability_date: values.availability_date
                        ? values.availability_date.format('YYYY-MM-DD')
                        : null,
                      resume_url: values.resume_url || '',
                      portfolio_url: values.portfolio_url || '',
                      github_url: values.github_url || '',
                      recruiter_rating: values.recruiter_rating || null,
                      do_not_contact: values.do_not_contact || false,
                      metadata: values.resume_url
                        ? { resume_public_url: values.resume_url }
                        : candidate.metadata || {},
                    })
                    // Add note if provided
                    if (values.notes?.trim()) {
                      await candidatesApi.addNote(candidateId, {
                        note_text: values.notes.trim(),
                        note_type: 'general',
                      }).catch(() => {})
                    }

                    message.success('Candidate updated')
                    queryClient.invalidateQueries({ 
                      queryKey: ['candidate', 'quick', candidateId] 
                    })
                    queryClient.invalidateQueries({ 
                      queryKey: ['candidates'] 
                    })
                    setEditMode(false)
                  } catch (err: any) {
                    console.error('[EditCandidate] error:', err)
                    message.error(
                      err?.response?.data?.message || 'Failed to update'
                    )
                  } finally {
                    setSaving(false)
                  }
                }}
              >
                Save Changes
              </Button>
            </Col>
          </Row>
        </div>

      </div>
    )
  }

  const avatarColors = [
    'bg-violet-500', 'bg-blue-500', 'bg-emerald-500',
    'bg-orange-500', 'bg-rose-500', 'bg-cyan-500'
  ]
  const colorIndex = (candidate.first_name?.charCodeAt(0) || 0) % 6
  const avatarColor = avatarColors[colorIndex]

  // Reusable mini card for a single data point
  const DataPoint = ({
    label,
    value,
    highlight
  }: {
    label: string
    value: React.ReactNode
    highlight?: boolean
  }) => (
    <div className="py-1.5">
      <p className="text-[9px] uppercase font-bold tracking-widest text-slate-400 m-0 mb-0.5">
        {label}
      </p>
      <p className={`text-[12px] font-bold m-0 ${
        highlight ? 'text-indigo-600' : 'text-slate-800'
      }`}>
        {value || <span className="text-slate-300 font-normal">—</span>}
      </p>
    </div>
  )

  // Section card wrapper
  const Card = ({
    title,
    color,
    children,
    fullWidth,
    extra
  }: {
    title: string
    color: string
    children: React.ReactNode
    fullWidth?: boolean
    extra?: React.ReactNode
  }) => (
    <div className={`bg-white rounded-xl border border-slate-100 overflow-hidden ${fullWidth ? 'col-span-2' : ''}`}>
      <div className="px-3 py-1.5 border-b border-slate-50 flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <div className={`h-1.5 w-1.5 rounded-full ${color}`} />
          <span className="text-[9px] font-black uppercase tracking-widest text-slate-400">
            {title}
          </span>
        </div>
        {extra}
      </div>
      <div className="px-3 py-2 divide-y divide-slate-50">
        {children}
      </div>
    </div>
  )

  return (
    <div className="flex flex-col h-full" 
         style={{ background: '#F8F9FB' }}>

      {/* Top bar */}
      <div className="flex items-center justify-between px-4 py-2
                      bg-white border-b border-slate-100 
                      sticky top-0 z-10 shrink-0">
        <span className="text-[10px] font-black uppercase 
                         text-slate-400">
          Profile
        </span>
        <Button type="text" size="small"
          icon={<X className="h-3.5 w-3.5 text-slate-400" />}
          onClick={onClose}
          className="h-6 w-6 flex items-center justify-center" />
      </div>

      <div className="flex-1 overflow-y-auto">

        {/* ── Hero ───────────────────────────────── */}
        <div className="bg-white px-4 pt-4 pb-3 
                        border-b border-slate-100 mb-2">
          <div className="flex items-center gap-3">
            <div className={`h-11 w-11 rounded-xl ${avatarColor} 
                            flex items-center justify-center 
                            shrink-0 shadow-sm`}>
              <span className="text-white font-bold text-sm">
                {candidate.first_name?.charAt(0)?.toUpperCase()}
                {candidate.last_name?.charAt(0)?.toUpperCase()}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-[14px] font-bold text-slate-900 
                             m-0 truncate">
                {candidate.full_name || '—'}
              </h3>
              <p className="text-[11px] text-slate-400 m-0 truncate">
                {[
                  candidate.current_title,
                  candidate.current_company,
                  candidate.current_location_city
                ].filter(Boolean).join(' · ') || '—'}
              </p>
            </div>
          </div>

          {/* Tags */}
          <div className="flex flex-wrap gap-1 mt-2.5">
            {[
              {
                show: true,
                color: (candidate as any).profile_status === 'complete' 
                  || (candidate as any).profile_status === 'claimed'
                  ? '#10B981' : '#F59E0B',
                bg: (candidate as any).profile_status === 'complete'
                  || (candidate as any).profile_status === 'claimed'
                  ? '#ECFDF5' : '#FFFBEB',
                label: (
                  (candidate as any).profile_status || 'PARTIAL'
                ).toUpperCase()
              },
              {
                show: candidate.is_actively_looking,
                color: '#10B981', bg: '#ECFDF5',
                label: 'ACTIVE'
              },
              {
                show: (candidate as any).availability_status 
                  === 'available_now',
                color: '#3B82F6', bg: '#EFF6FF',
                label: 'AVAILABLE NOW'
              },
              {
                show: !!(candidate as any).offer_in_hand,
                color: '#8B5CF6', bg: '#F5F3FF',
                label: 'OFFER IN HAND'
              },
              {
                show: !!candidate.source,
                color: '#64748B', bg: '#F1F5F9',
                label: (candidate.source || '').toUpperCase()
              },
            ].filter(t => t.show).map((t, i) => (
              <span key={i}
                className="px-1.5 py-0.5 rounded text-[9px] 
                           font-bold tracking-wide border"
                style={{
                  color: t.color,
                  background: t.bg,
                  borderColor: t.color + '40'
                }}>
                {t.label}
              </span>
            ))}
          </div>
        </div>

        {/* ── Two column grid ─────────────────────── */}
        <div className="px-2 grid grid-cols-2 gap-2 mb-2">

          {/* Contact */}
          <Card title="Contact" color="bg-blue-400">
            <DataPoint label="Email" 
              value={
                candidate.email 
                  ? <span className="truncate block text-[11px]">
                      {candidate.email}
                    </span>
                  : null
              } 
            />
            <DataPoint label="Phone" value={candidate.phone} />
            <DataPoint label="Location"
              value={candidate.current_location_city} />
            {candidate.linkedin_url && (
              <DataPoint label="LinkedIn"
                value={
                  <a href={candidate.linkedin_url}
                     target="_blank" rel="noreferrer"
                     className="text-indigo-500 text-[11px] 
                                hover:underline">
                    View →
                  </a>
                }
              />
            )}
            <DataPoint
              label="Nationality"
              value={(candidate as any).nationality || null}
            />
            <DataPoint
              label="Work Auth"
              value={(candidate as any).work_authorization
                ?.replace(/_/g, ' ') || null}
            />
          </Card>

          {/* Compensation */}
          <Card title="Compensation" color="bg-indigo-400">
            <DataPoint
              label={`Current (${salaryConfig.unit})`}
              value={currentCtc !== null
                ? `${salaryConfig.symbol}${currentCtc}`
                : null}
            />
            <DataPoint
              label={`Expected (${salaryConfig.unit})`}
              value={expectedCtc !== null
                ? `${salaryConfig.symbol}${expectedCtc}`
                : null}
              highlight={expectedCtc !== null}
            />
            <DataPoint
              label="Counter"
              value={counterOffer !== null
                ? `${salaryConfig.symbol}${counterOffer}`
                : null}
            />
            <DataPoint
              label="Notice"
              value={candidate.notice_period_days != null
                ? candidate.notice_period_days === 0
                  ? 'Immediate'
                  : `${candidate.notice_period_days}d`
                : null}
            />
          </Card>

          {/* Availability */}
          <Card title="Availability" color="bg-emerald-400">
            <DataPoint
              label="Status"
              value={(candidate as any).availability_status
                ?.replace(/_/g, ' ') || null}
            />
            <DataPoint
              label="Work Mode"
              value={(candidate as any).work_mode_preference
                ?.replace(/_/g, ' ') || null}
            />
            <DataPoint
              label="Available"
              value={candidate.availability_date
                ? dayjs(candidate.availability_date)
                    .format('DD MMM YY')
                : null}
            />
            <DataPoint
              label="Last Day"
              value={(candidate as any).last_working_day
                ? dayjs((candidate as any).last_working_day)
                    .format('DD MMM YY')
                : null}
            />
          </Card>

          {/* Experience */}
          <Card title="Experience" color="bg-violet-400">
            <DataPoint
              label="Total Exp"
              value={expYears != null
                ? `${expYears} yrs` : null}
            />
            <DataPoint
              label="Relevant"
              value={relevantYears != null
                ? `${relevantYears} yrs` : null}
            />
            <DataPoint
              label="Education"
              value={(candidate as any).highest_education
                ?.replace(/_/g, ' ') || null}
            />
            <DataPoint
              label="Grad Year"
              value={(candidate as any).graduation_year
                ? String((candidate as any).graduation_year)
                : null}
            />
            <DataPoint
              label="Relocate"
              value={(candidate as any).relocation_willing
                ?.replace(/_/g, ' ') || null}
            />
          </Card>

        </div>

        {/* ── Skills (full width) ─────────────────── */}
        <div className="px-2 mb-2">
          <Card title="Skills" color="bg-pink-400">
            <div className="flex flex-wrap gap-1.5 py-1">
              {candidate.skills?.length > 0
                ? candidate.skills.map((skill: string) => (
                    <span key={skill}
                      className="px-2 py-0.5 rounded-md text-[10px] 
                                 font-bold bg-violet-50 text-violet-700 
                                 border border-violet-100">
                      {skill}
                    </span>
                  ))
                : <span className="text-[11px] text-slate-300">
                    No skills added
                  </span>
              }
            </div>
            {(candidate as any).languages?.length > 0 && (
              <div className="flex flex-wrap gap-1 pt-2 
                              border-t border-slate-50 mt-1">
                {(candidate as any).languages.map((lang: string) => (
                  <span key={lang}
                    className="px-2 py-0.5 rounded-md text-[10px] 
                               font-bold bg-slate-100 text-slate-500 
                               border border-slate-200">
                    {lang}
                  </span>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* ── Documents (full width) ──────────────── */}
        <div className="px-2 mb-2">
          <Card title="Documents" color="bg-rose-400">
            <div className="flex items-center justify-between py-1">
              <div className="flex items-center gap-2">
                <div className="h-7 w-7 bg-rose-50 rounded-lg flex 
                               items-center justify-center">
                  <FileText className="h-3.5 w-3.5 text-rose-400" />
                </div>
                <div>
                  <p className="text-[11px] font-bold text-slate-700 
                                 m-0">
                    {candidate?.metadata?.resume_public_url
                      ? 'Resume' : 'Sample (Demo)'}
                  </p>
                  <p className="text-[9px] text-slate-400 m-0">PDF</p>
                </div>
              </div>
              <Button size="small" type="text"
                className="h-6 px-2 text-[10px] font-bold rounded-lg 
                           bg-slate-100 hover:bg-slate-200 text-slate-600"
                onClick={handleResumeClick}>
                View
              </Button>
            </div>
            {(candidate as any).portfolio_url && (
              <div className="flex items-center justify-between 
                              py-1.5 border-t border-slate-50">
                <span className="text-[10px] text-slate-400 font-medium">
                  Portfolio
                </span>
                <a href={(candidate as any).portfolio_url}
                   target="_blank" rel="noreferrer"
                   className="text-[10px] text-indigo-500 font-bold 
                              hover:underline">
                  View →
                </a>
              </div>
            )}
            {(candidate as any).github_url && (
              <div className="flex items-center justify-between 
                              py-1.5 border-t border-slate-50">
                <span className="text-[10px] text-slate-400 font-medium">
                  GitHub
                </span>
                <a href={(candidate as any).github_url}
                   target="_blank" rel="noreferrer"
                   className="text-[10px] text-indigo-500 font-bold 
                              hover:underline">
                  View →
                </a>
              </div>
            )}
          </Card>
        </div>

        {/* ── Notes (full width) ──────────────────── */}
        <div className="px-2 mb-3">
          <Card 
            title="Latest Note" 
            color="bg-amber-400"
            extra={(candidate as any).recruiter_rating && (
              <div className="flex items-center gap-0.5">
                {Array.from({ length: 5 }).map((_, i) => (
                  <span key={i} className={`text-[10px] ${
                    i < (candidate as any).recruiter_rating
                      ? 'text-amber-400' : 'text-slate-200'
                  }`}>★</span>
                ))}
              </div>
            )}
          >
            <div className="py-1">
              {lastNote ? (
                <>
                  <p className="text-[11px] text-slate-600 
                                 leading-relaxed m-0">
                    {lastNote.note_text}
                  </p>
                  <p className="text-[9px] text-slate-400 font-bold 
                                 uppercase mt-1 m-0">
                    {lastNote.note_type} · {' '}
                    {dayjs(lastNote.created_at).fromNow()}
                  </p>
                </>
              ) : (
                <p className="text-[11px] text-slate-300 m-0 
                               text-center py-1">
                  No notes yet
                </p>
              )}
            </div>
          </Card>
        </div>

        {extraActions && (
          <div className="px-2 mb-3">{extraActions}</div>
        )}

      </div>

      {/* ── Footer actions ──────────────────────── */}
      <div className="bg-white border-t border-slate-100 
                      px-3 py-2.5 shrink-0">
        <div className="grid grid-cols-4 gap-1.5 mb-1.5">
          <Button size="small"
            className="h-7 font-bold rounded-lg text-[10px] 
                       flex items-center justify-center gap-1"
            style={{
              background: '#0F172A',
              borderColor: '#0F172A',
              color: 'white'
            }}
            icon={<Edit className="h-3 w-3" />}
            onClick={() => setEditMode(true)}>
            Edit
          </Button>
          <Button size="small"
            className="h-7 font-bold rounded-lg text-[10px] 
                       flex items-center justify-center gap-1
                       border-slate-200 text-slate-600">
            <Mail className="h-3 w-3" /> Email
          </Button>
          <Button size="small"
            className="h-7 font-bold rounded-lg text-[10px] 
                       flex items-center justify-center gap-1
                       border-slate-200 text-slate-600">
            <Calendar className="h-3 w-3" /> Schedule
          </Button>
          <Button size="small"
            className="h-7 font-bold rounded-lg text-[10px] 
                       flex items-center justify-center gap-1
                       border-slate-200 text-slate-600">
            <FileText className="h-3 w-3" /> Offer
          </Button>
        </div>
        <Button block size="small"
          className="h-7 rounded-lg text-[10px] font-bold"
          style={{ borderColor: '#4F46E5', color: '#4F46E5' }}
          onClick={onOpenFullView}>
          View Full Profile →
        </Button>
      </div>

    </div>
  )
}
