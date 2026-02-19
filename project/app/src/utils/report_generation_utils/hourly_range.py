from django.utils import timezone as dj_timezone
from collections import Counter
import datetime

def getRange(eventos, request):
    horas = []

    for evento in eventos:
        fecha = evento.get('FechaHoraHecho')
        if not fecha:
            print("Evento sin fecha:", evento)
            continue

        
        fecha_dt = None
        if isinstance(fecha, str):
            try:
                fecha_dt = datetime.fromisoformat(fecha)
            except Exception as e:
                print("Error al convertir string a datetime:", e)
                continue
        elif hasattr(fecha, 'to_datetime'):
            try:
                fecha_dt = fecha.to_datetime()
            except Exception as e:
                print("Error al usar to_datetime():", e)
                continue
        elif isinstance(fecha, datetime.datetime):
            fecha_dt = fecha
        else:
            continue

        if fecha_dt.tzinfo is not None:
            fecha_local = dj_timezone.localtime(fecha_dt)
        else:
            fecha_local = fecha_dt  

        horas.append(fecha_local.hour)
     

    if not horas:
        return None, None

    ctr = Counter(horas)
    hora_critica, cantidad = ctr.most_common(1)[0]
    lang = request.session.get('lang')

    if hora_critica is not None:
        if cantidad > 1:
            if lang == 'en':
                    hour_txt = f"Between {hora_critica}:00 and {hora_critica+1}:00 it was registered {cantidad} events, which highlights this interval as a possible risk point."
            elif lang == 'es':
                    hour_txt = f"Entre las {hora_critica}:00 y las {hora_critica+1}:00 horas se registró {cantidad} eventos, lo que destaca este intervalo como un posible punto de riesgo."
        elif cantidad == 1:
            if lang == 'en':
                    hour_txt = f"Between {hora_critica}:00 and {hora_critica+1}:00 it was registered {cantidad} event, which highlights this interval as a possible risk point."
            elif lang == 'es':
                    hour_txt = f"Entre las {hora_critica}:00 y las {hora_critica+1}:00 horas se registró {cantidad} evento, lo que destaca este intervalo como un posible punto de riesgo."
    else:
        hour_txt = "No hay eventos para calcular rango horario crítico."
    return hour_txt
    