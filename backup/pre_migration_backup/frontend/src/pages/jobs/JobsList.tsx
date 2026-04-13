import { useState, useMemo, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  Button, Input, Typography, Card,
  Tag, Spin, Badge, message, Modal, Drawer,
  Tooltip, Avatar, Divider, Empty, Dropdown
} from 'antd'
import {
  Plus,
  Search,
  Briefcase,
  RefreshCw,
  MapPin,
  Users,
  Target,
  History,
  Building2,
  Activity,
  BrainCircuit,
  Edit,
  Globe,
  Copy,
  Trash2,
  MoreHorizontal,
  PanelLeftClose,
  PanelLeftOpen,
  X,
  Zap,
  UserPlus,
  AlertTriangle,
  CheckCircle,
  Eye,
  MessageSquare
} from 'lucide-react'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { useTranslation } from 'react-i18next'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { requisitionsApi } from '@/api/jobs'
import { organisationApi } from '@/api/organisation'
import { agenciesApi } from '@/api/agencies'
import type { JobRequisition } from '@/types'
import { cn } from '@/utils/cn'
import JobCreateForm from '@/components/forms/JobCreateForm'
import { formatStatusLabel, getStatusStyle } from '@/utils/status'
import { useAuthStore } from '@/store/authStore'
import PipelineBoard from '../pipeline/PipelineBoard'
import JobAutomationView from './JobAutomationView'
import JobMatchSuggestions from '@/components/JobMatchSuggestions'

import { JobCommandCenterView, MetricCard, UnifiedActivityFeed } from './JobCommandCenterView'
import { pipelineApi } from '@/api/pipeline'

import { CustomizeView } from '@/components/common/CustomizeView'
import { useUserPreferences } from '@/hooks/useUserPreferences'

dayjs.extend(relativeTime)
const { Text, Paragraph, Title } = Typography

// ─── Constants ───────────────────────────────────────────────────────────────

const JOB_STATUS_TABS = [
  { label: 'All Jobs', value: 'all' },
  { label: 'Active', value: 'active' },
  { label: 'Draft', value: 'draft' },
  { label: 'Pending Approval', value: 'pending_approval' },
  { label: 'Approved', value: 'approved' },
  { label: 'Paused', value: 'paused' },
  { label: 'Closed', value: 'closed' },
  { label: 'Archived', value: 'cancelled' },
]

const PRIORITY_STYLE: Record<string, { color: string; bg: string; label: string }> = {
  urgent: { color: '#ef4444', bg: '#fef2f2', label: 'Urgent' },
  high:    { color: '#f97316', bg: '#fff7ed', label: 'High' },
  medium:  { color: '#6366f1', bg: '#eef2ff', label: 'Medium' },
  low:     { color: '#94a3b8', bg: '#f8fafc', label: 'Low' },
}

// ─── Helpers ───────────────────────────────────────────────────────────────────

function avatarColor(name: string) {
  const colors = ['#6366f1', '#8b5cf6', '#ec4899', '#f97316', '#22c55e', '#14b8a6', '#3b82f6']
  return colors[(name?.charCodeAt(0) || 0) % colors.length]
}

const formatSalary = (amount: number | string, currency: string = 'INR') => 
  new Intl.NumberFormat('en-IN', { 
    style: 'currency', 
    currency: currency,
    maximumFractionDigits: 0
  }).format(Number(amount))

// ─── Main Component: JobsList ──────────────────────────────────────────────────────

