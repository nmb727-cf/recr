import { useState, useRef, useCallback, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Form, Input, Select, Switch, Tag, message, Tabs, Spin, Modal, Tooltip, Slider } from 'antd'
import {
  ArrowLeft, FileText, Save, Eye, Send, Plus, Layers, GitBranch,
  Trash2, Copy, GripVertical, Settings, ToggleRight, Hash, AlignLeft,
  AlignJustify, CheckSquare, ListIcon, Upload, ChevronDown, ChevronUp,
  Zap, HelpCircle, CheckCircle, XCircle, AlertTriangle, Star, Shield,
  Calendar, X, ChevronRight, Award, Target, Users,
} from 'lucide-react'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useQueryClient } from '@tanstack/react-query'
import { prequalificationApi } from '@/api/prequalification'
import { cn } from '@/utils/cn'

// Suppress unused import warnings for Form (used indirectly via antd patterns)
void Form

// ─── Question type config ─────────────────────────────────────────────────────

const Q_TYPES = [
  { value: 'yes_no',        label: 'Yes / No',        icon: ToggleRight,   hint: 'Simple yes or no answer'         },
  { value: 'single_select', label: 'Single Choice',   icon: CheckSquare,   hint: 'Pick one from multiple options'  },
  { value: 'multi_select',  label: 'Multiple Choice', icon: CheckSquare,   hint: 'Pick any that apply'             },
  { value: 'short_text',    label: 'Short Answer',    icon: AlignLeft,     hint: 'One line text response'          },
  { value: 'long_text',     label: 'Paragraph',       icon: AlignJustify,  hint: 'Multi-line text response'        },
  { value: 'number',        label: 'Number',          icon: Hash,          hint: 'Numeric value'                   },
  { value: 'dropdown',      label: 'Dropdown',        icon: ListIcon,      hint: 'Select from a dropdown list'     },
  { value: 'date',          label: 'Date',            icon: Calendar,      hint: 'Date picker'                     },
  { value: 'file_upload',   label: 'File Upload',     icon: Upload,        hint: 'Upload a document or file'       },
]

const HAS_OPTIONS = ['yes_no', 'single_select', 'multi_select', 'dropdown', 'multiple_choice']

const YES_NO_OPTIONS = [
  { label: 'Yes', value: 'yes' },
  { label: 'No',  value: 'no'  },
]

// ─── Condition + Action config ────────────────────────────────────────────────

const CONDITIONS = [
  { value: 'equals',      label: 'is'             },
  { value: 'not_equals',  label: 'is not'         },
  { value: 'greater_than',label: 'greater than'   },
  { value: 'less_than',   label: 'less than'      },
  { value: 'contains',    label: 'contains'       },
  { value: 'in',          label: 'is one of'      },
  { value: 'not_in',      label: 'is not one of'  },
  { value: 'is_empty',    label: 'is empty'       },
  { value: 'is_not_empty',label: 'is not empty'   },
]

const MULTI_VALUE_CONDITIONS = ['in', 'not_in']

const ACTIONS = [
  { value: 'reject',           label: 'Auto Reject',         color: 'text-red-600',    bg: 'bg-red-50 border-red-200'    },
  { value: 'manual_review',    label: 'Flag for Review',     color: 'text-amber-700',  bg: 'bg-amber-50 border-amber-200'},
  { value: 'next_question',    label: 'Continue to Next',    color: 'text-green-700',  bg: 'bg-green-50 border-green-200'},
  { value: 'skip_section',     label: 'Jump to Section',     color: 'text-blue-600',   bg: 'bg-blue-50 border-blue-200'  },
  { value: 'route_to_outcome', label: 'Route to Outcome',    color: 'text-indigo-600', bg: 'bg-indigo-50 border-indigo-200'},
  { value: 'end_form',         label: 'End Form',            color: 'text-slate-600',  bg: 'bg-slate-50 border-slate-200'},
  { value: 'show_question',    label: 'Show Question',       color: 'text-teal-600',   bg: 'bg-teal-50 border-teal-200'  },
  { value: 'hide_question',    label: 'Hide Question',       color: 'text-slate-500',  bg: 'bg-slate-50 border-slate-200'},
]

const OUTCOMES = [
  { code: 'pass',                          label: 'Pass',                        color: 'text-green-700',  bg: 'bg-green-50',  icon: CheckCircle    },
  { code: 'reject',                        label: 'Auto Reject',                 color: 'text-red-700',    bg: 'bg-red-50',    icon: XCircle        },
  { code: 'manual_review',                 label: 'Manual Review',               color: 'text-amber-700',  bg: 'bg-amber-50',  icon: AlertTriangle  },
  { code: 'shortlisted_for_ai_screening',  label: 'AI Screening',                color: 'text-purple-700', bg: 'bg-purple-50', icon: Zap            },
  { code: 'shortlisted_for_technical',     label: 'Technical Interview',         color: 'text-blue-700',   bg: 'bg-blue-50',   icon: Target         },
  { code: 'shortlisted_for_hr_interview',  label: 'HR Interview',                color: 'text-indigo-700', bg: 'bg-indigo-50', icon: Users          },
  { code: 'shortlisted_for_assignment',    label: 'Take-Home Assignment',        color: 'text-cyan-700',   bg: 'bg-cyan-50',   icon: Award          },
  { code: 'needs_recruiter_call',          label: 'Recruiter Call',              color: 'text-teal-700',   bg: 'bg-teal-50',   icon: HelpCircle     },
]

// ─── Question preset library ──────────────────────────────────────────────────

interface PresetQuestion {
  text: string
  type: string
  options?: Array<{ label: string; value: string }>
  is_knockout?: boolean
  score_weight?: number
  help?: string
}

const PRESETS: Record<string, PresetQuestion[]> = {
  'Eligibility': [
    { text: 'Are you legally authorized to work in this country?',    type: 'yes_no', is_knockout: true,  score_weight: 0,  help: 'Required for compliance'                     },
    { text: 'Do you require visa sponsorship now or in the future?',  type: 'yes_no', is_knockout: false, score_weight: 0                                                       },
    { text: 'Are you open to relocation for this role?',              type: 'yes_no', is_knockout: false, score_weight: 5                                                       },
    { text: 'Are you comfortable working night shifts?',              type: 'yes_no', is_knockout: false, score_weight: 0                                                       },
    { text: 'Can you join within 30 days if selected?',               type: 'yes_no', is_knockout: false, score_weight: 10, help: 'Immediate joiners preferred'                 },
  ],
  'Experience': [
    { text: 'Total years of professional experience',                 type: 'number',       score_weight: 10, help: 'Enter number of years'                                     },
    { text: 'Years of relevant experience in this domain',            type: 'number',       score_weight: 15                                                                     },
    { text: 'Current job title',                                      type: 'short_text',   score_weight: 0                                                                      },
    { text: 'Current industry or domain',                             type: 'dropdown',     score_weight: 5,  options: [{label:'Technology',value:'tech'},{label:'Finance',value:'finance'},{label:'Healthcare',value:'healthcare'},{label:'Education',value:'education'},{label:'Manufacturing',value:'manufacturing'},{label:'Other',value:'other'}] },
    { text: 'Highest educational qualification',                      type: 'single_select',score_weight: 5,  options: [{label:"High School",value:"high_school"},{label:"Diploma",value:"diploma"},{label:"Bachelor's",value:"bachelor"},{label:"Master's",value:"master"},{label:"PhD",value:"phd"},{label:"Other",value:"other"}] },
  ],
  'Skills': [
    { text: 'Do you have experience with the required technology stack?', type: 'yes_no',      score_weight: 20, is_knockout: false                                               },
    { text: 'Do you hold a relevant certification?',                  type: 'yes_no',          score_weight: 10                                                                   },
    { text: 'Rate your proficiency level in the primary skill',       type: 'single_select',   score_weight: 15, options: [{label:'Beginner',value:'beginner'},{label:'Intermediate',value:'intermediate'},{label:'Advanced',value:'advanced'},{label:'Expert',value:'expert'}] },
    { text: 'Are you available for a technical assessment test?',     type: 'yes_no',          score_weight: 5                                                                    },
  ],
  'Compensation': [
    { text: 'Current monthly/annual salary (CTC)',                    type: 'number',       score_weight: 0,  help: 'Specify currency in your answer'                            },
    { text: 'Expected salary (CTC)',                                  type: 'number',       score_weight: 0                                                                       },
    { text: 'Notice period (in days)',                                type: 'number',       score_weight: 0,  help: 'Enter 0 if immediately available'                           },
    { text: 'Earliest available start date',                          type: 'date',         score_weight: 5                                                                       },
  ],
  'Role Fit': [
    { text: 'Preferred work mode',                                    type: 'single_select',score_weight: 5,  options: [{label:'Onsite',value:'onsite'},{label:'Remote',value:'remote'},{label:'Hybrid',value:'hybrid'},{label:'Flexible',value:'flexible'}] },
    { text: 'Are you comfortable with frequent travel?',              type: 'yes_no',       score_weight: 5                                                                       },
    { text: 'Do you have a portfolio or work samples available?',     type: 'yes_no',       score_weight: 8                                                                       },
    { text: 'Are you willing to complete a take-home assignment?',    type: 'yes_no',       score_weight: 5                                                                       },
    { text: 'Do you have team leadership or management experience?',  type: 'yes_no',       score_weight: 10                                                                      },
  ],
  'Language': [
    { text: 'English proficiency level',                              type: 'single_select',score_weight: 10, options: [{label:'Basic',value:'basic'},{label:'Conversational',value:'conversational'},{label:'Business Fluent',value:'business'},{label:'Native',value:'native'}] },
    { text: 'Do you have experience in client-facing communication?', type: 'yes_no',       score_weight: 8                                                                       },
    { text: 'Are you comfortable presenting to senior stakeholders?', type: 'yes_no',       score_weight: 5                                                                       },
  ],
}

