"""
Automation Executive Engine
---------------------------
Produces executive-level KPIs, ROI calculations, risk detection,
opportunity surfacing, and department-level automation maps.

Draws from:
  - Workflow / WorkflowExecution (orchestration_center)
  - AutomationMaturityAssessment (automation_maturity)
  - WorkflowRecoveryCase / WorkflowDeadLetterItem (automation_recovery)
  - WorkflowAnomaly / WorkflowObservabilityEvent (automation_observability)
  - WorkflowSLAPolicy (automation_sla)
  - AutomationPlaybookInstall (automation_playbooks)
  - WorkflowPermissionPolicy (automation_permissions)
"""
import logging
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Q, Avg
from django.utils import timezone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Average minutes saved per successful automated execution
MINUTES_SAVED_PER_EXEC = 3

# Assumed hourly labour cost (USD) for ROI calculation
HOURLY_LABOUR_COST_USD = 25.0

# Department → module trigger prefix mapping
DEPARTMENT_MODULE_MAP = {
    'Recruitment':      ['candidate_', 'application_', 'pipeline_'],
    'HR Operations':    ['task_', 'sla_', 'notification_'],
    'Hiring Managers':  ['interview_', 'offer_', 'stage_'],
    'Agency Relations': ['agency_'],
    'Job Management':   ['job_'],
}


# ---------------------------------------------------------------------------
# Data collector
# ---------------------------------------------------------------------------

def _collect(tenant_id) -> dict:
    from apps.orchestration_center.models import Workflow, WorkflowExecution, AISuggestion
    from apps.automation_maturity.models import (
        AutomationMaturityAssessment, AutomationModuleMaturity,
    )
    from apps.automation_recovery.models import (
        WorkflowRecoveryCase, WorkflowDeadLetterItem, RecoveryStatus,
    )
    from apps.automation_observability.models import (
        WorkflowAnomaly, WorkflowObservabilityEvent, AnomalyStatus,
    )
    from apps.automation_sla.models import WorkflowSLAPolicy
    from apps.automation_permissions.models import WorkflowPermissionPolicy
    from apps.automation_playbooks.models import AutomationPlaybookInstall, InstallStatus
    from apps.automation_maturity.services.automation_maturity_engine import (
        calculate_overall_maturity,
    )

    now  = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    d30  = now - timedelta(days=30)
    d7   = now - timedelta(days=7)
    tid  = tenant_id

    wf_qs    = Workflow.objects.filter(tenant_id=tid, is_deleted=False)
    exec_qs  = WorkflowExecution.objects.filter(tenant_id=tid)

    total_wf  = wf_qs.count()
    active_wf = wf_qs.filter(is_active=True, status='active').count()
    exec_today= exec_qs.filter(started_at__gte=today_start).count()
    ok_today  = exec_qs.filter(started_at__gte=today_start, status='completed').count()
    exec_30d  = exec_qs.filter(started_at__gte=d30).count()
    ok_30d    = exec_qs.filter(started_at__gte=d30, status='completed').count()
    fail_30d  = exec_qs.filter(started_at__gte=d30, status='failed').count()
    fail_7d   = exec_qs.filter(started_at__gte=d7, status='failed').count()
    fail_prev = exec_qs.filter(started_at__gte=d30, started_at__lt=d7, status='failed').count()

    sla_active   = WorkflowSLAPolicy.objects.filter(tenant_id=tid, is_active=True, is_deleted=False).count()
    perm_policies= WorkflowPermissionPolicy.objects.filter(tenant_id=tid, is_active=True, is_deleted=False).count()
    pb_installs  = AutomationPlaybookInstall.objects.filter(
        tenant_id=tid, install_status=InstallStatus.COMPLETED, is_deleted=False
    ).count()

    dead_letter  = WorkflowDeadLetterItem.objects.filter(tenant_id=tid, status='pending', is_deleted=False).count()
    anomaly_open = WorkflowAnomaly.objects.filter(tenant_id=tid, status=AnomalyStatus.OPEN).count()
    critical_events = WorkflowObservabilityEvent.objects.filter(
        tenant_id=tid, severity='critical', created_at__gte=d7
    ).count()

    # Latest maturity assessment
    latest_maturity = (
        AutomationMaturityAssessment.objects
        .filter(tenant_id=tid, is_deleted=False)
        .order_by('-assessment_date')
        .first()
    )
    maturity_level  = latest_maturity.maturity_level if latest_maturity else 'manual'
    biz_impact_score= float(latest_maturity.business_impact_score) if latest_maturity else 0.0
    coverage_score  = float(latest_maturity.coverage_score) if latest_maturity else 0.0

    # Module maturity scores for weakest-module detection
    module_scores = []
    if latest_maturity:
        module_scores = list(
            AutomationModuleMaturity.objects
            .filter(tenant_id=tid, assessment=latest_maturity, is_deleted=False)
            .values('module_scope', 'maturity_score', 'workflow_count')
        )

    # AI suggestions
    ai_pending = AISuggestion.objects.filter(
        tenant_id=tid, status='pending', is_deleted=False
    ).count()

    # Trigger events for department mapping
    trigger_events = list(
        wf_qs.filter(is_active=True).values_list('trigger_event', flat=True)
    )

    # Workflows requiring approval (governance proxy)
    approved_wf = wf_qs.filter(require_approval=True).count()

    return {
        'total_wf': total_wf,
        'active_wf': active_wf,
        'exec_today': exec_today,
        'ok_today': ok_today,
        'exec_30d': exec_30d,
        'ok_30d': ok_30d,
        'fail_30d': fail_30d,
        'fail_7d': fail_7d,
        'fail_prev': fail_prev,
        'sla_active': sla_active,
        'perm_policies': perm_policies,
        'pb_installs': pb_installs,
        'dead_letter': dead_letter,
        'anomaly_open': anomaly_open,
        'critical_events': critical_events,
        'maturity_level': maturity_level,
        'biz_impact_score': biz_impact_score,
        'coverage_score': coverage_score,
        'module_scores': module_scores,
        'ai_pending': ai_pending,
        'trigger_events': trigger_events,
        'approved_wf': approved_wf,
    }


