from celery import shared_task

from apps.pipeline.guarantee import expire_due_placement_guarantees


@shared_task
def expire_placement_guarantees_task():
    count = expire_due_placement_guarantees()
    return f"Expired {count} placement guarantees"
