from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.models import CustomUser
from apps.candidates.models import Candidate
from apps.core.responses import error_response, success_response
from apps.jobs.models import JobRequisition
from apps.organisations.models import Organisation
from apps.orchestration_center.models import IntelligenceAuditLog
from apps.orchestration_center.services.audit_service import AuditService
from apps.tenants.admin_serializers import (
    PlatformSettingsBulkUpdateSerializer,
    PlatformSettingSerializer,
    TenantFeatureFlagsUpdateSerializer,
    TenantLimitsUpdateSerializer,
    TenantStatusActionSerializer,
)
from apps.tenants.models import Client, PlatformSetting
from apps.tenants.permissions import IsSuperAdmin


DEFAULT_PLATFORM_SETTINGS = (
    {
        'key': 'tenant_activation_requires_verification',
        'category': 'tenant_governance',
        'value_json': {'enabled': True},
        'description': 'Require explicit verification before tenant activation.',
    },
    {
        'key': 'default_tenant_limits',
        'category': 'tenant_limits',
        'value_json': {'user_limit': 50, 'job_limit': 100, 'candidate_limit': 5000},
        'description': 'Default tenant limits applied when no custom limits are set.',
    },
    {
        'key': 'default_feature_flags',
        'category': 'features',
        'value_json': {'agency_intelligence': True, 'automation_center': True, 'interview_ai': True},
        'description': 'Default feature flags for new tenants.',
    },
)


def _audit(*, actor, action_type, target_type, target_id=None, before_state=None, after_state=None, metadata=None):
    AuditService.log(
        tenant_id=actor.tenant_id,
        actor_id=actor.id,
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        before_state_json=before_state or {},
        after_state_json=after_state or {},
        metadata_json=metadata or {},
    )


def _tenant_usage(tenant_id):
    return {
        'users_total': CustomUser.objects.filter(tenant_id=tenant_id, is_deleted=False).count(),
        'users_active': CustomUser.objects.filter(tenant_id=tenant_id, is_deleted=False, is_active=True).count(),
        'jobs_total': JobRequisition.objects.filter(tenant_id=tenant_id, is_deleted=False).count(),
        'candidates_total': Candidate.objects.filter(tenant_id=tenant_id, is_deleted=False).count(),
    }


def _tenant_config(tenant_id):
    org = Organisation.objects.filter(tenant_id=tenant_id, is_deleted=False).first()
    settings = (org.settings if org and isinstance(org.settings, dict) else {}) if org else {}
    limits = settings.get('limits', {}) if isinstance(settings.get('limits', {}), dict) else {}
    feature_flags = settings.get('feature_flags', {}) if isinstance(settings.get('feature_flags', {}), dict) else {}
    return org, limits, feature_flags


def _get_or_create_org_for_tenant(tenant):
    org = Organisation.objects.filter(tenant_id=tenant.id, is_deleted=False).first()
    if org:
        return org
    return Organisation.objects.create(
        tenant_id=tenant.id,
        name=tenant.name,
        org_type='agency' if tenant.tenant_type == 'agency' else 'company',
        metadata={},
        settings={},
    )


def _tenant_summary_payload(tenant):
    org, limits, feature_flags = _tenant_config(tenant.id)
    meta = (org.metadata if org and isinstance(org.metadata, dict) else {}) if org else {}
    verification_state = meta.get('verification_state', 'unverified')
    created_at = None
    if org and hasattr(org, 'created_at'):
        created_at = org.created_at
    elif hasattr(tenant, 'created_at'):
        created_at = tenant.created_at
    return {
        'id': str(tenant.id),
        'schema_name': tenant.schema_name,
        'name': tenant.name,
        'tenant_type': tenant.tenant_type,
        'status': tenant.status,
        'verification_state': verification_state,
        'created_at': created_at,
        'limits': limits,
        'feature_flags': feature_flags,
        'usage': _tenant_usage(tenant.id),
        'organisation': {
            'name': org.name if org else None,
            'industry': org.industry if org else None,
            'country_code': org.country_code if org else tenant.country_code,
            'website': org.website if org else tenant.website,
        },
    }


