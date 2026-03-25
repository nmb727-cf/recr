import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import http from '../utils/http'
import type { CandidateNote } from '@/types'

export interface Engagement {
  id: string
  tenant_id: string
  candidate: string
  candidate_name: string
  candidate_title?: string
  candidate_avatar?: string
  candidate_location?: string
  job: string | null
  job_title: string | null
  engagement_type: string
  stage: string
  priority: 'hot' | 'warm' | 'cold'
  is_active: boolean
  owner_user: string | null
  owner_name: string | null
  follow_up_at: string | null
  is_follow_up_overdue: boolean
  last_activity_at: string | null
  started_at: string
  closed_at: string | null
  closure_reason: string | null
  days_since_activity?: number
  notes?: CandidateNote[]
  notes_search_text?: string
}

export interface ActiveCandidatesResponse {
  count: number
  engagements: Engagement[]
}

export function useActiveEngagements(filters: {
  priority?: string
  stage?: string
  owner?: string
  follow_up_overdue?: string
} = {}) {
  const params = new URLSearchParams()
  if (filters.priority) params.append('priority', filters.priority)
  if (filters.stage) params.append('stage', filters.stage)
  if (filters.owner) params.append('owner', filters.owner)
  if (filters.follow_up_overdue) params.append('follow_up_overdue', filters.follow_up_overdue)

  return useQuery<ActiveCandidatesResponse>({
    queryKey: ['active-engagements', filters],
    queryFn: async () => {
      const base = await http.get(`/candidates/active/?${params.toString()}`).then(r => r.data.data as ActiveCandidatesResponse)
      const candidateIds = [...new Set((base.engagements || []).map(engagement => engagement.candidate).filter(Boolean))]

      if (candidateIds.length === 0) {
        return base
      }

      const noteResponses = await Promise.all(
        candidateIds.map(async candidateId => {
          try {
            const data = await http.get(`/candidates/${candidateId}/notes/`).then(r => r.data.data)
            const notes = (Array.isArray(data) ? data : data?.notes || []) as CandidateNote[]
            return [candidateId, notes] as const
          } catch {
            return [candidateId, [] as CandidateNote[]] as const
          }
        })
      )

      const notesByCandidate = new Map<string, CandidateNote[]>(noteResponses)

      return {
        ...base,
        engagements: (base.engagements || []).map(engagement => {
          const notes = notesByCandidate.get(engagement.candidate) || []
          return {
            ...engagement,
            notes,
            notes_search_text: notes
              .map(note => note.note_text || '')
              .filter(Boolean)
              .join(' ')
              .toLowerCase(),
          }
        }),
      }
    },
  })
}

export function useCandidateEngagements(candidateId: string) {
  return useQuery<Engagement[]>({
    queryKey: ['candidate-engagements', candidateId],
    queryFn: () => http.get(`/candidates/${candidateId}/engagements/`).then(r => r.data.data),
    enabled: !!candidateId,
  })
}

export function useCreateEngagement(candidateId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<Engagement>) =>
      http.post(`/candidates/${candidateId}/engagements/`, data).then(r => r.data.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['active-engagements'] })
      queryClient.invalidateQueries({ queryKey: ['candidate-engagements', candidateId] })
    },
  })
}

export function useUpdateEngagement(candidateId: string, engagementId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<Engagement>) =>
      http.put(`/candidates/${candidateId}/engagements/${engagementId}/`, data).then(r => r.data.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['active-engagements'] })
      queryClient.invalidateQueries({ queryKey: ['candidate-engagements', candidateId] })
    },
  })
}

export function useReviveEngagement(candidateId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (engagementId: string) =>
      http.post(`/candidates/${candidateId}/engagements/${engagementId}/revive/`, {}).then(r => r.data.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['active-engagements'] })
      queryClient.invalidateQueries({ queryKey: ['candidate-engagements', candidateId] })
    },
  })
}

export function useCandidateTimeline(candidateId: string) {
  return useQuery({
    queryKey: ['candidate-timeline', candidateId],
    queryFn: () => http.get(`/candidates/${candidateId}/timeline-events/`).then(r => r.data.data),
    enabled: !!candidateId,
  })
}
