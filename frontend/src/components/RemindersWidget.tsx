import { useNavigate } from 'react-router-dom'
import { Card, Avatar, Button, Typography, Skeleton, Badge } from 'antd'
import { 
  Bell, CheckCircle, MessageSquare, 
} from 'lucide-react'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { useApiQuery } from '@/hooks/useApiQuery'
import http from '@/utils/http'
import { cn } from '@/utils/cn'

dayjs.extend(relativeTime)
const { Text } = Typography

export default function RemindersWidget() {
  const navigate = useNavigate()

  const { data, isLoading, refetch } = useApiQuery(['crm-reminders'], () => 
    http.get('/crm/reminders/')
  )
  const reminders = (data as any)?.data?.reminders ?? []

  const handleDone = async (id: string) => {
    try {
      await http.post(`/crm/reminders/${id}/complete/`)
      refetch()
    } catch {
      // error
    }
  }

  return (
    <Card 
      title={
        <div className="flex items-center gap-2 py-1">
          <Bell className="h-4 w-4 text-blue-600" />
          <span className="text-base font-bold text-slate-900">Today's Follow-ups</span>
          {reminders.length > 0 && (
            <Badge count={reminders.length} style={{ backgroundColor: '#1e40af', boxShadow: 'none' }} />
          )}
        </div>
      }
      bordered={false}
      className="shadow-soft-sm rounded-2xl h-full"
      extra={reminders.length > 0 && <CheckCircle className="h-4 w-4 text-emerald-500" />}
    >
      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map(i => <Skeleton key={i} active avatar paragraph={{ rows: 1 }} />)}
        </div>
      ) : reminders.length > 0 ? (
        <div className="divide-y divide-slate-100">
          {reminders.map((r: any) => {
            const isOverdue = dayjs(r.due_date).isBefore(dayjs(), 'day')
            return (
              <div key={r.id} className="py-4 first:pt-0 last:pb-0 group">
                <div className="flex items-start gap-3">
                  <Avatar className="bg-blue-50 text-blue-600 font-bold shrink-0">
                    {r.candidate_name?.charAt(0).toUpperCase()}
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <Text strong className="text-sm text-slate-900 block truncate">{r.candidate_name}</Text>
                    <Text type="secondary" className="text-xs block truncate mb-2">Follow up re: {r.job_title || 'Application'}</Text>
                    
                    <div className="flex items-center justify-between">
                      <span className={cn("text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded", isOverdue ? "bg-rose-50 text-rose-600" : "bg-slate-50 text-slate-500")}>
                        {isOverdue ? `${dayjs().diff(dayjs(r.due_date), 'day')}d Overdue` : 'Due Today'}
                      </span>
                      
                      <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Button 
                          size="small" 
                          type="text" 
                          icon={<CheckCircle className="h-3.5 w-3.5 text-emerald-600" />}
                          onClick={() => handleDone(r.id)}
                        />
                        <Button 
                          size="small" 
                          type="text" 
                          icon={<MessageSquare className="h-3.5 w-3.5 text-blue-600" />}
                          onClick={() => navigate('/candidates')} // Simplified
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="py-8 text-center">
          <div className="h-16 w-16 bg-emerald-50 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4 border border-emerald-100">
            <CheckCircle className="h-8 w-8" />
          </div>
          <p className="text-sm font-bold text-slate-900">All caught up!</p>
          <p className="text-xs text-slate-500 mt-1">No pending follow-ups for today.</p>
        </div>
      )}
    </Card>
  )
}
