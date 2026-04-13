import React, { useState } from 'react'
import { Link, useParams, useSearchParams, useNavigate } from 'react-router-dom'
import { Card, Space, Tag, Typography, Spin, Divider, Progress, Tooltip, Button, Alert } from 'antd'
import { useApiQuery } from '@/hooks/useApiQuery'
import { hdcApi } from '@/api/hdc'
import { ExternalLink, Briefcase, User, Info, ShieldCheck, CheckCircle2 } from 'lucide-react'

import DecisionDashboard from './sections/DecisionDashboard'
import HiringCommittee from './sections/HiringCommittee'
import CandidateComparison from './sections/CandidateComparison'
import DecisionApproval from './sections/DecisionApproval'
import OfferIntelligence from './sections/OfferIntelligence'
import Compensation from './sections/Compensation'
import Negotiation from './sections/Negotiation'
import OfferRelease from './sections/OfferRelease'
import OfferAcceptance from './sections/OfferAcceptance'
import JoiningTracking from './sections/JoiningTracking'

const { Title, Text } = Typography

const sections = [
  { key: 'overview', label: 'Decisions', tooltip: 'View all active hiring decisions', component: DecisionDashboard },
  { key: 'committee', label: 'Committees', tooltip: 'Involve multiple stakeholders in the final hiring choice', component: HiringCommittee },
  { key: 'comparison', label: 'Compare Candidates', tooltip: 'Side-by-side analysis of finalists', component: CandidateComparison },
  { key: 'approvals', label: 'Approvals', tooltip: 'Final executive sign-off for offers', component: DecisionApproval },
  { key: 'offer-intelligence', label: 'Offer Modeling', tooltip: 'Plan and compare compensation scenarios', component: OfferIntelligence },
  { key: 'compensation', label: 'Comp Details', tooltip: 'Detailed breakdown of salary and benefits', component: Compensation },
  { key: 'negotiation', label: 'Negotiations', tooltip: 'Track counter-offers and candidate requests', component: Negotiation },
  { key: 'offer-release', label: 'Offer Release', tooltip: 'Prepare and send the formal offer packet', component: OfferRelease },
  { key: 'offer-acceptance', label: 'Acceptance', tooltip: 'Track candidate response and acceptance', component: OfferAcceptance },
  { key: 'joining', label: 'Joining', tooltip: 'Track the candidate from acceptance to first day', component: JoiningTracking },
] as const

