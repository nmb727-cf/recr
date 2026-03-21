import {
  Button, Tag, Typography, Avatar,
  Spin, Empty, Divider
} from 'antd'
import {
  Mail, Phone, MapPin,
  ArrowRight, MessageSquare, Star
} from 'lucide-react'
import { useApiQuery } from '@/hooks/useApiQuery'
import { candidatesApi } from '@/api/candidates'
import type { CandidateDetail } from '@/types'

const { Title, Text } = Typography

interface CandidateQuickViewProps {
  candidateId: string
  onClose: () => void
  onOpenFullView: () => void
}

export default function CandidateQuickView({ candidateId, onOpenFullView }: CandidateQuickViewProps) {
  const { data, isLoading } = useApiQuery(
    ['candidate', 'quick', candidateId],
    () => candidatesApi.get(candidateId)
  )

  const candidate = (data as any)?.candidate as CandidateDetail

  if (isLoading) return <div className="p-12 text-center"><Spin /></div>
  if (!candidate) return <Empty description="Candidate not found" />

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto">
        {/* Profile Header */}
        <div className="flex flex-col items-center text-center mb-8">
          <Avatar 
            size={80} 
            className="bg-blue-100 text-blue-600 font-bold text-3xl mb-4 shadow-soft-md"
          >
            {candidate.full_name?.charAt(0).toUpperCase()}
          </Avatar>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
            {candidate.full_name}
          </h2>
          <p className="text-slate-500 font-medium mt-1">
            {candidate.current_title || 'No Title'} {candidate.current_company ? `at ${candidate.current_company}` : ''}
          </p>
          <div className="flex flex-wrap justify-center gap-2 mt-3">
            {candidate.is_actively_looking && (
              <Tag color="success" className="rounded-full px-2.5 py-0.5 border-none bg-emerald-50 text-emerald-700 font-bold text-[10px] uppercase">
                Actively Looking
              </Tag>
            )}
            <Tag className="rounded-full px-2.5 py-0.5 border-none bg-blue-50 text-blue-700 font-bold text-[10px] uppercase">
              {candidate.source || 'Direct'}
            </Tag>
          </div>
        </div>

        {/* Quick Info */}
        <div className="space-y-4 mb-8">
          <div className="flex items-center gap-3 text-slate-600">
            <Mail className="h-4 w-4 text-slate-400" />
            <span className="text-sm font-medium">{candidate.email}</span>
          </div>
          {candidate.phone && (
            <div className="flex items-center gap-3 text-slate-600">
              <Phone className="h-4 w-4 text-slate-400" />
              <span className="text-sm font-medium">{candidate.phone}</span>
            </div>
          )}
          <div className="flex items-center gap-3 text-slate-600">
            <MapPin className="h-4 w-4 text-slate-400" />
            <span className="text-sm font-medium">
              {[candidate.current_location_city, candidate.current_location_country].filter(Boolean).join(', ') || 'Remote'}
            </span>
          </div>
        </div>

        <Divider />

        {/* Skills */}
        <div className="mb-8">
          <Title level={5} className="!text-xs !font-bold !uppercase !tracking-widest !text-slate-400 !mb-3">Skills</Title>
          <div className="flex flex-wrap gap-2">
            {candidate.skills?.slice(0, 8).map(skill => (
              <Tag key={skill} className="m-0 border-none bg-slate-100 text-slate-700 font-semibold px-3 py-1 rounded-lg text-xs">
                {skill}
              </Tag>
            ))}
            {candidate.skills?.length > 8 && (
              <Text className="text-[10px] font-bold text-slate-400">+{candidate.skills.length - 8} more</Text>
            )}
          </div>
        </div>

        {/* Last Note (Placeholder) */}
        <div className="mb-8">
          <Title level={5} className="!text-xs !font-bold !uppercase !tracking-widest !text-slate-400 !mb-3">Last Note</Title>
          <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
            <p className="text-sm text-slate-600 italic">"Strong technical background, but needs more experience with AWS architecture."</p>
            <p className="text-[10px] text-slate-400 font-bold mt-2 uppercase">Added by Nirav · 2 days ago</p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="pt-6 border-t border-slate-100 mt-auto">
        <div className="grid grid-cols-2 gap-3 mb-4">
          <Button 
            className="h-11 rounded-xl font-bold flex items-center justify-center gap-2"
            icon={<MessageSquare className="h-4 w-4" />}
          >
            Message
          </Button>
          <Button 
            className="h-11 rounded-xl font-bold flex items-center justify-center gap-2"
            icon={<Star className="h-4 w-4" />}
          >
            Shortlist
          </Button>
        </div>

        <Button 
          type="primary" 
          block 
          className="h-12 rounded-xl font-bold flex items-center justify-center gap-2 bg-slate-900 hover:!bg-slate-800 border-none shadow-soft-md"
          onClick={onOpenFullView}
        >
          View Full Profile <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
