import React, { useState } from 'react'
import {
  Button, Card, Typography, Space, Tag, Empty, Spin, message, Modal, List, Badge, Divider
} from 'antd'
import {
  Settings, Zap, CheckCircle2, AlertCircle, Trash2, Link, Plus, 
  ChevronRight, ArrowRight, ShieldCheck, Clock, FileText, UserCheck, Lock
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useApiQuery } from '@/hooks/useApiQuery'
import { interviewsApi } from '@/api/interviews'
import { useQueryClient } from '@tanstack/react-query'
import type { InterviewPackageBinding, InterviewPackage, InterviewRoundConfig } from '@/types'
import { cn } from '@/utils/cn'

const { Title, Text, Paragraph } = Typography

interface InterviewsTabProps {
  jobId: string
  isOwner?: boolean
}

export default function JobInterviewsTab({ jobId, isOwner }: InterviewsTabProps) {
  const { t } = useTranslation(['pipeline', 'common'])
  const queryClient = useQueryClient()
  const [attachModalOpen, setAttachModalOpen] = useState(false)
  const [unbinding, setUnbinding] = useState(false)

  const { data: bindingData, isLoading: bindingLoading } = useApiQuery(
    ['job-interview-binding', jobId],
    () => interviewsApi.getJobBinding(jobId)
  )

  const { data: packagesData } = useApiQuery(
    ['interview-packages-available'],
    () => interviewsApi.listPackages({ is_active: true }),
    { enabled: attachModalOpen }
  )

  const binding = (bindingData as any)?.data?.binding as InterviewPackageBinding | null
  const packages = (packagesData as any)?.data?.packages || []

  const handleBind = async (packageId: string) => {
    if (!isOwner) return
    try {
      await interviewsApi.bindToJob(jobId, packageId)
      message.success('Interview package attached to job')
      setAttachModalOpen(false)
      queryClient.invalidateQueries({ queryKey: ['job-interview-binding', jobId] })
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to attach package')
    }
  }

  const handleUnbind = async () => {
    if (!isOwner) return
    setUnbinding(true)
    try {
      await interviewsApi.unbindFromJob(jobId)
      message.success('Interview package removed from job')
      queryClient.invalidateQueries({ queryKey: ['job-interview-binding', jobId] })
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to remove package')
    } finally {
      setUnbinding(false)
    }
  }

  if (bindingLoading) return <div className="p-20 text-center"><Spin size="large" /></div>

  if (!binding) {
    return (
      <Card bordered={false} className="shadow-soft-sm py-16">
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <div className="space-y-2">
              <Title level={4} className="!m-0 text-slate-800">No Interview Package Attached</Title>
              <Text className="text-slate-500">Define how candidates should be evaluated for this role.</Text>
            </div>
          }
        >
          <Button 
            type="primary" 
            size="large" 
            className="bg-indigo-600 border-none font-bold h-12 rounded-xl mt-4 px-8"
            icon={<Plus className="h-4 w-4 mr-2" />}
            onClick={() => setAttachModalOpen(true)}
            disabled={!isOwner}
          >
            Attach Interview Package
          </Button>
          {!isOwner && (
            <p className="mt-4 text-[10px] text-slate-400 font-bold uppercase tracking-widest flex items-center justify-center gap-1">
              <Lock size={10} /> {t('pipeline:ownership.restricted')}
            </p>
          )}
        </Empty>

        <AttachPackageModal 
          open={attachModalOpen} 
          packages={packages} 
          onClose={() => setAttachModalOpen(false)} 
          onSelect={handleBind} 
        />
      </Card>
    )
  }

  return (
    <div className="space-y-6 pb-20">
      {/* Package Header */}
      <Card bordered={false} className="shadow-soft-sm bg-slate-900 border-none overflow-hidden relative">
        <div className="absolute top-[-20px] right-[-20px] opacity-10">
          <Settings size={120} className="text-white" />
        </div>
        <div className="flex items-center justify-between relative z-10">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-2xl bg-white/10 flex items-center justify-center text-white">
              <ShieldCheck size={24} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <Title level={4} className="!m-0 !text-white tracking-tight">{binding.package_title}</Title>
                <Tag className="m-0 border-none bg-indigo-500 text-white font-bold text-[9px] uppercase px-2 rounded">Active Package</Tag>
              </div>
              <Text className="text-indigo-200 text-xs">Attached on {new Date(binding.created_at).toLocaleDateString()}</Text>
            </div>
          </div>
          <Space>
            <Button 
              ghost 
              className="border-white/20 text-white hover:!text-white hover:!border-white font-bold"
              icon={<Trash2 size={14} />}
              loading={unbinding}
              onClick={handleUnbind}
              disabled={!isOwner}
            >
              Unbind
            </Button>
            <Button 
              type="primary" 
              className="bg-indigo-500 border-none font-bold"
              icon={<Settings size={14} />}
              disabled={!isOwner}
            >
              Edit Settings
            </Button>
          </Space>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Rounds List */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between px-2">
            <Title level={5} className="!m-0 text-[11px] uppercase tracking-widest text-slate-400 font-black">Interview Rounds</Title>
            <Text className="text-[10px] text-slate-400 font-bold uppercase">{binding.rounds_summary.length} Rounds Defined</Text>
          </div>
          
          <div className="space-y-3">
            {binding.rounds_summary.map((round, idx) => (
              <RoundConfigCard key={round.id} round={round} index={idx} />
            ))}
          </div>
        </div>

        {/* Automation & Thresholds */}
        <div className="space-y-6">
          <Card 
            title={
              <div className="flex items-center gap-2">
                <Zap size={14} className="text-amber-500" />
                <span className="text-[11px] uppercase tracking-widest text-slate-500 font-black">Automation Settings</span>
              </div>
            }
            bordered={false} 
            className="shadow-soft-sm"
          >
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Text className="text-xs font-bold text-slate-600">Auto-movement Enabled</Text>
                <Badge status={binding.automation_enabled ? "success" : "default"} text={binding.automation_enabled ? "ON" : "OFF"} />
              </div>
              <Divider className="my-0" />
              <div className="space-y-2">
                <div className="flex items-start gap-2">
                  <CheckCircle2 size={12} className="text-emerald-500 mt-0.5" />
                  <div className="min-w-0">
                    <Text className="block text-[11px] font-bold text-slate-700">Threshold Compliance</Text>
                    <Text className="text-[10px] text-slate-400">Rounds with auto-pass will move candidates to next stage if threshold met.</Text>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <AlertCircle size={12} className="text-amber-500 mt-0.5" />
                  <div className="min-w-0">
                    <Text className="block text-[11px] font-bold text-slate-700">Manual Review Zones</Text>
                    <Text className="text-[10px] text-slate-400">Scores within review bands will pause automation for evaluator decision.</Text>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          <Card 
            title={
              <div className="flex items-center gap-2">
                <UserCheck size={14} className="text-blue-500" />
                <span className="text-[11px] uppercase tracking-widest text-slate-500 font-black">Evaluation Rules</span>
              </div>
            }
            bordered={false} 
            className="shadow-soft-sm"
          >
            <div className="space-y-3">
              <div className="p-3 bg-blue-50 rounded-xl border border-blue-100">
                <Text className="block text-[10px] font-bold text-blue-800 uppercase tracking-widest mb-1">Pass Rule</Text>
                <Text className="text-xs font-medium text-blue-700">Candidate score must be &ge; Threshold to move forward.</Text>
              </div>
              <div className="p-3 bg-rose-50 rounded-xl border border-rose-100">
                <Text className="block text-[10px] font-bold text-rose-800 uppercase tracking-widest mb-1">Reject Rule</Text>
                <Text className="text-xs font-medium text-rose-700">Candidates with &lt; 40% in any round are auto-disqualified.</Text>
              </div>
            </div>
          </Card>
        </div>
      </div>

      <AttachPackageModal 
        open={attachModalOpen} 
        packages={packages} 
        onClose={() => setAttachModalOpen(false)} 
        onSelect={handleBind} 
      />
    </div>
  )
}

