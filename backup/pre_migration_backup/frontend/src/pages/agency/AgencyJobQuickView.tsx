import { Button, Tag, Typography, Card, Empty, Select, message, Divider, Avatar } from 'antd'
import { Briefcase, Building2, Clock, Send, ShieldCheck, User } from 'lucide-react'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { agenciesApi } from '@/api/agencies'
import { useQueryClient } from '@tanstack/react-query'
import { useApiQuery } from '@/hooks/useApiQuery'
import http from '@/utils/http'

const { Title, Text, Paragraph } = Typography

type AgencyJobQuickViewProps = {
  data: any
  onClose: () => void
}

export default function AgencyJobQuickView({ data, onClose }: AgencyJobQuickViewProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [assigning, setAssigning] = useState(false)

  const assignment = data?.assignment || {}
  const requisition = data?.requisition || {}

  const { data: teamData } = useApiQuery(['agency-team'], () => http.get('/agencies/team/'))
  const teamMembers = (teamData as any)?.members || []

  if (!assignment?.id || !requisition?.id) {
    return (
      <div className="p-6">
        <Empty description="Job details are unavailable" />
      </div>
    )
  }

  const handleAssignRecruiter = async (recruiterId: string) => {
    setAssigning(true)
    try {
      await agenciesApi.assignInternalRecruiter(assignment.id, recruiterId)
      message.success('Internal recruiter assigned')
      queryClient.invalidateQueries({ queryKey: ['agency', 'my-jobs'] })
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to assign recruiter')
    } finally {
      setAssigning(false)
    }
  }

  const skills = Array.isArray(requisition?.skills_required) ? requisition.skills_required : []
  const clientName =
    data?.client_name ||
    assignment?.client_name ||
    assignment?.company_name ||
    assignment?.metadata?.company_name ||
    'Client company'

  const govMode = assignment?.governance_mode || 'direct'

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Tag color={assignment?.status === 'active' ? 'green' : 'default'} className="m-0 border-none font-bold text-[10px] uppercase rounded-full">
            {assignment?.status || 'assigned'}
          </Tag>
          {assignment?.deadline && (
            <Tag className="m-0 border-none bg-amber-50 text-amber-700 font-bold text-[10px] uppercase rounded-full">
              Due {dayjs(assignment.deadline).format('MMM D, YYYY')}
            </Tag>
          )}
        </div>
        <Tag className="m-0 border-none bg-indigo-50 text-indigo-700 font-bold text-[10px] uppercase rounded-full flex items-center gap-1">
          <ShieldCheck className="h-3 w-3" />
          {govMode.replace('_', ' ')}
        </Tag>
      </div>

      <Title level={4} className="!mb-1 !text-slate-900">
        {requisition?.title || 'Untitled Job'}
      </Title>

      <div className="mb-5 flex items-center gap-4">
        <Text className="text-slate-500 flex items-center gap-1">
          <Building2 className="h-4 w-4" />
          {clientName}
        </Text>
        <Text className="text-slate-500 flex items-center gap-1">
          <Briefcase className="h-4 w-4" />
          {String(requisition?.job_type || 'role').replace('_', ' ')}
        </Text>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-6">
        <Card size="small" className="border border-slate-100 bg-slate-50/50">
          <Text className="block text-[9px] uppercase text-slate-400 font-black tracking-widest mb-1">Submissions</Text>
          <Text className="font-bold text-slate-700 text-sm">
            {Number(assignment?.submissions_count || 0)} / {Number(assignment?.max_submissions || '∞')}
          </Text>
        </Card>
        <Card size="small" className="border border-slate-100 bg-slate-50/50">
          <Text className="block text-[9px] uppercase text-slate-400 font-black tracking-widest mb-1">Governance</Text>
          <Text className="font-bold text-slate-700 text-sm capitalize">
            {govMode.replace('_', ' ')}
          </Text>
        </Card>
      </div>

      <Divider className="my-6" />

      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <Text className="text-[10px] uppercase text-slate-400 font-bold">Internal Assignee</Text>
          {assignment?.internal_recruiter_name && (
            <Text className="text-[10px] text-blue-600 font-bold">Assigned</Text>
          )}
        </div>
        <Select
          className="w-full h-11"
          placeholder="Assign internal recruiter..."
          loading={assigning}
          value={assignment?.internal_recruiter_id}
          onChange={handleAssignRecruiter}
          suffixIcon={<User className="h-4 w-4 text-slate-400" />}
        >
          {teamMembers.map((m: any) => (
            <Select.Option key={m.id} value={m.id}>
              <div className="flex items-center gap-2">
                <Avatar size="small" className="bg-slate-100 text-slate-600 text-[10px]">
                  {m.name?.charAt(0)}
                </Avatar>
                {m.name}
              </div>
            </Select.Option>
          ))}
        </Select>
      </div>

      <Divider className="my-6" />

      <div className="mb-4">
        <Text className="block text-[10px] uppercase text-slate-400 font-bold mb-2">Description</Text>
        <Paragraph className="!mb-0 text-slate-700 text-sm leading-relaxed">
          {requisition?.description || 'No description provided by client.'}
        </Paragraph>
      </div>

      <div className="mb-6">
        <Text className="block text-[10px] uppercase text-slate-400 font-bold mb-2">Requirements</Text>
        <Paragraph className="!mb-0 text-slate-700 text-sm leading-relaxed">
          {requisition?.requirements || 'No explicit requirements provided.'}
        </Paragraph>
      </div>

      <div className="mb-8">
        <Text className="block text-[10px] uppercase text-slate-400 font-bold mb-2">Required Skills</Text>
        <div className="flex flex-wrap gap-1.5">
          {skills.length > 0 ? (
            skills.map((skill: string) => (
              <Tag key={skill} className="m-0 border-none bg-slate-100 text-slate-600 font-bold text-[10px] px-2.5 py-1 rounded-md">
                {skill}
              </Tag>
            ))
          ) : (
            <Text className="text-slate-500 italic text-xs">No specific skills listed.</Text>
          )}
        </div>
      </div>

      <div className="sticky bottom-0 bg-white pt-4 pb-2 border-t border-slate-50 mt-auto">
        <div className="flex gap-2">
          <Button
            type="primary"
            block
            size="large"
            icon={<Send className="h-4 w-4" />}
            className="bg-blue-600 border-none font-bold h-12 rounded-xl shadow-soft-md"
            onClick={() => {
              navigate(`/agencies/submit-candidate?requisition_id=${requisition.id}`)
              onClose()
            }}
          >
            {govMode === 'approval_required' ? 'Start Submission Draft' : 'Submit Candidate'}
          </Button>
        </div>
        {govMode === 'approval_required' && (
          <p className="text-[10px] text-slate-400 text-center mt-3 font-medium">
            Internal approval is required before the client sees this candidate.
          </p>
        )}
      </div>
    </div>
  )
}