// ─── Helper functions ─────────────────────────────────────────────────────────

function getTypeConfig(type: string) {
  return Q_TYPES.find(t => t.value === type) ?? Q_TYPES.find(t => t.value === 'short_text')!
}

function getActionConfig(action: string) {
  return ACTIONS.find(a => a.value === action) ?? ACTIONS[2]
}

function getOutcomeConfig(code: string) {
  return OUTCOMES.find(o => o.code === code) ?? OUTCOMES[0]
}

function getDefaultOptions(type: string): Array<{ label: string; value: string }> {
  if (type === 'yes_no') return YES_NO_OPTIONS
  if (type === 'single_select' || type === 'multi_select') return [{ label: 'Option 1', value: 'option_1' }, { label: 'Option 2', value: 'option_2' }]
  if (type === 'dropdown') return [{ label: 'Option 1', value: 'option_1' }, { label: 'Option 2', value: 'option_2' }]
  return []
}

// ─── Rule chip ────────────────────────────────────────────────────────────────

function RuleChip({ rule, onDelete }: { rule: any; onDelete: () => void }) {
  const ac = getActionConfig(rule.action_type)
  const noVal = ['is_empty', 'is_not_empty'].includes(rule.condition_type)
  const isMulti = MULTI_VALUE_CONDITIONS.includes(rule.condition_type)
  const condLabel = CONDITIONS.find(c => c.value === rule.condition_type)?.label ?? rule.condition_type
  return (
    <div className="flex items-center gap-2 text-[11px] bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 group">
      <GitBranch size={11} className="text-slate-400 shrink-0" />
      <span className="text-slate-500 font-semibold">IF answer</span>
      <span className="font-mono bg-white border border-slate-200 rounded px-1.5 py-0.5 text-[10px] text-slate-700">{condLabel}</span>
      {!noVal && rule.compare_value && (
        isMulti ? (
          <span className="font-mono bg-white border border-slate-200 rounded px-1.5 py-0.5 text-[10px] text-slate-700">
            [{rule.compare_value.split(',').map((v: string) => v.trim()).join(', ')}]
          </span>
        ) : (
          <span className="font-mono bg-white border border-slate-200 rounded px-1.5 py-0.5 text-[10px] text-slate-700">&ldquo;{rule.compare_value}&rdquo;</span>
        )
      )}
      <span className="text-slate-400">→</span>
      <span className={cn('text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded-lg border', ac.bg, ac.color)}>
        {ac.label}
        {rule.action_type === 'route_to_outcome' && rule.outcome_code && `: ${getOutcomeConfig(rule.outcome_code).label}`}
      </span>
      <button onClick={onDelete} className="ml-auto opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-500 transition-all shrink-0">
        <X size={12} />
      </button>
    </div>
  )
}

// ─── Add rule inline form ─────────────────────────────────────────────────────

