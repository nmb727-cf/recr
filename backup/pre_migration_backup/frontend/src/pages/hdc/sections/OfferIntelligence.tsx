import React, { useState } from 'react'
import { Card, Table, Tag, Typography, Button, message, Spin, Alert } from 'antd'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { hdcApi } from '@/api/hdc'
import { candidatesApi } from '@/api/candidates'
import { pipelineApi } from '@/api/pipeline'
import { Brain, Zap, CheckCircle2 } from 'lucide-react'

import { useNavigate, useSearchParams } from 'react-router-dom'

const { Text } = Typography

export default function OfferIntelligence() {
  const [selectedScenarioId, setSelectedScenarioId] = useState<string | null>(null)
  const [activeRecommendationId, setActiveRecommendationId] = useState<string | null>(null)
  const queryClient = useQueryClient()
  const [searchParams] = useSearchParams()
  const applicationIdFromUrl = searchParams.get('applicationId')

  const { data: recommendationsData, isLoading: loadingRecs, isError } = useApiQuery(
    ['hdc-offer-recommendations'],
    () => hdcApi.listOfferRecommendations()
  )
  const { data: candidatesData } = useApiQuery(['candidates-list'], () => candidatesApi.list())
  const { data: applicationsData } = useApiQuery(['pipeline-applications'], () => pipelineApi.listApplications())

  const selectMutation = useMutation({
    mutationFn: ({ id, scenarioId }: any) => hdcApi.selectScenario(id, scenarioId),
    onSuccess: () => {
      message.success('Offer scenario selected and locked')
      queryClient.invalidateQueries({ queryKey: ['hdc-offer-recommendations'] })
      setActiveRecommendationId(null)
      setSelectedScenarioId(null)
    },
    onError: () => message.error('Failed to lock scenario'),
  })

  let recommendations = (recommendationsData as any)?.data || (Array.isArray(recommendationsData) ? recommendationsData : [])
  if (applicationIdFromUrl) {
    recommendations = recommendations.filter((r: any) => r.application_id === applicationIdFromUrl)
  }
  const candidates = (candidatesData as any)?.candidates || (candidatesData as any)?.data?.candidates || []
  const applications = (applicationsData as any)?.applications || (applicationsData as any)?.data?.applications || []

  const activeRec = recommendations.find((r: any) => r.id === activeRecommendationId)
  const applicationById = new Map<string, any>(applications.map((app: any) => [app.id, app]))

  const columns = [
    {
      title: 'Candidate',
      dataIndex: 'application_id',
      key: 'candidate',
      render: (applicationId: string) => {
        const app = applicationById.get(applicationId)
        return candidates.find((c: any) => c.id === app?.candidate_id)?.full_name || 'Hiring Candidate'
      },
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'recommended' ? 'green' : 'blue'}>{status?.toUpperCase()}</Tag>
      ),
    },
    {
      title: 'Scenarios',
      dataIndex: 'scenarios',
      key: 'scenarios',
      render: (list: any[]) => <Text className="text-xs">{list?.length || 0} AI Scenarios</Text>,
    },
    {
      title: 'Action',
      key: 'action',
      render: (_: any, record: any) => (
        <Button
          size="small"
          type="primary"
          onClick={() => {
            setActiveRecommendationId(record.id)
            setSelectedScenarioId(record.selected_scenario_id || null)
          }}
          disabled={record.status === 'recommended'}
        >
          Select Scenario
        </Button>
      ),
    },
  ]

  if (isError) {
    return <Alert type="error" message="Failed to load offer recommendations. Please refresh." showIcon className="my-4" />
  }

  return (
    <div className="space-y-6">
      <Card
        className="rounded-3xl border-slate-200 shadow-sm"
        title={
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-purple-500" />
            <span>Offer Intelligence Modeling</span>
          </div>
        }
      >
        {loadingRecs ? (
          <div className="py-20 text-center"><Spin tip="Loading modeling data..." /></div>
        ) : (
          <div className="overflow-x-auto">
            <Table
              columns={columns}
              dataSource={recommendations}
              rowKey="id"
              pagination={{ pageSize: 5, size: 'small' }}
              locale={{ 
                emptyText: (
                  <div className="py-16 text-center flex flex-col items-center gap-4">
                    <Brain size={48} className="text-slate-100" />
                    <div>
                      <Text className="block font-black text-slate-400 uppercase tracking-widest text-[10px]">No active modeling found</Text>
                      {applicationIdFromUrl && (
                         <Button 
                          type="link" 
                          size="small" 
                          className="text-[10px] font-black uppercase mt-2 text-indigo-500"
                          onClick={() => navigate('/hiring-decisions/offer-intelligence')}
                        >
                          View All Recommendations
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

      {activeRec && (
        <Card
          className="rounded-3xl border-purple-200 bg-purple-50/10 shadow-lg"
          title={`Scenarios for ${
            candidates.find((c: any) => c.id === applicationById.get(activeRec.application_id)?.candidate_id)?.full_name || 'Candidate'
          }`}
          extra={
            <Button
              type="primary"
              disabled={!selectedScenarioId}
              loading={selectMutation.isPending}
              onClick={() => selectMutation.mutate({ id: activeRec.id, scenarioId: selectedScenarioId })}
            >
              Lock Selection
            </Button>
          }
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {activeRec.scenarios?.map((s: any) => (
              <div
                key={s.id}
                onClick={() => setSelectedScenarioId(s.id)}
                className={`p-6 rounded-[2rem] border-2 cursor-pointer transition-all ${
                  selectedScenarioId === s.id
                    ? 'border-purple-500 bg-white shadow-xl'
                    : 'border-slate-100 bg-white/50 hover:border-purple-200'
                }`}
              >
                <div className="flex justify-between items-start mb-4">
                  <Text className="text-sm font-black text-slate-800 uppercase">{s.name}</Text>
                  {selectedScenarioId === s.id && <CheckCircle2 size={20} className="text-purple-500" />}
                </div>
                <Text className="text-3xl font-black text-slate-900 block leading-none mb-2">
                  ₹ {s.ctc_amount?.toLocaleString()}
                </Text>
                <Tag className="m-0 border-none bg-slate-900 text-white text-[9px] font-black uppercase rounded-full px-2">
                  {s.market_position}
                </Tag>
                <div className="mt-6 space-y-3">
                  <div className="flex justify-between text-xs">
                    <Text className="text-slate-400">Acceptance Prob.</Text>
                    <Text className="font-bold text-emerald-600">
                      {s.acceptance_probability != null
                        ? `${Math.round(s.acceptance_probability * 100)}%`
                        : '—'}
                    </Text>
                  </div>
                  <div className="flex justify-between text-xs">
                    <Text className="text-slate-400">Risk Level</Text>
                    <Text className="font-bold text-amber-600">{s.risk_level || '—'}</Text>
                  </div>
                </div>
              </div>
            ))}
            {(!activeRec.scenarios || activeRec.scenarios.length === 0) && (
              <div className="col-span-3 py-12 text-center border-2 border-dashed border-slate-200 rounded-[2rem]">
                <Zap className="mx-auto h-8 w-8 text-purple-200 mb-2" />
                <Text className="font-bold text-slate-400">No scenarios generated yet for this recommendation</Text>
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  )
}
