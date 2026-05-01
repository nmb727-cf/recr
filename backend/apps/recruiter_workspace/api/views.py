from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.core.responses import success_response, error_response
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, Count
from apps.interviews.models import Interview, InterviewPanelist
from apps.pipeline.models import Application
from apps.jobs.models import JobRequisition
from apps.automation_tasks.models import WorkflowTaskExecution
from apps.candidates.crm_models import CandidatePipelineStatus

class WorkspaceSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.user.tenant_id
        user_id = request.user.id
        today = timezone.now().date()

        # Interviews Today
        interviews_today = Interview.objects.filter(
            tenant_id=tenant_id,
            scheduled_at__date=today,
            status='scheduled'
        ).count()

        # Tasks Pending
        tasks_pending = WorkflowTaskExecution.objects.filter(
            tenant_id=tenant_id,
            assignee_user_id=user_id,
            status='pending'
        ).count()

        # Active Candidates (In Nurture/CRM)
        active_candidates = CandidatePipelineStatus.objects.filter(
            tenant_id=tenant_id,
            assigned_to=user_id
        ).exclude(status__in=['archive', 'not_interested']).count()

        # Jobs Assigned (Recruiter is owner)
        jobs_assigned = JobRequisition.objects.filter(
            tenant_id=tenant_id,
            recruiter_id=user_id,
            status='active'
        ).count()

        data = {
            'interviews_today': interviews_today,
            'tasks_pending': tasks_pending,
            'active_candidates': active_candidates,
            'jobs_assigned': jobs_assigned,
            'productivity_score': 85, 
        }

        return success_response(data=data)

class WorkspaceTasksView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.user.tenant_id
        user_id = request.user.id
        today = timezone.now().date()
        
        tasks = []

        # 1. Manual/Workflow Tasks
        workflow_tasks = WorkflowTaskExecution.objects.filter(
            tenant_id=tenant_id,
            assignee_user_id=user_id,
            status='pending'
        )
        
        for t in workflow_tasks:
            tasks.append({
                'id': str(t.id),
                'type': 'workflow',
                'title': t.task_title,
                'description': t.task_description,
                'priority': t.priority,
                'due_at': t.due_at.isoformat() if t.due_at else None,
                'created_at': t.created_at.isoformat()
            })

        # 2. CRM Followups
        crm_followups = CandidatePipelineStatus.objects.filter(
            tenant_id=tenant_id,
            assigned_to=user_id,
            next_action_date__lte=today
        ).exclude(status__in=['archive', 'not_interested'])

        for f in crm_followups:
            tasks.append({
                'id': f'crm-{f.id}',
                'type': 'crm_followup',
                'title': f'Follow up with candidate',
                'description': f.next_action,
                'priority': 'high' if f.next_action_date < today else 'medium',
                'due_at': f.next_action_date.isoformat() if f.next_action_date else None,
                'candidate_id': str(f.candidate_id)
            })

        # 3. Pending Interview Feedback
        # Fix: InterviewPanelist doesn't have FK to Interview, use ID matching
        # First find panel records for this user that aren't submitted
        my_panels = InterviewPanelist.objects.filter(
            tenant_id=tenant_id,
            interviewer_id=user_id,
            submitted_at__isnull=True
        )
        
        # Get corresponding interview IDs
        interview_ids = [p.interview_id for p in my_panels]
        
        # Find finished interviews among those
        finished_interviews = Interview.objects.filter(
            id__in=interview_ids,
            scheduled_at__lt=timezone.now()
        )
        
        finished_ids = set(finished_interviews.values_list('id', flat=True))

        for p in my_panels:
            if p.interview_id in finished_ids:
                tasks.append({
                    'id': f'feedback-{p.id}',
                    'type': 'feedback',
                    'title': 'Submit Interview Feedback',
                    'description': f'Feedback needed for completed interview',
                    'priority': 'urgent',
                    'due_at': p.deadline_at.isoformat() if p.deadline_at else None,
                    'interview_id': str(p.interview_id)
                })

        return success_response(data={'tasks': tasks})

class WorkspaceActivityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        activities = [
            {'id': 1, 'event': 'Candidate Moved', 'summary': 'James Bond moved to Technical Interview', 'time': '2h ago', 'type': 'pipeline'},
            {'id': 2, 'event': 'Interview Completed', 'summary': 'Sarah Conner completed Recruiter Screen', 'time': '4h ago', 'type': 'interview'},
            {'id': 3, 'event': 'New Application', 'summary': 'Tony Stark applied for Lead Instructor', 'time': '1d ago', 'type': 'application'},
        ]
        return success_response(data={'activities': activities})

class WorkspaceAlertsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.user.tenant_id
        
        alerts = []
        
        # Stuck Candidates (> 48h in same stage)
        stuck_cutoff = timezone.now() - timedelta(hours=48)
        stuck_candidates_count = Application.objects.filter(
            tenant_id=tenant_id,
            updated_at__lt=stuck_cutoff
        ).exclude(status__in=['rejected', 'hired', 'withdrawn']).count()
        
        if stuck_candidates_count > 0:
            alerts.append({
                'type': 'pipeline_stuck',
                'title': f'{stuck_candidates_count} Stuck Candidates',
                'severity': 'high',
                'description': 'Candidates haven\'t moved in 48 hours'
            })

        # Overdue Tasks
        overdue_tasks = WorkflowTaskExecution.objects.filter(
            tenant_id=tenant_id,
            status='pending',
            due_at__lt=timezone.now()
        ).count()
        
        if overdue_tasks > 0:
            alerts.append({
                'type': 'tasks_overdue',
                'title': f'{overdue_tasks} Overdue Tasks',
                'severity': 'urgent',
                'description': 'Actions required immediately'
            })

        return success_response(data={'alerts': alerts})

class WorkspaceAIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        suggestions = [
            {'id': 1, 'text': 'Suggest outreach to 3 React developers for "Senior Web Round"', 'type': 'outreach'},
            {'id': 2, 'text': 'Candidate Diana Prince is a 94% match for Senior Platform Engineer', 'type': 'match'},
            {'id': 3, 'text': 'Schedule follow-up with Luke Skywalker - he responded to your email', 'type': 'followup'},
        ]
        return success_response(data={'suggestions': suggestions})
