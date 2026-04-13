import React, { useState } from 'react'
import { Card, Table, Tag, Typography, Button, Modal, message, Spin, Alert, Space, Input, Popconfirm } from 'antd'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { hdcApi } from '@/api/hdc'
import { candidatesApi } from '@/api/candidates'
import { pipelineApi } from '@/api/pipeline'
import { UserCheck, UserX, HelpCircle, CheckCircle2, ShieldAlert } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'

import { useSearchParams } from 'react-router-dom'

const { Text } = Typography

export default function OfferAcceptance() {
  const [selectedRelease, setSelectedRelease] = useState<any>(null)
  const [reason, setReason] = useState('')
  const queryClient = useQueryClient()
  const [searchParams] = useSearchParams()
  const applicationIdFromUrl = searchParams.get('applicationId')
  const user = useAuthStore(state => state.user)

  // Governance logic
  const isGovernanceUser = ['super_admin', 'tenant_admin', 'hr_manager'].includes(user?.role || '')

  // ─── Data Fetching ───
  const { data: releasesData, isLoading: loadingReleases, isError } = useApiQuery(
    ['hdc-offer-releases'],
    () => hdcApi.listOfferReleases()
  )
  const { data: candidatesData } = useApiQuery(['candidates-list'], () => candidatesApi.list())
  const { data: applicationsData } = useApiQuery(['pipeline-applications'], () => pipelineApi.listApplications())

  // ─── Mutations ───
  const acceptMutation = useMutation({
    mutationFn: () =>
      hdcApi.recordCandidateResponse(selectedRelease!.id, { response: 'accepted', reason }),
    onSuccess: () => {
      message.success('Offer acceptance recorded manually')
      setSelectedRelease(null)
      setReason('')
      queryClient.invalidateQueries({ queryKey: ['hdc-offer-releases'] })
      queryClient.invalidateQueries({ queryKey: ['hdc-joining-cases'] })
    },
    onError: () => message.error('Failed to record acceptance'),
  })

  const declineMutation = useMutation({
    mutationFn: () =>
      hdcApi.recordCandidateResponse(selectedRelease!.id, { response: 'declined', reason }),
    onSuccess: () => {
      message.warning('Offer rejection recorded manually')
      setSelectedRelease(null)
      setReason('')
      queryClient.invalidateQueries({ queryKey: ['hdc-offer-releases'] })
    },
    onError: () => message.error('Failed to record decline'),
  })

  const queryMutation = useMutation({
    mutationFn: () =>
      hdcApi.recordCandidateResponse(selectedRelease!.id, { response: 'query', reason }),
    onSuccess: () => {
      message.info('Candidate query recorded')
      setSelectedRelease(null)
      setReason('')
      queryClient.invalidateQueries({ queryKey: ['hdc-offer-releases'] })
    },
    onError: () => message.error('Failed to record query'),
  })

  const handleDecline = () => {
    if (!reason.trim()) {
      return message.error('Please provide a reason for the decline.')
    }
    declineMutation.mutate()
  }

  const releasesRaw = (releasesData as any)?.data || (Array.isArray(releasesData) ? releasesData : [])
  const releases = applicationIdFromUrl 
    ? releasesRaw.filter((r: any) => r.application_id === applicationIdFromUrl)
    : releasesRaw
  const candidates = (candidatesData as any)?.candidates || (candidatesData as any)?.data?.candidates || []
  const applications = (applicationsData as any)?.applications || (applicationsData as any)?.data?.applications || []
  const appById = new Map<string, any>(applications.map((app: any) => [app.id, app]))
  const candidateById = new Map<string, any>(candidates.map((c: any) => [c.id, c]))

  const candidateName = (applicationId: string) =>
    candidateById.get(appById.get(applicationId)?.candidate_id)?.full_name || 'Hiring Candidate'

  const releasedOffers = releases.filter((r: any) => r.status === 'released' || !!r.candidate_response)

  const columns = [
    {
      title: 'Candidate',
      dataIndex: 'application_id',
      key: 'candidate',
      render: candidateName,
    },
    {
      title: 'Offer State',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'released' ? 'blue' : 'green'}>{status?.toUpperCase()}</Tag>
      ),
    },
    {
      title: 'Response',
      dataIndex: 'candidate_response',
      key: 'response',
      render: (r: string) =>
        r ? (
          <Tag color={r === 'accepted' ? 'green' : r === 'declined' ? 'red' : 'orange'}>
            {r.toUpperCase()}
          </Tag>
        ) : (
          <Text className="text-xs text-slate-400">Awaiting</Text>
        ),
    },
    {
      title: 'Action',
      key: 'action',
      render: (_: any, record: any) => (
        <Button
          size="small"
          onClick={() => setSelectedRelease(record)}
          disabled={!!record.candidate_response && record.candidate_response !== 'query'}
        >
          Update Response
        </Button>
      ),
    },
  ]

  if (isError) {
    return <Alert type="error" message="Failed to load offer releases. Please refresh." showIcon className="my-4" />
  }

  const anyPending = acceptMutation.isPending || declineMutation.isPending || queryMutation.isPending

  return (
    <div className="space-y-6">
      <Card
        className="rounded-3xl border-slate-200 shadow-sm"
        title={
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-emerald-500" />
            <span>Candidate Response Tracking</span>
          </div>
        }
      >
        {loadingReleases ? (
          <div className="py-12 text-center"><Spin /></div>
        ) : (
          <Table
            columns={columns}
            dataSource={releasedOffers}
            rowKey="id"
            locale={{ emptyText: <EmptyState title="No offers currently released" /> }}
          />
        )}
      </Card>

      <Modal
        title={
          <div className="flex items-center gap-2">
            <UserCheck size={18} className="text-emerald-500" />
            <span>Record Manual Response: {selectedRelease ? candidateName(selectedRelease.application_id) : ''}</span>
          </div>
        }
        open={!!selectedRelease}
        onCancel={() => { setSelectedRelease(null); setReason('') }}
        footer={[
          <Button
            key="query"
            icon={<HelpCircle size={14} />}
            onClick={() => queryMutation.mutate()}
            loading={queryMutation.isPending}
            disabled={anyPending && !queryMutation.isPending}
          >
            Record Query
          </Button>,
          <Button
            key="reject"
            danger
            icon={<UserX size={14} />}
            onClick={handleDecline}
            loading={declineMutation.isPending}
            disabled={anyPending && !declineMutation.isPending}
          >
            Record Decline
          </Button>,
          <Popconfirm
            key="accept-confirm"
            title="Mark Offer as Accepted?"
            description="You are manually overriding the candidate response. This should only be done if acceptance is confirmed offline."
            onConfirm={() => acceptMutation.mutate()}
            okText="Confirm Acceptance"
            disabled={!isGovernanceUser}
          >
            <Button
              key="accept"
              type="primary"
              icon={<UserCheck size={14} />}
              loading={acceptMutation.isPending}
              disabled={(anyPending && !acceptMutation.isPending) || !isGovernanceUser}
            >
              Record Acceptance
            </Button>
          </Popconfirm>,
        ]}
      >
        <div className="py-4 space-y-4">
          {!isGovernanceUser && (
            <Alert 
              type="info"
              showIcon
              icon={<ShieldAlert size={14} />}
              message="Access Restricted"
              description="Only HR Managers or Admins can manually record offer acceptance. You can record queries or rejections."
              className="rounded-xl border-blue-100"
            />
          )}
          
          <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100">
            <Text className="text-[10px] font-black text-slate-400 uppercase block mb-3 text-center">Mandatory Rationale</Text>
            <Input.TextArea
              placeholder="Explain the context of this manual response (e.g. 'Confirmed via WhatsApp' or 'Declined due to other offer')..."
              rows={4}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="rounded-xl border-slate-200"
            />
          </div>
          
          {selectedRelease?.candidate_response === 'query' && (
            <div className="p-3 bg-amber-50 rounded-xl border border-amber-100">
              <Text className="text-xs text-amber-800 font-bold">
                Follow-up resolved? Update final status below.
              </Text>
            </div>
          )}
        </div>
      </Modal>
    </div>
  )
}

function EmptyState({ title }: { title: string }) {
  return (
    <div className="py-8 text-center">
      <CheckCircle2 className="mx-auto h-12 w-12 text-slate-200" />
      <Text className="mt-2 block font-bold text-slate-400">{title}</Text>
    </div>
  )
}