# ---------------------------------------------------------------------------
# 1. Executive Summary
# ---------------------------------------------------------------------------

def generate_executive_summary(tenant_id) -> dict:
    d = _collect(tenant_id)

    # Time saved: each completed execution = MINUTES_SAVED_PER_EXEC minutes
    time_saved_hours = round((d['ok_30d'] * MINUTES_SAVED_PER_EXEC) / 60, 2)

    # Automation coverage: % of modules with ≥1 active workflow
    from apps.automation_maturity.services.automation_maturity_engine import MODULE_PREFIXES
    modules_covered = sum(
        1 for _, prefixes in MODULE_PREFIXES.items()
        if any(any(te.startswith(p) for p in prefixes) for te in d['trigger_events'])
    )
    coverage_pct = round((modules_covered / len(MODULE_PREFIXES)) * 100, 2)

    # Business impact composite (coverage + success_rate proxy)
    success_rate = round((d['ok_30d'] / max(d['exec_30d'], 1)) * 100, 2)
    biz_impact   = round((coverage_pct * 0.4 + success_rate * 0.4 + min(d['sla_active'] * 5, 20) * 1.0) / 1.0, 2)
    biz_impact   = min(biz_impact, 100)

    return {
        'tenant_id':                str(tenant_id),
        'snapshot_date':            timezone.now().date().isoformat(),
        'total_workflows':          d['total_wf'],
        'active_workflows':         d['active_wf'],
        'total_executions_today':   d['exec_today'],
        'successful_executions_today': d['ok_today'],
        'automation_coverage_percent': coverage_pct,
        'automation_maturity_level':d['maturity_level'],
        'time_saved_hours':         time_saved_hours,
        'tasks_automated':          d['ok_30d'],
        'sla_improvement_percent':  min(d['sla_active'] * 8, 70),
        'open_risks':               0,   # filled after detect_operational_risks()
        'open_opportunities':       0,   # filled after generate_opportunities()
        'business_impact_score':    round(biz_impact, 2),
    }


