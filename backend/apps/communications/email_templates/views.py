from django.db import DatabaseError, ProgrammingError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.communications.email_audit.services import EmailAuditService
from apps.communications.feature_readiness import email_not_ready_response, get_email_feature_status
from apps.communications.email_templates.serializers import EmailTemplateDefinitionSerializer, QuickReplyTemplateSerializer
from apps.communications.email_templates.services import EmailTemplateService
from apps.communications.models import EmailTemplateDefinition, EmailTemplateScope, QuickReplyTemplate
from apps.communications.permissions import (
    can_manage_email_templates,
    can_manage_quick_replies,
    can_view_email_templates,
)
from apps.core.responses import error_response, success_response


class EmailTemplateListCreateView(APIView):
    permission_classes = [IsAuthenticated, can_view_email_templates]

    def get(self, request):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response(empty_data={'email_templates': []})
        try:
            EmailTemplateService.seed_defaults_for_tenant(str(request.user.tenant_id), str(request.user.id))
        except (ProgrammingError, DatabaseError):
            return email_not_ready_response(empty_data={'email_templates': []})
        template_type = request.query_params.get('template_type')
        category = request.query_params.get('category')
        try:
            qs = EmailTemplateDefinition.objects.filter(
                Q(tenant_id=request.user.tenant_id) | Q(template_scope=EmailTemplateScope.SYSTEM_DEFAULT, tenant_id__isnull=True),
                is_active=True,
            ).order_by('name')
        except (ProgrammingError, DatabaseError):
            return email_not_ready_response(empty_data={'email_templates': []})
        if template_type:
            qs = qs.filter(template_type=template_type)
        if category:
            qs = qs.filter(category=category)
        return success_response(data={'email_templates': EmailTemplateDefinitionSerializer(qs, many=True).data})

    def post(self, request):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response(empty_data={'email_template': None})
        if not can_manage_email_templates().has_permission(request, self):
            return error_response('Permission denied', status_code=status.HTTP_403_FORBIDDEN)
        serializer = EmailTemplateDefinitionSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response('Validation failed', serializer.errors)
        try:
            template = serializer.save(
                tenant_id=request.user.tenant_id,
                created_by=request.user.id,
                template_scope=serializer.validated_data.get('template_scope', EmailTemplateScope.TENANT_CUSTOM),
            )
        except (ProgrammingError, DatabaseError):
            return email_not_ready_response(empty_data={'email_template': None})
        EmailAuditService.record_usage(
            tenant_id=request.user.tenant_id,
            actor_user_id=request.user.id,
            action='email_template.created',
            target_type='email_template',
            target_id=template.id,
            details={'name': template.name, 'template_type': template.template_type},
        )
        return success_response(data={'email_template': EmailTemplateDefinitionSerializer(template).data}, status_code=status.HTTP_201_CREATED)


class EmailTemplateUpdateView(APIView):
    permission_classes = [IsAuthenticated, can_manage_email_templates]

    def patch(self, request, pk):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response(empty_data={'email_template': None})
        try:
            template = get_object_or_404(
                EmailTemplateDefinition,
                id=pk,
                tenant_id=request.user.tenant_id,
            )
        except (ProgrammingError, DatabaseError):
            return email_not_ready_response(empty_data={'email_template': None})
        if template.is_system_locked:
            return error_response('System template is locked.')

        serializer = EmailTemplateDefinitionSerializer(template, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response('Validation failed', serializer.errors)
        serializer.save()
        EmailAuditService.record_usage(
            tenant_id=request.user.tenant_id,
            actor_user_id=request.user.id,
            action='email_template.updated',
            target_type='email_template',
            target_id=template.id,
            details=serializer.validated_data,
        )
        return success_response(data={'email_template': serializer.data})


class EmailTemplateDuplicateView(APIView):
    permission_classes = [IsAuthenticated, can_manage_email_templates]

    def post(self, request, pk):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response(empty_data={'email_template': None})
        try:
            template = get_object_or_404(EmailTemplateDefinition, id=pk)
            duplicate = EmailTemplateService.duplicate_template(
                source=template,
                tenant_id=str(request.user.tenant_id),
                created_by=str(request.user.id),
            )
        except (ProgrammingError, DatabaseError):
            return email_not_ready_response(empty_data={'email_template': None})
        return success_response(data={'email_template': EmailTemplateDefinitionSerializer(duplicate).data}, status_code=status.HTTP_201_CREATED)


class EmailTemplatePreviewView(APIView):
    permission_classes = [IsAuthenticated, can_view_email_templates]

    def post(self, request, pk):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response(empty_data={'preview': {'subject': '', 'body_html': '', 'body_text': ''}})
        try:
            template = get_object_or_404(EmailTemplateDefinition, id=pk)
            variables = request.data.get('variables', {})
            rendered = EmailTemplateService.render_template(template, variables)
        except (ProgrammingError, DatabaseError):
            return email_not_ready_response(empty_data={'preview': {'subject': '', 'body_html': '', 'body_text': ''}})
        return success_response(data={'preview': rendered})


class QuickReplyListCreateView(APIView):
    permission_classes = [IsAuthenticated, can_view_email_templates]

    def get(self, request):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response(empty_data={'quick_replies': []})
        try:
            EmailTemplateService.seed_defaults_for_tenant(str(request.user.tenant_id), str(request.user.id))
            qs = QuickReplyTemplate.objects.filter(tenant_id=request.user.tenant_id, is_active=True).filter(
                Q(user_id=request.user.id) | Q(user_id__isnull=True)
            ).order_by('name')
        except (ProgrammingError, DatabaseError):
            return email_not_ready_response(empty_data={'quick_replies': []})
        return success_response(data={'quick_replies': QuickReplyTemplateSerializer(qs, many=True).data})

    def post(self, request):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response(empty_data={'quick_reply': None})
        if not can_manage_quick_replies().has_permission(request, self):
            return error_response('Permission denied', status_code=status.HTTP_403_FORBIDDEN)
        serializer = QuickReplyTemplateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response('Validation failed', serializer.errors)
        try:
            quick = serializer.save(tenant_id=request.user.tenant_id, user_id=request.user.id)
        except (ProgrammingError, DatabaseError):
            return email_not_ready_response(empty_data={'quick_reply': None})
        return success_response(data={'quick_reply': QuickReplyTemplateSerializer(quick).data}, status_code=status.HTTP_201_CREATED)


class QuickReplyUpdateView(APIView):
    permission_classes = [IsAuthenticated, can_manage_quick_replies]

    def patch(self, request, pk):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response(empty_data={'quick_reply': None})
        try:
            quick = get_object_or_404(QuickReplyTemplate, id=pk, tenant_id=request.user.tenant_id)
        except (ProgrammingError, DatabaseError):
            return email_not_ready_response(empty_data={'quick_reply': None})
        serializer = QuickReplyTemplateSerializer(quick, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response('Validation failed', serializer.errors)
        serializer.save()
        return success_response(data={'quick_reply': serializer.data})
