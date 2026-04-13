"""
Automation Maturity Engine
--------------------------
Computes multi-dimensional maturity scores for tenants, produces module
breakdowns, team adoption metrics, recommendations, and roadmaps.

Score dimensions (0–100 each):
  coverage     – breadth of automation across modules / processes
  adoption     – how actively teams use automation
  governance   – approval, versioning, sandbox, permission controls
  reliability  – failure rate, recovery health, observability
  intelligence – AI suggestions, playbook recommendations
  operating    – runtime health, registry, workload balance
  business_impact – executions, SLA results, effort reduction

Overall = weighted average → maps to MaturityLevel (Manual–Autonomous).
"""
import logging
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Weights
# ---------------------------------------------------------------------------
DIMENSION_WEIGHTS = {
    'coverage':       0.20,
    'adoption':       0.20,
    'governance':     0.15,
    'reliability':    0.15,
    'intelligence':   0.15,
    'operating':      0.10,
    'business_impact':0.05,
}

# Expected "full" values for normalisation (anything ≥ max → 100 pts)
NORMS = {
    'workflows':         20,
    'playbook_installs': 10,
    'sla_policies':       5,
    'notification_rules': 10,
    'task_rules':         10,
    'executions_30d':    200,
    'ai_suggestions':     30,
    'sandbox_runs':       10,
    'change_sets':        10,
    'perm_policies':       5,
}

# Module → trigger_event prefix mapping
MODULE_PREFIXES = {
    'candidates':    ['candidate_', 'application_'],
    'jobs':          ['job_'],
    'pipeline':      ['pipeline_', 'stage_'],
    'interviews':    ['interview_'],
    'offers':        ['offer_'],
    'agencies':      ['agency_'],
    'tasks':         ['task_'],
    'sla':           ['sla_'],
    'notifications': ['notification_'],
    'cross_module':  ['cross_', 'multi_'],
}