class MasterAdminTenantListView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        tenant_type = request.query_params.get('tenant_type')
        status_filter = request.query_params.get('status')
        search = request.query_params.get('search', '').strip()

        qs = Client.objects.filter(is_deleted=False).order_by('-created_at')
        if tenant_type in {'company', 'agency', 'candidate_pool'}:
            qs = qs.filter(tenant_type=tenant_type)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if search:
            qs = qs.filter(name__icontains=search)

        tenants = [_tenant_summary_payload(tenant) for tenant in qs[:200]]
        return success_response(
            data={'tenants': tenants},
            message='Master admin tenant list retrieved.',
            meta={'total': qs.count()},
        )


class MasterAdminTenantDetailView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request, tenant_id):
        tenant = Client.objects.filter(id=tenant_id, is_deleted=False).first()
        if not tenant:
            return error_response('Tenant not found.', status_code=status.HTTP_404_NOT_FOUND)

        payload = _tenant_summary_payload(tenant)
        recent_activity = IntelligenceAuditLog.objects.filter(tenant_id=tenant.id).order_by('-created_at')[:20]
        payload['recent_activity_summary'] = {
            'last_7_days_actions': IntelligenceAuditLog.objects.filter(
                tenant_id=tenant.id,
                created_at__gte=timezone.now() - timedelta(days=7),
            ).count(),
            'recent_actions': [
                {
                    'id': row.id,
                    'action_type': row.action_type,
                    'target_type': row.target_type,
                    'target_id': str(row.target_id) if row.target_id else None,
                    'created_at': row.created_at,
                }
                for row in recent_activity
            ],
        }
        return success_response(
            data={'tenant': payload},
            message='Master admin tenant detail retrieved.',
        )


class MasterAdminTenantVerifyView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request, tenant_id):
        tenant = Client.objects.filter(id=tenant_id, is_deleted=False).first()
        if not tenant:
            return error_response('Tenant not found.', status_code=status.HTTP_404_NOT_FOUND)

        org = _get_or_create_org_for_tenant(tenant)
        before_meta = dict(org.metadata or {})
        updated_meta = dict(before_meta)
        updated_meta.update(
            {
                'verification_state': 'verified',
                'verified_at': timezone.now().isoformat(),
                'verified_by': str(request.user.id),
            }
        )
        org.metadata = updated_meta
        org.save(update_fields=['metadata', 'updated_at'])

        _audit(
            actor=request.user,
            action_type='master_admin.tenant_verified',
            target_type='tenant',
            target_id=tenant.id,
            before_state={'metadata': before_meta},
            after_state={'metadata': updated_meta},
            metadata={'tenant_id': str(tenant.id)},
        )
        return success_response(data={'tenant': _tenant_summary_payload(tenant)}, message='Tenant verified.')


class MasterAdminTenantSuspendView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request, tenant_id):
        serializer = TenantStatusActionSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)

        tenant = Client.objects.filter(id=tenant_id, is_deleted=False).first()
        if not tenant:
            return error_response('Tenant not found.', status_code=status.HTTP_404_NOT_FOUND)
        if tenant.status == 'terminated':
            return error_response('Terminated tenant cannot be suspended.', status_code=status.HTTP_409_CONFLICT)

        org = _get_or_create_org_for_tenant(tenant)
        before_status = tenant.status
        tenant.status = 'suspended'
        metadata = dict(org.metadata or {})
        metadata['suspended_reason'] = serializer.validated_data.get('reason', '')
        metadata['suspended_at'] = timezone.now().isoformat()
        metadata['suspended_by'] = str(request.user.id)
        tenant.save(update_fields=['status'])
        org.metadata = metadata
        org.save(update_fields=['metadata', 'updated_at'])

        _audit(
            actor=request.user,
            action_type='master_admin.tenant_suspended',
            target_type='tenant',
            target_id=tenant.id,
            before_state={'status': before_status},
            after_state={'status': tenant.status},
            metadata={'reason': serializer.validated_data.get('reason', '')},
        )
        return success_response(data={'tenant': _tenant_summary_payload(tenant)}, message='Tenant suspended.')


