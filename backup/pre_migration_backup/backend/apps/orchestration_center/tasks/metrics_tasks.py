from celery import shared_task


@shared_task(bind=True)
def recompute_intelligence_metrics(self):
    return {'status': 'metrics_recompute_requested'}

