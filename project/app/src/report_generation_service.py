from django.shortcuts import redirect
from app.core.tasks import generate_report_task

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

