import React, { useEffect, useState } from 'react'
import { Card, Table, Tag, Typography, Button, Modal, message, Spin, Alert, Space, Popconfirm } from 'antd'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { hdcApi } from '@/api/hdc'
import { candidatesApi } from '@/api/candidates'
import { pipelineApi } from '@/api/pipeline'
import { Send, FileText, Mail, ShieldCheck, User } from 'lucide-react'
import { useNavigate, useSearchParams } from 'react-router-dom'

const { Text } = Typography

export default function OfferRelease() {
  const [releaseModal, setReleaseModal] = useState<any>(null)
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  // ─── Data Fetching ───
  const { data: releasesData, isLoading: loadingReleases, isError } = useApiQuery(
    ['hdc-offer-releases'],
    () => hdcApi.listOfferReleases()
  )
  const { data: candidatesData } = useApiQuery(['candidates-list'], () => candidatesApi.list())
  const { data: applicationsData } = useApiQuery(['pipeline-applications'], () => pipelineApi.listApplications())

  // ─── Mutations ───
  const releaseMutation = useMutation({
    mutationFn: (id: string) => hdcApi.releaseOffer(id),
    onSuccess: () => {
      message.success('Offer packet dispatched to candidate')
      setReleaseModal(null)
      queryClient.invalidateQueries({ queryKey: ['hdc-offer-releases'] })
    },
    onError: () => message.error('Failed to dispatch offer'),
  })
  const freezeMutation = useMutation({
    mutationFn: (id: string) => hdcApi.freezeOffer(id),
    onSuccess: () => {
      message.success('Offer packet frozen')
      queryClient.invalidateQueries({ queryKey: ['hdc-offer-releases'] })
    },
    onError: () => message.error('Failed to freeze offer packet'),
  })

  const releasesRaw = (releasesData as any)?.data || (Array.isArray(releasesData) ? releasesData : [])
  const applicationIdFromUrl = searchParams.get('applicationId')
  const releases = applicationIdFromUrl 
    ? releasesRaw.filter((r: any) => r.application_id === applicationIdFromUrl)
    : releasesRaw
  const candidates = (candidatesData as any)?.candidates || (candidatesData as any)?.data?.candidates || []
  const applications = (applicationsData as any)?.applications || (applicationsData as any)?.data?.applications || []
  const appById = new Map<string, any>(applications.map((app: any) => [app.id, app]))
  const candidateById = new Map<string, any>(candidates.map((c: any) => [c.id, c]))

  const candidateName = (applicationId: string) =>
    candidateById.get(appById.get(applicationId)?.candidate_id)?.full_name || 'Hiring Candidate'

  useEffect(() => {
    const releaseId = searchParams.get('releaseId')
    if (!releaseId || !releases.length) return
    const target = releases.find((item: any) => item.id === releaseId)
    if (target) {
      setReleaseModal(target)
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev)
        next.delete('releaseId')
        return next
      }, { replace: true })
    }
  }, [releases, searchParams, setSearchParams])

  const columns = [
    {
      title: 'Candidate',
      dataIndex: 'application_id',
      key: 'candidate',
      render: (applicationId: string) => (
        <Space>
           <User size={14} className="text-slate-400" />
           <Text strong className="text-sm">
             {candidateName(applicationId)}
           </Text>
        </Space>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'accepted' ? 'green' : status === 'released' ? 'blue' : 'orange'} className="rounded-md font-black text-[9px] uppercase border-none px-2">
          {status}
        </Tag>
      ),
    },
    {
      title: 'Action',
      key: 'action',
      align: 'right' as const,
      render: (_: any, record: any) => (
        <Space>
          <Button
            size="small"
            onClick={() => freezeMutation.mutate(record.id)}
            disabled={record.status === 'frozen' || record.status === 'released' || record.status === 'accepted' || record.status === 'declined'}
            loading={freezeMutation.isPending}
            className="rounded-lg h-7 text-[10px] font-bold uppercase tracking-widest"
          >
            Freeze
          </Button>
          <Popconfirm
            title="Dispatch Offer Packet?"
            description="This will send the formal offer to the candidate and mark it as released."
            onConfirm={() => releaseMutation.mutate(record.id)}
            okText="Yes, Dispatch"
            cancelText="Not Yet"
            disabled={record.status === 'released' || record.status === 'accepted' || record.status === 'declined'}
          >
            <Button
              type="primary"
              size="small"
              icon={<Send size={12} className="mr-1" />}
              disabled={record.status === 'released' || record.status === 'accepted' || record.status === 'declined'}
              loading={releaseMutation.isPending && releaseModal?.id === record.id}
              className="rounded-lg h-7 text-[10px] font-bold uppercase tracking-widest"
            >
              Dispatch
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  if (isError) {
    return <Alert type="error" message="Failed to load offer releases. Please refresh." showIcon className="my-4" />
  }

  return (
    <div className="space-y-6">
      <Card
        className="rounded-[2.5rem] border-slate-200 shadow-sm"
        title={
          <div className="flex items-center gap-2 py-2">
            <div className="p-2 bg-emerald-50 rounded-xl text-emerald-600"><Mail size={18} /></div>
            <div>
              <div className="text-[10px] font-black uppercase tracking-widest text-slate-400 leading-none mb-1">Final Dispatch</div>
              <div className="text-base font-black text-slate-800 leading-none">Offer Release Console</div>
            </div>
          </div>
        }
      >
        {loadingReleases ? (
          <div className="py-20 text-center"><Spin tip="Preparing offer list..." /></div>
        ) : (
          <div className="overflow-x-auto">
            <Table
              columns={columns}
              dataSource={releases}
              rowKey="id"
              pagination={{ pageSize: 10, size: 'small' }}
              locale={{ 
                emptyText: (
                  <div className="py-16 text-center flex flex-col items-center gap-4">
                    <FileText size={48} className="text-slate-100" />
                    <div>
                      <Text className="block font-black text-slate-400 uppercase tracking-widest text-[10px]">No offers ready for release</Text>
                      {applicationIdFromUrl && (
                         <Button 
                          type="link" 
                          size="small" 
                          className="text-[10px] font-black uppercase mt-2 text-indigo-500"
                          onClick={() => navigate('/hiring-decisions/offer-release')}
                        >
                          View All Offers
                        </Button>
                      )}
                    </div>
                  </div>
                )
              }}
            />
          </div>
        )}
      </Card>

      <Modal
        title={`Dispatch Offer: ${releaseModal ? candidateName(releaseModal.application_id) : ''}`}
        open={!!releaseModal}
        onCancel={() => setReleaseModal(null)}
        onOk={() => releaseMutation.mutate(releaseModal.id)}
        confirmLoading={releaseMutation.isPending}
        okText="Dispatch Now"
      >
        <div className="py-4 space-y-4">
          <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100">
            <Text className="text-[10px] font-black text-slate-400 uppercase block mb-2">Release Reference</Text>
            <Text className="font-mono text-xs text-slate-700">{releaseModal?.id}</Text>
          </div>
          <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100">
            <Text className="text-[10px] font-black text-slate-400 uppercase block mb-2">Current Status</Text>
            <Tag color="cyan">{releaseModal?.status?.toUpperCase()}</Tag>
          </div>
          <Text className="text-xs text-slate-500 block">
            Dispatching will send the offer packet to the candidate's registered email and transition the status to <strong>released</strong>.
          </Text>
        </div>
      </Modal>
    </div>
  )
}
