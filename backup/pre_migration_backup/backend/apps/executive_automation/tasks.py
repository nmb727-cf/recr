from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(name='executive_automation.run_daily_executive_snapshot')
def run_daily_executive_snapshot():
    """
    Generate the full executive snapshot for every active tenant.
    Scheduled: daily at 03:00 UTC (after maturity assessment at 02:00).
    """
    from django.db import connection

    # Collect all active tenant_ids from any key model
    try:
        from apps.automation.models import WorkflowDefinition
        tenant_ids = (
            WorkflowDefinition.objects
            .filter(is_deleted=False)
            .values_list('tenant_id', flat=True)
            .distinct()
        )
    except Exception:
        logger.warning('Could not enumerate tenants via WorkflowDefinition; skipping.')
        return

    from .services import automation_executive_engine as exec_engine

    success = 0
    errors  = 0
    for tid in tenant_ids:
        try:
            exec_engine.run_executive_snapshot(str(tid))
            success += 1
        except Exception as exc:
            logger.error('Executive snapshot failed for tenant %s: %s', tid, exc)
            errors += 1

    logger.info('Executive snapshots: %d ok, %d errors', success, errors)
    return {'success': success, 'errors': errors}


@shared_task(name='executive_automation.refresh_executive_risks')
def refresh_executive_risks():
    """
    Lightweight risk refresh: re-run detect_operational_risks and
    upsert new risks without touching ROI / department data.
    Scheduled: every 4 hours.
    """
    try:
        from apps.automation.models import WorkflowDefinition
        tenant_ids = (
            WorkflowDefinition.objects
            .filter(is_deleted=False)
            .values_list('tenant_id', flat=True)
            .distinct()
        )
    except Exception:
        return

    from .services import automation_executive_engine as exec_engine
    from .models import ExecutiveAutomationRisk, RiskStatus

    for tid in tenant_ids:
        try:
            risks = exec_engine.detect_operational_risks(str(tid))
            for r in risks:
                # Only create if no open/acknowledged risk of same type already exists
                exists = ExecutiveAutomationRisk.objects.filter(
                    tenant_id=tid,
                    risk_type=r['risk_type'],
                    status__in=[RiskStatus.OPEN, RiskStatus.ACKNOWLEDGED],
                    is_deleted=False,
                ).exists()
                if not exists:
                    ExecutiveAutomationRisk.objects.create(
                        tenant_id=tid,
                        risk_type=r['risk_type'],
                        severity=r['severity'],
                        affected_module=r.get('affected_module', ''),
                        title=r['title'],
                        description=r['description'],
                        metric_value=r.get('metric_value', {}),
                    )
        except Exception as exc:
            logger.error('Risk refresh failed for tenant %s: %s', tid, exc)


@shared_task(name='executive_automation.compute_periodic_roi')
def compute_periodic_roi():
    """
    Persist monthly ROI records for all tenants.
    Scheduled: 1st of every month at 04:00 UTC.
    """
    try:
        from apps.automation.models import WorkflowDefinition
        tenant_ids = (
            WorkflowDefinition.objects
            .filter(is_deleted=False)
            .values_list('tenant_id', flat=True)
            .distinct()
        )
    except Exception:
        return

    from .services import automation_executive_engine as exec_engine
    from .models import ExecutiveAutomationROI, ROIPeriod
    import datetime

    today = datetime.date.today()
    period_start = today.replace(day=1)
    import calendar
    last_day = calendar.monthrange(today.year, today.month)[1]
    period_end = today.replace(day=last_day)

    for tid in tenant_ids:
        try:
            # skip if already computed this month
            if ExecutiveAutomationROI.objects.filter(
                tenant_id=tid,
                period=ROIPeriod.MONTHLY,
                period_start=period_start,
                is_deleted=False,
            ).exists():
                continue

            roi = exec_engine.calculate_roi(str(tid), 'monthly')
            ExecutiveAutomationROI.objects.create(
                tenant_id=tid,
                period=ROIPeriod.MONTHLY,
                period_start=period_start,
                period_end=period_end,
                hours_saved=roi['hours_saved'],
                manual_tasks_reduced=roi['manual_tasks_reduced'],
                operational_cost_reduction=roi['operational_cost_reduction'],
                productivity_gain_percent=roi['productivity_gain_percent'],
                executions_count=roi['executions_count'],
                success_rate=roi['success_rate'],
            )
        except Exception as exc:
            logger.error('ROI compute failed for tenant %s: %s', tid, exc)
