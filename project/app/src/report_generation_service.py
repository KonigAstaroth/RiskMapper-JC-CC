from django.http import JsonResponse
from django.shortcuts import redirect
from app.core.tasks import generate_report_task
from celery.result import AsyncResult
from app.core.auth.firebase_config import db


def generateReport(request):
    uid = request.session.get("uid")
    if request.method == "POST":

        data = {
            "municipio": request.POST.get('municipio'),
            "estado": request.POST.get('estado'),
            "startDate": request.POST.get('startDate'),
            "endDate": request.POST.get('endDate'),
            "delitos": request.POST.getlist('delitos'),
            "unit": request.POST.get('selectUnit')
        }

        task = generate_report_task.delay(data, uid)
        request.session['generating_report'] = True
        request.session["task_id"] = task.id

        return redirect('main')


def check_report_status(request):

    task_id = request.session.get("task_id")

    if not task_id:
        return JsonResponse({"status": "no_task"})

    task = AsyncResult(task_id)

    if task.state == "SUCCESS":
        request.session.get('generating_report') = False

        report_id = task.result

        report_ref = db.collection("Reportes").document(report_id).get()

        if report_ref.exists:

            data = report_ref.to_dict()

            request.session['graphic'] = data.get("graphic")
            request.session['calendarios'] = data.get("calendars", [])
            request.session['hour_txt'] = data.get("hour_txt")
            request.session['AiText'] = data.get("AiText")
            request.session['lugar'] = data.get("lugar")
            request.session['tabla_base64'] = data.get("tabla_base64")


            return JsonResponse({"status": "finished"})

    return JsonResponse({"status": "processing"})