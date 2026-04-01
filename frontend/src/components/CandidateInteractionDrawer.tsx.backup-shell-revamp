import { useState } from 'react'
import {
  Drawer, Form, Select, Radio, Input, DatePicker,
  Button, Timeline, Typography, Tag, message
} from 'antd'
import {
  Phone, Mail, MessageCircle, FileText,
  Users, Linkedin, CheckCircle, MinusCircle,
  XCircle, BellOff
} from 'lucide-react'
import dayjs from 'dayjs'
import http from '@/utils/http'
import { useApiQuery } from '@/hooks/useApiQuery'

const { Title, Text } = Typography
const { TextArea } = Input

const INTERACTION_TYPES = [
  { value: 'call', label: 'Call', icon: <Phone className="h-4 w-4" /> },
  { value: 'email', label: 'Email', icon: <Mail className="h-4 w-4" /> },
  { value: 'whatsapp', label: 'WhatsApp', icon: <MessageCircle className="h-4 w-4" /> },
  { value: 'note', label: 'Note', icon: <FileText className="h-4 w-4" /> },
  { value: 'meeting', label: 'Meeting', icon: <Users className="h-4 w-4" /> },
  { value: 'linkedin', label: 'LinkedIn', icon: <Linkedin className="h-4 w-4" /> },
]

const OUTCOMES = [
  { value: 'positive', label: 'Positive', color: 'green', icon: <CheckCircle className="h-3 w-3" /> },
  { value: 'neutral', label: 'Neutral', color: 'blue', icon: <MinusCircle className="h-3 w-3" /> },
  { value: 'negative', label: 'Negative', color: 'red', icon: <XCircle className="h-3 w-3" /> },
  { value: 'no_response', label: 'No Response', color: 'default', icon: <BellOff className="h-3 w-3" /> },
]

export default function CandidateInteractionDrawer({ 
  candidate, 
  initialType = 'note',
  onClose 
}: { 
  candidate: any, 
  initialType?: string,
  onClose: () => void 
}) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  // Fetch recent interactions
  const { data: interactionData, refetch } = useApiQuery(
    ['interactions', candidate?.id],
    () => http.get(`/candidates/crm/candidates/${candidate.id}/interactions/`),
    { enabled: !!candidate?.id }
  )
  const interactions = (interactionData as any)?.data?.interactions ?? []

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      await http.post(`/candidates/crm/candidates/${candidate.id}/interactions/`, values)
      message.success('Interaction logged successfully')
      form.resetFields()
      refetch()
      // onClose() // User might want to log another or see timeline
    } catch {
      message.error('Failed to log interaction')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Drawer
      title={
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-slate-900 text-white flex items-center justify-center">
            <MessageCircle className="h-5 w-5" />
          </div>
          <div>
            <div className="text-base font-bold text-slate-900">Log Interaction</div>
            <div className="text-xs text-slate-500 font-medium">{candidate?.full_name}</div>
          </div>
        </div>
      }
      open={!!candidate}
      onClose={onClose}
      width={480}
      styles={{ body: { padding: '24px' } }}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        initialValues={{ interaction_type: initialType, direction: 'outbound', outcome: 'neutral' }}
        requiredMark={false}
      >
        <div className="grid grid-cols-2 gap-4">
          <Form.Item name="interaction_type" label="Channel" rules={[{ required: true }]}>
            <Select className="h-11">
              {INTERACTION_TYPES.map(t => (
                <Select.Option key={t.value} value={t.value}>
                  <div className="flex items-center gap-2">
                    {t.icon} <span>{t.label}</span>
                  </div>
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item name="outcome" label="Outcome">
            <Select className="h-11">
              {OUTCOMES.map(o => (
                <Select.Option key={o.value} value={o.value}>
                  <div className="flex items-center gap-2">
                    {o.icon} <span>{o.label}</span>
                  </div>
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
        </div>

        <Form.Item name="direction" label="Direction">
          <Radio.Group className="w-full">
            <Radio.Button value="outbound" className="w-1/2 text-center h-10 flex items-center justify-center font-bold">Outbound</Radio.Button>
            <Radio.Button value="inbound" className="w-1/2 text-center h-10 flex items-center justify-center font-bold">Inbound</Radio.Button>
          </Radio.Group>
        </Form.Item>

        <Form.Item name="subject" label="Subject">
          <Input placeholder="e.g. Discussed salary expectations" className="h-11 rounded-xl" />
        </Form.Item>

        <Form.Item name="content" label="Notes / Discussion">
          <TextArea rows={4} placeholder="What was discussed?" className="rounded-xl" />
        </Form.Item>

        <Form.Item name="next_followup_date" label="Next Follow-up">
          <DatePicker 
            className="w-full h-11 rounded-xl" 
            placeholder="Select date"
            disabledDate={(current) => current && current < dayjs().startOf('day')}
          />
        </Form.Item>

        <Button type="primary" htmlType="submit" block size="large" loading={loading} className="h-14 rounded-2xl font-black bg-blue-600 border-none shadow-soft-md">
          Save Interaction
        </Button>
      </Form>

      <div className="mt-12">
        <Title level={5} className="!text-[10px] !font-bold !uppercase !tracking-widest !text-slate-400 !mb-6">Recent History</Title>
        {interactions.length > 0 ? (
          <Timeline 
            items={interactions.map((i: any) => ({
              children: (
                <div className="pb-6">
                  <div className="flex items-center justify-between mb-1">
                    <Text strong className="text-sm text-slate-900">{i.subject || 'No Subject'}</Text>
                    <span className="text-[10px] text-slate-400 font-bold uppercase">{dayjs(i.created_at).fromNow()}</span>
                  </div>
                  <div className="flex items-center gap-2 mb-2">
                    <Tag className="m-0 border-none bg-slate-100 text-slate-500 font-bold text-[9px] uppercase px-1.5">{i.interaction_type}</Tag>
                    <Tag color={OUTCOMES.find(o => o.value === i.outcome)?.color} className="m-0 border-none font-bold text-[9px] uppercase px-1.5">{i.outcome}</Tag>
                  </div>
                  <p className="text-xs text-slate-500 leading-relaxed italic">"{i.content}"</p>
                </div>
              )
            }))}
          />
        ) : (
          <div className="py-8 text-center bg-slate-50 rounded-2xl border border-dashed border-slate-200">
            <p className="text-xs text-slate-400 font-medium">No interaction history recorded yet.</p>
          </div>
        )}
      </div>
    </Drawer>
  )
}