class MasterAdminTenantReactivateView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request, tenant_id):
        serializer = TenantStatusActionSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)

        tenant = Client.objects.filter(id=tenant_id, is_deleted=False).first()
        if not tenant:
            return error_response('Tenant not found.', status_code=status.HTTP_404_NOT_FOUND)
        if tenant.status == 'terminated':
            return error_response('Terminated tenant cannot be reactivated.', status_code=status.HTTP_409_CONFLICT)

        org = _get_or_create_org_for_tenant(tenant)
        before_status = tenant.status
        tenant.status = 'active'
        metadata = dict(org.metadata or {})
        metadata['reactivated_at'] = timezone.now().isoformat()
        metadata['reactivated_by'] = str(request.user.id)
        if serializer.validated_data.get('reason'):
            metadata['reactivated_reason'] = serializer.validated_data.get('reason')
        tenant.save(update_fields=['status'])
        org.metadata = metadata
        org.save(update_fields=['metadata', 'updated_at'])

        _audit(
            actor=request.user,
            action_type='master_admin.tenant_reactivated',
            target_type='tenant',
            target_id=tenant.id,
            before_state={'status': before_status},
            after_state={'status': tenant.status},
            metadata={'reason': serializer.validated_data.get('reason', '')},
        )
        return success_response(data={'tenant': _tenant_summary_payload(tenant)}, message='Tenant reactivated.')


class MasterAdminTenantDeactivateView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request, tenant_id):
        serializer = TenantStatusActionSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)

        tenant = Client.objects.filter(id=tenant_id, is_deleted=False).first()
        if not tenant:
            return error_response('Tenant not found.', status_code=status.HTTP_404_NOT_FOUND)

        org = _get_or_create_org_for_tenant(tenant)
        before_status = tenant.status
        tenant.status = 'terminated'
        metadata = dict(org.metadata or {})
        metadata['terminated_reason'] = serializer.validated_data.get('reason', '')
        metadata['terminated_at'] = timezone.now().isoformat()
        metadata['terminated_by'] = str(request.user.id)
        tenant.save(update_fields=['status'])
        org.metadata = metadata
        org.save(update_fields=['metadata', 'updated_at'])

        _audit(
            actor=request.user,
            action_type='master_admin.tenant_deactivated',
            target_type='tenant',
            target_id=tenant.id,
            before_state={'status': before_status},
            after_state={'status': tenant.status},
            metadata={'reason': serializer.validated_data.get('reason', '')},
        )
        return success_response(data={'tenant': _tenant_summary_payload(tenant)}, message='Tenant safely deactivated.')


class MasterAdminTenantFeatureFlagsView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def put(self, request, tenant_id):
        serializer = TenantFeatureFlagsUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tenant = Client.objects.filter(id=tenant_id, is_deleted=False).first()
        if not tenant:
            return error_response('Tenant not found.', status_code=status.HTTP_404_NOT_FOUND)

        org = Organisation.objects.filter(tenant_id=tenant.id, is_deleted=False).first()
        if not org:
            return error_response('Organisation not found for tenant.', status_code=status.HTTP_404_NOT_FOUND)

        settings = dict(org.settings or {})
        before = settings.get('feature_flags', {})
        settings['feature_flags'] = serializer.validated_data['feature_flags']
        org.settings = settings
        org.save(update_fields=['settings', 'updated_at'])

        _audit(
            actor=request.user,
            action_type='master_admin.tenant_feature_flags_updated',
            target_type='tenant',
            target_id=tenant.id,
            before_state={'feature_flags': before},
            after_state={'feature_flags': settings['feature_flags']},
            metadata={'tenant_id': str(tenant.id)},
        )
        return success_response(
            data={'tenant_id': str(tenant.id), 'feature_flags': settings['feature_flags']},
            message='Tenant feature flags updated.',
        )


