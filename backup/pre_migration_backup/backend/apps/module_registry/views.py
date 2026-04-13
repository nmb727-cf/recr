from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.responses import error_response, success_response
from apps.module_registry.models import (
    GeneratedPrompt,
    ModuleAuditLog,
    ModuleBlocker,
    ModuleContinuationNote,
    ModuleDependency,
    ModuleDependencyChain,
    ModuleGapRecord,
    NextModuleCandidateScore,
    NextModuleDecisionAudit,
    NextModuleDelayRisk,
    NextModuleDependencyPressure,
    NextModuleReadinessRecord,
    NextModuleRecommendation,
    NextModuleRejectionReason,
    NextModuleSelection,
    NextModuleSequencePlan,
    PromptContext,
    PromptDependency,
    PromptHistory,
    PromptScope,
    PromptStatusChoices,
    PromptVersion,
    ModuleOwner,
    ModulePlanningAuditLog,
    ModulePriorityRecord,
    ModuleRegistry,
    ModuleSequencePlan,
    ModuleStatus,
    RemainingModuleMap,
    BuildModeChoices,
    CandidateStatusChoices,
    ClassificationChoices,
    ModuleStatusChoices,
    GapStatusChoices,
    PhaseBucketChoices,
    ReadinessChoices,
    SelectionStatusChoices,
)
from apps.module_registry.serializers import (
    GeneratedPromptSerializer,
    ModuleBlockerSerializer,
    ModuleContinuationNoteSerializer,
    ModuleDependencySerializer,
    ModuleDependencyChainSerializer,
    ModuleGapRecordSerializer,
    NextModuleCandidateScoreSerializer,
    NextModuleDelayRiskSerializer,
    NextModuleDependencyPressureSerializer,
    NextModuleReadinessRecordSerializer,
    NextModuleRecommendationSerializer,
    NextModuleRejectionReasonSerializer,
    NextModuleSelectionSerializer,
    NextModuleSequencePlanSerializer,
    PromptDependencySerializer,
    PromptHistorySerializer,
    PromptScopeSerializer,
    ModuleOwnerSerializer,
    ModulePriorityRecordSerializer,
    ModuleRegistrySerializer,
    ModuleSequencePlanSerializer,
    ModuleStatusSerializer,
    PromptVersionSerializer,
    RemainingModuleMapSerializer,
)


MANAGER_ROLES = {
    'super_admin',
    'tenant_admin',
    'hr_manager',
    'hrbp',
    'recruiter',
}


def _can_manage_registry(user):
    return bool(getattr(user, 'is_staff', False) or getattr(user, 'role', None) in MANAGER_ROLES)


def _log_event(module, actor_name, event_type, payload):
    ModuleAuditLog.objects.create(
        tenant_id=module.tenant_id,
        created_by=getattr(module, 'created_by', None),
        module=module,
        actor_name=actor_name or '',
        event_type=event_type,
        event_payload=payload or {},
    )


def _log_planning_event(module, actor_name, event_type, payload):
    ModulePlanningAuditLog.objects.create(
        tenant_id=module.tenant_id,
        created_by=getattr(module, 'created_by', None),
        module=module,
        actor_name=actor_name or '',
        event_type=event_type,
        event_payload=payload or {},
    )


def _log_selection_event(module, actor_name, event_type, payload):
    NextModuleDecisionAudit.objects.create(
        tenant_id=module.tenant_id,
        created_by=getattr(module, 'created_by', None),
        module=module,
        actor_name=actor_name or '',
        event_type=event_type,
        event_payload=payload or {},
    )


class ModuleRegistryListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.user.tenant_id
        queryset = ModuleRegistry.objects.filter(tenant_id=tenant_id)

        module_domain = request.query_params.get('module_domain')
        status_filter = request.query_params.get('status')
        backend_status = request.query_params.get('backend_status')
        frontend_status = request.query_params.get('frontend_status')

        if module_domain:
            queryset = queryset.filter(module_domain=module_domain)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if backend_status:
            queryset = queryset.filter(backend_status=backend_status)
        if frontend_status:
            queryset = queryset.filter(frontend_status=frontend_status)

        serializer = ModuleRegistrySerializer(queryset.order_by('implementation_order', 'module_name'), many=True)
        return success_response(data=serializer.data, message='Modules retrieved.')

    def post(self, request):
        if not _can_manage_registry(request.user):
            return error_response('You do not have permission to create modules.', status_code=status.HTTP_403_FORBIDDEN)

        serializer = ModuleRegistrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        module = serializer.save(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
        )
        ModuleStatus.objects.get_or_create(
            module=module,
            defaults={
                'tenant_id': request.user.tenant_id,
                'created_by': request.user.id,
                'status': module.status,
                'architecture_status': module.architecture_status,
                'backend_status': module.backend_status,
                'frontend_status': module.frontend_status,
                'integration_status': module.integration_status,
                'qa_status': module.qa_status,
                'dependency_status': module.dependency_status,
                'blocker_status': module.blocker_status,
            },
        )
        _log_event(module, getattr(request.user, 'email', ''), 'module.created', serializer.data)
        return success_response(
            data=ModuleRegistrySerializer(module).data,
            message='Module created.',
            status_code=status.HTTP_201_CREATED,
        )


class ModuleRegistryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, module_id):
        if not _can_manage_registry(request.user):
            return error_response('You do not have permission to update modules.', status_code=status.HTTP_403_FORBIDDEN)

        try:
            module = ModuleRegistry.objects.get(id=module_id, tenant_id=request.user.tenant_id)
        except ModuleRegistry.DoesNotExist:
            return error_response('Module not found.', status_code=status.HTTP_404_NOT_FOUND)

        serializer = ModuleRegistrySerializer(module, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        module = serializer.save()
        _log_event(module, getattr(request.user, 'email', ''), 'module.updated', serializer.validated_data)
        return success_response(data=ModuleRegistrySerializer(module).data, message='Module updated.')


class ModuleStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, module_id):
        if not _can_manage_registry(request.user):
            return error_response('You do not have permission to update status.', status_code=status.HTTP_403_FORBIDDEN)

        try:
            module = ModuleRegistry.objects.get(id=module_id, tenant_id=request.user.tenant_id)
        except ModuleRegistry.DoesNotExist:
            return error_response('Module not found.', status_code=status.HTTP_404_NOT_FOUND)

        status_record, _ = ModuleStatus.objects.get_or_create(
            module=module,
            defaults={'tenant_id': request.user.tenant_id, 'created_by': request.user.id},
        )
        serializer = ModuleStatusSerializer(status_record, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        status_record = serializer.save()

        sync_fields = [
            'status', 'architecture_status', 'backend_status', 'frontend_status',
            'integration_status', 'qa_status', 'dependency_status', 'blocker_status',
        ]
        for field in sync_fields:
            setattr(module, field, getattr(status_record, field))
        module.save(update_fields=sync_fields + ['updated_at'])
        _log_event(module, getattr(request.user, 'email', ''), 'module.status.updated', serializer.validated_data)
        return success_response(data=ModuleStatusSerializer(status_record).data, message='Status updated.')


class ModuleDependencyCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, module_id):
        if not _can_manage_registry(request.user):
            return error_response('You do not have permission to add dependencies.', status_code=status.HTTP_403_FORBIDDEN)

        payload = {**request.data, 'module': module_id}
        serializer = ModuleDependencySerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        dependency = serializer.save(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
        )
        _log_event(dependency.module, getattr(request.user, 'email', ''), 'module.dependency.added', serializer.validated_data)
        return success_response(
            data=ModuleDependencySerializer(dependency).data,
            message='Dependency added.',
            status_code=status.HTTP_201_CREATED,
        )


class ModuleBlockerCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, module_id):
        if not _can_manage_registry(request.user):
            return error_response('You do not have permission to add blockers.', status_code=status.HTTP_403_FORBIDDEN)

        payload = {**request.data, 'module': module_id}
        serializer = ModuleBlockerSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        blocker = serializer.save(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
        )
        module = blocker.module
        module.blocker_status = blocker.blocker_status
        module.priority_level = blocker.priority_level
        module.save(update_fields=['blocker_status', 'priority_level', 'updated_at'])
        _log_event(module, getattr(request.user, 'email', ''), 'module.blocker.added', serializer.validated_data)
        return success_response(
            data=ModuleBlockerSerializer(blocker).data,
            message='Blocker added.',
            status_code=status.HTTP_201_CREATED,
        )


class ModuleOwnerCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, module_id):
        if not _can_manage_registry(request.user):
            return error_response('You do not have permission to assign owners.', status_code=status.HTTP_403_FORBIDDEN)

        payload = {**request.data, 'module': module_id}
        serializer = ModuleOwnerSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        owner = serializer.save(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
        )
        _log_event(owner.module, getattr(request.user, 'email', ''), 'module.owner.assigned', serializer.validated_data)
        return success_response(
            data=ModuleOwnerSerializer(owner).data,
            message='Owner assigned.',
            status_code=status.HTTP_201_CREATED,
        )


class RemainingModuleMapScanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not _can_manage_registry(request.user):
            return error_response('You do not have permission to scan remaining modules.', status_code=status.HTTP_403_FORBIDDEN)

        modules = ModuleRegistry.objects.filter(tenant_id=request.user.tenant_id).prefetch_related('dependencies', 'blockers', 'owners')
        scanned = 0
        for module in modules:
            backend_gap = GapStatusChoices.NONE if module.backend_status in {ReadinessChoices.READY, ReadinessChoices.VERIFIED} else GapStatusChoices.MAJOR
            frontend_gap = GapStatusChoices.NONE if module.frontend_status in {ReadinessChoices.READY, ReadinessChoices.VERIFIED} else GapStatusChoices.MAJOR
            dependency_status = module.dependency_status

            if module.status == ModuleStatusChoices.COMPLETE and backend_gap == GapStatusChoices.NONE and frontend_gap == GapStatusChoices.NONE:
                classification = ClassificationChoices.CRITICAL_IMPL_READY
                phase_bucket = PhaseBucketChoices.MVP_REQUIRED
            elif module.status == ModuleStatusChoices.PARTIAL:
                classification = ClassificationChoices.CRITICAL_PARTIAL
                phase_bucket = PhaseBucketChoices.MVP_REQUIRED
            elif module.architecture_status in {ReadinessChoices.READY, ReadinessChoices.VERIFIED} and module.backend_status == ReadinessChoices.NOT_READY:
                classification = ClassificationChoices.CRITICAL_ARCH_ONLY
                phase_bucket = PhaseBucketChoices.MVP_REQUIRED
            elif module.blocker_status == ModuleStatusChoices.BLOCKED:
                classification = ClassificationChoices.BLOCKED_DEPENDENCY if dependency_status != ReadinessChoices.VERIFIED else ClassificationChoices.BLOCKED_BUSINESS_RULE
                phase_bucket = PhaseBucketChoices.PHASE_2_REQUIRED
            else:
                classification = ClassificationChoices.CRITICAL_NOT_STARTED
                phase_bucket = PhaseBucketChoices.MVP_REQUIRED

            priority_score = (
                (30 if classification in {
                    ClassificationChoices.CRITICAL_NOT_STARTED,
                    ClassificationChoices.CRITICAL_PARTIAL,
                    ClassificationChoices.CRITICAL_ARCH_ONLY,
                } else 10)
                + (20 if module.priority_level == 'critical' else 15 if module.priority_level == 'high' else 10 if module.priority_level == 'medium' else 5)
                + (15 if dependency_status != ReadinessChoices.VERIFIED else 5)
                + (15 if backend_gap in {GapStatusChoices.MAJOR, GapStatusChoices.BLOCKING} else 0)
                + (15 if frontend_gap in {GapStatusChoices.MAJOR, GapStatusChoices.BLOCKING} else 0)
            )

            owner_tool = module.owners.filter(is_primary=True).values_list('owner_tool', flat=True).first() or ''
            recommended_action = 'Continue implementation and close backend/frontend gaps.'
            if classification == ClassificationChoices.CRITICAL_ARCH_ONLY:
                recommended_action = 'Convert approved architecture into backend contracts and minimal admin/runtime coverage.'
            elif classification == ClassificationChoices.BLOCKED_DEPENDENCY:
                recommended_action = 'Resolve upstream dependency before continuing implementation.'
            elif classification == ClassificationChoices.BLOCKED_BUSINESS_RULE:
                recommended_action = 'Clarify business rule before committing further implementation.'

            RemainingModuleMap.objects.update_or_create(
                module=module,
                defaults={
                    'tenant_id': request.user.tenant_id,
                    'created_by': request.user.id,
                    'classification_status': classification,
                    'priority_score': priority_score,
                    'mvp_status': module.backend_status,
                    'enterprise_status': module.integration_status,
                    'backend_gap_status': backend_gap,
                    'frontend_gap_status': frontend_gap,
                    'dependency_chain_status': dependency_status,
                    'blocker_reason': module.notes if module.blocker_status == ModuleStatusChoices.BLOCKED else '',
                    'recommended_next_action': recommended_action,
                    'phase_bucket': phase_bucket,
                    'sequence_order': module.implementation_order,
                    'owner_tool': owner_tool,
                    'notes': module.notes,
                },
            )
            ModuleGapRecord.objects.update_or_create(
                module=module,
                defaults={
                    'tenant_id': request.user.tenant_id,
                    'created_by': request.user.id,
                    'backend_gap_status': backend_gap,
                    'frontend_gap_status': frontend_gap,
                    'integration_gap_status': GapStatusChoices.NONE if module.integration_status in {ReadinessChoices.READY, ReadinessChoices.VERIFIED} else GapStatusChoices.MODERATE,
                    'architecture_gap_status': GapStatusChoices.NONE if module.architecture_status in {ReadinessChoices.READY, ReadinessChoices.VERIFIED} else GapStatusChoices.MAJOR,
                    'qa_gap_status': GapStatusChoices.NONE if module.qa_status in {ReadinessChoices.READY, ReadinessChoices.VERIFIED} else GapStatusChoices.MODERATE,
                    'blocker_reason': module.notes if module.blocker_status == ModuleStatusChoices.BLOCKED else '',
                    'notes': module.notes,
                },
            )
            ModulePriorityRecord.objects.update_or_create(
                module=module,
                defaults={
                    'tenant_id': request.user.tenant_id,
                    'created_by': request.user.id,
                    'priority_score': priority_score,
                    'product_criticality': 10 if module.priority_level == 'critical' else 8 if module.priority_level == 'high' else 5,
                    'dependency_weight': 8 if dependency_status != ReadinessChoices.VERIFIED else 3,
                    'user_journey_impact': 9 if module.module_domain in {'ats_core', 'interview_system', 'hiring_decision'} else 5,
                    'frontend_gap_severity': 8 if frontend_gap != GapStatusChoices.NONE else 0,
                    'backend_gap_severity': 8 if backend_gap != GapStatusChoices.NONE else 0,
                    'blocker_severity': 9 if module.blocker_status == ModuleStatusChoices.BLOCKED else 0,
                    'implementation_readiness': 9 if module.status == ModuleStatusChoices.PARTIAL else 4,
                    'cross_system_impact': 9 if module.module_domain == 'cross_system' else 5,
                    'near_term_usefulness': 8,
                    'notes': recommended_action,
                },
            )
            scanned += 1

        return success_response(data={'scanned_modules': scanned}, message='Remaining module scan completed.')


class RemainingModuleMapListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = RemainingModuleMap.objects.filter(tenant_id=request.user.tenant_id).select_related('module')
        classification = request.query_params.get('classification_status')
        phase_bucket = request.query_params.get('phase_bucket')

        if classification:
            queryset = queryset.filter(classification_status=classification)
        if phase_bucket:
            queryset = queryset.filter(phase_bucket=phase_bucket)

        serializer = RemainingModuleMapSerializer(queryset.order_by('-priority_score', 'sequence_order'), many=True)
        return success_response(data=serializer.data, message='Remaining module map retrieved.')


class ModuleGapListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = ModuleGapRecord.objects.filter(tenant_id=request.user.tenant_id).select_related('module')
        serializer = ModuleGapRecordSerializer(queryset, many=True)
        return success_response(data=serializer.data, message='Module gaps retrieved.')


class PartiallyBuiltModuleListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = RemainingModuleMap.objects.filter(
            tenant_id=request.user.tenant_id,
            classification_status=ClassificationChoices.CRITICAL_PARTIAL,
        ).select_related('module')
        serializer = RemainingModuleMapSerializer(queryset.order_by('-priority_score', 'sequence_order'), many=True)
        return success_response(data=serializer.data, message='Partially built modules retrieved.')


class BlockedModuleListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = RemainingModuleMap.objects.filter(
            tenant_id=request.user.tenant_id,
            classification_status__in=[ClassificationChoices.BLOCKED_DEPENDENCY, ClassificationChoices.BLOCKED_BUSINESS_RULE],
        ).select_related('module')
        serializer = RemainingModuleMapSerializer(queryset.order_by('-priority_score', 'sequence_order'), many=True)
        return success_response(data=serializer.data, message='Blocked modules retrieved.')


class ArchitectureOnlyModuleListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = RemainingModuleMap.objects.filter(
            tenant_id=request.user.tenant_id,
            classification_status=ClassificationChoices.CRITICAL_ARCH_ONLY,
        ).select_related('module')
        serializer = RemainingModuleMapSerializer(queryset.order_by('-priority_score', 'sequence_order'), many=True)
        return success_response(data=serializer.data, message='Architecture-only modules retrieved.')


class ModulePrioritySummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = ModulePriorityRecord.objects.filter(tenant_id=request.user.tenant_id).select_related('module').order_by('-priority_score')
        serializer = ModulePriorityRecordSerializer(queryset, many=True)
        return success_response(data=serializer.data, message='Priority summary retrieved.')


class NextRecommendedModulesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = RemainingModuleMap.objects.filter(
            tenant_id=request.user.tenant_id,
        ).exclude(
            classification_status__in=[ClassificationChoices.OPTIONAL_LATER, ClassificationChoices.BLOCKED_BUSINESS_RULE]
        ).order_by('-priority_score', 'sequence_order')[:10]
        serializer = RemainingModuleMapSerializer(queryset, many=True)
        return success_response(data=serializer.data, message='Next recommended modules retrieved.')


class MVPModulesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = RemainingModuleMap.objects.filter(
            tenant_id=request.user.tenant_id,
            phase_bucket=PhaseBucketChoices.MVP_REQUIRED,
        ).order_by('-priority_score', 'sequence_order')
        serializer = RemainingModuleMapSerializer(queryset, many=True)
        return success_response(data=serializer.data, message='MVP critical modules retrieved.')


class EnterpriseLaterModulesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = RemainingModuleMap.objects.filter(
            tenant_id=request.user.tenant_id,
            phase_bucket__in=[PhaseBucketChoices.ENTERPRISE_EXTENSION, PhaseBucketChoices.FUTURE_INNOVATION],
        ).order_by('-priority_score', 'sequence_order')
        serializer = RemainingModuleMapSerializer(queryset, many=True)
        return success_response(data=serializer.data, message='Enterprise later modules retrieved.')


class ModuleSequencePlanListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = ModuleSequencePlan.objects.filter(tenant_id=request.user.tenant_id).select_related('module')
        serializer = ModuleSequencePlanSerializer(queryset, many=True)
        return success_response(data=serializer.data, message='Sequence plan retrieved.')

    def post(self, request):
        if not _can_manage_registry(request.user):
            return error_response('You do not have permission to create sequence plans.', status_code=status.HTTP_403_FORBIDDEN)

        serializer = ModuleSequencePlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan = serializer.save(tenant_id=request.user.tenant_id, created_by=request.user.id)
        _log_planning_event(plan.module, getattr(request.user, 'email', ''), 'planning.sequence.created', serializer.validated_data)
        return success_response(data=ModuleSequencePlanSerializer(plan).data, message='Sequence plan created.', status_code=status.HTTP_201_CREATED)


class ModuleDependencyChainListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = ModuleDependencyChain.objects.filter(tenant_id=request.user.tenant_id).select_related('module', 'depends_on')
        serializer = ModuleDependencyChainSerializer(queryset, many=True)
        return success_response(data=serializer.data, message='Dependency chain retrieved.')


class ParallelSafeModulesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = ModuleSequencePlan.objects.filter(tenant_id=request.user.tenant_id, is_parallel_safe=True).select_related('module')
        serializer = ModuleSequencePlanSerializer(queryset.order_by('sequence_order'), many=True)
        return success_response(data=serializer.data, message='Parallel-safe modules retrieved.')


class ModuleContinuationPlanUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, module_id):
        if not _can_manage_registry(request.user):
            return error_response('You do not have permission to update continuation plans.', status_code=status.HTTP_403_FORBIDDEN)

        try:
            module = ModuleRegistry.objects.get(id=module_id, tenant_id=request.user.tenant_id)
        except ModuleRegistry.DoesNotExist:
            return error_response('Module not found.', status_code=status.HTTP_404_NOT_FOUND)

        payload = {**request.data, 'module': module_id}
        serializer = ModuleContinuationNoteSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        note = serializer.save(tenant_id=request.user.tenant_id, created_by=request.user.id)
        _log_planning_event(module, getattr(request.user, 'email', ''), 'planning.continuation.updated', serializer.validated_data)
        return success_response(data=ModuleContinuationNoteSerializer(note).data, message='Continuation plan updated.', status_code=status.HTTP_201_CREATED)


def _infer_build_mode(module):
    if module.backend_status in {ReadinessChoices.NOT_READY, ReadinessChoices.PARTIAL} and module.frontend_status in {ReadinessChoices.NOT_READY, ReadinessChoices.PARTIAL}:
        return BuildModeChoices.BACKEND_FIRST
    if module.backend_status in {ReadinessChoices.READY, ReadinessChoices.VERIFIED} and module.frontend_status in {ReadinessChoices.NOT_READY, ReadinessChoices.PARTIAL}:
        return BuildModeChoices.FRONTEND_FIRST
    if module.backend_status in {ReadinessChoices.NOT_READY, ReadinessChoices.PARTIAL} and module.frontend_status in {ReadinessChoices.READY, ReadinessChoices.VERIFIED}:
        return BuildModeChoices.BACKEND_FIRST
    return BuildModeChoices.FULL_STACK


def _candidate_owner_tool(module):
    return module.owners.filter(is_primary=True).values_list('owner_tool', flat=True).first() or 'codex'


class CandidateModulePoolView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = RemainingModuleMap.objects.filter(tenant_id=request.user.tenant_id).select_related('module')
        serializer = RemainingModuleMapSerializer(queryset.order_by('-priority_score', 'sequence_order'), many=True)
        return success_response(data=serializer.data, message='Candidate module pool retrieved.')


class ScoreModuleCandidatesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not _can_manage_registry(request.user):
            return error_response('You do not have permission to score module candidates.', status_code=status.HTTP_403_FORBIDDEN)

        candidates = RemainingModuleMap.objects.filter(tenant_id=request.user.tenant_id).select_related('module')
        scored = 0
        for remaining in candidates:
            module = remaining.module
            priority = module.priority_records.order_by('-created_at').first()
            gap = module.gap_records.order_by('-created_at').first()
            dependency_count = module.dependencies.count()
            downstream_count = module.dependents.count()
            ambiguity_score = 9 if remaining.classification_status == ClassificationChoices.BLOCKED_BUSINESS_RULE else 2 if module.notes else 4
            readiness_score = 9 if module.status == ModuleStatusChoices.PARTIAL else 7 if module.architecture_status in {ReadinessChoices.READY, ReadinessChoices.VERIFIED} else 4
            dependency_score = min(10, 4 + dependency_count + downstream_count)
            journey_impact_score = 10 if module.module_key in {'workflow_system', 'job_pipeline', 'submissions', 'candidate_database'} else 8 if module.module_domain in {'ats_core', 'candidate_system'} else 6
            backend_gap_score = 9 if module.backend_status in {ReadinessChoices.NOT_READY, ReadinessChoices.PARTIAL} else 2
            frontend_gap_score = 8 if module.frontend_status in {ReadinessChoices.NOT_READY, ReadinessChoices.PARTIAL} else 2
            delay_risk_score = min(10, journey_impact_score + dependency_score // 2)
            criticality_score = priority.product_criticality if priority else (10 if module.priority_level == 'critical' else 8 if module.priority_level == 'high' else 5)
            final_score = (
                criticality_score * 5
                + dependency_score * 4
                + journey_impact_score * 5
                + backend_gap_score * 3
                + frontend_gap_score * 2
                + readiness_score * 4
                + delay_risk_score * 4
                - ambiguity_score * 4
            )

            candidate_status = CandidateStatusChoices.IMMEDIATE
            if remaining.classification_status == ClassificationChoices.BLOCKED_BUSINESS_RULE:
                candidate_status = CandidateStatusChoices.BLOCKED
            elif remaining.phase_bucket in {PhaseBucketChoices.ENTERPRISE_EXTENSION, PhaseBucketChoices.FUTURE_INNOVATION}:
                candidate_status = CandidateStatusChoices.DEFERRED

            NextModuleCandidateScore.objects.update_or_create(
                module=module,
                defaults={
                    'tenant_id': request.user.tenant_id,
                    'created_by': request.user.id,
                    'candidate_status': candidate_status,
                    'criticality_score': criticality_score,
                    'dependency_score': dependency_score,
                    'journey_impact_score': journey_impact_score,
                    'frontend_gap_score': frontend_gap_score,
                    'backend_gap_score': backend_gap_score,
                    'readiness_score': readiness_score,
                    'ambiguity_score': ambiguity_score,
                    'final_selection_score': max(0, final_score),
                    'notes': remaining.recommended_next_action,
                },
            )
            NextModuleDependencyPressure.objects.update_or_create(
                module=module,
                defaults={
                    'tenant_id': request.user.tenant_id,
                    'created_by': request.user.id,
                    'dependency_score': dependency_score,
                    'blocking_dependency_count': dependency_count,
                    'downstream_modules_affected': downstream_count,
                    'notes': remaining.blocker_reason,
                },
            )
            NextModuleDelayRisk.objects.update_or_create(
                module=module,
                defaults={
                    'tenant_id': request.user.tenant_id,
                    'created_by': request.user.id,
                    'delay_risk_score': delay_risk_score,
                    'user_journey_risk': journey_impact_score,
                    'dependency_risk': dependency_score,
                    'coordination_risk': 8 if module.owners.count() > 1 else 4,
                    'notes': remaining.notes,
                },
            )
            NextModuleReadinessRecord.objects.update_or_create(
                module=module,
                defaults={
                    'tenant_id': request.user.tenant_id,
                    'created_by': request.user.id,
                    'readiness_score': readiness_score,
                    'ambiguity_score': ambiguity_score,
                    'backend_first_recommended': _infer_build_mode(module) == BuildModeChoices.BACKEND_FIRST,
                    'frontend_first_recommended': _infer_build_mode(module) == BuildModeChoices.FRONTEND_FIRST,
                    'blocked_by_business_rule': remaining.classification_status == ClassificationChoices.BLOCKED_BUSINESS_RULE,
                    'can_codex_start_immediately': remaining.classification_status != ClassificationChoices.BLOCKED_BUSINESS_RULE,
                    'notes': gap.notes if gap else remaining.notes,
                },
            )
            scored += 1

        return success_response(data={'scored_candidates': scored}, message='Module candidates scored.')


class CandidateScoringSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = NextModuleCandidateScore.objects.filter(tenant_id=request.user.tenant_id).select_related('module')
        serializer = NextModuleCandidateScoreSerializer(queryset.order_by('-final_selection_score'), many=True)
        return success_response(data=serializer.data, message='Candidate scoring summary retrieved.')


class RejectedCandidatesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = NextModuleRejectionReason.objects.filter(tenant_id=request.user.tenant_id).select_related('module')
        serializer = NextModuleRejectionReasonSerializer(queryset, many=True)
        return success_response(data=serializer.data, message='Rejected candidates retrieved.')


class DependencyPressureSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = NextModuleDependencyPressure.objects.filter(tenant_id=request.user.tenant_id).select_related('module')
        serializer = NextModuleDependencyPressureSerializer(queryset.order_by('-dependency_score'), many=True)
        return success_response(data=serializer.data, message='Dependency pressure summary retrieved.')


class NextModuleReadinessSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = NextModuleReadinessRecord.objects.filter(tenant_id=request.user.tenant_id).select_related('module')
        serializer = NextModuleReadinessRecordSerializer(queryset.order_by('-readiness_score'), many=True)
        return success_response(data=serializer.data, message='Readiness summary retrieved.')


class SelectNextCriticalModuleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not _can_manage_registry(request.user):
            return error_response('You do not have permission to select the next critical module.', status_code=status.HTTP_403_FORBIDDEN)

        scores = NextModuleCandidateScore.objects.filter(
            tenant_id=request.user.tenant_id,
            candidate_status=CandidateStatusChoices.IMMEDIATE,
        ).select_related('module').order_by('-final_selection_score', '-readiness_score', '-dependency_score', '-journey_impact_score')

        if not scores.exists():
            return error_response('No eligible module candidates found. Run candidate scoring first.', status_code=status.HTTP_400_BAD_REQUEST)

        NextModuleSelection.objects.filter(tenant_id=request.user.tenant_id, selection_status=SelectionStatusChoices.SELECTED).update(selection_status=SelectionStatusChoices.CANDIDATE)
        NextModuleRecommendation.objects.filter(tenant_id=request.user.tenant_id, selection_status=SelectionStatusChoices.SELECTED).update(selection_status=SelectionStatusChoices.CANDIDATE)
        NextModuleRejectionReason.objects.filter(tenant_id=request.user.tenant_id).delete()
        NextModuleSequencePlan.objects.filter(tenant_id=request.user.tenant_id).delete()

        selected_score = scores.first()
        selected_module = selected_score.module
        build_mode = _infer_build_mode(selected_module)
        why_selected = 'Highest current score on product continuity, dependency pressure, user-journey closure, and implementation readiness with acceptable ambiguity.'
        next_step = 'Start backend contracts and operational flow first, then expose frontend only after the runtime path is coherent.'

        selection, _ = NextModuleSelection.objects.update_or_create(
            module=selected_module,
            defaults={
                'tenant_id': request.user.tenant_id,
                'created_by': request.user.id,
                'candidate_status': selected_score.candidate_status,
                'criticality_score': selected_score.criticality_score,
                'dependency_score': selected_score.dependency_score,
                'journey_impact_score': selected_score.journey_impact_score,
                'frontend_gap_score': selected_score.frontend_gap_score,
                'backend_gap_score': selected_score.backend_gap_score,
                'readiness_score': selected_score.readiness_score,
                'ambiguity_score': selected_score.ambiguity_score,
                'delay_risk_score': min(10, selected_score.journey_impact_score + selected_score.dependency_score // 2),
                'final_selection_score': selected_score.final_selection_score,
                'selection_status': SelectionStatusChoices.SELECTED,
                'rejection_reason': '',
                'recommended_build_mode': build_mode,
                'recommended_owner_type': _candidate_owner_tool(selected_module),
                'recommended_next_step': next_step,
                'sequence_rank': 1,
                'notes': why_selected,
            },
        )
        NextModuleRecommendation.objects.update_or_create(
            module=selected_module,
            defaults={
                'tenant_id': request.user.tenant_id,
                'created_by': request.user.id,
                'selection_status': SelectionStatusChoices.SELECTED,
                'recommended_build_mode': build_mode,
                'recommended_owner_type': _candidate_owner_tool(selected_module),
                'recommended_next_step': next_step,
                'why_selected': why_selected,
                'notes': selected_score.notes,
            },
        )

        for rank, candidate in enumerate(scores, start=1):
            plan_mode = _infer_build_mode(candidate.module)
            NextModuleSequencePlan.objects.update_or_create(
                module=candidate.module,
                defaults={
                    'tenant_id': request.user.tenant_id,
                    'created_by': request.user.id,
                    'sequence_rank': rank,
                    'recommended_next_step': 'Begin after current selected module.' if rank > 1 else next_step,
                    'recommended_build_mode': plan_mode,
                    'prerequisite_summary': 'Requires current selected module to progress first.' if rank > 1 else 'Ready for immediate execution.',
                    'notes': candidate.notes,
                },
            )
            if candidate.module_id != selected_module.id:
                rejection_reason = 'Lower current priority due to weaker immediate journey closure, dependency urgency, or readiness.'
                if candidate.ambiguity_score >= 8:
                    rejection_reason = 'Deferred because business-rule ambiguity is too high for immediate execution.'
                NextModuleRejectionReason.objects.update_or_create(
                    module=candidate.module,
                    defaults={
                        'tenant_id': request.user.tenant_id,
                        'created_by': request.user.id,
                        'rejection_reason': rejection_reason,
                        'rejected_due_to': 'priority_gap' if candidate.ambiguity_score < 8 else 'ambiguity',
                        'sequence_rank': rank,
                    },
                )
                NextModuleSelection.objects.update_or_create(
                    module=candidate.module,
                    defaults={
                        'tenant_id': request.user.tenant_id,
                        'created_by': request.user.id,
                        'candidate_status': candidate.candidate_status,
                        'criticality_score': candidate.criticality_score,
                        'dependency_score': candidate.dependency_score,
                        'journey_impact_score': candidate.journey_impact_score,
                        'frontend_gap_score': candidate.frontend_gap_score,
                        'backend_gap_score': candidate.backend_gap_score,
                        'readiness_score': candidate.readiness_score,
                        'ambiguity_score': candidate.ambiguity_score,
                        'delay_risk_score': min(10, candidate.journey_impact_score + candidate.dependency_score // 2),
                        'final_selection_score': candidate.final_selection_score,
                        'selection_status': SelectionStatusChoices.REJECTED,
                        'rejection_reason': rejection_reason,
                        'recommended_build_mode': _infer_build_mode(candidate.module),
                        'recommended_owner_type': _candidate_owner_tool(candidate.module),
                        'recommended_next_step': 'Re-evaluate after selected module execution.',
                        'sequence_rank': rank,
                        'notes': candidate.notes,
                    },
                )

        _log_selection_event(selected_module, getattr(request.user, 'email', ''), 'selection.next_module.selected', {'module_key': selected_module.module_key, 'score': selected_score.final_selection_score})
        return success_response(data=NextModuleSelectionSerializer(selection).data, message='Next critical module selected.')


class SelectedNextModuleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        selection = NextModuleSelection.objects.filter(
            tenant_id=request.user.tenant_id,
            selection_status__in=[SelectionStatusChoices.SELECTED, SelectionStatusChoices.LOCKED],
        ).select_related('module').order_by('-final_selection_score').first()
        if not selection:
            return error_response('No selected module found.', status_code=status.HTTP_404_NOT_FOUND)
        return success_response(data=NextModuleSelectionSerializer(selection).data, message='Selected module retrieved.')


class WhySelectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        recommendation = NextModuleRecommendation.objects.filter(
            tenant_id=request.user.tenant_id,
            selection_status__in=[SelectionStatusChoices.SELECTED, SelectionStatusChoices.LOCKED],
        ).select_related('module').first()
        if not recommendation:
            return error_response('No selection recommendation found.', status_code=status.HTTP_404_NOT_FOUND)
        return success_response(data=NextModuleRecommendationSerializer(recommendation).data, message='Selection rationale retrieved.')


class WhyNotOthersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = NextModuleRejectionReason.objects.filter(tenant_id=request.user.tenant_id).select_related('module')
        serializer = NextModuleRejectionReasonSerializer(queryset, many=True)
        return success_response(data=serializer.data, message='Rejected candidate reasons retrieved.')


class LockNextModuleDecisionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not _can_manage_registry(request.user):
            return error_response('You do not have permission to lock the decision.', status_code=status.HTTP_403_FORBIDDEN)
        selection = NextModuleSelection.objects.filter(tenant_id=request.user.tenant_id, selection_status=SelectionStatusChoices.SELECTED).first()
        if not selection:
            return error_response('No selected module to lock.', status_code=status.HTTP_404_NOT_FOUND)
        selection.selection_status = SelectionStatusChoices.LOCKED
        selection.save(update_fields=['selection_status', 'updated_at'])
        _log_selection_event(selection.module, getattr(request.user, 'email', ''), 'selection.next_module.locked', {'module_key': selection.module.module_key})
        return success_response(data=NextModuleSelectionSerializer(selection).data, message='Next module decision locked.')


class UpdateNextModuleDecisionView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        if not _can_manage_registry(request.user):
            return error_response('You do not have permission to update the decision.', status_code=status.HTTP_403_FORBIDDEN)
        selection = NextModuleSelection.objects.filter(
            tenant_id=request.user.tenant_id,
            selection_status__in=[SelectionStatusChoices.SELECTED, SelectionStatusChoices.LOCKED],
        ).first()
        if not selection:
            return error_response('No selected module found.', status_code=status.HTTP_404_NOT_FOUND)
        serializer = NextModuleSelectionSerializer(selection, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        selection = serializer.save()
        _log_selection_event(selection.module, getattr(request.user, 'email', ''), 'selection.next_module.updated', serializer.validated_data)
        return success_response(data=NextModuleSelectionSerializer(selection).data, message='Next module decision updated.')


class ImmediateImplementationOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = NextModuleSequencePlan.objects.filter(tenant_id=request.user.tenant_id).select_related('module')
        serializer = NextModuleSequencePlanSerializer(queryset.order_by('sequence_rank'), many=True)
        return success_response(data=serializer.data, message='Immediate implementation order retrieved.')


class BackendFirstRecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = NextModuleSelection.objects.filter(
            tenant_id=request.user.tenant_id,
            recommended_build_mode=BuildModeChoices.BACKEND_FIRST,
            selection_status__in=[SelectionStatusChoices.SELECTED, SelectionStatusChoices.LOCKED],
        ).select_related('module')
        serializer = NextModuleSelectionSerializer(queryset, many=True)
        return success_response(data=serializer.data, message='Backend-first recommendation retrieved.')


class FrontendFirstRecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = NextModuleSelection.objects.filter(
            tenant_id=request.user.tenant_id,
            recommended_build_mode=BuildModeChoices.FRONTEND_FIRST,
            selection_status__in=[SelectionStatusChoices.SELECTED, SelectionStatusChoices.LOCKED],
        ).select_related('module')
        serializer = NextModuleSelectionSerializer(queryset, many=True)
        return success_response(data=serializer.data, message='Frontend-first recommendation retrieved.')


class BlockerPrerequisitesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        selection = NextModuleSelection.objects.filter(
            tenant_id=request.user.tenant_id,
            selection_status__in=[SelectionStatusChoices.SELECTED, SelectionStatusChoices.LOCKED],
        ).select_related('module').first()
        if not selection:
            return error_response('No selected module found.', status_code=status.HTTP_404_NOT_FOUND)
        prerequisites = ModuleDependencyChain.objects.filter(tenant_id=request.user.tenant_id, module=selection.module).select_related('depends_on')
        serializer = ModuleDependencyChainSerializer(prerequisites, many=True)
        return success_response(data=serializer.data, message='Blocker prerequisites retrieved.')


class FollowUpModuleSequenceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = NextModuleSequencePlan.objects.filter(tenant_id=request.user.tenant_id, sequence_rank__gt=1).select_related('module')
        serializer = NextModuleSequencePlanSerializer(queryset.order_by('sequence_rank'), many=True)
        return success_response(data=serializer.data, message='Follow-up module sequence retrieved.')


def _selected_module_for_prompt(tenant_id):
    return NextModuleSelection.objects.filter(
        tenant_id=tenant_id,
        selection_status__in=[SelectionStatusChoices.SELECTED, SelectionStatusChoices.LOCKED],
    ).select_related('module').order_by('-final_selection_score').first()


def _build_workflow_system_prompt(module, dependencies, follow_up):
    dependency_lines = '\n'.join([f'* {dep.depends_on.module_name}' for dep in dependencies]) or '* Jobs\n* Job Pipeline\n* Submissions'
    follow_up_lines = '\n'.join([f'{plan.sequence_rank}. {plan.module.module_name}' for plan in follow_up]) or '1. Job Pipeline\n2. Submissions\n3. Candidate Database'
    return f"""PROMPT ID: TOS-WORKFLOW-SYSTEM-IMPLEMENTATION-42
PROJECT: Talent Operating System
MODULE: Workflow System
TASK: Build Workflow System Core Execution Layer
ARCHITECTURE LEVEL: Enterprise Grade

==================================================
MASTER CONTEXT
==============

Use:

TOS-NEXT-CRITICAL-MODULE-SELECTION-40
TOS-REMAINING-CORE-MODULE-MAP-39
TOS-CORE-MODULE-REGISTRY-38
ICC-INTERVIEW-COMMAND-CENTER-COMPLETE-36
HDC-MASTER-FINAL-REVIEW-15

This module was selected as the single next critical core module.

==================================================
OBJECTIVE
=========

Build enterprise-grade Workflow System for Talent Operating System.

This module must become the state movement and orchestration core for:

* jobs
* job pipeline
* submissions
* recruiter actions
* candidate progression
* interview triggers
* hiring decision handoff

This is not a reporting layer.
This is the runtime workflow backbone for ATS continuity.

==================================================
SYSTEM PLACEMENT
================

Talent Operating System
↓
Jobs
↓
Workflow System ← CURRENT
↓
Pipeline / Submissions / ICC / HDC / Communications / Automation

==================================================
CORE SCOPE
==========

Build:

1. Workflow Definition Engine
2. Workflow State Engine
3. Stage Transition Engine
4. Candidate Progression Engine
5. Recruiter Action Engine
6. Workflow Rule Engine
7. Workflow Event Engine
8. Workflow Audit Engine
9. Workflow Read Model / Projection Layer
10. Workflow Admin Controls

==================================================
UI ARCHITECTURE REQUIRED
========================

Frontend must be included for operational surfaces that already exist in ATS:

### Recruiter UI

* workflow-aware candidate progression actions
* stage transition controls
* blocker visibility
* transition history
* workflow status summary

### Hiring / Ops UI

* stage policy visibility
* transition audit timeline
* workflow exception visibility

### Admin UI

* Django Admin visibility for workflow configs, states, transitions, and audit

==================================================
BACKEND ARCHITECTURE REQUIRED
=============================

Define and implement:

* workflow definitions
* workflow stages
* transition rules
* runtime candidate workflow state
* transition validation
* transition side effects
* event emission for downstream systems
* audit-safe state history

The backend must be contract-first and tenant-scoped.

==================================================
DATABASE DESIGN REQUIRED
========================

Include entities such as:

* workflow_definition
* workflow_stage
* workflow_transition_rule
* workflow_runtime_state
* workflow_transition_log
* workflow_event_log
* workflow_action_binding
* workflow_audit_log

Critical rule remains unchanged:
Candidate = Global Entity
Tenant association only
No ownership in core

==================================================
API STRUCTURE REQUIRED
======================

APIs must include at minimum:

* create workflow definition
* update workflow definition
* fetch workflow definition
* fetch workflow state for candidate
* move candidate to next stage
* move candidate to named stage
* validate transition
* fetch transition history
* fetch workflow audit trail
* fetch stage actions

==================================================
EXECUTION FLOW REQUIRED
=======================

1. Job uses workflow definition
2. Candidate enters workflow state
3. Recruiter or system triggers transition
4. Rule engine validates stage movement
5. Runtime state is updated
6. Audit trail is recorded
7. Events emit to pipeline, communication, ICC, HDC, automation, and analytics
8. Read models update for recruiter operations

==================================================
EDGE CASES REQUIRED
===================

Handle:

* invalid stage transition
* candidate already in terminal state
* stage moved while downstream action pending
* workflow definition changed after runtime state exists
* duplicate transition event
* recruiter action conflicts with automation-triggered move
* job closed while candidate still active in workflow
* stale UI action against newer runtime state

==================================================
INTEGRATION MAPPING
===================

Dependencies:
{dependency_lines}

Integrate with:

* jobs
* job pipeline
* submissions
* candidate database
* communications
* automation
* analytics
* ICC
* HDC

==================================================
IMPLEMENTATION ORDER
====================

1. backend workflow contracts and models
2. runtime state machine and transition validation
3. event emission and audit continuity
4. recruiter-facing stage action APIs
5. operational UI exposure
6. integration closure with pipeline / submissions / ICC / HDC

Follow-up modules after this:
{follow_up_lines}
"""


def _build_generated_prompt(selection, dependencies, follow_up):
    module = selection.module
    if module.module_key == 'workflow_system':
        return _build_workflow_system_prompt(module, dependencies, follow_up)
    return f"""PROMPT ID: TOS-{module.module_key.upper()}-IMPLEMENTATION
PROJECT: Talent Operating System
MODULE: {module.module_name}
TASK: Build {module.module_name}
ARCHITECTURE LEVEL: Enterprise Grade

Use module registry, remaining map, and selection context.
Dependencies:
{chr(10).join([f'* {dep.depends_on.module_name}' for dep in dependencies])}
"""


class GenerateImplementationPromptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not _can_manage_registry(request.user):
            return error_response('You do not have permission to generate prompts.', status_code=status.HTTP_403_FORBIDDEN)

        selection = _selected_module_for_prompt(request.user.tenant_id)
        if not selection:
            return error_response('No selected module found.', status_code=status.HTTP_404_NOT_FOUND)

        module = selection.module
        dependencies = ModuleDependencyChain.objects.filter(tenant_id=request.user.tenant_id, module=module).select_related('depends_on')
        follow_up = NextModuleSequencePlan.objects.filter(tenant_id=request.user.tenant_id).select_related('module').order_by('sequence_rank')[:5]
        prompt_body = _build_generated_prompt(selection, dependencies, follow_up)
        latest = GeneratedPrompt.objects.filter(tenant_id=request.user.tenant_id, module=module).order_by('-prompt_version').first()
        next_version = (latest.prompt_version + 1) if latest else 1

        generated = GeneratedPrompt.objects.create(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
            module=module,
            prompt_title=f'{module.module_name} Implementation Prompt',
            prompt_scope=selection.recommended_next_step,
            prompt_dependencies=[dep.depends_on.module_key for dep in dependencies],
            prompt_status=PromptStatusChoices.GENERATED,
            prompt_version=next_version,
            generated_by=getattr(request.user, 'email', '') or 'codex',
            prompt_body=prompt_body,
        )
        PromptContext.objects.create(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
            prompt=generated,
            module_key=module.module_key,
            context_payload={
                'selection': NextModuleSelectionSerializer(selection).data,
                'follow_up_sequence': NextModuleSequencePlanSerializer(follow_up, many=True).data,
            },
        )
        for dep in dependencies:
            PromptDependency.objects.create(
                tenant_id=request.user.tenant_id,
                created_by=request.user.id,
                prompt=generated,
                depends_on=dep.depends_on,
                notes=dep.notes,
            )
        for scope_type, payload in [
            ('ui_architecture', {'build_mode': selection.recommended_build_mode}),
            ('backend_architecture', {'backend_first': selection.recommended_build_mode == BuildModeChoices.BACKEND_FIRST}),
            ('integration_mapping', {'dependencies': [dep.depends_on.module_key for dep in dependencies]}),
        ]:
            PromptScope.objects.create(
                tenant_id=request.user.tenant_id,
                created_by=request.user.id,
                prompt=generated,
                scope_type=scope_type,
                scope_payload=payload,
            )
        PromptVersion.objects.create(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
            prompt=generated,
            prompt_version=next_version,
            version_snapshot={'prompt_body': prompt_body, 'prompt_status': generated.prompt_status},
        )
        PromptHistory.objects.create(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
            prompt=generated,
            event_type='prompt.generated',
            actor_name=getattr(request.user, 'email', '') or 'codex',
            event_payload={'prompt_version': next_version, 'module_key': module.module_key},
        )
        return success_response(data=GeneratedPromptSerializer(generated).data, message='Implementation prompt generated.', status_code=status.HTTP_201_CREATED)


class GeneratedPromptDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        selection = _selected_module_for_prompt(request.user.tenant_id)
        if not selection:
            return error_response('No selected module found.', status_code=status.HTTP_404_NOT_FOUND)
        prompt = GeneratedPrompt.objects.filter(tenant_id=request.user.tenant_id, module=selection.module).order_by('-prompt_version').first()
        if not prompt:
            return error_response('No generated prompt found.', status_code=status.HTTP_404_NOT_FOUND)
        return success_response(data=GeneratedPromptSerializer(prompt).data, message='Generated prompt retrieved.')


class RegeneratePromptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return GenerateImplementationPromptView().post(request)


class PromptHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        selection = _selected_module_for_prompt(request.user.tenant_id)
        if not selection:
            return error_response('No selected module found.', status_code=status.HTTP_404_NOT_FOUND)
        prompt = GeneratedPrompt.objects.filter(tenant_id=request.user.tenant_id, module=selection.module).order_by('-prompt_version').first()
        if not prompt:
            return error_response('No generated prompt found.', status_code=status.HTTP_404_NOT_FOUND)
        queryset = PromptHistory.objects.filter(tenant_id=request.user.tenant_id, prompt=prompt)
        return success_response(data=PromptHistorySerializer(queryset, many=True).data, message='Prompt history retrieved.')


class ApprovePromptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        selection = _selected_module_for_prompt(request.user.tenant_id)
        if not selection:
            return error_response('No selected module found.', status_code=status.HTTP_404_NOT_FOUND)
        prompt = GeneratedPrompt.objects.filter(tenant_id=request.user.tenant_id, module=selection.module).order_by('-prompt_version').first()
        if not prompt:
            return error_response('No generated prompt found.', status_code=status.HTTP_404_NOT_FOUND)
        prompt.prompt_status = PromptStatusChoices.APPROVED
        prompt.approved_by = getattr(request.user, 'email', '') or 'codex'
        prompt.save(update_fields=['prompt_status', 'approved_by', 'updated_at'])
        PromptHistory.objects.create(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
            prompt=prompt,
            event_type='prompt.approved',
            actor_name=prompt.approved_by,
            event_payload={'prompt_version': prompt.prompt_version},
        )
        return success_response(data=GeneratedPromptSerializer(prompt).data, message='Prompt approved.')


class LockPromptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        selection = _selected_module_for_prompt(request.user.tenant_id)
        if not selection:
            return error_response('No selected module found.', status_code=status.HTTP_404_NOT_FOUND)
        prompt = GeneratedPrompt.objects.filter(tenant_id=request.user.tenant_id, module=selection.module).order_by('-prompt_version').first()
        if not prompt:
            return error_response('No generated prompt found.', status_code=status.HTTP_404_NOT_FOUND)
        prompt.prompt_status = PromptStatusChoices.LOCKED
        prompt.save(update_fields=['prompt_status', 'updated_at'])
        PromptHistory.objects.create(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
            prompt=prompt,
            event_type='prompt.locked',
            actor_name=getattr(request.user, 'email', '') or 'codex',
            event_payload={'prompt_version': prompt.prompt_version},
        )
        return success_response(data=GeneratedPromptSerializer(prompt).data, message='Prompt locked.')


class PromptSelectedModuleContextView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        selection = _selected_module_for_prompt(request.user.tenant_id)
        if not selection:
            return error_response('No selected module found.', status_code=status.HTTP_404_NOT_FOUND)
        return success_response(data=NextModuleSelectionSerializer(selection).data, message='Selected module context retrieved.')


class PromptModuleDependenciesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        selection = _selected_module_for_prompt(request.user.tenant_id)
        if not selection:
            return error_response('No selected module found.', status_code=status.HTTP_404_NOT_FOUND)
        dependencies = ModuleDependencyChain.objects.filter(tenant_id=request.user.tenant_id, module=selection.module).select_related('depends_on')
        return success_response(data=ModuleDependencyChainSerializer(dependencies, many=True).data, message='Module dependencies retrieved.')


class PromptModuleContextView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        selection = _selected_module_for_prompt(request.user.tenant_id)
        if not selection:
            return error_response('No selected module found.', status_code=status.HTTP_404_NOT_FOUND)
        module = selection.module
        payload = {
            'module': ModuleRegistrySerializer(module).data,
            'remaining_map': RemainingModuleMapSerializer(getattr(module, 'remaining_map', None)).data if hasattr(module, 'remaining_map') else None,
            'selection': NextModuleSelectionSerializer(selection).data,
        }
        return success_response(data=payload, message='Module context retrieved.')


class PromptIntegrationMappingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        selection = _selected_module_for_prompt(request.user.tenant_id)
        if not selection:
            return error_response('No selected module found.', status_code=status.HTTP_404_NOT_FOUND)
        dependencies = ModuleDependencyChain.objects.filter(tenant_id=request.user.tenant_id, module=selection.module).select_related('depends_on')
        payload = {
            'module_key': selection.module.module_key,
            'dependencies': ModuleDependencyChainSerializer(dependencies, many=True).data,
            'follow_up_sequence': NextModuleSequencePlanSerializer(
                NextModuleSequencePlan.objects.filter(tenant_id=request.user.tenant_id).select_related('module').order_by('sequence_rank')[:5],
                many=True,
            ).data,
        }
        return success_response(data=payload, message='Integration mapping retrieved.')
