import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  Select, Card, Tag, Typography, Spin, Empty, Button,
  Avatar, message, Modal, Input,
  Drawer,
} from 'antd'
import {
  Clock,
  Star,
  X,
  ArrowRight,
  Briefcase,
  Search,
} from 'lucide-react'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)
import {
  DragDropContext,
  Droppable,
  Draggable,
  type DropResult,
} from 'react-beautiful-dnd'
import { useApiQuery } from '@/hooks/useApiQuery'
import { pipelineApi } from '@/api/pipeline'
import { requisitionsApi } from '@/api/jobs'
import { candidatesApi } from '@/api/candidates'
import type {
  PipelineData, PipelineStageData, Application,
  JobRequisition, Candidate,
} from '@/types'
import { cn } from '@/utils/cn'
import ApplicationQuickView from './ApplicationQuickView'
import ApplicationFullView from './ApplicationFullView'

const { Text } = Typography

// ─── Helpers ─────────────────────────────────────────────────────────────────

const STAGE_TYPE_COLOR: Record<string, string> = {
  screening: 'bg-blue-500',
  interview: 'bg-purple-500',
  offer: 'bg-amber-500',
  joined: 'bg-emerald-500',
}

// ─── Application card ─────────────────────────────────────────────────────────

interface AppCardProps {
  application: Application
  index: number
  candidateMap: Map<string, Candidate>
  onShortlist: (app: Application) => void
  onReject: (app: Application) => void
  onMove: (app: Application) => void
  onCardClick: (app: Application) => void
}

function AppCard({ application, index, candidateMap, onShortlist, onReject, onMove, onCardClick }: AppCardProps) {
  const candidate = candidateMap.get(application.candidate_id)
  const displayName = candidate?.full_name || candidate?.email || application.candidate_id.slice(0, 8)
  const daysInStage = dayjs().diff(dayjs(application.updated_at), 'day')

  return (
    <Draggable draggableId={application.id} index={index}>
      {(provided, snapshot) => (
        <div
          ref={provided.innerRef}
          {...provided.draggableProps}
          {...provided.dragHandleProps}
          style={{
            ...provided.draggableProps.style,
            marginBottom: 12,
          }}
        >
          <Card
            size="small"
            bordered={false}
            onClick={() => !snapshot.isDragging && onCardClick(application)}
            className={cn(
              "transition-all duration-200 border border-transparent shadow-soft-sm",
              snapshot.isDragging ? "rotate-2 scale-105 border-blue-200 shadow-soft-lg" : "hover:border-slate-200 hover:shadow-soft-md"
            )}
            styles={{ body: { padding: '12px' } }}
          >
            {/* Candidate name + avatar */}
            <div className="flex items-center gap-2 mb-3">
              <Avatar
                size={32}
                className="bg-blue-100 text-blue-600 shrink-0 font-bold"
              >
                {displayName.charAt(0).toUpperCase()}
              </Avatar>
              <div className="min-w-0">
                <Text className="block font-bold text-slate-900 text-xs leading-tight truncate">
                  {displayName}
                </Text>
                <Text className="text-[10px] text-slate-400 font-medium truncate">
                  {candidate?.current_title || 'No Title'}
                </Text>
              </div>
            </div>

            {/* Meta row */}
            <div className="flex items-center justify-between gap-2 mb-3">
              <div className="flex flex-wrap gap-1">
                {application.match_score !== null && (
                  <Tag className="m-0 border-none bg-emerald-50 text-emerald-700 font-bold text-[9px] uppercase px-1.5 rounded">
                    {application.match_score}% Match
                  </Tag>
                )}
                <Tag className="m-0 border-none bg-slate-100 text-slate-600 font-bold text-[9px] uppercase px-1.5 rounded">
                  {application.status.replace(/_/g, ' ')}
                </Tag>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <Clock className={cn("h-3 w-3", daysInStage > 7 ? "text-rose-500" : "text-slate-300")} />
                <span className={cn("text-[10px] font-bold", daysInStage > 7 ? "text-rose-500" : "text-slate-400")}>
                  {daysInStage}d
                </span>
              </div>
            </div>

            {/* Action buttons */}
            <div
              className="flex items-center gap-1 pt-3 border-t border-slate-100 opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={(e) => e.stopPropagation()}
            >
              <Button
                type="text"
                size="small"
                icon={<Star className="h-3 w-3" />}
                className="flex-1 text-[10px] font-bold text-emerald-600 hover:bg-emerald-50 rounded-md h-7 p-0"
                onClick={() => onShortlist(application)}
              >
                Short
              </Button>
              <Button
                type="text"
                size="small"
                icon={<ArrowRight className="h-3 w-3" />}
                className="flex-1 text-[10px] font-bold text-blue-600 hover:bg-blue-50 rounded-md h-7 p-0"
                onClick={() => onMove(application)}
              >
                Move
              </Button>
              <Button
                type="text"
                size="small"
                danger
                icon={<X className="h-3 w-3" />}
                className="flex-1 text-[10px] font-bold hover:bg-rose-50 rounded-md h-7 p-0"
                onClick={() => onReject(application)}
              >
                Reject
              </Button>
            </div>
          </Card>
        </div>
      )}
    </Draggable>
  )
}

