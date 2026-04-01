import uuid
from django.db.models import Count, Q, Avg, F
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
    @staticmethod
    def get_global_agency_stats(tenant_id):
        """
        Aggregates performance for all agencies connected to this company tenant.
        """
        from apps.agencies.models import AgencyClientRelationship
        from apps.tenants.models import Client
        relationships = AgencyClientRelationship.objects.filter(
            company_tenant_id=tenant_id,
            status='active',
            is_deleted=False
        )
        
        results = []
        for rel in relationships:
            metrics = AgencyIntelligenceService.calculate_agency_metrics(
                tenant_id=tenant_id,
                agency_tenant_id=rel.agency_tenant_id
            )
            # Fetch agency name from Client model
            agency_tenant = Client.objects.filter(id=rel.agency_tenant_id).first()
            agency_name = agency_tenant.name if agency_tenant else f"Agency {str(rel.agency_tenant_id)[:8]}"
            
            results.append({
                'agency_tenant_id': str(rel.agency_tenant_id),
                'agency_name': agency_name,
                'score': metrics['overall_score'],
                'metrics': metrics
            })
            
        return sorted(results, key=lambda x: x['score'], reverse=True)

    @staticmethod
    def calculate_agency_metrics(tenant_id, agency_tenant_id=None, company_tenant_id=None):
        """
        Calculates performance metrics for one or all agencies for a specific company.
        """
        query = Q(tenant_id=tenant_id, is_agency_submission=True)
        if agency_tenant_id:
            query &= Q(agency_id=agency_tenant_id)
        if company_tenant_id:
            query &= Q(tenant_id=company_tenant_id)

        apps = Application.objects.filter(query)
        
        # Aggregate counts
        stats = apps.aggregate(
            total_submissions=Count('id'),
            shortlisted=Count('id', filter=Q(status='shortlisted') | Q(status__in=['interview', 'offer', 'joined'])),
            interviewed=Count('id', filter=Q(status='interview') | Q(status__in=['offer', 'joined'])),
            offered=Count('id', filter=Q(status='offer') | Q(status='joined')),
            joined=Count('id', filter=Q(status='joined')),
        )

        total = stats['total_submissions'] or 1 # Avoid division by zero
        
        metrics = {
            'total_submissions': stats['total_submissions'],
            'shortlisted_count': stats['shortlisted'],
            'interviewed_count': stats['interviewed'],
            'offered_count': stats['offered'],
            'joined_count': stats['joined'],
            'shortlist_rate': (stats['shortlisted'] / total) * 100,
            'interview_rate': (stats['interviewed'] / total) * 100,
            'offer_rate': (stats['offered'] / total) * 100,
            'join_rate': (stats['joined'] / total) * 100,
        }

        # Calculate performance score (out of 100)
        # Weights: Shortlist (20%), Interview (30%), Join (50%)
        score = (metrics['shortlist_rate'] * 0.2) + (metrics['interview_rate'] * 0.3) + (metrics['join_rate'] * 0.5)
        metrics['overall_score'] = min(score, 100)

        return metrics

    @staticmethod
    def detect_agency_risks(tenant_id, agency_tenant_id):
        """
        Detects risks such as low quality or inactivity.
        """
        metrics = AgencyIntelligenceService.calculate_agency_metrics(tenant_id, agency_tenant_id)
        risks = []

        if metrics['total_submissions'] > 10 and metrics['shortlist_rate'] < 15:
            risks.append({'type': 'low_quality', 'message': 'High volume of submissions with very low shortlist rate.'})
        
        # Check inactivity
        last_sub = Application.objects.filter(tenant_id=tenant_id, agency_id=agency_tenant_id).order_at('-created_at').first()
        if not last_sub or (timezone.now() - last_sub.created_at).days > 30:
            risks.append({'type': 'inactive', 'message': 'No submissions received in the last 30 days.'})

        if metrics['interview_rate'] > 0 and metrics['join_rate'] == 0 and metrics['interviewed_count'] > 5:
            risks.append({'type': 'poor_conversion', 'message': 'Candidates reaching interview stage but not converting to hires.'})

        return risks

    @staticmethod
    def get_job_agency_recommendations(requisition_id, tenant_id):
        """
        Recommends agencies for a specific job based on historical performance in similar roles.
        """
        # For now, recommend top 3 active agencies by overall score
        top_agencies = AgencyPerformanceScore.objects.filter(tenant_id=tenant_id).order_by('-overall_score')[:3]
        
        recommendations = []
        for score in top_agencies:
            recommendations.append({
                'agency_tenant_id': score.agency_tenant_id,
                'score': score.overall_score,
                'reason': 'Top performing agency globally.'
            })
        
        return recommendations