# ---------------------------------------------------------------------------
# 2. ROI Calculation
# ---------------------------------------------------------------------------

def calculate_roi(tenant_id, period: str = 'monthly') -> dict:
    from apps.orchestration_center.models import WorkflowExecution
    from django.utils import timezone

    now = timezone.now()
    if period == 'daily':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end   = now
    elif period == 'weekly':
        start = now - timedelta(days=7)
        end   = now
    elif period == 'yearly':
        start = now - timedelta(days=365)
        end   = now
    else:  # monthly
        start = now - timedelta(days=30)
        end   = now

    exec_qs = WorkflowExecution.objects.filter(
        tenant_id=tenant_id, started_at__gte=start, started_at__lte=end
    )
    total    = exec_qs.count()
    ok_count = exec_qs.filter(status='completed').count()

    hours_saved = round((ok_count * MINUTES_SAVED_PER_EXEC) / 60, 2)
    cost_reduction = round(hours_saved * HOURLY_LABOUR_COST_USD, 2)
    productivity_gain = round((ok_count / max(total, 1)) * 100, 2)

    return {
        'tenant_id':                str(tenant_id),
        'period':                   period,
        'period_start':             start.date().isoformat(),
        'period_end':               end.date().isoformat(),
        'hours_saved':              hours_saved,
        'manual_tasks_reduced':     ok_count,
        'operational_cost_reduction': cost_reduction,
        'productivity_gain_percent':productivity_gain,
        'executions_count':         total,
        'success_rate':             round((ok_count / max(total, 1)) * 100, 2),
    }


# ---------------------------------------------------------------------------
# 3. Operational Risk Detection
# ---------------------------------------------------------------------------

def detect_operational_risks(tenant_id) -> list[dict]:
    d   = _collect(tenant_id)
    risks: list[dict] = []

    def _risk(risk_type, severity, module, title, description, metric_value=None):
        risks.append({
            'tenant_id':       str(tenant_id),
            'risk_type':       risk_type,
            'severity':        severity,
            'affected_module': module,
            'title':           title,
            'description':     description,
            'metric_value':    metric_value or {},
        })

    # ── Failure spike ────────────────────────────────────────────────────
    if d['fail_7d'] > 0:
        spike_ratio = d['fail_7d'] / max(d['fail_prev'], 1)
        if spike_ratio > 2 or d['fail_7d'] > 20:
            severity = 'critical' if spike_ratio > 3 or d['fail_7d'] > 50 else 'high'
            _risk(
                'failure_spike', severity, 'workflows',
                f'Workflow Failure Spike — {d["fail_7d"]} failures in 7 days',
                f'Failure count increased {spike_ratio:.1f}x vs prior period. '
                f'Investigate the Recovery Engine and execution logs.',
                {'failures_7d': d['fail_7d'], 'ratio': round(spike_ratio, 2)},
            )

    # ── Dead letter queue buildup ────────────────────────────────────────
    if d['dead_letter'] > 0:
        severity = 'critical' if d['dead_letter'] > 10 else 'high' if d['dead_letter'] > 5 else 'medium'
        _risk(
            'failure_spike', severity, 'recovery',
            f'Dead Letter Queue: {d["dead_letter"]} unresolved items',
            f'{d["dead_letter"]} executions are stuck in the dead letter queue and require investigation.',
            {'dead_letter_count': d['dead_letter']},
        )

    # ── Governance gap ───────────────────────────────────────────────────
    if d['perm_policies'] < 2:
        _risk(
            'governance_gap', 'high', 'governance',
            'Insufficient Permission Policies Configured',
            'Fewer than 2 permission policies are active. '
            'Automation actions are running without role-based access controls.',
            {'perm_policies': d['perm_policies']},
        )
    if d['approved_wf'] == 0 and d['active_wf'] > 3:
        _risk(
            'governance_gap', 'high', 'governance',
            'No Approval Gates on Active Workflows',
            f'{d["active_wf"]} workflows are active with no approval requirements. '
            'Critical automations should require governance approval.',
            {'active_wf': d['active_wf'], 'approved_wf': 0},
        )

    # ── Manual gap ───────────────────────────────────────────────────────
    low_modules = [
        m['module_scope'] for m in d['module_scores']
        if float(m['maturity_score']) < 25 and m['workflow_count'] == 0
    ]
    if low_modules:
        _risk(
            'manual_gap', 'medium', ', '.join(low_modules[:3]),
            f'{len(low_modules)} Module(s) Fully Manual',
            f'The following modules have zero automation: {", ".join(low_modules[:3])}. '
            'Manual processes here create operational risk and inconsistency.',
            {'manual_modules': low_modules},
        )

    # ── Anomaly buildup ──────────────────────────────────────────────────
    if d['anomaly_open'] > 3:
        severity = 'critical' if d['anomaly_open'] > 10 else 'high'
        _risk(
            'overload_risk', severity, 'observability',
            f'{d["anomaly_open"]} Open Anomalies Detected',
            f'The Observability Engine has flagged {d["anomaly_open"]} open anomalies. '
            'Unresolved anomalies may indicate systemic automation issues.',
            {'anomaly_count': d['anomaly_open']},
        )

    # ── Critical events ──────────────────────────────────────────────────
    if d['critical_events'] > 0:
        _risk(
            'dependency_risk', 'critical', 'system',
            f'{d["critical_events"]} Critical Events in Last 7 Days',
            'Critical severity observability events indicate infrastructure or '
            'dependency failures requiring immediate executive attention.',
            {'critical_event_count': d['critical_events']},
        )

    # ── No SLA coverage ──────────────────────────────────────────────────
    if d['sla_active'] == 0 and d['active_wf'] > 2:
        _risk(
            'manual_gap', 'medium', 'sla',
            'No SLA Policies Configured',
            'Active workflows exist but no SLA policies are configured. '
            'Hiring deadlines and operational SLAs are not enforced.',
            {'sla_active': 0, 'active_wf': d['active_wf']},
        )

    return risks


