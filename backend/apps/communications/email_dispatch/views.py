from django.db import DatabaseError, ProgrammingError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.communications.email_dispatch.dispatch import EmailDispatchService
from apps.communications.email_dispatch.serializers import EmailMessageSerializer, EmailSendSerializer
from apps.communications.email_dispatch.types import EmailSendRequest
from apps.communications.feature_readiness import email_not_ready_response, get_email_feature_status
from apps.communications.email_templates.services import EmailTemplateService
from apps.communications.models import EmailMessage, EmailTemplateDefinition
from apps.communications.permissions import can_send_email
from apps.core.responses import error_response, success_response


def _build_template_context(
    *,
    request,
    candidate_id: str | None = None,
    job_id: str | None = None,
    interview_id: str | None = None,
    offer_id: str | None = None,
) -> dict:
    """
    Build the full variable context dict for template rendering.
    All keys match the {{ tag }} names defined in the tag system.
    Missing data falls back to empty string — never raises.
    """
    ctx: dict = {}

    # ── System ────────────────────────────────────────────────────────────────
    ctx['today_date'] = timezone.now().strftime('%B %d, %Y')
    ctx['support_email'] = 'support@talentos.app'

    # ── Recruiter (current user) ───────────────────────────────────────────────
    user = request.user
    ctx['recruiter_name'] = f'{user.first_name} {user.last_name}'.strip() or user.email
    ctx['recruiter_first_name'] = user.first_name or ''
    ctx['recruiter_email'] = user.email or ''
    ctx['recruiter_phone'] = getattr(user, 'phone', '') or ''
    ctx['sender_name'] = ctx['recruiter_name']
    ctx['sender_email'] = ctx['recruiter_email']

    # ── Tenant / company ──────────────────────────────────────────────────────
    tenant_id = getattr(user, 'tenant_id', None)
    ctx['tenant_name'] = ''
    ctx['company_name'] = ''
    ctx['company_email'] = ''
    ctx['company_phone'] = ''
    ctx['company_website'] = ''
    ctx['agency_name'] = ''
    ctx['agency_email'] = ''
    ctx['agency_phone'] = ''
    if tenant_id:
        try:
            from apps.organisations.models import Organisation
            org = Organisation.objects.filter(tenant_id=tenant_id).first()
            if org:
                ctx['tenant_name'] = org.name
                ctx['company_name'] = org.name
                ctx['company_website'] = org.website or ''
                ctx['company_phone'] = org.contact_phone_number or ''
                if org.org_type == 'agency':
                    ctx['agency_name'] = org.name
                    ctx['agency_phone'] = org.contact_phone_number or ''
        except Exception:
            pass

    # ── Candidate ─────────────────────────────────────────────────────────────
    ctx['candidate_first_name'] = ''
    ctx['candidate_last_name'] = ''
    ctx['candidate_full_name'] = ''
    ctx['candidate_email'] = ''
    ctx['candidate_phone'] = ''
    ctx['candidate_location'] = ''
    ctx['candidate_notice_period'] = ''
    ctx['candidate_current_company'] = ''
    ctx['candidate_current_role'] = ''
    ctx['candidate_experience_years'] = ''
    ctx['candidate_expected_salary'] = ''
    ctx['candidate_availability_date'] = ''
    if candidate_id:
        try:
            from apps.candidates.models import Candidate
            c = Candidate.objects.filter(id=candidate_id, is_deleted=False).first()
            if c:
                ctx['candidate_first_name'] = c.first_name or ''
                ctx['candidate_last_name'] = c.last_name or ''
                ctx['candidate_full_name'] = f'{c.first_name} {c.last_name}'.strip()
                ctx['candidate_email'] = c.email or ''
                ctx['candidate_phone'] = c.phone or ''
                ctx['candidate_location'] = ', '.join(
                    x for x in [c.current_location_city, c.current_location_country] if x
                )
                ctx['candidate_notice_period'] = (
                    f'{c.notice_period_days} days' if c.notice_period_days else ''
                )
                ctx['candidate_current_company'] = c.current_company or ''
                ctx['candidate_current_role'] = c.current_title or ''
                ctx['candidate_experience_years'] = (
                    f'{c.experience_years} years' if c.experience_years else ''
                )
                if c.expected_salary_min and c.expected_salary_max:
                    ctx['candidate_expected_salary'] = (
                        f'{c.salary_currency} {c.expected_salary_min}–{c.expected_salary_max}'
                    )
                elif c.expected_salary_min:
                    ctx['candidate_expected_salary'] = f'{c.salary_currency} {c.expected_salary_min}+'
                ctx['candidate_availability_date'] = (
                    c.availability_date.strftime('%B %d, %Y') if c.availability_date else ''
                )
                # Also resolve job from active_job_id if no explicit job_id given
                if not job_id and c.active_job_id:
                    job_id = str(c.active_job_id)
        except Exception:
            pass

    # ── Job ───────────────────────────────────────────────────────────────────
    ctx['job_title'] = ''
    ctx['job_code'] = ''
    ctx['job_location'] = ''
    ctx['job_type'] = ''
    ctx['job_department'] = ''
    ctx['job_salary_range'] = ''
    ctx['job_work_mode'] = ''
    if job_id:
        try:
            from apps.jobs.models import JobRequisition
            j = JobRequisition.objects.filter(id=job_id).first()
            if j:
                ctx['job_title'] = j.title or ''
                ctx['job_type'] = j.job_type or ''
                ctx['job_work_mode'] = j.work_mode or ''
                if j.salary_min and j.salary_max:
                    ctx['job_salary_range'] = (
                        f'{j.salary_currency} {j.salary_min}–{j.salary_max}'
                    )
        except Exception:
            pass

    # ── Interview ─────────────────────────────────────────────────────────────
    ctx['interview_date'] = ''
    ctx['interview_time'] = ''
    ctx['interview_datetime'] = ''
    ctx['interview_mode'] = ''
    ctx['interview_location'] = ''
    ctx['meeting_link'] = ''
    ctx['interviewer_name'] = ''
    if interview_id:
        try:
            from apps.interviews.models import Interview
            iv = Interview.objects.filter(id=interview_id).first()
            if iv and iv.scheduled_at:
                ctx['interview_date'] = iv.scheduled_at.strftime('%B %d, %Y')
                ctx['interview_time'] = iv.scheduled_at.strftime('%I:%M %p')
                ctx['interview_datetime'] = iv.scheduled_at.strftime('%B %d, %Y at %I:%M %p')
            if iv:
                ctx['interview_mode'] = iv.interview_type or ''
                ctx['meeting_link'] = iv.interview_link or ''
        except Exception:
            pass

    # ── Offer ─────────────────────────────────────────────────────────────────
    ctx['offer_title'] = ctx.get('job_title', '')
    ctx['offer_salary'] = ''
    ctx['offer_joining_date'] = ''
    ctx['offer_expiry_date'] = ''
    if offer_id:
        try:
            from apps.documents.models import OfferLetter
            o = OfferLetter.objects.filter(id=offer_id).first()
            if o:
                ctx['offer_title'] = o.title or ctx.get('job_title', '')
                if o.offered_salary:
                    ctx['offer_salary'] = f'{o.currency} {o.offered_salary}'
                ctx['offer_joining_date'] = (
                    o.joining_date.strftime('%B %d, %Y') if o.joining_date else ''
                )
        except Exception:
            pass

    return ctx


