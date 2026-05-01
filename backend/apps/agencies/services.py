import uuid
from collections import defaultdict
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
from apps.agencies.models import AgencyPerformanceScore, AgencyClientRelationship, AgencyJobAssignment
from apps.pipeline.models import Application, ApplicationStageHistory
from shared.owner_contracts import OwnerActionContext, OwnerActionResult, OwnerContractError


class AgencyAssignmentService:
    EXTERNAL_SOURCE_ORCHESTRATION_CENTER = 'orchestration_center'

    @staticmethod
    def assign_job_to_agency(
        *,
        tenant_id,
        requisition_id,
        agency_tenant_id,
        assigned_by=None,
        deadline=None,
        max_submissions=None,
        notes: str = '',
        metadata: dict | None = None,
        external_source: str = EXTERNAL_SOURCE_ORCHESTRATION_CENTER,
        external_reference: str = '',
    ):
        parsed_requisition_id = AgencyAssignmentService._parse_uuid(requisition_id)
        parsed_agency_tenant_id = AgencyAssignmentService._parse_uuid(agency_tenant_id)
        if not parsed_requisition_id:
            raise ValueError('Agency assignment requires a valid UUID requisition_id.')
        if not parsed_agency_tenant_id:
            raise ValueError('Agency assignment requires a valid UUID agency_tenant_id.')

        relationship = AgencyClientRelationship.objects.filter(
            tenant_id=tenant_id,
            company_tenant_id=tenant_id,
            agency_tenant_id=parsed_agency_tenant_id,
            status='active',
            is_deleted=False,
        ).first()
        if not relationship:
            raise ValueError('Active agency relationship not found for assignment.')

        assignment = AgencyJobAssignment.objects.filter(
            tenant_id=tenant_id,
            requisition_id=parsed_requisition_id,
            agency_tenant_id=parsed_agency_tenant_id,
        ).first()

        metadata_payload = {
            **(assignment.metadata if assignment else {}),
            **(metadata or {}),
            'external_source': external_source,
        }
        if external_reference:
            metadata_payload['external_reference'] = external_reference

        if assignment:
            comparable_deadline = deadline or assignment.deadline
            comparable_max_submissions = max_submissions if max_submissions is not None else assignment.max_submissions
            comparable_notes = notes if notes else assignment.notes
            unchanged = (
                not assignment.is_deleted
                and assignment.status == 'active'
                and assignment.deadline == comparable_deadline
                and assignment.max_submissions == comparable_max_submissions
                and assignment.notes == comparable_notes
                and assignment.metadata == metadata_payload
            )
            if unchanged:
                return assignment, False

            assignment.is_deleted = False
            assignment.deleted_at = None
            assignment.status = 'active'
            assignment.assigned_by = assigned_by
            assignment.created_by = assignment.created_by or assigned_by
            if deadline is not None:
                assignment.deadline = deadline
            if max_submissions is not None:
                assignment.max_submissions = max_submissions
            if notes:
                assignment.notes = notes
            assignment.metadata = metadata_payload
            assignment.save(
                update_fields=[
                    'is_deleted',
                    'deleted_at',
                    'status',
                    'assigned_by',
                    'created_by',
                    'deadline',
                    'max_submissions',
                    'notes',
                    'metadata',
                    'updated_at',
                ]
            )
            return assignment, True

        assignment = AgencyJobAssignment.objects.create(
            tenant_id=tenant_id,
            requisition_id=parsed_requisition_id,
            agency_tenant_id=parsed_agency_tenant_id,
            assigned_by=assigned_by,
            deadline=deadline,
            max_submissions=max_submissions,
            notes=notes,
            created_by=assigned_by,
            metadata=metadata_payload,
        )
        return assignment, True

    @staticmethod
    def _parse_uuid(value):
        if not value:
            return None
        try:
            return uuid.UUID(str(value))
        except (TypeError, ValueError, AttributeError):
            return None

    @staticmethod
    def assign_from_orchestration(
        *,
        context: OwnerActionContext,
        requisition_id,
        agency_tenant_id,
        deadline=None,
        max_submissions=None,
        notes: str = '',
        assignment_reason: str = 'automation_rule',
    ):
        try:
            assignment, created = AgencyAssignmentService.assign_job_to_agency(
                tenant_id=context.tenant_id,
                requisition_id=requisition_id,
                agency_tenant_id=agency_tenant_id,
                assigned_by=context.actor_id,
                deadline=deadline,
                max_submissions=max_submissions,
                notes=notes,
                metadata=context.audit_metadata,
                external_source=context.external_source,
                external_reference=context.external_reference,
            )
        except ValueError as exc:
            message = str(exc)
            if 'valid UUID' in message:
                raise OwnerContractError.validation(message) from exc
            if 'Active agency relationship not found' in message:
                raise OwnerContractError.ownership(message) from exc
            raise OwnerContractError.validation(message) from exc
        return OwnerActionResult(
            owner_module='agencies',
            action_family='assign',
            status='completed',
            target_type='job_assignment',
            target_id=str(assignment.id),
            duplicate=not created,
            audit_metadata=context.metadata_payload(assignment_reason=assignment_reason),
            payload={
                'assignment_id': str(assignment.id),
                'requisition_id': str(assignment.requisition_id),
                'agency_tenant_id': str(assignment.agency_tenant_id) if assignment.agency_tenant_id else '',
            },
        )


