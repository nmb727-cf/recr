import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  Button,
  Card,
  Empty,
  Input,
  InputNumber,
  Modal,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from 'antd'
import {
  ArrowDown,
  ArrowLeft,
  ArrowUp,
  Bot,
  BrainCircuit,
  ClipboardList,
  Copy,
  Cpu,
  Eye,
  FileText,
  LayoutGrid,
  List,
  Mic,
  Plus,
  Settings2,
  ShieldCheck,
  Target,
  Trash2,
  Video,
  Workflow,
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import { useQueryClient } from '@tanstack/react-query'

import { interviewsApi } from '@/api/interviews'
import { useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'
import { getCategoryOptions, getInterviewTypeCategory, INTERVIEW_TYPE_CATEGORIES, type InterviewTypeCategory } from '@/utils/interviewTypeUx'

const { Text } = Typography
const { TextArea } = Input

const AI_SUPPORTED_TYPES = [
  'ai_screening',
  'ai_behavioral',
  'ai_technical',
  'async_text',
  'async_audio',
  'one_way_video',
]

const AI_TYPE_ROUTE_ALIASES: Record<string, string> = {
  ai_screening: 'ai_screening',
  ai_behavioral: 'ai_behavioral',
  ai_technical: 'ai_technical',
  async_text: 'async_text',
  async_text_interview: 'async_text',
  async_audio: 'async_audio',
  one_way_video: 'one_way_video',
  prerecorded_video: 'one_way_video',
}

const RESPONSE_OPTIONS = [
  { value: 'video', label: 'Video response' },
  { value: 'audio', label: 'Audio response' },
  { value: 'text', label: 'Text response' },
]

const CREATION_METHODS = [
  {
    value: 'manual',
    label: 'Build Manually',
    description: 'Configure the AI interview section by section.',
    icon: Settings2,
  },
  {
    value: 'ai',
    label: 'Generate with AI',
    description: 'Future mode. Collect role, skills, seniority, and JD for auto-generation.',
    icon: Bot,
  },
] as const

type CreationMethod = (typeof CREATION_METHODS)[number]['value']

type QuestionFlowItem = {
  id: string
  title: string
  question: string
  objective: string
  follow_up_shell: string
  follow_up_enabled: boolean
  follow_up_objective: string
  follow_up_trigger_note: string
  expected_answer_guidance: string
  poor_answer_guidance: string
  expected_keywords: string[]
  evaluation_dimensions: string[]
  custom_dimension: string
  skill_mapping: string[]
  knockout_intent_shell: string
  internal_note: string
  prep_guidance: string
  duration_guidance: string
  min_length_guidance: string
  max_length_guidance: string
  response_mode: 'video' | 'audio' | 'text'
}

type EvaluationDimension = {
  id: string
  key: string
  name: string
  description: string
  scorecard_attribute_name: string
  weight: number
  enabled: boolean
  scoring_owner: 'ai' | 'human' | 'blended'
  rubric: {
    excellent: string
    acceptable: string
    weak: string
    red_flags: string
    positive_signals: string
  }
}

type OutcomeRule = {
  id: string
  label: string
  min_score: number
  max_score: number
  route_action: 'move_to_next_stage' | 'manual_review_queue' | 'reject_candidate' | 'shortlist' | 'schedule_next_interview'
  next_stage_mapping: string
}

type AIInterviewDraft = {
  id: string | null
  creation_method: CreationMethod
  setup: {
    name: string
    interview_type: string
    duration_minutes: number
    response_mode: 'video' | 'audio' | 'text'
    prep_time_seconds: number
    retries: number
  }
  question_flow: {
    intro_message: string
    questions: QuestionFlowItem[]
  }
  candidate_experience: {
    instructions: string
    intro_message: string
    practice_mode: boolean
    camera_required: boolean
    mic_required: boolean
    retry_behavior: string
  }
  evaluation: {
    scoring_enabled: boolean
    manual_override: boolean
    scoring_blend_mode: 'ai_only' | 'human_only' | 'blended'
    ai_scoring_weight: number
    human_scoring_weight: number
    skill_mapping: string[]
    recommendation_logic: string
    scorecard_template_id: string
    dimensions: EvaluationDimension[]
    score_sync: {
      save_ai_score_to_scorecard: boolean
      save_dimension_scores_to_scorecard: boolean
      save_total_score_to_scorecard: boolean
      save_ai_recommendation_to_scorecard: boolean
      sync_target: 'scorecard_engine'
    }
    recommendation_thresholds: {
      strong_recommend: number
      recommend: number
      neutral: number
      concern: number
      reject: number
    }
    final_outcome_suggestion: {
      suggested_score_shell: string
      suggested_recommendation_shell: string
      suggested_next_action_shell: string
    }
  }
  outcome_routing: {
    outcomes: OutcomeRule[]
    automation: {
      auto_decision_enabled: boolean
      manual_override_allowed: boolean
      recruiter_review_required: boolean
      confidence_threshold: number
      fallback_to_manual_review: boolean
    }
    preview: {
      suggested_outcome: string
      suggested_route: string
      auto_notify_recruiter: boolean
    }
  }
  generation_brief: {
    role: string
    skills: string[]
    seniority: string
    job_description: string
  }
}

type InterviewAIEngineProps = {
  embedded?: boolean
}

const BUILDER_STEPS = [
  { key: 'setup', label: '1. Setup', icon: Settings2 },
  { key: 'question-flow', label: '2. Question Flow', icon: ClipboardList },
  { key: 'candidate-experience', label: '3. Candidate Experience', icon: Video },
  { key: 'evaluation', label: '4. Evaluation', icon: ShieldCheck },
  { key: 'outcome-routing', label: '5. Outcome / Routing', icon: Workflow },
] as const

const BUILDER_STEP_ORDER = BUILDER_STEPS.map((step) => step.key)

const EVALUATION_DIMENSION_OPTIONS = [
  'communication',
  'confidence',
  'problem_solving',
  'domain_knowledge',
  'leadership',
  'collaboration',
  'persuasion',
  'technical_depth',
  'behavioral_fit',
  'custom',
].map((value) => ({ value, label: value.replace(/_/g, ' ') }))

function getTypeSpecificGuidance(type: string) {
  if (type === 'ai_screening') {
    return {
      title: 'Screening Logic',
      description: 'Use concise qualification prompts, knockout intent, and fit or eligibility skill tags.',
    }
  }
  if (type === 'ai_behavioral') {
    return {
      title: 'Behavioral Logic',
      description: 'Emphasize competency testing, STAR-style guidance, and follow-up probing.',
    }
  }
  if (type === 'ai_technical') {
    return {
      title: 'Technical Logic',
      description: 'Focus on technical objective, concepts, skill depth, and optional architecture or coding context.',
    }
  }
  if (type === 'async_text') {
    return {
      title: 'Async Text Logic',
      description: 'Emphasize written communication quality and length guidance.',
    }
  }
  if (type === 'async_audio') {
    return {
      title: 'Async Audio Logic',
      description: 'Emphasize verbal communication quality and audio duration guidance.',
    }
  }
  return {
    title: 'One-Way Video Logic',
    description: 'Emphasize preparation, confidence, presence, and recorded video response behavior.',
  }
}

function createQuestion(overrides: Partial<QuestionFlowItem> = {}): QuestionFlowItem {
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    title: '',
    question: '',
    objective: '',
    follow_up_shell: '',
    follow_up_enabled: false,
    follow_up_objective: '',
    follow_up_trigger_note: '',
    expected_answer_guidance: '',
    poor_answer_guidance: '',
    expected_keywords: [],
    evaluation_dimensions: [],
    custom_dimension: '',
    skill_mapping: [],
    knockout_intent_shell: '',
    internal_note: '',
    prep_guidance: '',
    duration_guidance: '',
    min_length_guidance: '',
    max_length_guidance: '',
    response_mode: 'video',
    ...overrides,
  }
}

function createEvaluationDimension(key = 'communication'): EvaluationDimension {
  const label = key.replace(/_/g, ' ')
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    key,
    name: label.replace(/\b\w/g, (char) => char.toUpperCase()),
    description: '',
    scorecard_attribute_name: label.replace(/\b\w/g, (char) => char.toUpperCase()),
    weight: 20,
    enabled: true,
    scoring_owner: 'blended',
    rubric: {
      excellent: '',
      acceptable: '',
      weak: '',
      red_flags: '',
      positive_signals: '',
    },
  }
}

function createOutcomeRule(label = 'Custom Outcome', minScore = 0, maxScore = 100): OutcomeRule {
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    label,
    min_score: minScore,
    max_score: maxScore,
    route_action: 'manual_review_queue',
    next_stage_mapping: '',
  }
}

function normalizeScorecardKey(value: string) {
  return value.trim().toLowerCase().replace(/[_\s]+/g, ' ')
}

function createDraft(typeCode = 'ai_screening', method: CreationMethod = 'manual'): AIInterviewDraft {
  const responseMode: 'video' | 'audio' | 'text' =
    typeCode === 'async_audio'
      ? 'audio'
      : typeCode === 'async_text'
        ? 'text'
        : 'video'

  return {
    id: null,
    creation_method: method,
    setup: {
      name: '',
      interview_type: typeCode,
      duration_minutes: 30,
      response_mode: responseMode,
      prep_time_seconds: 60,
      retries: 1,
    },
    question_flow: {
      intro_message: '',
      questions: [createQuestion({ response_mode: responseMode })],
    },
    candidate_experience: {
      instructions: '',
      intro_message: '',
      practice_mode: true,
      camera_required: responseMode === 'video',
      mic_required: responseMode !== 'text',
      retry_behavior: 'Allow retries within configured limit',
    },
    evaluation: {
      scoring_enabled: true,
      manual_override: true,
      scoring_blend_mode: 'blended',
      ai_scoring_weight: 70,
      human_scoring_weight: 30,
      skill_mapping: [],
      recommendation_logic: 'manual_review',
      scorecard_template_id: '',
      dimensions: [
        createEvaluationDimension(typeCode === 'ai_technical' ? 'technical_depth' : typeCode === 'ai_behavioral' ? 'behavioral_fit' : 'communication'),
        createEvaluationDimension(typeCode === 'ai_technical' ? 'problem_solving' : 'confidence'),
      ],
      score_sync: {
        save_ai_score_to_scorecard: true,
        save_dimension_scores_to_scorecard: true,
        save_total_score_to_scorecard: true,
        save_ai_recommendation_to_scorecard: true,
        sync_target: 'scorecard_engine',
      },
      recommendation_thresholds: {
        strong_recommend: 90,
        recommend: 75,
        neutral: 60,
        concern: 45,
        reject: 0,
      },
      final_outcome_suggestion: {
        suggested_score_shell: '',
        suggested_recommendation_shell: '',
        suggested_next_action_shell: '',
      },
    },
    outcome_routing: {
      outcomes: [
        createOutcomeRule('Strong Recommend', 90, 100),
        createOutcomeRule('Recommend', 75, 89),
        createOutcomeRule('Neutral', 50, 74),
        createOutcomeRule('Concern', 30, 49),
        createOutcomeRule('Reject', 0, 29),
      ],
      automation: {
        auto_decision_enabled: true,
        manual_override_allowed: true,
        recruiter_review_required: true,
        confidence_threshold: 60,
        fallback_to_manual_review: true,
      },
      preview: {
        suggested_outcome: 'Strong Recommend',
        suggested_route: 'Move to next stage',
        auto_notify_recruiter: true,
      },
    },
    generation_brief: {
      role: '',
      skills: [],
      seniority: '',
      job_description: '',
    },
  }
}

