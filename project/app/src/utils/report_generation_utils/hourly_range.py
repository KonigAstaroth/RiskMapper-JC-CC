from django.utils import timezone as dj_timezone
from collections import Counter
import datetime

def getRange(eventos):
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
     return hora_critica, cantidad