class AgencyOperationalFlagService:
    EXTERNAL_SOURCE_ORCHESTRATION_CENTER = 'orchestration_center'
    ALLOWED_FLAGS = {'attention_needed', 'review_required', 'manual_check_required', 'overdue_risk'}

    @staticmethod
    def mark_operational_flag(
        *,
        tenant_id,
        entity_type: str,
        entity_id,
        flag_key: str,
        flag_value=True,
        metadata: dict | None = None,
        external_source: str = EXTERNAL_SOURCE_ORCHESTRATION_CENTER,
        external_reference: str = '',
    ):
        if flag_key not in AgencyOperationalFlagService.ALLOWED_FLAGS:
            raise ValueError('Unsupported agency operational flag.')
        parsed_entity_id = AgencyAssignmentService._parse_uuid(entity_id)
        if not parsed_entity_id:
            raise ValueError('Agency flagging requires a valid UUID entity_id.')
        if entity_type != 'job_assignment':
            raise ValueError('Unsupported agency entity_type for flagging.')

        assignment = AgencyJobAssignment.objects.filter(
            tenant_id=tenant_id,
            id=parsed_entity_id,
            is_deleted=False,
        ).first()
        if not assignment:
            raise ValueError('Agency job assignment not found for flagging.')

        payload = dict(metadata or {})
        payload['external_source'] = external_source
        if external_reference:
            payload['external_reference'] = external_reference

        changed = AgencyOperationalFlagService._apply_flag(
            assignment=assignment,
            flag_key=flag_key,
            flag_value=flag_value,
            payload=payload,
        )
        return assignment, changed

    @staticmethod
    def _apply_flag(*, assignment, flag_key: str, flag_value, payload: dict) -> bool:
        metadata_json = dict(assignment.metadata or {})
        flags = dict(metadata_json.get('operational_flags') or {})
        comparable = {'value': bool(flag_value), **payload}
        existing = flags.get(flag_key)
        if existing and {k: v for k, v in existing.items() if k != 'updated_at'} == comparable:
            return False

        flags[flag_key] = {
            **comparable,
            'updated_at': timezone.now().isoformat(),
        }
        metadata_json['operational_flags'] = flags
        assignment.metadata = metadata_json
        assignment.save(update_fields=['metadata', 'updated_at'])
        return True

    @staticmethod
    def mark_flag_from_orchestration(
        *,
        context: OwnerActionContext,
        entity_type: str,
        entity_id,
        flag_key: str,
        flag_value=True,
    ):
        try:
            assignment, created = AgencyOperationalFlagService.mark_operational_flag(
                tenant_id=context.tenant_id,
                entity_type=entity_type,
                entity_id=entity_id,
                flag_key=flag_key,
                flag_value=flag_value,
                metadata=context.audit_metadata,
                external_source=context.external_source,
                external_reference=context.external_reference,
            )
        except ValueError as exc:
            message = str(exc)
            if 'Unsupported agency entity_type' in message or 'Unsupported agency operational flag' in message:
                raise OwnerContractError.unsupported(message) from exc
            if 'valid UUID' in message:
                raise OwnerContractError.validation(message) from exc
            if 'Agency job assignment not found' in message:
                raise OwnerContractError.not_found(message) from exc
            raise OwnerContractError.validation(message) from exc
        return OwnerActionResult(
            owner_module='agencies',
            action_family='mark_flag',
            status='completed',
            target_type='job_assignment',
            target_id=str(assignment.id),
            duplicate=not created,
            audit_metadata=context.metadata_payload(flag_key=flag_key, flag_value=bool(flag_value)),
            payload={
                'flag_key': flag_key,
                'entity_id': str(assignment.id),
                'assignment_id': str(assignment.id),
            },
        )


