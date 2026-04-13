import {
  Card, Avatar, Button, Typography, Tag,
  Progress, Badge, message
} from 'antd'
import {
  Send, Star, AlertCircle
} from 'lucide-react'
import { useApiQuery } from '@/hooks/useApiQuery'
import http from '@/utils/http'

const { Text, Title } = Typography

export default function JobMatchSuggestions({ jobId, onMatched }: { jobId: string; onMatched?: () => void }) {
  const { data, isLoading, refetch } = useApiQuery(['job-suggestions', jobId], () => 
    http.get(`/candidates/crm/suggestions/${jobId}/`)
  )
  const suggestions = (data as any)?.data?.suggestions ?? []

  const handleAddToPipeline = async (candidateId: string) => {
    try {
      await http.post('/candidates/crm/pipeline/add/', { candidate_id: candidateId, requisition_id: jobId })
      message.success('Candidate added to CRM pipeline')
      refetch()
      onMatched?.()
    } catch {
      message.error('Failed to add to pipeline')
    }
  }

  const handleDirectSubmit = async (candidateId: string) => {
    try {
      await http.post('/applications/', { candidate_id: candidateId, requisition_id: jobId })
      message.success('Candidate submitted for job')
      refetch()
      onMatched?.()
    } catch {
      message.error('Failed to submit application')
    }
  }

  return (
    <div className="space-y-6 pt-4">
      <div className="flex items-center justify-between">
        <div>
          <Title level={4} className="!mb-1">Intelligent Match Suggestions</Title>
          <Text type="secondary">AI-powered matches from your talent database based on job requirements.</Text>
        </div>
        <Badge count={suggestions.length} color="#1e40af" />
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[1, 2].map(i => <Card key={i} loading bordered={false} className="rounded-2xl shadow-soft-sm" />)}
        </div>
      ) : suggestions.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {suggestions.map((item: any) => (
            <Card 
              key={item.candidate.id} 
              bordered={false} 
              className="shadow-soft-sm rounded-2xl hover:shadow-soft-md transition-all border border-slate-50"
              styles={{ body: { padding: '24px' } }}
            >
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-center gap-4">
                  <Avatar size={56} className="bg-blue-100 text-blue-600 font-bold text-xl shrink-0">
                    {item.candidate.full_name?.charAt(0).toUpperCase()}
                  </Avatar>
                  <div className="min-w-0">
                    <Title level={5} className="!mb-0 truncate">{item.candidate.full_name}</Title>
                    <Text type="secondary" className="text-xs block truncate">{item.candidate.current_title}</Text>
                  </div>
                </div>
                <div className="text-center shrink-0">
                  <Progress 
                    type="circle" 
                    percent={item.match_score} 
                    size={48} 
                    strokeWidth={10}
                    strokeColor={item.match_score > 80 ? '#10b981' : '#3b82f6'}
                  />
                  <div className="text-[9px] font-black uppercase text-slate-400 mt-1 tracking-widest">Match</div>
                </div>
              </div>

              <div className="space-y-4 mb-8">
                <div>
                  <Text className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-2">Matched Skills</Text>
                  <div className="flex flex-wrap gap-1.5">
                    {item.matched_skills?.map((s: string) => (
                      <Tag key={s} className="m-0 border-none bg-emerald-50 text-emerald-700 font-bold text-[9px] uppercase px-2 rounded">
                        {s}
                      </Tag>
                    ))}
                  </div>
                </div>
                {item.missing_skills?.length > 0 && (
                  <div>
                    <Text className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-2">Missing Skills</Text>
                    <div className="flex flex-wrap gap-1.5">
                      {item.missing_skills?.map((s: string) => (
                        <Tag key={s} className="m-0 border-none bg-slate-100 text-slate-400 font-bold text-[9px] uppercase px-2 rounded">
                          {s}
                        </Tag>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3 pt-4 border-t border-slate-50">
                <Button 
                  block 
                  className="rounded-xl font-bold h-10 border-slate-200 text-slate-600 hover:text-blue-600"
                  icon={<Star className="h-3.5 w-3.5" />}
                  onClick={() => handleAddToPipeline(item.candidate.id)}
                >
                  Add to CRM
                </Button>
                <Button 
                  type="primary" 
                  block 
                  className="rounded-xl font-bold h-10 bg-blue-600 border-none shadow-sm"
                  icon={<Send className="h-3.5 w-3.5" />}
                  onClick={() => handleDirectSubmit(item.candidate.id)}
                >
                  Submit
                </Button>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card bordered={false} className="text-center py-16 rounded-3xl bg-slate-50/50 border border-dashed border-slate-200">
          <AlertCircle className="h-10 w-10 text-slate-200 mx-auto mb-4" />
          <p className="text-slate-500 font-medium">No highly matching candidates in your talent pool yet.</p>
          <Text type="secondary" className="text-xs">Add more candidates to your database to see AI-powered suggestions.</Text>
        </Card>
      )}
    </div>
  )
}