# ---------------------------------------------------------------------------
# 4. Opportunity Generation
# ---------------------------------------------------------------------------

def generate_opportunities(tenant_id) -> list[dict]:
    d = _collect(tenant_id)
    opps: list[dict] = []

    def _opp(opp_type, module, title, description, impact, priority, source=None):
        opps.append({
            'tenant_id':       str(tenant_id),
            'opportunity_type':opp_type,
            'module':          module,
            'title':           title,
            'description':     description,
            'expected_impact': impact,
            'priority':        priority,
            'source_data':     source or {},
        })

    # ── Manual modules → automate ────────────────────────────────────────
    manual_modules = [
        m['module_scope'] for m in d['module_scores']
        if float(m['maturity_score']) < 25
    ]
    if manual_modules:
        for m in manual_modules[:3]:
            _opp(
                'automate_manual_process', m,
                f'Automate {m.replace("_", " ").title()} Processes',
                f'The {m} module has very low automation maturity. '
                f'Creating basic workflows here could save significant recruiter time.',
                'High time-saving potential — estimated 2–4 hrs/week saved',
                'high' if m in ('interviews', 'offers', 'pipeline') else 'medium',
                {'module_maturity_score': next(
                    (float(ms['maturity_score']) for ms in d['module_scores'] if ms['module_scope'] == m), 0
                )},
            )

    # ── AI suggestions pending ───────────────────────────────────────────
    if d['ai_pending'] > 0:
        _opp(
            'enable_ai', 'ai_engine',
            f'Review {d["ai_pending"]} Pending AI Automation Suggestions',
            f'The AI engine has generated {d["ai_pending"]} automation suggestions that have not yet '
            'been reviewed. Accepting these could improve automation coverage and maturity.',
            'Estimated 5–15 pt maturity score improvement',
            'high' if d['ai_pending'] > 5 else 'medium',
            {'ai_pending_count': d['ai_pending']},
        )

    # ── Low cross-module coverage ────────────────────────────────────────
    from apps.automation_maturity.services.automation_maturity_engine import MODULE_PREFIXES
    covered = sum(
        1 for _, prefixes in MODULE_PREFIXES.items()
        if any(any(te.startswith(p) for p in prefixes) for te in d['trigger_events'])
    )
    if covered < 5:
        _opp(
            'enable_cross_module', 'cross_module',
            'Extend Automation Across More Hiring Modules',
            f'Only {covered} of {len(MODULE_PREFIXES)} modules have automation coverage. '
            'End-to-end hiring automation requires connecting candidates → interviews → offers.',
            'Full pipeline automation reduces time-to-hire by an estimated 30%',
            'critical' if covered < 3 else 'high',
            {'modules_covered': covered, 'total_modules': len(MODULE_PREFIXES)},
        )

    # ── Reliability improvement ──────────────────────────────────────────
    fail_rate = (d['fail_30d'] / max(d['exec_30d'], 1)) * 100
    if fail_rate > 15:
        _opp(
            'improve_reliability', 'recovery',
            'Reduce Workflow Failure Rate',
            f'Current failure rate is {fail_rate:.1f}%. '
            'Configuring fallback rules and retry policies in the Recovery Engine '
            'will reduce failures and improve overall reliability.',
            'Estimated 10–20% improvement in automation reliability',
            'critical' if fail_rate > 30 else 'high',
            {'failure_rate_percent': round(fail_rate, 2)},
        )

    # ── No playbooks ─────────────────────────────────────────────────────
    if d['pb_installs'] < 3:
        _opp(
            'automate_manual_process', 'playbooks',
            'Install Pre-Built Automation Playbooks',
            'Fewer than 3 automation playbooks are installed. '
            'Playbooks provide enterprise-validated automation patterns that can be '
            'deployed quickly without custom workflow development.',
            'Fast deployment of proven automation patterns — weeks not months',
            'high',
            {'installed_playbooks': d['pb_installs']},
        )

    # ── Expand existing workflows ─────────────────────────────────────────
    if d['active_wf'] > 5 and d['sla_active'] < 3:
        _opp(
            'expand_existing_workflow', 'sla',
            'Add SLA Enforcement to Active Workflows',
            f'{d["active_wf"]} workflows are active but only {d["sla_active"]} SLA policies '
            'are configured. Adding SLA rules ensures deadline accountability.',
            'Improved SLA compliance — estimated 15–25% reduction in late-stage delays',
            'medium',
            {'active_wf': d['active_wf'], 'sla_policies': d['sla_active']},
        )

    return opps


