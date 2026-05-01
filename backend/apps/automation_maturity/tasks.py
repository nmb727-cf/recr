"""
Celery background tasks for the Automation Maturity Center.
"""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='automation_maturity.run_daily_assessment')
def run_daily_assessment():
    """
    Run a full maturity assessment for every active tenant.
    Scheduled: daily at 02:00 UTC via Celery Beat.
    """
    from apps.tenants.models import Client
    from apps.automation_maturity.services.automation_maturity_engine import run_full_assessment

    processed = 0
    for tenant in Client.objects.filter(is_active=True):
        try:
            assessment = run_full_assessment(tenant_id=tenant.id)
            logger.info(
                'Daily maturity assessment: tenant=%s score=%.2f level=%s',
                tenant.id, assessment.overall_maturity_score, assessment.maturity_level,
            )
            processed += 1
        except Exception as exc:  # noqa: BLE001
            logger.exception('Maturity assessment failed for tenant %s: %s', tenant.id, exc)

    logger.info('run_daily_assessment: %d tenant(s) assessed.', processed)
    return processed


@shared_task(name='automation_maturity.refresh_recommendations')
def refresh_recommendations():
    """
    Refresh recommendations for all active tenants without running a full assessment.
    Scheduled: every 6 hours via Celery Beat.
    """
    from apps.tenants.models import Client
    from apps.automation_maturity.services.automation_maturity_engine import (
        calculate_overall_maturity,
        generate_maturity_recommendations,
    )
    from apps.automation_maturity.models import (
        AutomationMaturityRecommendation,
        RecommendationStatus,
    )
    from decimal import Decimal

    refreshed = 0
    for tenant in Client.objects.filter(is_active=True):
        try:
            scores = calculate_overall_maturity(tenant.id)
            recs   = generate_maturity_recommendations(tenant.id, scores)
            for r in recs:
                AutomationMaturityRecommendation.objects.update_or_create(
                    tenant_id          = tenant.id,
                    recommendation_type= r['recommendation_type'],
                    status__in         = [RecommendationStatus.NEW, RecommendationStatus.ACKNOWLEDGED],
                    defaults={
                        'title':                  r['title'],
                        'description':            r['description'],
                        'target_area':            r['target_area'],
                        'expected_maturity_gain': Decimal(str(round(r['expected_maturity_gain'], 2))),
                        'priority':               r['priority'],
                        'status':                 RecommendationStatus.NEW,
                    },
                )
            refreshed += 1
        except Exception as exc:  # noqa: BLE001
            logger.exception('Recommendation refresh failed for tenant %s: %s', tenant.id, exc)

    logger.info('refresh_recommendations: %d tenant(s) processed.', refreshed)
    return refreshed


@shared_task(name='automation_maturity.store_maturity_trend')
def store_maturity_trend():
    """
    Persist a lightweight trend snapshot for all tenants.
    Scheduled: every 12 hours via Celery Beat.
    """
    # Delegates to run_daily_assessment which already stores a snapshot per call.
    # This task is a lighter alias that skips module/team details for speed.
    from apps.tenants.models import Client
    from apps.automation_maturity.services.automation_maturity_engine import (
        calculate_overall_maturity,
        determine_maturity_level,
    )
    from apps.automation_maturity.models import AutomationMaturityAssessment
    from decimal import Decimal
    from django.utils import timezone

    stored = 0
    today  = timezone.now().date()
    for tenant in Client.objects.filter(is_active=True):
        # Only store if no record for today yet
        if AutomationMaturityAssessment.objects.filter(
            tenant_id=tenant.id, assessment_date=today
        ).exists():
            continue
        try:
            scores = calculate_overall_maturity(tenant.id)
            AutomationMaturityAssessment.objects.create(
                tenant_id             = tenant.id,
                assessment_date       = today,
                overall_maturity_score= Decimal(str(scores['overall'])),
                maturity_level        = scores['maturity_level'],
                coverage_score        = Decimal(str(scores['coverage'])),
                adoption_score        = Decimal(str(scores['adoption'])),
                governance_score      = Decimal(str(scores['governance'])),
                reliability_score     = Decimal(str(scores['reliability'])),
                intelligence_score    = Decimal(str(scores['intelligence'])),
                operating_score       = Decimal(str(scores['operating'])),
                business_impact_score = Decimal(str(scores['business_impact'])),
            )
            stored += 1
        except Exception as exc:  # noqa: BLE001
            logger.exception('Trend snapshot failed for tenant %s: %s', tenant.id, exc)

    logger.info('store_maturity_trend: %d snapshot(s) stored.', stored)
    return stored