export default function JobsList() {
  const { t } = useTranslation(['jobs', 'common'])
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const user = useAuthStore((s) => s.user)

  const { pages } = useUserPreferences()
  const pagePrefs = pages['jobs'] || { hiddenColumns: [], hiddenSections: [], density: 'comfortable' }
  const isCompact = pagePrefs.density === 'compact'
  const isIntelligenceHidden = pagePrefs.hiddenSections.includes('intelligence')

  // State
  const [activeSurface, setActiveSurface] = useState<'jobs' | 'pipeline'>(
    (searchParams.get('tab') as 'jobs' | 'pipeline') || 'jobs'
  )
  const [activeStatusTab, setActiveStatusTab] = useState<string>(searchParams.get('status') || 'active')
  const [search, setSearch] = useState('')
  const [selectedJobId, setSelectedJobId] = useState<string | null>(searchParams.get('id'))
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'overview')

  // Layout State
  const [leftPanelCollapsed, setLeftPanelCollapsed] = useState(() => 
    localStorage.getItem('jobs_left_panel_collapsed') === 'true'
  )

  // Agency Assignment State
  const [assignAgencyModalOpen, setAssignAgencyModalOpen] = useState(false)
  const [assigningAgency, setAssigningAgency] = useState(false)
  const [selectedAgencies, setSelectedAgencies] = useState<string[]>([])

  // Queries
  const { data: usersData } = useApiQuery(['organisation-users'], () => organisationApi.listUsers())
  const users = (usersData as any)?.users ?? []

  const { data: deptsData } = useApiQuery(['organisation-departments'], () => organisationApi.listDepartments())
  const departments = (deptsData as any)?.departments ?? []

  const { data: locsData } = useApiQuery(['organisation-locations'], () => organisationApi.listLocations())
  const locations = (locsData as any)?.locations ?? []

  const { data: agencyRelData } = useApiQuery(['agency-relationships'], () => agenciesApi.listRelationships(), { enabled: activeSurface === 'jobs' })
  const agencyRelationships = (agencyRelData as any)?.relationships ?? []

  const { data, isLoading, refetch } = useApiQuery(
    ['jobs', activeStatusTab, search],
    () => requisitionsApi.list({
      status: activeStatusTab === 'all' ? undefined : activeStatusTab,
      search: search || undefined,
    })
  )

  const requisitions = useMemo(() => {
    const list = ((data as any)?.requisitions as JobRequisition[] | undefined) ??
                 ((data as any)?.data?.requisitions as JobRequisition[] | undefined) ??
                 []
    return list
  }, [data])

  const handleDuplicate = async (id: string) => {
    try {
      await requisitionsApi.clone(id)
      message.success('Job requisition duplicated')
      refetch()
    } catch (err) {
      message.error('Failed to duplicate job')
    }
  }

  const handleArchive = async (id: string) => {
    Modal.confirm({
      title: 'Archive Requisition',
      content: 'Are you sure you want to archive this job? You can restore it from the Archived tab.',
      okText: 'Archive',
      okType: 'danger',
      onOk: async () => {
        try {
          await requisitionsApi.update(id, { status: 'cancelled' })
          message.success('Job archived')
          if (selectedJobId === id) setSelectedJobId(null)
          refetch()
        } catch (err) {
          message.error('Failed to archive job')
        }
      }
    })
  }

  const handleRestore = async (id: string) => {
    Modal.confirm({
      title: 'Restore Job',
      content: 'Restore this job to Draft status so it can be worked on again?',
      okText: 'Restore',
      onOk: async () => {
        try {
          await requisitionsApi.update(id, { status: 'draft' })
          message.success('Job restored to Draft')
          refetch()
        } catch (err) {
          message.error('Failed to restore job')
        }
      }
    })
  }

  const handleAssignAgencies = async () => {
    if (!selectedJobId || selectedAgencies.length === 0) return
    setAssigningAgency(true)
    try {
      await Promise.all(selectedAgencies.map(agencyId => 
        agenciesApi.assignJob(selectedJobId, agencyId, { notes: 'Assigned from Job Command Center' })
      ))
      message.success(`Successfully assigned ${selectedAgencies.length} agencies`)
      setAssignAgencyModalOpen(false)
      setSelectedAgencies([])
      queryClient.invalidateQueries({ queryKey: ['job-agency-intelligence', selectedJobId] })
      queryClient.invalidateQueries({ queryKey: ['requisition-full', selectedJobId] })
    } catch (err) {
      message.error('Failed to assign agencies')
    } finally {
      setAssigningAgency(false)
    }
  }

  // Default selection
  useEffect(() => {
    if (!selectedJobId && requisitions.length > 0 && !isLoading) {
      setSelectedJobId(requisitions[0].id)
    }
  }, [requisitions, selectedJobId, isLoading])

  const selectedJob = useMemo(() => 
    requisitions.find(j => j.id === selectedJobId) || null
  , [requisitions, selectedJobId])

  // Sync URL
  useEffect(() => {
    const params: any = {}
    if (selectedJobId) params.id = selectedJobId
    if (activeStatusTab !== 'active') params.status = activeStatusTab
    if (activeTab !== 'overview') params.innerTab = activeTab
    params.tab = activeSurface
    setSearchParams(params, { replace: true })
  }, [selectedJobId, activeStatusTab, activeTab, activeSurface, setSearchParams])

  // Persistence
  useEffect(() => {
    localStorage.setItem('jobs_left_panel_collapsed', String(leftPanelCollapsed))
  }, [leftPanelCollapsed])

  const selectJob = (id: string) => {
    setSelectedJobId(id)
  }

  return (
    <div className="flex flex-col h-[calc(100vh-56px)] bg-[#F8FAFC] -mt-6 -mx-6 overflow-hidden">
      
      {/* ══ Level 1: Workspace Header ══════════════════════════════════════ */}
      <div className="flex h-14 flex-none items-center justify-between border-b border-slate-200 bg-white px-6 z-20">
        <div className="flex items-center gap-4">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-soft-sm">
            <Briefcase size={18} />
          </div>
          <h1 className="text-sm font-black text-slate-900 uppercase tracking-widest">Workspace</h1>

          <div className="flex items-center gap-1 rounded-xl bg-slate-100 p-1 border border-slate-200/50 ml-4">
            <button 
              onClick={() => setActiveSurface('jobs')}
              className={cn(
                "flex items-center gap-2 rounded-lg px-4 py-1.5 text-[10px] font-black uppercase tracking-widest transition-all",
                activeSurface === 'jobs' ? "bg-white text-indigo-700 shadow-sm border border-indigo-100" : "text-slate-500 hover:text-slate-700"
              )}
            >
              Hub
            </button>
            <button 
              onClick={() => setActiveSurface('pipeline')}
              className={cn(
                "flex items-center gap-2 rounded-lg px-4 py-1.5 text-[10px] font-black uppercase tracking-widest transition-all",
                activeSurface === 'pipeline' ? "bg-white text-indigo-700 shadow-sm border border-indigo-100" : "text-slate-500 hover:text-slate-700"
              )}
            >
              Pipeline
            </button>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <CustomizeView 
            pageId="jobs"
            columns={[]}
            sections={[
              { id: 'intelligence', label: 'Job Intelligence Panel' },
            ]}
          />
          <button 
            onClick={() => navigate('/jobs/create')}
            className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-[10px] font-black uppercase tracking-widest text-white hover:bg-indigo-700 transition shadow-soft-lg"
          >
            <Plus size={14} /> Add Job
          </button>
          <button
            onClick={() => refetch()}
            className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-500 hover:bg-slate-50 shadow-soft-sm transition-all"
          >
            <RefreshCw size={16} className={cn(isLoading && "animate-spin")} />
          </button>
        </div>
      </div>

      {/* ══ Level 2: Body ═══════════════════════════════════════════════════ */}
      <div className="flex flex-1 overflow-hidden relative">
        
        {/* COLUMN 1: Job List Panel */}
        <div 
          className={cn(
            "flex flex-none flex-col overflow-hidden border-r border-slate-200 bg-[#f8fafc] transition-all duration-300 relative z-10",
            leftPanelCollapsed ? "w-14" : "w-[300px]"
          )}
        >
          <div className="flex-none border-b border-slate-200 bg-white p-3 flex items-center justify-between h-14">
            {!leftPanelCollapsed && (
              <div className="flex-1 flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-1.5 focus-within:border-indigo-300 transition-all">
                <Search size={12} className="text-slate-400 shrink-0" />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search..."
                  className="flex-1 bg-transparent text-xs text-slate-700 outline-none placeholder-slate-400"
                />
              </div>
            )}
            <button onClick={() => setLeftPanelCollapsed(!leftPanelCollapsed)} className={cn("flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-50", leftPanelCollapsed ? "w-full" : "ml-2")}>
              {leftPanelCollapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
            </button>
          </div>

          <div className="flex-1 overflow-y-auto custom-scrollbar p-2 space-y-1">
            {isLoading && requisitions.length === 0 ? (
              <div className="py-12 flex justify-center"><Spin /></div>
            ) : (
              requisitions.map((job) => (
                <JobOperationalCard
                  key={job.id}
                  job={job}
                  selected={selectedJobId === job.id}
                  onSelect={() => selectJob(job.id)}
                  users={users}
                  departments={departments}
                  locations={locations}
                  collapsed={leftPanelCollapsed}
                  onDuplicate={handleDuplicate}
                  onArchive={handleArchive}
                  onRestore={handleRestore}
                  density={pagePrefs.density}
                />
              ))
            )}
          </div>
        </div>

        {/* COLUMN 2: Workspace */}
        <div className="flex flex-1 flex-row overflow-hidden bg-white">
          <div className="flex-1 flex flex-col overflow-hidden">
            {selectedJob ? (
              activeSurface === 'pipeline' ? (
                <div className="h-full">
                  <PipelineBoard jobId={selectedJob.id} isSubView />
                </div>
              ) : (
                <JobCommandCenter
                  job={selectedJob}
                  activeTab={activeTab}
                  setActiveTab={setActiveTab}
                  onEdit={() => navigate(`/jobs/${selectedJob.id}/setup`)}
                  onRefresh={refetch}
                  onDuplicate={handleDuplicate}
                  onArchive={handleArchive}
                  onAssignAgency={() => setAssignAgencyModalOpen(true)}
                />
              )
            ) : (
              <div className="flex flex-1 flex-col items-center justify-center gap-3 p-8 text-center bg-[#f8fafc]">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-50 shadow-soft-sm">
                  <Target size={28} className="text-indigo-300" />
                </div>
                <p className="text-sm font-bold text-slate-600 uppercase tracking-widest">Select a Requisition</p>
              </div>
            )}
          </div>

          {/* COLUMN 3: Intelligence Panel (Right) - Hidden when Pipeline surface is active for max width */}
          {selectedJob && activeSurface !== 'pipeline' && activeTab !== 'pipeline' && !isIntelligenceHidden && (
            <div className="flex w-[300px] flex-none flex-col overflow-hidden border-l border-slate-200 bg-[#f8fafc] animate-in slide-in-from-right duration-300">
              <JobIntelligencePanel job={selectedJob} />
            </div>
          )}
        </div>
      </div>

      {/* Agency Assignment Modal */}
      <Modal
        title={
          <div className="flex items-center gap-2">
            <div className="p-2 bg-blue-50 text-blue-600 rounded-xl"><UserPlus size={18} /></div>
            <div>
              <Text className="block text-sm font-black uppercase tracking-tight">Assign Agencies</Text>
              <Text className="text-[10px] text-slate-400 font-bold uppercase">{selectedJob?.title}</Text>
            </div>
          </div>
        }
        open={assignAgencyModalOpen}
        onCancel={() => setAssignAgencyModalOpen(false)}
        onOk={handleAssignAgencies}
        okText="Assign Selected"
        confirmLoading={assigningAgency}
        okButtonProps={{ className: "bg-blue-600 border-none rounded-xl h-10 font-black uppercase text-[10px] tracking-widest" }}
        cancelButtonProps={{ className: "rounded-xl h-10 font-black uppercase text-[10px] tracking-widest" }}
        className="modern-modal"
        width={440}
      >
        <div className="py-4">
          <Text className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-3">Select agencies to invite</Text>
          <div className="space-y-4">
            <div className="p-1 rounded-2xl bg-slate-50 border border-slate-100">
               <div className="max-h-[200px] overflow-y-auto p-2 space-y-1">
                 {agencyRelationships.map((rel: any) => {
                   const agencyId = rel.agency_tenant_id
                   const isSelected = selectedAgencies.includes(agencyId)
                   return (
                     <div 
                       key={agencyId}
                       onClick={() => {
                         if (isSelected) {
                           setSelectedAgencies(prev => prev.filter(id => id !== agencyId))
                         } else {
                           setSelectedAgencies(prev => [...prev, agencyId])
                         }
                       }}
                       className={cn(
                         "flex items-center justify-between p-3 rounded-xl cursor-pointer transition-all border",
                         isSelected ? "bg-white border-blue-200 shadow-sm" : "hover:bg-white hover:border-slate-200 border-transparent"
                       )}
                     >
                       <div className="flex items-center gap-3">
                         <Avatar size="small" className="bg-slate-200 text-slate-600 font-black border-none text-[8px]">
                           {rel.agency_name?.charAt(0) || 'A'}
                         </Avatar>
                         <Text className={cn("text-xs font-bold", isSelected ? "text-blue-600" : "text-slate-700")}>
                           {rel.agency_name || `Agency ${agencyId.slice(0, 8)}`}
                         </Text>
                       </div>
                       {isSelected && <div className="h-5 w-5 bg-blue-600 rounded-full flex items-center justify-center text-white"><CheckCircle size={12} /></div>}
                     </div>
                   )
                 })}
                 {agencyRelationships.length === 0 && <div className="py-8 text-center"><Text className="text-[10px] font-bold text-slate-400 uppercase">No connected agencies</Text></div>}
               </div>
            </div>
          </div>
          <div className="mt-6 p-4 bg-amber-50 rounded-2xl border border-amber-100">
            <div className="flex items-start gap-3">
              <Zap size={14} className="text-amber-500 mt-1" />
              <Text className="text-[11px] text-amber-800 font-medium leading-relaxed">
                Selected agencies will receive an immediate invitation to submit candidates for this role.
              </Text>
            </div>
          </div>
        </div>
      </Modal>

    </div>
  )
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function JobOperationalCard({ job, selected, onSelect, users, departments, locations, collapsed, onDuplicate, onArchive, onRestore, density }: any) {
  const isCompact = density === 'compact'
  const navigate = useNavigate()
  const statusStyle = getStatusStyle(job.status, 'job')
  const priority = PRIORITY_STYLE[job.priority || 'medium']
  const metadata = (job.metadata || {}) as Record<string, any>
  const owner = users?.find((u: any) => u.id === job.created_by)
  // Expiry badge
  const expiryDate = metadata.expiry_date || job.target_date
  const isExpired = expiryDate && dayjs(expiryDate).isBefore(dayjs(), 'day')
  const isExpiringSoon = !isExpired && expiryDate && dayjs(expiryDate).diff(dayjs(), 'day') <= 7
  const ownerName = owner ? `${owner.first_name} ${owner.last_name}` : 'Unknown'
  
  const deptName = departments?.find((d: any) => d.id === job.department_id)?.name || 'General'
  const locName = locations?.find((l: any) => l.id === job.location_id)?.name || 'Remote'

  const metadata_app_count = Number(metadata.applications_count) || 0
  const totalApps = metadata_app_count

  if (collapsed) {
    return (
      <Tooltip title={job.title} placement="right">
        <button
          onClick={onSelect}
          className={cn(
            "w-full aspect-square rounded-xl flex flex-col items-center justify-center transition-all relative group mb-1 border",
            selected
              ? "border-indigo-400 bg-white shadow-sm ring-2 ring-indigo-100"
              : "border-transparent hover:bg-white hover:border-slate-200"
          )}
        >
          <Avatar size={24} style={{ backgroundColor: avatarColor(ownerName), fontSize: '10px' }} className="font-black">
            {ownerName.charAt(0)}
          </Avatar>
          <div className={cn("mt-1.5 h-1.5 w-1.5 rounded-full", statusStyle.dotClass)} />
          {selected && <div className="absolute left-0 top-2 bottom-2 w-1 bg-indigo-600 rounded-r-full" />}
        </button>
      </Tooltip>
    )
  }

  return (
    <button
      onClick={onSelect}
      className={cn(
        "w-full rounded-xl border text-left transition-all relative overflow-hidden group mb-1",
        isCompact ? "p-2.5" : "p-3.5",
        selected
          ? "border-indigo-400 bg-white shadow-sm ring-2 ring-indigo-100"
          : "border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm"
      )}
    >
      {selected && <div className="absolute left-0 top-0 bottom-0 w-1 bg-indigo-600" />}
      
      <div className={cn("flex items-start justify-between gap-2", isCompact ? "mb-1.5" : "mb-2.5")}>
        <div className="min-w-0 flex-1">
          <div className={cn(
            "truncate font-bold leading-tight",
            isCompact ? "text-[11px] mb-0.5" : "text-xs mb-1",
            selected ? "text-slate-900" : "text-slate-800"
          )}>
            {job.title || 'Untitled Role'}
          </div>
          <div className={cn("text-indigo-600 font-bold uppercase tracking-wider truncate", isCompact ? "text-[8px] mb-0.5" : "text-[9px] mb-1")}>
            {job.job_ref_id || '—'}
          </div>
          {!isCompact && (
            <div className="flex items-center gap-2 text-[10px] text-slate-500 font-medium">
              <span className="truncate">{job.work_mode?.replace('_', ' ')}</span>
              <span className="text-slate-300">•</span>
              <span className="truncate">{deptName}</span>
            </div>
          )}
        </div>
        <div className="shrink-0 flex items-center gap-2">
          <Dropdown
            menu={{
              items: [
                { key: 'edit', label: 'Edit Setup', icon: <Edit size={12} />, onClick: (e) => { e.domEvent.stopPropagation(); navigate(`/jobs/${job.id}/setup`) } },
                { key: 'duplicate', label: 'Duplicate Job', icon: <Copy size={12} />, onClick: (e) => { e.domEvent.stopPropagation(); onDuplicate(job.id) } },
                { key: 'map_relations', label: 'Map to Relations', icon: <MessageSquare size={12} />, onClick: (e) => { e.domEvent.stopPropagation(); message.success('Job mapped to Candidate Relations for sourcing') } },
                { type: 'divider' },
                job.status === 'cancelled'
                  ? { key: 'restore', label: 'Restore Job', icon: <Trash2 size={12} />, onClick: (e) => { e.domEvent.stopPropagation(); onRestore?.(job.id) } }
                  : { key: 'archive', label: 'Archive Job', icon: <Trash2 size={12} />, danger: true, onClick: (e) => { e.domEvent.stopPropagation(); onArchive(job.id) } },
              ]
            }}
            placement="bottomRight"
            trigger={['click']}
          >
            <Button 
              type="text" 
              size="small" 
              icon={<MoreHorizontal size={14} className="text-slate-400 group-hover:text-slate-600" />} 
              className="h-6 w-6 flex items-center justify-center rounded-md hover:bg-slate-100"
              onClick={(e) => e.stopPropagation()}
            />
          </Dropdown>
          <span 
            className="px-1.5 py-0.5 rounded text-[8px] font-bold uppercase tracking-wider border"
            style={{ backgroundColor: priority.bg, color: priority.color, borderColor: priority.color + '20' }}
          >
            {priority.label}
          </span>
        </div>
      </div>

      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-1.5 flex-wrap">
          <div className={cn(
            "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide border",
            statusStyle.softClass
          )}>
            <span className={cn("h-1 w-1 rounded-full", statusStyle.dotClass)} />
            {formatStatusLabel(job.status)}
          </div>
          {isExpired && (
            <span className="inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[9px] font-bold uppercase bg-red-50 text-red-600 border border-red-200">
              Expired
            </span>
          )}
          {isExpiringSoon && (
            <span className="inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[9px] font-bold uppercase bg-amber-50 text-amber-600 border border-amber-200">
              Expiring {dayjs(expiryDate).fromNow()}
            </span>
          )}
          {job.is_confidential && (
            <span className="inline-flex items-center gap-0.5 rounded-full px-1.5 py-0.5 text-[9px] font-bold uppercase bg-slate-100 text-slate-500 border border-slate-200">
              Conf.
            </span>
          )}
        </div>
        <div className="flex items-center gap-1.5 opacity-80">
          <Avatar size={16} style={{ backgroundColor: avatarColor(ownerName), fontSize: '7px' }} className="font-bold">
            {ownerName.charAt(0)}
          </Avatar>
          <Text className="text-[10px] font-medium text-slate-500">{ownerName.split(' ')[0]}</Text>
        </div>
      </div>

      <div className="flex items-end justify-between gap-4 pt-2.5 border-t border-slate-50">
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1.5">
            <Text className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">Pipeline</Text>
            <Text className="text-[10px] font-bold text-indigo-600 leading-none">{totalApps}</Text>
          </div>
          <div className="flex gap-0.5 h-1 w-full bg-slate-100 rounded-full overflow-hidden">
            <div className="h-full bg-blue-500" style={{ width: `${(Number(metadata.applied) || 0) / (totalApps || 1) * 100}%` }} />
            <div className="h-full bg-orange-500" style={{ width: `${(Number(metadata.interview) || 0) / (totalApps || 1) * 100}%` }} />
            <div className="h-full bg-emerald-500" style={{ width: `${(Number(metadata.offer) || 0) / (totalApps || 1) * 100}%` }} />
          </div>
        </div>
        <div className="shrink-0 text-right">
           <div className="flex items-center gap-1 text-slate-400 text-[9px] font-bold uppercase">
             <MapPin size={8} /> {locName}
           </div>
           <Text className="text-[9px] font-medium text-slate-400 leading-none block mt-1">{dayjs(job.created_at).fromNow(true)}</Text>
        </div>
      </div>
    </button>
  )
}

function JobCommandCenter({ job: jobSummary, activeTab, setActiveTab, onEdit, onRefresh, onDuplicate, onArchive, onAssignAgency }: any) {
  const { t } = useTranslation('jobs')
  const navigate = useNavigate()
  const statusStyle = getStatusStyle(jobSummary.status, 'job')
  const queryClient = useQueryClient()

  // Fetch full requisition details to ensure we have all data
  const { data: fullJobData, isLoading: jobLoading } = useApiQuery(
    ['requisition-full', jobSummary.id],
    () => requisitionsApi.get(jobSummary.id)
  )
  const job = (fullJobData as any)?.requisition || jobSummary

  const { data: pipelineData, isLoading: pipelineLoading } = useApiQuery(
    ['job-command-center-pipeline', job.id],
    () => pipelineApi.listApplications({ requisition_id: job.id }),
    { enabled: Boolean(job?.id) },
  )
  const applications = (pipelineData as any)?.applications || []
  const stats = {
    total: applications.length,
    submitted: applications.filter((a: any) => ['applied', 'screening'].includes(a.status)).length,
    shortlisted: applications.filter((a: any) => a.status === 'shortlisted').length,
    interview: applications.filter((a: any) => ['interview', 'interview_scheduled'].includes(a.status)).length,
    offer: applications.filter((a: any) => a.status === 'offer_extended').length,
    joined: applications.filter((a: any) => a.status === 'joined').length,
  }

  // ... (stats, etc.)

  const submitMutation = useMutation({
    mutationFn: () => requisitionsApi.submitForApproval(job.id),
    onSuccess: () => {
      message.success('Submitted for approval')
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
      onRefresh()
    }
  })

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* Header */}
      <div className="border-b border-slate-100 bg-white px-6 py-4 shrink-0">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-white shadow-soft-sm">
              <Briefcase size={22} />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                <span className={cn("inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[9px] font-black uppercase tracking-[0.1em] border", statusStyle.softClass)}>
                  {formatStatusLabel(job.status)}
                </span>
                <span className={cn(
                  "px-2.5 py-0.5 rounded-full text-[9px] font-black uppercase tracking-[0.1em] border shadow-soft-sm",
                  job.priority === 'urgent' ? "bg-rose-50 text-rose-600 border-rose-100" : "bg-slate-50 text-slate-500 border-slate-100"
                )}>
                  {job.priority} {t('fields.priority')}
                </span>
              </div>
              <h1 className="text-lg font-black text-slate-900 tracking-tight leading-none uppercase">{job.title}</h1>
              {job.job_ref_id && (
                <div className="mt-1">
                  <span className="inline-flex items-center rounded-full border border-indigo-100 bg-indigo-50 px-2.5 py-0.5 text-[9px] font-black uppercase tracking-[0.12em] text-indigo-700">
                    {job.job_ref_id}
                  </span>
                </div>
              )}
            </div>
          </div>
          
          <div className="flex flex-col items-end gap-3">
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-3 text-[9px] font-bold text-slate-400 uppercase tracking-widest mr-4">
                <span className="flex items-center gap-1"><MapPin size={11} /> {job.location_id || 'Remote'}</span>
                <span>•</span>
                <span className="flex items-center gap-1"><Users size={11} /> {job.headcount} slots</span>
              </div>
              <button 
                onClick={() => navigate(`/jobs/${job.id}/setup`)} 
                className="flex h-8 items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 text-[10px] font-black uppercase tracking-widest text-slate-600 hover:bg-slate-50 transition-all shadow-soft-sm"
              >
                <Edit size={12} /> Edit Setup
              </button>
              
              <Tooltip title="Duplicate Job">
                <button 
                  onClick={() => onDuplicate(job.id)}
                  className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 hover:text-indigo-600 transition-all shadow-soft-sm"
                >
                  <Copy size={14} />
                </button>
              </Tooltip>

              <Tooltip title="Archive Job">
                <button 
                  onClick={() => onArchive(job.id)}
                  className="flex h-8 w-8 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-400 hover:text-rose-600 transition-all shadow-soft-sm"
                >
                  <Trash2 size={14} />
                </button>
              </Tooltip>

              <Divider type="vertical" className="h-6 border-slate-200 mx-1" />
              {job.status === 'draft' && (
                <Button type="primary" onClick={() => submitMutation.mutate()} loading={submitMutation.isPending} className="!h-8 !text-[9px] font-black uppercase tracking-widest bg-blue-600 border-none shadow-soft-lg">
                  Submit
                </Button>
              )}
            </div>
            {/* Live Metrics strip in header */}
            <div className="flex gap-1.5 overflow-x-auto pb-1 max-w-[500px]">
              <MetricCard label={t('candidate_panel.total')} value={stats.total} color="slate" />
              <MetricCard label={t('summary.submitted')} value={stats.submitted} color="blue" />
              <MetricCard label={t('summary.shortlisted')} value={stats.shortlisted} color="indigo" />
              <MetricCard label={t('summary.interview')} value={stats.interview} color="purple" />
              <MetricCard label={t('summary.offer')} value={stats.offer} color="amber" />
              <MetricCard label={t('summary.joined')} value={stats.joined} color="emerald" />
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex h-11 flex-none items-center border-b border-slate-100 bg-white px-6">
        <div className="flex items-center gap-1 h-full">
          {[
            { key: 'overview', label: t('command_center.title'), icon: <Zap size={12} /> },
            { key: 'job_info', label: t('tabs.overview') },
            { key: 'pipeline', label: t('command_center.pipeline') },
            { key: 'interviews', label: t('tabs.interviews') },
            { key: 'candidates', label: 'Match' },
            { key: 'automation', label: 'Automation', icon: <BrainCircuit size={12} /> },
            { key: 'activity', label: t('tabs.activity') },
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={cn(
                "px-4 py-1 text-[10px] font-black uppercase tracking-widest transition h-full relative flex items-center gap-2",
                activeTab === tab.key ? "text-indigo-600" : "text-slate-400 hover:text-slate-600"
              )}
            >
              {tab.icon}
              {tab.label}
              {activeTab === tab.key && <div className="absolute bottom-0 left-0 h-0.5 w-full bg-indigo-600 rounded-full" />}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-hidden relative bg-[#F8FAFC]/30">
        <div className="absolute inset-0 overflow-hidden">
          {(jobLoading || pipelineLoading) && <div className="absolute inset-0 flex items-center justify-center bg-white/50 z-10"><Spin /></div>}
          {activeTab === 'overview' && (
            <div className="overflow-y-auto h-full custom-scrollbar p-6">
              <JobCommandCenterView requisition={job} applications={applications} onAssignAgency={onAssignAgency} />
            </div>
          )}
          {activeTab === 'job_info' && (
            <div className="overflow-y-auto h-full custom-scrollbar p-6">
              <OverviewTabContent job={job} />
            </div>
          )}
          {activeTab === 'pipeline' && (
            <div className="overflow-y-auto h-full custom-scrollbar p-6">
              <PipelineCompactView applications={applications} onOpenFull={() => setActiveTab('pipeline')} />
            </div>
          )}
          {activeTab === 'candidates' && (
            <div className="overflow-y-auto h-full custom-scrollbar p-6">
              <JobMatchSuggestions jobId={job.id} onMatched={() => onRefresh()} />
            </div>
          )}
          {activeTab === 'automation' && (
            <div className="overflow-y-auto h-full custom-scrollbar p-6">
              <JobAutomationView job={job} applications={applications} />
            </div>
          )}
          {activeTab === 'activity' && (
            <div className="overflow-y-auto h-full custom-scrollbar p-6">
              <UnifiedActivityFeed jobId={job.id} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function PipelineCompactView({ applications, onOpenFull }: { applications: any[], onOpenFull: () => void }) {
  const { t } = useTranslation('jobs')
  const stages = [
    { key: 'applied', label: 'Sourced', count: applications.filter(a => a.status === 'applied').length, color: 'bg-slate-400' },
    { key: 'screening', label: 'Screening', count: applications.filter(a => a.status === 'screening').length, color: 'bg-blue-500' },
    { key: 'interview', label: 'Interview', count: applications.filter(a => a.status === 'interview').length, color: 'bg-purple-500' },
    { key: 'offer', label: 'Offer', count: applications.filter(a => a.status === 'offer_extended').length, color: 'bg-amber-500' },
    { key: 'joined', label: 'Hired', count: applications.filter(a => a.status === 'joined').length, color: 'bg-emerald-500' },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-black uppercase tracking-widest text-slate-800">Pipeline Distribution</h3>
        <Button type="primary" size="small" onClick={onOpenFull} className="text-[10px] font-black uppercase tracking-widest bg-indigo-600 h-8 rounded-xl shadow-soft-lg">
          Open Full Kanban
        </Button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {stages.map(s => (
          <Card key={s.key} className="rounded-2xl border-slate-100 shadow-soft-sm text-center">
            <div className={cn("h-1 w-12 mx-auto rounded-full mb-3", s.color)} />
            <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">{s.label}</p>
            <p className="text-2xl font-black text-slate-800">{s.count}</p>
          </Card>
        ))}
      </div>
      
      <Card className="rounded-3xl border-slate-100 shadow-soft-sm mt-6" title={<span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Recent Stage Movements</span>}>
        <div className="py-8 text-center">
           <Activity size={32} className="mx-auto text-slate-200 mb-3" />
           <p className="text-[10px] font-bold text-slate-400 uppercase">Select a stage to view candidates</p>
        </div>
      </Card>
    </div>
  )
}

function JobIntelligencePanel({ job }: { job: JobRequisition }) {
  const { t } = useTranslation('jobs')
  
  // Fetch applications for real intelligence
  const { data: pipelineData } = useApiQuery(
    ['job-intel-pipeline', job.id],
    () => pipelineApi.listApplications({ requisition_id: job.id })
  )
  const applications = (pipelineData as any)?.applications || []

  const urgentActions = [
    { label: 'Waiting Review', count: applications.filter((a: any) => a.status === 'applied' || a.status === 'screening').length, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Pending Feedback', count: applications.filter((a: any) => a.status === 'interview' && !a.feedback).length, color: 'text-purple-600', bg: 'bg-purple-50' },
    { label: 'Offer Decisions', count: applications.filter((a: any) => a.status === 'offer_extended' && !a.offer_accepted_at).length, color: 'text-amber-600', bg: 'bg-amber-50' },
  ]

  const bottlenecks = applications.filter((a: any) => 
    dayjs().diff(dayjs(a.updated_at), 'days') > 7 && a.status !== 'joined' && a.status !== 'rejected'
  ).length

  const slaStats = {
    overdue: applications.filter((a: any) => dayjs().diff(dayjs(a.updated_at), 'hour') > 48).length,
    dueSoon: applications.filter((a: any) => {
      const diff = dayjs().diff(dayjs(a.updated_at), 'hour')
      return diff > 36 && diff <= 48
    }).length,
    onTrack: applications.filter((a: any) => dayjs().diff(dayjs(a.updated_at), 'hour') <= 36).length,
  }

  return (
    <div className="flex flex-col h-full bg-white">
      <div className="p-4 border-b border-slate-100 bg-white flex items-center justify-between h-14">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600">
             <BrainCircuit size={16} />
          </div>
          <span className="text-[10px] font-black text-slate-900 uppercase tracking-widest leading-none">Operational Intel</span>
        </div>
        <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-blue-50 border border-blue-100/50">
           <div className="h-1.5 w-1.5 rounded-full bg-blue-500 animate-pulse" />
           <span className="text-[8px] font-black text-blue-600 uppercase">Live</span>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-8 custom-scrollbar">
        {/* SLA Engine */}
        <div>
          <span className="text-[9px] font-black text-slate-400 uppercase tracking-[0.2em] block mb-4 ml-1">Hiring SLA Engine</span>
          <div className="grid grid-cols-3 gap-2">
             <div className="p-2 rounded-xl bg-emerald-50 border border-emerald-100 text-center">
                <Text className="block text-[8px] font-black text-emerald-600 uppercase mb-1">On Track</Text>
                <Text className="text-sm font-black text-emerald-700">{slaStats.onTrack}</Text>
             </div>
             <div className="p-2 rounded-xl bg-amber-50 border border-amber-100 text-center">
                <Text className="block text-[8px] font-black text-amber-600 uppercase mb-1">Due Soon</Text>
                <Text className="text-sm font-black text-amber-700">{slaStats.dueSoon}</Text>
             </div>
             <div className="p-2 rounded-xl bg-rose-50 border border-rose-100 text-center">
                <Text className="block text-[8px] font-black text-rose-600 uppercase mb-1">Overdue</Text>
                <Text className="text-sm font-black text-rose-700">{slaStats.overdue}</Text>
             </div>
          </div>
        </div>

        {/* Urgent Actions */}
        <div>
          <span className="text-[9px] font-black text-slate-400 uppercase tracking-[0.2em] block mb-4 ml-1">Urgent Actions</span>
          <div className="space-y-2">
            {urgentActions.map((action, i) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-2xl bg-white border border-slate-100 hover:border-indigo-100 hover:shadow-sm transition-all group cursor-pointer">
                <Text className="text-[10px] font-bold text-slate-600 uppercase group-hover:text-indigo-600 transition-colors">{action.label}</Text>
                <div className={cn("px-2 py-0.5 rounded-lg font-black text-[10px]", action.bg, action.color)}>
                   {action.count}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Bottlenecks */}
        <div>
          <span className="text-[9px] font-black text-slate-400 uppercase tracking-[0.2em] block mb-4 ml-1">Risk Analysis</span>
          {bottlenecks > 0 ? (
            <div className="p-4 rounded-2xl bg-rose-50 border border-rose-100 relative overflow-hidden">
              <div className="absolute top-0 right-0 p-2 opacity-10">
                 <AlertTriangle size={48} className="text-rose-600" />
              </div>
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle size={14} className="text-rose-600" />
                <span className="text-[10px] font-black text-rose-700 uppercase">Bottleneck Alert</span>
              </div>
              <p className="text-[11px] text-rose-800 font-bold leading-relaxed">
                {bottlenecks} candidates are stuck without movement for {'>'} 7 days. This is slowing down your Time-to-Fill.
              </p>
              <Button size="small" className="mt-3 bg-white border-rose-200 text-rose-600 font-black text-[9px] uppercase h-7 rounded-lg">Action Items</Button>
            </div>
          ) : (
            <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-100 text-center">
               <CheckCircle size={20} className="mx-auto text-emerald-500 mb-2" />
               <Text className="block text-[10px] font-black text-emerald-700 uppercase">Flow is Healthy</Text>
               <Text className="text-[9px] text-emerald-600 font-medium">No candidate bottlenecks detected.</Text>
            </div>
          )}
        </div>

        {/* Hiring Health */}
        <div>
          <span className="text-[9px] font-black text-slate-400 uppercase tracking-[0.2em] block mb-4 ml-1">Job Health</span>
          <div className="space-y-5 bg-slate-50/50 p-4 rounded-2xl border border-slate-100">
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <Text className="text-[10px] font-bold text-slate-500 uppercase">Velocity</Text>
                <Text className="text-[10px] font-black text-emerald-600">Optimal</Text>
              </div>
              <div className="h-1.5 w-full bg-slate-200 rounded-full overflow-hidden">
                <div className="h-full bg-emerald-500" style={{ width: '85%' }} />
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <Text className="text-[10px] font-bold text-slate-500 uppercase">Quality Index</Text>
                <Text className="text-[10px] font-black text-indigo-600">8.4 / 10</Text>
              </div>
              <div className="h-1.5 w-full bg-slate-200 rounded-full overflow-hidden">
                <div className="h-full bg-indigo-500" style={{ width: '84%' }} />
              </div>
            </div>
          </div>
        </div>

        {/* Momentum */}
        <div>
          <span className="text-[9px] font-black text-slate-400 uppercase tracking-[0.2em] block mb-4 ml-1">Recent Momentum</span>
          <div className="space-y-3">
             <div className="flex items-center gap-3 p-3 rounded-2xl bg-white border border-slate-100 shadow-soft-sm">
                <div className="h-9 w-9 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600 shadow-sm"><UserPlus size={16} /></div>
                <div>
                   <Text className="block text-[11px] font-black text-slate-800 tracking-tight">+4 New Applications</Text>
                   <Text className="text-[9px] text-slate-400 font-bold uppercase">In the last 24 hours</Text>
                </div>
             </div>
             <div className="flex items-center gap-3 p-3 rounded-2xl bg-white border border-slate-100 shadow-soft-sm">
                <div className="h-9 w-9 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600 shadow-sm"><Zap size={16} /></div>
                <div>
                   <Text className="block text-[11px] font-black text-slate-800 tracking-tight">2 Stage Moves</Text>
                   <Text className="text-[9px] text-slate-400 font-bold uppercase">Trending Upward</Text>
                </div>
             </div>
          </div>
        </div>
      </div>

      <div className="p-4 border-t border-slate-100 bg-white">
        <Button block icon={<Globe size={14} />} className="!h-10 !text-[10px] font-black uppercase tracking-widest border-slate-200 text-slate-600 shadow-soft-sm rounded-xl hover:text-indigo-600 transition-colors">
          Generate Intelligence Report
        </Button>
      </div>
    </div>
  )
}

function OverviewTabContent({ job }: any) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="rounded-2xl border-slate-100 shadow-soft-sm">
           <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Total Pipeline</p>
           <p className="text-2xl font-black text-slate-900">{(job.metadata as any)?.applications_count || 0}</p>
        </Card>
        <Card className="rounded-2xl border-slate-100 shadow-soft-sm">
           <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Interviewing</p>
           <p className="text-2xl font-black text-orange-600">{(job.metadata as any)?.interview || 0}</p>
        </Card>
        <Card className="rounded-2xl border-slate-100 shadow-soft-sm">
           <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Time to Fill</p>
           <p className="text-2xl font-black text-indigo-600">14d</p>
        </Card>
        <Card className="rounded-2xl border-slate-100 shadow-soft-sm">
           <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Fill Index</p>
           <p className="text-2xl font-black text-emerald-600">8.4</p>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card title={<span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Description</span>} className="rounded-2xl border-slate-100 shadow-soft-sm">
            <Paragraph className="text-[13px] text-slate-600 leading-relaxed whitespace-pre-wrap">{job.description || 'No description provided.'}</Paragraph>
          </Card>
        </div>
        <div className="space-y-6">
           <Card title={<span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Core Meta</span>} className="rounded-2xl border-slate-100 shadow-soft-sm">
              <div className="space-y-4">
                 <div className="flex justify-between items-center"><span className="text-[9px] text-slate-400 font-black uppercase tracking-widest">Experience</span><span className="text-xs font-black text-slate-800">{job.experience_min}-{job.experience_max}y</span></div>
                 <div className="flex justify-between items-center"><span className="text-[9px] text-slate-400 font-black uppercase tracking-widest">Comp Bracket</span><span className="text-xs font-black text-indigo-600">{formatSalary(job.salary_min)} - {formatSalary(job.salary_max)}</span></div>
                 <div className="flex justify-between items-center"><span className="text-[9px] text-slate-400 font-black uppercase tracking-widest">Engagement</span><span className="text-xs font-black text-slate-800 uppercase">{job.work_mode?.replace('_', ' ')}</span></div>
              </div>
           </Card>
        </div>
      </div>
    </div>
  )
}
