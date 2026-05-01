"""
Prequalification evaluation service for job-bound prequal forms.

Connects JobRequisition.prequal_* config to candidate responses, evaluates
pass/fail, and (optionally) mutates application status.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ── Score Evaluator ───────────────────────────────────────────────────────────

def _parse_numeric(value: str) -> Optional[float]:
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        return None


def _condition_matches(condition_type: str, answer: str, compare: str) -> bool:
    """Evaluate a single PrequalRule condition against an answer string."""
    ans = str(answer).lower().strip()
    cmp = str(compare).lower().strip()

    if condition_type == 'equals':
        return ans == cmp
    if condition_type == 'not_equals':
        return ans != cmp
    if condition_type == 'contains':
        return cmp in ans
    if condition_type == 'is_empty':
        return ans == ''
    if condition_type == 'is_not_empty':
        return ans != ''
    if condition_type == 'in':
        return ans in [v.strip() for v in cmp.split(',')]
    if condition_type == 'not_in':
        return ans not in [v.strip() for v in cmp.split(',')]
    if condition_type in ('greater_than', 'less_than'):
        num_ans = _parse_numeric(ans)
        num_cmp = _parse_numeric(cmp)
        if num_ans is None or num_cmp is None:
            return False
        return num_ans > num_cmp if condition_type == 'greater_than' else num_ans < num_cmp
    return False


# ── Main Evaluation ───────────────────────────────────────────────────────────

def evaluate_candidate_prequal(
    job_id: str,
    candidate_id: str,
    tenant_id: str,
) -> dict:
    """
    Evaluate a candidate's prequalification responses for a specific job.

    Returns:
        {
            'eligible': bool,
            'result': 'pass' | 'fail' | 'manual_review' | 'not_configured',
            'score': int,            # 0-100
            'total_weight': int,
            'earned_weight': int,
            'knockout_triggered': bool,
            'knockout_question': str | None,
            'action': str,           # from job config
            'details': list[dict],
        }
    """
    from apps.jobs.models import JobRequisition
    from apps.prequalification.models import PrequalForm, PrequalQuestion, PrequalResponse, PrequalRule

    # ── Load job config ───────────────────────────────────────────────────────
    try:
        job = JobRequisition.objects.get(id=job_id, tenant_id=tenant_id, is_deleted=False)
    except JobRequisition.DoesNotExist:
        return {'result': 'not_configured', 'eligible': False}

    if not job.prequal_enabled or not job.prequal_form_id:
        return {'result': 'not_configured', 'eligible': True}

    # ── Load form ─────────────────────────────────────────────────────────────
    try:
        form = PrequalForm.objects.get(id=job.prequal_form_id, tenant_id=tenant_id, is_deleted=False)
    except PrequalForm.DoesNotExist:
        logger.warning('Prequal form %s not found for job %s', job.prequal_form_id, job_id)
        return {'result': 'not_configured', 'eligible': True}

    # ── Load all questions for this form ──────────────────────────────────────
    questions = PrequalQuestion.objects.filter(
        section__form_id=form.id, tenant_id=tenant_id
    ).select_related('section').prefetch_related('rules')

    # ── Load candidate responses ──────────────────────────────────────────────
    # Latest response per question (in case of re-submission)
    all_responses = PrequalResponse.objects.filter(
        form_id=form.id, candidate_id=candidate_id, tenant_id=tenant_id
    ).order_by('-created_at')

    responses_by_question: dict[str, str] = {}
    for r in all_responses:
        q_id = str(r.question_id)
        if q_id not in responses_by_question:
            responses_by_question[q_id] = r.answer_text or ''

    # ── Evaluate each question ────────────────────────────────────────────────
    total_weight = 0
    earned_weight = 0
    knockout_triggered = False
    knockout_question_text: Optional[str] = None
    details = []

    for question in questions:
        q_id = str(question.id)
        answer = responses_by_question.get(q_id, '')
        weight = question.score_weight or 0
        total_weight += weight

        # Check knockout rules first
        question_failed_knockout = False
        if question.is_knockout:
            for rule in question.rules.all():
                if rule.action_type == 'reject' and _condition_matches(
                    rule.condition_type, answer, rule.compare_value
                ):
                    knockout_triggered = True
                    knockout_question_text = question.question_text
                    question_failed_knockout = True
                    break

        # Determine if answer earns points (no reject rule triggered)
        earned = False
        if not question_failed_knockout and answer:
            reject_triggered = False
            for rule in question.rules.all():
                if rule.action_type == 'reject' and _condition_matches(
                    rule.condition_type, answer, rule.compare_value
                ):
                    reject_triggered = True
                    break
            if not reject_triggered:
                earned = True
                earned_weight += weight

        details.append({
            'question_id': q_id,
            'question_text': question.question_text[:80],
            'answer': answer,
            'weight': weight,
            'earned': earned,
            'is_knockout': question.is_knockout,
            'knockout_failed': question_failed_knockout,
        })

    # ── Compute score ─────────────────────────────────────────────────────────
    score = int((earned_weight / total_weight * 100)) if total_weight > 0 else 100

    # ── Determine pass threshold ──────────────────────────────────────────────
    threshold = job.prequal_threshold_override
    if threshold is None:
        # Try form metadata (set by InterviewPrequalificationEngine)
        engine_meta = form.metadata.get('prequalification_engine', {})
        knockout_cfg = engine_meta.get('knockout_logic', {})
        threshold = knockout_cfg.get('pass_threshold', 70)

    # ── Final verdict ─────────────────────────────────────────────────────────
    if knockout_triggered:
        result = 'fail'
        action = job.prequal_fail_action
        eligible = False
    elif score >= threshold:
        result = 'pass'
        action = job.prequal_pass_action
        eligible = True
    else:
        result = 'fail'
        action = job.prequal_fail_action
        eligible = False

    return {
        'eligible': eligible,
        'result': result,
        'score': score,
        'total_weight': total_weight,
        'earned_weight': earned_weight,
        'threshold': threshold,
        'knockout_triggered': knockout_triggered,
        'knockout_question': knockout_question_text,
        'action': action,
        'details': details,
    }


def get_job_prequal_snapshot(job_id: str, tenant_id: str) -> dict:
    """
    Returns aggregate prequal stats for the job command center widget.
    """
    from apps.jobs.models import JobRequisition
    from apps.prequalification.models import PrequalForm, PrequalResponse

    try:
        job = JobRequisition.objects.get(id=job_id, tenant_id=tenant_id, is_deleted=False)
    except JobRequisition.DoesNotExist:
        return {'enabled': False}

    if not job.prequal_enabled or not job.prequal_form_id:
        return {'enabled': False}

    form_name = None
    try:
        form = PrequalForm.objects.get(id=job.prequal_form_id, tenant_id=tenant_id, is_deleted=False)
        form_name = form.name
    except PrequalForm.DoesNotExist:
        pass

    # Count distinct candidates who submitted responses for this form
    from django.db.models import Count
    candidate_counts = (
        PrequalResponse.objects
        .filter(form_id=job.prequal_form_id, tenant_id=tenant_id)
        .values('candidate_id')
        .annotate(cnt=Count('id'))
    )
    total_submitted = candidate_counts.count()

    # Pass/fail counts are stored in application metadata if evaluate was called.
    # For a snapshot we report totals from metadata on applications.
    from apps.pipeline.models import Application
    apps_qs = Application.objects.filter(
        requisition_id=job_id, tenant_id=tenant_id, is_deleted=False
    )
    pass_count = apps_qs.filter(
        application_form_data__prequal_result='pass'
    ).count()
    fail_count = apps_qs.filter(
        application_form_data__prequal_result='fail'
    ).count()
    pending_count = total_submitted - pass_count - fail_count
    pending_count = max(pending_count, 0)

    pass_rate = int(pass_count / total_submitted * 100) if total_submitted > 0 else 0

    return {
        'enabled': True,
        'form_id': str(job.prequal_form_id),
        'form_name': form_name,
        'threshold': job.prequal_threshold_override,
        'pass_action': job.prequal_pass_action,
        'fail_action': job.prequal_fail_action,
        'total_submitted': total_submitted,
        'pass_count': pass_count,
        'fail_count': fail_count,
        'pending_count': pending_count,
        'pass_rate': pass_rate,
    }
