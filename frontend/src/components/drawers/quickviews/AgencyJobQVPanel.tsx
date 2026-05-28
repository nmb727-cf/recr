import { useState } from 'react'
import { Button, Tag, Progress, Form, Input, Drawer, message } from 'antd'
import { MapPin, Clock } from 'lucide-react'
import dayjs from 'dayjs'
import type { AgencyAssignment, JobRequisition } from '@/types'
import { agenciesApi } from '@/api/agencies'
import { useDrawerStore } from '@/store/drawerStore'

const { TextArea } = Input

type JobWithAssignment = { assignment: AgencyAssignment; requisition: JobRequisition }

export default function AgencyJobQVPanel({ data }: { data: JobWithAssignment }) {
  const { requisition, assignment } = data
  const openFullView = useDrawerStore(s => s.openFullView)
  const [submitOpen, setSubmitOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()
  const daysRemaining = dayjs(assignment.deadline).diff(dayjs(), 'day')

  const onSubmit = async (values: any) => {
    setLoading(true)
    try {
      await agenciesApi.submitCandidate({ requisition_id: requisition.id, candidate_id: values.candidate_id, cover_note: values.cover_note })
      message.success('Candidate submitted!')
      setSubmitOpen(false)
      form.resetFields()
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to submit candidate')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <div className="space-y-8">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Tag className="m-0 border-none bg-emerald-50 text-emerald-700 font-bold text-[10px] uppercase px-2 py-0.5 rounded-full">{requisition.status}</Tag>
            <Tag className="m-0 border-none bg-blue-50 text-blue-700 font-bold text-[10px] uppercase px-2 py-0.5 rounded-full">{requisition.job_type.replace('_', ' ')}</Tag>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight leading-tight">{requisition.title}</h2>
          <p className="text-slate-500 mt-1 flex items-center gap-1.5 text-sm font-medium">
            <MapPin className="h-3.5 w-3.5" /> {requisition.location_id || 'Remote'}
          </p>
        </div>
        <div className="bg-slate-50/50 rounded-2xl p-5 border border-slate-100 shadow-sm">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Submission Progress</span>
            <span className="text-sm font-bold text-slate-700">{assignment.submissions_count} / {assignment.max_submissions}</span>
          </div>
          <Progress percent={(assignment.submissions_count / assignment.max_submissions) * 100} showInfo={false} strokeColor="#3b82f6" trailColor="#e2e8f0" />
          <div className="mt-4 flex items-center gap-2 text-amber-600 font-bold text-sm">
            <Clock className="h-4 w-4" />
            <span>{daysRemaining > 0 ? `${daysRemaining} days remaining` : 'Deadline passed'}</span>
          </div>
        </div>
        {requisition.skills_required?.length > 0 && (
          <div>
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-widest mb-3">Required Skills</h3>
            <div className="flex flex-wrap gap-2">
              {requisition.skills_required.map(s => (
                <Tag key={s} className="m-0 border-none bg-white shadow-soft-sm text-slate-700 font-semibold px-3 py-1 rounded-lg">{s}</Tag>
              ))}
            </div>
          </div>
        )}
        <div className="grid grid-cols-2 gap-3">
          <Button block className="h-12 rounded-xl font-bold" onClick={() => openFullView()}>View Full Details</Button>
          <Button type="primary" block className="h-12 rounded-xl font-bold bg-blue-600 border-none shadow-soft-md" onClick={() => setSubmitOpen(true)}>
            Submit Candidate
          </Button>
        </div>
      </div>

      <Drawer
        title={<div><div className="text-base font-bold text-slate-900">Submit Candidate</div><div className="text-xs text-slate-500">{requisition.title}</div></div>}
        open={submitOpen}
        onClose={() => setSubmitOpen(false)}
        width={440}
        styles={{ body: { padding: '24px' } }}
        destroyOnHidden
      >
        <Form form={form} layout="vertical" onFinish={onSubmit}>
          <Form.Item name="candidate_id" label="Candidate ID" rules={[{ required: true }]}>
            <Input placeholder="Enter user UUID" className="h-10 rounded-xl" />
          </Form.Item>
          <Form.Item name="cover_note" label="Cover Note" rules={[{ required: true }]}>
            <TextArea rows={6} placeholder="Why is this candidate a good fit?" />
          </Form.Item>
          <div className="flex gap-3 mt-6">
            <Button onClick={() => setSubmitOpen(false)} className="flex-1 h-11 rounded-xl font-bold">Cancel</Button>
            <Button type="primary" htmlType="submit" loading={loading} className="flex-1 h-11 rounded-xl font-bold bg-blue-600 border-none">Submit</Button>
          </div>
        </Form>
      </Drawer>
    </>
  )
}