// ─── Pipeline column ──────────────────────────────────────────────────────────

interface StageColumnProps {
  stageData: PipelineStageData
  candidateMap: Map<string, Candidate>
  onShortlist: (app: Application) => void
  onReject: (app: Application) => void
  onMove: (app: Application) => void
  onCardClick: (app: Application) => void
}

function StageColumn({ stageData, candidateMap, onShortlist, onReject, onMove, onCardClick }: StageColumnProps) {
  const dotColor = STAGE_TYPE_COLOR[stageData.stage.stage_type] ?? 'bg-blue-500'

  return (
    <div className="flex flex-col w-72 shrink-0 h-full max-h-full bg-slate-50/50 rounded-2xl border border-slate-200 shadow-soft-sm overflow-hidden">
      {/* Column header */}
      <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-slate-200">
        <div className="flex items-center gap-2">
          <span className={cn("h-2 w-2 rounded-full", dotColor)} />
          <span className="font-bold text-slate-900 text-sm tracking-tight truncate max-w-[160px]">
            {stageData.stage.name}
          </span>
        </div>
        <span className="bg-slate-100 text-slate-600 text-[10px] font-bold px-2 py-0.5 rounded-full ring-1 ring-slate-200">
          {stageData.count}
        </span>
      </div>

      {/* Droppable area */}
      <Droppable droppableId={stageData.stage.id}>
        {(provided, snapshot) => (
          <div
            ref={provided.innerRef}
            {...provided.droppableProps}
            className={cn(
              "flex-1 overflow-y-auto p-3 transition-colors duration-200",
              snapshot.isDraggingOver ? "bg-blue-50/50" : ""
            )}
            style={{ minHeight: '400px' }}
          >
            {stageData.applications.map((app, i) => (
              <AppCard
                key={app.id}
                application={app}
                index={i}
                candidateMap={candidateMap}
                onShortlist={onShortlist}
                onReject={onReject}
                onMove={onMove}
                onCardClick={onCardClick}
              />
            ))}
            {provided.placeholder}
            {stageData.applications.length === 0 && !snapshot.isDraggingOver && (
              <div className="h-20 flex items-center justify-center border-2 border-dashed border-slate-200 rounded-xl">
                <span className="text-[10px] font-bold text-slate-300 uppercase tracking-widest">Empty Stage</span>
              </div>
            )}
          </div>
        )}
      </Droppable>
    </div>
  )
}

// ─── Main board ───────────────────────────────────────────────────────────────

