import { useState } from 'react'
import { Button, Typography, Alert } from 'antd'
import { CheckOutlined, ArrowRightOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { authApi, type OnboardingPayload } from '@/api/auth'
import { communicationsApi } from '@/api/communications'
import { useAuthStore } from '@/store/authStore'

const { Title, Text } = Typography

// ─── Step types ───────────────────────────────────────────────────────────────

interface StepOption {
  value: string
  label: string
  description: string
  icon: string
}

// A welcome step is purely informational — no selection required.
interface WelcomeStepConfig {
  kind: 'welcome'
  title: string
  subtitle: string
  icon: string
  highlights: string[]
}

// A selection step collects one choice from the user.
interface SelectionStepConfig {
  kind: 'selection'
  title: string
  subtitle: string
  field: keyof OnboardingPayload
  options: StepOption[]
}

interface ConnectEmailStepConfig {
  kind: 'connect_email'
  title: string
  subtitle: string
  options: StepOption[]
}

type StepConfig = WelcomeStepConfig | SelectionStepConfig | ConnectEmailStepConfig

// ─── Role-specific step sets ───────────────────────────────────────────────────

const COMPANY_STEPS: StepConfig[] = [
  {
    kind: 'welcome',
    title: "Let's set up your hiring workspace",
    subtitle: 'Three quick questions to configure your environment.',
    icon: '🏢',
    highlights: [
      'Configure your hiring pipeline and workflow',
      'Calibrate the UI for your team size',
      'Set your automation level',
    ],
  },
  {
    kind: 'selection',
    title: 'How do you hire?',
    subtitle: 'This shapes your default pipeline and workflow templates.',
    field: 'hiring_style',
    options: [
      { value: 'internal', label: 'In-house team', description: 'Your team handles all recruiting end-to-end', icon: '👥' },
      { value: 'agency', label: 'External agencies', description: 'Agencies source and screen candidates for you', icon: '🔗' },
      { value: 'mixed', label: 'Mixed approach', description: 'Combination of internal and agency recruiting', icon: '🔀' },
    ],
  },
  {
    kind: 'selection',
    title: 'How big is your team?',
    subtitle: "We'll calibrate the UI complexity and role structure.",
    field: 'team_size',
    options: [
      { value: '1-5', label: '1–5 people', description: 'Lean team, minimal overhead', icon: '🌱' },
      { value: '5-20', label: '5–20 people', description: 'Growing team with structured workflows', icon: '🌿' },
      { value: '20+', label: '20+ people', description: 'Scaled team needing full role management', icon: '🌳' },
    ],
  },
  {
    kind: 'selection',
    title: 'Automation preference',
    subtitle: 'Set how much the system should work for you automatically.',
    field: 'automation_preference',
    options: [
      { value: 'manual', label: 'Manual', description: 'Full control — you drive every action', icon: '🎛️' },
      { value: 'smart', label: 'Smart assist', description: 'Suggested automations, you approve', icon: '🧠' },
      { value: 'fully_automated', label: 'Fully automated', description: 'System handles routine tasks for you', icon: '🚀' },
    ],
  },
]

const AGENCY_STEPS: StepConfig[] = [
  {
    kind: 'welcome',
    title: "Let's set up your agency workspace",
    subtitle: 'Three quick questions to configure your recruitment environment.',
    icon: '🤝',
    highlights: [
      'Configure your placement and candidate pipeline',
      'Calibrate the UI for your consultant team size',
      'Set your automation level',
    ],
  },
  {
    kind: 'selection',
    title: 'What type of placements do you handle?',
    subtitle: 'This shapes your default pipeline and candidate tracking setup.',
    field: 'hiring_style',
    options: [
      { value: 'internal', label: 'Permanent placement', description: 'You place candidates in full-time roles', icon: '📋' },
      { value: 'agency', label: 'Contract / temp staffing', description: 'You fill short-term and contract positions', icon: '⏱️' },
      { value: 'mixed', label: 'Both types', description: 'Permanent and contract placements', icon: '🔀' },
    ],
  },
  {
    kind: 'selection',
    title: 'How big is your consultant team?',
    subtitle: "We'll calibrate the UI and role structure for your agency size.",
    field: 'team_size',
    options: [
      { value: '1-5', label: '1–5 consultants', description: 'Small agency, lean operations', icon: '🌱' },
      { value: '5-20', label: '5–20 consultants', description: 'Growing agency with structured workflows', icon: '🌿' },
      { value: '20+', label: '20+ consultants', description: 'Large agency needing full management tools', icon: '🌳' },
    ],
  },
  {
    kind: 'selection',
    title: 'Automation preference',
    subtitle: 'Set how much the system should work for you automatically.',
    field: 'automation_preference',
    options: [
      { value: 'manual', label: 'Manual', description: 'Full control — you drive every action', icon: '🎛️' },
      { value: 'smart', label: 'Smart assist', description: 'Suggested automations, you approve', icon: '🧠' },
      { value: 'fully_automated', label: 'Fully automated', description: 'System handles routine tasks for you', icon: '🚀' },
    ],
  },
]

const AGENCY_ROLES = ['agency_owner', 'agency_admin', 'agency_recruiter']

const CONNECT_EMAIL_STEP: ConnectEmailStepConfig = {
  kind: 'connect_email',
  title: 'Connect your email (optional)',
  subtitle: 'Connect now to send from your company or agency domain. You can skip and configure later in Settings.',
  options: [
    { value: 'gmail', label: 'Connect Gmail', description: 'Use Google Workspace or Gmail account', icon: '📧' },
    { value: 'outlook', label: 'Connect Outlook', description: 'Use Microsoft 365 / Outlook account', icon: '📨' },
    { value: 'skip', label: 'Skip for now', description: 'Use secure system fallback until you connect later', icon: '⏭️' },
  ],
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function WelcomeCard({ step }: { step: WelcomeStepConfig }) {
  return (
    <div style={{ textAlign: 'center', padding: '8px 0 4px' }}>
      <div style={{ fontSize: 52, marginBottom: 16 }}>{step.icon}</div>
      <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 8px', textAlign: 'left' }}>
        {step.highlights.map((h, i) => (
          <li
            key={i}
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 10,
              padding: '10px 0',
              borderBottom: i < step.highlights.length - 1 ? '1px solid #f1f5f9' : 'none',
            }}
          >
            <span style={{
              width: 22,
              height: 22,
              borderRadius: '50%',
              background: '#eff6ff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              marginTop: 1,
            }}>
              <CheckOutlined style={{ fontSize: 10, color: '#1e40af' }} />
            </span>
            <Text style={{ fontSize: 14, color: '#334155' }}>{h}</Text>
          </li>
        ))}
      </ul>
    </div>
  )
}

