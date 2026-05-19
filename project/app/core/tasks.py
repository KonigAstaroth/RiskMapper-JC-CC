from celery import shared_task
from app.src.report_generation import process_report
from app.core.auth.firebase_config import db

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def generate_report_task(self,data,uid):
    result = process_report(data,uid)

    report_id = self.request.id

    db.collection("Reportes").document(report_id).set(result)

    return report_id