class EmailRenderTemplateView(APIView):
    """
    POST /communications/email/render-template

    Resolves all template variables from DB using entity IDs,
    renders the template, and returns subject + body + list of unresolved tags.
    """
    permission_classes = [IsAuthenticated, can_send_email]

    def post(self, request):
        template_id = request.data.get('template_id')
        if not template_id:
            return error_response('template_id is required.')

        try:
            template = get_object_or_404(EmailTemplateDefinition, id=template_id)
        except Exception:
            return error_response('Template not found.', status_code=status.HTTP_404_NOT_FOUND)

        ctx = _build_template_context(
            request=request,
            candidate_id=request.data.get('candidate_id'),
            job_id=request.data.get('job_id'),
            interview_id=request.data.get('interview_id'),
            offer_id=request.data.get('offer_id'),
        )

        rendered = EmailTemplateService.render_template(template, ctx)

        # Variables present in the template but empty in our resolved context
        all_vars = EmailTemplateService.extract_variables(
            (template.subject_template or '') + ' ' + (template.body_text or '')
        )
        unresolved = [v for v in all_vars if not ctx.get(v)]

        return success_response(data={
            'rendered_subject': rendered['subject'],
            'rendered_body_text': rendered['body_text'],
            'rendered_body_html': rendered['body_html'],
            'unresolved_tags': unresolved,
        })


