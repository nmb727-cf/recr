from apps.core import events
from apps.jobs.workflow_service import JobWorkflowService

def on_job_created(sender, requisition, **kwargs):
    """
    Trigger Workflow Master on job creation.
    Also handles Auto-Publish from Step 8.
    """
    # 1. Trigger Workflow
    JobWorkflowService.trigger_job_workflow(
        requisition=requisition,
        event_type='job.created'
    )

    # 2. Check for Auto-Publish
    metadata = requisition.metadata or {}
    if metadata.get('auto_publish_enabled') and requisition.status == 'draft':
        requisition.status = 'published'
        requisition.save(update_fields=['status'])
        events.job.published.send(sender=None, requisition=requisition)

def on_job_approved(sender, requisition, **kwargs):
    """
    Trigger Workflow Master when job is approved.
    Also handles Auto-Publish if approval was required.
    """
    JobWorkflowService.trigger_job_workflow(
        requisition=requisition,
        event_type='job.approved'
    )

    # Check for Auto-Publish after approval
    metadata = requisition.metadata or {}
    if metadata.get('auto_publish_enabled') and requisition.status == 'pending_approval':
        requisition.status = 'published'
        requisition.save(update_fields=['status'])
        events.job.published.send(sender=None, requisition=requisition)

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
