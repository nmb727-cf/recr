import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import IntelligenceHubWorkspace from './IntelligenceHubWorkspace'
import { intelligenceHubApi } from '../../api/intelligenceHub'

vi.mock('../../api/intelligenceHub', () => ({
  intelligenceHubApi: {
    listPrompts: vi.fn(),
    getPrompt: vi.fn(),
    listProviders: vi.fn(),
    listAutomations: vi.fn(),
    getAutomation: vi.fn(),
    listAutomationRuns: vi.fn(),
    listExecutionsAI: vi.fn(),
    listExecutionsAutomation: vi.fn(),
    getExecutionDetail: vi.fn(),
    listSuggestions: vi.fn(),
    getSuggestion: vi.fn(),
    listFailures: vi.fn(),
    listDeadLetter: vi.fn(),
    listApprovals: vi.fn(),
    listConnectors: vi.fn(),
    getSettings: vi.fn(),
    updateSettings: vi.fn(),
  },
}))

function apiResponse<T>(data: T) {
  return Promise.resolve({ data: { success: true, data } } as any)
}

function renderHub(initialEntry: string) {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route path="/intelligence" element={<IntelligenceHubWorkspace />} />
          <Route path="/intelligence/:section" element={<IntelligenceHubWorkspace />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function resetApiMocks() {
  vi.mocked(intelligenceHubApi.listSuggestions).mockReturnValue(apiResponse([]))
  vi.mocked(intelligenceHubApi.getSuggestion).mockReturnValue(apiResponse({}))
  vi.mocked(intelligenceHubApi.listAutomations).mockReturnValue(apiResponse([]))
  vi.mocked(intelligenceHubApi.getAutomation).mockReturnValue(apiResponse({}))
  vi.mocked(intelligenceHubApi.listAutomationRuns).mockReturnValue(apiResponse([]))
  vi.mocked(intelligenceHubApi.listExecutionsAI).mockReturnValue(apiResponse([]))
  vi.mocked(intelligenceHubApi.listExecutionsAutomation).mockReturnValue(apiResponse([]))
  vi.mocked(intelligenceHubApi.getExecutionDetail).mockReturnValue(apiResponse({}))
  vi.mocked(intelligenceHubApi.listFailures).mockReturnValue(apiResponse([]))
  vi.mocked(intelligenceHubApi.listPrompts).mockReturnValue(apiResponse([]))
  vi.mocked(intelligenceHubApi.getPrompt).mockReturnValue(apiResponse({}))
  vi.mocked(intelligenceHubApi.getSettings).mockReturnValue(
    apiResponse({
      tenant_id: 'tenant-1',
      ai_enabled: true,
      automation_enabled: true,
      default_approval_mode: 'suggestion_only',
      allowed_provider_ids_json: [],
      feature_flags_json: {},
      notification_preferences_json: {},
      retry_policy_overrides_json: {},
      connector_enablement_json: {},
      visibility_permissions_json: {},
      updated_at: '2026-04-02T12:00:00Z',
    }),
  )
  vi.mocked(intelligenceHubApi.updateSettings).mockReturnValue(apiResponse({}))
}

describe('IntelligenceHubWorkspace', () => {
  beforeEach(() => {
    resetApiMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('loads suggestions from the suggestions endpoint and opens the detail drawer', async () => {
    vi.mocked(intelligenceHubApi.listSuggestions).mockReturnValue(
      apiResponse([
        {
          id: 'sug-1',
          title: 'Follow up with candidate',
          category: 'followup_recommendation',
          suggestion_key: 'followup_recommendation',
          payload_json: { suggestion_subtype: 'followup_recommendation' },
          confidence_band: 'high',
          confidence_score: '0.88',
          source_module: 'communications',
          source_entity_type: 'candidate',
          source_entity_id: 'cand-1',
          status: 'pending_review',
          updated_at: '2026-04-02T10:00:00Z',
        },
      ]),
    )
    vi.mocked(intelligenceHubApi.getSuggestion).mockReturnValue(
      apiResponse({
        id: 'sug-1',
        title: 'Follow up with candidate',
        category: 'followup_recommendation',
        suggestion_key: 'followup_recommendation',
        payload_json: { suggestion_subtype: 'followup_recommendation', reason: 'Candidate is idle' },
        rationale_json: { reason: 'No response in 48 hours' },
        audit_metadata_json: { ai_execution_id: 'exec-1' },
        confidence_band: 'high',
        confidence_score: '0.88',
        source_module: 'communications',
        source_entity_type: 'candidate',
        source_entity_id: 'cand-1',
        status: 'pending_review',
        summary: 'Send a follow-up.',
        created_at: '2026-04-02T09:00:00Z',
        updated_at: '2026-04-02T10:00:00Z',
        ai_request: {
          id: 'exec-1',
          module_scope: 'communications',
          use_case_key: 'followup_recommendation',
          status: 'completed',
        },
      }),
    )

    renderHub('/intelligence')

    expect(await screen.findByText('Suggestions')).toBeInTheDocument()
    fireEvent.click(await screen.findByText('Follow up with candidate'))
    expect(await screen.findByText('Suggestion Detail')).toBeInTheDocument()
    expect(
      (await screen.findAllByText((_, element) => element?.textContent?.includes('No response in 48 hours') ?? false))
        .length,
    ).toBeGreaterThan(0)
  })

  it('loads automations from real endpoints after section navigation', async () => {
    vi.mocked(intelligenceHubApi.listAutomations).mockReturnValue(
      apiResponse([
        {
          id: 'rule-1',
          rule_title: 'Candidate follow-up',
          rule_key: 'candidate-followup',
          module_scope: 'pipeline',
          trigger_event: 'application.created',
          status: 'active',
          mode: 'suggestion_only',
          duplicate_window_seconds: 300,
          priority_order: 10,
          conditions: [],
          actions: [],
        },
      ]),
    )
    vi.mocked(intelligenceHubApi.listExecutionsAutomation).mockReturnValue(
      apiResponse([
        {
          id: 'run-1',
          rule: 'rule-1',
          status: 'completed',
          source_event: 'application.created',
          source_entity_type: 'application',
          source_entity_id: 'app-1',
          created_at: '2026-04-02T08:00:00Z',
        },
      ]),
    )

    renderHub('/intelligence')
    fireEvent.click(await screen.findByRole('button', { name: 'Automations' }))

    expect(await screen.findByText('Automation Rules')).toBeInTheDocument()
    expect(await screen.findByText('Candidate follow-up')).toBeInTheDocument()
    expect(intelligenceHubApi.listAutomations).toHaveBeenCalled()
  })

  it('shows the executions empty state when no execution data exists', async () => {
    renderHub('/intelligence/executions')
    expect(await screen.findByText('Executions')).toBeInTheDocument()
    expect(await screen.findByText('No executions exist yet.')).toBeInTheDocument()
  })

  it('shows the failures empty state when no failure data exists', async () => {
    renderHub('/intelligence/failures')
    expect(await screen.findByText('Failures')).toBeInTheDocument()
    expect(await screen.findByText('No failures are currently recorded.')).toBeInTheDocument()
  })

  it('shows an error state when prompts fail to load', async () => {
    vi.mocked(intelligenceHubApi.listPrompts).mockRejectedValue(new Error('Prompt endpoint failed'))
    renderHub('/intelligence/prompts')

    expect(await screen.findByText('Prompts could not be loaded.')).toBeInTheDocument()
    expect(await screen.findByText('Prompt endpoint failed')).toBeInTheDocument()
  })

  it('loads settings from the real settings endpoint', async () => {
    renderHub('/intelligence/settings')

    expect(await screen.findByText('Tenant Intelligence Settings')).toBeInTheDocument()
    expect(await screen.findByText('suggestion only')).toBeInTheDocument()
    expect(intelligenceHubApi.getSettings).toHaveBeenCalled()
  })

  it('saves settings through the backend settings endpoint', async () => {
    renderHub('/intelligence/settings')

    const saveButton = await screen.findByRole('button', { name: 'Save settings' })
    fireEvent.click(saveButton)

    await waitFor(() => {
      expect(intelligenceHubApi.updateSettings).toHaveBeenCalled()
    })
  })
})