function parseTemplate(template: any): AIInterviewDraft {
  const meta = template?.metadata?.ai_interview || {}
  const setup = meta.setup || {}
  const flow = meta.question_flow || {}
  const candidate = meta.candidate_experience || {}
  const evaluation = meta.evaluation || {}
  const outcome = meta.outcome_routing || {}
  const generationBrief = meta.generation_brief || {}
  const compatQuestions = Array.isArray(template?.questions) ? template.questions : []
  const responseMode = (setup.response_mode || template?.questions?.[0]?.type || 'video') as 'video' | 'audio' | 'text'
  const questions = Array.isArray(flow.questions) && flow.questions.length
    ? flow.questions
    : compatQuestions.map((question: any) =>
        createQuestion({
          id: question.id,
          title: question.title || '',
          question: question.text || '',
          objective: question.objective || '',
          follow_up_shell: question.follow_up_shell || '',
          follow_up_enabled: Boolean(question.follow_up_enabled || question.follow_up_shell),
          follow_up_objective: question.follow_up_objective || '',
          follow_up_trigger_note: question.follow_up_trigger_note || '',
          expected_answer_guidance: question.expected_answer || '',
          poor_answer_guidance: question.poor_answer_guidance || '',
          expected_keywords: Array.isArray(question.expected_keywords) ? question.expected_keywords : [],
          evaluation_dimensions: Array.isArray(question.evaluation_dimensions) ? question.evaluation_dimensions : [],
          custom_dimension: question.custom_dimension || '',
          skill_mapping: Array.isArray(question.skills) ? question.skills : [],
          knockout_intent_shell: question.knockout_intent_shell || '',
          internal_note: question.internal_note || '',
          prep_guidance: question.prep_guidance || '',
          duration_guidance: question.duration_guidance || '',
          min_length_guidance: question.min_length_guidance || '',
          max_length_guidance: question.max_length_guidance || '',
          response_mode: (question.type || responseMode) as 'video' | 'audio' | 'text',
        }),
      )

  return {
    id: template?.id || null,
    creation_method: meta.creation_method || 'manual',
    setup: {
      name: template?.name || '',
      interview_type: template?.interview_type || 'ai_screening',
      duration_minutes: template?.duration_minutes ?? setup.duration_minutes ?? 30,
      response_mode: responseMode,
      prep_time_seconds: setup.prep_time_seconds ?? 60,
      retries: setup.retries ?? 1,
    },
    question_flow: {
      intro_message: flow.intro_message || '',
      questions: questions.length ? questions : [createQuestion({ response_mode: responseMode })],
    },
    candidate_experience: {
      instructions: template?.instructions || candidate.instructions || '',
      intro_message: candidate.intro_message || '',
      practice_mode: candidate.practice_mode ?? true,
      camera_required: candidate.camera_required ?? (responseMode === 'video'),
      mic_required: candidate.mic_required ?? (responseMode !== 'text'),
      retry_behavior: candidate.retry_behavior || 'Allow retries within configured limit',
    },
    evaluation: {
      scoring_enabled: evaluation.scoring_enabled ?? true,
      manual_override: evaluation.manual_override ?? true,
      scoring_blend_mode: evaluation.scoring_blend_mode ?? 'blended',
      ai_scoring_weight: evaluation.ai_scoring_weight ?? 70,
      human_scoring_weight: evaluation.human_scoring_weight ?? 30,
      skill_mapping: Array.isArray(evaluation.skill_mapping) ? evaluation.skill_mapping : [],
      recommendation_logic: evaluation.recommendation_logic || 'manual_review',
      scorecard_template_id: evaluation.scorecard_template_id || '',
      dimensions: Array.isArray(evaluation.dimensions) && evaluation.dimensions.length
        ? evaluation.dimensions.map((dimension: any) => ({
            id: dimension.id || `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
            key: dimension.key || 'custom',
            name: dimension.name || 'Custom Dimension',
            description: dimension.description || '',
            scorecard_attribute_name: dimension.scorecard_attribute_name || dimension.name || 'Custom Dimension',
            weight: Number(dimension.weight ?? 0),
            enabled: dimension.enabled ?? true,
            scoring_owner: dimension.scoring_owner || 'blended',
            rubric: {
              excellent: dimension.rubric?.excellent || '',
              acceptable: dimension.rubric?.acceptable || '',
              weak: dimension.rubric?.weak || '',
              red_flags: dimension.rubric?.red_flags || '',
              positive_signals: dimension.rubric?.positive_signals || '',
            },
          }))
        : [createEvaluationDimension()],
      score_sync: {
        save_ai_score_to_scorecard: evaluation.score_sync?.save_ai_score_to_scorecard ?? true,
        save_dimension_scores_to_scorecard: evaluation.score_sync?.save_dimension_scores_to_scorecard ?? true,
        save_total_score_to_scorecard: evaluation.score_sync?.save_total_score_to_scorecard ?? true,
        save_ai_recommendation_to_scorecard: evaluation.score_sync?.save_ai_recommendation_to_scorecard ?? true,
        sync_target: 'scorecard_engine',
      },
      recommendation_thresholds: {
        strong_recommend: evaluation.recommendation_thresholds?.strong_recommend ?? 90,
        recommend: evaluation.recommendation_thresholds?.recommend ?? 75,
        neutral: evaluation.recommendation_thresholds?.neutral ?? 60,
        concern: evaluation.recommendation_thresholds?.concern ?? 45,
        reject: evaluation.recommendation_thresholds?.reject ?? 0,
      },
      final_outcome_suggestion: {
        suggested_score_shell: evaluation.final_outcome_suggestion?.suggested_score_shell || '',
        suggested_recommendation_shell: evaluation.final_outcome_suggestion?.suggested_recommendation_shell || '',
        suggested_next_action_shell: evaluation.final_outcome_suggestion?.suggested_next_action_shell || '',
      },
    },
    outcome_routing: {
      outcomes: Array.isArray(outcome.outcomes) && outcome.outcomes.length
        ? outcome.outcomes.map((rule: any) => ({
            id: rule.id || `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
            label: rule.label || 'Custom Outcome',
            min_score: Number(rule.min_score ?? 0),
            max_score: Number(rule.max_score ?? 100),
            route_action: rule.route_action || 'manual_review_queue',
            next_stage_mapping: rule.next_stage_mapping || '',
          }))
        : [
            createOutcomeRule('Strong Recommend', 90, 100),
            createOutcomeRule('Recommend', 75, 89),
            createOutcomeRule('Neutral', 50, 74),
            createOutcomeRule('Concern', 30, 49),
            createOutcomeRule('Reject', 0, 29),
          ],
      automation: {
        auto_decision_enabled: outcome.automation?.auto_decision_enabled ?? true,
        manual_override_allowed: outcome.automation?.manual_override_allowed ?? true,
        recruiter_review_required: outcome.automation?.recruiter_review_required ?? true,
        confidence_threshold: outcome.automation?.confidence_threshold ?? 60,
        fallback_to_manual_review: outcome.automation?.fallback_to_manual_review ?? true,
      },
      preview: {
        suggested_outcome: outcome.preview?.suggested_outcome || 'Strong Recommend',
        suggested_route: outcome.preview?.suggested_route || 'Move to next stage',
        auto_notify_recruiter: outcome.preview?.auto_notify_recruiter ?? true,
      },
    },
    generation_brief: {
      role: generationBrief.role || '',
      skills: Array.isArray(generationBrief.skills) ? generationBrief.skills : [],
      seniority: generationBrief.seniority || '',
      job_description: generationBrief.job_description || '',
    },
  }
}

function serializeDraft(draft: AIInterviewDraft, selectedTemplate: any) {
  const promptQuestions = draft.question_flow.questions
    .filter((question) => question.question.trim())
    .map((question, index) => ({
      id: question.id,
      title: question.title,
      text: question.question,
      objective: question.objective,
      type: question.response_mode,
      follow_up_shell: question.follow_up_shell,
      follow_up_enabled: question.follow_up_enabled,
      follow_up_objective: question.follow_up_objective,
      follow_up_trigger_note: question.follow_up_trigger_note,
      expected_answer: question.expected_answer_guidance,
      poor_answer_guidance: question.poor_answer_guidance,
      expected_keywords: question.expected_keywords,
      evaluation_dimensions: question.evaluation_dimensions,
      custom_dimension: question.custom_dimension,
      skills: question.skill_mapping,
      knockout_intent_shell: question.knockout_intent_shell,
      internal_note: question.internal_note,
      prep_guidance: question.prep_guidance,
      duration_guidance: question.duration_guidance,
      min_length_guidance: question.min_length_guidance,
      max_length_guidance: question.max_length_guidance,
      order_index: index,
      duration: Math.ceil((draft.setup.duration_minutes * 60) / Math.max(draft.question_flow.questions.length, 1)),
      options: [],
    }))

  return {
    name: draft.setup.name,
    description: `${draft.setup.interview_type.replace(/_/g, ' ')} reusable AI interview`,
    interview_type: draft.setup.interview_type,
    duration_minutes: draft.setup.duration_minutes,
    instructions: draft.candidate_experience.instructions,
    scoring_type: draft.evaluation.scoring_enabled ? 'criteria' : 'numeric',
    questions: promptQuestions,
    metadata: {
      ...(selectedTemplate?.metadata || {}),
      ai_interview: {
        entity_type: 'reusable_ai_interview_template',
        creation_method: draft.creation_method,
        setup: draft.setup,
        question_flow: draft.question_flow,
        candidate_experience: draft.candidate_experience,
        evaluation: draft.evaluation,
        outcome_routing: draft.outcome_routing,
        generation_brief: draft.generation_brief,
        integrations: {
          question_engine: true,
          scorecard_engine: true,
          flow_engine: true,
          decision_engine: true,
        },
      },
    },
  }
}

function responseTag(mode: string) {
  if (mode === 'audio') return <Tag color="gold">Audio</Tag>
  if (mode === 'text') return <Tag color="green">Text</Tag>
  return <Tag color="blue">Video</Tag>
}

