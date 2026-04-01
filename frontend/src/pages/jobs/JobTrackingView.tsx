import React from 'react'
import {
  Table, Tag, Typography, Avatar, Card, Badge, Spin
} from 'antd'
import {
  Clock, ChevronRight, Briefcase, Calendar
} from 'lucide-react'
import dayjs from 'dayjs'
import { useTranslation } from 'react-i18next'
import { useApiQuery } from '@/hooks/useApiQuery'
import { pipelineApi } from '@/api/pipeline'
import { candidatesApi } from '@/api/candidates'
import { formatStatusLabel, getStageZone, type TrackingZone } from '@/utils/status'
import type { Application, Candidate } from '@/types'

const { Text, Title } = Typography

// ── Sub-components ─────────────────────────────────────────────────────────

function TrackingTable({ applications, candidateMap, loading }: { 
  applications: Application[], 
  candidateMap: Map<string, Candidate>,
  loading: boolean 
}) {
  const { t } = useTranslation('pipeline')
  const columns = [
    {
      title: t('table.columns.candidate_name'),
      key: 'candidate',
      render: (_: any, app: Application) => {
        const candidate = candidateMap.get(app.candidate_id)
        return (
          <div className="flex items-center gap-3">
            <Avatar className="bg-slate-100 text-slate-600 font-bold border-none shrink-0">
              {candidate?.first_name?.charAt(0)}{candidate?.last_name?.charAt(0)}
            </Avatar>
            <div className="min-w-0">
              <Text className="block font-bold text-slate-900 text-xs leading-tight">
                {candidate?.full_name || `Candidate ${app.candidate_id.slice(0, 4)}`}
              </Text>
              <Text className="text-[10px] text-slate-400 font-medium">
                {candidate?.current_title || 'No Title'}
              </Text>
            </div>
          </div>
        )
      }
    },
    {
      title: t('table.columns.source'),
      dataIndex: 'source',
      key: 'source',
      render: (s: string) => (
        <Tag className="m-0 border-none bg-blue-50 text-blue-600 font-bold text-[9px] uppercase px-2 rounded">
          {s || 'Direct'}
        </Tag>
      )
    },
    {
      title: t('table.columns.tracking_stage'),
      key: 'stage',
      render: (_: any, app: Application) => {
        const stage = app.status || 'applied'
        const govStatus = app.governance_status
        const placementStatus = app.placement_status
        return (
          <div className="flex flex-col gap-1">
            <Tag className="m-0 border-none bg-slate-100 text-slate-600 font-bold text-[9px] uppercase px-2 rounded w-fit">
              {formatStatusLabel(stage)}
            </Tag>
            {placementStatus && placementStatus !== 'not_applicable' && (
              <Tag color={placementStatus === 'placement_confirmed' ? 'purple' : placementStatus === 'joined' ? 'cyan' : 'amber'} className="m-0 border-none font-bold text-[8px] uppercase px-1.5 rounded w-fit">
                {placementStatus.replace('_', ' ')}
              </Tag>
            )}
            {govStatus && govStatus !== 'submitted' && (
              <Tag className="m-0 border-none bg-amber-50 text-amber-600 font-bold text-[8px] uppercase px-1.5 rounded w-fit">
                Gov: {govStatus.replace('_', ' ')}
              </Tag>
            )}
          </div>
        )
      }
    },
    {
      title: t('table.columns.joining'),
      key: 'joining',
      render: (_: any, app: Application) => {
        const date = app.joined_at || app.expected_joining_date || app.joining_date
        if (!date) return <Text className="text-[10px] text-slate-300">—</Text>
        return (
          <div className="flex items-center gap-1 text-[10px] font-medium text-slate-500">
            <Calendar size={10} className="text-slate-400" />
            {dayjs(date).format('MMM D, YY')}
          </div>
        )
      }
    },
    {
      title: t('table.columns.owner'),
      key: 'owner',
      render: (_: any, app: Application) => (
        <Text className="text-xs text-slate-500 font-medium">
          {app.submitted_by || '—'}
        </Text>
      )
    },
    {
      title: t('table.columns.last_activity'),
      dataIndex: 'updated_at',
      key: 'activity',
      render: (d: string) => (
        <div className="flex items-center gap-1 text-slate-400 text-[11px] font-medium">
          <Clock size={12} />
          {d ? dayjs(d).fromNow() : 'N/A'}
        </div>
      )
    },
    {
      title: '',
      key: 'actions',
      width: 50,
      render: () => <ChevronRight size={14} className="text-slate-300" />
    }
  ]

  return (
    <Table 
      dataSource={applications} 
      columns={columns} 
      rowKey="id" 
      loading={loading}
      pagination={false}
      size="small"
      className="modern-table"
    />
  )
}