function OptionCard({
  option,
  selected,
  onClick,
}: {
  option: StepOption
  selected: boolean
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 16,
        width: '100%',
        padding: '16px 20px',
        border: `2px solid ${selected ? '#1e40af' : '#e2e8f0'}`,
        borderRadius: 12,
        background: selected ? '#eff6ff' : '#ffffff',
        cursor: 'pointer',
        textAlign: 'left',
        transition: 'all 0.15s ease',
      }}
    >
      <span style={{ fontSize: 28, flexShrink: 0 }}>{option.icon}</span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 600, fontSize: 15, color: '#0f172a', lineHeight: 1.3 }}>
          {option.label}
        </div>
        <div style={{ fontSize: 13, color: '#64748b', marginTop: 2 }}>
          {option.description}
        </div>
      </div>
      {selected && (
        <span style={{
          width: 22,
          height: 22,
          borderRadius: '50%',
          background: '#1e40af',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}>
          <CheckOutlined style={{ fontSize: 11, color: '#fff' }} />
        </span>
      )}
    </button>
  )
}

function ProgressBar({ current, total }: { current: number; total: number }) {
  return (
    <div style={{ marginBottom: 32 }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 8,
      }}>
        <Text style={{ fontSize: 12, color: '#64748b', fontWeight: 500 }}>
          Step {current + 1} of {total}
        </Text>
        <Text style={{ fontSize: 12, color: '#64748b' }}>
          {Math.round((current / total) * 100)}% complete
        </Text>
      </div>
      <div style={{ height: 4, background: '#e2e8f0', borderRadius: 4, overflow: 'hidden' }}>
        <div
          style={{
            height: '100%',
            width: `${(current / total) * 100}%`,
            background: '#1e40af',
            borderRadius: 4,
            transition: 'width 0.3s ease',
          }}
        />
      </div>
      <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
        {Array.from({ length: total }).map((_, i) => (
          <div
            key={i}
            style={{
              flex: 1,
              height: 3,
              borderRadius: 2,
              background: i <= current ? '#1e40af' : '#e2e8f0',
              transition: 'background 0.2s',
            }}
          />
        ))}
      </div>
    </div>
  )
}

// ─── Main wizard ──────────────────────────────────────────────────────────────