class AgencyIntelligenceService:
    ACTIVE_RELATIONSHIP_STATUSES = {'active'}
    WEAK_SCORE_THRESHOLD = 45
    INACTIVE_DAYS_THRESHOLD = 30

    @staticmethod
    def _safe_pct(numerator, denominator):
        if not denominator:
            return 0.0
        return round((numerator / denominator) * 100, 2)

    @staticmethod
    def _clamp(value, minimum=0.0, maximum=100.0):
        return max(minimum, min(maximum, round(value, 2)))

    @staticmethod
    def _agency_name_map(agency_ids):
        from apps.organisations.models import Organisation

        normalized_ids = [agency_id for agency_id in {str(value) for value in agency_ids if value}]
        if not normalized_ids:
            return {}

        names = {}
        for org in Organisation.objects.filter(tenant_id__in=normalized_ids, is_deleted=False).values('tenant_id', 'name'):
            tenant_id = str(org['tenant_id'])
            if org.get('name'):
                names[tenant_id] = org['name']

        for tenant_id in normalized_ids:
            names.setdefault(tenant_id, f"Agency {tenant_id[:8]}")
        return names

    @staticmethod
    def _load_balancing_snapshot(tenant_id):
        assignment_rows = AgencyJobAssignment.objects.filter(
            tenant_id=tenant_id,
            is_deleted=False,
            status='active',
        ).values('agency_tenant_id').annotate(active_assignments=Count('id'))
        by_agency = {str(row['agency_tenant_id']): int(row['active_assignments']) for row in assignment_rows if row['agency_tenant_id']}
        average_load = (sum(by_agency.values()) / len(by_agency)) if by_agency else 0
        return by_agency, average_load

    @staticmethod
    def _relationship_map(tenant_id):
        relationships = AgencyClientRelationship.objects.filter(
            company_tenant_id=tenant_id,
            is_deleted=False,
        )
        return {str(rel.agency_tenant_id): rel for rel in relationships if rel.agency_tenant_id}

    @staticmethod
    def _similar_job_success_rate(tenant_id, agency_tenant_id, requisition):
        from apps.jobs.models import JobRequisition

        similar_job_ids = list(
            JobRequisition.objects.filter(
                tenant_id=tenant_id,
                is_deleted=False,
            ).filter(
                Q(job_category=requisition.job_category, job_category__gt='') |
                Q(department_id=requisition.department_id) |
                Q(work_mode=requisition.work_mode)
            ).exclude(id=requisition.id).values_list('id', flat=True)[:25]
        )
        if not similar_job_ids:
            return 0.0

        similar_apps = Application.objects.filter(
            tenant_id=tenant_id,
            agency_id=agency_tenant_id,
            requisition_id__in=similar_job_ids,
            is_agency_submission=True,
            is_deleted=False,
        )
        total = similar_apps.count()
        joined = similar_apps.filter(status='joined').count()
        return AgencyIntelligenceService._safe_pct(joined, total)

    @staticmethod
    def refresh_agency_performance_scores(tenant_id):
        """
        Calculates and persists performance metrics and scores for all 
        active agency relationships of a specific tenant.
        """
        relationships = AgencyClientRelationship.objects.filter(
            company_tenant_id=tenant_id,
            status__in=AgencyIntelligenceService.ACTIVE_RELATIONSHIP_STATUSES,
            is_deleted=False
        )
        
        results = []
        for rel in relationships:
            if not rel.agency_tenant_id:
                continue
                
            metrics = AgencyIntelligenceService.calculate_agency_metrics(
                tenant_id=tenant_id, 
                agency_tenant_id=rel.agency_tenant_id
            )
            
            # Update or create persisted score record
            score_obj, _ = AgencyPerformanceScore.objects.update_or_create(
                tenant_id=tenant_id,
                agency_tenant_id=rel.agency_tenant_id,
                defaults={
                    'total_submissions': metrics['total_submissions'],
                    'shortlisted_count': metrics['shortlisted_count'],
                    'interviewed_count': metrics['interviewed_count'],
                    'offered_count': metrics['offered_count'],
                    'joined_count': metrics['joined_count'],
                    'shortlist_rate': metrics['shortlist_rate'],
                    'interview_rate': metrics['interview_rate'],
                    'offer_rate': metrics['offer_rate'],
                    'join_rate': metrics['join_rate'],
                    'avg_submission_time_hours': metrics['response_time_hours'],
                    'overall_score': metrics['overall_score'],
                    'metadata': {
                        'candidate_quality': metrics['candidate_quality'],
                        'job_coverage': metrics['job_coverage'],
                        'activity_level': metrics['activity_level']
                    }
                }
            )
            results.append(score_obj)
        
        return results

    @staticmethod
    def get_global_agency_stats(tenant_id):
        relationships = AgencyClientRelationship.objects.filter(
            company_tenant_id=tenant_id,
            status__in=AgencyIntelligenceService.ACTIVE_RELATIONSHIP_STATUSES,
            is_deleted=False,
        )
        agency_ids = [str(rel.agency_tenant_id) for rel in relationships if rel.agency_tenant_id]
        name_map = AgencyIntelligenceService._agency_name_map(agency_ids)
        results = []
        for rel in relationships:
            if not rel.agency_tenant_id:
                continue
            metrics = AgencyIntelligenceService.calculate_agency_metrics(
                tenant_id=tenant_id,
                agency_tenant_id=rel.agency_tenant_id,
            )
            results.append({
                'agency_tenant_id': str(rel.agency_tenant_id),
                'agency_name': name_map.get(str(rel.agency_tenant_id), f"Agency {str(rel.agency_tenant_id)[:8]}"),
                'tier': rel.tier,
                'status': rel.status,
                'score': metrics['overall_score'],
                'metrics': metrics,
            })
        return sorted(results, key=lambda item: item['score'], reverse=True)

    @staticmethod
    def calculate_agency_metrics(tenant_id, agency_tenant_id=None, company_tenant_id=None, requisition_id=None):
        query = Q(tenant_id=tenant_id, is_agency_submission=True, is_deleted=False)
        if agency_tenant_id:
            query &= Q(agency_id=agency_tenant_id)
        if company_tenant_id:
            query &= Q(tenant_id=company_tenant_id)
        if requisition_id:
            query &= Q(requisition_id=requisition_id)

        apps = Application.objects.filter(query)
        stats = apps.aggregate(
            total_submissions=Count('id'),
            shortlisted=Count('id', filter=Q(status='shortlisted') | Q(status__in=['interview', 'offer', 'joined'])),
            interviewed=Count('id', filter=Q(status='interview') | Q(status__in=['offer', 'joined'])),
            offered=Count('id', filter=Q(status='offer') | Q(status='joined')),
            joined=Count('id', filter=Q(status='joined')),
            avg_match_score=Avg('match_score'),
        )

        total_submissions = int(stats['total_submissions'] or 0)
        shortlisted_count = int(stats['shortlisted'] or 0)
        interviewed_count = int(stats['interviewed'] or 0)
        offered_count = int(stats['offered'] or 0)
        joined_count = int(stats['joined'] or 0)
        avg_match_score = float(stats['avg_match_score'] or 0)

        assignment_query = AgencyJobAssignment.objects.filter(
            tenant_id=tenant_id,
            is_deleted=False,
        )
        if agency_tenant_id:
            assignment_query = assignment_query.filter(agency_tenant_id=agency_tenant_id)
        if requisition_id:
            assignment_query = assignment_query.filter(requisition_id=requisition_id)

        assignment_list = list(assignment_query)
        active_assignments = [assignment for assignment in assignment_list if assignment.status == 'active']
        distinct_jobs = {str(assignment.requisition_id) for assignment in assignment_list if assignment.requisition_id}
        submitted_jobs = {str(app.requisition_id) for app in apps.only('requisition_id')}

        response_hours = []
        app_map = defaultdict(list)
        for app in apps.only('requisition_id', 'created_at'):
            app_map[str(app.requisition_id)].append(app)
        for assignment in active_assignments:
            candidates = sorted(app_map.get(str(assignment.requisition_id), []), key=lambda item: item.created_at)
            if candidates:
                delta = candidates[0].created_at - assignment.created_at
                response_hours.append(max(delta.total_seconds() / 3600, 0))

        avg_response_hours = round(sum(response_hours) / len(response_hours), 2) if response_hours else 0.0
        response_speed_score = 100.0 if avg_response_hours == 0 else AgencyIntelligenceService._clamp(100 - (avg_response_hours * 1.5))
        job_coverage_rate = AgencyIntelligenceService._safe_pct(len(submitted_jobs), len(distinct_jobs))
        candidate_quality_score = AgencyIntelligenceService._clamp((avg_match_score * 0.4) + (AgencyIntelligenceService._safe_pct(shortlisted_count, total_submissions) * 0.6))
        recent_submissions = apps.filter(created_at__gte=timezone.now() - timedelta(days=30)).count()

        metrics = {
            'total_submissions': total_submissions,
            'shortlisted_count': shortlisted_count,
            'interviewed_count': interviewed_count,
            'offered_count': offered_count,
            'joined_count': joined_count,
            'shortlist_rate': AgencyIntelligenceService._safe_pct(shortlisted_count, total_submissions),
            'interview_rate': AgencyIntelligenceService._safe_pct(interviewed_count, total_submissions),
            'offer_rate': AgencyIntelligenceService._safe_pct(offered_count, total_submissions),
            'hire_rate': AgencyIntelligenceService._safe_pct(joined_count, total_submissions),
            'join_rate': AgencyIntelligenceService._safe_pct(joined_count, total_submissions),
            'response_time_hours': avg_response_hours,
            'response_speed_score': response_speed_score,
            'candidate_quality': candidate_quality_score,
            'job_coverage': round(job_coverage_rate, 2),
            'active_assignments': len(active_assignments),
            'assignment_count': len(assignment_list),
            'recent_submissions': int(recent_submissions),
            'activity_level': 'high' if recent_submissions >= 8 else 'medium' if recent_submissions >= 3 else 'low',
            'avg_match_score': round(avg_match_score, 2),
        }

        overall_score = (
            (metrics['shortlist_rate'] * 0.20) +
            (metrics['interview_rate'] * 0.10) +
            (metrics['hire_rate'] * 0.25) +
            (metrics['response_speed_score'] * 0.15) +
            (metrics['candidate_quality'] * 0.20) +
            (metrics['job_coverage'] * 0.10)
        )
        metrics['overall_score'] = AgencyIntelligenceService._clamp(overall_score)
        return metrics

    @staticmethod
    def detect_agency_risks(tenant_id, agency_tenant_id):
        metrics = AgencyIntelligenceService.calculate_agency_metrics(tenant_id, agency_tenant_id)
        risks = []

        if metrics['total_submissions'] >= 5 and metrics['shortlist_rate'] < 20:
            risks.append({'type': 'low_quality', 'severity': 'high', 'message': 'Low shortlist conversion against current submission volume.'})
        if metrics['response_time_hours'] and metrics['response_time_hours'] > 72:
            risks.append({'type': 'slow_response', 'severity': 'medium', 'message': 'First candidate response is slower than the expected operating window.'})
        if metrics['interviewed_count'] >= 4 and metrics['hire_rate'] == 0:
            risks.append({'type': 'poor_conversion', 'severity': 'medium', 'message': 'Candidates progress to interview but are not converting to hires.'})

        last_sub = Application.objects.filter(
            tenant_id=tenant_id,
            agency_id=agency_tenant_id,
            is_deleted=False,
        ).order_by('-created_at').first()
        if not last_sub or (timezone.now() - last_sub.created_at).days > AgencyIntelligenceService.INACTIVE_DAYS_THRESHOLD:
            risks.append({'type': 'inactive', 'severity': 'high', 'message': 'No recent agency submission activity was detected.'})
        return risks

    @staticmethod
    def perform_intelligent_distribution(requisition_id):
        """
        Executes the intelligent distribution logic for a newly published job.
        Uses JobRequisition distribution policy and performance scoring.
        """
        from apps.jobs.models import JobRequisition

        requisition = JobRequisition.objects.filter(id=requisition_id, is_deleted=False).first()
        if not requisition or not requisition.auto_distribute_to_agencies:
            return {'status': 'skipped', 'reason': 'auto_distribute_disabled'}

        tenant_id = requisition.tenant_id
        policy = requisition.agency_distribution_policy or 'manual'
        
        if policy == 'manual':
            return {'status': 'skipped', 'reason': 'manual_policy'}

        recommendations = AgencyIntelligenceService.get_job_agency_recommendations(
            requisition_id=requisition_id, 
            tenant_id=tenant_id
        )
        
        target_agencies = []
        if policy == 'all':
            # Assign to all active preferred agencies
            target_agencies = [r for r in recommendations if r['relationship_tier'] == 'preferred']
        elif policy == 'performance_ranked':
            # Assign to top 3 agencies with score > 60
            target_agencies = [r for r in recommendations if r['score'] >= 60][:3]
        
        if not target_agencies:
            # Fallback to top 2 if policy resulted in empty list but we have active agencies
            target_agencies = recommendations[:2]

        assignments_created = 0
        for rec in target_agencies:
            _, created = AgencyAssignmentService.assign_job_to_agency(
                tenant_id=tenant_id,
                requisition_id=requisition_id,
                agency_tenant_id=rec['agency_tenant_id'],
                notes=f"Automated distribution based on {policy} policy.",
                metadata={'distribution_score': rec['score'], 'distribution_policy': policy}
            )
            if created:
                assignments_created += 1

        return {
            'status': 'completed',
            'policy': policy,
            'assignments_created': assignments_created,
            'agencies': [a['agency_tenant_id'] for a in target_agencies]
        }

    @staticmethod
    def get_job_agency_recommendations(requisition_id, tenant_id):
        from apps.jobs.models import JobRequisition

        requisition = JobRequisition.objects.filter(id=requisition_id, tenant_id=tenant_id, is_deleted=False).first()
        if not requisition:
            return []

        relationship_map = AgencyIntelligenceService._relationship_map(tenant_id)
        active_relationships = [
            rel for rel in relationship_map.values()
            if rel.status in AgencyIntelligenceService.ACTIVE_RELATIONSHIP_STATUSES and rel.tier != 'blacklisted'
        ]
        load_by_agency, average_load = AgencyIntelligenceService._load_balancing_snapshot(tenant_id)
        name_map = AgencyIntelligenceService._agency_name_map([rel.agency_tenant_id for rel in active_relationships])

        recommendations = []
        for relationship in active_relationships:
            agency_id = str(relationship.agency_tenant_id)
            metrics = AgencyIntelligenceService.calculate_agency_metrics(tenant_id=tenant_id, agency_tenant_id=relationship.agency_tenant_id)
            similar_success = AgencyIntelligenceService._similar_job_success_rate(tenant_id, relationship.agency_tenant_id, requisition)
            load = int(load_by_agency.get(agency_id, 0))
            load_balance_score = 100.0 if average_load == 0 else AgencyIntelligenceService._clamp(100 - max(load - average_load, 0) * 18)
            tier_boost = {'preferred': 8, 'standard': 3, 'probation': -8}.get(relationship.tier, 0)
            recommendation_score = AgencyIntelligenceService._clamp(
                (metrics['overall_score'] * 0.60) +
                (similar_success * 0.15) +
                (load_balance_score * 0.15) +
                (metrics['job_coverage'] * 0.10) +
                tier_boost
            )

            reasons = []
            if metrics['hire_rate'] >= 20:
                reasons.append('strong hire conversion')
            if similar_success >= 20:
                reasons.append('relevant job success')
            if load <= average_load:
                reasons.append('balanced current load')
            if relationship.tier == 'preferred':
                reasons.append('preferred partner tier')
            if not reasons:
                reasons.append('eligible fallback coverage')

            recommendations.append({
                'agency_tenant_id': agency_id,
                'agency_name': name_map.get(agency_id, f"Agency {agency_id[:8]}"),
                'relationship_tier': relationship.tier,
                'score': recommendation_score,
                'metrics': metrics,
                'current_load': load,
                'similar_job_success_rate': round(similar_success, 2),
                'reason': ', '.join(reasons[:2]),
                'recommended_distribution': 'primary' if recommendation_score >= 75 else 'secondary' if recommendation_score >= 55 else 'fallback',
            })

        recommendations.sort(key=lambda item: item['score'], reverse=True)
        return recommendations[:5]

    @staticmethod
    def build_job_agency_intelligence(*, tenant_id, requisition_id):
        assignments = list(
            AgencyJobAssignment.objects.filter(
                tenant_id=tenant_id,
                requisition_id=requisition_id,
                is_deleted=False,
            ).order_by('-created_at')
        )
        recommendations = AgencyIntelligenceService.get_job_agency_recommendations(requisition_id=requisition_id, tenant_id=tenant_id)
        recommendation_map = {item['agency_tenant_id']: item for item in recommendations}
        name_map = AgencyIntelligenceService._agency_name_map([assignment.agency_tenant_id for assignment in assignments] + [item['agency_tenant_id'] for item in recommendations])

        assigned_agencies = []
        underperforming_agencies = []
        inactive_agencies = []
        for assignment in assignments:
            agency_id = str(assignment.agency_tenant_id)
            metrics = AgencyIntelligenceService.calculate_agency_metrics(
                tenant_id=tenant_id,
                agency_tenant_id=assignment.agency_tenant_id,
                requisition_id=requisition_id,
            )
            global_metrics = AgencyIntelligenceService.calculate_agency_metrics(
                tenant_id=tenant_id,
                agency_tenant_id=assignment.agency_tenant_id,
            )
            risks = AgencyIntelligenceService.detect_agency_risks(tenant_id=tenant_id, agency_tenant_id=assignment.agency_tenant_id)
            payload = {
                'assignment_id': str(assignment.id),
                'agency_tenant_id': agency_id,
                'agency_name': name_map.get(agency_id, f"Agency {agency_id[:8]}"),
                'status': assignment.status,
                'submission_count': assignment.submission_count,
                'score': global_metrics['overall_score'],
                'job_metrics': metrics,
                'global_metrics': global_metrics,
                'risks': risks,
            }
            assigned_agencies.append(payload)
            if global_metrics['overall_score'] < AgencyIntelligenceService.WEAK_SCORE_THRESHOLD:
                underperforming_agencies.append(payload)
            if any(risk['type'] == 'inactive' for risk in risks):
                inactive_agencies.append(payload)

        application_rows = list(
            Application.objects.filter(
                tenant_id=tenant_id,
                requisition_id=requisition_id,
                is_deleted=False,
            )
        )
        agency_apps = [app for app in application_rows if app.is_agency_submission and app.agency_id]
        source_counts = defaultdict(int)
        contribution_by_agency = defaultdict(lambda: {'submissions': 0, 'shortlisted': 0, 'interviewed': 0, 'joined': 0})
        for app in application_rows:
            source_key = str(app.source or ('agency' if app.is_agency_submission else 'direct')).lower()
            source_counts[source_key] += 1
        for app in agency_apps:
            agency_key = str(app.agency_id)
            contribution_by_agency[agency_key]['submissions'] += 1
            if app.status in {'shortlisted', 'interview', 'offer', 'joined'}:
                contribution_by_agency[agency_key]['shortlisted'] += 1
            if app.status in {'interview', 'offer', 'joined'}:
                contribution_by_agency[agency_key]['interviewed'] += 1
            if app.status == 'joined':
                contribution_by_agency[agency_key]['joined'] += 1

        contribution_rows = []
        for agency_key, counts in contribution_by_agency.items():
            contribution_rows.append({
                'agency_tenant_id': agency_key,
                'agency_name': name_map.get(agency_key, f"Agency {agency_key[:8]}"),
                **counts,
                'success_rate': AgencyIntelligenceService._safe_pct(counts['joined'], counts['submissions']),
            })
        contribution_rows.sort(key=lambda item: item['submissions'], reverse=True)

        return {
            'assigned_agencies': assigned_agencies,
            'recommended_agencies': recommendations,
            'underperforming_agencies': underperforming_agencies,
            'inactive_agencies': inactive_agencies,
            'assigned_performance': assigned_agencies,
            'recommendations': recommendations,
            'source_intelligence': {
                'agency_submission_share': AgencyIntelligenceService._safe_pct(len(agency_apps), len(application_rows)),
                'agency_submissions': len(agency_apps),
                'total_candidates': len(application_rows),
                'candidate_sources': [{'source': source, 'count': count} for source, count in sorted(source_counts.items(), key=lambda item: item[1], reverse=True)],
                'agency_contribution': contribution_rows,
            },
        }

    @staticmethod
    def build_dashboard(tenant_id):
        relationship_map = AgencyIntelligenceService._relationship_map(tenant_id)
        global_stats = AgencyIntelligenceService.get_global_agency_stats(tenant_id)
        load_by_agency, average_load = AgencyIntelligenceService._load_balancing_snapshot(tenant_id)

        active_relationships = [rel for rel in relationship_map.values() if rel.status in AgencyIntelligenceService.ACTIVE_RELATIONSHIP_STATUSES]
        weak_agencies = [item for item in global_stats if item['score'] < AgencyIntelligenceService.WEAK_SCORE_THRESHOLD]
        risk_rows = []
        for item in global_stats:
            risks = AgencyIntelligenceService.detect_agency_risks(tenant_id=tenant_id, agency_tenant_id=item['agency_tenant_id'])
            if risks:
                risk_rows.append({**item, 'risks': risks})

        fallback_agencies = [item for item in global_stats if item['score'] >= AgencyIntelligenceService.WEAK_SCORE_THRESHOLD][:5]
        comparison_rows = []
        if global_stats:
            top_score = global_stats[0]['score']
            for item in global_stats[:8]:
                comparison_rows.append({
                    'agency_tenant_id': item['agency_tenant_id'],
                    'agency_name': item['agency_name'],
                    'score': item['score'],
                    'score_gap_vs_leader': round(top_score - item['score'], 2),
                    'hire_rate': item['metrics']['hire_rate'],
                    'response_time_hours': item['metrics']['response_time_hours'],
                    'job_coverage': item['metrics']['job_coverage'],
                })

        agency_apps = Application.objects.filter(
            tenant_id=tenant_id,
            is_agency_submission=True,
            is_deleted=False,
        )
        contribution_rows = []
        for item in global_stats:
            agency_id = item['agency_tenant_id']
            submissions = agency_apps.filter(agency_id=agency_id).count()
            joined = agency_apps.filter(agency_id=agency_id, status='joined').count()
            shortlisted = agency_apps.filter(agency_id=agency_id, status__in=['shortlisted', 'interview', 'offer', 'joined']).count()
            contribution_rows.append({
                'agency_tenant_id': agency_id,
                'agency_name': item['agency_name'],
                'submissions': submissions,
                'shortlist_rate': AgencyIntelligenceService._safe_pct(shortlisted, submissions),
                'success_rate': AgencyIntelligenceService._safe_pct(joined, submissions),
                'score': item['score'],
            })
        contribution_rows.sort(key=lambda row: row['submissions'], reverse=True)

        direct_count = Application.objects.filter(tenant_id=tenant_id, is_deleted=False, is_agency_submission=False).count()
        total_count = Application.objects.filter(tenant_id=tenant_id, is_deleted=False).count()

        return {
            'overview': {
                'connected_agencies': len(relationship_map),
                'active_agencies': len(active_relationships),
                'agency_submissions': int(agency_apps.count()),
                'agency_hires': int(agency_apps.filter(status='joined').count()),
                'weak_agencies': len(weak_agencies),
                'inactive_agencies': sum(1 for row in risk_rows if any(risk['type'] == 'inactive' for risk in row['risks'])),
                'average_agency_score': round(sum(item['score'] for item in global_stats) / len(global_stats), 2) if global_stats else 0,
            },
            'performance': global_stats,
            'distribution': {
                'best_agencies': global_stats[:5],
                'fallback_agencies': fallback_agencies,
                'load_balancing': [
                    {
                        'agency_tenant_id': item['agency_tenant_id'],
                        'agency_name': item['agency_name'],
                        'active_assignments': int(load_by_agency.get(item['agency_tenant_id'], 0)),
                        'load_state': 'balanced' if average_load == 0 or load_by_agency.get(item['agency_tenant_id'], 0) <= average_load else 'busy',
                    }
                    for item in global_stats[:8]
                ],
            },
            'risks': risk_rows,
            'comparison': comparison_rows,
            'pipeline': {
                'agency_contribution': contribution_rows[:8],
                'candidate_source_intelligence': {
                    'agency_share': AgencyIntelligenceService._safe_pct(agency_apps.count(), total_count),
                    'direct_share': AgencyIntelligenceService._safe_pct(direct_count, total_count),
                    'total_candidates': total_count,
                },
            },
        }
