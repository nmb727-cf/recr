import { useState } from 'react'
import { Alert, Button, Card, Collapse, Input, Space, Typography, message } from 'antd'
import { useNavigate } from 'react-router-dom'
import {
  Bug,
  CircleHelp,
  Headphones,
  Lightbulb,
  Mic,
  MonitorSmartphone,
  Video,
  Wifi,
} from 'lucide-react'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input

function SectionCard({
  title,
  icon: Icon,
  subtitle,
  children,
}: {
  title: string
  icon: React.ElementType
  subtitle: string
  children: React.ReactNode
}) {
  return (
    <Card className="rounded-3xl border-slate-200 shadow-sm">
      <div className="mb-4 flex items-start gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <div className="text-sm font-black uppercase tracking-wider text-slate-900">{title}</div>
          <div className="mt-1 text-sm text-slate-500">{subtitle}</div>
        </div>
      </div>
      {children}
    </Card>
  )
}

export default function CandidateInterviewHelp() {
  const navigate = useNavigate()
  const [supportMessage, setSupportMessage] = useState('')

  const faqItems = [
    {
      key: 'join',
      label: 'How do I join an interview?',
      children:
        'Open Interviews from the candidate portal, select the interview row, and use Join Interview. You can also open the interview details first if you want to review instructions before starting.',
    },
    {
      key: 'reschedule',
      label: 'How do I reschedule an interview?',
      children:
        'Use the Reschedule or Schedule action available on eligible interview rows. If self-scheduling is enabled, the system will open the available slot picker for that interview.',
    },
    {
      key: 'technical',
      label: 'What should I do if I have a technical issue?',
      children:
        'Run the preparation system checks, confirm browser permissions for camera and microphone, refresh the page, and retry from the interview instructions or runtime screen.',
    },
    {
      key: 'instructions',
      label: 'Where can I see interview instructions?',
      children:
        'Use View Details on any interview from the candidate interviews dashboard. Instructions, access window, and runtime guidance are shown there.',
    },
  ]

  const troubleshooting = [
    {
      icon: Video,
      title: 'Camera Issues',
      body: 'Check browser camera permissions, close other apps using the camera, and retry from the preparation center.',
    },
    {
      icon: Mic,
      title: 'Microphone Issues',
      body: 'Check mic permissions, system input device settings, and mute state before joining again.',
    },
    {
      icon: Wifi,
      title: 'Internet Issues',
      body: 'Switch to a stable network, avoid heavy downloads, and stay close to the router if possible.',
    },
    {
      icon: MonitorSmartphone,
      title: 'Login / Device Issues',
      body: 'Refresh the portal, retry from the candidate dashboard, and use a supported desktop browser when possible.',
    },
  ]

  const supportItems = [
    'Connection issue during live interview',
    'Audio or video issue during runtime',
    'Browser compatibility question',
    'Need help understanding interview instructions',
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <Title level={3} className="!mb-1 !mt-0">
            Interview Help
          </Title>
          <Text className="text-sm text-slate-500">
            Find quick answers, troubleshooting guidance, and candidate-side interview support in one place.
          </Text>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button onClick={() => navigate('/candidate/interviews')}>Back to Interviews</Button>
          <Button type="primary" onClick={() => navigate('/candidate/interviews/preparation')}>
            Open Preparation
          </Button>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-6">
          <SectionCard
            title="FAQ"
            icon={CircleHelp}
            subtitle="Common interview help topics for joining, rescheduling, and instructions."
          >
            <Collapse
              items={faqItems.map((item) => ({
                key: item.key,
                label: <span className="text-sm font-semibold text-slate-900">{item.label}</span>,
                children: <Paragraph className="!mb-0 text-sm text-slate-600">{item.children}</Paragraph>,
              }))}
            />
          </SectionCard>

          <SectionCard
            title="Technical Support"
            icon={Headphones}
            subtitle="Candidate-side help for connection, audio, video, and browser compatibility."
          >
            <div className="grid gap-4 md:grid-cols-2">
              {supportItems.map((item) => (
                <div key={item} className="rounded-2xl border border-slate-200 bg-white p-4">
                  <div className="text-sm font-semibold text-slate-900">{item}</div>
                  <div className="mt-2 text-sm text-slate-500">
                    Use the preparation center system checks first, then retry the interview runtime or instructions page.
                  </div>
                </div>
              ))}
            </div>
            <Alert
              className="mt-4"
              type="info"
              showIcon
              message="Browser Compatibility"
              description="For the best interview experience, use a current desktop browser with camera and microphone permissions enabled."
            />
          </SectionCard>

          <SectionCard
            title="Contact Support"
            icon={Bug}
            subtitle="Quick help message and future-ready support request flow."
          >
            <div className="space-y-4">
              <TextArea
                rows={5}
                placeholder="Describe the issue you are facing with your interview, scheduling, or access."
                value={supportMessage}
                onChange={(event) => setSupportMessage(event.target.value)}
              />
              <div className="flex flex-wrap gap-2">
                <Button
                  type="primary"
                  onClick={() => {
                    if (!supportMessage.trim()) {
                      message.info('Add a support message first')
                      return
                    }
                    message.success('Support request shell submitted')
                  }}
                >
                  Send Support Request
                </Button>
                <Button onClick={() => message.success('Help ticket shell created for future-ready support flow')}>
                  Create Help Ticket
                </Button>
                <Button onClick={() => navigate('/candidate/interviews/notifications')}>
                  Open Notifications
                </Button>
              </div>
              <div className="rounded-2xl border border-dashed border-slate-200 p-4 text-sm text-slate-500">
                Ticketing and routed support workflows are future ready. This page currently provides candidate-side quick help actions without a dedicated support backend.
              </div>
            </div>
          </SectionCard>

          <SectionCard
            title="Interview Guidance"
            icon={Lightbulb}
            subtitle="Tips, best practices, and preparation guidance for interviews."
          >
            <div className="space-y-3">
              {[
                'Review the interview instructions and format before your scheduled time.',
                'Prepare a quiet environment, stable internet connection, and a charged device.',
                'Keep examples, achievements, and project context ready for structured answers.',
                'Join a few minutes early when your interview type supports an early access window.',
              ].map((item) => (
                <div key={item} className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                  {item}
                </div>
              ))}
            </div>
          </SectionCard>
        </div>

        <div className="space-y-6">
          <SectionCard
            title="Troubleshooting"
            icon={MonitorSmartphone}
            subtitle="Quick fixes for common camera, microphone, internet, and login issues."
          >
            <div className="space-y-3">
              {troubleshooting.map((item) => {
                const Icon = item.icon
                return (
                  <div key={item.title} className="rounded-2xl border border-slate-200 bg-white p-4">
                    <div className="flex items-start gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 text-slate-600">
                        <Icon className="h-4 w-4" />
                      </div>
                      <div>
                        <div className="text-sm font-semibold text-slate-900">{item.title}</div>
                        <div className="mt-1 text-sm text-slate-500">{item.body}</div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </SectionCard>

          <SectionCard
            title="Quick Help"
            icon={Headphones}
            subtitle="Fast self-service actions for common interview needs."
          >
            <Space direction="vertical" size={12} className="w-full">
              <Button block type="primary" onClick={() => navigate('/candidate/interviews/preparation')}>
                Open Preparation Center
              </Button>
              <Button block onClick={() => navigate('/candidate/interviews/timeline')}>
                Open Interview Timeline
              </Button>
              <Button block onClick={() => navigate('/candidate/interviews/notifications')}>
                Open Notifications
              </Button>
              <Button block onClick={() => navigate('/candidate/interviews/results')}>
                Open Results
              </Button>
            </Space>
          </SectionCard>
        </div>
      </div>
    </div>
  )
}