class EmailSendView(APIView):
    permission_classes = [IsAuthenticated, can_send_email]

    def post(self, request):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response(empty_data={'email_message': None})
        serializer = EmailSendSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response('Validation failed', serializer.errors)

        send_request = serializer.to_request(
            tenant_id=request.user.tenant_id,
            actor_user_id=request.user.id,
            trigger_source='manual',
        )

        try:
            if send_request.schedule_at:
                EmailDispatchService.queue_send(send_request)
                return success_response(message='Email scheduled.', status_code=status.HTTP_202_ACCEPTED)
            message = EmailDispatchService.send_now(send_request)
            return success_response(data={'email_message': EmailMessageSerializer(message).data}, status_code=status.HTTP_201_CREATED)
        except Exception as exc:
            return error_response(str(exc), status_code=status.HTTP_400_BAD_REQUEST)


class EmailSendTestView(APIView):
    permission_classes = [IsAuthenticated, can_send_email]

    def post(self, request):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response(empty_data={'email_message': None})
        serializer = EmailSendSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response('Validation failed', serializer.errors)

        send_request = serializer.to_request(
            tenant_id=request.user.tenant_id,
            actor_user_id=request.user.id,
            trigger_source='manual_test',
        )
        send_request.message_purpose = 'platform_notification'
        send_request.allow_fallback = True

        try:
            message = EmailDispatchService.send_now(send_request)
            return success_response(data={'email_message': EmailMessageSerializer(message).data}, status_code=status.HTTP_201_CREATED)
        except Exception as exc:
            return error_response(str(exc), status_code=status.HTTP_400_BAD_REQUEST)


class EmailRenderPreviewView(APIView):
    permission_classes = [IsAuthenticated, can_send_email]

    def post(self, request):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response(empty_data={'preview': {'subject': '', 'body_html': '', 'body_text': ''}})
        template_id = request.data.get('template_id')
        quick_reply_template_id = request.data.get('quick_reply_template_id')
        variables = request.data.get('variables', {})

        payload = {'subject': '', 'body_html': '', 'body_text': ''}

        try:
            if template_id:
                template = get_object_or_404(EmailTemplateDefinition, id=template_id)
                payload = EmailTemplateService.render_template(template, variables)

            if quick_reply_template_id:
                send_request = EmailSendRequest(
                    tenant_id=str(request.user.tenant_id),
                    actor_user_id=str(request.user.id),
                    email_type='business',
                    message_purpose='platform_notification',
                    recipients=['preview@example.com'],
                    quick_reply_template_id=str(quick_reply_template_id),
                    variables=variables,
                )
                _, body_html, body_text = EmailDispatchService._render_content(send_request)
                payload.update({'body_html': body_html, 'body_text': body_text})
        except (ProgrammingError, DatabaseError):
            return email_not_ready_response(empty_data={'preview': {'subject': '', 'body_html': '', 'body_text': ''}})

        return success_response(data={'preview': payload})


class EmailMessageListView(APIView):
    permission_classes = [IsAuthenticated, can_send_email]

    def get(self, request):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response(empty_data={'email_messages': []})
        try:
            qs = EmailMessage.objects.filter(tenant_id=request.user.tenant_id).order_by('-created_at')
        except (ProgrammingError, DatabaseError):
            return email_not_ready_response(empty_data={'email_messages': []})
        related_object_type = request.query_params.get('related_object_type')
        related_object_id = request.query_params.get('related_object_id')
        trigger_source = request.query_params.get('trigger_source')
        if related_object_type:
            qs = qs.filter(related_object_type=related_object_type)
        if related_object_id:
            qs = qs.filter(related_object_id=related_object_id)
        if trigger_source:
            qs = qs.filter(trigger_source=trigger_source)
        return success_response(data={'email_messages': EmailMessageSerializer(qs[:200], many=True).data}, meta={'total': qs.count()})


class EmailMessageDetailView(APIView):
    permission_classes = [IsAuthenticated, can_send_email]

    def get(self, request, pk):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response(empty_data={'email_message': None})
        try:
            message = get_object_or_404(EmailMessage, id=pk, tenant_id=request.user.tenant_id)
        except (ProgrammingError, DatabaseError):
            return email_not_ready_response(empty_data={'email_message': None})
        return success_response(data={'email_message': EmailMessageSerializer(message).data})