function RoundConfigCard({ round, index }: { round: InterviewRoundConfig, index: number }) {
  return (
    <Card bordered={false} className="shadow-soft-sm hover:shadow-soft-md transition-shadow border border-slate-50 overflow-hidden" bodyStyle={{ padding: 0 }}>
      <div className="flex items-stretch">
        <div className="w-12 bg-slate-50 flex items-center justify-center font-black text-slate-300 border-r border-slate-100">
          {index + 1}
        </div>
        <div className="flex-1 p-4">
          <div className="flex items-start justify-between">
            <div className="min-w-0">
              <Title level={5} className="!m-0 !text-sm text-slate-900 leading-tight truncate">{round.name}</Title>
              <div className="flex items-center gap-3 mt-1.5">
                <Text className="text-[10px] text-slate-400 font-bold uppercase flex items-center gap-1">
                  <FileText size={10} /> {round.type.replace('_', ' ')}
                </Text>
                <Text className="text-[10px] text-slate-400 font-bold uppercase flex items-center gap-1">
                  <UserCheck size={10} /> {round.evaluator_type.replace('_', ' ')}
                </Text>
              </div>
            </div>
            <div className="text-right">
              <div className="flex items-center gap-1 justify-end">
                <Zap size={10} className={cn("text-slate-300", round.auto_pass_enabled && "text-amber-500")} />
                <Text className="text-[11px] font-bold text-slate-700">Threshold: {round.threshold_score}%</Text>
              </div>
              <Tag className="m-0 mt-1 border-none bg-slate-100 text-slate-500 font-bold text-[8px] uppercase px-1.5 rounded">
                {round.manual_review_required ? "Review Required" : "Auto-Action Enabled"}
              </Tag>
            </div>
          </div>
          
          {round.threshold_rules && round.threshold_rules.length > 0 && (
            <div className="mt-4 pt-3 border-t border-slate-50 flex flex-wrap gap-2">
              {round.threshold_rules.map((rule, idx) => (
                <Tag 
                  key={idx} 
                  className="m-0 border-none bg-slate-50 text-[9px] font-bold text-slate-500 py-0.5 px-2 rounded-md"
                >
                  {rule.min_score}&ndash;{rule.max_score}%: <span className={cn(
                    rule.action === 'pass' ? "text-emerald-600" : 
                    rule.action === 'reject' ? "text-rose-600" : "text-amber-600"
                  )}>{rule.action.replace('_', ' ').toUpperCase()}</span>
                </Tag>
              ))}
            </div>
          )}
        </div>
        <div className="w-10 flex items-center justify-center border-l border-slate-50 hover:bg-slate-50 cursor-pointer">
          <ChevronRight size={16} className="text-slate-300" />
        </div>
      </div>
    </Card>
  )
}