class MasterAdminTenantLimitsView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def put(self, request, tenant_id):
        serializer = TenantLimitsUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tenant = Client.objects.filter(id=tenant_id, is_deleted=False).first()
        if not tenant:
            return error_response('Tenant not found.', status_code=status.HTTP_404_NOT_FOUND)

        org = Organisation.objects.filter(tenant_id=tenant.id, is_deleted=False).first()
        if not org:
            return error_response('Organisation not found for tenant.', status_code=status.HTTP_404_NOT_FOUND)

        settings = dict(org.settings or {})
        limits = dict(settings.get('limits', {}))
        before_limits = dict(limits)
        for key, value in serializer.validated_data.items():
            limits[key] = int(value)
        settings['limits'] = limits
        org.settings = settings
        org.save(update_fields=['settings', 'updated_at'])

        _audit(
            actor=request.user,
            action_type='master_admin.tenant_limits_updated',
            target_type='tenant',
            target_id=tenant.id,
            before_state={'limits': before_limits},
            after_state={'limits': limits},
            metadata={'tenant_id': str(tenant.id)},
        )
        return success_response(
            data={'tenant_id': str(tenant.id), 'limits': limits},
            message='Tenant usage limits updated.',
        )


class MasterAdminPlatformSettingsView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def _ensure_defaults(self):
        for payload in DEFAULT_PLATFORM_SETTINGS:
            PlatformSetting.objects.get_or_create(
                key=payload['key'],
                defaults=payload,
            )

    def get(self, request):
        self._ensure_defaults()
        settings_qs = PlatformSetting.objects.all().order_by('category', 'key')
        return success_response(
            data={'settings': PlatformSettingSerializer(settings_qs, many=True).data},
            message='Platform settings retrieved.',
        )

    @transaction.atomic
    def put(self, request):
        serializer = PlatformSettingsBulkUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_rows = []
        for raw in serializer.validated_data['settings']:
            key = raw.get('key')
            if not key:
                return error_response('Each setting update requires a key.', status_code=status.HTTP_400_BAD_REQUEST)

            row = PlatformSetting.objects.filter(key=key).first()
            if not row:
                return error_response(f"Unknown platform setting '{key}'.", status_code=status.HTTP_404_NOT_FOUND)
            if not row.is_editable:
                return error_response(f"Platform setting '{key}' is read-only.", status_code=status.HTTP_409_CONFLICT)

            before_value = row.value_json
            row.value_json = raw.get('value_json', row.value_json)
            if 'description' in raw:
                row.description = raw.get('description') or row.description
            row.updated_by = request.user.id
            row.save(update_fields=['value_json', 'description', 'updated_by', 'updated_at'])

            _audit(
                actor=request.user,
                action_type='master_admin.platform_setting_updated',
                target_type='platform_setting',
                metadata={'key': row.key},
                before_state={'value_json': before_value},
                after_state={'value_json': row.value_json},
            )
            updated_rows.append(row)

        return success_response(
            data={'settings': PlatformSettingSerializer(updated_rows, many=True).data},
            message='Platform settings updated.',
        )


class MasterAdminAuditLogView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        qs = IntelligenceAuditLog.objects.filter(action_type__startswith='master_admin.').order_by('-created_at')

        action_type = request.query_params.get('action_type')
        if action_type:
            qs = qs.filter(action_type=action_type)

        target_type = request.query_params.get('target_type')
        if target_type:
            qs = qs.filter(target_type=target_type)

        tenant_id = request.query_params.get('tenant_id')
        if tenant_id:
            qs = qs.filter(target_id=tenant_id)

        limit = min(int(request.query_params.get('limit', 100)), 500)
        rows = qs[:limit]
        payload = [
            {
                'id': row.id,
                'tenant_id': str(row.tenant_id) if row.tenant_id else None,
                'actor_id': str(row.actor_id) if row.actor_id else None,
                'action_type': row.action_type,
                'target_type': row.target_type,
                'target_id': str(row.target_id) if row.target_id else None,
                'before_state_json': row.before_state_json,
                'after_state_json': row.after_state_json,
                'metadata_json': row.metadata_json,
                'created_at': row.created_at,
            }
            for row in rows
        ]
        return success_response(
            data={'audit_entries': payload},
            message='Master admin audit entries retrieved.',
            meta={'total': qs.count(), 'limit': limit},
        )
