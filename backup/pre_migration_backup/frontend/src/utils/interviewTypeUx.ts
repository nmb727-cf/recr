export type InterviewTypeCategory =
  | 'All'
  | 'AI'
  | 'Human'
  | 'Technical'
  | 'Assessment'
  | 'Screening'
  | 'Advanced'

export type InterviewTypeOption = {
  value: string
  label: string
  category: Exclude<InterviewTypeCategory, 'All'>
}

export const INTERVIEW_TYPE_CATEGORIES: Array<Exclude<InterviewTypeCategory, 'All'>> = [
  'AI',
  'Human',
  'Technical',
  'Assessment',
  'Screening',
  'Advanced',
]

export const INTERVIEW_TYPE_CATALOG: InterviewTypeOption[] = [
  { value: 'ai_screening', label: 'AI Screening', category: 'AI' },
  { value: 'ai_behavioral', label: 'AI Behavioral', category: 'AI' },
  { value: 'ai_technical', label: 'AI Technical', category: 'AI' },
  { value: 'one_way_video', label: 'AI One Way', category: 'AI' },
  { value: 'async_text', label: 'AI Async', category: 'AI' },
  { value: 'async_audio', label: 'AI Async Audio', category: 'AI' },

  { value: 'hr_interview', label: 'HR Interview', category: 'Human' },
  { value: 'hiring_manager_interview', label: 'Hiring Manager', category: 'Human' },
  { value: 'final_round', label: 'Final Interview', category: 'Human' },
  { value: 'panel_interview', label: 'Panel Interview', category: 'Human' },
  { value: 'leadership_interview', label: 'Leadership Interview', category: 'Human' },
  { value: 'behavioral_interview', label: 'Behavioral Interview', category: 'Human' },

  { value: 'coding_interview', label: 'Coding', category: 'Technical' },
  { value: 'system_design', label: 'System Design', category: 'Technical' },
  { value: 'technical_interview', label: 'Architecture', category: 'Technical' },
  { value: 'pair_programming', label: 'Pair Programming', category: 'Technical' },
  { value: 'debugging_interview', label: 'Debugging', category: 'Technical' },
  { value: 'technical_panel', label: 'Technical Panel', category: 'Technical' },
  { value: 'whiteboard_interview', label: 'Whiteboard', category: 'Technical' },

  { value: 'case_study', label: 'Case Study', category: 'Assessment' },
  { value: 'take_home_assignment', label: 'Take Home', category: 'Assessment' },
  { value: 'mcq_assessment', label: 'MCQ', category: 'Assessment' },
  { value: 'work_sample_test', label: 'Assignment', category: 'Assessment' },
  { value: 'aptitude_test', label: 'Aptitude Test', category: 'Assessment' },

  { value: 'recruiter_screening', label: 'Prequalification', category: 'Screening' },
  { value: 'phone_interview', label: 'Knockout', category: 'Screening' },
  { value: 'eligibility_screening', label: 'Eligibility', category: 'Screening' },

  { value: 'group_discussion', label: 'Group Discussion', category: 'Advanced' },
  { value: 'role_play', label: 'Role Play', category: 'Advanced' },
  { value: 'presentation_interview', label: 'Presentation', category: 'Advanced' },
  { value: 'sales_simulation', label: 'Sales Simulation', category: 'Advanced' },
  { value: 'stakeholder_interview', label: 'Stakeholder Interview', category: 'Advanced' },
]

export function getInterviewTypeCategory(typeCode: string): Exclude<InterviewTypeCategory, 'All'> {
  const direct = INTERVIEW_TYPE_CATALOG.find((item) => item.value === typeCode)
  if (direct) return direct.category

  if (typeCode.startsWith('ai_') || ['one_way_video', 'async_text', 'async_audio'].includes(typeCode)) return 'AI'
  if (['coding_interview', 'system_design', 'technical_interview', 'technical_panel', 'debugging_interview', 'whiteboard_interview', 'pair_programming'].includes(typeCode)) return 'Technical'
  if (['mcq_assessment', 'aptitude_test', 'psychometric_test', 'cognitive_test', 'language_assessment', 'case_study', 'take_home_assignment', 'work_sample_test'].includes(typeCode)) return 'Assessment'
  if (['recruiter_screening', 'phone_interview', 'eligibility_screening'].includes(typeCode)) return 'Screening'
  if (['group_discussion', 'role_play', 'presentation_interview', 'sales_simulation', 'assessment_center', 'stakeholder_interview'].includes(typeCode)) return 'Advanced'
  return 'Human'
}

export function getInterviewTypeLabel(typeCode: string) {
  const direct = INTERVIEW_TYPE_CATALOG.find((item) => item.value === typeCode)
  return direct?.label || typeCode.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
}

export function getCategoryOptions(category: InterviewTypeCategory) {
  if (category === 'All') return INTERVIEW_TYPE_CATALOG
  return INTERVIEW_TYPE_CATALOG.filter((item) => item.category === category)
}