function AttachPackageModal({ open, packages, onClose, onSelect }: { 
  open: boolean, 
  packages: InterviewPackage[], 
  onClose: () => void,
  onSelect: (id: string) => void
}) {
  return (
    <Modal
      title="Attach Interview Package"
      open={open}
      onCancel={onClose}
      footer={null}
      width={600}
      className="modern-modal"
    >
      <div className="py-4 space-y-3">
        {packages.map(pkg => (
          <div 
            key={pkg.id} 
            className="group p-4 bg-white rounded-2xl border border-slate-100 hover:border-indigo-200 hover:bg-indigo-50/30 transition-all cursor-pointer"
            onClick={() => onSelect(pkg.id)}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-xl bg-indigo-50 group-hover:bg-indigo-100 text-indigo-600 flex items-center justify-center">
                  <ShieldCheck size={20} />
                </div>
                <div>
                  <Title level={5} className="!m-0 !text-sm text-slate-900">{pkg.title}</Title>
                  <Text className="text-xs text-slate-500">{pkg.rounds.length} Rounds &bull; {pkg.description || 'Standard evaluation'}</Text>
                </div>
              </div>
              <ArrowRight size={16} className="text-slate-300 group-hover:text-indigo-600 group-hover:translate-x-1 transition-all" />
            </div>
          </div>
        ))}
        {packages.length === 0 && (
          <div className="py-10 text-center">
            <Text className="text-slate-400 italic">No active interview templates found.</Text>
          </div>
        )}
        <Divider className="my-4">
          <Text className="text-[10px] text-slate-400 font-bold uppercase">OR</Text>
        </Divider>
        <Button 
          block 
          size="large" 
          className="h-12 rounded-xl border-dashed border-slate-300 text-slate-500 hover:!border-indigo-400 hover:!text-indigo-600 font-bold"
          icon={<Plus size={16} className="mr-2" />}
        >
          Create New Package Template
        </Button>
      </div>
    </Modal>
  )
}
