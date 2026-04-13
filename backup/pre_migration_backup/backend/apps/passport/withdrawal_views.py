from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.passport.models import TalentPassport, DataWithdrawalRequest
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

        withdrawal = DataWithdrawalRequest.objects.create(
            candidate_id=passport.candidate_id or request.user.id,
            user_id=request.user.id,
            reason=request.data.get('reason', ''),
            deletion_scheduled_at=timezone.now() + timedelta(days=30),
        )

        # Immediately anonymize PII
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

        # Anonymize user account
        request.user.first_name = 'Withdrawn'
        request.user.last_name = 'User'
        request.user.phone = ''
        request.user.save()

        withdrawal.status = 'anonymized'
        withdrawal.anonymized_at = timezone.now()
        withdrawal.save()

        return success_response(
            data={
                'withdrawal_id': str(withdrawal.id),
                'deletion_scheduled_at': withdrawal.deletion_scheduled_at,
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