# ---------------------------------------------------------------------------
# 5. Department Scores
# ---------------------------------------------------------------------------

def compute_department_scores(tenant_id) -> list[dict]:
    d = _collect(tenant_id)
    results = []

    for dept, prefixes in DEPARTMENT_MODULE_MAP.items():
        dept_triggers = [
            te for te in d['trigger_events']
            if any(te.startswith(p) for p in prefixes)
        ]
        wf_count  = len(dept_triggers)
        coverage  = min(wf_count * 20, 100)  # 5 workflows = 100%
        gap       = round(100 - coverage, 2)

        # Adoption: execution proxy
        from apps.orchestration_center.models import WorkflowExecution
        from django.utils import timezone
        d30 = timezone.now() - timedelta(days=30)
        exec_count = WorkflowExecution.objects.filter(
            tenant_id=tenant_id,
            workflow__trigger_event__in=dept_triggers[:50],
            started_at__gte=d30,
        ).count() if dept_triggers else 0

        adoption = min(round((exec_count / 50) * 100, 2), 100)

        # Maturity: derived from coverage + adoption
        composite = coverage * 0.6 + adoption * 0.4
        if composite <= 20:   level = 'manual'
        elif composite <= 40: level = 'assisted'
        elif composite <= 60: level = 'structured'
        elif composite <= 80: level = 'optimized'
        else:                  level = 'autonomous'

        results.append({
            'tenant_id':          str(tenant_id),
            'snapshot_date':      timezone.now().date().isoformat(),
            'department_name':    dept,
            'automation_coverage':round(coverage, 2),
            'adoption_score':     round(adoption, 2),
            'maturity_level':     level,
            'manual_gap_percent': gap,
            'workflow_count':     wf_count,
            'executions_30d':     exec_count,
        })

    results.sort(key=lambda x: x['automation_coverage'], reverse=True)
    return results


