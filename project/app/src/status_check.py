from django.http import JsonResponse
from celery.result import AsyncResult
from app.core.auth.firebase_config import db


def check_report_status(request):

    task_id = request.session.get("task_id")

    if not task_id:
        return JsonResponse({"status": "no_task"})

    task = AsyncResult(task_id)

    if task.state == "SUCCESS":
        request.session['generating_report'] = False

        report_id = task.result

        report_ref = db.collection("Reportes").document(report_id).get()

        if report_ref.exists:

            return JsonResponse({"status": "finished"})

    return JsonResponse({"status": "processing"})


def check_bulk_status(request):

    task_id = request.session.get("bulk_task_id")

    if not task_id:
        return JsonResponse({"status": "no_task"})

    task = AsyncResult(task_id)

    if task.state == "SUCCESS":

        request.session["loading_bulk"] = False

        result = task.result

        return JsonResponse({
            "status": "finished",
            "inserted": result.get("inserted", 0)
        })

    return JsonResponse({"status": "processing"})