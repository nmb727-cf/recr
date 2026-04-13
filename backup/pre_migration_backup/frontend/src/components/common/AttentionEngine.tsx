import React, { useState, useMemo } from 'react'
import { Button, Drawer, Typography, Badge, Space, Card, Tag, Divider } from 'antd'
import { 
  Zap, 
  Clock3, 
  AlertCircle, 
  Calendar, 
  ArrowRight,
  ChevronRight,
  Sparkles
} from 'lucide-react'
import { useLocation, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/utils/cn'

const { Title, Text } = Typography

interface AttentionItem {
  id: string
  title: string
  description: string
  priority: 'urgent' | 'today' | 'upcoming'
  type: string
  link: string
}

export const AttentionEngine: React.FC = () => {
  const [isOpen, setIsModalOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()

  const attentionItems = useMemo(() => {
    const items: AttentionItem[] = []
    const path = location.pathname

    // Mock logic based on path - in real implementation this would pull from react-query caches or specific lightweight endpoints
    if (path.includes('/candidates/leads')) {
      items.push(
        { id: '1', title: 'Overdue Follow-up', description: 'Sarah Chen has been waiting for 2 days', priority: 'urgent', type: 'lead', link: '/candidates/leads?id=1' },
        { id: '2', title: 'Follow-up Today', description: 'Schedule catch-up with Marcus', priority: 'today', type: 'lead', link: '/candidates/leads?id=2' },
        { id: '3', title: 'Cold Lead', description: 'James Wilson hasn\'t been contacted in 2 weeks', priority: 'upcoming', type: 'lead', link: '/candidates/leads?id=3' }
      )
    } else if (path.includes('/pipeline')) {
      items.push(
        { id: 'p1', title: 'Scoring Pending', description: 'Final round feedback for Alex Rivera', priority: 'urgent', type: 'interview', link: '/interviews/1' },
        { id: 'p2', title: 'Stuck in Stage', description: 'Candidate in "Technical" for 5 days', priority: 'today', type: 'pipeline', link: '/pipeline' },
        { id: 'p3', title: 'Offer Pending', description: 'Draft offer for Elena Gilbert', priority: 'today', type: 'offer', link: '/hiring-decisions/offer-release' }
      )
    } else if (path.includes('/jobs')) {
      items.push(
        { id: 'j1', title: 'Nearing Deadline', description: 'Frontend Engineer role expires in 48h', priority: 'urgent', type: 'job', link: '/jobs/1' },
        { id: 'j2', title: 'No Candidates', description: 'DevOps Lead has 0 active applicants', priority: 'today', type: 'job', link: '/jobs/2' }
      )
    } else if (path.includes('/candidates')) {
      items.push(
        { id: 'c1', title: 'Incomplete Profile', description: 'John Doe is missing contact info', priority: 'today', type: 'candidate', link: '/candidates/1' },
        { id: 'c2', title: 'Missing Resume', description: '4 applicants have no resume attached', priority: 'upcoming', type: 'candidate', link: '/candidates' }
      )
    } else if (path === '/dashboard') {
      // Aggregated for Home
      items.push(
        { id: '1', title: 'Overdue Follow-up', description: 'Sarah Chen (Lead)', priority: 'urgent', type: 'lead', link: '/candidates/leads' },
        { id: 'p1', title: 'Scoring Pending', description: 'Alex Rivera (Interview)', priority: 'urgent', type: 'interview', link: '/interviews' },
        { id: 'j1', title: 'Job Nearing Deadline', description: 'Frontend Engineer', priority: 'today', type: 'job', link: '/jobs' }
      )
    }

    return items
  }, [location.pathname])

  const urgentCount = attentionItems.filter(i => i.priority === 'urgent').length
  const hasItems = attentionItems.length > 0

  const sections = [
    { key: 'urgent', label: 'Urgent', icon: <AlertCircle size={14} className="text-red-500" />, items: attentionItems.filter(i => i.priority === 'urgent') },
    { key: 'today', label: 'Today', icon: <Clock3 size={14} className="text-amber-500" />, items: attentionItems.filter(i => i.priority === 'today') },
    { key: 'upcoming', label: 'Upcoming', icon: <Calendar size={14} className="text-blue-500" />, items: attentionItems.filter(i => i.priority === 'upcoming') },
  ]

  return (
    <>
      {/* Floating Button */}
      <div className="fixed bottom-6 right-6 z-[100]">
        <motion.div
          animate={hasItems ? { scale: [1, 1.05, 1] } : {}}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <Badge count={urgentCount} offset={[-2, 5]} size="small" status="processing">
            <Button
              type="primary"
              shape="circle"
              size="large"
              className={cn(
                "h-14 w-14 shadow-2xl flex items-center justify-center border-none transition-all",
                hasItems ? "bg-indigo-600 hover:bg-indigo-700" : "bg-slate-700 hover:bg-slate-800"
              )}
              icon={<Zap size={24} className={cn(hasItems && "text-amber-300 fill-amber-300")} />}
              onClick={() => setIsModalOpen(true)}
            />
          </Badge>
        </motion.div>
      </div>

      <Drawer
        title={
          <div className="flex items-center gap-2">
            <Sparkles size={18} className="text-indigo-600" />
            <span className="text-base font-bold text-slate-800 uppercase tracking-tight">Attention Assistant</span>
          </div>
        }
        placement="right"
        onClose={() => setIsModalOpen(false)}
        open={isOpen}
        width={380}
        closeIcon={null}
        extra={<Button type="text" onClick={() => setIsModalOpen(false)} icon={<ChevronRight size={20} />} />}
        headerStyle={{ borderBottom: '1px solid #f1f5f9', padding: '16px 20px' }}
        bodyStyle={{ padding: '0', background: '#f8fafc' }}
      >
        <div className="flex flex-col h-full">
          <div className="flex-1 overflow-y-auto p-5 space-y-8">
            {sections.map(section => (
              <section key={section.key} className={cn(section.items.length === 0 && "opacity-40")}>
                <div className="flex items-center gap-2 mb-4">
                  {section.icon}
                  <span className="text-[11px] font-black text-slate-400 uppercase tracking-[0.2em]">{section.label}</span>
                  <div className="h-[1px] flex-1 bg-slate-100 ml-2" />
                </div>

                <div className="space-y-3">
                  {section.items.length > 0 ? (
                    section.items.map(item => (
                      <div
                        key={item.id}
                        onClick={() => {
                          navigate(item.link)
                          setIsModalOpen(false)
                        }}
                        className="group bg-white p-4 rounded-2xl border border-slate-100 hover:border-indigo-200 hover:shadow-md transition-all cursor-pointer relative overflow-hidden"
                      >
                        <div className={cn(
                          "absolute left-0 top-0 bottom-0 w-1",
                          item.priority === 'urgent' ? "bg-red-500" : item.priority === 'today' ? "bg-amber-500" : "bg-blue-500"
                        )} />
                        
                        <div className="flex justify-between items-start gap-3">
                          <div className="flex-1">
                            <Text className="block text-sm font-bold text-slate-800 leading-tight mb-1 group-hover:text-indigo-600">
                              {item.title}
                            </Text>
                            <Text className="block text-[11px] text-slate-500 line-clamp-2 leading-relaxed">
                              {item.description}
                            </Text>
                          </div>
                          <div className="mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <ArrowRight size={14} className="text-indigo-400" />
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="py-4 text-center border border-dashed border-slate-200 rounded-2xl">
                      <Text className="text-[10px] font-bold text-slate-300 uppercase">All caught up</Text>
                    </div>
                  )}
                </div>
              </section>
            ))}
          </div>

          <div className="p-5 bg-white border-t border-slate-100">
            <div className="p-4 bg-indigo-50 rounded-2xl border border-indigo-100 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 bg-indigo-600 rounded-xl flex items-center justify-center text-white">
                  <Zap size={16} />
                </div>
                <div>
                  <Text className="block text-xs font-bold text-indigo-900">Focus Mode</Text>
                  <Text className="text-[10px] text-indigo-700/70">Showing context-aware tasks</Text>
                </div>
              </div>
              <Tag className="m-0 border-none bg-indigo-200 text-indigo-700 font-bold text-[9px] uppercase px-2 rounded-full">ACTIVE</Tag>
            </div>
          </div>
        </div>
      </Drawer>
    </>
  )
}
