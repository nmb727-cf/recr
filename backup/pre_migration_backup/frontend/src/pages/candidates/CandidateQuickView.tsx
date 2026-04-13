import React, { useState, useEffect } from 'react'
import {
  Button, Tag, Typography, Avatar,
  Spin, Empty, message, Form, Tabs, Row, Col, DatePicker, InputNumber, Select, Input, Divider, Checkbox
} from 'antd'
import {
  Mail, Phone, MapPin, Briefcase, Clock,
  ArrowRight, FileText, ExternalLink,
  TrendingUp, Calendar, Layers, X, Edit, Plus, ShieldCheck
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
import PhoneInput, { formatPhoneDisplay, getPhoneValidationRule, PhoneValue } from '@/components/common/PhoneInput'
import AddToActiveModal from './AddToActiveModal'
import AddCandidateWorkflowModal from '@/components/candidates/AddCandidateWorkflowModal'

dayjs.extend(relativeTime)

const { Text } = Typography

function formatProtectionDate(value?: string | null, format = 'DD MMM YYYY') {
  if (!value) return 'Agreement release'
  const parsed = dayjs(value)
  return parsed.isValid() ? parsed.format(format) : value
}

function protectionScopeLabel(scope?: string | null) {
  if (!scope) return 'Not Protected'
  if (scope === 'job_only') return 'Job Only'
  if (scope === 'view_only') return 'View Only'
  if (scope === 'limited_company_access') return 'Limited Company Access'
  return scope.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
}

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
  const [activeModalOpen, setActiveModalOpen] = useState(false)
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
  
  // Step 1 — Check what the API returns
  console.log('[CandidateQuickView] Full response:', data);

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

  if (editMode && candidate) {
    return (
      <AddCandidateWorkflowModal
        open
        onClose={() => setEditMode(false)}
        sourceSurface="database"
        mode="edit"
        candidateId={candidateId}
        initialCandidate={candidate as any}
        onCompleted={() => {
          queryClient.invalidateQueries({ queryKey: ['candidate', 'quick', candidateId] })
          queryClient.invalidateQueries({ queryKey: ['candidate-list'] })
          setEditMode(false)
        }}
      />
    )
  }

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
                show: !!(candidate as any).is_agency_protected,
                color: '#7C3AED', bg: '#F5F3FF',
                label: (
                  <div className="flex items-center gap-1">
                    <ShieldCheck size={10} />
                    <span>AGENCY PROTECTED</span>
                    <span className="opacity-60 ml-1">
                      (Until {dayjs((candidate as any).protected_until).format('DD MMM')})
                    </span>
                  </div>
                )
              },
              {
                show: !!(candidate as any).is_agency_protected && !!(candidate as any).protection_scope,
                color: '#7C3AED', bg: '#F5F3FF',
                label: (candidate as any).protection_scope?.replace(/_/g, ' ')?.toUpperCase()
              },
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

          {candidate.is_agency_protected && (
            <div className="mt-3 rounded-xl border border-violet-200 bg-violet-50 px-3 py-3">
              <div className="flex items-start gap-2">
                <ShieldCheck size={14} className="mt-0.5 shrink-0 text-violet-600" />
                <div className="min-w-0">
                  <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-violet-700">Protection Status</p>
                  <div className="mt-2 space-y-1 text-[11px] text-slate-700">
                    <p><span className="font-semibold">Status:</span> Agency Protected</p>
                    <p><span className="font-semibold">Protected Until:</span> {formatProtectionDate(candidate.protected_until)}</p>
                    <p><span className="font-semibold">Scope:</span> {protectionScopeLabel(candidate.protection_scope)}</p>
                    <p className="text-slate-600">Candidate cannot be reused outside agreed scope during protection period.</p>
                  </div>
                </div>
              </div>
            </div>
          )}
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
            <DataPoint 
              label="Phone" 
              value={
                (candidate as any).phone_number
                  ? formatPhoneDisplay((candidate as any).phone_country_code || 'IN', (candidate as any).phone_number)
                  : candidate.phone || null
              } 
            />
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
          <Card title="Experience" color="bg-violet-400" fullWidth>
            <div className="grid grid-cols-2 divide-x divide-slate-50 -mx-3">
              <div className="px-3">
                <DataPoint
                  label="Total Exp"
                  value={expYears != null ? `${expYears} yrs` : null}
                />
                <DataPoint
                  label="Relevant"
                  value={relevantYears != null ? `${relevantYears} yrs` : null}
                />
                <DataPoint
                  label="Work Auth"
                  value={(candidate as any).work_authorization?.replace(/_/g, ' ') || null}
                />
                <DataPoint
                  label="Nationality"
                  value={(candidate as any).nationality || null}
                />
              </div>
              <div className="px-3">
                <DataPoint
                  label="Relocate"
                  value={
                    (candidate as any).relocation_willing ? (
                      <Tag 
                        color={(candidate as any).relocation_willing === 'yes' ? 'success' : (candidate as any).relocation_willing === 'maybe' ? 'processing' : 'default'}
                        className="m-0 uppercase font-bold text-[10px] rounded-md px-1.5 border-none"
                      >
                        {(candidate as any).relocation_willing}
                      </Tag>
                    ) : null
                  }
                />
                <DataPoint
                  label="Grad Year"
                  value={(candidate as any).graduation_year || (candidate as any).candidate_profile?.education?.[0]?.end_year || null}
                />
                <DataPoint
                  label="Highest Edu"
                  value={(candidate as any).highest_education?.replace(/_/g, ' ') || null}
                />
              </div>
            </div>
            
            {/* Education History */}
            {((candidate as any).candidate_profile?.education?.length > 0) && (
              <div className="pt-2 border-t border-slate-50 mt-1">
                <p className="text-[9px] uppercase font-bold tracking-widest text-slate-400 m-0 mb-1.5">Education History</p>
                <div className="space-y-2">
                  {[...(candidate as any).candidate_profile.education]
                    .sort((a, b) => (b.end_year || 0) - (a.end_year || 0))
                    .map((edu, idx) => (
                      <div key={idx} className="bg-slate-50/50 p-2 rounded-lg border border-slate-100">
                        <p className="text-[11px] font-bold text-slate-800 m-0 leading-tight">
                          {edu.degree}{edu.field_of_study ? `, ${edu.field_of_study}` : ''}
                        </p>
                        <p className="text-[10px] text-slate-500 m-0 mt-0.5 font-medium">
                          {edu.institution} {edu.end_year ? `(${edu.end_year})` : ''}
                        </p>
                      </div>
                    ))
                  }
                </div>
              </div>
            )}
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
          className="h-8 rounded-lg text-[11px] font-bold mb-1.5 shadow-md"
          style={{ background: '#4F46E5', color: 'white', border: 'none' }}
          icon={<Plus className="h-3.5 w-3.5" />}
          onClick={() => setActiveModalOpen(true)}
        >
          Add to Active Work
        </Button>

        <Button block size="small"
          className="h-7 rounded-lg text-[10px] font-bold"
          style={{ borderColor: '#4F46E5', color: '#4F46E5' }}
          onClick={onOpenFullView}>
          View Full Profile →
        </Button>
      </div>

      <AddToActiveModal 
        open={activeModalOpen}
        onClose={() => setActiveModalOpen(false)}
        preSelectedCandidate={candidate ? {
          id: candidate.id,
          full_name: candidate.full_name,
          current_title: candidate.current_title,
          email: candidate.email
        } : undefined}
      />
    </div>
  )
}