# Roadmap step templates
_ROADMAP_STEPS: dict[tuple, list[dict]] = {
    ('manual', 'assisted'): [
        {'step': 1, 'action': 'Enable 3 starter playbooks from the Playbook Marketplace',             'effort': 'Low',    'timeline_days': 7},
        {'step': 2, 'action': 'Create a candidate follow-up workflow with email trigger',              'effort': 'Low',    'timeline_days': 7},
        {'step': 3, 'action': 'Activate SLA reminder rules for active pipeline stages',               'effort': 'Low',    'timeline_days': 14},
        {'step': 4, 'action': 'Configure basic notification templates for key recruiter events',       'effort': 'Medium', 'timeline_days': 14},
    ],
    ('assisted', 'structured'): [
        {'step': 1, 'action': 'Expand automation to interviews and offers modules',                    'effort': 'Medium', 'timeline_days': 21},
        {'step': 2, 'action': 'Enable task orchestration for critical hiring-stage transitions',       'effort': 'Medium', 'timeline_days': 14},
        {'step': 3, 'action': 'Standardise on workflow templates and enable analytics tracking',       'effort': 'Low',    'timeline_days': 14},
        {'step': 4, 'action': 'Set up SLA policies for every key hiring stage',                       'effort': 'Medium', 'timeline_days': 21},
        {'step': 5, 'action': 'Instrument notification rules across all active modules',               'effort': 'Low',    'timeline_days': 7},
    ],
    ('structured', 'optimized'): [
        {'step': 1, 'action': 'Enable governance approvals for all critical and high-priority workflows', 'effort': 'Medium', 'timeline_days': 14},
        {'step': 2, 'action': 'Run sandbox test simulations before deploying workflow changes',           'effort': 'Medium', 'timeline_days': 7},
        {'step': 3, 'action': 'Activate Change Impact Analysis for every workflow version increment',     'effort': 'Low',    'timeline_days': 7},
        {'step': 4, 'action': 'Configure Observability Center with anomaly detection thresholds',         'effort': 'High',   'timeline_days': 21},
        {'step': 5, 'action': 'Establish Recovery Policies (retry + fallback) for critical workflows',   'effort': 'High',   'timeline_days': 21},
        {'step': 6, 'action': 'Configure Permission Policies per role / team for automation actions',     'effort': 'Medium', 'timeline_days': 14},
    ],
    ('optimized', 'autonomous'): [
        {'step': 1, 'action': 'Review and adopt AI Recommendations on a weekly cadence',              'effort': 'Low',    'timeline_days': 30},
        {'step': 2, 'action': 'Enable cross-module automation chains for end-to-end hiring flows',    'effort': 'High',   'timeline_days': 45},
        {'step': 3, 'action': 'Activate Automation OS controls for system-wide orchestration',        'effort': 'High',   'timeline_days': 30},
        {'step': 4, 'action': 'Set up advanced analytics dashboards and optimization feedback loops', 'effort': 'Medium', 'timeline_days': 21},
        {'step': 5, 'action': 'Establish a continuous automation improvement governance process',     'effort': 'Medium', 'timeline_days': 30},
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _norm(value: int, maximum: int) -> float:
    """Normalise a raw count to 0–100, capped at maximum."""
    return min(value / max(maximum, 1), 1.0) * 100.0


def _score_to_level(score: float) -> str:
    if score <= 20:   return 'manual'
    if score <= 40:   return 'assisted'
    if score <= 60:   return 'structured'
    if score <= 80:   return 'optimized'
    return 'autonomous'


def _round2(v: float) -> Decimal:
    return Decimal(str(round(v, 2)))


# ---------------------------------------------------------------------------
# Data collection helper (all queries centralised here)
# ---------------------------------------------------------------------------

def _collect_tenant_data(tenant_id) -> dict:
    """Run all DB queries once and return a compact data dict."""
    from apps.orchestration_center.models import Workflow, WorkflowExecution, AISuggestion
    from apps.automation_playbooks.models import AutomationPlaybookInstall, InstallStatus
    from apps.automation_sla.models import WorkflowSLAPolicy
    from apps.automation_tasks.models import WorkflowTaskRule
    from apps.automation_notifications.models import WorkflowNotificationRule
    from apps.automation_permissions.models import WorkflowPermissionPolicy
    from apps.automation_sandbox.models import WorkflowSandboxRun
    from apps.automation_change_impact.models import WorkflowChangeSet
    from apps.automation_recovery.models import WorkflowRecoveryCase, WorkflowDeadLetterItem, RecoveryStatus
    from apps.automation_observability.models import WorkflowAnomaly, WorkflowDependencyHealth, DependencyStatus

    now   = timezone.now()
    d30   = now - timedelta(days=30)
    tid   = tenant_id

    wf_qs  = Workflow.objects.filter(tenant_id=tid, is_deleted=False)
    exec_qs = WorkflowExecution.objects.filter(tenant_id=tid)

    total_wf       = wf_qs.count()
    active_wf      = wf_qs.filter(is_active=True, status='active').count()
    critical_wf    = wf_qs.filter(is_critical=True).count()
    approved_wf    = wf_qs.filter(require_approval=True).count()
    dry_run_wf     = wf_qs.filter(dry_run_mode=True).count()

    exec_30d       = exec_qs.filter(started_at__gte=d30).count()
    exec_success   = exec_qs.filter(started_at__gte=d30, status='completed').count()
    exec_failed    = exec_qs.filter(started_at__gte=d30, status='failed').count()

    playbook_installs = AutomationPlaybookInstall.objects.filter(
        tenant_id=tid, install_status=InstallStatus.COMPLETED, is_deleted=False
    ).count()

    sla_active     = WorkflowSLAPolicy.objects.filter(tenant_id=tid, is_active=True, is_deleted=False).count()
    task_rules     = WorkflowTaskRule.objects.filter(tenant_id=tid, is_active=True, is_deleted=False).count()
    notif_rules    = WorkflowNotificationRule.objects.filter(tenant_id=tid, is_active=True, is_deleted=False).count()
    perm_policies  = WorkflowPermissionPolicy.objects.filter(tenant_id=tid, is_active=True, is_deleted=False).count()
    sandbox_runs   = WorkflowSandboxRun.objects.filter(tenant_id=tid, created_at__gte=d30, is_deleted=False).count()
    change_sets    = WorkflowChangeSet.objects.filter(tenant_id=tid, created_at__gte=d30, is_deleted=False).count()

    ai_total    = AISuggestion.objects.filter(tenant_id=tid, is_deleted=False).count()
    ai_accepted = AISuggestion.objects.filter(
        tenant_id=tid, is_deleted=False, status__in=['approved', 'applied', 'converted']
    ).count()

    recovery_resolved  = WorkflowRecoveryCase.objects.filter(tenant_id=tid, recovery_status=RecoveryStatus.RESOLVED).count()
    recovery_total     = WorkflowRecoveryCase.objects.filter(tenant_id=tid).count()
    dead_letter_pending= WorkflowDeadLetterItem.objects.filter(tenant_id=tid, status='pending', is_deleted=False).count()

    anomaly_open = WorkflowAnomaly.objects.filter(tenant_id=tid, status='open').count()
    dep_healthy  = WorkflowDependencyHealth.objects.filter(
        tenant_id=tid, status=DependencyStatus.HEALTHY
    ).count()
    dep_total    = WorkflowDependencyHealth.objects.filter(tenant_id=tid).count()

    # Modules covered: count distinct trigger_event prefixes present
    trigger_events = list(wf_qs.filter(is_active=True).values_list('trigger_event', flat=True))
    modules_covered = 0
    for module, prefixes in MODULE_PREFIXES.items():
        if any(any(te.startswith(pfx) for pfx in prefixes) for te in trigger_events):
            modules_covered += 1

    # Unique workflow creators (proxy for "active automation users")
    unique_creators = wf_qs.filter(is_active=True).values('created_by').distinct().count()

    return {
        'total_wf': total_wf,
        'active_wf': active_wf,
        'critical_wf': critical_wf,
        'approved_wf': approved_wf,
        'dry_run_wf': dry_run_wf,
        'exec_30d': exec_30d,
        'exec_success': exec_success,
        'exec_failed': exec_failed,
        'playbook_installs': playbook_installs,
        'sla_active': sla_active,
        'task_rules': task_rules,
        'notif_rules': notif_rules,
        'perm_policies': perm_policies,
        'sandbox_runs': sandbox_runs,
        'change_sets': change_sets,
        'ai_total': ai_total,
        'ai_accepted': ai_accepted,
        'recovery_resolved': recovery_resolved,
        'recovery_total': recovery_total,
        'dead_letter_pending': dead_letter_pending,
        'anomaly_open': anomaly_open,
        'dep_healthy': dep_healthy,
        'dep_total': dep_total,
        'modules_covered': modules_covered,
        'unique_creators': unique_creators,
        'trigger_events': trigger_events,
    }


# ---------------------------------------------------------------------------
# 1. Coverage Score
# ---------------------------------------------------------------------------

def calculate_coverage_score(d: dict) -> float:
    wf_s      = _norm(d['active_wf'],        NORMS['workflows'])
    pb_s      = _norm(d['playbook_installs'], NORMS['playbook_installs'])
    sla_s     = _norm(d['sla_active'],        NORMS['sla_policies'])
    notif_s   = _norm(d['notif_rules'],       NORMS['notification_rules'])
    task_s    = _norm(d['task_rules'],        NORMS['task_rules'])
    module_s  = _norm(d['modules_covered'],   len(MODULE_PREFIXES))
    return (wf_s * 0.35 + pb_s * 0.20 + sla_s * 0.10
            + notif_s * 0.10 + task_s * 0.10 + module_s * 0.15)


# ---------------------------------------------------------------------------
# 2. Adoption Score
# ---------------------------------------------------------------------------

def calculate_adoption_score(d: dict) -> float:
    exec_s   = _norm(d['exec_30d'],     NORMS['executions_30d'])
    # AI review rate
    ai_rate  = (d['ai_accepted'] / max(d['ai_total'], 1)) * 100
    sandbox_s= _norm(d['sandbox_runs'], NORMS['sandbox_runs'])
    user_s   = _norm(d['unique_creators'], 10)
    return (exec_s * 0.50 + ai_rate * 0.20 + sandbox_s * 0.15 + user_s * 0.15)


# ---------------------------------------------------------------------------
# 3. Governance Score
# ---------------------------------------------------------------------------

def calculate_governance_score(d: dict) -> float:
    # Approval rate among critical/active workflows
    approval_rate = (
        (d['approved_wf'] / max(d['critical_wf'], d['active_wf'], 1)) * 100
        if d['active_wf'] else 0
    )
    perm_s    = _norm(d['perm_policies'],  NORMS['perm_policies'])
    sandbox_s = _norm(d['sandbox_runs'],   NORMS['sandbox_runs'])
    change_s  = _norm(d['change_sets'],    NORMS['change_sets'])
    return (min(approval_rate, 100) * 0.35 + perm_s * 0.25
            + sandbox_s * 0.20 + change_s * 0.20)


# ---------------------------------------------------------------------------
# 4. Reliability Score
# ---------------------------------------------------------------------------

def calculate_reliability_score(d: dict) -> float:
    # Execution success rate
    exec_total = d['exec_30d']
    success_rate = (d['exec_success'] / max(exec_total, 1)) * 100 if exec_total else 50.0
    # Recovery effectiveness
    rec_rate = (
        (d['recovery_resolved'] / max(d['recovery_total'], 1)) * 100
        if d['recovery_total'] else 80.0   # no cases → neutral
    )
    # Dead letter penalty: cap at 50 points penalty for >10 items
    dl_penalty = min(d['dead_letter_pending'] * 5, 50)
    # Anomaly penalty
    anomaly_penalty = min(d['anomaly_open'] * 3, 30)
    # Dep health
    dep_rate = (d['dep_healthy'] / max(d['dep_total'], 1)) * 100 if d['dep_total'] else 80.0

    base = (success_rate * 0.40 + rec_rate * 0.30 + dep_rate * 0.30)
    return max(0.0, base - dl_penalty * 0.10 - anomaly_penalty * 0.10)


# ---------------------------------------------------------------------------
# 5. Intelligence Score
# ---------------------------------------------------------------------------

def calculate_intelligence_score(d: dict) -> float:
    ai_gen_s  = _norm(d['ai_total'],    NORMS['ai_suggestions'])
    ai_rate   = (d['ai_accepted'] / max(d['ai_total'], 1)) * 100
    sandbox_s = _norm(d['sandbox_runs'],NORMS['sandbox_runs'])
    return (ai_gen_s * 0.35 + ai_rate * 0.45 + sandbox_s * 0.20)


# ---------------------------------------------------------------------------
# 6. Operating Score
# ---------------------------------------------------------------------------

def calculate_operating_score(d: dict) -> float:
    active_ratio = (d['active_wf'] / max(d['total_wf'], 1)) * 100 if d['total_wf'] else 0
    dep_rate     = (d['dep_healthy'] / max(d['dep_total'], 1)) * 100 if d['dep_total'] else 80.0
    dry_run_s    = _norm(d['dry_run_wf'], max(d['total_wf'], 1)) * 100 if d['total_wf'] else 0
    return (min(active_ratio, 100) * 0.50 + dep_rate * 0.35 + min(dry_run_s, 100) * 0.15)


# ---------------------------------------------------------------------------
# 7. Business Impact Score
# ---------------------------------------------------------------------------

def calculate_business_impact_score(d: dict) -> float:
    exec_s     = _norm(d['exec_30d'], NORMS['executions_30d'])
    sla_s      = _norm(d['sla_active'], NORMS['sla_policies'])
    task_s     = _norm(d['task_rules'], NORMS['task_rules'])
    success_rate = (d['exec_success'] / max(d['exec_30d'], 1)) * 100 if d['exec_30d'] else 0
    return (exec_s * 0.35 + success_rate * 0.35 + sla_s * 0.15 + task_s * 0.15)


# ---------------------------------------------------------------------------
# 8. Overall Maturity
# ---------------------------------------------------------------------------

def determine_maturity_level(score: float) -> str:
    return _score_to_level(score)


def calculate_overall_maturity(tenant_id) -> dict:
    """
    Main entry point for a full tenant maturity calculation.
    Returns a dict with all dimension scores and overall.
    """
    d = _collect_tenant_data(tenant_id)

    coverage     = calculate_coverage_score(d)
    adoption     = calculate_adoption_score(d)
    governance   = calculate_governance_score(d)
    reliability  = calculate_reliability_score(d)
    intelligence = calculate_intelligence_score(d)
    operating    = calculate_operating_score(d)
    biz_impact   = calculate_business_impact_score(d)

    overall = (
        coverage     * DIMENSION_WEIGHTS['coverage']
        + adoption   * DIMENSION_WEIGHTS['adoption']
        + governance * DIMENSION_WEIGHTS['governance']
        + reliability* DIMENSION_WEIGHTS['reliability']
        + intelligence*DIMENSION_WEIGHTS['intelligence']
        + operating  * DIMENSION_WEIGHTS['operating']
        + biz_impact * DIMENSION_WEIGHTS['business_impact']
    )
    overall = round(min(overall, 100), 2)

    return {
        'tenant_id':       tenant_id,
        'overall':         overall,
        'maturity_level':  determine_maturity_level(overall),
        'coverage':        round(coverage,     2),
        'adoption':        round(adoption,     2),
        'governance':      round(governance,   2),
        'reliability':     round(reliability,  2),
        'intelligence':    round(intelligence, 2),
        'operating':       round(operating,    2),
        'business_impact': round(biz_impact,   2),
        'raw_data':        d,
    }


# ---------------------------------------------------------------------------
# 9. Module Maturity
# ---------------------------------------------------------------------------

def calculate_module_maturity(tenant_id, raw_data: dict | None = None) -> list[dict]:
    """
    Compute maturity for each ModuleScope using workflow + playbook data.
    """
    from apps.orchestration_center.models import Workflow, WorkflowExecution
    from apps.automation_playbooks.models import AutomationPlaybookInstall, AutomationPlaybook, InstallStatus

    if raw_data is None:
        raw_data = _collect_tenant_data(tenant_id)

    wf_qs = Workflow.objects.filter(tenant_id=tenant_id, is_deleted=False, is_active=True)
    trigger_events = raw_data['trigger_events']

    results = []
    for module, prefixes in MODULE_PREFIXES.items():
        # Workflows for this module
        module_wfs = [te for te in trigger_events if any(te.startswith(p) for p in prefixes)]
        wf_count = len(module_wfs)

        # Playbooks for this module
        pb_count = AutomationPlaybookInstall.objects.filter(
            tenant_id=tenant_id,
            install_status=InstallStatus.COMPLETED,
            is_deleted=False,
            playbook__module_scope=module,
        ).count()

        # Coverage: each active workflow adds ~10% up to 100
        coverage_pct = min(wf_count * 10, 100)

        # Governance: approved workflows in this module
        approved = wf_qs.filter(
            require_approval=True,
            trigger_event__in=module_wfs[:50],  # slice for safety
        ).count() if module_wfs else 0
        governance_s = min((approved / max(wf_count, 1)) * 100, 100) if wf_count else 0

        # Reliability: execution success rate for module workflows
        if module_wfs:
            exec_qs = WorkflowExecution.objects.filter(
                tenant_id=tenant_id,
                workflow__trigger_event__in=module_wfs[:50],
            )
            total_exec = exec_qs.count()
            ok_exec    = exec_qs.filter(status='completed').count()
            reliability_s = (ok_exec / max(total_exec, 1)) * 100 if total_exec else 50.0
        else:
            reliability_s = 0.0

        # Module maturity score
        module_score = (
            (coverage_pct * 0.35)
            + (min(wf_count / 5, 1.0) * 100 * 0.25)
            + (governance_s * 0.20)
            + (reliability_s * 0.20)
        )
        module_score = round(min(module_score, 100), 2)

        results.append({
            'module_scope':                 module,
            'maturity_score':               module_score,
            'maturity_level':               determine_maturity_level(module_score),
            'automation_coverage_percent':  round(coverage_pct, 2),
            'workflow_count':               wf_count,
            'playbook_count':               pb_count,
            'reliability_score':            round(reliability_s, 2),
            'governance_score':             round(governance_s, 2),
        })

    results.sort(key=lambda x: x['maturity_score'], reverse=True)
    return results


# ---------------------------------------------------------------------------
# 10. Team Adoption
# ---------------------------------------------------------------------------

def calculate_team_adoption(tenant_id) -> list[dict]:
    """
    Builds per-creator adoption records as a proxy for team adoption.
    Groups workflows by their created_by UUID.
    """
    from apps.orchestration_center.models import Workflow, WorkflowExecution
    from apps.automation_playbooks.models import AutomationPlaybookInstall, InstallStatus

    wf_qs = Workflow.objects.filter(tenant_id=tenant_id, is_deleted=False)
    creators = (
        wf_qs.values('created_by')
        .annotate(
            wf_count=Count('id'),
            approved_count=Count('id', filter=Q(require_approval=True)),
        )
        .order_by('-wf_count')[:20]
    )

    results = []
    for row in creators:
        creator_id = row['created_by']
        if not creator_id:
            continue

        wf_count   = row['wf_count']
        # Executions triggered by this creator's workflows
        exec_count = WorkflowExecution.objects.filter(
            tenant_id=tenant_id,
            workflow__created_by=creator_id,
        ).count()

        pb_count = AutomationPlaybookInstall.objects.filter(
            tenant_id=tenant_id,
            installed_by=creator_id,
            install_status=InstallStatus.COMPLETED,
        ).count()

        # Score: weighted blend of workflow count + execution count + playbook use
        adoption_s = round(min(
            (wf_count / 10) * 40
            + (_norm(exec_count, 50)) * 0.35
            + (_norm(pb_count, 5)) * 0.25,
            100,
        ), 2)

        results.append({
            'team_name':           f'User {str(creator_id)[:8]}',
            'department_id':       None,
            'adoption_score':      adoption_s,
            'active_user_count':   1,
            'workflow_usage_count':wf_count,
            'playbook_usage_count':pb_count,
            'manual_override_count': 0,
        })

    return results


# ---------------------------------------------------------------------------
# 11. Recommendations
# ---------------------------------------------------------------------------

def generate_maturity_recommendations(tenant_id, scores: dict) -> list[dict]:
    """
    Produce actionable recommendations based on lowest-scoring dimensions.
    Returns a list of recommendation dicts (not yet persisted).
    """
    recs: list[dict] = []
    overall = scores['overall']

    def _priority(gap: float) -> str:
        if gap > 60: return 'critical'
        if gap > 40: return 'high'
        if gap > 20: return 'medium'
        return 'low'

    def _add(rec_type, title, description, area, gain, priority):
        recs.append({
            'recommendation_type': rec_type,
            'title': title,
            'description': description,
            'target_area': area,
            'expected_maturity_gain': round(gain, 2),
            'priority': priority,
        })

    cov  = scores['coverage']
    gov  = scores['governance']
    rel  = scores['reliability']
    intel= scores['intelligence']
    adopt= scores['adoption']

    # Coverage recommendations
    if cov < 50:
        _add('increase_coverage',
             'Expand Workflow Coverage Across Modules',
             'Only a fraction of hiring modules are automated. '
             'Activating workflows for interviews, offers, and agencies can significantly '
             'increase your automation coverage score.',
             'Multi-module Coverage', 15.0, _priority(100 - cov))

    if scores['raw_data']['sla_active'] < 3:
        _add('improve_sla_usage',
             'Configure SLA Policies for Key Hiring Stages',
             'SLA automation ensures deadlines are enforced automatically. '
             'Add SLA policies for interview scheduling, offer letters, and pipeline stages.',
             'SLA Engine', 8.0, 'high')

    # Governance recommendations
    if gov < 50:
        _add('improve_governance',
             'Enable Approval Gates for Critical Workflows',
             'Critical workflows are currently running without governance approval gates. '
             'Configure require_approval for high-risk and business-critical workflows.',
             'Governance Controls', 12.0, _priority(100 - gov))

    if scores['raw_data']['sandbox_runs'] < 3:
        _add('strengthen_sandbox_usage',
             'Use Sandbox Testing Before Workflow Deployment',
             'Sandbox testing was used infrequently. '
             'Run sandbox simulations before deploying new or modified workflows to production.',
             'Sandbox Testing', 8.0, 'high')

    if scores['raw_data']['perm_policies'] < 2:
        _add('improve_governance',
             'Configure Permission Policies Per Role',
             'Automation permission policies control who can trigger, modify, or approve workflows. '
             'Set up role-based policies to strengthen governance.',
             'Permission Policies', 6.0, 'medium')

    # Reliability recommendations
    if rel < 60:
        _add('improve_reliability',
             'Address High Failure Rate in Workflow Executions',
             'Your workflow execution failure rate is above acceptable thresholds. '
             'Review failed executions in the Recovery Engine and add fallback rules.',
             'Reliability & Recovery', 10.0, _priority(100 - rel))

    if scores['raw_data']['dead_letter_pending'] > 5:
        _add('improve_reliability',
             'Clear Dead Letter Queue — High Pending Volume',
             f"{scores['raw_data']['dead_letter_pending']} executions are pending in the dead letter queue. "
             'Investigate root causes and resolve or retry each item.',
             'Dead Letter Queue', 7.0, 'critical')

    # Intelligence recommendations
    if intel < 40:
        _add('increase_ai_adoption',
             'Review and Act on AI Automation Suggestions',
             'The system has generated AI suggestions that have not been reviewed or applied. '
             'Regularly reviewing AI recommendations accelerates maturity improvement.',
             'AI Intelligence', 10.0, _priority(100 - intel))

    # Playbooks
    if scores['raw_data']['playbook_installs'] < 3:
        _add('enable_playbooks',
             'Install Pre-Built Automation Playbooks',
             'Playbooks provide enterprise-validated automation patterns out of the box. '
             'Install starter playbooks for candidate nurture, interview scheduling, and onboarding.',
             'Playbook Library', 9.0, 'high')

    # Cross-module
    if scores['raw_data']['modules_covered'] < 4:
        _add('expand_cross_module',
             'Extend Automation Across More Hiring Modules',
             f"Automation currently covers only {scores['raw_data']['modules_covered']} modules. "
             'Expanding to offers, agencies, and cross-module chains boosts overall maturity.',
             'Module Breadth', 12.0, 'high')

    # Adoption
    if adopt < 40:
        _add('increase_coverage',
             'Drive Wider Automation Adoption Across Teams',
             'Automation is concentrated in a small set of users. '
             'Share templates, playbooks, and quick-start guides with all recruiter teams.',
             'Team Adoption', 8.0, 'medium')

    # De-duplicate by type (keep highest priority)
    seen: dict[str, dict] = {}
    for r in recs:
        key = r['recommendation_type']
        if key not in seen or r['priority'] in ('critical', 'high'):
            seen[key] = r
    return list(seen.values())


# ---------------------------------------------------------------------------
# 12. Roadmap Generation
# ---------------------------------------------------------------------------

def generate_maturity_roadmap(tenant_id, current_level: str, target_level: str) -> dict:
    """
    Return a roadmap dict (not yet persisted) for current_level → target_level.
    Builds multi-hop plans (e.g. manual → optimized = 3 sequential hop sets).
    """
    LEVEL_ORDER = ['manual', 'assisted', 'structured', 'optimized', 'autonomous']
    try:
        src_idx = LEVEL_ORDER.index(current_level)
        tgt_idx = LEVEL_ORDER.index(target_level)
    except ValueError:
        src_idx, tgt_idx = 0, 1

    if tgt_idx <= src_idx:
        tgt_idx = min(src_idx + 1, len(LEVEL_ORDER) - 1)

    # Flatten steps across all hops
    all_steps: list[dict] = []
    total_days = 0
    step_num = 1
    for i in range(src_idx, tgt_idx):
        hop_key = (LEVEL_ORDER[i], LEVEL_ORDER[i + 1])
        hop_steps = _ROADMAP_STEPS.get(hop_key, [])
        for s in hop_steps:
            all_steps.append({**s, 'step': step_num, 'from_level': LEVEL_ORDER[i], 'to_level': LEVEL_ORDER[i + 1]})
            total_days += s.get('timeline_days', 14)
            step_num += 1

    corrected_target = LEVEL_ORDER[tgt_idx]
    roadmap_name = (
        f'Maturity Journey: {LEVEL_ORDER[src_idx].title()} → {corrected_target.title()}'
    )

    return {
        'tenant_id':             tenant_id,
        'roadmap_name':          roadmap_name,
        'current_level':         LEVEL_ORDER[src_idx],
        'target_level':          corrected_target,
        'roadmap_steps':         all_steps,
        'expected_timeline_days':total_days,
    }


# ---------------------------------------------------------------------------
# 13. Business Transformation Metrics
# ---------------------------------------------------------------------------

def track_transformation_metrics(tenant_id) -> list[dict]:
    """
    Derive business transformation metrics for key processes.
    """
    from apps.orchestration_center.models import WorkflowExecution
    from apps.automation_sla.models import WorkflowSLAPolicy
    from django.utils import timezone

    today   = timezone.now().date()
    d30     = timezone.now() - timedelta(days=30)
    d60     = timezone.now() - timedelta(days=60)

    processes = [
        'Candidate Pipeline',
        'Interview Scheduling',
        'Offer Management',
        'Task Automation',
        'SLA Enforcement',
    ]

    exec_30 = WorkflowExecution.objects.filter(tenant_id=tenant_id, started_at__gte=d30).count()
    exec_60 = WorkflowExecution.objects.filter(
        tenant_id=tenant_id, started_at__gte=d60, started_at__lt=d30
    ).count()
    sla_count = WorkflowSLAPolicy.objects.filter(tenant_id=tenant_id, is_active=True, is_deleted=False).count()

    # Growth from prior period (proxy for effort reduction)
    growth = ((exec_30 - exec_60) / max(exec_60, 1)) * 100 if exec_60 else 0
    effort_reduction  = min(max(growth * 0.5, 0), 85)
    response_improve  = min(sla_count * 5, 60)
    sla_improve       = min(sla_count * 8, 70)
    usage_pct         = min((exec_30 / max(NORMS['executions_30d'], 1)) * 100, 100)

    metrics = []
    for i, process in enumerate(processes):
        factor = 1.0 - i * 0.10  # slight variation per process
        metrics.append({
            'tenant_id':                        tenant_id,
            'metric_date':                      today,
            'process_name':                     process,
            'manual_effort_reduction_percent':  round(effort_reduction * factor, 2),
            'response_time_improvement_percent':round(response_improve * factor, 2),
            'sla_improvement_percent':          round(sla_improve * factor, 2),
            'automation_usage_percent':         round(usage_pct * factor, 2),
            'executions_this_period':           exec_30,
            'baseline_executions':              exec_60,
        })
    return metrics


# ---------------------------------------------------------------------------
# 14. Full Assessment Persistence
# ---------------------------------------------------------------------------

@transaction.atomic
def run_full_assessment(tenant_id) -> 'AutomationMaturityAssessment':  # type: ignore[name-defined]
    """
    Run a complete maturity assessment, persist all models, and return the
    AutomationMaturityAssessment instance.
    """
    from apps.automation_maturity.models import (
        AutomationMaturityAssessment,
        AutomationModuleMaturity,
        AutomationTeamAdoption,
        AutomationMaturityRecommendation,
        AutomationBusinessTransformationMetric,
        RecommendationStatus,
    )
    from django.utils import timezone

    today = timezone.now().date()

    # ── Overall scores ──────────────────────────────────────────────────
    scores = calculate_overall_maturity(tenant_id)
    raw    = scores['raw_data']

    assessment = AutomationMaturityAssessment.objects.create(
        tenant_id             = tenant_id,
        assessment_date       = today,
        overall_maturity_score= _round2(scores['overall']),
        maturity_level        = scores['maturity_level'],
        coverage_score        = _round2(scores['coverage']),
        adoption_score        = _round2(scores['adoption']),
        governance_score      = _round2(scores['governance']),
        reliability_score     = _round2(scores['reliability']),
        intelligence_score    = _round2(scores['intelligence']),
        operating_score       = _round2(scores['operating']),
        business_impact_score = _round2(scores['business_impact']),
        score_breakdown       = {k: v for k, v in scores.items() if k != 'raw_data'},
    )

    # ── Module maturity ─────────────────────────────────────────────────
    module_results = calculate_module_maturity(tenant_id, raw_data=raw)
    for mr in module_results:
        AutomationModuleMaturity.objects.create(
            tenant_id                  = tenant_id,
            assessment                 = assessment,
            module_scope               = mr['module_scope'],
            maturity_score             = _round2(mr['maturity_score']),
            maturity_level             = mr['maturity_level'],
            automation_coverage_percent= _round2(mr['automation_coverage_percent']),
            workflow_count             = mr['workflow_count'],
            playbook_count             = mr['playbook_count'],
            reliability_score          = _round2(mr['reliability_score']),
            governance_score           = _round2(mr['governance_score']),
        )

    # ── Team adoption ────────────────────────────────────────────────────
    team_results = calculate_team_adoption(tenant_id)
    for tr in team_results:
        AutomationTeamAdoption.objects.create(
            tenant_id            = tenant_id,
            assessment           = assessment,
            team_name            = tr['team_name'],
            department_id        = tr['department_id'],
            adoption_score       = _round2(tr['adoption_score']),
            active_user_count    = tr['active_user_count'],
            workflow_usage_count = tr['workflow_usage_count'],
            playbook_usage_count = tr['playbook_usage_count'],
            manual_override_count= tr['manual_override_count'],
        )

    # ── Recommendations ──────────────────────────────────────────────────
    recs = generate_maturity_recommendations(tenant_id, scores)
    for r in recs:
        # Upsert by type — update existing new/acknowledged ones
        AutomationMaturityRecommendation.objects.update_or_create(
            tenant_id          = tenant_id,
            recommendation_type= r['recommendation_type'],
            status__in         = [RecommendationStatus.NEW, RecommendationStatus.ACKNOWLEDGED],
            defaults={
                'title':                  r['title'],
                'description':            r['description'],
                'target_area':            r['target_area'],
                'expected_maturity_gain': _round2(r['expected_maturity_gain']),
                'priority':               r['priority'],
                'status':                 RecommendationStatus.NEW,
            },
        )

    # ── Transformation metrics ───────────────────────────────────────────
    metrics = track_transformation_metrics(tenant_id)
    for m in metrics:
        AutomationBusinessTransformationMetric.objects.update_or_create(
            tenant_id   = tenant_id,
            metric_date = m['metric_date'],
            process_name= m['process_name'],
            defaults={
                'manual_effort_reduction_percent':   _round2(m['manual_effort_reduction_percent']),
                'response_time_improvement_percent': _round2(m['response_time_improvement_percent']),
                'sla_improvement_percent':           _round2(m['sla_improvement_percent']),
                'automation_usage_percent':          _round2(m['automation_usage_percent']),
                'executions_this_period':            m['executions_this_period'],
                'baseline_executions':               m['baseline_executions'],
            },
        )

    # ── Observability event ──────────────────────────────────────────────
    _emit_observability_event(
        tenant_id=tenant_id,
        event_type='maturity_assessment_completed',
        severity='info',
        message=(
            f'Maturity assessment: score={scores["overall"]}, '
            f'level={scores["maturity_level"]}'
        ),
    )
    logger.info(
        'Maturity assessment completed for tenant %s: score=%.2f level=%s',
        tenant_id, scores['overall'], scores['maturity_level'],
    )
    return assessment


# ---------------------------------------------------------------------------
# Observability helper
# ---------------------------------------------------------------------------

def _emit_observability_event(tenant_id, event_type: str, severity: str, message: str):
    try:
        from apps.automation_observability.services.workflow_observability_engine import (
            WorkflowObservabilityEngine,
        )
        WorkflowObservabilityEngine.log_event(
            tenant_id=tenant_id,
            workflow_id=None,
            event_type=event_type,
            severity=severity,
            message=message,
        )
    except Exception:  # noqa: BLE001
        pass
