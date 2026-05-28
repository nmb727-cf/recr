from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

from apps.passport.models import TalentPassport, DataWithdrawalRequest, PassportAccessLog
from apps.candidates.models import Candidate
from apps.passport.notification_service import dispatch_withdrawal_notifications
from apps.core.responses import success_response, error_response
from django.utils import timezone
from datetime import timedelta


class DataWithdrawalView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            passport = TalentPassport.objects.get(
                user_id=request.user.id,
                is_deleted=False
            )
        except TalentPassport.DoesNotExist:
            return error_response("Passport not found.", status_code=404)

        if DataWithdrawalRequest.objects.filter(
            user_id=request.user.id,
            status__in=['pending', 'anonymized']
        ).exists():
            return error_response("A withdrawal request is already in progress.")

        now = timezone.now()
        deletion_at = now + timedelta(days=30)
        with transaction.atomic():
            withdrawal = DataWithdrawalRequest.objects.create(
                candidate_id=passport.candidate_id or request.user.id,
                user_id=request.user.id,
                reason=request.data.get('reason', ''),
                deletion_scheduled_at=deletion_at,
            )

            # Collect affected tenant IDs to support downstream notification jobs.
            notified_tenants = set(
                str(tid)
                for tid in PassportAccessLog.objects.filter(
                    passport_id=passport.id,
                    accessed_by_tenant_id__isnull=False,
                ).values_list('accessed_by_tenant_id', flat=True).distinct()
                if tid
            )

            candidate = Candidate.objects.filter(
                passport_id=passport.id,
                user_id=request.user.id,
                is_deleted=False,
            ).first()
            if candidate and candidate.tenant_id:
                notified_tenants.add(str(candidate.tenant_id))

            # Immediately anonymize passport PII
            passport.headline = ''
            passport.summary = ''
            passport.current_title = ''
            passport.current_company = ''
            passport.current_cv_url = ''
            passport.current_cv_filename = ''
            passport.linkedin_url = ''
            passport.github_url = ''
            passport.portfolio_url = ''
            passport.work_history = []
            passport.education = []
            passport.is_active = False
            passport.save()

            # Anonymize linked candidate identity only when this account owns it.
            if candidate:
                candidate.first_name = "Withdrawn"
                candidate.last_name = "Candidate"
                candidate.email = ""
                candidate.phone = ""
                candidate.phone_number = ""
                candidate.resume_url = ""
                candidate.linkedin_url = ""
                candidate.passport_linked = False
                candidate.passport_id = None
                candidate.user_id = None
                candidate.metadata = {
                    **(candidate.metadata or {}),
                    "withdrawn_at": now.isoformat(),
                    "withdrawal_request_id": str(withdrawal.id),
                }
                candidate.save(update_fields=[
                    'first_name', 'last_name', 'email', 'phone', 'phone_number',
                    'resume_url', 'linkedin_url',
                    'passport_linked', 'passport_id', 'user_id', 'metadata',
                    'updated_at',
                ])

            # Anonymize user account
            request.user.first_name = 'Withdrawn'
            request.user.last_name = 'User'
            request.user.phone = ''
            request.user.save(update_fields=['first_name', 'last_name', 'phone', 'updated_at'])

            withdrawal.status = 'anonymized'
            withdrawal.anonymized_at = now
            withdrawal.notified_tenants = sorted(notified_tenants)
            withdrawal.metadata = {
                **(withdrawal.metadata or {}),
                "tenant_notifications_pending": bool(notified_tenants),
            }
            withdrawal.save(update_fields=['status', 'anonymized_at', 'notified_tenants', 'metadata'])
            dispatch_result = dispatch_withdrawal_notifications(
                withdrawal=withdrawal,
                actor_user_id=request.user.id,
            )

        return success_response(
            data={
                'withdrawal_id': str(withdrawal.id),
                'deletion_scheduled_at': withdrawal.deletion_scheduled_at,
                'tenant_notifications': dispatch_result,
            },
            message="Data withdrawal initiated. Your data has been anonymized and will be permanently deleted in 30 days."
        )

    def get(self, request):
        try:
            withdrawal = DataWithdrawalRequest.objects.filter(
                user_id=request.user.id
            ).latest('requested_at')
            return success_response(
                data={
                    'status': withdrawal.status,
                    'requested_at': withdrawal.requested_at,
                    'deletion_scheduled_at': withdrawal.deletion_scheduled_at,
                },
                message="Withdrawal status retrieved."
            )
        except DataWithdrawalRequest.DoesNotExist:
            return error_response("No withdrawal request found.", status_code=404)
