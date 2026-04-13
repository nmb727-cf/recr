import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
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
    approveSuggestion: vi.fn(),
    rejectSuggestion: vi.fn(),
    dismissSuggestion: vi.fn(),
    applySuggestion: vi.fn(),
    listFailures: vi.fn(),
    retryFailure: vi.fn(),
    listDeadLetter: vi.fn(),
    listApprovals: vi.fn(),
    listConnectors: vi.fn(),
    getSettings: vi.fn(),
    updateSettings: vi.fn(),
    listAutomationIntelligencePolicies: vi.fn(),
    createAutomationIntelligencePolicy: vi.fn(),
    updateAutomationIntelligencePolicy: vi.fn(),
    deleteAutomationIntelligencePolicy: vi.fn(),
    listAutomationPolicies: vi.fn(),
    createAutomationPolicy: vi.fn(),
    updateAutomationPolicy: vi.fn(),
    deleteAutomationPolicy: vi.fn(),
  },
}))

function apiResponse<T>(data: T) {
  return Promise.resolve({ data: { success: true, data } } as any)
}

function pendingResponse() {
  return new Promise(() => {})
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
  vi.mocked(intelligenceHubApi.approveSuggestion).mockReturnValue(apiResponse({}))
  vi.mocked(intelligenceHubApi.rejectSuggestion).mockReturnValue(apiResponse({}))
  vi.mocked(intelligenceHubApi.dismissSuggestion).mockReturnValue(apiResponse({}))
  vi.mocked(intelligenceHubApi.applySuggestion).mockReturnValue(apiResponse({}))
  vi.mocked(intelligenceHubApi.listAutomations).mockReturnValue(apiResponse([]))
  vi.mocked(intelligenceHubApi.getAutomation).mockReturnValue(apiResponse({}))
  vi.mocked(intelligenceHubApi.listAutomationRuns).mockReturnValue(apiResponse([]))
  vi.mocked(intelligenceHubApi.listExecutionsAI).mockReturnValue(apiResponse([]))
  vi.mocked(intelligenceHubApi.listExecutionsAutomation).mockReturnValue(apiResponse([]))
  vi.mocked(intelligenceHubApi.getExecutionDetail).mockReturnValue(apiResponse({}))
  vi.mocked(intelligenceHubApi.listFailures).mockReturnValue(apiResponse([]))
  vi.mocked(intelligenceHubApi.retryFailure).mockReturnValue(apiResponse({}))
  vi.mocked(intelligenceHubApi.listPrompts).mockReturnValue(apiResponse([]))
  vi.mocked(intelligenceHubApi.getPrompt).mockReturnValue(apiResponse({}))
  vi.mocked(intelligenceHubApi.listProviders).mockReturnValue(apiResponse([]))
  vi.mocked(intelligenceHubApi.listConnectors).mockReturnValue(apiResponse([]))
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
  vi.mocked(intelligenceHubApi.listAutomationIntelligencePolicies).mockReturnValue(apiResponse([]))
  vi.mocked(intelligenceHubApi.createAutomationIntelligencePolicy).mockReturnValue(apiResponse({}))
  vi.mocked(intelligenceHubApi.updateAutomationIntelligencePolicy).mockReturnValue(apiResponse({}))
  vi.mocked(intelligenceHubApi.deleteAutomationIntelligencePolicy).mockReturnValue(apiResponse({}))
  vi.mocked(intelligenceHubApi.listAutomationPolicies).mockReturnValue(apiResponse([]))
  vi.mocked(intelligenceHubApi.createAutomationPolicy).mockReturnValue(apiResponse({}))
  vi.mocked(intelligenceHubApi.updateAutomationPolicy).mockReturnValue(apiResponse({}))
  vi.mocked(intelligenceHubApi.deleteAutomationPolicy).mockReturnValue(apiResponse({}))
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
          status: 'pending',
          created_at: '2026-04-02T10:00:00Z',
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
        status: 'pending',
        summary: 'Send a follow-up.',
        created_at: '2026-04-02T09:00:00Z',
        updated_at: '2026-04-02T10:00:00Z',
        requires_approval: true,
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

  it('approves a pending suggestion from the actions column', async () => {
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
          status: 'pending',
          created_at: '2026-04-02T10:00:00Z',
        },
      ]),
    )
    vi.mocked(intelligenceHubApi.getSuggestion).mockReturnValue(
      apiResponse({
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
        status: 'pending',
        created_at: '2026-04-02T09:00:00Z',
        updated_at: '2026-04-02T10:06:00Z',
        conversions: [],
      }),
    )

    renderHub('/intelligence')

    fireEvent.click(await screen.findByRole('button', { name: 'Approve' }))
    await waitFor(() => expect(intelligenceHubApi.approveSuggestion).toHaveBeenCalledWith('sug-1', { comment: '' }))
  })

  it('shows apply action for approved suggestions and hides pending-only actions', async () => {
    vi.mocked(intelligenceHubApi.listSuggestions).mockReturnValue(
      apiResponse([
        {
          id: 'sug-1',
          title: 'Approved suggestion',
          category: 'review_recommendation',
          suggestion_key: 'review_recommendation',
          payload_json: { suggestion_subtype: 'review_recommendation' },
          confidence_band: 'medium',
          confidence_score: '0.70',
          source_module: 'interviews',
          source_entity_type: 'interview',
          source_entity_id: 'int-1',
          owner_module: 'communications',
          proposed_action_family: 'enqueue_communication',
          status: 'approved',
          created_at: '2026-04-02T10:00:00Z',
        },
      ]),
    )

    renderHub('/intelligence')
    expect(await screen.findByText('Approved suggestion')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Apply' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Approve' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Reject' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Dismiss' })).not.toBeInTheDocument()
  })

  it('applies an approved suggestion from the actions column', async () => {
    vi.mocked(intelligenceHubApi.listSuggestions).mockReturnValue(
      apiResponse([
        {
          id: 'sug-2',
          title: 'Approved suggestion',
          category: 'followup_recommendation',
          suggestion_key: 'followup_recommendation',
          payload_json: { suggestion_subtype: 'followup_recommendation' },
          confidence_band: 'high',
          confidence_score: '0.88',
          source_module: 'communications',
          source_entity_type: 'candidate',
          source_entity_id: 'cand-2',
          owner_module: 'communications',
          proposed_action_family: 'enqueue_communication',
          status: 'approved',
          created_at: '2026-04-02T10:00:00Z',
        },
      ]),
    )

    renderHub('/intelligence')
    fireEvent.click(await screen.findByRole('button', { name: 'Apply' }))
    await waitFor(() => expect(intelligenceHubApi.applySuggestion).toHaveBeenCalledWith('sug-2', { comment: '' }))
  })

  it('keeps unsupported approved suggestions read-only without fake apply action', async () => {
    vi.mocked(intelligenceHubApi.listSuggestions).mockReturnValue(
      apiResponse([
        {
          id: 'sug-3',
          title: 'Unsupported approved suggestion',
          category: 'deadline_recommendation',
          suggestion_key: 'deadline_recommendation',
          payload_json: { suggestion_subtype: 'deadline_recommendation' },
          confidence_band: 'medium',
          confidence_score: '0.65',
          source_module: 'pipeline',
          source_entity_type: 'application',
          source_entity_id: 'app-3',
          owner_module: 'deadline',
          proposed_action_family: 'create_deadline_recommendation',
          status: 'approved',
          created_at: '2026-04-02T10:00:00Z',
        },
      ]),
    )

    renderHub('/intelligence')

    expect(await screen.findByText('Unsupported approved suggestion')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Apply' })).not.toBeInTheDocument()
    expect(screen.getByText('Apply not supported for this owner contract')).toBeInTheDocument()
  })

  it('shows apply_failed detail metadata and read-only retry state', async () => {
    vi.mocked(intelligenceHubApi.listSuggestions).mockReturnValue(
      apiResponse([
        {
          id: 'sug-4',
          title: 'Failed apply suggestion',
          category: 'followup_recommendation',
          suggestion_key: 'followup_recommendation',
          payload_json: { suggestion_subtype: 'followup_recommendation' },
          confidence_band: 'medium',
          confidence_score: '0.62',
          source_module: 'communications',
          source_entity_type: 'candidate',
          source_entity_id: 'cand-4',
          owner_module: 'communications',
          proposed_action_family: 'enqueue_communication',
          status: 'apply_failed',
          created_at: '2026-04-02T10:00:00Z',
        },
      ]),
    )
    vi.mocked(intelligenceHubApi.getSuggestion).mockReturnValue(
      apiResponse({
        id: 'sug-4',
        title: 'Failed apply suggestion',
        category: 'followup_recommendation',
        suggestion_key: 'followup_recommendation',
        payload_json: { suggestion_subtype: 'followup_recommendation' },
        rationale_json: { reason: 'No candidate response' },
        confidence_band: 'medium',
        confidence_score: '0.62',
        source_module: 'communications',
        source_entity_type: 'candidate',
        source_entity_id: 'cand-4',
        owner_module: 'communications',
        proposed_action_family: 'enqueue_communication',
        status: 'apply_failed',
        last_apply_status: 'apply_failed',
        last_apply_error_message: 'Mailbox not available',
        last_apply_result_json: { error_category: 'owner_contract_validation', retry_safe: true },
        created_at: '2026-04-02T09:00:00Z',
        updated_at: '2026-04-02T10:06:00Z',
      }),
    )

    renderHub('/intelligence')

    fireEvent.click(await screen.findByText('Failed apply suggestion'))
    expect(await screen.findByText('Apply failed')).toBeInTheDocument()
    expect((await screen.findAllByText('Mailbox not available')).length).toBeGreaterThan(0)
    expect(
      await screen.findByText('Retry not available in current backend API (read-only failure state).'),
    ).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Retry Apply' })).not.toBeInTheDocument()
  })

  it('rejects and dismisses pending suggestions from the actions column', async () => {
    vi.mocked(intelligenceHubApi.listSuggestions).mockReturnValue(
      apiResponse([
        {
          id: 'sug-1',
          title: 'Rejectable suggestion',
          category: 'followup_recommendation',
          suggestion_key: 'followup_recommendation',
          payload_json: { suggestion_subtype: 'followup_recommendation' },
          confidence_band: 'medium',
          confidence_score: '0.55',
          source_module: 'communications',
          source_entity_type: 'candidate',
          source_entity_id: 'cand-1',
          status: 'pending',
          created_at: '2026-04-02T10:00:00Z',
        },
      ]),
    )
    vi.mocked(intelligenceHubApi.getSuggestion).mockReturnValue(
      apiResponse({
        id: 'sug-1',
        title: 'Rejectable suggestion',
        category: 'followup_recommendation',
        suggestion_key: 'followup_recommendation',
        payload_json: { suggestion_subtype: 'followup_recommendation' },
        confidence_band: 'medium',
        confidence_score: '0.55',
        source_module: 'communications',
        source_entity_type: 'candidate',
        source_entity_id: 'cand-1',
        status: 'pending',
        created_at: '2026-04-02T09:00:00Z',
        updated_at: '2026-04-02T10:06:00Z',
        conversions: [],
      }),
    )

    renderHub('/intelligence')

    fireEvent.click(await screen.findByRole('button', { name: 'Reject' }))
    await waitFor(() => expect(intelligenceHubApi.rejectSuggestion).toHaveBeenCalledWith('sug-1', { comment: '' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Dismiss' }))
    await waitFor(() => expect(intelligenceHubApi.dismissSuggestion).toHaveBeenCalledWith('sug-1', { comment: '' }))
  })

  it('filters suggestions client-side', async () => {
    vi.mocked(intelligenceHubApi.listSuggestions).mockReturnValue(
      apiResponse([
        {
          id: 'sug-1',
          title: 'Communications suggestion',
          category: 'followup_recommendation',
          payload_json: { suggestion_subtype: 'followup_recommendation' },
          confidence_band: 'high',
          confidence_score: '0.90',
          source_module: 'communications',
          source_entity_type: 'candidate',
          source_entity_id: 'cand-1',
          status: 'pending',
          created_at: '2026-04-02T10:00:00Z',
        },
        {
          id: 'sug-2',
          title: 'Pipeline suggestion',
          category: 'deadline_recommendation',
          payload_json: { suggestion_subtype: 'deadline_recommendation' },
          confidence_band: 'medium',
          confidence_score: '0.40',
          source_module: 'pipeline',
          source_entity_type: 'application',
          source_entity_id: 'app-1',
          status: 'approved',
          created_at: '2026-04-02T10:00:00Z',
        },
      ]),
    )

    renderHub('/intelligence')

    expect(await screen.findByText('Communications suggestion')).toBeInTheDocument()
    expect(await screen.findByText('Pipeline suggestion')).toBeInTheDocument()

    fireEvent.change(screen.getByTestId('suggestion-filter-status'), { target: { value: 'approved' } })
    await waitFor(() => {
      expect(screen.getByText('Pipeline suggestion')).toBeInTheDocument()
      expect(screen.queryByText('Communications suggestion')).not.toBeInTheDocument()
    })
  })

  it('shows the suggestions empty state when no suggestion data exists', async () => {
    renderHub('/intelligence')
    expect(await screen.findByText('No suggestions yet')).toBeInTheDocument()
  })

  it('shows Auto Approved badge when suggestion was auto-approved', async () => {
    vi.mocked(intelligenceHubApi.listSuggestions).mockReturnValue(
      apiResponse([
        {
          id: 'sug-auto',
          title: 'Auto approved suggestion',
          category: 'followup_recommendation',
          payload_json: {},
          confidence_band: 'high',
          confidence_score: '0.92',
          source_module: 'communications',
          source_entity_type: 'candidate',
          source_entity_id: 'cand-1',
          status: 'approved',
          approval_comment: 'Auto-approved by automation intelligence policy abc-123',
          apply_comment: '',
          created_at: '2026-04-03T10:00:00Z',
        },
      ]),
    )

    renderHub('/intelligence')

    expect(await screen.findByText('Auto Approved')).toBeInTheDocument()
  })

  it('shows Auto Applied badge when suggestion was auto-applied', async () => {
    vi.mocked(intelligenceHubApi.listSuggestions).mockReturnValue(
      apiResponse([
        {
          id: 'sug-applied',
          title: 'Auto applied suggestion',
          category: 'followup_recommendation',
          payload_json: {},
          confidence_band: 'high',
          confidence_score: '0.94',
          source_module: 'communications',
          source_entity_type: 'candidate',
          source_entity_id: 'cand-2',
          status: 'applied',
          approval_comment: 'Auto-approved by automation intelligence policy abc-123',
          apply_comment: 'Auto-applied by automation intelligence policy abc-123',
          created_at: '2026-04-03T10:00:00Z',
        },
      ]),
    )

    renderHub('/intelligence')

    expect(await screen.findByText('Auto Approved')).toBeInTheDocument()
    expect(await screen.findByText('Auto Applied')).toBeInTheDocument()
  })

  it('loads automation intelligence policies and updates a policy', async () => {
    vi.mocked(intelligenceHubApi.listAutomationIntelligencePolicies).mockReturnValue(
      apiResponse([
        {
          id: 'policy-1',
          suggestion_type: 'followup_recommendation',
          module_scope: 'communications',
          confidence_threshold: '0.85',
          auto_approve: true,
          auto_apply: false,
          approval_required: true,
          is_enabled: true,
          last_outcome: 'auto_approved',
          updated_at: '2026-04-02T10:00:00Z',
        },
      ]),
    )

    renderHub('/intelligence/automation-intelligence')

    expect(await screen.findByText('Automation Intelligence Policies')).toBeInTheDocument()
    expect((await screen.findAllByText('followup recommendation')).length).toBeGreaterThan(0)

    fireEvent.change(screen.getByTestId('automation-intelligence-level-policy-1'), { target: { value: 'auto_apply' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() =>
      expect(intelligenceHubApi.updateAutomationIntelligencePolicy).toHaveBeenCalledWith(
        'policy-1',
        expect.objectContaining({
          auto_approve: true,
          auto_apply: true,
          approval_required: false,
        }),
      ),
    )
  })

  it('creates a new automation intelligence policy from the create form', async () => {
    renderHub('/intelligence/automation-intelligence')

    await screen.findByText('Automation Intelligence Policies')

    fireEvent.change(screen.getByTestId('automation-intelligence-new-type'), { target: { value: 'deadline_recommendation' } })
    fireEvent.change(screen.getByTestId('automation-intelligence-new-threshold'), { target: { value: '0.90' } })
    fireEvent.change(screen.getByTestId('automation-intelligence-new-level'), { target: { value: 'auto_approve' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add Policy' }))

    await waitFor(() =>
      expect(intelligenceHubApi.createAutomationIntelligencePolicy).toHaveBeenCalledWith(
        expect.objectContaining({
          suggestion_type: 'deadline_recommendation',
          confidence_threshold: 0.9,
          auto_approve: true,
          auto_apply: false,
          approval_required: true,
          is_enabled: true,
        }),
      ),
    )
  })

  it('deletes an automation intelligence policy', async () => {
    vi.mocked(intelligenceHubApi.listAutomationIntelligencePolicies).mockReturnValue(
      apiResponse([
        {
          id: 'policy-1',
          suggestion_type: 'followup_recommendation',
          module_scope: 'communications',
          confidence_threshold: '0.85',
          auto_approve: false,
          auto_apply: false,
          approval_required: true,
          is_enabled: true,
          last_outcome: '',
          updated_at: '2026-04-03T10:00:00Z',
        },
      ]),
    )

    renderHub('/intelligence/automation-intelligence')

    fireEvent.click(await screen.findByRole('button', { name: 'Delete' }))

    await waitFor(() =>
      expect(intelligenceHubApi.deleteAutomationIntelligencePolicy).toHaveBeenCalledWith('policy-1'),
    )
  })

  it('toggles the enabled switch and saves the updated policy', async () => {
    const user = userEvent.setup()

    vi.mocked(intelligenceHubApi.listAutomationIntelligencePolicies).mockReturnValue(
      apiResponse([
        {
          id: 'policy-1',
          suggestion_type: 'followup_recommendation',
          module_scope: 'communications',
          confidence_threshold: '0.85',
          auto_approve: false,
          auto_apply: false,
          approval_required: true,
          is_enabled: true,
          last_outcome: '',
          updated_at: '2026-04-03T10:00:00Z',
        },
      ]),
    )

    renderHub('/intelligence/automation-intelligence')

    await screen.findByText('Automation Intelligence Policies')

    await user.click(screen.getByTestId('automation-intelligence-enabled-policy-1'))
    await user.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() =>
      expect(intelligenceHubApi.updateAutomationIntelligencePolicy).toHaveBeenCalledWith(
        'policy-1',
        expect.objectContaining({ is_enabled: false }),
      ),
    )
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

  it('opens automation detail with real rule and run data', async () => {
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
          is_builtin: false,
          duplicate_window_seconds: 300,
          priority_order: 10,
          created_by: 'user-1',
          updated_at: '2026-04-02T08:00:00Z',
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
          source_module: 'pipeline',
          source_entity_type: 'application',
          source_entity_id: 'app-1',
          created_at: '2026-04-02T09:00:00Z',
          completed_at: '2026-04-02T09:05:00Z',
        },
      ]),
    )
    vi.mocked(intelligenceHubApi.getAutomation).mockReturnValue(
      apiResponse({
        id: 'rule-1',
        rule_title: 'Candidate follow-up',
        rule_key: 'candidate-followup',
        module_scope: 'pipeline',
        trigger_event: 'application.created',
        status: 'active',
        mode: 'suggestion_only',
        is_builtin: false,
        duplicate_window_seconds: 300,
        priority_order: 10,
        created_by: 'user-1',
        tenant_id: 'tenant-1',
        updated_at: '2026-04-02T08:00:00Z',
        conditions: [{ id: 'c-1', condition_group: 'default', field_path: 'application.status', operator: 'eq', expected_value_json: { value: 'applied' }, is_negated: false }],
        actions: [{ id: 'a-1', action_type: 'schedule_followup', action_config_json: { delay: 3600 }, delay_seconds: 3600, requires_approval: false }],
        scopes: [{ id: 's-1', entity_type: 'application', stage_key: 'applied', role_scope: '', source_scope: '', working_hours_only: false, is_active: true }],
      }),
    )
    vi.mocked(intelligenceHubApi.listAutomationRuns).mockReturnValue(
      apiResponse([
        {
          id: 'run-1',
          rule: 'rule-1',
          status: 'completed',
          source_event: 'application.created',
          source_module: 'pipeline',
          source_entity_type: 'application',
          source_entity_id: 'app-1',
          created_at: '2026-04-02T09:00:00Z',
          completed_at: '2026-04-02T09:05:00Z',
          evaluated_conditions_json: [{ ok: true }],
          action_results_json: [{ action: 'schedule_followup', result: 'completed' }],
          trigger_payload_json: { entity_id: 'app-1' },
        },
      ]),
    )

    renderHub('/intelligence/automations')

    fireEvent.click(await screen.findByText('Candidate follow-up'))
    expect(await screen.findByText('Automation Rule Detail')).toBeInTheDocument()
    expect(await screen.findByText('Conditions')).toBeInTheDocument()
    expect(await screen.findByText('schedule followup')).toBeInTheDocument()
  })

  it('filters automation rules client-side', async () => {
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
          is_builtin: false,
          updated_at: '2026-04-02T08:00:00Z',
        },
        {
          id: 'rule-2',
          rule_title: 'Interview escalation',
          rule_key: 'interview-escalation',
          module_scope: 'interviews',
          trigger_event: 'interview.missed',
          status: 'paused',
          mode: 'approval_required',
          is_builtin: true,
          updated_at: '2026-04-02T07:00:00Z',
        },
      ]),
    )

    renderHub('/intelligence/automations')

    expect(await screen.findByText('Candidate follow-up')).toBeInTheDocument()
    expect(await screen.findByText('Interview escalation')).toBeInTheDocument()

    const statusFilter = await screen.findByTestId('automation-filter-status')
    fireEvent.change(statusFilter, { target: { value: 'paused' } })

    await waitFor(() => {
      expect(screen.getByText('Interview escalation')).toBeInTheDocument()
      expect(screen.queryByText('Candidate follow-up')).not.toBeInTheDocument()
    })
  })

  it('shows automations empty state when no rules exist', async () => {
    renderHub('/intelligence/automations')

    expect(await screen.findByText('Automation Rules')).toBeInTheDocument()
    expect(await screen.findByText('No automation rules exist yet.')).toBeInTheDocument()
  })

  it('shows automations loading state while rules are pending', async () => {
    vi.mocked(intelligenceHubApi.listAutomations).mockReturnValue(pendingResponse() as any)

    renderHub('/intelligence/automations')

    expect(await screen.findByText('Loading automation rules…')).toBeInTheDocument()
  })

  it('shows an automations error state when the backend fails', async () => {
    vi.mocked(intelligenceHubApi.listAutomations).mockRejectedValue(new Error('Automation endpoint failed'))

    renderHub('/intelligence/automations')

    expect(await screen.findByText('Automation rules could not be loaded.')).toBeInTheDocument()
    expect(await screen.findByText('Automation endpoint failed')).toBeInTheDocument()
  })

  it('loads AI executions from the real execution endpoint', async () => {
    vi.mocked(intelligenceHubApi.listExecutionsAI).mockReturnValue(
      apiResponse([
        {
          id: 'ai-exec-1',
          status: 'completed',
          source_module: 'communications',
          module_scope: 'communications',
          source_entity_type: 'candidate',
          source_entity_id: 'cand-1',
          source_event: 'candidate.followup_requested',
          provider: 'provider-openai',
          model: 'gpt-5.4',
          queued_at: '2026-04-02T09:00:00Z',
          completed_at: '2026-04-02T09:01:00Z',
          result: { execution_ms: 1200 },
        },
      ]),
    )

    renderHub('/intelligence/executions')

    expect(await screen.findByText('Executions')).toBeInTheDocument()
    expect(await screen.findByText('ai-exec-1')).toBeInTheDocument()
    expect((await screen.findAllByText('communications')).length).toBeGreaterThan(0)
    expect(await screen.findByText('candidate:cand-1')).toBeInTheDocument()
    expect(intelligenceHubApi.listExecutionsAI).toHaveBeenCalled()
  })

  it('loads automation runs when switching to the automation executions view', async () => {
    vi.mocked(intelligenceHubApi.listExecutionsAutomation).mockReturnValue(
      apiResponse([
        {
          id: 'auto-run-1',
          status: 'failed',
          source_module: 'pipeline',
          source_entity_type: 'application',
          source_entity_id: 'app-1',
          source_event: 'application.created',
          created_at: '2026-04-02T07:00:00Z',
          completed_at: '2026-04-02T07:02:00Z',
          retry_count: 1,
        },
      ]),
    )

    renderHub('/intelligence/executions')

    fireEvent.click(await screen.findByRole('button', { name: 'Automation Runs' }))

    expect(await screen.findByText('auto-run-1')).toBeInTheDocument()
    expect(await screen.findByText('application:app-1')).toBeInTheDocument()
    expect(await screen.findByText('application.created')).toBeInTheDocument()
  })

  it('opens execution detail from the real detail endpoint', async () => {
    vi.mocked(intelligenceHubApi.listExecutionsAI).mockReturnValue(
      apiResponse([
        {
          id: 'ai-exec-1',
          status: 'failed',
          source_module: 'communications',
          module_scope: 'communications',
          source_entity_type: 'candidate',
          source_entity_id: 'cand-1',
          source_event: 'candidate.followup_requested',
          provider: 'provider-openai',
          model: 'gpt-5.4',
          queued_at: '2026-04-02T09:00:00Z',
          completed_at: '2026-04-02T09:01:00Z',
          retry_count: 2,
        },
      ]),
    )
    vi.mocked(intelligenceHubApi.getExecutionDetail).mockReturnValue(
      apiResponse({
        execution_type: 'ai',
        payload: {
          id: 'ai-exec-1',
          status: 'failed',
          source_module: 'communications',
          module_scope: 'communications',
          source_entity_type: 'candidate',
          source_entity_id: 'cand-1',
          source_event: 'candidate.followup_requested',
          use_case_key: 'followup_recommendation',
          provider: 'provider-openai',
          model: 'gpt-5.4',
          prompt_version: 'prompt-v1',
          queued_at: '2026-04-02T09:00:00Z',
          started_at: '2026-04-02T09:00:10Z',
          completed_at: '2026-04-02T09:01:00Z',
          retry_count: 2,
          failure_category: 'provider_error',
          failure_reason: 'Rate limited by provider',
          context_snapshot_json: { candidate_id: 'cand-1' },
          result: { validation_status: 'invalid', execution_ms: 1200 },
          review: { review_status: 'pending_review', application_status: 'not_applied' },
          metadata: { trace_id: 'trace-1' },
        },
      }),
    )

    renderHub('/intelligence/executions')

    fireEvent.click(await screen.findByText('ai-exec-1'))

    expect(await screen.findByText('Execution Detail')).toBeInTheDocument()
    expect(await screen.findByText('Rate limited by provider')).toBeInTheDocument()
    expect(await screen.findByText('followup recommendation')).toBeInTheDocument()
    expect(await screen.findByText('Request / Source Context')).toBeInTheDocument()
  })

  it('filters AI executions client-side', async () => {
    vi.mocked(intelligenceHubApi.listExecutionsAI).mockReturnValue(
      apiResponse([
        {
          id: 'ai-exec-1',
          status: 'completed',
          source_module: 'communications',
          module_scope: 'communications',
          source_entity_type: 'candidate',
          source_entity_id: 'cand-1',
          provider: 'provider-openai',
          model: 'gpt-5.4',
          queued_at: '2026-04-02T09:00:00Z',
        },
        {
          id: 'ai-exec-2',
          status: 'queued',
          source_module: 'pipeline',
          module_scope: 'pipeline',
          source_entity_type: 'application',
          source_entity_id: 'app-2',
          provider: 'provider-anthropic',
          model: 'claude-sonnet',
          queued_at: '2026-04-01T09:00:00Z',
        },
      ]),
    )

    renderHub('/intelligence/executions')

    expect(await screen.findByText('ai-exec-1')).toBeInTheDocument()
    expect(await screen.findByText('candidate:cand-1')).toBeInTheDocument()
    expect(await screen.findByText('application:app-2')).toBeInTheDocument()

    fireEvent.change(screen.getByTestId('execution-filter-status'), { target: { value: 'queued' } })

    await waitFor(() => {
      expect(screen.getByText('application:app-2')).toBeInTheDocument()
      expect(screen.queryByText('candidate:cand-1')).not.toBeInTheDocument()
    })
  })

  it('shows the executions empty state when no execution data exists', async () => {
    renderHub('/intelligence/executions')
    expect(await screen.findByText('Executions')).toBeInTheDocument()
    expect(await screen.findByText('No AI executions exist yet.')).toBeInTheDocument()
  })

  it('shows the executions loading state while AI executions are pending', async () => {
    vi.mocked(intelligenceHubApi.listExecutionsAI).mockReturnValue(pendingResponse() as any)

    renderHub('/intelligence/executions')

    expect(await screen.findByText('Loading executions…')).toBeInTheDocument()
  })

  it('shows an executions error state when the AI execution backend fails', async () => {
    vi.mocked(intelligenceHubApi.listExecutionsAI).mockRejectedValue(new Error('AI execution endpoint failed'))

    renderHub('/intelligence/executions')

    expect(await screen.findByText('AI executions could not be loaded.')).toBeInTheDocument()
    expect(await screen.findByText('AI execution endpoint failed')).toBeInTheDocument()
  })

  it('loads failures from the real failure endpoint with linked execution context', async () => {
    vi.mocked(intelligenceHubApi.listFailures).mockReturnValue(
      apiResponse([
        {
          id: 'failure-1',
          failure_type: 'runtime_error',
          related_request_id: 'ai-exec-1',
          related_run_id: null,
          category: 'provider_error',
          severity: 'high',
          status: 'new',
          retryable: true,
          max_retries: 2,
          next_retry_at: null,
          operator_notes: '',
          last_error_message: 'Provider timed out while generating response',
          tenant_id: 'tenant-1',
          created_at: '2026-04-02T09:00:00Z',
          updated_at: '2026-04-02T09:05:00Z',
        },
      ]),
    )
    vi.mocked(intelligenceHubApi.listExecutionsAI).mockReturnValue(
      apiResponse([
        {
          id: 'ai-exec-1',
          status: 'failed',
          source_module: 'communications',
          module_scope: 'communications',
          source_entity_type: 'candidate',
          source_entity_id: 'cand-1',
          retry_count: 1,
        },
      ]),
    )

    renderHub('/intelligence/failures')

    expect(await screen.findByText('Failures')).toBeInTheDocument()
    expect(await screen.findByText('failure-1')).toBeInTheDocument()
    expect((await screen.findAllByText('communications')).length).toBeGreaterThan(0)
    expect(await screen.findByText('candidate:cand-1')).toBeInTheDocument()
  })

  it('opens failure detail and shows linked execution data', async () => {
    vi.mocked(intelligenceHubApi.listFailures).mockReturnValue(
      apiResponse([
        {
          id: 'failure-1',
          failure_type: 'runtime_error',
          related_request_id: 'ai-exec-1',
          related_run_id: null,
          category: 'provider_error',
          severity: 'high',
          status: 'new',
          retryable: true,
          max_retries: 2,
          next_retry_at: null,
          operator_notes: 'Traceback line 42',
          last_error_message: 'Provider timed out while generating response',
          tenant_id: 'tenant-1',
          metadata: { trace_id: 'trace-1' },
          created_at: '2026-04-02T09:00:00Z',
          updated_at: '2026-04-02T09:05:00Z',
        },
      ]),
    )
    vi.mocked(intelligenceHubApi.listExecutionsAI).mockReturnValue(
      apiResponse([
        {
          id: 'ai-exec-1',
          status: 'failed',
          source_module: 'communications',
          module_scope: 'communications',
          source_entity_type: 'candidate',
          source_entity_id: 'cand-1',
          retry_count: 1,
        },
      ]),
    )
    vi.mocked(intelligenceHubApi.getExecutionDetail).mockReturnValue(
      apiResponse({
        execution_type: 'ai',
        payload: {
          id: 'ai-exec-1',
          status: 'failed',
          source_module: 'communications',
          source_entity_type: 'candidate',
          source_entity_id: 'cand-1',
          provider: 'provider-openai',
          model: 'gpt-5.4',
          context_snapshot_json: { candidate_id: 'cand-1' },
          retry_count: 1,
          failure_reason: 'Provider timed out while generating response',
          failure_category: 'provider_error',
          result: { execution_ms: 900 },
        },
      }),
    )

    renderHub('/intelligence/failures')

    fireEvent.click(await screen.findByText('failure-1'))

    expect(await screen.findByText('Failure Detail')).toBeInTheDocument()
    expect(await screen.findByText('Stack / Technical Detail')).toBeInTheDocument()
    expect(await screen.findByText('Execution Linkage')).toBeInTheDocument()
    expect(
      (await screen.findAllByText((_, element) => element?.textContent?.includes('Provider timed out while generating response') ?? false)).length,
    ).toBeGreaterThan(0)
  })

  it('filters failures client-side', async () => {
    vi.mocked(intelligenceHubApi.listFailures).mockReturnValue(
      apiResponse([
        {
          id: 'failure-1',
          failure_type: 'runtime_error',
          related_request_id: 'ai-exec-1',
          related_run_id: null,
          category: 'provider_error',
          severity: 'high',
          status: 'new',
          retryable: true,
          last_error_message: 'Provider timed out while generating response',
          tenant_id: 'tenant-1',
          created_at: '2026-04-02T09:00:00Z',
          updated_at: '2026-04-02T09:05:00Z',
        },
        {
          id: 'failure-2',
          failure_type: 'runtime_error',
          related_request_id: null,
          related_run_id: 'auto-run-1',
          category: 'rule_error',
          severity: 'medium',
          status: 'resolved',
          retryable: false,
          last_error_message: 'Automation condition evaluation failed',
          tenant_id: 'tenant-1',
          created_at: '2026-04-01T09:00:00Z',
          updated_at: '2026-04-01T09:05:00Z',
        },
      ]),
    )
    vi.mocked(intelligenceHubApi.listExecutionsAI).mockReturnValue(
      apiResponse([
        {
          id: 'ai-exec-1',
          status: 'failed',
          source_module: 'communications',
          source_entity_type: 'candidate',
          source_entity_id: 'cand-1',
          retry_count: 1,
        },
      ]),
    )
    vi.mocked(intelligenceHubApi.listExecutionsAutomation).mockReturnValue(
      apiResponse([
        {
          id: 'auto-run-1',
          status: 'failed',
          source_module: 'pipeline',
          source_entity_type: 'application',
          source_entity_id: 'app-1',
          retry_count: 0,
        },
      ]),
    )

    renderHub('/intelligence/failures')

    expect(await screen.findByText('failure-1')).toBeInTheDocument()
    expect(await screen.findByText('failure-2')).toBeInTheDocument()

    fireEvent.change(screen.getByTestId('failure-filter-classification'), { target: { value: 'terminal' } })

    await waitFor(() => {
      expect(screen.getByText('failure-2')).toBeInTheDocument()
      expect(screen.queryByText('failure-1')).not.toBeInTheDocument()
    })
  })

  it('shows the failures empty state when no failure data exists', async () => {
    renderHub('/intelligence/failures')
    expect(await screen.findByText('Failures')).toBeInTheDocument()
    expect(await screen.findByText('No failures detected')).toBeInTheDocument()
  })

  it('shows the failures loading state while the list is pending', async () => {
    vi.mocked(intelligenceHubApi.listFailures).mockReturnValue(pendingResponse() as any)

    renderHub('/intelligence/failures')

    expect(await screen.findByText('Loading failures…')).toBeInTheDocument()
  })

  it('shows a failures error state when the backend fails', async () => {
    vi.mocked(intelligenceHubApi.listFailures).mockRejectedValue(new Error('Failure endpoint failed'))

    renderHub('/intelligence/failures')

    expect(await screen.findByText('Failures could not be loaded.')).toBeInTheDocument()
    expect(await screen.findByText('Failure endpoint failed')).toBeInTheDocument()
  })

  it('retries a retryable failure through the backend retry endpoint', async () => {
    vi.mocked(intelligenceHubApi.listFailures).mockReturnValue(
      apiResponse([
        {
          id: 'failure-1',
          failure_type: 'runtime_error',
          related_request_id: 'ai-exec-1',
          related_run_id: null,
          category: 'provider_error',
          severity: 'high',
          status: 'new',
          retryable: true,
          max_retries: 2,
          next_retry_at: null,
          operator_notes: '',
          last_error_message: 'Provider timed out while generating response',
          tenant_id: 'tenant-1',
          created_at: '2026-04-02T09:00:00Z',
          updated_at: '2026-04-02T09:05:00Z',
        },
      ]),
    )
    vi.mocked(intelligenceHubApi.listExecutionsAI).mockReturnValue(
      apiResponse([
        {
          id: 'ai-exec-1',
          status: 'failed',
          source_module: 'communications',
          source_entity_type: 'candidate',
          source_entity_id: 'cand-1',
          retry_count: 1,
        },
      ]),
    )
    vi.mocked(intelligenceHubApi.getExecutionDetail).mockReturnValue(
      apiResponse({
        execution_type: 'ai',
        payload: {
          id: 'ai-exec-1',
          status: 'failed',
          source_module: 'communications',
          source_entity_type: 'candidate',
          source_entity_id: 'cand-1',
          context_snapshot_json: { candidate_id: 'cand-1' },
          result: { execution_ms: 900 },
        },
      }),
    )

    renderHub('/intelligence/failures')

    fireEvent.click(await screen.findByText('failure-1'))
    fireEvent.click(await screen.findByRole('button', { name: 'Retry failure' }))

    await waitFor(() => {
      expect(intelligenceHubApi.retryFailure).toHaveBeenCalledWith('failure-1')
    })
  })

  it('loads prompts from the real prompt endpoint', async () => {
    vi.mocked(intelligenceHubApi.listPrompts).mockReturnValue(
      apiResponse([
        {
          id: 'prompt-1',
          prompt_title: 'Candidate follow-up prompt',
          prompt_key: 'candidate_followup_prompt',
          module_scope: 'communications',
          use_case_key: 'followup_recommendation',
          status: 'active',
          active_version_id: 'version-2',
          created_by: 'user-1',
          updated_at: '2026-04-02T10:00:00Z',
          versions: [
            { id: 'version-2', version_number: 2, status: 'active' },
            { id: 'version-1', version_number: 1, status: 'archived' },
          ],
          scopes: [],
        },
      ]),
    )

    renderHub('/intelligence/prompts')

    expect(await screen.findByText('Prompts')).toBeInTheDocument()
    expect(await screen.findByText('Candidate follow-up prompt')).toBeInTheDocument()
    expect(await screen.findByText('candidate_followup_prompt')).toBeInTheDocument()
    expect((await screen.findAllByText('communications')).length).toBeGreaterThan(0)
  })

  it('opens prompt detail with real version and schema data', async () => {
    vi.mocked(intelligenceHubApi.listPrompts).mockReturnValue(
      apiResponse([
        {
          id: 'prompt-1',
          prompt_title: 'Candidate follow-up prompt',
          prompt_key: 'candidate_followup_prompt',
          module_scope: 'communications',
          use_case_key: 'followup_recommendation',
          status: 'active',
          active_version_id: 'version-2',
          updated_at: '2026-04-02T10:00:00Z',
          versions: [{ id: 'version-2', version_number: 2, status: 'active' }],
          scopes: [],
        },
      ]),
    )
    vi.mocked(intelligenceHubApi.getPrompt).mockReturnValue(
      apiResponse({
        id: 'prompt-1',
        prompt_title: 'Candidate follow-up prompt',
        prompt_key: 'candidate_followup_prompt',
        description: 'Drafts recruiter follow-up prompts.',
        module_scope: 'communications',
        use_case_key: 'followup_recommendation',
        status: 'active',
        active_version_id: 'version-2',
        approval_required: true,
        tenant_override_allowed: false,
        safety_notes: 'Never send automatically.',
        owner_role: 'hr_manager',
        tenant_id: 'tenant-1',
        metadata: { registry: 'default' },
        versions: [
          {
            id: 'version-2',
            version_number: 2,
            status: 'active',
            approval_required: true,
            approved_at: '2026-04-02T09:00:00Z',
            variables_schema_json: { candidate_name: { type: 'string' } },
            expected_output_schema_json: { summary: { type: 'string' } },
            validation_rules_json: { required: ['summary'] },
            system_prompt: 'You are a recruiter assistant.',
            user_prompt_template: 'Draft a follow-up for {{candidate_name}}.',
          },
          {
            id: 'version-1',
            version_number: 1,
            status: 'archived',
            approval_required: true,
          },
        ],
        scopes: [{ id: 'scope-1', module_scope: 'communications', use_case_key: 'followup_recommendation', entity_type: 'candidate', is_active: true }],
      }),
    )

    renderHub('/intelligence/prompts')

    fireEvent.click(await screen.findByText('Candidate follow-up prompt'))

    expect(await screen.findByText('Prompt Detail')).toBeInTheDocument()
    expect(await screen.findByText('Variables / Schema Info')).toBeInTheDocument()
    expect(await screen.findByText('Active Version Prompts')).toBeInTheDocument()
    expect(await screen.findByText('Drafts recruiter follow-up prompts.')).toBeInTheDocument()
  })

  it('filters prompts client-side', async () => {
    vi.mocked(intelligenceHubApi.listPrompts).mockReturnValue(
      apiResponse([
        {
          id: 'prompt-1',
          prompt_title: 'Candidate follow-up prompt',
          prompt_key: 'candidate_followup_prompt',
          module_scope: 'communications',
          use_case_key: 'followup_recommendation',
          status: 'active',
          active_version_id: 'version-2',
          versions: [{ id: 'version-2', version_number: 2, status: 'active' }],
        },
        {
          id: 'prompt-2',
          prompt_title: 'Interview summary prompt',
          prompt_key: 'interview_summary_prompt',
          module_scope: 'interviews',
          use_case_key: 'interview_summary',
          status: 'draft',
          active_version_id: null,
          versions: [],
        },
      ]),
    )

    renderHub('/intelligence/prompts')

    expect(await screen.findByText('Candidate follow-up prompt')).toBeInTheDocument()
    expect(await screen.findByText('Interview summary prompt')).toBeInTheDocument()

    fireEvent.change(screen.getByTestId('prompt-filter-module'), { target: { value: 'interviews' } })

    await waitFor(() => {
      expect(screen.getByText('Interview summary prompt')).toBeInTheDocument()
      expect(screen.queryByText('Candidate follow-up prompt')).not.toBeInTheDocument()
    })
  })

  it('shows the prompts empty state when no prompts exist', async () => {
    renderHub('/intelligence/prompts')

    expect(await screen.findByText('Prompts')).toBeInTheDocument()
    expect(await screen.findByText('No prompts registered yet.')).toBeInTheDocument()
  })

  it('shows the prompts loading state while the list is pending', async () => {
    vi.mocked(intelligenceHubApi.listPrompts).mockReturnValue(pendingResponse() as any)

    renderHub('/intelligence/prompts')

    expect(await screen.findByText('Loading prompts…')).toBeInTheDocument()
  })

  it('shows an error state when prompts fail to load', async () => {
    vi.mocked(intelligenceHubApi.listPrompts).mockRejectedValue(new Error('Prompt endpoint failed'))
    renderHub('/intelligence/prompts')

    expect(await screen.findByText('Prompts could not be loaded.')).toBeInTheDocument()
    expect(await screen.findByText('Prompt endpoint failed')).toBeInTheDocument()
  })

  it('loads settings from the real settings endpoint', async () => {
    vi.mocked(intelligenceHubApi.listProviders).mockReturnValue(
      apiResponse([
        { id: 'provider-1', provider_name: 'OpenAI Primary', provider_key: 'openai_primary', status: 'active' },
      ]),
    )
    vi.mocked(intelligenceHubApi.listConnectors).mockReturnValue(
      apiResponse([
        { id: 'connector-1', module_code: 'communications', status: 'active', version_tag: 'v1' },
      ]),
    )
    vi.mocked(intelligenceHubApi.getSettings).mockReturnValue(
      apiResponse({
        tenant_id: 'tenant-1',
        ai_enabled: true,
        automation_enabled: true,
        default_approval_mode: 'suggestion_only',
        allowed_provider_ids_json: ['provider-1'],
        feature_flags_json: {},
        notification_preferences_json: {},
        retry_policy_overrides_json: {},
        connector_enablement_json: { communications: true },
        visibility_permissions_json: {},
        updated_at: '2026-04-02T12:00:00Z',
      }),
    )

    renderHub('/intelligence/settings')

    expect(await screen.findByText('Tenant Intelligence Settings')).toBeInTheDocument()
    expect(await screen.findByText('suggestion only')).toBeInTheDocument()
    expect(await screen.findByText('Provider Policy')).toBeInTheDocument()
    expect(await screen.findByText('Connector Enablement')).toBeInTheDocument()
    expect(await screen.findByText('OpenAI Primary')).toBeInTheDocument()
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
