import datetime
from django.utils import timezone as dj_timezone

def parseTimestamp(fecha_value):
    try:
        dt = datetime.datetime.fromisoformat(fecha_value)

        # convertir a aware
        if dj_timezone.is_naive(dt):
            dt = dj_timezone.make_aware(
                dt,
                dj_timezone.get_current_timezone()
            )

        return dt
            
    except:
        raise ValueError(f"Fecha inválida: {fecha_value}")