function PreviewModal({
  open,
  draft,
  onClose,
}: {
  open: boolean
  draft: AIInterviewDraft | null
  onClose: () => void
}) {
  return (
    <Modal open={open} onCancel={onClose} footer={null} width={900} destroyOnClose title="AI Interview Preview">
      {!draft ? null : (
        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-200 bg-slate-950 p-6 text-white">
            <p className="text-[10px] font-black uppercase tracking-[0.25em] text-slate-400">Candidate View</p>
            <h2 className="mt-3 text-2xl font-black">{draft.setup.name || 'Untitled AI Interview'}</h2>
            <p className="mt-3 text-sm text-slate-300">{draft.question_flow.intro_message || draft.candidate_experience.intro_message || 'Candidate intro message appears here.'}</p>
            <div className="mt-5 grid grid-cols-4 gap-3">
              <div className="rounded-xl bg-white/5 p-3">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Mode</p>
                <p className="mt-2 text-sm font-bold">{draft.setup.response_mode}</p>
              </div>
              <div className="rounded-xl bg-white/5 p-3">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Duration</p>
                <p className="mt-2 text-sm font-bold">{draft.setup.duration_minutes}m</p>
              </div>
              <div className="rounded-xl bg-white/5 p-3">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Prep</p>
                <p className="mt-2 text-sm font-bold">{draft.setup.prep_time_seconds}s</p>
              </div>
              <div className="rounded-xl bg-white/5 p-3">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Retries</p>
                <p className="mt-2 text-sm font-bold">{draft.setup.retries}</p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-12 gap-6">
            <Card className="col-span-12 lg:col-span-7">
              <h3 className="text-sm font-black uppercase tracking-widest text-slate-900">Question Sequence</h3>
              <div className="mt-4 space-y-3">
                {draft.question_flow.questions.map((question, index) => (
                  <div key={question.id} className="rounded-2xl border border-slate-200 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Question {index + 1}</p>
                        <p className="mt-2 text-sm font-bold text-slate-900">{question.question || 'Question not authored yet'}</p>
                      </div>
                      {responseTag(question.response_mode)}
                    </div>
                    <p className="mt-3 text-xs text-slate-500">{question.expected_answer_guidance || 'Expected answer guidance not defined yet.'}</p>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="col-span-12 lg:col-span-5">
              <h3 className="text-sm font-black uppercase tracking-widest text-slate-900">Runtime Experience</h3>
              <div className="mt-4 space-y-3">
                <div className="rounded-2xl border border-slate-200 p-4">
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Instructions</p>
                  <p className="mt-2 text-sm font-bold text-slate-900">{draft.candidate_experience.instructions || 'No candidate instructions yet'}</p>
                </div>
                <div className="rounded-2xl border border-slate-200 p-4">
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Practice Mode</p>
                  <p className="mt-2 text-sm font-bold text-slate-900">{draft.candidate_experience.practice_mode ? 'Enabled' : 'Disabled'}</p>
                </div>
                <div className="rounded-2xl border border-slate-200 p-4">
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Evaluation</p>
                  <p className="mt-2 text-sm font-bold text-slate-900">{draft.evaluation.ai_scoring_weight}% AI weight · {draft.evaluation.recommendation_logic}</p>
                  <p className="mt-1 text-xs text-slate-500">{draft.evaluation.scorecard_template_id ? 'Linked to Scorecard Engine' : 'No scorecard linked yet'}</p>
                </div>
              </div>
            </Card>
          </div>
        </div>
      )}
    </Modal>
  )
}

export default function InterviewAIEngine({ embedded = false }: InterviewAIEngineProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const queryClient = useQueryClient()
  const requestedType = new URLSearchParams(location.search).get('type')
  const initialType = useMemo(() => {
    const normalized = AI_TYPE_ROUTE_ALIASES[requestedType || '']
    return normalized && AI_SUPPORTED_TYPES.includes(normalized) ? normalized : 'ai_screening'
  }, [requestedType])
  const [isBuilderOpen, setIsBuilderOpen] = useState(false)
  const [createMethodOpen, setCreateMethodOpen] = useState(false)
  const [previewOpen, setPreviewOpen] = useState(false)
  const [activeStep, setActiveStep] = useState<(typeof BUILDER_STEPS)[number]['key']>('setup')
  const [creationMethod, setCreationMethod] = useState<CreationMethod>('manual')
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null)
  const [selectedTypeCategory, setSelectedTypeCategory] = useState<InterviewTypeCategory>('AI')
  const [draft, setDraft] = useState<AIInterviewDraft>(createDraft(initialType))
  const [saving, setSaving] = useState(false)

  const { data: templatesData, isLoading } = useApiQuery(['interview-templates-list'], () => interviewsApi.listTemplates())
  const { data: flowsData } = useApiQuery(['interview-flows'], () => interviewsApi.listFlows())
  const { data: scorecardsData } = useApiQuery(['interview-scorecards'], () => interviewsApi.listScorecards())

  const templates = ((templatesData as any)?.templates ?? []).filter((template: any) => AI_SUPPORTED_TYPES.includes(template.interview_type))
  const flows = (flowsData as any)?.flows ?? []
  const scorecards = (scorecardsData as any)?.scorecards ?? []

  const selectedTemplate = useMemo(
    () => templates.find((template: any) => template.id === selectedTemplateId) ?? null,
    [selectedTemplateId, templates],
  )

  useEffect(() => {
    if (!selectedTemplate) return
    setDraft(parseTemplate(selectedTemplate))
  }, [selectedTemplate])

  useEffect(() => {
    if (!requestedType || isBuilderOpen) return
    const nextType = AI_TYPE_ROUTE_ALIASES[requestedType]
    if (!nextType || !AI_SUPPORTED_TYPES.includes(nextType)) return
    setDraft(createDraft(nextType, creationMethod))
    setSelectedTemplateId(null)
    setActiveStep('setup')
    setIsBuilderOpen(true)
  }, [requestedType, isBuilderOpen, creationMethod])

  useEffect(() => {
    setSelectedTypeCategory(getInterviewTypeCategory(draft.setup.interview_type))
  }, [draft.setup.interview_type])

  const usageStats = useMemo(() => {
    return new Map(
      templates.map((template: any) => {
        const meta = template?.metadata?.ai_interview || {}
        const usage = meta.usage || {}
        const count =
          (Array.isArray(usage.linked_jobs) ? usage.linked_jobs.length : 0) +
          (Array.isArray(usage.linked_flows) ? usage.linked_flows.length : 0) +
          (Array.isArray(usage.linked_stages) ? usage.linked_stages.length : 0)
        return [template.id, count]
      }),
    )
  }, [templates])
  const filteredAiTypeOptions = getCategoryOptions(selectedTypeCategory).filter((item) => AI_SUPPORTED_TYPES.includes(item.value))

  const stepCompletion = useMemo(() => {
    return {
      setup: Boolean(draft.setup.name.trim() && draft.setup.interview_type && draft.setup.duration_minutes > 0),
      'question-flow': Boolean(draft.question_flow.questions.some((question) => question.question.trim())),
      'candidate-experience': Boolean(
        draft.candidate_experience.instructions.trim() &&
        draft.candidate_experience.intro_message.trim() &&
        draft.candidate_experience.retry_behavior.trim(),
      ),
      evaluation: Boolean(draft.evaluation.ai_scoring_weight >= 0),
      'outcome-routing': Boolean(draft.outcome_routing.outcomes.length > 0),
    }
  }, [draft])

  const jumpToStep = (step: (typeof BUILDER_STEPS)[number]['key']) => {
    setActiveStep(step)
  }
  const activeStepIndex = BUILDER_STEP_ORDER.indexOf(activeStep)
  const goToPrevStep = () => {
    if (activeStepIndex > 0) setActiveStep(BUILDER_STEP_ORDER[activeStepIndex - 1])
  }
  const goToNextStep = () => {
    if (activeStepIndex < BUILDER_STEP_ORDER.length - 1) setActiveStep(BUILDER_STEP_ORDER[activeStepIndex + 1])
  }

  const openCreate = () => {
    setCreationMethod('manual')
    setCreateMethodOpen(true)
  }

  const startBuilder = () => {
    setCreateMethodOpen(false)
    setSelectedTemplateId(null)
    setDraft(createDraft('ai_screening', creationMethod))
    setActiveStep('setup')
    setIsBuilderOpen(true)
  }

  const editTemplate = (template: any) => {
    setSelectedTemplateId(template.id)
    setDraft(parseTemplate(template))
    setCreationMethod((template?.metadata?.ai_interview?.creation_method || 'manual') as CreationMethod)
    setActiveStep('setup')
    setIsBuilderOpen(true)
  }

  const duplicateTemplate = async (template: any) => {
    try {
      const sourceDraft = parseTemplate(template)
      const payload = serializeDraft({
        ...sourceDraft,
        id: null,
        setup: { ...sourceDraft.setup, name: `${sourceDraft.setup.name || template.name} Copy` },
      }, null)
      await interviewsApi.createTemplate(payload)
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      message.success('AI interview duplicated')
    } catch {
      message.error('Failed to duplicate AI interview')
    }
  }

  const archiveTemplate = async (template: any) => {
    try {
      await interviewsApi.updateTemplate(template.id, { ...template, is_active: false })
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      message.success('AI interview archived')
    } catch {
      message.error('Failed to archive AI interview')
    }
  }

  const saveDraft = async () => {
    if (!draft.setup.name.trim()) {
      message.error('Interview name is required')
      return
    }
    if (!draft.question_flow.questions.some((question) => question.question.trim())) {
      message.error('Add at least one question to the prompt flow')
      return
    }

    setSaving(true)
    try {
      const payload = serializeDraft(draft, selectedTemplate)
      let savedId = selectedTemplateId
      if (selectedTemplateId) {
        await interviewsApi.updateTemplate(selectedTemplateId, payload)
      } else {
        const response = await interviewsApi.createTemplate(payload)
        savedId = response.data?.data?.template?.id || null
      }
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      setSelectedTemplateId(savedId)
      setIsBuilderOpen(false)
      message.success(selectedTemplateId ? 'AI interview updated' : 'AI interview created')
    } catch {
      message.error('Failed to save AI interview')
    } finally {
      setSaving(false)
    }
  }

  const updateDraft = (updater: (current: AIInterviewDraft) => AIInterviewDraft) => {
    setDraft((current) => updater(current))
  }

  const applyScorecardTemplate = (scorecardId: string) => {
    const nextScorecard = scorecards.find((scorecard: any) => scorecard.id === scorecardId)
    const nextAttributes = nextScorecard?.attributes ?? []

    updateDraft((current) => ({
      ...current,
      evaluation: {
        ...current.evaluation,
        scorecard_template_id: scorecardId,
        dimensions: current.evaluation.dimensions.map((dimension) => {
          const matchedAttribute = nextAttributes.find((attribute: any) =>
            normalizeScorecardKey(attribute.attribute_name) === normalizeScorecardKey(dimension.name)
            || normalizeScorecardKey(attribute.attribute_name) === normalizeScorecardKey(dimension.key.replace(/_/g, ' '))
          )

          return {
            ...dimension,
            scorecard_attribute_name: matchedAttribute?.attribute_name || dimension.scorecard_attribute_name || dimension.name,
          }
        }),
      },
    }))
  }

  const updateQuestion = (questionId: string, updates: Partial<QuestionFlowItem>) => {
    updateDraft((current) => ({
      ...current,
      question_flow: {
        ...current.question_flow,
        questions: current.question_flow.questions.map((question) =>
          question.id === questionId ? { ...question, ...updates } : question,
        ),
      },
    }))
  }

  const addQuestion = () => {
    updateDraft((current) => ({
      ...current,
      question_flow: {
        ...current.question_flow,
        questions: [...current.question_flow.questions, createQuestion({ response_mode: current.setup.response_mode })],
      },
    }))
  }

  const removeQuestion = (questionId: string) => {
    updateDraft((current) => {
      const nextQuestions = current.question_flow.questions.filter((question) => question.id !== questionId)
      return {
        ...current,
        question_flow: {
          ...current.question_flow,
          questions: nextQuestions.length ? nextQuestions : [createQuestion({ response_mode: current.setup.response_mode })],
        },
      }
    })
  }

  const duplicateQuestion = (questionId: string) => {
    updateDraft((current) => {
      const index = current.question_flow.questions.findIndex((question) => question.id === questionId)
      if (index === -1) return current
      const source = current.question_flow.questions[index]
      const clone = createQuestion({
        ...source,
        title: source.title ? `${source.title} Copy` : '',
      })
      const nextQuestions = [...current.question_flow.questions]
      nextQuestions.splice(index + 1, 0, clone)
      return {
        ...current,
        question_flow: {
          ...current.question_flow,
          questions: nextQuestions,
        },
      }
    })
  }

  const moveQuestion = (questionId: string, direction: -1 | 1) => {
    updateDraft((current) => {
      const index = current.question_flow.questions.findIndex((question) => question.id === questionId)
      const target = index + direction
      if (index === -1 || target < 0 || target >= current.question_flow.questions.length) return current
      const nextQuestions = [...current.question_flow.questions]
      const [item] = nextQuestions.splice(index, 1)
      nextQuestions.splice(target, 0, item)
      return {
        ...current,
        question_flow: {
          ...current.question_flow,
          questions: nextQuestions,
        },
      }
    })
  }

  const columns: ColumnsType<any> = [
    {
      title: 'Template Name',
      dataIndex: 'name',
      key: 'name',
      render: (name, record) => (
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-slate-900 text-white">
            <Cpu size={16} />
          </div>
          <div>
            <Text className="block font-bold text-slate-900">{name}</Text>
            <Text className="block text-xs text-slate-400">{record.description || 'Reusable AI interview template'}</Text>
          </div>
        </div>
      ),
    },
    {
      title: 'Interview Type',
      dataIndex: 'interview_type',
      key: 'interview_type',
      render: (value) => <Tag className="uppercase">{String(value).replace(/_/g, ' ')}</Tag>,
    },
    {
      title: 'Response Mode',
      key: 'response_mode',
      render: (_, record) => responseTag(record.metadata?.ai_interview?.setup?.response_mode || record.questions?.[0]?.type || 'video'),
    },
    {
      title: 'Duration',
      dataIndex: 'duration_minutes',
      key: 'duration_minutes',
      render: (value) => `${value || 0} min`,
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (value) => (
        <Tag color={value ? 'success' : 'default'}>{value ? 'Active' : 'Archived'}</Tag>
      ),
    },
    {
      title: 'Usage Count',
      key: 'usage_count',
      render: (_, record) => usageStats.get(record.id) || 0,
    },
    {
      title: 'Last Updated',
      dataIndex: 'updated_at',
      key: 'updated_at',
      render: (value) => new Date(value).toLocaleDateString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space wrap>
          <Button size="small" onClick={() => editTemplate(record)}>Edit</Button>
          <Button size="small" onClick={() => duplicateTemplate(record)}>Duplicate</Button>
          <Button size="small" onClick={() => { setDraft(parseTemplate(record)); setPreviewOpen(true) }}>Preview</Button>
          <Button size="small" danger onClick={() => archiveTemplate(record)}>Archive</Button>
        </Space>
      ),
    },
  ]

  const typeSpecificGuidance = getTypeSpecificGuidance(draft.setup.interview_type)
  const totalEnabledDimensionWeight = draft.evaluation.dimensions
    .filter((dimension) => dimension.enabled)
    .reduce((sum, dimension) => sum + Number(dimension.weight || 0), 0)
  const questionDimensionMap = draft.question_flow.questions.map((question, index) => ({
    id: question.id,
    label: question.title || `Question ${index + 1}`,
    dimensions: question.evaluation_dimensions.includes('custom') && question.custom_dimension
      ? [...question.evaluation_dimensions.filter((dimension) => dimension !== 'custom'), question.custom_dimension]
      : question.evaluation_dimensions,
    skills: question.skill_mapping,
  }))
  const predictedOutcome = draft.outcome_routing.outcomes
    .slice()
    .sort((a, b) => b.max_score - a.max_score)[0] || null
  const selectedScorecard = scorecards.find((scorecard: any) => scorecard.id === draft.evaluation.scorecard_template_id) ?? null
  const scorecardAttributes = selectedScorecard?.attributes ?? []
  const mappedScorecardDimensions = draft.evaluation.dimensions.map((dimension, index) => {
    const explicit = scorecardAttributes.find((attribute: any) => attribute.attribute_name === dimension.scorecard_attribute_name)
    const inferred = scorecardAttributes.find((attribute: any) =>
      normalizeScorecardKey(attribute.attribute_name) === normalizeScorecardKey(dimension.name)
      || normalizeScorecardKey(attribute.attribute_name) === normalizeScorecardKey(dimension.key.replace(/_/g, ' '))
    )
    const linkedAttribute = explicit || inferred || null
    const sampleScore = Math.max(55, 88 - (index * 6))

    return {
      id: dimension.id,
      dimension,
      linkedAttribute,
      sampleScore,
    }
  })
  const enabledMappedDimensions = mappedScorecardDimensions.filter((item) => item.dimension.enabled)
  const previewAIScore = enabledMappedDimensions.length
    ? Math.round(enabledMappedDimensions.reduce((sum, item) => sum + item.sampleScore, 0) / enabledMappedDimensions.length)
    : 0
  const previewHumanScore = draft.evaluation.scoring_blend_mode === 'ai_only'
    ? 0
    : draft.evaluation.scoring_blend_mode === 'human_only'
      ? previewAIScore
      : Math.max(0, Math.min(100, previewAIScore - 6))
  const previewFinalScore = draft.evaluation.scoring_blend_mode === 'ai_only'
    ? previewAIScore
    : draft.evaluation.scoring_blend_mode === 'human_only'
      ? previewHumanScore
      : Math.round(((previewAIScore * draft.evaluation.ai_scoring_weight) + (previewHumanScore * draft.evaluation.human_scoring_weight)) / Math.max(draft.evaluation.ai_scoring_weight + draft.evaluation.human_scoring_weight, 1))
  const previewRecommendation =
    previewFinalScore >= draft.evaluation.recommendation_thresholds.strong_recommend ? 'strong_recommend'
      : previewFinalScore >= draft.evaluation.recommendation_thresholds.recommend ? 'recommend'
        : previewFinalScore >= draft.evaluation.recommendation_thresholds.neutral ? 'neutral'
          : previewFinalScore >= draft.evaluation.recommendation_thresholds.concern ? 'concern'
            : 'reject'

  const BuilderField = ({
    label,
    helper,
    children,
  }: {
    label: string
    helper?: string
    children: ReactNode
  }) => (
    <div className="space-y-2">
      <div>
        <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">{label}</p>
        {helper ? <p className="mt-1 text-xs text-slate-500">{helper}</p> : null}
      </div>
      {children}
    </div>
  )

  const updateEvaluationDimension = (dimensionId: string, updates: Partial<EvaluationDimension>) => {
    updateDraft((current) => ({
      ...current,
      evaluation: {
        ...current.evaluation,
        dimensions: current.evaluation.dimensions.map((dimension) =>
          dimension.id === dimensionId ? { ...dimension, ...updates } : dimension,
        ),
      },
    }))
  }

  const updateEvaluationRubric = (dimensionId: string, key: keyof EvaluationDimension['rubric'], value: string) => {
    updateDraft((current) => ({
      ...current,
      evaluation: {
        ...current.evaluation,
        dimensions: current.evaluation.dimensions.map((dimension) =>
          dimension.id === dimensionId
            ? { ...dimension, rubric: { ...dimension.rubric, [key]: value } }
            : dimension,
        ),
      },
    }))
  }

  const addEvaluationDimension = () => {
    updateDraft((current) => ({
      ...current,
      evaluation: {
        ...current.evaluation,
        dimensions: [...current.evaluation.dimensions, createEvaluationDimension()],
      },
    }))
  }

  const removeEvaluationDimension = (dimensionId: string) => {
    updateDraft((current) => ({
      ...current,
      evaluation: {
        ...current.evaluation,
        dimensions: current.evaluation.dimensions.length > 1
          ? current.evaluation.dimensions.filter((dimension) => dimension.id !== dimensionId)
          : current.evaluation.dimensions,
      },
    }))
  }

  const addOutcomeRule = (label = 'Custom Outcome') => {
    updateDraft((current) => ({
      ...current,
      outcome_routing: {
        ...current.outcome_routing,
        outcomes: [...current.outcome_routing.outcomes, createOutcomeRule(label, 0, 100)],
      },
    }))
  }

  const updateOutcomeRule = (ruleId: string, updates: Partial<OutcomeRule>) => {
    updateDraft((current) => ({
      ...current,
      outcome_routing: {
        ...current.outcome_routing,
        outcomes: current.outcome_routing.outcomes.map((rule) =>
          rule.id === ruleId ? { ...rule, ...updates } : rule,
        ),
      },
    }))
  }

  const removeOutcomeRule = (ruleId: string) => {
    updateDraft((current) => ({
      ...current,
      outcome_routing: {
        ...current.outcome_routing,
        outcomes: current.outcome_routing.outcomes.length > 1
          ? current.outcome_routing.outcomes.filter((rule) => rule.id !== ruleId)
          : current.outcome_routing.outcomes,
      },
    }))
  }

  const builder = (
    <div className="grid grid-cols-12 gap-6">
      <div className="col-span-12 lg:col-span-3">
        <div className="sticky top-6 space-y-4">
          <Card>
            <h3 className="text-sm font-black uppercase tracking-widest text-slate-900">Builder Steps</h3>
            <div className="mt-4 space-y-2">
              {BUILDER_STEPS.map((step) => {
                const Icon = step.icon
                const done = stepCompletion[step.key]
                return (
                  <button
                    key={step.key}
                    type="button"
                    onClick={() => jumpToStep(step.key)}
                    className={cn(
                      'flex w-full items-center justify-between rounded-2xl border px-4 py-3 text-left transition',
                      activeStep === step.key
                        ? 'border-indigo-300 bg-indigo-50'
                        : 'border-slate-200 bg-white hover:border-slate-300',
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <div className={cn(
                        'flex h-8 w-8 items-center justify-center rounded-xl',
                        done ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500',
                      )}>
                        <Icon size={14} />
                      </div>
                      <div>
                        <p className="text-xs font-black uppercase tracking-widest text-slate-900">{step.label}</p>
                        <p className="text-[11px] text-slate-500">{done ? 'Complete' : 'Needs input'}</p>
                      </div>
                    </div>
                    <Tag color={done ? 'success' : 'default'}>{done ? 'Done' : 'Open'}</Tag>
                  </button>
                )
              })}
            </div>
          </Card>

          <Card>
            <h3 className="text-sm font-black uppercase tracking-widest text-slate-900">Template Status</h3>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <div className="rounded-2xl border border-slate-200 p-4">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">State</p>
                <p className="mt-2 text-sm font-bold text-slate-900">{selectedTemplateId ? 'Editing' : 'Draft'}</p>
              </div>
              <div className="rounded-2xl border border-slate-200 p-4">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Completed</p>
                <p className="mt-2 text-sm font-bold text-slate-900">{Object.values(stepCompletion).filter(Boolean).length}/5</p>
              </div>
            </div>
          </Card>
        </div>
      </div>

      <div className="col-span-12 lg:col-span-6 space-y-6">
        <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3">
          <div>
            <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Current Step</p>
            <p className="mt-1 text-sm font-bold text-slate-900">{BUILDER_STEPS[activeStepIndex]?.label}</p>
          </div>
          <div className="flex items-center gap-2">
            <Button onClick={goToPrevStep} disabled={activeStepIndex === 0}>Back</Button>
            <Button onClick={goToNextStep} disabled={activeStepIndex === BUILDER_STEP_ORDER.length - 1}>Next</Button>
          </div>
        </div>
        <Card id="ai-builder-setup" className={cn(activeStep === 'setup' ? 'block' : 'hidden')}>
          <div className="mb-4 flex items-center gap-2">
            <Settings2 size={16} className="text-indigo-600" />
            <h2 className="text-sm font-black uppercase tracking-widest text-slate-900">1. Setup</h2>
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <BuilderField label="Interview Name">
              <Input
                value={draft.setup.name}
                placeholder="Interview name"
                onChange={(event) => updateDraft((current) => ({ ...current, setup: { ...current.setup, name: event.target.value } }))}
              />
            </BuilderField>
            <BuilderField label="AI Interview Type">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <Select
                  value={selectedTypeCategory}
                  options={INTERVIEW_TYPE_CATEGORIES
                    .filter((category) => getCategoryOptions(category).some((item) => AI_SUPPORTED_TYPES.includes(item.value)))
                    .map((category) => ({ value: category, label: category }))}
                  onChange={(value) => setSelectedTypeCategory(value)}
                />
                <Select
                  value={draft.setup.interview_type}
                  options={filteredAiTypeOptions.map((option) => ({ value: option.value, label: option.label }))}
                  onChange={(value) => updateDraft((current) => ({ ...current, setup: { ...current.setup, interview_type: value } }))}
                />
              </div>
            </BuilderField>
            <BuilderField label="Duration">
              <InputNumber
                min={5}
                max={180}
                className="w-full"
                addonAfter="min"
                value={draft.setup.duration_minutes}
                onChange={(value) => updateDraft((current) => ({ ...current, setup: { ...current.setup, duration_minutes: Number(value || 30) } }))}
              />
            </BuilderField>
            <BuilderField label="Response Mode">
              <Select
                value={draft.setup.response_mode}
                options={RESPONSE_OPTIONS}
                onChange={(value) => updateDraft((current) => ({ ...current, setup: { ...current.setup, response_mode: value } }))}
              />
            </BuilderField>
            <BuilderField label="Preparation Time">
              <InputNumber
                min={0}
                max={300}
                className="w-full"
                addonAfter="sec"
                value={draft.setup.prep_time_seconds}
                onChange={(value) => updateDraft((current) => ({ ...current, setup: { ...current.setup, prep_time_seconds: Number(value || 0) } }))}
              />
            </BuilderField>
            <BuilderField label="Retries">
              <InputNumber
                min={0}
                max={5}
                className="w-full"
                value={draft.setup.retries}
                onChange={(value) => updateDraft((current) => ({ ...current, setup: { ...current.setup, retries: Number(value || 0) } }))}
              />
            </BuilderField>
          </div>

          {draft.creation_method === 'ai' && (
            <div className="mt-6 rounded-2xl border border-dashed border-amber-300 bg-amber-50 p-4">
              <div className="flex items-center gap-2">
                <BrainCircuit size={16} className="text-amber-700" />
                <p className="text-sm font-black text-amber-900">Generate with AI (Future)</p>
              </div>
              <p className="mt-2 text-xs text-amber-800">Architecture support only. This will later generate setup, question flow, evaluation, and routing from job context.</p>
              <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                <Input
                  value={draft.generation_brief.role}
                  placeholder="Role"
                  onChange={(event) => updateDraft((current) => ({ ...current, generation_brief: { ...current.generation_brief, role: event.target.value } }))}
                />
                <Input
                  value={draft.generation_brief.seniority}
                  placeholder="Seniority"
                  onChange={(event) => updateDraft((current) => ({ ...current, generation_brief: { ...current.generation_brief, seniority: event.target.value } }))}
                />
                <Select
                  mode="tags"
                  value={draft.generation_brief.skills}
                  placeholder="Skills"
                  onChange={(value) => updateDraft((current) => ({ ...current, generation_brief: { ...current.generation_brief, skills: value } }))}
                  open={false}
                />
                <TextArea
                  rows={4}
                  value={draft.generation_brief.job_description}
                  placeholder="Job description"
                  onChange={(event) => updateDraft((current) => ({ ...current, generation_brief: { ...current.generation_brief, job_description: event.target.value } }))}
                />
              </div>
            </div>
          )}
        </Card>

        <Card id="ai-builder-question-flow" className={cn(activeStep === 'question-flow' ? 'block' : 'hidden')}>
          <div className="mb-4 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <ClipboardList size={16} className="text-indigo-600" />
              <h2 className="text-sm font-black uppercase tracking-widest text-slate-900">2. Question / Prompt Flow</h2>
            </div>
            <Button type="dashed" onClick={addQuestion} icon={<Plus size={14} />}>Add Question</Button>
          </div>
          <div className="space-y-4">
            <div className="rounded-2xl border border-indigo-100 bg-indigo-50/60 p-4">
              <p className="text-[10px] font-black uppercase tracking-widest text-indigo-500">{typeSpecificGuidance.title}</p>
              <p className="mt-2 text-sm text-slate-700">{typeSpecificGuidance.description}</p>
            </div>
            <BuilderField label="Intro Prompt" helper="Opening prompt shown before the question sequence begins.">
              <TextArea
                rows={2}
                value={draft.question_flow.intro_message}
                placeholder="Intro message"
                onChange={(event) => updateDraft((current) => ({ ...current, question_flow: { ...current.question_flow, intro_message: event.target.value } }))}
              />
            </BuilderField>
            {draft.question_flow.questions.map((question, index) => (
              <div key={question.id} className="rounded-2xl border border-slate-200 p-4">
                <div className="mb-4 flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-black text-slate-900">{question.title || `Question ${index + 1}`}</p>
                    <p className="mt-1 text-[11px] text-slate-500">{draft.setup.interview_type.replace(/_/g, ' ')} · {question.response_mode} response</p>
                  </div>
                  <div className="flex items-center gap-1">
                    <Button size="small" onClick={() => moveQuestion(question.id, -1)} disabled={index === 0} icon={<ArrowUp size={14} />} />
                    <Button size="small" onClick={() => moveQuestion(question.id, 1)} disabled={index === draft.question_flow.questions.length - 1} icon={<ArrowDown size={14} />} />
                    <Button size="small" onClick={() => duplicateQuestion(question.id)} icon={<Copy size={14} />}>Duplicate</Button>
                    <Button danger type="text" icon={<Trash2 size={14} />} onClick={() => removeQuestion(question.id)}>Remove</Button>
                  </div>
                </div>
                <div className="space-y-4">
                  <BuilderField label="Question Title / Label">
                    <Input value={question.title} placeholder="Question title" onChange={(event) => updateQuestion(question.id, { title: event.target.value })} />
                  </BuilderField>
                  <BuilderField label="Question Prompt">
                    <TextArea rows={3} value={question.question} placeholder="Question prompt" onChange={(event) => updateQuestion(question.id, { question: event.target.value })} />
                  </BuilderField>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <BuilderField label="Response Type">
                      <Select value={question.response_mode} options={RESPONSE_OPTIONS} onChange={(value) => updateQuestion(question.id, { response_mode: value })} />
                    </BuilderField>
                    <BuilderField label={draft.setup.interview_type === 'ai_behavioral' ? 'Competency Being Tested' : draft.setup.interview_type === 'ai_technical' ? 'Problem-Solving Objective' : draft.setup.interview_type === 'ai_screening' ? 'Screening Objective' : 'Evaluation Objective'}>
                      <Input value={question.objective} placeholder="Objective" onChange={(event) => updateQuestion(question.id, { objective: event.target.value })} />
                    </BuilderField>
                  </div>
                  {draft.setup.interview_type === 'ai_screening' ? (
                    <BuilderField label="Knockout Intent Shell" helper="Optional eligibility gate or hard filter logic.">
                      <TextArea rows={2} value={question.knockout_intent_shell} placeholder="Knockout intent shell" onChange={(event) => updateQuestion(question.id, { knockout_intent_shell: event.target.value })} />
                    </BuilderField>
                  ) : null}
                  <div className="rounded-2xl border border-slate-200 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-sm font-bold text-slate-900">Follow-up Logic</p>
                        <p className="text-xs text-slate-500">Structured AI follow-up shell for this question.</p>
                      </div>
                      <Switch checked={question.follow_up_enabled} onChange={(checked) => updateQuestion(question.id, { follow_up_enabled: checked })} />
                    </div>
                    {question.follow_up_enabled ? (
                      <div className="mt-4 space-y-4">
                        <TextArea rows={2} value={question.follow_up_shell} placeholder="Follow-up prompt shell" onChange={(event) => updateQuestion(question.id, { follow_up_shell: event.target.value })} />
                        <Input value={question.follow_up_objective} placeholder="Follow-up objective" onChange={(event) => updateQuestion(question.id, { follow_up_objective: event.target.value })} />
                        <Input value={question.follow_up_trigger_note} placeholder="Optional trigger note" onChange={(event) => updateQuestion(question.id, { follow_up_trigger_note: event.target.value })} />
                      </div>
                    ) : null}
                  </div>
                  <BuilderField label="Expected Answer Guidance" helper="What a strong answer should contain.">
                    <TextArea rows={2} value={question.expected_answer_guidance} placeholder="Expected answer guidance" onChange={(event) => updateQuestion(question.id, { expected_answer_guidance: event.target.value })} />
                  </BuilderField>
                  <BuilderField label="Poor Answer Guidance" helper="What a weak answer may miss or avoid.">
                    <TextArea rows={2} value={question.poor_answer_guidance} placeholder="Poor answer guidance" onChange={(event) => updateQuestion(question.id, { poor_answer_guidance: event.target.value })} />
                  </BuilderField>
                  <BuilderField label={draft.setup.interview_type === 'ai_technical' ? 'Expected Concepts / Topics' : draft.setup.interview_type === 'ai_behavioral' ? 'STAR / Evidence Keywords' : 'Expected Keywords / Concepts'}>
                    <Select mode="tags" value={question.expected_keywords} placeholder="Expected keywords or concepts" onChange={(value) => updateQuestion(question.id, { expected_keywords: value })} open={false} />
                  </BuilderField>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <BuilderField label="Evaluation Dimensions">
                      <Select mode="multiple" value={question.evaluation_dimensions} options={EVALUATION_DIMENSION_OPTIONS} onChange={(value) => updateQuestion(question.id, { evaluation_dimensions: value })} />
                    </BuilderField>
                    <BuilderField label="Skill Tags / Competencies / Domains">
                      <Select mode="tags" value={question.skill_mapping} placeholder="Skill tags" onChange={(value) => updateQuestion(question.id, { skill_mapping: value })} open={false} />
                    </BuilderField>
                  </div>
                  {question.evaluation_dimensions.includes('custom') ? (
                    <BuilderField label="Custom Dimension Shell">
                      <Input value={question.custom_dimension} placeholder="Custom evaluation dimension" onChange={(event) => updateQuestion(question.id, { custom_dimension: event.target.value })} />
                    </BuilderField>
                  ) : null}
                  {question.response_mode === 'video' ? (
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                      <BuilderField label="Preparation Guidance">
                        <Input value={question.prep_guidance} placeholder="Preparation guidance" onChange={(event) => updateQuestion(question.id, { prep_guidance: event.target.value })} />
                      </BuilderField>
                      <BuilderField label="Video Duration Guidance">
                        <Input value={question.duration_guidance} placeholder="Duration guidance" onChange={(event) => updateQuestion(question.id, { duration_guidance: event.target.value })} />
                      </BuilderField>
                    </div>
                  ) : null}
                  {question.response_mode === 'audio' ? (
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                      <BuilderField label="Verbal Guidance">
                        <Input value={question.prep_guidance} placeholder="Verbal communication guidance" onChange={(event) => updateQuestion(question.id, { prep_guidance: event.target.value })} />
                      </BuilderField>
                      <BuilderField label="Audio Duration Guidance">
                        <Input value={question.duration_guidance} placeholder="Duration guidance" onChange={(event) => updateQuestion(question.id, { duration_guidance: event.target.value })} />
                      </BuilderField>
                    </div>
                  ) : null}
                  {question.response_mode === 'text' ? (
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                      <BuilderField label="Minimum Length Guidance">
                        <Input value={question.min_length_guidance} placeholder="Minimum words / characters" onChange={(event) => updateQuestion(question.id, { min_length_guidance: event.target.value })} />
                      </BuilderField>
                      <BuilderField label="Maximum Length Guidance">
                        <Input value={question.max_length_guidance} placeholder="Maximum words / characters" onChange={(event) => updateQuestion(question.id, { max_length_guidance: event.target.value })} />
                      </BuilderField>
                    </div>
                  ) : null}
                  <BuilderField label="Internal Interviewer Note" helper="Optional internal note for future QA or orchestration.">
                    <Input value={question.internal_note} placeholder="Internal note" onChange={(event) => updateQuestion(question.id, { internal_note: event.target.value })} />
                  </BuilderField>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card id="ai-builder-candidate-experience" className={cn(activeStep === 'candidate-experience' ? 'block' : 'hidden')}>
          <div className="mb-4 flex items-center gap-2">
            <Video size={16} className="text-indigo-600" />
            <h2 className="text-sm font-black uppercase tracking-widest text-slate-900">3. Candidate Experience</h2>
          </div>
          <div className="space-y-4">
            <BuilderField label="Instructions" helper="Shown before the candidate starts the AI interview.">
              <TextArea rows={3} value={draft.candidate_experience.instructions} placeholder="Instructions" onChange={(event) => updateDraft((current) => ({ ...current, candidate_experience: { ...current.candidate_experience, instructions: event.target.value } }))} />
            </BuilderField>
            <BuilderField label="Intro Message" helper="Warm opening line used in the runtime experience.">
              <TextArea rows={2} value={draft.candidate_experience.intro_message} placeholder="Intro message" onChange={(event) => updateDraft((current) => ({ ...current, candidate_experience: { ...current.candidate_experience, intro_message: event.target.value } }))} />
            </BuilderField>
            <BuilderField label="Retry Behavior" helper="Explain how retries behave for candidates.">
              <Input value={draft.candidate_experience.retry_behavior} placeholder="Retry behavior" onChange={(event) => updateDraft((current) => ({ ...current, candidate_experience: { ...current.candidate_experience, retry_behavior: event.target.value } }))} />
            </BuilderField>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <div className="rounded-2xl border border-slate-200 p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-slate-900">Practice mode</span>
                  <Switch checked={draft.candidate_experience.practice_mode} onChange={(checked) => updateDraft((current) => ({ ...current, candidate_experience: { ...current.candidate_experience, practice_mode: checked } }))} />
                </div>
              </div>
              <div className="rounded-2xl border border-slate-200 p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-slate-900">Camera required</span>
                  <Switch checked={draft.candidate_experience.camera_required} onChange={(checked) => updateDraft((current) => ({ ...current, candidate_experience: { ...current.candidate_experience, camera_required: checked } }))} />
                </div>
              </div>
              <div className="rounded-2xl border border-slate-200 p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-slate-900">Mic required</span>
                  <Switch checked={draft.candidate_experience.mic_required} onChange={(checked) => updateDraft((current) => ({ ...current, candidate_experience: { ...current.candidate_experience, mic_required: checked } }))} />
                </div>
              </div>
            </div>
          </div>
        </Card>

        <Card id="ai-builder-evaluation" className={cn(activeStep === 'evaluation' ? 'block' : 'hidden')}>
          <div className="mb-4 flex items-center gap-2">
            <ShieldCheck size={16} className="text-indigo-600" />
            <h2 className="text-sm font-black uppercase tracking-widest text-slate-900">4. Evaluation</h2>
          </div>
          <div className="space-y-4">
            <div className="rounded-2xl border border-slate-200 p-4">
              <div className="mb-4 flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-black text-slate-900">Dimensions</p>
                  <p className="text-xs text-slate-500">Configure enabled dimensions, weights, and scoring owner.</p>
                </div>
                <Button type="dashed" onClick={addEvaluationDimension} icon={<Plus size={14} />}>Add Dimension</Button>
              </div>
              <div className="space-y-4">
                {draft.evaluation.dimensions.map((dimension) => (
                  <div key={dimension.id} className="rounded-2xl border border-slate-200 p-4">
                    <div className="mb-4 flex items-center justify-between gap-3">
                      <div>
                        <p className="text-sm font-bold text-slate-900">{dimension.name}</p>
                        <p className="text-xs text-slate-500">{dimension.enabled ? 'Enabled' : 'Disabled'} · {dimension.scoring_owner}</p>
                      </div>
                      <Button danger type="text" onClick={() => removeEvaluationDimension(dimension.id)}>Remove</Button>
                    </div>
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                      <BuilderField label="Dimension">
                        <Select
                          value={dimension.key}
                          options={EVALUATION_DIMENSION_OPTIONS}
                          onChange={(value) => updateEvaluationDimension(dimension.id, {
                            key: value,
                            name: value === 'custom' ? dimension.name : value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase()),
                          })}
                        />
                      </BuilderField>
                      <BuilderField label="Name">
                        <Input value={dimension.name} placeholder="Dimension name" onChange={(event) => updateEvaluationDimension(dimension.id, { name: event.target.value })} />
                      </BuilderField>
                      <BuilderField label="Description">
                        <Input value={dimension.description} placeholder="What this dimension measures" onChange={(event) => updateEvaluationDimension(dimension.id, { description: event.target.value })} />
                      </BuilderField>
                      <BuilderField label="Weight">
                        <InputNumber min={0} max={100} className="w-full" addonAfter="%" value={dimension.weight} onChange={(value) => updateEvaluationDimension(dimension.id, { weight: Number(value || 0) })} />
                      </BuilderField>
                      <BuilderField label="Scoring Owner">
                        <Select
                          value={dimension.scoring_owner}
                          options={[
                            { value: 'ai', label: 'AI' },
                            { value: 'human', label: 'Human' },
                            { value: 'blended', label: 'Blended' },
                          ]}
                          onChange={(value) => updateEvaluationDimension(dimension.id, { scoring_owner: value })}
                        />
                      </BuilderField>
                      <div className="rounded-2xl border border-slate-200 p-4">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-bold text-slate-900">Enabled</span>
                          <Switch checked={dimension.enabled} onChange={(checked) => updateEvaluationDimension(dimension.id, { enabled: checked })} />
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 p-4">
              <div className="mb-4">
                <p className="text-sm font-black text-slate-900">Rubric Builder</p>
                <p className="text-xs text-slate-500">Define excellent, acceptable, weak, risk, and positive-signal guidance.</p>
              </div>
              <div className="space-y-4">
                {draft.evaluation.dimensions.filter((dimension) => dimension.enabled).map((dimension) => (
                  <div key={dimension.id} className="rounded-2xl border border-slate-200 p-4">
                    <p className="text-sm font-bold text-slate-900">{dimension.name}</p>
                    <div className="mt-4 space-y-4">
                      <BuilderField label="Excellent Answer Guidance">
                        <TextArea rows={2} value={dimension.rubric.excellent} placeholder="Excellent answer guidance" onChange={(event) => updateEvaluationRubric(dimension.id, 'excellent', event.target.value)} />
                      </BuilderField>
                      <BuilderField label="Acceptable Answer Guidance">
                        <TextArea rows={2} value={dimension.rubric.acceptable} placeholder="Acceptable answer guidance" onChange={(event) => updateEvaluationRubric(dimension.id, 'acceptable', event.target.value)} />
                      </BuilderField>
                      <BuilderField label="Weak Answer Guidance">
                        <TextArea rows={2} value={dimension.rubric.weak} placeholder="Weak answer guidance" onChange={(event) => updateEvaluationRubric(dimension.id, 'weak', event.target.value)} />
                      </BuilderField>
                      <BuilderField label="Red Flags">
                        <TextArea rows={2} value={dimension.rubric.red_flags} placeholder="Red flags" onChange={(event) => updateEvaluationRubric(dimension.id, 'red_flags', event.target.value)} />
                      </BuilderField>
                      <BuilderField label="Positive Signals">
                        <TextArea rows={2} value={dimension.rubric.positive_signals} placeholder="Positive signals" onChange={(event) => updateEvaluationRubric(dimension.id, 'positive_signals', event.target.value)} />
                      </BuilderField>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 p-4">
              <div className="mb-4">
                <p className="text-sm font-black text-slate-900">Scorecard Alignment</p>
                <p className="text-xs text-slate-500">Map AI evaluation into the Scorecard Engine instead of maintaining a separate scoring system.</p>
              </div>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <BuilderField label="Scorecard Template">
                  <Select
                    allowClear
                    value={draft.evaluation.scorecard_template_id || undefined}
                    placeholder="Link scorecard template"
                    options={scorecards.map((scorecard: any) => ({ value: scorecard.id, label: scorecard.name }))}
                    onChange={(value) => applyScorecardTemplate(value || '')}
                  />
                </BuilderField>
                <div className="rounded-2xl border border-slate-200 p-4">
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Linked Scorecard</p>
                  <p className="mt-2 text-sm font-bold text-slate-900">{selectedScorecard?.name || 'No scorecard linked'}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {selectedScorecard
                      ? `${selectedScorecard.attributes?.length || 0} attributes • ${selectedScorecard.interview_type?.replace(/_/g, ' ')}`
                      : 'Choose a scorecard template to align AI evaluation dimensions.'}
                  </p>
                </div>
                <div className="rounded-2xl border border-slate-200 p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-slate-900">Scoring enabled</span>
                    <Switch checked={draft.evaluation.scoring_enabled} onChange={(checked) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, scoring_enabled: checked } }))} />
                  </div>
                </div>
                <div className="rounded-2xl border border-slate-200 p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-slate-900">Manual override</span>
                    <Switch checked={draft.evaluation.manual_override} onChange={(checked) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, manual_override: checked } }))} />
                  </div>
                </div>
                <BuilderField label="Blend Mode">
                  <Select
                    value={draft.evaluation.scoring_blend_mode}
                    options={[
                      { value: 'ai_only', label: 'AI only' },
                      { value: 'human_only', label: 'Human only' },
                      { value: 'blended', label: 'Blended' },
                    ]}
                    onChange={(value) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, scoring_blend_mode: value } }))}
                  />
                </BuilderField>
                <div className="rounded-2xl border border-slate-200 p-4">
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Sync Target</p>
                  <p className="mt-2 text-sm font-bold text-slate-900">Scorecard Engine</p>
                  <p className="mt-1 text-xs text-slate-500">AI score, dimension ratings, total score, and recommendation flow into the linked scorecard/interview records.</p>
                </div>
              </div>
              {draft.evaluation.scoring_blend_mode === 'blended' ? (
                <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                  <BuilderField label="AI Weight">
                    <InputNumber min={0} max={100} className="w-full" addonAfter="% AI" value={draft.evaluation.ai_scoring_weight} onChange={(value) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, ai_scoring_weight: Number(value || 0) } }))} />
                  </BuilderField>
                  <BuilderField label="Human Weight">
                    <InputNumber min={0} max={100} className="w-full" addonAfter="% Human" value={draft.evaluation.human_scoring_weight} onChange={(value) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, human_scoring_weight: Number(value || 0) } }))} />
                  </BuilderField>
                </div>
              ) : null}
              <div className="mt-4 rounded-2xl border border-slate-200 p-4">
                <div className="mb-4">
                  <p className="text-sm font-black text-slate-900">Score Sync</p>
                  <p className="text-xs text-slate-500">Define what gets written into the Scorecard Engine when the AI interview completes.</p>
                </div>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div className="rounded-2xl border border-slate-200 p-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold text-slate-900">Save AI score</span>
                      <Switch checked={draft.evaluation.score_sync.save_ai_score_to_scorecard} onChange={(checked) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, score_sync: { ...current.evaluation.score_sync, save_ai_score_to_scorecard: checked } } }))} />
                    </div>
                  </div>
                  <div className="rounded-2xl border border-slate-200 p-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold text-slate-900">Save dimension scores</span>
                      <Switch checked={draft.evaluation.score_sync.save_dimension_scores_to_scorecard} onChange={(checked) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, score_sync: { ...current.evaluation.score_sync, save_dimension_scores_to_scorecard: checked } } }))} />
                    </div>
                  </div>
                  <div className="rounded-2xl border border-slate-200 p-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold text-slate-900">Save total score</span>
                      <Switch checked={draft.evaluation.score_sync.save_total_score_to_scorecard} onChange={(checked) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, score_sync: { ...current.evaluation.score_sync, save_total_score_to_scorecard: checked } } }))} />
                    </div>
                  </div>
                  <div className="rounded-2xl border border-slate-200 p-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold text-slate-900">Save AI recommendation</span>
                      <Switch checked={draft.evaluation.score_sync.save_ai_recommendation_to_scorecard} onChange={(checked) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, score_sync: { ...current.evaluation.score_sync, save_ai_recommendation_to_scorecard: checked } } }))} />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 p-4">
              <div className="mb-4">
                <p className="text-sm font-black text-slate-900">Recommendation Rules</p>
                <p className="text-xs text-slate-500">Map weighted scores to enterprise recommendation bands.</p>
              </div>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <BuilderField label="Strong Recommend">
                  <InputNumber min={0} max={100} className="w-full" value={draft.evaluation.recommendation_thresholds.strong_recommend} onChange={(value) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, recommendation_thresholds: { ...current.evaluation.recommendation_thresholds, strong_recommend: Number(value || 0) } } }))} />
                </BuilderField>
                <BuilderField label="Recommend">
                  <InputNumber min={0} max={100} className="w-full" value={draft.evaluation.recommendation_thresholds.recommend} onChange={(value) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, recommendation_thresholds: { ...current.evaluation.recommendation_thresholds, recommend: Number(value || 0) } } }))} />
                </BuilderField>
                <BuilderField label="Neutral">
                  <InputNumber min={0} max={100} className="w-full" value={draft.evaluation.recommendation_thresholds.neutral} onChange={(value) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, recommendation_thresholds: { ...current.evaluation.recommendation_thresholds, neutral: Number(value || 0) } } }))} />
                </BuilderField>
                <BuilderField label="Concern">
                  <InputNumber min={0} max={100} className="w-full" value={draft.evaluation.recommendation_thresholds.concern} onChange={(value) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, recommendation_thresholds: { ...current.evaluation.recommendation_thresholds, concern: Number(value || 0) } } }))} />
                </BuilderField>
                <BuilderField label="Reject">
                  <InputNumber min={0} max={100} className="w-full" value={draft.evaluation.recommendation_thresholds.reject} onChange={(value) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, recommendation_thresholds: { ...current.evaluation.recommendation_thresholds, reject: Number(value || 0) } } }))} />
                </BuilderField>
                <BuilderField label="Recommendation Logic">
                  <Select value={draft.evaluation.recommendation_logic} options={[
                    { value: 'strong_recommend', label: 'Strong recommend' },
                    { value: 'recommend', label: 'Recommend' },
                    { value: 'neutral', label: 'Neutral' },
                    { value: 'concern', label: 'Concern' },
                    { value: 'reject', label: 'Reject' },
                  ]} onChange={(value) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, recommendation_logic: value } }))} />
                </BuilderField>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 p-4">
              <div className="mb-4">
                <p className="text-sm font-black text-slate-900">Scorecard Mapping Review</p>
                <p className="text-xs text-slate-500">See how AI evaluation dimensions map into scorecard attributes and how question tags support the scorecard record.</p>
              </div>
              <div className="space-y-3">
                {draft.evaluation.dimensions.map((dimension) => (
                  <div key={dimension.id} className="rounded-2xl border border-slate-200 p-4">
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-[1.2fr_1fr]">
                      <div>
                        <p className="text-sm font-bold text-slate-900">{dimension.name}</p>
                        <p className="mt-1 text-xs text-slate-500">Owner: {dimension.scoring_owner} • Weight: {dimension.weight}%</p>
                      </div>
                      <BuilderField label="Mapped Scorecard Attribute">
                        <Select
                          allowClear
                          value={dimension.scorecard_attribute_name || undefined}
                          placeholder="Map to scorecard attribute"
                          options={scorecardAttributes.map((attribute: any) => ({
                            value: attribute.attribute_name,
                            label: `${attribute.attribute_name} (${attribute.weight}% weight)`,
                          }))}
                          onChange={(value) => updateEvaluationDimension(dimension.id, { scorecard_attribute_name: value || '' })}
                        />
                      </BuilderField>
                    </div>
                  </div>
                ))}
                {questionDimensionMap.map((row) => (
                  <div key={row.id} className="rounded-2xl border border-slate-200 p-4">
                    <p className="text-sm font-bold text-slate-900">{row.label}</p>
                    <p className="mt-2 text-xs text-slate-500">Dimensions: {row.dimensions.length ? row.dimensions.join(', ') : 'Not mapped yet'}</p>
                    <p className="mt-1 text-xs text-slate-500">Skills: {row.skills.length ? row.skills.join(', ') : 'No skill tags yet'}</p>
                  </div>
                ))}
                <BuilderField label="Skill Mapping Review">
                  <Select mode="tags" value={draft.evaluation.skill_mapping} placeholder="Shared evaluation skill mapping" onChange={(value) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, skill_mapping: value } }))} open={false} />
                </BuilderField>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 p-4">
              <div className="mb-4">
                <p className="text-sm font-black text-slate-900">Scorecard Preview</p>
                <p className="text-xs text-slate-500">Preview how AI score, dimension scores, recommendation, and blended total appear in the Scorecard Engine.</p>
              </div>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <div className="rounded-2xl border border-slate-200 bg-slate-950 p-4 text-white">
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">AI Score</p>
                  <p className="mt-2 text-2xl font-black">{previewAIScore}</p>
                  <p className="mt-1 text-xs text-slate-400">Saved to `Interview.ai_score`</p>
                </div>
                <div className="rounded-2xl border border-slate-200 p-4">
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Human Score</p>
                  <p className="mt-2 text-2xl font-black text-slate-900">{previewHumanScore}</p>
                  <p className="mt-1 text-xs text-slate-500">Supports multi-interviewer blending</p>
                </div>
                <div className="rounded-2xl border border-slate-200 p-4">
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Final Blended Score</p>
                  <p className="mt-2 text-2xl font-black text-slate-900">{previewFinalScore}</p>
                  <p className="mt-1 text-xs text-slate-500">{previewRecommendation.replace(/_/g, ' ')}</p>
                </div>
              </div>
              <div className="mt-4 space-y-2">
                {enabledMappedDimensions.map((item) => (
                  <div key={item.id} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                    <div>
                      <p className="text-sm font-bold text-slate-900">{item.dimension.name}</p>
                      <p className="text-xs text-slate-500">{item.linkedAttribute?.attribute_name || item.dimension.scorecard_attribute_name || 'Unmapped attribute'}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-black text-slate-900">{item.sampleScore}</p>
                      <p className="text-[11px] text-slate-500">dimension score</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 p-4">
              <div className="mb-4">
                <p className="text-sm font-black text-slate-900">Final Outcome Suggestion</p>
                <p className="text-xs text-slate-500">Shell for final score, recommendation, and next action guidance.</p>
              </div>
              <div className="space-y-4">
                <BuilderField label="Suggested Score Shell">
                  <Input value={draft.evaluation.final_outcome_suggestion.suggested_score_shell} placeholder="Suggested score shell" onChange={(event) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, final_outcome_suggestion: { ...current.evaluation.final_outcome_suggestion, suggested_score_shell: event.target.value } } }))} />
                </BuilderField>
                <BuilderField label="Suggested Recommendation Shell">
                  <Input value={draft.evaluation.final_outcome_suggestion.suggested_recommendation_shell} placeholder="Suggested recommendation shell" onChange={(event) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, final_outcome_suggestion: { ...current.evaluation.final_outcome_suggestion, suggested_recommendation_shell: event.target.value } } }))} />
                </BuilderField>
                <BuilderField label="Suggested Next Action Shell">
                  <Input value={draft.evaluation.final_outcome_suggestion.suggested_next_action_shell} placeholder="Suggested next action shell" onChange={(event) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, final_outcome_suggestion: { ...current.evaluation.final_outcome_suggestion, suggested_next_action_shell: event.target.value } } }))} />
                </BuilderField>
              </div>
            </div>
          </div>
        </Card>

        <Card id="ai-builder-outcome-routing" className={cn(activeStep === 'outcome-routing' ? 'block' : 'hidden')}>
          <div className="mb-4 flex items-center gap-2">
            <Workflow size={16} className="text-indigo-600" />
            <h2 className="text-sm font-black uppercase tracking-widest text-slate-900">5. Outcome / Routing</h2>
          </div>
          <div className="space-y-4">
            <div className="rounded-2xl border border-slate-200 p-4">
              <div className="mb-4 flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-black text-slate-900">Outcome Rules</p>
                  <p className="text-xs text-slate-500">Enterprise recommendation outcomes with editable routing behavior.</p>
                </div>
                <Button type="dashed" onClick={() => addOutcomeRule()} icon={<Plus size={14} />}>Add Outcome</Button>
              </div>
              <div className="space-y-4">
                {draft.outcome_routing.outcomes.map((rule) => (
                  <div key={rule.id} className="rounded-2xl border border-slate-200 p-4">
                    <div className="mb-4 flex items-center justify-between gap-3">
                      <p className="text-sm font-bold text-slate-900">{rule.label}</p>
                      <Button danger type="text" onClick={() => removeOutcomeRule(rule.id)}>Remove</Button>
                    </div>
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                      <BuilderField label="Outcome">
                        <Input value={rule.label} placeholder="Outcome label" onChange={(event) => updateOutcomeRule(rule.id, { label: event.target.value })} />
                      </BuilderField>
                      <BuilderField label="Route Action">
                        <Select
                          value={rule.route_action}
                          options={[
                            { value: 'move_to_next_stage', label: 'Move to next stage' },
                            { value: 'manual_review_queue', label: 'Manual review queue' },
                            { value: 'reject_candidate', label: 'Reject candidate' },
                            { value: 'shortlist', label: 'Shortlist' },
                            { value: 'schedule_next_interview', label: 'Schedule next interview' },
                          ]}
                          onChange={(value) => updateOutcomeRule(rule.id, { route_action: value })}
                        />
                      </BuilderField>
                      <BuilderField label="Minimum Score">
                        <InputNumber min={0} max={100} className="w-full" value={rule.min_score} onChange={(value) => updateOutcomeRule(rule.id, { min_score: Number(value || 0) })} />
                      </BuilderField>
                      <BuilderField label="Maximum Score">
                        <InputNumber min={0} max={100} className="w-full" value={rule.max_score} onChange={(value) => updateOutcomeRule(rule.id, { max_score: Number(value || 100) })} />
                      </BuilderField>
                      <BuilderField label="Next Stage Mapping" helper="Used when route action forwards the candidate.">
                        <Input value={rule.next_stage_mapping} placeholder="Next stage mapping" onChange={(event) => updateOutcomeRule(rule.id, { next_stage_mapping: event.target.value })} />
                      </BuilderField>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 p-4">
              <div className="mb-4">
                <p className="text-sm font-black text-slate-900">Score Threshold Mapping</p>
                <p className="text-xs text-slate-500">Weighted score bands connected to outcome rules.</p>
              </div>
              <div className="space-y-3">
                {draft.outcome_routing.outcomes.map((rule) => (
                  <div key={rule.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <p className="text-sm font-bold text-slate-900">{rule.min_score} - {rule.max_score} → {rule.label}</p>
                    <p className="mt-1 text-xs text-slate-500">{rule.route_action.replace(/_/g, ' ')}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 p-4">
              <div className="mb-4">
                <p className="text-sm font-black text-slate-900">Automation Behavior</p>
                <p className="text-xs text-slate-500">Define auto-decision behavior and recruiter review safeguards.</p>
              </div>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="rounded-2xl border border-slate-200 p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-slate-900">Auto decision enabled</span>
                    <Switch checked={draft.outcome_routing.automation.auto_decision_enabled} onChange={(checked) => updateDraft((current) => ({ ...current, outcome_routing: { ...current.outcome_routing, automation: { ...current.outcome_routing.automation, auto_decision_enabled: checked } } }))} />
                  </div>
                </div>
                <div className="rounded-2xl border border-slate-200 p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-slate-900">Manual override allowed</span>
                    <Switch checked={draft.outcome_routing.automation.manual_override_allowed} onChange={(checked) => updateDraft((current) => ({ ...current, outcome_routing: { ...current.outcome_routing, automation: { ...current.outcome_routing.automation, manual_override_allowed: checked } } }))} />
                  </div>
                </div>
                <div className="rounded-2xl border border-slate-200 p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-slate-900">Recruiter review required</span>
                    <Switch checked={draft.outcome_routing.automation.recruiter_review_required} onChange={(checked) => updateDraft((current) => ({ ...current, outcome_routing: { ...current.outcome_routing, automation: { ...current.outcome_routing.automation, recruiter_review_required: checked } } }))} />
                  </div>
                </div>
                <div className="rounded-2xl border border-slate-200 p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-slate-900">Fallback to manual review</span>
                    <Switch checked={draft.outcome_routing.automation.fallback_to_manual_review} onChange={(checked) => updateDraft((current) => ({ ...current, outcome_routing: { ...current.outcome_routing, automation: { ...current.outcome_routing.automation, fallback_to_manual_review: checked } } }))} />
                  </div>
                </div>
                <BuilderField label="AI Confidence Threshold" helper="If AI confidence falls below this threshold, trigger manual review.">
                  <InputNumber min={0} max={100} className="w-full" addonAfter="% confidence" value={draft.outcome_routing.automation.confidence_threshold} onChange={(value) => updateDraft((current) => ({ ...current, outcome_routing: { ...current.outcome_routing, automation: { ...current.outcome_routing.automation, confidence_threshold: Number(value || 0) } } }))} />
                </BuilderField>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 p-4">
              <div className="mb-4">
                <p className="text-sm font-black text-slate-900">Decision Preview</p>
                <p className="text-xs text-slate-500">How evaluation output routes into the workflow.</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-950 p-5 text-white">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Example Decision</p>
                <p className="mt-3 text-xl font-black">{draft.outcome_routing.preview.suggested_outcome || predictedOutcome?.label || 'Strong Recommend'}</p>
                <p className="mt-2 text-sm text-slate-300">{draft.outcome_routing.preview.suggested_route || predictedOutcome?.route_action.replace(/_/g, ' ') || 'Move to next stage'}</p>
                <p className="mt-2 text-xs text-slate-400">
                  Confidence below {draft.outcome_routing.automation.confidence_threshold}% {draft.outcome_routing.automation.fallback_to_manual_review ? 'falls back to manual review.' : 'does not force manual review.'}
                </p>
                <p className="mt-3 text-xs text-slate-400">{draft.outcome_routing.preview.auto_notify_recruiter ? 'Auto notify recruiter enabled.' : 'Auto notify recruiter disabled.'}</p>
              </div>
            </div>
          </div>
        </Card>

        <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3">
          <Button onClick={goToPrevStep} disabled={activeStepIndex === 0}>Back</Button>
          <div className="flex items-center gap-2">
            <Button onClick={() => setPreviewOpen(true)}>Preview</Button>
            {activeStepIndex < BUILDER_STEP_ORDER.length - 1 ? (
              <Button type="primary" onClick={goToNextStep}>Next Step</Button>
            ) : (
              <Button type="primary" loading={saving} onClick={saveDraft}>Save AI Interview</Button>
            )}
          </div>
        </div>
      </div>

      <div className="col-span-12 lg:col-span-3 space-y-6">
        <Card>
          <div className="mb-4 flex items-center gap-2">
            <Eye size={16} className="text-indigo-600" />
            <h2 className="text-sm font-black uppercase tracking-widest text-slate-900">Preview</h2>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-950 p-5 text-white">
            <p className="text-[10px] font-black uppercase tracking-[0.25em] text-slate-400">Candidate View</p>
            <h3 className="mt-3 text-xl font-black">{draft.setup.name || 'Untitled AI Interview'}</h3>
            <p className="mt-2 text-sm text-slate-300">{draft.question_flow.intro_message || draft.candidate_experience.intro_message || 'Candidate intro message appears here.'}</p>
            <div className="mt-5 grid grid-cols-3 gap-3">
              <div className="rounded-xl bg-white/5 p-3">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Response</p>
                <p className="mt-2 text-sm font-bold">{draft.setup.response_mode}</p>
              </div>
              <div className="rounded-xl bg-white/5 p-3">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Duration</p>
                <p className="mt-2 text-sm font-bold">{draft.setup.duration_minutes}m</p>
              </div>
              <div className="rounded-xl bg-white/5 p-3">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Questions</p>
                <p className="mt-2 text-sm font-bold">{draft.question_flow.questions.filter((question) => question.question.trim()).length}</p>
              </div>
            </div>
            <div className="mt-4 rounded-xl bg-white/5 p-3">
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Type Context</p>
              <p className="mt-2 text-xs text-slate-300">{typeSpecificGuidance.description}</p>
            </div>
            <div className="mt-4 rounded-xl bg-white/5 p-3">
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Outcome Logic</p>
              <div className="mt-2 space-y-2 text-xs text-slate-300">
                {draft.outcome_routing.outcomes.slice(0, 3).map((rule) => (
                  <p key={rule.id}>
                    {rule.min_score}-{rule.max_score}: {rule.label} {'->'} {rule.route_action.replace(/_/g, ' ')}
                  </p>
                ))}
                {draft.outcome_routing.outcomes.length > 3 ? (
                  <p className="text-slate-400">+{draft.outcome_routing.outcomes.length - 3} more outcome rules configured</p>
                ) : null}
              </div>
            </div>
          </div>
        </Card>

        <Card className={cn(activeStep === 'question-flow' ? 'block' : 'hidden')}>
          <h3 className="text-sm font-black uppercase tracking-widest text-slate-900">Question Sequence</h3>
          <div className="mt-4 space-y-3">
            {draft.question_flow.questions.map((question, index) => (
              <div key={question.id} className="rounded-2xl border border-slate-200 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Question {index + 1}</p>
                    <p className="mt-2 text-sm font-bold text-slate-900">{question.title || question.question || 'Prompt pending'}</p>
                    <p className="mt-1 text-xs text-slate-500">{question.objective || 'Objective pending'}</p>
                  </div>
                  {responseTag(question.response_mode)}
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card className={cn(activeStep === 'question-flow' ? 'block' : 'hidden')}>
          <h3 className="text-sm font-black uppercase tracking-widest text-slate-900">Response Summary</h3>
          <div className="mt-4 flex flex-wrap gap-2">
            {['video', 'audio', 'text'].map((mode) => {
              const count = draft.question_flow.questions.filter((question) => question.response_mode === mode).length
              return <Tag key={mode}>{mode}: {count}</Tag>
            })}
          </div>
        </Card>

        <Card>
          <h3 className="text-sm font-black uppercase tracking-widest text-slate-900">Engine Integration</h3>
          <div className="mt-4 flex flex-wrap gap-2">
            <Tag color="blue">Question Engine</Tag>
            <Tag color="purple">Scorecard Engine</Tag>
            <Tag color="cyan">Flow Engine</Tag>
            <Tag color="gold">Decision Engine</Tag>
          </div>
        </Card>

        <Card className={cn(activeStep === 'evaluation' ? 'block' : 'hidden')}>
          <h3 className="text-sm font-black uppercase tracking-widest text-slate-900">Evaluation Summary</h3>
          <div className="mt-4 space-y-3">
            <div className="rounded-2xl border border-slate-200 p-4">
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Scorecard Sync</p>
              <p className="mt-2 text-sm font-bold text-slate-900">{selectedScorecard?.name || 'No linked scorecard'}</p>
              <p className="mt-1 text-xs text-slate-500">AI {previewAIScore} · Human {previewHumanScore} · Final {previewFinalScore}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 p-4">
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Weighted Dimensions</p>
              <p className="mt-2 text-sm font-bold text-slate-900">{draft.evaluation.dimensions.filter((dimension) => dimension.enabled).length} active · {totalEnabledDimensionWeight}% total weight</p>
            </div>
            <div className="rounded-2xl border border-slate-200 p-4">
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Blend Logic</p>
              <p className="mt-2 text-sm font-bold text-slate-900">
                {draft.evaluation.scoring_blend_mode === 'blended'
                  ? `${draft.evaluation.ai_scoring_weight}% AI / ${draft.evaluation.human_scoring_weight}% Human`
                  : draft.evaluation.scoring_blend_mode === 'ai_only'
                    ? 'AI only'
                    : 'Human only'}
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200 p-4">
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Recommendation Thresholds</p>
              <p className="mt-2 text-xs text-slate-600">
                Strong recommend {draft.evaluation.recommendation_thresholds.strong_recommend}+<br />
                Recommend {draft.evaluation.recommendation_thresholds.recommend}+<br />
                Neutral {draft.evaluation.recommendation_thresholds.neutral}+<br />
                Concern {draft.evaluation.recommendation_thresholds.concern}+<br />
                Reject {draft.evaluation.recommendation_thresholds.reject}+
              </p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )

  const listView = (
    <div className="space-y-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-sm font-black uppercase tracking-widest text-slate-900">AI Interviews</h2>
            <p className="mt-1 text-xs text-slate-500">Reusable AI interview templates for jobs, flows, and stages.</p>
          </div>
          <Button type="primary" icon={<Plus size={14} />} onClick={openCreate}>
            Create AI Interview
          </Button>
        </div>
      </div>

      <Card>
        <Table
          rowKey="id"
          loading={isLoading}
          columns={columns}
          dataSource={templates}
          pagination={{ pageSize: 10 }}
          locale={{
            emptyText: (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description={<span className="text-xs text-slate-500">No AI interviews yet.</span>}
              />
            ),
          }}
        />
      </Card>
    </div>
  )

  const content = isBuilderOpen ? builder : listView

  if (embedded) {
    return (
      <>
        {isBuilderOpen ? (
          <div className="mb-4 flex items-center justify-between">
            <Button icon={<ArrowLeft size={14} />} onClick={() => setIsBuilderOpen(false)}>
              Back to AI Interviews
            </Button>
            <Space>
              <Button onClick={() => setPreviewOpen(true)}>Preview</Button>
              <Button type="primary" loading={saving} onClick={saveDraft}>Save AI Interview</Button>
            </Space>
          </div>
        ) : null}
        {content}
        <PreviewModal open={previewOpen} draft={draft} onClose={() => setPreviewOpen(false)} />
        <Modal open={createMethodOpen} onCancel={() => setCreateMethodOpen(false)} onOk={startBuilder} title="Create AI Interview" okText="Continue">
          <div className="space-y-3 pt-4">
            {CREATION_METHODS.map((method) => {
              const Icon = method.icon
              return (
                <button
                  key={method.value}
                  type="button"
                  onClick={() => setCreationMethod(method.value)}
                  className={cn(
                    'w-full rounded-2xl border p-4 text-left transition',
                    creationMethod === method.value
                      ? 'border-indigo-300 bg-indigo-50'
                      : 'border-slate-200 bg-white hover:border-slate-300',
                  )}
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-900 text-white">
                      <Icon size={18} />
                    </div>
                    <div>
                      <p className="text-sm font-black text-slate-900">{method.label}</p>
                      <p className="mt-1 text-xs text-slate-500">{method.description}</p>
                    </div>
                  </div>
                </button>
              )
            })}
          </div>
        </Modal>
      </>
    )
  }

  return (
    <div className="flex flex-col h-[calc(100vh-96px)] bg-[#F8FAFC] -m-4 overflow-hidden">
      <div className="flex h-14 flex-none items-center justify-between border-b border-slate-200 bg-white px-6">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-slate-900 text-white">
              <Cpu size={18} />
            </div>
            <h1 className="text-base font-black text-slate-900 tracking-tight leading-none uppercase">AI Interviews</h1>
          </div>
          <div className="flex items-center gap-1 rounded-lg bg-slate-100 p-0.5 ml-2">
            <button onClick={() => navigate('/interviews')} className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-slate-700">
              <List size={12} /> Command Center
            </button>
            <button onClick={() => navigate('/interviews/types')} className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-slate-700">
              <Target size={12} /> Registry
            </button>
            <button onClick={() => navigate('/interviews/types/ai-interviews')} className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[10px] font-black uppercase tracking-widest bg-white text-indigo-700 shadow-sm border border-indigo-50">
              <Cpu size={12} /> AI Interviews
            </button>
            <button onClick={() => navigate('/interviews/templates')} className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-slate-700">
              <LayoutGrid size={12} /> Templates
            </button>
          </div>
        </div>
      </div>

      <div className="p-6 flex-1 overflow-auto">{content}</div>
    </div>
  )
}