export default function HiringDecisionWorkspace() {
  const { section } = useParams<{ section?: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const applicationId = searchParams.get('applicationId')
  const [showWelcome, setShowWelcome] = useState(!localStorage.getItem('hdc_onboarding_seen'))

  const activeSectionKey = section || 'overview'
  const activeSection = sections.find(s => s.key === activeSectionKey) || sections[0]
  const ActiveComponent = activeSection.component

  const handleDismissWelcome = () => {
    localStorage.setItem('hdc_onboarding_seen', 'true')
    setShowWelcome(false)
  }

  // ─── Application Context Query ───
  const { data: appStatus, isLoading: loadingStatus } = useApiQuery(
    ['hdc-application-status', applicationId],
    () => hdcApi.getApplicationStatus(applicationId!),
    { enabled: !!applicationId }
  )

  const hdcData = (appStatus as any)?.data

  const handleClearSelection = () => {
    const params = new URLSearchParams(searchParams)
    params.delete('applicationId')
    navigate({ search: params.toString() })
  }

  return (
    <div className="space-y-6 pb-20 px-6">
      {showWelcome && (
        <Card className="mx-auto mt-6 max-w-[1500px] rounded-3xl border-none bg-indigo-600 text-white shadow-xl animate-in fade-in slide-in-from-top-4 duration-700">
          <div className="flex items-center justify-between p-2">
            <div className="flex items-center gap-6">
              <div className="h-12 w-12 rounded-2xl bg-white/20 flex items-center justify-center">
                <CheckCircle2 size={24} className="text-white" />
              </div>
              <div>
                <Title level={4} className="!text-white !m-0 font-black uppercase tracking-tight">Welcome to the Hiring Decision Center</Title>
                <Text className="text-white/80 text-xs">Manage the final hiring lifecycle from committee voting to candidate joining.</Text>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <Button ghost size="small" className="border-white/40 text-white hover:border-white text-[10px] font-bold uppercase" onClick={() => window.open('/docs/user/hdc_guide', '_blank')}>View Guide</Button>
              <Button type="text" className="text-white/60 hover:text-white" onClick={handleDismissWelcome}>Dismiss</Button>
            </div>
          </div>
        </Card>
      )}

      <Card className="mx-auto mt-6 max-w-[1500px] rounded-3xl border border-slate-200 shadow-sm">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <Text className="text-[11px] font-black uppercase tracking-[0.24em] text-slate-400">Hiring Decision Command Center</Text>
            <Title level={3} className="!mb-1 !mt-2 uppercase tracking-tight font-black">
              HDC Console
            </Title>
            <Text className="text-slate-500 text-xs font-medium">
              Unified hub for committee decisions, executive approvals, and offer release.
            </Text>
          </div>
          <Space size={[8, 8]} wrap>
            {sections.map((item) => (
              <Tooltip key={item.key} title={item.tooltip} mouseEnterDelay={0.5}>
                <Link 
                  to={item.key === 'overview' 
                    ? `/hiring-decisions${applicationId ? `?applicationId=${applicationId}` : ''}` 
                    : `/hiring-decisions/${item.key}${applicationId ? `?applicationId=${applicationId}` : ''}`
                  }
                >
                  <Tag color={item.key === activeSectionKey ? 'blue' : 'default'} className="cursor-pointer rounded-full px-3 py-1 text-[10px] font-black uppercase tracking-widest border-slate-200">
                    {item.label}
                  </Tag>
                </Link>
              </Tooltip>
            ))}
          </Space>
        </div>
      </Card>

      {/* ─── Persistent Application Context ─── */}
      {applicationId && (
        <div className="mx-auto max-w-[1500px] space-y-4">
          {hdcData && (hdcData.job?.status !== 'active' || ['rejected', 'withdrawn'].includes(hdcData.current_stage?.toLowerCase())) && (
            <Alert 
              type="warning" 
              showIcon 
              message="Operational Alert" 
              description={`This application is currently in '${hdcData.current_stage}' status. Some actions may be restricted.`} 
              className="rounded-2xl border-amber-200"
            />
          )}
          
          <Card className="rounded-3xl border-slate-900 bg-slate-900 text-white shadow-2xl overflow-hidden relative">
            <div className="absolute top-0 right-0 p-8 opacity-10">
              <Info size={120} />
            </div>
            
            {loadingStatus ? (
              <div className="py-8 text-center"><Spin /></div>
            ) : hdcData ? (
              <div className="flex flex-col md:flex-row items-center justify-between gap-8 relative z-10 p-2">
                <div className="flex items-center gap-6">
                  <div className="h-16 w-16 rounded-2xl bg-white/10 flex items-center justify-center border border-white/20">
                    <User size={32} className="text-blue-400" />
                  </div>
                  <div>
                    <Title level={4} className="!text-white !m-0">
                      {hdcData.candidate?.name}
                    </Title>
                    <Space split={<Divider type="vertical" className="bg-white/20" />}>
                      <Text className="text-white/60 text-xs flex items-center gap-1.5">
                        <Briefcase size={12} /> {hdcData.job?.title}
                      </Text>
                      <Tag className="m-0 border-none bg-blue-500 text-white text-[10px] font-bold uppercase rounded-md">
                        {hdcData.current_stage}
                      </Tag>
                    </Space>
                  </div>
                </div>

                <div className="flex-1 max-w-md w-full">
                  <div className="flex justify-between items-center mb-2">
                    <Text className="text-[10px] font-black uppercase tracking-widest text-white/40">Decision Progress</Text>
                    <Text className="text-[10px] font-black text-blue-400 uppercase">{hdcData.progress_percentage}%</Text>
                  </div>
                  <Progress 
                    percent={hdcData.progress_percentage} 
                    showInfo={false} 
                    strokeColor="#3b82f6" 
                    trailColor="rgba(255,255,255,0.1)"
                    size="small"
                  />
                </div>

                <div className="flex gap-3">
                  <Tooltip title="View Full Application Pipeline">
                    <Button 
                      ghost 
                      icon={<ExternalLink size={14} />} 
                      className="border-white/20 text-white/80 hover:text-white hover:border-white text-xs rounded-xl"
                      onClick={() => window.open(`/pipeline/applications/${applicationId}`, '_blank')}
                    >
                      Pipeline View
                    </Button>
                  </Tooltip>
                  <Button 
                    danger 
                    type="text" 
                    className="text-white/40 hover:text-white text-xs"
                    onClick={handleClearSelection}
                  >
                    Clear Selection
                  </Button>
                </div>
              </div>
            ) : (
              <div className="py-8 px-8 text-center">
                <Text className="text-white/60 italic">Could not load application context.</Text>
              </div>
            )}
          </Card>
        </div>
      )}

      <div className="mx-auto max-w-[1500px] grid grid-cols-1 xl:grid-cols-4 gap-8">
        <div className="xl:col-span-3">
          <ActiveComponent />
        </div>
        
        {/* ─── ICC Evidence Linkage ─── */}
        <div className="space-y-6">
          {applicationId && hdcData && (
            <Card 
              className="rounded-3xl border-slate-200 shadow-sm sticky top-6"
              title={
                <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-slate-400">
                  <ShieldCheck size={14} className="text-blue-500" /> ICC Interview Evidence
                </div>
              }
            >
              {hdcData.interview_summary?.length > 0 ? (
                <div className="space-y-4">
                  {hdcData.interview_summary.map((i: any) => (
                    <div key={i.id} className="p-4 rounded-2xl bg-slate-50 border border-slate-100 hover:border-blue-200 transition-all cursor-pointer group">
                      <div className="flex justify-between items-start mb-2">
                        <Tag className="m-0 border-none bg-white text-slate-900 text-[9px] font-black uppercase rounded-full shadow-sm">
                          Round {i.round} • {i.type}
                        </Tag>
                        {i.overall_score && (
                          <Text className="text-xs font-black text-blue-600">{i.overall_score}/100</Text>
                        )}
                      </div>
                      <div className="flex justify-between items-center">
                        <Text className="text-[11px] font-bold text-slate-600 truncate mr-2">{i.status?.toUpperCase()}</Text>
                        <Tag color={i.decision === 'hire' ? 'green' : i.decision === 'reject' ? 'red' : 'default'} className="m-0 border-none text-[8px] font-black uppercase px-2 py-0.5 rounded-sm">
                          {i.decision || 'No Decision'}
                        </Tag>
                      </div>
                      <div className="mt-3 pt-3 border-t border-slate-200/50 flex justify-between items-center opacity-0 group-hover:opacity-100 transition-opacity">
                        <Text className="text-[10px] text-slate-400 font-medium">{i.feedback_count} Feedbacks</Text>
                        <Button type="link" size="small" className="text-[10px] font-bold p-0 h-auto uppercase tracking-tighter" onClick={() => window.open(`/interviews/sessions/${i.id}`, '_blank')}>
                          View Details
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-8 text-center border-2 border-dashed border-slate-100 rounded-[2rem]">
                  <Info className="mx-auto h-8 w-8 text-slate-200 mb-2" />
                  <Text className="text-xs text-slate-400 block font-medium">No interview history found.</Text>
                </div>
              )}
              
              <Divider className="my-6 border-slate-100" />
              
              <div className="bg-blue-50 rounded-2xl p-4 border border-blue-100">
                <Text className="text-[10px] font-black uppercase text-blue-600 block mb-2">HDC Eligibility Signal</Text>
                {hdcData.can_approve ? (
                  <div className="flex items-center gap-2 text-emerald-600">
                    <CheckCircle2 size={14} />
                    <Text className="text-xs font-bold">Eligible for Decision</Text>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-amber-600">
                    <Info size={14} />
                    <Text className="text-xs font-bold">Awaiting Pipeline Progress</Text>
                  </div>
                )}
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
