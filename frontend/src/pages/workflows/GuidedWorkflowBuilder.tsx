import React, { useState } from 'react'
import {
  Typography,
  Card,
  Button,
  Space,
  Tag,
  Divider,
  Input,
  Select,
  Form,
  Steps,
  Row,
  Col,
  Checkbox,
  InputNumber,
  Radio,
  Collapse,
  Switch,
  message,
} from 'antd'
import {
  Rocket,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  Clock,
  Building2,
  Users,
  Briefcase,
  FileText,
  Calendar,
  DollarSign,
  UserCheck,
  Send,
  Zap,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'

const { Title, Text, Paragraph } = Typography
const { Step } = Steps
const { Panel } = Collapse

type FlowType =
  | 'e2e-hiring'
  | 'company-hiring'
  | 'agency-recruitment'
  | 'interview'
  | 'offer'
  | 'onboarding'
  | 'custom'

interface GuidedBuilderProps {
  initialFlowType?: FlowType
}

export default function GuidedWorkflowBuilder({ initialFlowType }: GuidedBuilderProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [flowType, setFlowType] = useState<FlowType | null>(initialFlowType || null)
  const navigate = useNavigate()
  const [form] = Form.useForm()

  const handleFlowTypeSelect = (type: FlowType) => {
    setFlowType(type)
    setCurrentStep(1)
  }

  const next = () => setCurrentStep(currentStep + 1)
  const prev = () => setCurrentStep(currentStep - 1)

  // ─── Flow Type Selection ──────────────────────────────────────────────────

  if (currentStep === 0) {
    return (
      <div className="mx-auto max-w-5xl py-12">
        <div className="text-center mb-12">
          <Title level={2}>What kind of process are you building?</Title>
          <Paragraph className="text-slate-500">
            Select a template to start with. Our guided builder will help you configure the business rules for your workflow.
          </Paragraph>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <FlowTypeCard
            type="e2e-hiring"
            title="End-to-End Hiring Flow"
            description="Complete lifecycle from job creation to candidate onboarding."
            icon={<Rocket className="text-indigo-500" />}
            onClick={() => handleFlowTypeSelect('e2e-hiring')}
          />
          <FlowTypeCard
            type="company-hiring"
            title="Company Internal Flow"
            description="Standard internal hiring process for company teams."
            icon={<Building2 className="text-blue-500" />}
            onClick={() => handleFlowTypeSelect('company-hiring')}
          />
          <FlowTypeCard
            type="agency-recruitment"
            title="Agency Recruitment Flow"
            description="Specialized flow for agency sourcing, submission, and placements."
            icon={<Users className="text-emerald-500" />}
            onClick={() => handleFlowTypeSelect('agency-recruitment')}
          />
          <FlowTypeCard
            type="interview"
            title="Interview Flow"
            description="Configure multi-round interview stages and scheduling rules."
            icon={<Calendar className="text-cyan-500" />}
            onClick={() => handleFlowTypeSelect('interview')}
          />
          <FlowTypeCard
            type="offer"
            title="Offer & Negotiation"
            description="Approvals, salary bands, and negotiation logic."
            icon={<DollarSign className="text-amber-500" />}
            onClick={() => handleFlowTypeSelect('offer')}
          />
          <FlowTypeCard
            type="onboarding"
            title="Onboarding & Handoff"
            description="Post-acceptance tasks and HRMS system integration."
            icon={<UserCheck className="text-purple-500" />}
            onClick={() => handleFlowTypeSelect('onboarding')}
          />
        </div>
      </div>
    )
  }

  // ─── Step Configuration ──────────────────────────────────────────────────

  const e2eSteps = [
    { title: 'Job Setup', icon: <Briefcase size={16} /> },
    { title: 'Hiring Plan', icon: <FileText size={16} /> },
    { title: 'Agency Rules', icon: <Users size={16} /> },
    { title: 'Qualification', icon: <UserCheck size={16} /> },
    { title: 'Interviewing', icon: <Calendar size={16} /> },
    { title: 'Scheduling', icon: <Clock size={16} /> },
    { title: 'Offer & Terms', icon: <DollarSign size={16} /> },
    { title: 'Documents', icon: <FileText size={16} /> },
    { title: 'Onboarding', icon: <Send size={16} /> },
    { title: 'Automation', icon: <Zap size={16} /> },
  ]

  const agencySteps = [
    { title: 'Job Intake', icon: <Briefcase size={16} /> },
    { title: 'Talent Pool', icon: <Users size={16} /> },
    { title: 'Submission', icon: <Send size={16} /> },
    { title: 'Coordination', icon: <Calendar size={16} /> },
    { title: 'Offer & Placement', icon: <DollarSign size={16} /> },
    { title: 'Guarantee', icon: <CheckCircle2 size={16} /> },
  ]

  const activeSteps = flowType === 'agency-recruitment' ? agencySteps : e2eSteps

  return (
    <div className="mx-auto max-w-6xl py-8">
      <div className="flex items-center justify-between mb-8">
        <Space direction="vertical" size={0}>
          <Text className="text-[10px] font-black uppercase tracking-widest text-indigo-400">Guided Builder</Text>
          <Title level={3} className="!m-0">{flowType === 'e2e-hiring' ? 'End-to-End Hiring Workflow' : flowType === 'agency-recruitment' ? 'Agency Recruitment Flow' : 'Configure Process'}</Title>
        </Space>
        <Space>
          <Button onClick={() => setCurrentStep(0)} ghost>Change Template</Button>
          <Button type="primary" className="rounded-xl h-10 font-bold bg-indigo-600 border-none shadow-lg">Save Workflow</Button>
        </Space>
      </div>

      <Row gutter={32}>
        <Col span={6}>
          <Steps
            direction="vertical"
            current={currentStep - 1}
            items={activeSteps.map(s => ({ title: s.title, icon: s.icon }))}
            className="sticky top-8"
          />
        </Col>
        <Col span={18}>
          <Card className="rounded-3xl border-slate-200 shadow-sm p-6">
            <Form form={form} layout="vertical">
              {currentStep === 1 && flowType === 'e2e-hiring' && <JobSetupSection />}
              {currentStep === 2 && flowType === 'e2e-hiring' && <HiringPlanSection />}
              {currentStep === 3 && flowType === 'e2e-hiring' && <AgencyRulesSection />}
              {currentStep === 4 && flowType === 'e2e-hiring' && <CandidateQualificationSection />}
              {currentStep === 5 && flowType === 'e2e-hiring' && <InterviewPlanSection />}
              {currentStep === 6 && flowType === 'e2e-hiring' && <SchedulingRulesSection />}
              {currentStep === 7 && flowType === 'e2e-hiring' && <OfferRulesSection />}
              {currentStep === 8 && flowType === 'e2e-hiring' && <DocumentGenerationSection />}
              {currentStep === 9 && flowType === 'e2e-hiring' && <OnboardingSection />}
              {currentStep === 10 && flowType === 'e2e-hiring' && <AutomationSlaSection />}

              {currentStep === 1 && flowType === 'agency-recruitment' && <AgencyJobIntakeSection />}
              {currentStep === 2 && flowType === 'agency-recruitment' && <AgencyTalentPoolSection />}
              {currentStep === 3 && flowType === 'agency-recruitment' && <AgencySubmissionSection />}
              {currentStep === 4 && flowType === 'agency-recruitment' && <AgencyInterviewCoordinationSection />}
              {currentStep === 5 && flowType === 'agency-recruitment' && <AgencyOfferPlacementSection />}
              {currentStep === 6 && flowType === 'agency-recruitment' && <AgencyGuaranteeSection />}

              <div className="mt-12 flex justify-between pt-6 border-t border-slate-100">
                <Button 
                  icon={<ArrowLeft size={16}/>} 
                  onClick={prev}
                  disabled={currentStep === 1}
                  className="rounded-xl h-10 px-6 font-bold"
                >
                  Previous Section
                </Button>
                <Button 
                  type="primary" 
                  onClick={next}
                  disabled={currentStep === activeSteps.length}
                  className="rounded-xl h-10 px-8 font-bold bg-indigo-600 border-none shadow-lg"
                >
                  Next: {activeSteps[currentStep]?.title || 'Finish'} <ArrowRight size={16} className="ml-2" />
                </Button>
              </div>
            </Form>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

function FlowTypeCard({ type, title, description, icon, onClick }: any) {
  return (
    <Card 
      hoverable 
      className="rounded-3xl border-slate-200 text-center p-6 transition-all hover:border-indigo-300 hover:shadow-xl group"
      onClick={onClick}
    >
      <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-50 group-hover:bg-indigo-50 transition-colors">
        {React.cloneElement(icon, { size: 32 })}
      </div>
      <Title level={4} className="!mb-2">{title}</Title>
      <Paragraph className="text-slate-500 text-sm mb-6">{description}</Paragraph>
      <Button block className="rounded-xl font-bold group-hover:bg-indigo-600 group-hover:text-white transition-all">Start Building</Button>
    </Card>
  )
}

// ─── Business Sections ────────────────────────────────────────────────────

function JobSetupSection() {
  return (
    <div className="space-y-6">
      <Title level={4}>1. Job Creation & Approval</Title>
      <Paragraph className="text-slate-500">Define how jobs are initiated and who needs to approve them before they go live.</Paragraph>
      
      <Form.Item label="Who can create a job requisition?" name="creator_role" initialValue="hiring_manager">
        <Radio.Group>
          <Radio value="hiring_manager">Hiring Manager</Radio>
          <Radio value="recruiter">Recruiter Only</Radio>
          <Radio value="any">Any Department Head</Radio>
        </Radio.Group>
      </Form.Item>

      <Form.Item label="Approval Workflow" name="requires_approval" initialValue={true}>
        <Switch checkedChildren="Required" unCheckedChildren="Not Required" defaultChecked />
      </Form.Item>

      <Form.Item label="Recruiter Assignment" name="recruiter_assignment" initialValue="auto">
        <Select options={[
          { label: 'Automatic (Round Robin)', value: 'auto' },
          { label: 'Manual by HR Manager', value: 'manual' },
          { label: 'Specific Recruiter Team', value: 'team' },
        ]} />
      </Form.Item>
    </div>
  )
}

function HiringPlanSection() {
  return (
    <div className="space-y-6">
      <Title level={4}>2. Hiring Plan</Title>
      <Form.Item label="Sourcing Strategy" name="sourcing_strategy" initialValue="hybrid">
        <Radio.Group>
          <Radio value="internal">Internal Only</Radio>
          <Radio value="external">External Only</Radio>
          <Radio value="hybrid">Hybrid (Internal + External)</Radio>
        </Radio.Group>
      </Form.Item>

      <Form.Item label="Interview Rounds" name="interview_rounds" initialValue={3}>
        <InputNumber min={1} max={10} />
      </Form.Item>

      <Form.Item label="Stage SLA (Days)" name="stage_sla" initialValue={2}>
        <InputNumber min={1} max={30} />
      </Form.Item>
    </div>
  )
}

function AgencyRulesSection() {
  return (
    <div className="space-y-6">
      <Title level={4}>3. Agency Participation</Title>
      <Form.Item label="Enable Agencies" name="agencies_enabled" initialValue={true}>
        <Switch defaultChecked />
      </Form.Item>

      <Form.Item label="Submission Rules" name="submission_rules">
        <Checkbox.Group options={[
          { label: 'Validate Ownership/Protection', value: 'ownership' },
          { label: 'Duplicate Control (Email Match)', value: 'duplicate_email' },
          { label: 'Duplicate Control (Mobile Match)', value: 'duplicate_mobile' },
        ]} />
      </Form.Item>
    </div>
  )
}

function CandidateQualificationSection() {
  return (
    <div className="space-y-6">
      <Title level={4}>4. Candidate Qualification</Title>
      <Form.Item label="Prequalification Required" name="prequal_required">
        <Switch />
      </Form.Item>
      <Form.Item label="Auto-Screening Conditions" name="auto_screen">
        <Select mode="multiple" placeholder="Select criteria..." options={[
          { label: 'Years of Experience > 5', value: 'exp_5' },
          { label: 'Must have LinkedIn Profile', value: 'linkedin' },
          { label: 'Location Match', value: 'location' },
        ]} />
      </Form.Item>
    </div>
  )
}

function InterviewPlanSection() {
  return (
    <div className="space-y-6">
      <Title level={4}>5. Interview Plan</Title>
      <Collapse defaultActiveKey={['1']}>
        <Panel header="Round 1: Screening" key="1">
          <Form.Item label="Interviewer" initialValue="recruiter">
            <Select options={[{label: 'Recruiter', value: 'recruiter'}]} />
          </Form.Item>
        </Panel>
        <Panel header="Round 2: Technical" key="2">
          <Form.Item label="Interviewer" initialValue="panel">
            <Select options={[{label: 'Technical Panel', value: 'panel'}]} />
          </Form.Item>
        </Panel>
      </Collapse>
    </div>
  )
}

function OfferRulesSection() {
  return (
    <div className="space-y-6">
      <Title level={4}>6. Offer & Terms</Title>
      <Form.Item label="Salary Band Logic" name="salary_band">
        <Checkbox>Enforce budget bands</Checkbox>
      </Form.Item>
      <Form.Item label="Negotiation Allowed" name="negotiation_allowed">
        <Switch defaultChecked />
      </Form.Item>
      <Form.Item label="Max Negotiation Rounds" name="neg_rounds" initialValue={2}>
        <InputNumber min={1} max={5} />
      </Form.Item>
      <Form.Item label="Approval above threshold" name="threshold_approval" initialValue={true}>
        <Switch defaultChecked />
      </Form.Item>
    </div>
  )
}

function OnboardingSection() {
  return (
    <div className="space-y-6">
      <Title level={4}>9. Onboarding & Handoff</Title>
      <Form.Item label="HRMS Handoff" name="hrms_integration">
        <Select options={[
          { label: 'Automatic (SAP SuccessFactors)', value: 'sap' },
          { label: 'Automatic (Workday)', value: 'workday' },
          { label: 'Manual Export', value: 'manual' },
        ]} />
      </Form.Item>
      <Form.Item label="Onboarding Checklist" name="onboarding_checklist">
        <Checkbox.Group options={[
          { label: 'Background Check', value: 'bgc' },
          { label: 'IT Equipment Request', value: 'it' },
          { label: 'Document Signature', value: 'sign' },
        ]} />
      </Form.Item>
    </div>
  )
}

function SchedulingRulesSection() {
  return (
    <div className="space-y-6">
      <Title level={4}>6. Scheduling Rules</Title>
      <Form.Item label="Scheduling Mode" name="scheduling_mode" initialValue="auto">
        <Radio.Group>
          <Radio value="auto">Automated (Smart Slot Finder)</Radio>
          <Radio value="manual">Manual (Recruiter Managed)</Radio>
        </Radio.Group>
      </Form.Item>
      <Form.Item label="Availability Check" name="availability_check">
        <Checkbox.Group options={[
          { label: 'Interviewer Calendar', value: 'interviewer' },
          { label: 'Hiring Manager Calendar', value: 'hm' },
          { label: 'Meeting Room Availability', value: 'room' },
        ]} />
      </Form.Item>
    </div>
  )
}

function DocumentGenerationSection() {
  return (
    <div className="space-y-6">
      <Title level={4}>8. Document Generation</Title>
      <Form.Item label="Generate Offer Letter" name="gen_offer" initialValue={true}>
        <Switch defaultChecked />
      </Form.Item>
      <Form.Item label="Electronic Signature" name="e_sign" initialValue={true}>
        <Switch defaultChecked />
      </Form.Item>
      <Form.Item label="Additional Documents" name="extra_docs">
        <Checkbox.Group options={[
          { label: 'Non-Disclosure Agreement', value: 'nda' },
          { label: 'Employment Contract', value: 'contract' },
          { label: 'Benefit Summary', value: 'benefits' },
        ]} />
      </Form.Item>
    </div>
  )
}

function AutomationSlaSection() {
  return (
    <div className="space-y-6">
      <Title level={4}>10. Notifications / Tasks / SLA</Title>
      <Form.Item label="Reminders" name="reminders">
        <Checkbox.Group options={[
          { label: 'Interview Reminders (Candidate)', value: 'rem_cand' },
          { label: 'Interview Reminders (Interviewer)', value: 'rem_int' },
          { label: 'Offer Follow-up (Candidate)', value: 'rem_offer' },
        ]} />
      </Form.Item>
      <Form.Item label="SLA Breach Action" name="sla_action">
        <Select options={[
          { label: 'Escalate to Manager', value: 'escalate' },
          { label: 'Notify HR Team', value: 'notify_hr' },
          { label: 'Re-assign Task', value: 'reassign' },
        ]} />
      </Form.Item>
    </div>
  )
}

// ─── Agency Specific Sections ─────────────────────────────────────────────

function AgencyJobIntakeSection() {
  return (
    <div className="space-y-6">
      <Title level={4}>1. Client Job Intake</Title>
      <Form.Item label="Recruiter Assignment" name="agency_recruiter">
        <Select options={[{ label: 'Assign to Account Manager', value: 'am' }, { label: 'Pool Assignment', value: 'pool' }]} />
      </Form.Item>
      <Form.Item label="Sourcing Start Trigger" name="sourcing_trigger">
        <Switch checkedChildren="Manual" unCheckedChildren="Auto" />
      </Form.Item>
    </div>
  )
}

function AgencyTalentPoolSection() {
  return (
    <div className="space-y-6">
      <Title level={4}>2. Talent Pool Qualification</Title>
      <Form.Item label="Qualification Checks" name="qualification_checks">
        <Checkbox.Group options={[
          { label: 'Salary Aligned', value: 'salary' },
          { label: 'Availability Confirmed', value: 'availability' },
          { label: 'Pre-screened', value: 'prescreen' },
        ]} />
      </Form.Item>
    </div>
  )
}

function AgencySubmissionSection() {
  return (
    <div className="space-y-6">
      <Title level={4}>3. Client Submission</Title>
      <Form.Item label="Internal Review Required" name="internal_review">
        <Switch />
      </Form.Item>
      <Form.Item label="Wait for Client Response (Days)" name="client_wait_days">
        <InputNumber min={1} max={14} defaultValue={3} />
      </Form.Item>
    </div>
  )
}

function AgencyInterviewCoordinationSection() {
  return (
    <div className="space-y-6">
      <Title level={4}>4. Interview Coordination</Title>
      <Form.Item label="Coordination Mode" name="coord_mode">
        <Radio.Group>
          <Radio value="automated">Automated (System Scheduler)</Radio>
          <Radio value="manual">Manual (Recruiter Handled)</Radio>
        </Radio.Group>
      </Form.Item>
    </div>
  )
}

function AgencyOfferPlacementSection() {
  return (
    <div className="space-y-6">
      <Title level={4}>5. Offer & Placement</Title>
      <Form.Item label="Counter Offer Tracking" name="counter_tracking">
        <Switch defaultChecked />
      </Form.Item>
    </div>
  )
}

function AgencyGuaranteeSection() {
  return (
    <div className="space-y-6">
      <Title level={4}>6. Guarantee & Closure</Title>
      <Form.Item label="Guarantee Period (Months)" name="guarantee_period">
        <InputNumber min={1} max={12} defaultValue={3} />
      </Form.Item>
    </div>
  )
}
