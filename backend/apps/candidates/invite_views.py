from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from apps.candidates.models import CandidateInviteLink, CandidateFormSubmission
from apps.core.responses import success_response, error_response
from django.utils import timezone


class InviteLinkListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        links = CandidateInviteLink.objects.filter(
            tenant_id=request.user.tenant_id,
        ).order_by('-created_at')
        data = [{
            'id': str(l.id),
            'token': l.token,
            'url': f'/apply/{l.token}/',
            'job_id': str(l.job_id) if l.job_id else None,
            'status': l.status,
            'use_count': l.use_count,
            'max_uses': l.max_uses,
            'expires_at': l.expires_at,
            'created_at': l.created_at,
        } for l in links]
        return success_response(data={'links': data}, message="Invite links retrieved.")

    def post(self, request):
        import secrets
        from datetime import timedelta
        
        expires_days = request.data.get('expires_days')
        expires_at = None
        if expires_days:
            expires_at = timezone.now() + timedelta(days=int(expires_days))

        link = CandidateInviteLink.objects.create(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
            token=secrets.token_urlsafe(32),
            job_id=request.data.get('job_id'),
            form_config=request.data.get('form_config', {}),
            expires_at=expires_at,
            max_uses=request.data.get('max_uses'),
        )
        return success_response(
            data={
                'link': {
                    'id': str(link.id),
                    'token': link.token,
                    'url': f'/apply/{link.token}/',
                    'expires_at': link.expires_at,
                }
            },
            message="Invite link created.",
            status_code=201
        )


class InviteLinkDeactivateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            link = CandidateInviteLink.objects.get(
                id=pk, tenant_id=request.user.tenant_id
            )
        except CandidateInviteLink.DoesNotExist:
            return error_response("Link not found.", status_code=404)
        link.status = 'disabled'
        link.save()
        return success_response(message="Link deactivated.")


class PublicApplyFormView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            link = CandidateInviteLink.objects.get(
                token=token, status='active'
            )
        except CandidateInviteLink.DoesNotExist:
            return error_response("Invalid or expired link.", status_code=404)

        if link.expires_at and link.expires_at < timezone.now():
            return error_response("This invite link has expired.", status_code=410)

        if link.max_uses and link.use_count >= link.max_uses:
            return error_response("This invite link has reached its maximum uses.", status_code=410)

        from apps.tenants.models import Client
        try:
            tenant = Client.objects.get(id=link.tenant_id)
            company_name = tenant.name
        except:
            company_name = "A Company"

        job_title = None
        if link.job_id:
            from apps.jobs.models import JobRequisition
            try:
                job = JobRequisition.objects.get(id=link.job_id)
                job_title = job.title
            except:
                pass

        return success_response(data={
            'company_name': company_name,
            'job_title': job_title,
            'form_config': link.form_config,
        }, message="Form config retrieved.")

    def post(self, request, token):
        try:
            link = CandidateInviteLink.objects.get(
                token=token, status='active'
            )
        except CandidateInviteLink.DoesNotExist:
            return error_response("Invalid or expired link.", status_code=404)

        if link.expires_at and link.expires_at < timezone.now():
            return error_response("This invite link has expired.", status_code=410)

        # Create form submission
        submission = CandidateFormSubmission.objects.create(
            invite_link_id=link.id,
            tenant_id=link.tenant_id,
            first_name=request.data.get('first_name', ''),
            last_name=request.data.get('last_name', ''),
            email=request.data.get('email', ''),
            phone=request.data.get('phone', ''),
            cv_filename=request.data.get('cv_filename', ''),
            form_data=request.data,
            ip_address=request.META.get('REMOTE_ADDR', ''),
            wants_account=request.data.get('wants_account', False),
        )

        # Create candidate record
        from apps.candidates.models import Candidate, CandidateProfile
        candidate = Candidate.objects.create(
            tenant_id=link.tenant_id,
            first_name=request.data.get('first_name', ''),
            last_name=request.data.get('last_name', ''),
            email=request.data.get('email', ''),
            phone=request.data.get('phone', ''),
            linkedin_url=request.data.get('linkedin_url', ''),
            current_title=request.data.get('current_title', ''),
            current_company=request.data.get('current_company', ''),
            current_location_city=request.data.get(
                'current_location_city', ''),
            experience_years=request.data.get('experience_years'),
            relevant_experience_years=request.data.get(
                'relevant_experience_years'),
            skills=request.data.get('skills', []),
            nationality=request.data.get('nationality', ''),
            work_authorization=request.data.get(
                'work_authorization', 'not_specified'),
            highest_education=request.data.get(
                'highest_education', ''),
            graduation_year=request.data.get('graduation_year'),
            availability_status=request.data.get(
                'availability_status', ''),
            notice_period_days=request.data.get('notice_period_days'),
            work_mode_preference=request.data.get(
                'work_mode_preference', 'any'),
            resume_url=request.data.get('resume_url', ''),
            source='invite_link',
            initial_entry_type='invite',
            profile_status='partial',
            owner_tenant_id=link.tenant_id,
        )

        CandidateProfile.objects.create(
            tenant_id=link.tenant_id,
            candidate_id=candidate.id,
        )

        submission.candidate_id = candidate.id
        submission.status = 'processed'
        submission.save()

        # Increment use count
        link.use_count += 1
        link.save()

        # Create account if requested
        access_token = None
        if request.data.get('wants_account') and request.data.get('password'):
            from apps.accounts.models import CustomUser
            from apps.tenants.models import Client
            try:
                public_tenant = Client.objects.get(schema_name='public')
                if not CustomUser.objects.filter(email=request.data.get('email')).exists():
                    user = CustomUser.objects.create_user(
                        email=request.data.get('email'),
                        password=request.data.get('password'),
                        first_name=request.data.get('first_name', ''),
                        last_name=request.data.get('last_name', ''),
                        role='candidate',
                        tenant_id=public_tenant.id,
                    )
                    submission.user_id = user.id
                    submission.account_created = True
                    submission.status = 'converted'
                    submission.save()

                    from rest_framework_simplejwt.tokens import RefreshToken
                    refresh = RefreshToken.for_user(user)
                    access_token = str(refresh.access_token)
            except Exception as e:
                pass

        return success_response(
            data={
                'submission_id': str(submission.id),
                'account_created': submission.account_created,
                'access_token': access_token,
            },
            message="Application submitted successfully.",
            status_code=201
        )
