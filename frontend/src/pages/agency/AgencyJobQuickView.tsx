import { Button, Tag, Typography, Card, Empty } from 'antd'
import { Briefcase, Building2, Clock, Send } from 'lucide-react'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router-dom'

const { Title, Text, Paragraph } = Typography

type AgencyJobQuickViewProps = {
  data: any
  onClose: () => void
}

export default function AgencyJobQuickView({ data, onClose }: AgencyJobQuickViewProps) {
  const navigate = useNavigate()

  const assignment = data?.assignment || {}
  const requisition = data?.requisition || {}

  if (!assignment?.id || !requisition?.id) {
    return (
      <div className="p-6">
        <Empty description="Job details are unavailable" />
      </div>
    )
  }

  const skills = Array.isArray(requisition?.skills_required) ? requisition.skills_required : []
  const clientName =
    data?.client_name ||
    assignment?.client_name ||
    assignment?.company_name ||
    assignment?.metadata?.company_name ||
    'Client company'

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="mb-4 flex items-center gap-2">
        <Tag color={assignment?.status === 'active' ? 'green' : 'default'} className="m-0 border-none font-bold text-[10px] uppercase rounded-full">
          {assignment?.status || 'assigned'}
        </Tag>
        {assignment?.deadline && (
          <Tag className="m-0 border-none bg-amber-50 text-amber-700 font-bold text-[10px] uppercase rounded-full">
            Due {dayjs(assignment.deadline).format('MMM D, YYYY')}
          </Tag>
        )}
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

      <Card size="small" className="mb-4 border border-slate-200">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <Text className="block text-[10px] uppercase text-slate-400 font-bold">Submission count</Text>
            <Text className="font-semibold text-slate-700">
              {Number(assignment?.submission_count || assignment?.submissions_count || 0)} / {Number(assignment?.max_submissions || 0)}
            </Text>
          </div>
          <div>
            <Text className="block text-[10px] uppercase text-slate-400 font-bold">Deadline</Text>
            <Text className="font-semibold text-slate-700 flex items-center gap-1">
              <Clock className="h-3.5 w-3.5" />
              {assignment?.deadline ? dayjs(assignment.deadline).format('MMM D, YYYY') : 'Not specified'}
            </Text>
          </div>
        </div>
      </Card>

      <div className="mb-4">
        <Text className="block text-[10px] uppercase text-slate-400 font-bold mb-2">Description</Text>
        <Paragraph className="!mb-0 text-slate-700">
          {requisition?.description || 'No description provided by client.'}
        </Paragraph>
      </div>

      <div className="mb-4">
        <Text className="block text-[10px] uppercase text-slate-400 font-bold mb-2">Requirements</Text>
        <Paragraph className="!mb-0 text-slate-700">
          {requisition?.requirements || 'No explicit requirements provided.'}
        </Paragraph>
      </div>

      <div className="mb-6">
        <Text className="block text-[10px] uppercase text-slate-400 font-bold mb-2">Skills</Text>
        <div className="flex flex-wrap gap-2">
          {skills.length > 0 ? (
            skills.map((skill: string) => (
              <Tag key={skill} className="m-0 border-none bg-blue-50 text-blue-700 rounded-full">
                {skill}
              </Tag>
            ))
          ) : (
            <Text className="text-slate-500">No skills listed.</Text>
          )}
        </div>
      </div>

      <div className="sticky bottom-0 bg-white pt-3">
        <div className="flex gap-2">
          <Button
            type="primary"
            icon={<Send className="h-4 w-4" />}
            className="bg-blue-600 border-none font-bold"
            onClick={() => {
              navigate(`/agencies/submit-candidate?requisition_id=${requisition.id}`)
              onClose()
            }}
          >
            Submit Candidate
          </Button>
        </div>
      </div>
    </div>
  )
}

