from apps.core import events
from apps.jobs.workflow_service import JobWorkflowService

def on_job_created(sender, requisition, **kwargs):
    """
    Trigger Workflow Master on job creation.
    """
    JobWorkflowService.trigger_job_workflow(
        requisition=requisition,
        event_type='job.created'
    )

def on_job_approved(sender, requisition, **kwargs):
    """
    Trigger Workflow Master when job is approved.
    """
    JobWorkflowService.trigger_job_workflow(
        requisition=requisition,
        event_type='job.approved'
    )

def on_job_published(sender, requisition, **kwargs):
    """
    Trigger Workflow Master when job is published.
    """
    JobWorkflowService.trigger_job_workflow(
        requisition=requisition,
        event_type='job.published'
    )

# Connect signals
events.job.created.connect(on_job_created, dispatch_uid='workflow_job_created')
events.job.approved.connect(on_job_approved, dispatch_uid='workflow_job_approved')
events.job.published.connect(on_job_published, dispatch_uid='workflow_job_published')
