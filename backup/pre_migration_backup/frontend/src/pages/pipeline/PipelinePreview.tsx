import React, { useMemo } from 'react'
import { Card, Typography, Button, Spin, Empty, Row, Col } from 'antd'
import { ArrowRight, Clock, AlertCircle, TrendingUp, Users } from 'lucide-react'
import { useApiQuery } from '@/hooks/useApiQuery'
import { pipelineApi } from '@/api/pipeline'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)

const { Text, Title } = Typography

interface PipelinePreviewProps {
  jobId: string
}

export default function PipelinePreview({ jobId }: PipelinePreviewProps) {
  const navigate = useNavigate()
  const { data, isLoading } = useApiQuery(['pipeline-summary', jobId], () => pipelineApi.getPipeline(jobId), {
    enabled: !!jobId
  })
  
  const pipeline = (data as any)?.pipeline || {}
  const stages = useMemo(() => 
    Object.values(pipeline).sort((a: any, b: any) => a.stage.stage_order - b.stage.stage_order),
    [pipeline]
  )

  const stats = useMemo(() => {
    if (stages.length === 0) return null
    
    let total = 0
    let bottleneck: any = null
    let maxCount = -1
    let recentMovements: any[] = []

    stages.forEach((s: any) => {
      const count = s.count || 0
      total += count
      if (count > maxCount) {
        maxCount = count
        bottleneck = s.stage
      }
      
      // Collect recent apps (updated in last 48h)
      if (Array.isArray(s.applications)) {
        s.applications.forEach((app: any) => {
          if (dayjs().diff(dayjs(app.updated_at), 'hour') < 48) {
            recentMovements.push({ ...app, stageName: s.stage.name })
          }
        })
      }
    })

    return {
      total,
      bottleneck,
      recentMovements: recentMovements.sort((a, b) => dayjs(b.updated_at).unix() - dayjs(a.updated_at).unix()).slice(0, 5)
    }
  }, [stages])

  if (isLoading) return <div className="p-20 text-center"><Spin size="large" /></div>
  if (stages.length === 0) return <Card className="shadow-soft-sm border-none py-10"><Empty description="No pipeline defined for this job" /></Card>

  return (
    <div className="space-y-8 pb-10">
      {/* Stage Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {stages.map((s: any) => (
          <Card 
            key={s.stage.id} 
            className="shadow-soft-sm border-none bg-white hover:shadow-md transition-all cursor-default overflow-hidden relative"
            bodyStyle={{ padding: '20px 16px' }}
          >
            <div className="absolute top-0 left-0 w-1 h-full bg-blue-500 opacity-20" />
            <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2 truncate">
              {s.stage.name}
            </Text>
            <div className="flex items-end justify-between">
              <Title level={2} className="!m-0 !font-black text-slate-800 leading-none">{s.count || 0}</Title>
              {s.count > 0 && <TrendingUp size={16} className="text-emerald-500 mb-1" />}
            </div>
          </Card>
        ))}
      </div>

      <Row gutter={24}>
        <Col span={12}>
          <Card 
            title={<span className="text-[11px] font-black uppercase tracking-widest text-slate-400">Execution Intel</span>}
            bordered={false}
            className="shadow-soft-sm h-full"
          >
            <div className="space-y-6">
              <div className="flex items-start gap-4">
                <div className="h-10 w-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center shrink-0">
                  <AlertCircle size={20} />
                </div>
                <div>
                  <Text className="block text-xs font-bold text-slate-500 uppercase tracking-tight">Active Bottleneck</Text>
                  <Title level={4} className="!m-0 !text-slate-800">{stats?.bottleneck?.name || 'None'}</Title>
                  <Text className="text-[11px] text-slate-400 mt-1">This stage currently holds the highest number of active candidates.</Text>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="h-10 w-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                  <Users size={20} />
                </div>
                <div>
                  <Text className="block text-xs font-bold text-slate-500 uppercase tracking-tight">Total Active Load</Text>
                  <Title level={4} className="!m-0 !text-slate-800">{stats?.total || 0} Candidates</Title>
                  <Text className="text-[11px] text-slate-400 mt-1">Total applications being managed in this pipeline workspace.</Text>
                </div>
              </div>
            </div>
          </Card>
        </Col>

        <Col span={12}>
          <Card 
            title={<span className="text-[11px] font-black uppercase tracking-widest text-slate-400">Recent Movement</span>}
            bordered={false}
            className="shadow-soft-sm h-full"
          >
            {stats?.recentMovements && stats.recentMovements.length > 0 ? (
              <div className="space-y-4">
                {stats.recentMovements.map((app) => (
                  <div key={app.id} className="flex items-center justify-between group p-2 hover:bg-slate-50 rounded-lg transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="h-2 w-2 rounded-full bg-blue-500" />
                      <div>
                        <Text className="block text-xs font-bold text-slate-700">Candidate Progressed</Text>
                        <Text className="text-[10px] text-slate-400 uppercase font-bold tracking-tight">Moved to {app.stageName}</Text>
                      </div>
                    </div>
                    <Text className="text-[10px] font-bold text-slate-400 uppercase">{dayjs(app.updated_at).fromNow()}</Text>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-10 text-center">
                <Clock size={24} className="mx-auto text-slate-200 mb-2" />
                <Text className="text-[11px] text-slate-400 italic font-medium">No movement activity in the last 48 hours.</Text>
              </div>
            )}
          </Card>
        </Col>
      </Row>

      <div className="flex justify-center pt-6 border-t border-slate-100">
        <Button 
          type="primary" 
          size="large" 
          icon={<ArrowRight size={18} className="mr-2" />} 
          onClick={() => navigate(`/pipeline?job=${jobId}`)}
          className="bg-blue-600 h-14 px-10 rounded-2xl font-black uppercase tracking-widest shadow-soft-lg hover:!scale-[1.02] transition-transform"
        >
          Open Full Execution Workspace
        </Button>
      </div>
    </div>
  )
}