# ---------------------------------------------------------------------------
# 6. Executive Insights (text-based narrative)
# ---------------------------------------------------------------------------

def generate_executive_insights(tenant_id) -> list[str]:
    d    = _collect(tenant_id)
    insights: list[str] = []

    # Maturity narrative
    level = d['maturity_level']
    insights.append(
        f"Your organisation is at the '{level.title()}' automation maturity level. "
        + {
            'manual':      'Significant automation potential remains untapped.',
            'assisted':    'Basic automation is in place. Structured expansion is the next step.',
            'structured':  'Core automation is working. Focus on governance and reliability.',
            'optimized':   'Automation is mature and governed. AI adoption will drive further gains.',
            'autonomous':  'You are operating at peak automation maturity.',
        }.get(level, '')
    )

    # Coverage narrative
    from apps.automation_maturity.services.automation_maturity_engine import MODULE_PREFIXES
    covered = sum(
        1 for _, prefixes in MODULE_PREFIXES.items()
        if any(any(te.startswith(p) for p in prefixes) for te in d['trigger_events'])
    )
    if covered < len(MODULE_PREFIXES):
        gaps = [
            m for m, prefixes in MODULE_PREFIXES.items()
            if not any(any(te.startswith(p) for p in prefixes) for te in d['trigger_events'])
        ]
        insights.append(
            f"{len(gaps)} module(s) have no automation: {', '.join(gaps[:3])}. "
            "These represent your highest-value automation opportunities."
        )

    # Failure narrative
    fail_rate = (d['fail_30d'] / max(d['exec_30d'], 1)) * 100
    if fail_rate > 10:
        insights.append(
            f"Workflow failure rate is {fail_rate:.1f}% — above the recommended 5% threshold. "
            "Review the Recovery Engine and add fallback rules for critical workflows."
        )

    # Governance narrative
    if d['perm_policies'] < 2 or d['approved_wf'] == 0:
        insights.append(
            "Automation governance is weak. Approval gates and permission policies are missing. "
            "This increases operational risk and audit exposure."
        )

    # ROI narrative
    hours_saved = round((d['ok_30d'] * MINUTES_SAVED_PER_EXEC) / 60, 2)
    cost_saved  = round(hours_saved * HOURLY_LABOUR_COST_USD, 2)
    if hours_saved > 0:
        insights.append(
            f"Automation saved approximately {hours_saved:.1f} hours and "
            f"${cost_saved:,.0f} in operational costs this month."
        )

    # AI insights
    if d['ai_pending'] > 3:
        insights.append(
            f"{d['ai_pending']} AI-generated automation suggestions are awaiting review. "
            "Acting on these is the fastest path to maturity improvement."
        )

    return insights


# ---------------------------------------------------------------------------
# 7. Full Executive Snapshot Persistence
# ---------------------------------------------------------------------------