function AddRuleInline({
  question,
  sections,
  onAdded,
}: {
  question: any
  sections: any[]
  formId: string
  onAdded: () => void
}) {
  const [open, setOpen] = useState(false)
  const [condType, setCondType] = useState('equals')
  const [condVal, setCondVal] = useState('')
  const [action, setAction] = useState('next_question')
  const [outcomeCode, setOutcomeCode] = useState('pass')
  const [targetSection, setTargetSection] = useState('')
  const [saving, setSaving] = useState(false)

  const noVal = ['is_empty', 'is_not_empty'].includes(condType)
  const isMultiVal = MULTI_VALUE_CONDITIONS.includes(condType)
  const isChoice = HAS_OPTIONS.includes(question?.question_type ?? '')
  const opts: Array<{ label: string; value: string }> = question?.options_json ?? []

  const handleSave = async () => {
    setSaving(true)
    try {
      await prequalificationApi.createRule({
        question_id: question.id,
        condition_type: condType,
        compare_value: noVal ? '' : condVal,
        action_type: action,
        outcome_code: action === 'route_to_outcome' ? outcomeCode : '',
        target_section_id: action === 'skip_section' ? targetSection || undefined : undefined,
      })
      message.success('Rule added')
      setOpen(false)
      setCondType('equals')
      setCondVal('')
      setAction('next_question')
      onAdded()
    } catch {
      message.error('Failed to save rule')
    } finally {
      setSaving(false)
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-widest text-indigo-600 hover:text-indigo-800 transition-all"
      >
        <Plus size={12} /> Add Logic Rule
      </button>
    )
  }

  return (
    <div className="mt-2 rounded-xl border border-indigo-200 bg-indigo-50/30 p-4 space-y-3">
      <p className="text-[9px] font-black uppercase tracking-widest text-indigo-500">Routing Rule</p>
      {/* IF row */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-[10px] font-black text-slate-500 uppercase">IF</span>
        <span className="text-[10px] font-semibold text-slate-500">answer</span>
        <Select
          size="small"
          value={condType}
          onChange={setCondType}
          style={{ minWidth: 130 }}
          options={CONDITIONS.map(c => ({ value: c.value, label: c.label }))}
        />
        {!noVal && (
          isMultiVal && isChoice && opts.length > 0 ? (
            <Select
              mode="multiple"
              size="small"
              value={condVal ? condVal.split(',') : []}
              onChange={(vals: string[]) => setCondVal(vals.join(','))}
              placeholder="select values"
              style={{ minWidth: 180 }}
              options={opts.map((o: any) => ({ value: o.value ?? o.label ?? o, label: o.label ?? o.value ?? o }))}
            />
          ) : isMultiVal ? (
            <Input
              size="small"
              value={condVal}
              onChange={e => setCondVal(e.target.value)}
              placeholder="val1, val2, val3"
              className="w-40 font-mono text-xs"
            />
          ) : isChoice && opts.length > 0 ? (
            <Select
              size="small"
              value={condVal}
              onChange={setCondVal}
              placeholder="select value"
              style={{ minWidth: 120 }}
              options={opts.map((o: any) => ({ value: o.value ?? o.label ?? o, label: o.label ?? o.value ?? o }))}
            />
          ) : (
            <Input
              size="small"
              value={condVal}
              onChange={e => setCondVal(e.target.value)}
              placeholder="value"
              className="w-28 font-mono text-xs"
            />
          )
        )}
      </div>
      {/* THEN row */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-[10px] font-black text-slate-500 uppercase">THEN</span>
        <Select
          size="small"
          value={action}
          onChange={setAction}
          style={{ minWidth: 160 }}
          options={ACTIONS.map(a => ({ value: a.value, label: a.label }))}
        />
        {action === 'route_to_outcome' && (
          <Select
            size="small"
            value={outcomeCode}
            onChange={setOutcomeCode}
            style={{ minWidth: 160 }}
            options={OUTCOMES.map(o => ({ value: o.code, label: o.label }))}
          />
        )}
        {action === 'skip_section' && (
          <Select
            size="small"
            value={targetSection}
            onChange={setTargetSection}
            placeholder="target section"
            style={{ minWidth: 160 }}
            options={sections.map(s => ({ value: s.id, label: s.title }))}
          />
        )}
      </div>
      <div className="flex gap-2">
        <button onClick={handleSave} disabled={saving} className="flex-1 h-7 rounded-lg bg-indigo-600 text-white text-[10px] font-black uppercase tracking-widest hover:bg-indigo-700 disabled:opacity-50 transition-all">
          {saving ? 'Saving…' : 'Save Rule'}
        </button>
        <button onClick={() => setOpen(false)} className="flex-1 h-7 rounded-lg border border-slate-200 bg-white text-slate-500 text-[10px] font-black uppercase tracking-widest hover:bg-slate-50 transition-all">
          Cancel
        </button>
      </div>
    </div>
  )
}

// ─── Options editor ───────────────────────────────────────────────────────────

function OptionsEditor({
  question,
  onChange,
}: {
  question: any
  onChange: (opts: any[]) => void
}) {
  const [newLabel, setNewLabel] = useState('')
  const opts: Array<{ label: string; value: string }> = question?.options_json ?? []

  const addOpt = () => {
    const label = newLabel.trim()
    if (!label) return
    const value = label.toLowerCase().replace(/[^a-z0-9]+/g, '_')
    onChange([...opts, { label, value }])
    setNewLabel('')
  }

  const removeOpt = (i: number) => {
    const next = opts.filter((_, idx) => idx !== i)
    onChange(next)
  }

  const updateLabel = (i: number, label: string) => {
    const value = label.toLowerCase().replace(/[^a-z0-9]+/g, '_')
    const next = opts.map((o, idx) => idx === i ? { label, value } : o)
    onChange(next)
  }

  return (
    <div className="space-y-2">
      {opts.map((opt, i) => (
        <div key={i} className="flex items-center gap-2">
          <div className="h-4 w-4 rounded-full border-2 border-slate-300 shrink-0" />
          <Input
            size="small"
            value={opt.label}
            onChange={e => updateLabel(i, e.target.value)}
            onBlur={() => onChange(opts)}
            className="flex-1 text-sm rounded-lg"
          />
          <button onClick={() => removeOpt(i)} className="text-slate-300 hover:text-red-500 transition-all shrink-0">
            <X size={14} />
          </button>
        </div>
      ))}
      <div className="flex items-center gap-2 mt-1">
        <div className="h-4 w-4 rounded-full border-2 border-dashed border-slate-200 shrink-0" />
        <Input
          size="small"
          value={newLabel}
          onChange={e => setNewLabel(e.target.value)}
          onPressEnter={addOpt}
          placeholder="Add option..."
          className="flex-1 text-sm rounded-lg text-slate-400"
        />
        <button onClick={addOpt} className="text-indigo-500 hover:text-indigo-700 transition-all shrink-0">
          <Plus size={14} />
        </button>
      </div>
    </div>
  )
}

// ─── Question card ────────────────────────────────────────────────────────────

function QuestionCard({
  question,
  index,
  sectionIndex,
  isSelected,
  sections,
  formId,
  onSelect,
  onUpdate,
  onDelete,
  onDuplicate,
  onRefresh,
}: {
  question: any
  index: number
  sectionIndex: number
  isSelected: boolean
  sections: any[]
  formId: string
  onSelect: () => void
  onUpdate: (data: Partial<any>) => void
  onDelete: () => void
  onDuplicate: () => void
  onRefresh: () => void
}) {
  const tc = getTypeConfig(question.question_type)
  const TypeIcon = tc.icon
  const rules: any[] = question.rules ?? []
  const opts: Array<{ label: string; value: string }> = question.options_json ?? []
  const showOpts = HAS_OPTIONS.includes(question.question_type)
  const [editing, setEditing] = useState(false)
  const [text, setText] = useState(question.question_text)
  const textRef = useRef<any>(null)

  void textRef

  const handleTextBlur = () => {
    setEditing(false)
    if (text.trim() && text !== question.question_text) {
      onUpdate({ question_text: text })
    }
  }

  const handleDeleteRule = async (ruleId: string) => {
    try {
      await prequalificationApi.deleteRule(ruleId)
      onRefresh()
    } catch {
      message.error('Failed to delete rule')
    }
  }

  const handleOptionsChange = (newOpts: any[]) => {
    onUpdate({ options_json: newOpts })
  }

  return (
    <div
      className={cn(
        'group relative rounded-2xl bg-white border-2 transition-all duration-150',
        isSelected
          ? 'border-indigo-400 shadow-md shadow-indigo-100'
          : 'border-slate-200 hover:border-slate-300 hover:shadow-sm',
      )}
      onClick={() => { if (!isSelected) onSelect() }}
    >
      {isSelected && (
        <div className="absolute left-0 top-4 bottom-4 w-1 bg-indigo-500 rounded-r-full" />
      )}

      <div className="flex items-start gap-3 px-5 pt-5 pb-3">
        <div className="flex items-center gap-2 shrink-0">
          <GripVertical size={14} className="text-slate-200 cursor-grab" />
          <span className="h-6 w-6 rounded-full bg-indigo-100 text-indigo-700 text-[10px] font-black flex items-center justify-center">
            {sectionIndex + 1}.{index + 1}
          </span>
        </div>

        <div className="flex-1 min-w-0">
          {editing ? (
            <Input.TextArea
              autoFocus
              autoSize={{ minRows: 1, maxRows: 4 }}
              value={text}
              onChange={e => setText(e.target.value)}
              onBlur={handleTextBlur}
              onKeyDown={e => { if (e.key === 'Escape') { setEditing(false); setText(question.question_text) } }}
              className="text-sm font-medium text-slate-900 rounded-xl border-indigo-300 focus:border-indigo-500 p-0 resize-none"
              bordered={false}
              style={{ fontSize: 14, fontWeight: 500, padding: 0 }}
            />
          ) : (
            <p
              className={cn(
                'text-sm font-medium text-slate-900 leading-snug cursor-text',
                !question.question_text && 'text-slate-400 italic',
              )}
              onClick={e => { e.stopPropagation(); onSelect(); setEditing(true) }}
            >
              {question.question_text || 'Click to add question text...'}
              {question.required && <span className="ml-1 text-red-500">*</span>}
            </p>
          )}
          {question.help_text && (
            <p className="mt-0.5 text-xs text-slate-400 italic">{question.help_text}</p>
          )}
        </div>

        <div className="shrink-0 flex items-center gap-1.5 bg-slate-100 rounded-lg px-2.5 py-1.5 border border-slate-200">
          <TypeIcon size={12} className="text-slate-500" />
          <span className="text-[10px] font-bold text-slate-600">{tc.label}</span>
        </div>

        <div className="shrink-0 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Tooltip title="Duplicate">
            <button onClick={e => { e.stopPropagation(); onDuplicate() }} className="h-7 w-7 flex items-center justify-center rounded-lg border border-slate-200 text-slate-400 hover:text-indigo-600 hover:border-indigo-200 hover:bg-indigo-50 transition-all">
              <Copy size={12} />
            </button>
          </Tooltip>
          <Tooltip title="Delete">
            <button onClick={e => { e.stopPropagation(); onDelete() }} className="h-7 w-7 flex items-center justify-center rounded-lg border border-slate-200 text-slate-400 hover:text-red-500 hover:border-red-200 hover:bg-red-50 transition-all">
              <Trash2 size={12} />
            </button>
          </Tooltip>
        </div>
      </div>

      {showOpts && isSelected && (
        <div className="px-5 pb-3 ml-11">
          <OptionsEditor question={question} onChange={handleOptionsChange} />
        </div>
      )}
      {showOpts && !isSelected && opts.length > 0 && (
        <div className="px-5 pb-3 ml-11 space-y-1">
          {opts.slice(0, 4).map((opt, i) => (
            <div key={i} className="flex items-center gap-2 text-sm text-slate-500">
              <div className="h-3.5 w-3.5 rounded-full border-2 border-slate-300 shrink-0" />
              {opt.label}
            </div>
          ))}
          {opts.length > 4 && <p className="text-xs text-slate-400 ml-5">+{opts.length - 4} more options</p>}
        </div>
      )}

      {rules.length > 0 && (
        <div className="px-5 pb-3 ml-11 space-y-1.5">
          {rules.map(r => (
            <RuleChip key={r.id} rule={r} onDelete={() => handleDeleteRule(r.id)} />
          ))}
        </div>
      )}

      {isSelected && (
        <div className="px-5 pb-4 ml-11">
          <AddRuleInline question={question} sections={sections} formId={formId} onAdded={onRefresh} />
        </div>
      )}

      <div className="flex items-center gap-2 px-5 py-2.5 border-t border-slate-100 ml-8">
        {question.is_knockout && (
          <span className="flex items-center gap-1 text-[9px] font-black uppercase tracking-widest text-red-600 bg-red-50 px-2 py-0.5 rounded-full border border-red-200">
            <Shield size={9} /> Knockout
          </span>
        )}
        {question.score_weight > 0 && (
          <span className="flex items-center gap-1 text-[9px] font-black uppercase tracking-widest text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
            <Star size={9} /> {question.score_weight} pts
          </span>
        )}
        {rules.length > 0 && (
          <span className="flex items-center gap-1 text-[9px] font-black uppercase tracking-widest text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full border border-indigo-200">
            <GitBranch size={9} /> {rules.length} {rules.length === 1 ? 'rule' : 'rules'}
          </span>
        )}
        <div className="ml-auto flex items-center gap-2">
          <span className={cn('text-[9px] font-black uppercase tracking-widest', question.required ? 'text-red-500' : 'text-slate-300')}>
            {question.required ? 'Required' : 'Optional'}
          </span>
          <Switch
            size="small"
            checked={question.required}
            onChange={v => { onUpdate({ required: v }) }}
            onClick={(_, e) => e.stopPropagation()}
          />
        </div>
      </div>
    </div>
  )
}

// ─── Right config panel ───────────────────────────────────────────────────────

function RightConfigPanel({
  question,
  sections,
  onUpdate,
  onRefresh,
}: {
  question: any | null
  sections: any[]
  onUpdate: (data: Partial<any>) => void
  onRefresh: () => void
}) {
  void sections
  void onRefresh

  // Local state so slider drags and keystrokes don't fire a PATCH on every event.
  // Only synced from server data when the selected question itself changes.
  const [localHelpText, setLocalHelpText] = useState(question?.help_text ?? '')
  const [localScore, setLocalScore] = useState<number>(question?.score_weight ?? 0)

  useEffect(() => {
    setLocalHelpText(question?.help_text ?? '')
    setLocalScore(question?.score_weight ?? 0)
  }, [question?.id]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!question) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center px-5 gap-3">
        <div className="h-12 w-12 rounded-2xl bg-slate-100 flex items-center justify-center">
          <Settings size={22} className="text-slate-300" />
        </div>
        <p className="text-[11px] font-black uppercase tracking-widest text-slate-400">No question selected</p>
        <p className="text-xs text-slate-300 text-center">Click a question card to configure it</p>
      </div>
    )
  }

  const tc = getTypeConfig(question.question_type)
  const TypeIcon = tc.icon

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="flex-none px-4 py-3 border-b border-slate-100 bg-slate-50/50">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-indigo-100 flex items-center justify-center">
            <TypeIcon size={13} className="text-indigo-600" />
          </div>
          <div className="min-w-0">
            <p className="text-[10px] font-black uppercase tracking-widest text-slate-700 truncate">{tc.label}</p>
            <p className="text-[9px] text-slate-400 truncate">{question.question_text.substring(0, 40)}{question.question_text.length > 40 ? '…' : ''}</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        <Tabs
          defaultActiveKey="settings"
          size="small"
          tabBarStyle={{ paddingLeft: 12, paddingRight: 12, marginBottom: 0 }}
          items={[
            {
              key: 'settings',
              label: <span className="text-[10px] font-black uppercase">Settings</span>,
              children: (
                <div className="px-4 py-3 space-y-4">
                  <div>
                    <label className="block text-[9px] font-black uppercase tracking-widest text-slate-400 mb-1.5">Question Type</label>
                    <Select
                      value={question.question_type}
                      onChange={(v: string) => onUpdate({ question_type: v, options_json: getDefaultOptions(v) })}
                      className="w-full"
                      options={Q_TYPES.map(t => ({
                        value: t.value,
                        label: (
                          <span className="flex items-center gap-2">
                            <t.icon size={13} className="text-slate-500" />
                            {t.label}
                          </span>
                        ),
                      }))}
                    />
                  </div>

                  <div className="flex items-center justify-between py-2 border-t border-slate-100">
                    <div>
                      <p className="text-xs font-bold text-slate-700">Required</p>
                      <p className="text-[10px] text-slate-400">Candidate must answer</p>
                    </div>
                    <Switch size="small" checked={question.required} onChange={(v: boolean) => onUpdate({ required: v })} />
                  </div>

                  <div>
                    <label className="block text-[9px] font-black uppercase tracking-widest text-slate-400 mb-1.5">Help Text</label>
                    <Input.TextArea
                      rows={2}
                      value={localHelpText}
                      onChange={e => setLocalHelpText(e.target.value)}
                      onBlur={() => {
                        if (localHelpText !== (question.help_text ?? '')) {
                          onUpdate({ help_text: localHelpText })
                        }
                      }}
                      placeholder="Optional hint shown to candidate..."
                      className="rounded-xl text-xs"
                    />
                  </div>
                </div>
              ),
            },
            {
              key: 'scoring',
              label: <span className="text-[10px] font-black uppercase">Scoring</span>,
              children: (
                <div className="px-4 py-3 space-y-4">
                  <div className="rounded-xl border border-red-200 bg-red-50/50 p-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Shield size={14} className="text-red-500" />
                        <div>
                          <p className="text-xs font-black text-red-800">Knockout Question</p>
                          <p className="text-[10px] text-red-600 mt-0.5">Rules on this question can auto-reject</p>
                        </div>
                      </div>
                      <Switch
                        size="small"
                        checked={question.is_knockout}
                        onChange={(v: boolean) => onUpdate({ is_knockout: v })}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-[9px] font-black uppercase tracking-widest text-slate-400 flex items-center gap-1">
                        <Star size={10} className="text-amber-500" /> Score Weight
                      </label>
                      <span className={cn('text-sm font-black', localScore > 0 ? 'text-amber-600' : 'text-slate-300')}>
                        {localScore} pts
                      </span>
                    </div>
                    <Slider
                      min={0}
                      max={25}
                      step={1}
                      value={localScore}
                      onChange={(v: number) => setLocalScore(v)}
                      onChangeComplete={(v: number) => onUpdate({ score_weight: v })}
                      marks={{ 0: '0', 5: '5', 10: '10', 15: '15', 20: '20', 25: '25' }}
                    />
                    <p className="text-[10px] text-slate-400 mt-2">Points added to candidate's total score when answered correctly. Use 0 for unscored questions.</p>
                  </div>
                </div>
              ),
            },
            {
              key: 'logic',
              label: (
                <span className="text-[10px] font-black uppercase flex items-center gap-1">
                  Logic
                  {(question.rules?.length ?? 0) > 0 && (
                    <span className="h-4 min-w-4 px-1 rounded-full bg-indigo-500 text-white text-[8px] font-black flex items-center justify-center">
                      {question.rules.length}
                    </span>
                  )}
                </span>
              ),
              children: (
                <div className="px-4 py-3 space-y-3">
                  <p className="text-[10px] text-slate-400">
                    Rules are shown on the question card below. Click &ldquo;Add Logic Rule&rdquo; on the card to add branching.
                  </p>
                  {(question.rules ?? []).length === 0 ? (
                    <div className="py-8 text-center rounded-xl border border-dashed border-slate-200">
                      <GitBranch size={24} className="text-slate-200 mx-auto mb-2" />
                      <p className="text-[10px] font-black uppercase text-slate-300">No rules yet</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {question.rules.map((r: any) => {
                        const ac = getActionConfig(r.action_type)
                        return (
                          <div key={r.id} className={cn('rounded-xl border p-3 text-[11px]', ac.bg)}>
                            <p className="font-semibold text-slate-700">
                              IF {CONDITIONS.find(c => c.value === r.condition_type)?.label ?? r.condition_type}
                              {r.compare_value && <span className="font-mono text-slate-900"> &ldquo;{r.compare_value}&rdquo;</span>}
                            </p>
                            <p className={cn('font-black uppercase text-[9px] tracking-widest mt-1', ac.color)}>
                              → {ac.label}
                              {r.outcome_code && `: ${getOutcomeConfig(r.outcome_code).label}`}
                            </p>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              ),
            },
          ]}
        />
      </div>
    </div>
  )
}

// ─── Outcomes panel ───────────────────────────────────────────────────────────

function OutcomesPanel({ formDetail, onUpdateForm }: { formDetail: any; onUpdateForm: (meta: object) => void }) {
  const meta = formDetail?.metadata ?? {}
  const activeOutcomes: string[] = meta.active_outcomes ?? OUTCOMES.map(o => o.code)
  const scoreThreshold: { pass: number; review: number } = meta.score_threshold ?? { pass: 70, review: 40 }

  const toggleOutcome = (code: string) => {
    const next = activeOutcomes.includes(code)
      ? activeOutcomes.filter((c: string) => c !== code)
      : [...activeOutcomes, code]
    onUpdateForm({ ...meta, active_outcomes: next })
  }

  return (
    <div className="p-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-[9px] font-black uppercase tracking-widest text-slate-400 mb-3">Active Outcomes</p>
          <div className="grid grid-cols-2 gap-2">
            {OUTCOMES.map(o => {
              const Icon = o.icon
              const active = activeOutcomes.includes(o.code)
              return (
                <button
                  key={o.code}
                  onClick={() => toggleOutcome(o.code)}
                  className={cn(
                    'flex items-center gap-2 rounded-xl border px-3 py-2.5 text-left transition-all',
                    active
                      ? `${o.bg} border-current ${o.color}`
                      : 'bg-white border-slate-200 text-slate-400 hover:border-slate-300',
                  )}
                >
                  <Icon size={13} className={active ? o.color : 'text-slate-300'} />
                  <span className={cn('text-[10px] font-black uppercase tracking-wider', active ? o.color : 'text-slate-400')}>
                    {o.label}
                  </span>
                </button>
              )
            })}
          </div>
        </div>

        <div>
          <p className="text-[9px] font-black uppercase tracking-widest text-slate-400 mb-3">Score Thresholds</p>
          <div className="space-y-4 bg-white rounded-xl border border-slate-200 p-4">
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-[10px] font-bold text-green-700 flex items-center gap-1"><CheckCircle size={10} /> Pass threshold</label>
                <span className="text-sm font-black text-green-700">{scoreThreshold.pass}%</span>
              </div>
              <Slider
                min={0} max={100} step={5}
                value={scoreThreshold.pass}
                onChange={(v: number) => onUpdateForm({ ...meta, score_threshold: { ...scoreThreshold, pass: v } })}
              />
            </div>
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-[10px] font-bold text-amber-700 flex items-center gap-1"><AlertTriangle size={10} /> Review threshold</label>
                <span className="text-sm font-black text-amber-700">{scoreThreshold.review}%</span>
              </div>
              <Slider
                min={0} max={100} step={5}
                value={scoreThreshold.review}
                onChange={(v: number) => onUpdateForm({ ...meta, score_threshold: { ...scoreThreshold, review: v } })}
              />
            </div>
            <p className="text-[10px] text-slate-400">Score ≥ {scoreThreshold.pass}% → Pass · Score {scoreThreshold.review}–{scoreThreshold.pass}% → Review · Below → Reject</p>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Presets modal ────────────────────────────────────────────────────────────

function PresetsModal({
  open,
  onClose,
  onAdd,
}: {
  open: boolean
  onClose: () => void
  onAdd: (preset: PresetQuestion) => void
}) {
  const [activeCategory, setActiveCategory] = useState('Eligibility')
  const categories = Object.keys(PRESETS)

  return (
    <Modal
      open={open}
      onCancel={onClose}
      footer={null}
      width={800}
      title={
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-indigo-600 flex items-center justify-center">
            <Layers size={15} className="text-white" />
          </div>
          <div>
            <p className="font-black text-slate-900 text-sm uppercase tracking-tight">Question Library</p>
            <p className="text-[10px] text-slate-400 font-medium">Click any question to add it to your form</p>
          </div>
        </div>
      }
      destroyOnHidden
    >
      <div className="flex gap-4 mt-3" style={{ minHeight: 360 }}>
        <div className="w-40 shrink-0 space-y-1">
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={cn(
                'w-full text-left px-3 py-2 rounded-xl text-[11px] font-black uppercase tracking-widest transition-all',
                activeCategory === cat
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-500 hover:bg-slate-50',
              )}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="flex-1 space-y-2 overflow-y-auto" style={{ maxHeight: 400 }}>
          {(PRESETS[activeCategory] ?? []).map((preset, i) => {
            const tc = getTypeConfig(preset.type)
            return (
              <button
                key={i}
                onClick={() => { onAdd(preset); onClose() }}
                className="w-full text-left flex items-start gap-3 p-3 rounded-xl border border-slate-200 hover:border-indigo-300 hover:bg-indigo-50/30 transition-all group"
              >
                <div className="h-7 w-7 rounded-lg bg-slate-100 flex items-center justify-center shrink-0 group-hover:bg-indigo-100 transition-all">
                  <tc.icon size={13} className="text-slate-500 group-hover:text-indigo-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-800 group-hover:text-indigo-800 leading-snug">{preset.text}</p>
                  <div className="flex items-center gap-2 mt-1 flex-wrap">
                    <span className="text-[9px] font-black uppercase tracking-widest text-slate-400 bg-slate-100 px-2 py-0.5 rounded">{tc.label}</span>
                    {preset.is_knockout && <span className="text-[9px] font-black uppercase tracking-widest text-red-600 bg-red-50 px-2 py-0.5 rounded">Knockout</span>}
                    {(preset.score_weight ?? 0) > 0 && <span className="text-[9px] font-black uppercase tracking-widest text-amber-600 bg-amber-50 px-2 py-0.5 rounded">{preset.score_weight} pts</span>}
                    {preset.help && <span className="text-[10px] text-slate-400 italic">{preset.help}</span>}
                  </div>
                </div>
                <ChevronRight size={14} className="text-slate-300 group-hover:text-indigo-400 shrink-0 mt-1 transition-all" />
              </button>
            )
          })}
        </div>
      </div>
    </Modal>
  )
}

// ─── Preview modal ────────────────────────────────────────────────────────────

function PreviewModal({ open, onClose, formDetail }: { open: boolean; onClose: () => void; formDetail: any }) {
  const sections = formDetail?.sections ?? []

  return (
    <Modal
      open={open}
      onCancel={onClose}
      footer={null}
      width={620}
      title={
        <div className="flex items-center gap-3">
          <Eye size={16} className="text-indigo-600" />
          <span className="font-black text-slate-900 uppercase tracking-tight text-sm">Form Preview — Candidate View</span>
        </div>
      }
      destroyOnHidden
    >
      <div className="mt-2 space-y-4 max-h-[70vh] overflow-y-auto pr-1">
        <div className="rounded-2xl bg-gradient-to-br from-indigo-600 to-indigo-700 p-6 text-white">
          <h2 className="text-lg font-black">{formDetail?.name}</h2>
          {formDetail?.description && <p className="text-indigo-200 text-sm mt-1">{formDetail.description}</p>}
        </div>

        {sections.map((section: any, si: number) => (
          <div key={section.id}>
            <div className="bg-slate-50 rounded-xl px-4 py-3 border border-slate-200 mb-3">
              <p className="text-sm font-black text-slate-800">{section.title}</p>
              {section.description && <p className="text-xs text-slate-500 mt-0.5">{section.description}</p>}
            </div>
            <div className="space-y-3 pl-2">
              {(section.questions ?? []).map((q: any, qi: number) => {
                const tc = getTypeConfig(q.question_type)
                const opts = q.options_json ?? []
                void tc
                return (
                  <div key={q.id} className="bg-white rounded-xl border border-slate-200 p-4">
                    <p className="text-sm font-medium text-slate-900">
                      {si + 1}.{qi + 1}. {q.question_text}
                      {q.required && <span className="text-red-500 ml-1">*</span>}
                    </p>
                    {q.help_text && <p className="text-xs text-slate-400 italic mt-0.5">{q.help_text}</p>}
                    <div className="mt-3">
                      {q.question_type === 'yes_no' && (
                        <div className="flex gap-3">
                          {[{ l: 'Yes' }, { l: 'No' }].map(o => (
                            <label key={o.l} className="flex items-center gap-2 cursor-pointer">
                              <input type="radio" name={q.id} className="text-indigo-600" readOnly />
                              <span className="text-sm text-slate-700">{o.l}</span>
                            </label>
                          ))}
                        </div>
                      )}
                      {['single_select', 'dropdown', 'multiple_choice'].includes(q.question_type) && opts.length > 0 && (
                        <div className="space-y-1.5">
                          {opts.map((o: any, oi: number) => (
                            <label key={oi} className="flex items-center gap-2 cursor-pointer">
                              <input type="radio" name={q.id} className="text-indigo-600" readOnly />
                              <span className="text-sm text-slate-700">{o.label ?? o}</span>
                            </label>
                          ))}
                        </div>
                      )}
                      {['multi_select'].includes(q.question_type) && opts.length > 0 && (
                        <div className="space-y-1.5">
                          {opts.map((o: any, oi: number) => (
                            <label key={oi} className="flex items-center gap-2 cursor-pointer">
                              <input type="checkbox" className="text-indigo-600 rounded" readOnly />
                              <span className="text-sm text-slate-700">{o.label ?? o}</span>
                            </label>
                          ))}
                        </div>
                      )}
                      {['short_text', 'text'].includes(q.question_type) && (
                        <input disabled placeholder="Your answer..." className="w-full border-b border-slate-300 py-1 text-sm text-slate-500 bg-transparent outline-none" />
                      )}
                      {q.question_type === 'long_text' && (
                        <textarea disabled rows={3} placeholder="Your answer..." className="w-full border border-slate-200 rounded-xl p-2 text-sm text-slate-500 bg-transparent outline-none resize-none" />
                      )}
                      {q.question_type === 'number' && (
                        <input type="number" disabled placeholder="0" className="border-b border-slate-300 py-1 text-sm text-slate-500 bg-transparent outline-none w-32" />
                      )}
                      {q.question_type === 'date' && (
                        <input type="date" disabled className="border border-slate-200 rounded-xl px-3 py-1.5 text-sm text-slate-500 bg-transparent outline-none" />
                      )}
                      {q.question_type === 'file_upload' && (
                        <div className="border-2 border-dashed border-slate-200 rounded-xl p-4 text-center text-sm text-slate-400">
                          <Upload size={18} className="mx-auto mb-1 text-slate-300" /> Click to upload file
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        ))}

        {sections.length === 0 && (
          <div className="py-10 text-center text-slate-400">
            <FileText size={28} className="mx-auto mb-2 text-slate-200" />
            <p className="text-sm font-bold">No questions yet</p>
          </div>
        )}

        <div className="flex justify-end pt-2 border-t border-slate-100">
          <button className="px-6 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-black uppercase tracking-widest opacity-60 cursor-not-allowed">
            Submit Application
          </button>
        </div>
      </div>
    </Modal>
  )
}

// ─── Main builder ─────────────────────────────────────────────────────────────

export default function PrequalificationBuilder() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [activeSectionId, setActiveSectionId] = useState<string | null>(null)
  const [selectedQuestionId, setSelectedQuestionId] = useState<string | null>(null)
  const [outcomesOpen, setOutcomesOpen] = useState(false)
  const [presetsOpen, setPresetsOpen] = useState(false)
  const [previewOpen, setPreviewOpen] = useState(false)
  const [addingSection, setAddingSection] = useState(false)
  const [newSectionTitle, setNewSectionTitle] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [addTypePickerOpen, setAddTypePickerOpen] = useState(false)

  const { data, isLoading } = useApiQuery(
    ['prequal-builder', id],
    () => prequalificationApi.getForm(id!),
    { enabled: !!id, staleTime: 0 }
  )

  const formDetail = (data as any)?.form
  const sections: any[] = formDetail?.sections ?? []
  const activeSec = sections.find((s: any) => s.id === activeSectionId) ?? sections[0] ?? null
  const questions: any[] = activeSec?.questions ?? []
  const selectedQ = questions.find((q: any) => q.id === selectedQuestionId) ?? null

  const totalQ = sections.reduce((a: number, s: any) => a + (s.questions?.length ?? 0), 0)
  const totalRules = sections.reduce((a: number, s: any) =>
    a + (s.questions ?? []).reduce((b: number, q: any) => b + (q.rules?.length ?? 0), 0), 0)
  const totalScore = sections.reduce((a: number, s: any) =>
    a + (s.questions ?? []).reduce((b: number, q: any) => b + (q.score_weight ?? 0), 0), 0)

  const refresh = useCallback(() => {
    queryClient.refetchQueries({ queryKey: ['prequal-builder', id] })
  }, [queryClient, id])

  const handleSave = async () => {
    if (!formDetail) return
    setIsSaving(true)
    try {
      await prequalificationApi.updateForm(id!, {
        name: formDetail.name,
        description: formDetail.description,
        metadata: formDetail.metadata ?? {},
      })
      message.success('Form saved')
    } catch {
      message.error('Save failed')
    } finally {
      setIsSaving(false)
    }
  }

  const handlePublishToggle = async () => {
    if (!formDetail) return
    try {
      await prequalificationApi.updateForm(id!, { is_active: !formDetail.is_active })
      message.success(formDetail.is_active ? 'Form unpublished' : 'Form published')
      refresh()
    } catch {
      message.error('Failed to update status')
    }
  }

  const handleUpdateForm = async (metadata: object) => {
    if (!formDetail) return
    try {
      await prequalificationApi.updateForm(id!, { metadata })
      refresh()
    } catch {
      message.error('Failed to update')
    }
  }

  const handleAddSection = async () => {
    if (!newSectionTitle.trim()) return
    try {
      const nextOrder = sections.length
      await prequalificationApi.createSection({ form: id!, title: newSectionTitle.trim(), order: nextOrder })
      message.success('Section added')
      setNewSectionTitle('')
      setAddingSection(false)
      refresh()
    } catch {
      message.error('Failed to add section')
    }
  }

  const handleDeleteSection = async (sectionId: string) => {
    Modal.confirm({
      title: 'Delete Section?',
      content: 'All questions in this section will also be deleted.',
      okText: 'Delete',
      okButtonProps: { danger: true },
      onOk: async () => {
        try {
          await prequalificationApi.deleteSection(sectionId)
          if (activeSectionId === sectionId) setActiveSectionId(null)
          refresh()
          message.success('Section deleted')
        } catch {
          message.error('Failed to delete section')
        }
      },
    })
  }

  const handleAddQuestion = async (type: string) => {
    if (!activeSec) { message.warning('Select a section first'); return }
    setAddTypePickerOpen(false)
    try {
      const order = questions.length
      const defaultOpts = getDefaultOptions(type)
      const resp = await prequalificationApi.createQuestion({
        section: activeSec.id,
        question_text: '',
        question_type: type,
        required: true,
        order,
        options_json: defaultOpts,
        score_weight: 0,
        is_knockout: false,
      })
      refresh()
      const newQ = (resp as any)?.data?.question ?? (resp as any)?.question
      if (newQ?.id) {
        setTimeout(() => setSelectedQuestionId(newQ.id), 300)
      }
    } catch {
      message.error('Failed to add question')
    }
  }

  const handleAddPreset = async (preset: PresetQuestion) => {
    if (!activeSec) { message.warning('Select a section first'); return }
    try {
      const order = questions.length
      await prequalificationApi.createQuestion({
        section: activeSec.id,
        question_text: preset.text,
        question_type: preset.type,
        required: true,
        order,
        options_json: preset.options ?? getDefaultOptions(preset.type),
        help_text: preset.help ?? '',
        score_weight: preset.score_weight ?? 0,
        is_knockout: preset.is_knockout ?? false,
      })
      message.success('Question added from library')
      refresh()
    } catch {
      message.error('Failed to add question')
    }
  }

  const handleUpdateQuestion = async (questionId: string, data: Partial<any>) => {
    try {
      await prequalificationApi.updateQuestion(questionId, data)
      refresh()
    } catch {
      message.error('Failed to update question')
    }
  }

  const handleDeleteQuestion = async (questionId: string) => {
    try {
      await prequalificationApi.deleteQuestion(questionId)
      if (selectedQuestionId === questionId) setSelectedQuestionId(null)
      refresh()
    } catch {
      message.error('Failed to delete question')
    }
  }

  const handleDuplicateQuestion = async (question: any) => {
    if (!activeSec) return
    try {
      await prequalificationApi.createQuestion({
        section: activeSec.id,
        question_text: question.question_text + ' (copy)',
        question_type: question.question_type,
        required: question.required,
        order: question.order + 1,
        options_json: question.options_json,
        help_text: question.help_text,
        score_weight: question.score_weight,
        is_knockout: question.is_knockout,
      })
      refresh()
    } catch {
      message.error('Failed to duplicate')
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#F8FAFC]">
        <Spin size="large" />
      </div>
    )
  }

  if (!formDetail) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-[#F8FAFC] gap-3">
        <FileText size={40} className="text-slate-300" />
        <p className="text-slate-400 font-bold">Form not found</p>
        <button onClick={() => navigate('/interviews?s=prequalification')} className="text-indigo-600 text-sm font-bold hover:underline">
          Back to forms list
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen bg-[#F8FAFC] overflow-hidden -m-4">

      {/* TOP HEADER */}
      <div className="h-14 flex-none flex items-center justify-between border-b border-slate-200 bg-white px-4 shadow-sm z-30">
        <div className="flex items-center gap-3 min-w-0">
          <button
            onClick={() => navigate('/interviews?s=prequalification')}
            className="h-8 w-8 flex items-center justify-center rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50 hover:text-slate-800 transition-all shrink-0"
          >
            <ArrowLeft size={15} />
          </button>
          <div className="h-8 w-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white shrink-0">
            <FileText size={15} />
          </div>
          <div className="min-w-0">
            <h1 className="text-sm font-black text-slate-900 leading-none truncate">{formDetail.name}</h1>
            <p className="text-[10px] text-slate-400 font-medium mt-0.5 uppercase tracking-widest">
              {sections.length}S · {totalQ}Q · {totalRules}R · {totalScore}pts max
            </p>
          </div>
          <Tag
            color={formDetail.is_active ? 'success' : 'default'}
            className="m-0 border-none uppercase font-black text-[8px] tracking-widest px-2 py-0.5 rounded-full shrink-0"
          >
            {formDetail.is_active ? 'Published' : 'Draft'}
          </Tag>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button onClick={() => setPreviewOpen(true)} className="flex items-center gap-1.5 h-8 px-3 rounded-lg border border-slate-200 text-slate-600 text-[10px] font-black uppercase tracking-widest hover:bg-slate-50 transition-all">
            <Eye size={13} /> Preview
          </button>
          <button
            onClick={handlePublishToggle}
            className={cn(
              'flex items-center gap-1.5 h-8 px-3 rounded-lg border text-[10px] font-black uppercase tracking-widest transition-all',
              formDetail.is_active
                ? 'border-slate-200 text-slate-600 hover:bg-slate-50'
                : 'border-green-200 bg-green-50 text-green-700 hover:bg-green-100',
            )}
          >
            <Send size={13} />
            {formDetail.is_active ? 'Unpublish' : 'Publish'}
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-1.5 h-8 px-4 rounded-lg bg-indigo-600 text-white text-[10px] font-black uppercase tracking-widest hover:bg-indigo-700 shadow-sm active:scale-95 disabled:opacity-60 transition-all"
          >
            <Save size={13} /> {isSaving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>

      {/* MAIN */}
      <div className="flex flex-1 overflow-hidden">

        {/* LEFT SIDEBAR */}
        <div className="w-56 flex-none border-r border-slate-200 bg-white flex flex-col overflow-hidden">
          <div className="p-3 border-b border-slate-100">
            <p className="text-[9px] font-black uppercase tracking-widest text-slate-400 px-1 mb-2 flex items-center gap-1.5">
              <Layers size={10} /> Sections
            </p>
            {sections.length === 0 ? (
              <div className="py-6 text-center">
                <p className="text-[10px] font-bold text-slate-300 uppercase tracking-widest">No sections</p>
              </div>
            ) : (
              <div className="space-y-0.5">
                {sections.map((sec: any) => {
                  const isActive = activeSec?.id === sec.id
                  return (
                    <div
                      key={sec.id}
                      className={cn(
                        'group flex items-center gap-2 px-2 py-2 rounded-xl cursor-pointer transition-all',
                        isActive ? 'bg-indigo-600 text-white' : 'hover:bg-slate-50 text-slate-600',
                      )}
                      onClick={() => { setActiveSectionId(sec.id); setSelectedQuestionId(null) }}
                    >
                      <GripVertical size={11} className={cn('shrink-0', isActive ? 'text-indigo-300' : 'text-slate-200')} />
                      <div className="flex-1 min-w-0">
                        <p className={cn('text-[11px] font-bold truncate', isActive ? 'text-white' : 'text-slate-800')}>{sec.title}</p>
                        <p className={cn('text-[9px]', isActive ? 'text-indigo-200' : 'text-slate-400')}>{(sec.questions ?? []).length}Q</p>
                      </div>
                      <button
                        onClick={e => { e.stopPropagation(); handleDeleteSection(sec.id) }}
                        className={cn('opacity-0 group-hover:opacity-100 shrink-0 transition-all', isActive ? 'text-indigo-200 hover:text-white' : 'text-slate-300 hover:text-red-500')}
                      >
                        <Trash2 size={11} />
                      </button>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          <div className="p-3">
            {addingSection ? (
              <div className="space-y-2">
                <Input
                  autoFocus
                  size="small"
                  value={newSectionTitle}
                  onChange={e => setNewSectionTitle(e.target.value)}
                  onPressEnter={handleAddSection}
                  placeholder="Section name..."
                  className="rounded-lg text-xs"
                />
                <div className="flex gap-2">
                  <button onClick={handleAddSection} disabled={!newSectionTitle.trim()} className="flex-1 h-7 rounded-lg bg-indigo-600 text-white text-[10px] font-black disabled:opacity-50 hover:bg-indigo-700 transition-all">Add</button>
                  <button onClick={() => { setAddingSection(false); setNewSectionTitle('') }} className="flex-1 h-7 rounded-lg border border-slate-200 text-slate-500 text-[10px] font-black hover:bg-slate-50 transition-all">Cancel</button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setAddingSection(true)}
                className="w-full flex items-center justify-center gap-1.5 py-2 rounded-xl border border-dashed border-slate-300 text-[10px] font-black uppercase tracking-widest text-slate-400 hover:border-indigo-300 hover:text-indigo-600 transition-all"
              >
                <Plus size={13} /> Add Section
              </button>
            )}
          </div>

          <div className="mt-auto p-3 border-t border-slate-100 space-y-1">
            {[
              { label: 'Total Score', value: `${totalScore} pts`, color: 'text-amber-600' },
              { label: 'Rules', value: totalRules, color: 'text-indigo-600' },
            ].map(s => (
              <div key={s.label} className="flex items-center justify-between text-[10px]">
                <span className="text-slate-400 font-bold uppercase tracking-widest">{s.label}</span>
                <span className={cn('font-black', s.color)}>{s.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* CENTER */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          {activeSec && (
            <div className="flex-none flex items-center justify-between px-6 py-3 bg-white border-b border-slate-200">
              <div>
                <h2 className="text-sm font-black text-slate-900">{activeSec.title}</h2>
                {activeSec.description && <p className="text-xs text-slate-400 mt-0.5">{activeSec.description}</p>}
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPresetsOpen(true)}
                  className="flex items-center gap-1.5 h-8 px-3 rounded-lg border border-slate-200 text-slate-600 text-[10px] font-black uppercase tracking-widest hover:bg-slate-50 hover:border-indigo-300 hover:text-indigo-600 transition-all"
                >
                  <Layers size={13} /> From Library
                </button>
                <div className="relative">
                  <button
                    onClick={() => setAddTypePickerOpen(!addTypePickerOpen)}
                    className="flex items-center gap-1.5 h-8 px-3 rounded-lg bg-indigo-600 text-white text-[10px] font-black uppercase tracking-widest hover:bg-indigo-700 transition-all shadow-sm"
                  >
                    <Plus size={13} /> Add Question
                  </button>
                  {addTypePickerOpen && (
                    <div className="absolute right-0 top-10 z-50 w-72 bg-white rounded-2xl border border-slate-200 shadow-xl p-3">
                      <p className="text-[9px] font-black uppercase tracking-widest text-slate-400 mb-2 px-1">Choose question type</p>
                      <div className="grid grid-cols-3 gap-1.5">
                        {Q_TYPES.map(t => (
                          <button
                            key={t.value}
                            onClick={() => handleAddQuestion(t.value)}
                            className="flex flex-col items-center gap-1 px-2 py-2.5 rounded-xl border border-slate-200 hover:border-indigo-300 hover:bg-indigo-50 transition-all group"
                          >
                            <t.icon size={16} className="text-slate-400 group-hover:text-indigo-600" />
                            <span className="text-[9px] font-black uppercase tracking-widest text-slate-500 group-hover:text-indigo-600 text-center leading-tight">{t.label}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          <div
            className="flex-1 overflow-y-auto p-5 space-y-3"
            onClick={() => { setAddTypePickerOpen(false) }}
          >
            {!activeSec ? (
              <div className="flex flex-col items-center justify-center h-full gap-4">
                <div className="h-16 w-16 rounded-2xl bg-slate-100 flex items-center justify-center">
                  <Layers size={28} className="text-slate-300" />
                </div>
                <p className="text-[11px] font-black uppercase tracking-widest text-slate-400">
                  {sections.length === 0 ? 'Add a section to get started' : 'Select a section from the sidebar'}
                </p>
                {sections.length === 0 && (
                  <button
                    onClick={() => setAddingSection(true)}
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 text-white text-[11px] font-black uppercase tracking-widest hover:bg-indigo-700 transition-all"
                  >
                    <Plus size={14} /> Add First Section
                  </button>
                )}
              </div>
            ) : questions.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-60 gap-4 rounded-2xl border-2 border-dashed border-slate-200 bg-white">
                <HelpCircle size={28} className="text-slate-200" />
                <p className="text-[11px] font-black uppercase tracking-widest text-slate-300">No questions yet</p>
                <div className="flex gap-2">
                  <button onClick={() => setPresetsOpen(true)} className="flex items-center gap-1.5 px-4 py-2 rounded-xl border border-slate-200 text-slate-600 text-[10px] font-black uppercase tracking-widest hover:border-indigo-300 hover:text-indigo-600 transition-all">
                    <Layers size={13} /> From Library
                  </button>
                  <button onClick={() => setAddTypePickerOpen(true)} className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 text-white text-[10px] font-black uppercase tracking-widest hover:bg-indigo-700 transition-all">
                    <Plus size={13} /> Add Question
                  </button>
                </div>
              </div>
            ) : (
              questions.map((q: any, qi: number) => (
                <QuestionCard
                  key={q.id}
                  question={q}
                  index={qi}
                  sectionIndex={sections.findIndex((s: any) => s.id === activeSec.id)}
                  isSelected={selectedQuestionId === q.id}
                  sections={sections}
                  formId={id!}
                  onSelect={() => setSelectedQuestionId(selectedQuestionId === q.id ? null : q.id)}
                  onUpdate={data => handleUpdateQuestion(q.id, data)}
                  onDelete={() => handleDeleteQuestion(q.id)}
                  onDuplicate={() => handleDuplicateQuestion(q)}
                  onRefresh={refresh}
                />
              ))
            )}
          </div>

          {/* BOTTOM: Outcomes + routing */}
          <div className="flex-none border-t border-slate-200 bg-white">
            <button
              onClick={() => setOutcomesOpen(!outcomesOpen)}
              className="w-full flex items-center justify-between px-5 py-3 hover:bg-slate-50 transition-all"
            >
              <div className="flex items-center gap-2">
                <Award size={15} className="text-indigo-500" />
                <span className="text-[11px] font-black uppercase tracking-widest text-slate-700">Outcomes & Score Logic</span>
                <span className="text-[9px] font-bold text-slate-400">Pass / Reject / Review thresholds</span>
              </div>
              {outcomesOpen ? <ChevronDown size={14} className="text-slate-400" /> : <ChevronUp size={14} className="text-slate-400" />}
            </button>
            {outcomesOpen && (
              <div className="border-t border-slate-100 max-h-72 overflow-y-auto">
                <OutcomesPanel formDetail={formDetail} onUpdateForm={handleUpdateForm} />
              </div>
            )}
          </div>
        </div>

        {/* RIGHT CONFIG PANEL */}
        <div className="w-72 flex-none border-l border-slate-200 bg-white flex flex-col overflow-hidden">
          <div className="flex-none px-4 py-3 border-b border-slate-100 bg-slate-50/60">
            <p className="text-[9px] font-black uppercase tracking-widest text-slate-400 flex items-center gap-1.5">
              <Settings size={10} /> Question Config
            </p>
          </div>
          <div className="flex-1 overflow-hidden">
            <RightConfigPanel
              question={selectedQ}
              sections={sections}
              onUpdate={data => selectedQ && handleUpdateQuestion(selectedQ.id, data)}
              onRefresh={refresh}
            />
          </div>
        </div>
      </div>

      <PresetsModal open={presetsOpen} onClose={() => setPresetsOpen(false)} onAdd={handleAddPreset} />
      <PreviewModal open={previewOpen} onClose={() => setPreviewOpen(false)} formDetail={formDetail} />
    </div>
  )
}
