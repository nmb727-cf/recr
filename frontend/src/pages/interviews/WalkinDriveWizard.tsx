import { useState } from 'react'
import {
  Modal, Steps, Form, Input, DatePicker, Select,
  Button, Card, Typography, Divider, Space,
  Badge, Avatar, Tooltip, InputNumber, Switch, Tag
} from 'antd'
import {
  Zap,
  Info,
  GitPullRequest,
  Users,
  BarChart3,
  Eye,
  Plus,
  Trash2,
  ChevronRight,
  ChevronLeft,
  CheckCircle2,
  Clock,
  Calendar,
  Briefcase,
  MapPin,
  Globe
} from 'lucide-react'
import dayjs from 'dayjs'
import { cn } from '@/utils/cn'

const { Text, Title, Paragraph } = Typography
const { Option } = Select
const { TextArea } = Input

interface WalkinDriveWizardProps {
  open: boolean
  onClose: () => void
  onSuccess: () => void
}

export default function WalkinDriveWizard({ open, onClose, onSuccess }: WalkinDriveWizardProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [form] = Form.useForm()

  const steps = [
    { title: 'Setup', icon: <Info size={16} /> },
    { title: 'Flow', icon: <GitPullRequest size={16} /> },
    { title: 'Candidates', icon: <Users size={16} /> },
    { title: 'Evaluation', icon: <BarChart3 size={16} /> },
    { title: 'Preview', icon: <Eye size={16} /> }
  ]

  const next = () => setCurrentStep(currentStep + 1)
  const prev = () => setCurrentStep(currentStep - 1)

  return (
    <Modal
      open={open}
      onCancel={onClose}
      footer={null}
      width={1000}
      className="wizard-modal"
      styles={{ body: { padding: 0 } }}
      closable={false}
      destroyOnClose
    >
      <div className="flex h-[700px] overflow-hidden rounded-3xl">
        {/* Sidebar */}
        <div className="w-[280px] bg-slate-900 p-8 flex flex-col">
          <div className="flex items-center gap-3 mb-10">
            <div className="h-10 w-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white">
              <Zap size={20} />
            </div>
            <div>
              <Text className="block text-sm font-black text-white uppercase tracking-widest">Drive Wizard</Text>
              <Text className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Walk-in Engine</Text>
            </div>
          </div>

          <div className="flex-1 space-y-2">
            {steps.map((step, i) => (
              <div 
                key={i}
                className={cn(
                  "flex items-center gap-4 p-3 rounded-xl transition-all cursor-default",
                  currentStep === i ? "bg-indigo-600/10 border border-indigo-600/20 text-indigo-400" : 
                  currentStep > i ? "text-emerald-400" : "text-slate-500"
                )}
              >
                <div className={cn(
                  "h-8 w-8 rounded-lg flex items-center justify-center font-black text-xs border transition-all",
                  currentStep === i ? "bg-indigo-600 border-indigo-500 text-white shadow-lg shadow-indigo-900/20" : 
                  currentStep > i ? "bg-emerald-600/20 border-emerald-500/30 text-emerald-400" : "bg-slate-800 border-slate-700"
                )}>
                  {currentStep > i ? <CheckCircle2 size={14} /> : i + 1}
                </div>
                <div className="flex flex-col">
                  <Text className={cn("text-[10px] font-black uppercase tracking-widest", currentStep === i ? "text-indigo-400" : currentStep > i ? "text-emerald-400" : "text-slate-500")}>
                    {step.title}
                  </Text>
                </div>
              </div>
            ))}
          </div>

          <div className="pt-6 border-t border-slate-800">
            <Text className="text-[10px] text-slate-500 font-bold uppercase tracking-widest leading-relaxed">
              Define high-volume events with automated flow and scoring.
            </Text>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 bg-white flex flex-col relative">
          <div className="absolute top-6 right-6 z-10">
             <Button type="text" icon={<Trash2 size={16} />} className="text-slate-400 hover:text-rose-500 transition-colors" onClick={onClose} />
          </div>

          <div className="flex-1 overflow-y-auto p-12 custom-scrollbar">
            <Form form={form} layout="vertical" requiredMark={false}>
              {currentStep === 0 && <StepSetup />}
              {currentStep === 1 && <StepInterviewFlow />}
              {currentStep === 2 && <StepCandidateHandling />}
              {currentStep === 3 && <StepEvaluation />}
              {currentStep === 4 && <StepPreview values={form.getFieldsValue()} />}
            </Form>
          </div>

          {/* Footer Navigation */}
          <div className="h-20 border-t border-slate-100 px-12 flex items-center justify-between bg-slate-50/50">
            <Button 
              disabled={currentStep === 0}
              onClick={prev}
              icon={<ChevronLeft size={16} />}
              className="h-11 px-6 rounded-xl border-slate-200 text-slate-600 font-black text-[10px] uppercase tracking-widest"
            >
              Back
            </Button>
            
            {currentStep === steps.length - 1 ? (
              <Button 
                onClick={onSuccess}
                type="primary"
                className="h-11 px-8 bg-emerald-600 hover:bg-emerald-700 border-none rounded-xl shadow-emerald-100 shadow-xl font-black text-[10px] uppercase tracking-widest"
              >
                Launch Drive
              </Button>
            ) : (
              <Button 
                onClick={next}
                type="primary"
                className="h-11 px-8 bg-indigo-600 hover:bg-indigo-700 border-none rounded-xl shadow-indigo-100 shadow-xl font-black text-[10px] uppercase tracking-widest"
              >
                Continue <ChevronRight size={16} className="ml-1" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </Modal>
  )
}

// ─── Step Components ────────────────────────────────────────────────────────

function StepSetup() {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <Title level={3} className="!font-black !m-0 text-slate-900 uppercase tracking-tight">Setup Drive</Title>
        <Text className="text-slate-400 text-xs font-bold uppercase tracking-widest">Primary event parameters</Text>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <Form.Item name="name" label={<span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Drive Name</span>} className="col-span-2">
          <Input placeholder="e.g. Q2 Engineering Mega Drive" className="h-11 rounded-xl border-slate-200" />
        </Form.Item>
        <Form.Item name="role" label={<span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Role / Domain</span>}>
          <Input placeholder="e.g. Full Stack Engineer" className="h-11 rounded-xl border-slate-200" />
        </Form.Item>
        <Form.Item name="date" label={<span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Drive Date</span>}>
          <DatePicker className="h-11 w-full rounded-xl border-slate-200" />
        </Form.Item>
        <Form.Item name="mode" label={<span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Mode</span>}>
          <Select className="h-11 rounded-xl" placeholder="Select mode">
            <Option value="onsite">Onsite</Option>
            <Option value="virtual">Virtual</Option>
            <Option value="hybrid">Hybrid</Option>
          </Select>
        </Form.Item>
        <Form.Item name="location" label={<span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Location</span>}>
          <Input placeholder="e.g. Bangalore HQ" className="h-11 rounded-xl border-slate-200" />
        </Form.Item>
        <Form.Item name="description" label={<span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Description</span>} className="col-span-2">
          <TextArea rows={4} placeholder="Internal drive description and goals..." className="rounded-xl border-slate-200" />
        </Form.Item>
      </div>
    </div>
  )
}

function StepInterviewFlow() {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between">
        <div>
          <Title level={3} className="!font-black !m-0 text-slate-900 uppercase tracking-tight">Interview Flow</Title>
          <Text className="text-slate-400 text-xs font-bold uppercase tracking-widest">Define stages and evaluators</Text>
        </div>
        <Button icon={<Plus size={14} />} className="h-9 text-[9px] font-black uppercase tracking-widest bg-slate-900 text-white rounded-xl border-none shadow-lg">
          Add Stage
        </Button>
      </div>

      <div className="space-y-4">
        {[
          { stage: 'Screening', type: 'MCQ Test', evaluator: 'Automated' },
          { stage: 'Technical Round 1', type: 'Coding', evaluator: 'Tech Team' },
          { stage: 'Final HR', type: 'Behavioral', evaluator: 'HR Leads' }
        ].map((s, i) => (
          <Card key={i} className="rounded-2xl border-slate-100 shadow-soft-sm hover:border-indigo-200 transition-colors" bodyStyle={{ padding: '16px 24px' }}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-6">
                <div className="h-8 w-8 rounded-full bg-slate-50 flex items-center justify-center text-slate-400 font-black text-xs border border-slate-100">{i + 1}</div>
                <div>
                   <Text className="block text-xs font-black text-slate-800 uppercase">{s.stage}</Text>
                   <Text className="text-[9px] text-indigo-600 font-bold uppercase">{s.type}</Text>
                </div>
              </div>
              <div className="flex items-center gap-12">
                 <div className="text-right">
                    <Text className="block text-[9px] text-slate-400 font-black uppercase mb-1">Evaluator</Text>
                    <div className="flex items-center gap-2">
                       <Avatar size={16} className="bg-amber-100 text-amber-600 font-black text-[7px] border-none">E</Avatar>
                       <Text className="text-[10px] font-bold text-slate-600 uppercase">{s.evaluator}</Text>
                    </div>
                 </div>
                 <Button type="text" icon={<Trash2 size={14} />} className="text-slate-300" />
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}

function StepCandidateHandling() {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <Title level={3} className="!font-black !m-0 text-slate-900 uppercase tracking-tight">Candidate Handling</Title>
        <Text className="text-slate-400 text-xs font-bold uppercase tracking-widest">Queue and capacity management</Text>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <Card className="rounded-2xl border-indigo-50 bg-indigo-50/20 p-4" bodyStyle={{ padding: 0 }}>
           <div className="flex items-center gap-3 mb-4">
              <div className="h-8 w-8 rounded-lg bg-indigo-600 text-white flex items-center justify-center"><Users size={16} /></div>
              <Text className="text-[10px] font-black uppercase tracking-widest text-indigo-900">Bulk Entry</Text>
           </div>
           <Button block className="h-10 border-indigo-200 text-indigo-600 font-black text-[10px] uppercase rounded-xl">Upload CSV / Excel</Button>
           <Text className="block text-[9px] text-indigo-400 font-medium mt-2">Maximum 500 candidates per batch.</Text>
        </Card>

        <div className="space-y-4">
          <Form.Item label={<span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Capacity per Slot</span>}>
            <InputNumber className="h-11 w-full rounded-xl" min={1} defaultValue={20} />
          </Form.Item>
          <Form.Item label={<span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Auto-Queue Management</span>}>
            <Switch defaultChecked />
            <Text className="text-[10px] font-bold text-slate-400 uppercase ml-3">Smart load balancing</Text>
          </Form.Item>
        </div>
      </div>
    </div>
  )
}

function StepEvaluation() {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <Title level={3} className="!font-black !m-0 text-slate-900 uppercase tracking-tight">Evaluation Strategy</Title>
        <Text className="text-slate-400 text-xs font-bold uppercase tracking-widest">Scorecards and decision logic</Text>
      </div>

      <div className="space-y-6">
        <Card className="rounded-2xl border-slate-100 shadow-soft-sm" title={<span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Scorecard Mapping</span>}>
           <div className="flex items-center justify-between mb-4">
              <Text className="text-xs font-bold text-slate-600">Standard Engineering Scorecard</Text>
              <Button type="link" size="small" className="text-[10px] font-black uppercase tracking-widest">Change</Button>
           </div>
           <div className="flex gap-2">
              {['Coding', 'System Design', 'Behavioral', 'Culture'].map(t => <Tag key={t} className="bg-slate-50 border-slate-200 text-slate-500 text-[9px] font-black uppercase px-2 rounded-lg">{t}</Tag>)}
           </div>
        </Card>

        <Card className="rounded-2xl border-slate-100 shadow-soft-sm" title={<span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Pass / Reject Logic</span>}>
           <div className="flex items-center gap-6">
              <div className="flex-1">
                 <Text className="text-[10px] font-black text-slate-400 uppercase block mb-2">Minimum Score for Pass</Text>
                 <InputNumber className="h-11 w-full rounded-xl" min={0} max={100} defaultValue={70} />
              </div>
              <div className="flex-1">
                 <Text className="text-[10px] font-black text-slate-400 uppercase block mb-2">Auto-Reject Below</Text>
                 <InputNumber className="h-11 w-full rounded-xl" min={0} max={100} defaultValue={40} />
              </div>
           </div>
        </Card>
      </div>
    </div>
  )
}

function StepPreview({ values }: any) {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <Title level={3} className="!font-black !m-0 text-slate-900 uppercase tracking-tight">Review & Launch</Title>
        <Text className="text-slate-400 text-xs font-bold uppercase tracking-widest">Final drive configuration</Text>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <Card className="rounded-3xl border-slate-100 shadow-soft-sm bg-slate-50/50" bodyStyle={{ padding: 24 }}>
             <div className="flex items-center gap-4 mb-6">
                <div className="h-12 w-12 rounded-2xl bg-slate-900 text-white flex items-center justify-center shadow-lg"><Zap size={24} /></div>
                <div>
                   <h2 className="text-xl font-black text-slate-900 uppercase tracking-tight">{values.name || 'Untitled Drive'}</h2>
                   <Text className="text-[10px] font-black text-indigo-600 uppercase tracking-[0.2em]">{values.role || 'No Role Set'}</Text>
                </div>
             </div>

             <div className="grid grid-cols-2 gap-y-4">
                <div className="flex items-center gap-3">
                   <Calendar size={16} className="text-slate-400" />
                   <Text className="text-xs font-bold text-slate-600">{values.date ? dayjs(values.date).format('MMM D, YYYY') : 'Not scheduled'}</Text>
                </div>
                <div className="flex items-center gap-3">
                   {values.mode === 'virtual' ? <Globe size={16} className="text-blue-500" /> : <MapPin size={16} className="text-orange-500" />}
                   <Text className="text-xs font-bold text-slate-600 uppercase">{values.location || (values.mode === 'virtual' ? 'Virtual' : 'No Location')}</Text>
                </div>
             </div>
          </Card>

          <Card className="rounded-3xl border-slate-100 shadow-soft-sm" title={<span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Flow Summary</span>}>
             <div className="flex items-center gap-3">
                <div className="flex-1 h-1 bg-indigo-600 rounded-full" />
                <ChevronRight size={12} className="text-slate-300" />
                <div className="flex-1 h-1 bg-indigo-600 rounded-full" />
                <ChevronRight size={12} className="text-slate-300" />
                <div className="flex-1 h-1 bg-slate-200 rounded-full" />
             </div>
             <div className="flex justify-between mt-3 px-1">
                <Text className="text-[9px] font-black text-slate-400 uppercase">Screening</Text>
                <Text className="text-[9px] font-black text-slate-400 uppercase">Tech R1</Text>
                <Text className="text-[9px] font-black text-slate-400 uppercase">HR</Text>
             </div>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="rounded-3xl border-slate-100 shadow-soft-sm text-center py-6" bodyStyle={{ padding: 12 }}>
             <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Target Capacity</p>
             <p className="text-3xl font-black text-slate-800">500+</p>
             <Text className="text-[9px] text-emerald-600 font-bold uppercase">Candidate Limit</Text>
          </Card>

          <Card className="rounded-3xl border-slate-100 shadow-soft-sm" title={<span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Linked Jobs</span>}>
             <div className="space-y-2">
                <div className="flex items-center gap-2 p-2 bg-slate-50 rounded-xl">
                   <div className="h-6 w-6 rounded bg-white border border-slate-200 flex items-center justify-center text-[10px] font-black">JS</div>
                   <Text className="text-[10px] font-bold text-slate-700 truncate">Software Engineer II</Text>
                </div>
             </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