export default function OnboardingWizard() {
  const navigate = useNavigate()
  const user = useAuthStore(state => state.user)
  const setUser = useAuthStore(state => state.setUser)

  // Pick the correct step set based on signup role — no need to ask the user.
  const BASE_STEPS = user && AGENCY_ROLES.includes(user.role) ? AGENCY_STEPS : COMPANY_STEPS
  const STEPS = [...BASE_STEPS, CONNECT_EMAIL_STEP]

  const [step, setStep] = useState(0)
  const [selections, setSelections] = useState<Partial<OnboardingPayload>>({})
  const [connectChoice, setConnectChoice] = useState<string>('skip')
  const [onboardingSubmitted, setOnboardingSubmitted] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const currentStep = STEPS[step]
  const isLast = step === STEPS.length - 1
  const currentValue = currentStep.kind === 'selection'
    ? selections[currentStep.field]
    : currentStep.kind === 'connect_email'
      ? connectChoice
      : undefined

  const handleSelect = (value: string) => {
    if (currentStep.kind === 'selection') {
      setSelections(prev => ({ ...prev, [currentStep.field]: value as any }))
      return
    }
    if (currentStep.kind === 'connect_email') {
      setConnectChoice(value)
    }
  }

  const submitOnboarding = async () => {
    if (onboardingSubmitted) return
    const payload = selections as OnboardingPayload
    const { data: res } = await authApi.completeOnboarding(payload)
    setUser(res.data.user)
    setOnboardingSubmitted(true)
  }

  const handleNext = async () => {
    // Welcome step: no selection required — just advance
    if (currentStep.kind === 'welcome') {
      setStep(s => s + 1)
      return
    }

    if (!currentValue) return

    if (!isLast) {
      setStep(s => s + 1)
      return
    }

    // Final optional connect step.
    setSaving(true)
    setError(null)
    try {
      await submitOnboarding()
      if (connectChoice === 'gmail' || connectChoice === 'outlook') {
        const redirect_uri = `${window.location.origin}/settings?tab=communication`
        const response = connectChoice === 'gmail'
          ? await communicationsApi.initiateGmailConnect(redirect_uri)
          : await communicationsApi.initiateMicrosoftConnect(redirect_uri)
        const authUrl = response.data.data.auth_url
        if (authUrl) {
          window.location.href = authUrl
          return
        }
      }
      navigate('/dashboard', { replace: true })
    } catch (err: any) {
      setError(err?.response?.data?.message || 'Something went wrong. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  const canAdvance = currentStep.kind === 'welcome' || !!currentValue

  return (
    <div style={{
      minHeight: '100vh',
      background: '#f8fafc',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px 16px',
    }}>
      <div style={{ width: '100%', maxWidth: 520 }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 8,
            background: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: 24,
            padding: '6px 16px',
            marginBottom: 20,
          }}>
            <span style={{ fontSize: 16 }}>⚡</span>
            <Text style={{ fontSize: 13, fontWeight: 600, color: '#1e40af' }}>TalentOS Setup</Text>
          </div>
          <Title level={2} style={{ margin: 0, color: '#0f172a', fontSize: 26 }}>
            {currentStep.title}
          </Title>
          <Text type="secondary" style={{ display: 'block', marginTop: 8, fontSize: 14 }}>
            {currentStep.subtitle}
          </Text>
        </div>

        {/* Card */}
        <div style={{
          background: '#ffffff',
          borderRadius: 16,
          border: '1px solid #e2e8f0',
          padding: '28px 28px 24px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
        }}>
          <ProgressBar current={step} total={STEPS.length} />

          {error && (
            <Alert
              type="error"
              message={error}
              showIcon
              closable
              onClose={() => setError(null)}
              style={{ marginBottom: 20 }}
            />
          )}

          <div style={{ marginBottom: 28 }}>
            {currentStep.kind === 'welcome' ? (
              <WelcomeCard step={currentStep} />
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {currentStep.options.map(option => (
                  <OptionCard
                    key={option.value}
                    option={option}
                    selected={currentValue === option.value}
                    onClick={() => handleSelect(option.value)}
                  />
                ))}
              </div>
            )}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            {step > 0 ? (
              <Button
                type="text"
                onClick={() => setStep(s => s - 1)}
                disabled={saving}
                style={{ color: '#64748b' }}
              >
                Back
              </Button>
            ) : (
              <div />
            )}

            <Button
              type="primary"
              size="large"
              icon={!isLast ? <ArrowRightOutlined /> : undefined}
              iconPosition="end"
              disabled={!canAdvance}
              loading={saving}
              onClick={handleNext}
              style={{ minWidth: 140, height: 44, fontWeight: 600 }}
            >
              {currentStep.kind === 'welcome'
                ? 'Get started'
                : isLast
                  ? 'Launch workspace'
                  : 'Continue'}
            </Button>
          </div>
        </div>

        <Text type="secondary" style={{ display: 'block', textAlign: 'center', marginTop: 16, fontSize: 12 }}>
          You can change these settings anytime from your workspace preferences.
        </Text>
      </div>
    </div>
  )
}
