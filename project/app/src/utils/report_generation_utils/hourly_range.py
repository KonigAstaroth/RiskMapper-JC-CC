from django.utils import timezone as dj_timezone
from collections import Counter
import datetime

def getRange(eventos):
    horas = []
    eventos_por_hora = []


    for evento in eventos:
        fecha = evento.get('FechaHoraHecho')
        if not fecha:
            continue

        
        fecha_dt = None
        if isinstance(fecha, str):
            try:
                fecha_dt = datetime.fromisoformat(fecha)
            except:
                continue
        elif hasattr(fecha, 'to_datetime'):
            try:
                fecha_dt = fecha.to_datetime()
            except:
                continue
        elif isinstance(fecha, datetime.datetime):
            fecha_dt = fecha
        else:
            continue

        if fecha_dt.tzinfo is not None:
            fecha_local = dj_timezone.localtime(fecha_dt)
        else:
            fecha_local = fecha_dt  

        hora = fecha_local.hour
        horas.append(hora)
    
        eventos_por_hora.append((hora, evento))

    if not horas:
        return None

    ctr = Counter(horas)
    hora_critica, cantidad = ctr.most_common(1)[0]
    eventos_criticos = [
        ev for h, ev in eventos_por_hora if h == hora_critica
    ]

    categorias = []
    delitos = []
    for ev in eventos_criticos:
        categoria = ev.get('Categoria').title()
        delito = ev.get('Delito')
        categorias.append(categoria)
        delitos.append(delito)

    categoria_critica = None
    if categorias:
        ctr_categorias = Counter(categorias)
        categoria_critica, _ = ctr_categorias.most_common(1)[0]
    print(f"Delitos con la misma categoria en la misma hora critica: {delitos}")

    if hora_critica is not None:
        if cantidad > 1:
            hour_txt = f"Entre las {hora_critica}:00 y las {hora_critica+1}:00 horas se registró {cantidad} eventos. La categoría más frecuente en este intervalo fue {categoria_critica}, por lo que este rango horario representa un posible punto crítico principalmente asociado a este tipo de evento."
        elif cantidad == 1:
            hour_txt = f"Entre las {hora_critica}:00 y las {hora_critica+1}:00 horas se registró {cantidad} evento, lo que destaca este intervalo como un posible punto de riesgo. La categoría corresponde a {categoria_critica}, lo que indica un posible riesgo aislado en este intervalo."
    else:
        hour_txt = "No hay eventos para calcular el rango horario crítico."
    return hour_txt
    