// ── Main View ──────────────────────────────────────────────────────────────

export default function JobTrackingView({ jobId }: { jobId: string }) {
  const { t } = useTranslation('pipeline')
  const { data: pipelineData, isLoading: pipelineLoading } = useApiQuery(
    ['job-pipeline-tracking', jobId],
    () => pipelineApi.listApplications({ requisition_id: jobId })
  )

  const { data: candidatesData } = useApiQuery(
    ['candidates', 'all'],
    () => candidatesApi.list()
  )

  const candidateMap = new Map<string, Candidate>(
    ((candidatesData as { candidates: Candidate[] } | undefined)?.candidates ?? []).map((c) => [c.id, c])
  )

  const allApplications = (pipelineData as any)?.applications ?? [] as Application[]
  
  // Visibility Rule: Company only sees Submitted or Approved, or those with no gov status (direct)
  const applications = allApplications.filter((app: Application) => {
    if (!app.governance_status) return true // Direct or standard
    return ['approved', 'submitted'].includes(app.governance_status)
  })

  // Group applications by zone
  const groupedApps: Record<TrackingZone, Application[]> = {
    pre_submission: [],
    submitted: [],
    hiring_flow: [],
  }

  applications.forEach((app: any) => {
    const zone = getStageZone(app.status || 'applied')
    groupedApps[zone].push(app)
  })

  if (pipelineLoading) return <div className="p-20 text-center"><Spin size="large" /></div>
  if (applications.length === 0) return (
    <div className="p-20 flex flex-col items-center justify-center bg-white rounded-3xl border border-dashed border-slate-200">
      <Briefcase size={48} className="text-slate-200 mb-4" />
      <Title level={4} className="!m-0 text-slate-400">{t('tracking.empty.no_candidates')}</Title>
      <p className="text-slate-400 mt-2 font-medium">{t('tracking.empty.start_sourcing')}</p>
    </div>
  )

  const ZONE_CONFIG: Record<TrackingZone, { label: string, color: string }> = {
    pre_submission: { label: t('tracking.zones.pre_submission'), color: 'blue' },
    submitted: { label: t('tracking.zones.submitted'), color: 'purple' },
    hiring_flow: { label: t('tracking.zones.hiring_flow'), color: 'emerald' },
  }

  return (
    <div className="space-y-6 pb-20">
      {(['pre_submission', 'submitted', 'hiring_flow'] as TrackingZone[]).map((zone) => {
        const apps = groupedApps[zone]
        const config = ZONE_CONFIG[zone]
        if (apps.length === 0 && zone !== 'submitted') return null // Only show empty if it's the main zone

        return (
          <Card 
            key={zone}
            title={
              <div className="flex items-center gap-2">
                <span className={`h-2 w-2 rounded-full bg-${config.color}-500`} />
                <span className="text-xs font-black uppercase tracking-widest text-slate-500">{config.label}</span>
                <Badge count={apps.length} showZero size="small" style={{ backgroundColor: '#f1f5f9', color: '#64748b', boxShadow: 'none' }} />
              </div>
            }
            bordered={false}
            className="shadow-soft-sm overflow-hidden"
            bodyStyle={{ padding: 0 }}
          >
            {apps.length === 0 ? (
               <div className="p-10 text-center border-t border-slate-50">
                  <Text className="text-slate-400 italic text-xs">{t('tracking.empty.no_candidates_in_zone')}</Text>
               </div>
            ) : (
              <TrackingTable 
                applications={apps} 
                candidateMap={candidateMap} 
                loading={pipelineLoading} 
              />
            )}
          </Card>
        )
      })}
    </div>
  )
}