@transaction.atomic
def run_executive_snapshot(tenant_id):
    """
    Persist a full executive snapshot: summary, ROI, risks, opportunities, departments.
    Returns the ExecutiveAutomationSummary instance.
    """
    from apps.executive_automation.models import (
        ExecutiveAutomationSummary,
        ExecutiveAutomationROI,
        ExecutiveAutomationRisk,
        ExecutiveAutomationDepartment,
        ExecutiveAutomationOpportunity,
        RiskStatus,
        OpportunityStatus,
        ROIPeriod,
    )
    from django.utils import timezone

    today = timezone.now().date()

    # ── Summary ──────────────────────────────────────────────────────────
    summary_data = generate_executive_summary(tenant_id)
    risks        = detect_operational_risks(tenant_id)
    opps         = generate_opportunities(tenant_id)

    summary_data['open_risks']         = len(risks)
    summary_data['open_opportunities'] = len(opps)

    summary = ExecutiveAutomationSummary.objects.create(
        tenant_id                  = tenant_id,
        snapshot_date              = today,
        total_workflows            = summary_data['total_workflows'],
        active_workflows           = summary_data['active_workflows'],
        total_executions_today     = summary_data['total_executions_today'],
        successful_executions_today= summary_data['successful_executions_today'],
        automation_coverage_percent= Decimal(str(summary_data['automation_coverage_percent'])),
        automation_maturity_level  = summary_data['automation_maturity_level'],
        time_saved_hours           = Decimal(str(summary_data['time_saved_hours'])),
        tasks_automated            = summary_data['tasks_automated'],
        sla_improvement_percent    = Decimal(str(summary_data['sla_improvement_percent'])),
        open_risks                 = summary_data['open_risks'],
        open_opportunities         = summary_data['open_opportunities'],
        business_impact_score      = Decimal(str(summary_data['business_impact_score'])),
    )

    # ── ROI ──────────────────────────────────────────────────────────────
    for period_key in ('daily', 'monthly'):
        roi = calculate_roi(tenant_id, period=period_key)
        ExecutiveAutomationROI.objects.update_or_create(
            tenant_id   = tenant_id,
            period      = period_key,
            period_start= roi['period_start'],
            defaults={
                'period_end':               roi['period_end'],
                'hours_saved':              Decimal(str(roi['hours_saved'])),
                'manual_tasks_reduced':     roi['manual_tasks_reduced'],
                'operational_cost_reduction': Decimal(str(roi['operational_cost_reduction'])),
                'productivity_gain_percent':Decimal(str(roi['productivity_gain_percent'])),
                'executions_count':         roi['executions_count'],
                'success_rate':             Decimal(str(roi['success_rate'])),
            },
        )

    # ── Risks (close resolved, create new) ──────────────────────────────
    # Mark old open risks from today as mitigated first, then create fresh ones
    ExecutiveAutomationRisk.objects.filter(
        tenant_id=tenant_id,
        status=RiskStatus.OPEN,
        created_at__date=today,
    ).update(status=RiskStatus.MITIGATED)

    for r in risks:
        ExecutiveAutomationRisk.objects.create(
            tenant_id      = tenant_id,
            risk_type      = r['risk_type'],
            severity       = r['severity'],
            affected_module= r['affected_module'],
            title          = r['title'],
            description    = r['description'],
            metric_value   = r['metric_value'],
            status         = RiskStatus.OPEN,
        )

    # ── Opportunities (upsert by title) ──────────────────────────────────
    for o in opps:
        ExecutiveAutomationOpportunity.objects.update_or_create(
            tenant_id        = tenant_id,
            opportunity_type = o['opportunity_type'],
            module           = o['module'],
            status__in       = [OpportunityStatus.NEW, OpportunityStatus.ASSIGNED],
            defaults={
                'title':           o['title'],
                'description':     o['description'],
                'expected_impact': o['expected_impact'],
                'priority':        o['priority'],
                'source_data':     o['source_data'],
                'status':          OpportunityStatus.NEW,
            },
        )

    # ── Departments ──────────────────────────────────────────────────────
    depts = compute_department_scores(tenant_id)
    for dept in depts:
        ExecutiveAutomationDepartment.objects.update_or_create(
            tenant_id      = tenant_id,
            snapshot_date  = today,
            department_name= dept['department_name'],
            defaults={
                'automation_coverage': Decimal(str(dept['automation_coverage'])),
                'adoption_score':      Decimal(str(dept['adoption_score'])),
                'maturity_level':      dept['maturity_level'],
                'manual_gap_percent':  Decimal(str(dept['manual_gap_percent'])),
                'workflow_count':      dept['workflow_count'],
                'executions_30d':      dept['executions_30d'],
            },
        )

    _emit_event(tenant_id, 'executive_snapshot_completed', 'info',
                f'Executive snapshot: risks={len(risks)} opps={len(opps)}')
    return summary


# ---------------------------------------------------------------------------
# Observability helper
# ---------------------------------------------------------------------------

def _emit_event(tenant_id, event_type, severity, message):
    try:
        from apps.automation_observability.services.workflow_observability_engine import (
            WorkflowObservabilityEngine,
        )
        WorkflowObservabilityEngine.log_event(
            tenant_id=tenant_id, workflow_id=None,
            event_type=event_type, severity=severity, message=message,
        )
    except Exception:  # noqa: BLE001
        pass
