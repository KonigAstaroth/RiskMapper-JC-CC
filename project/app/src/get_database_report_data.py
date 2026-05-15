from app.core.auth.firebase_config import db

def getDataDBMain(task_id, request):
    lugar = None
    if not task_id:
        return lugar

    report_ref = db.collection("Reportes").document(task_id).get()

    if not report_ref.exists:
        return lugar
    
    data = report_ref.to_dict()

    request.session['map_config'] = data.get("map_config")

    lugar = data.get('lugar')

    return lugar


def getDataDBWord(task_id):
    AiMarkdown = graphic = calendarios = horas = now_str =  place_str = tabla_img = None
    if not task_id:
        return AiMarkdown, graphic, calendarios, horas, now_str,  place_str, tabla_img
    
    report_ref = db.collection("Reportes").document(task_id).get()

    if not report_ref:
        return AiMarkdown, graphic, calendarios, horas, now_str,  place_str, tabla_img
    
    data = report_ref.to_dict()

    graphic = data.get('graphic', [])
    calendarios = data.get('calendars', [])
    horas = data.get('hour_txt')
    AiMarkdown = data.get('AiMarkdown')
    place_str= data.get('lugar')
    tabla_img = data.get('tabla_base64')
    now_str = data.get('now_str')


    return AiMarkdown, graphic, calendarios, horas, now_str,  place_str, tabla_img