export default function PipelineBoard({ jobId }: { jobId?: string }) {
  const [searchParams, setSearchParams] = useSearchParams()
  const [selectedJobId, setSelectedJobId] = useState<string>(jobId ?? searchParams.get('job') ?? '')
  const [boardState, setBoardState] = useState<Record<string, PipelineStageData>>({})
  const [rejectModal, setRejectModal] = useState<{ open: boolean; app: Application | null }>({ open: false, app: null })
  const [rejectReason, setRejectReason] = useState('')
  const [moveModal, setMoveModal] = useState<{ open: boolean; app: Application | null }>({ open: false, app: null })
  const [moveTargetStage, setMoveTargetStage] = useState('')
  
  const [drawerAppId, setDrawerAppId] = useState<string | null>(null)
  const [fullViewOpen, setFullViewOpen] = useState(false)

  // Fetch all requisitions for the selector
  const { data: jobsData } = useApiQuery(
    ['jobs'],
    () => requisitionsApi.list()
  )
  const jobs: JobRequisition[] =
    (jobsData as { requisitions: JobRequisition[] } | undefined)?.requisitions ?? []

  // Fetch pipeline for selected job
  const { data: pipelineData, isLoading: pipelineLoading } = useApiQuery(
    ['pipeline', selectedJobId],
    () => pipelineApi.getPipeline(selectedJobId),
    { enabled: !!selectedJobId }
  )

  // Fetch all candidates for name lookup
  const { data: candidatesData } = useApiQuery(
    ['candidates', 'all'],
    () => candidatesApi.list()
  )
  const candidateMap = new Map<string, Candidate>(
    ((candidatesData as { candidates: Candidate[] } | undefined)?.candidates ?? []).map((c) => [c.id, c])
  )

  // Sync pipeline data into local board state
  useEffect(() => {
    const pd = pipelineData as PipelineData | undefined
    if (pd?.pipeline) {
      setBoardState(pd.pipeline)
    }
  }, [pipelineData])

  // Sync prop changes
  useEffect(() => {
    if (jobId) {
      setSelectedJobId(jobId)
    }
  }, [jobId])

  // Keep URL in sync
  useEffect(() => {
    if (selectedJobId && !jobId) {
      setSearchParams({ job: selectedJobId }, { replace: true })
    }
  }, [selectedJobId, setSearchParams, jobId])

  const orderedStages = Object.values(boardState).sort(
    (a, b) => a.stage.stage_order - b.stage.stage_order
  )

  // ── Drag end handler ──────────────────────────────────────────────────────
  const handleDragEnd = async (result: DropResult) => {
    const { source, destination, draggableId } = result
    if (!destination || source.droppableId === destination.droppableId) return

    const fromStageId = source.droppableId
    const toStageId = destination.droppableId

    // Optimistic update
    const newBoard = { ...boardState }
    const fromStage = {
      ...newBoard[fromStageId],
      applications: [...newBoard[fromStageId].applications],
    }
    const toStage = {
      ...newBoard[toStageId],
      applications: [...newBoard[toStageId].applications],
    }

    const [movedApp] = fromStage.applications.splice(source.index, 1)
    toStage.applications.splice(destination.index, 0, {
      ...movedApp,
      current_stage_id: toStageId,
    })

    newBoard[fromStageId] = { ...fromStage, count: fromStage.count - 1 }
    newBoard[toStageId] = { ...toStage, count: toStage.count + 1 }
    setBoardState(newBoard)

    try {
      await pipelineApi.moveStage(draggableId, toStageId)
    } catch {
      // Rollback
      setBoardState(boardState)
      message.error('Failed to move application')
    }
  }

  // ── Shortlist ─────────────────────────────────────────────────────────────
  const handleShortlist = async (app: Application) => {
    try {
      await pipelineApi.shortlist(app.id)
      message.success('Application shortlisted')
      // Update local status
      const newBoard = { ...boardState }
      const col = { ...newBoard[app.current_stage_id!] }
      col.applications = col.applications.map((a) =>
        a.id === app.id ? { ...a, status: 'shortlisted' as const } : a
      )
      newBoard[app.current_stage_id!] = col
      setBoardState(newBoard)
    } catch {
      message.error('Failed to shortlist')
    }
  }

  // ── Reject ────────────────────────────────────────────────────────────────
  const handleRejectConfirm = async () => {
    if (!rejectModal.app) return
    try {
      await pipelineApi.reject(rejectModal.app.id, rejectReason)
      message.success('Application rejected')
      // Remove from board
      const app = rejectModal.app
      const stageId = app.current_stage_id!
      const newBoard = { ...boardState }
      newBoard[stageId] = {
        ...newBoard[stageId],
        applications: newBoard[stageId].applications.filter((a) => a.id !== app.id),
        count: newBoard[stageId].count - 1,
      }
      setBoardState(newBoard)
    } catch {
      message.error('Failed to reject application')
    } finally {
      setRejectModal({ open: false, app: null })
      setRejectReason('')
    }
  }

  // ── Move stage ────────────────────────────────────────────────────────────
  const handleMoveConfirm = async () => {
    if (!moveModal.app || !moveTargetStage) return
    const app = moveModal.app
    const fromStageId = app.current_stage_id!
    const toStageId = moveTargetStage

    if (fromStageId === toStageId) {
      setMoveModal({ open: false, app: null })
      return
    }

    const newBoard = { ...boardState }
    const fromStage = { ...newBoard[fromStageId], applications: [...newBoard[fromStageId].applications] }
    const toStage = { ...newBoard[toStageId], applications: [...newBoard[toStageId].applications] }

    const idx = fromStage.applications.findIndex((a) => a.id === app.id)
    const [movedApp] = fromStage.applications.splice(idx, 1)
    toStage.applications.push({ ...movedApp, current_stage_id: toStageId })

    newBoard[fromStageId] = { ...fromStage, count: fromStage.count - 1 }
    newBoard[toStageId] = { ...toStage, count: toStage.count + 1 }
    setBoardState(newBoard)

    try {
      await pipelineApi.moveStage(app.id, toStageId)
      message.success('Application moved')
    } catch {
      setBoardState(boardState)
      message.error('Failed to move application')
    } finally {
      setMoveModal({ open: false, app: null })
      setMoveTargetStage('')
    }
  }

  const closeQuickView = () => {
    setDrawerAppId(null)
    setFullViewOpen(false)
  }

  return (
    <div className="space-y-6 h-full flex flex-col">
      {/* ── Header ────────────────────────────────────────────────────────── */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between shrink-0">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Pipeline Board</h1>
          {selectedJobId && (
            <p className="text-slate-500 mt-1">
              {(pipelineData as PipelineData | undefined)?.total_applications ?? 0} active applications for this role.
            </p>
          )}
        </div>
        <div className="flex items-center gap-3">
          <Select
            className="w-72 h-10"
            placeholder="Select a job to view pipeline…"
            value={selectedJobId || undefined}
            onChange={(val) => setSelectedJobId(val)}
            showSearch
            optionFilterProp="label"
            options={jobs.map((j) => ({ value: j.id, label: j.title }))}
          />
          {selectedJobId && (
            <Button 
              className="h-10 flex items-center gap-2 font-medium"
              icon={<Briefcase className="h-4 w-4" />}
              onClick={() => {
                // Should open JobFullView instead? Or keep navigate for now.
                // Re-enabling detailId logic in JobsList would be better.
              }}
            >
              View Job
            </Button>
          )}
        </div>
      </div>

      {/* ── Board ─────────────────────────────────────────────────────────── */}
      <div className="flex-1 min-h-0 overflow-hidden">
        {!selectedJobId ? (
          <Card bordered={false} className="h-full flex items-center justify-center shadow-soft-sm">
            <Empty
              description={<span className="text-slate-400 font-medium">Select a job above to view its recruitment pipeline</span>}
              image={<Search className="h-12 w-12 text-slate-200 mx-auto mb-4" />}
            />
          </Card>
        ) : pipelineLoading ? (
          <div className="h-full flex items-center justify-center">
            <Spin size="large" />
          </div>
        ) : orderedStages.length === 0 ? (
          <Empty description="No pipeline stages found for this job" />
        ) : (
          <DragDropContext onDragEnd={handleDragEnd}>
            <div className="flex gap-6 h-full overflow-x-auto pb-4 items-start">
              {orderedStages.map((stageData) => (
                <StageColumn
                  key={stageData.stage.id}
                  stageData={stageData}
                  candidateMap={candidateMap}
                  onShortlist={handleShortlist}
                  onReject={(app) => setRejectModal({ open: true, app })}
                  onMove={(app) => { setMoveModal({ open: true, app }); setMoveTargetStage('') }}
                  onCardClick={(app) => setDrawerAppId(app.id)}
                />
              ))}
            </div>
          </DragDropContext>
        )}
      </div>

      {/* ── Reject modal ──────────────────────────────────────────────────── */}
      <Modal
        title="Reject Application"
        open={rejectModal.open}
        onCancel={() => { setRejectModal({ open: false, app: null }); setRejectReason('') }}
        onOk={handleRejectConfirm}
        okText="Reject"
        okButtonProps={{ danger: true }}
        className="rounded-2xl overflow-hidden"
      >
        <Text type="secondary">Provide an optional reason for rejecting this application:</Text>
        <Input.TextArea
          className="mt-4 rounded-xl"
          rows={3}
          value={rejectReason}
          onChange={(e) => setRejectReason(e.target.value)}
          placeholder="e.g. Doesn't meet minimum experience requirements"
        />
      </Modal>

      {/* ── Move stage modal ───────────────────────────────────────────────── */}
      <Modal
        title="Move to Stage"
        open={moveModal.open}
        onCancel={() => setMoveModal({ open: false, app: null })}
        onOk={handleMoveConfirm}
        okText="Move Application"
        okButtonProps={{ disabled: !moveTargetStage }}
        className="rounded-2xl overflow-hidden"
      >
        <Text className="block mb-4 text-slate-500 font-medium">
          Select the stage to move this application to:
        </Text>
        <Select
          className="w-full h-10"
          placeholder="Select target stage…"
          value={moveTargetStage || undefined}
          onChange={setMoveTargetStage}
          options={orderedStages
            .filter((s) => s.stage.id !== moveModal.app?.current_stage_id)
            .map((s) => ({ value: s.stage.id, label: s.stage.name }))}
        />
      </Modal>

      {/* Level 1: Quick View Drawer */}
      <Drawer
        title={null}
        open={!!drawerAppId}
        onClose={closeQuickView}
        width={480}
        styles={{ body: { padding: '32px 24px' } }}
        destroyOnClose
        closeIcon={null}
        push={{ distance: 480 }}
      >
        {drawerAppId && (
          <>
            <ApplicationQuickView
              applicationId={drawerAppId}
              onClose={closeQuickView}
              onOpenFullView={() => setFullViewOpen(true)}
              onShortlist={() => { /* shortlist logic already in handleShortlist */ }}
            />

            {/* Level 2: Full View Drawer */}
            <Drawer
              title={null}
              open={fullViewOpen}
              onClose={() => setFullViewOpen(false)}
              width={900}
              styles={{ body: { padding: '40px' } }}
              destroyOnClose
              closeIcon={null}
            >
              <ApplicationFullView applicationId={drawerAppId} />
            </Drawer>
          </>
        )}
      </Drawer>
    </div>
  )
}
