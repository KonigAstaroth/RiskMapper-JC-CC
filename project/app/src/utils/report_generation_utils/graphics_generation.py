from app.src.graph_generation_service import genDataImg, genGraph, generateCalendar
import urllib.parse
from django.shortcuts import redirect
from collections import defaultdict
import datetime
from app.src.utils.report_generation_utils.parse_timestamp_num import time_to_num
from app.src.utils.report_generation_utils.lists import color_delitos
from django.utils import timezone as dj_timezone
import numpy as np



def reportGraphics(eventos_lista, eventos_por_mes, graficos_por_mes):
    calendars = []
    graphic = []
    cat_color = []
    conteo_delitos = defaultdict(int)
    cat_color_cuenta = []
    data_table = None

    for  eventos in eventos_lista:
        date_obj = eventos.get('FechaHoraHecho')
        if not date_obj:
            continue
        fecha = date_obj
        categorie = eventos.get('Categoria')


        match = next((item for item in color_delitos if item['valor'] == categorie), None)
        if match:
            nombre = match['nombre']
            color = match['color']
        else:
            nombre = 'Otro'
            color = 'gray'

        conteo_delitos[nombre] += 1

        if not any(c['nombre'] == nombre for c in cat_color):
            cat_color.append({'nombre': nombre, 'color': color})

        if fecha:
            if isinstance(fecha,str):
                    fecha = datetime.fromisoformat(fecha)
            elif hasattr(fecha, 'to_datetime'):
                    fecha = fecha.to_datetime()

            year = fecha.year
            month = fecha.month
            day = fecha.day


        eventos_por_mes[(year, month)].append((day, categorie))


        if date_obj:
            hora_local = dj_timezone.localtime(date_obj)
            hora_str = hora_local.strftime('%H:%M:%S').strip()
            hora_str = ''.join(c for c in hora_str if c.isdigit() or c == ':')
            segundos = time_to_num(hora_str)
            if segundos is not None:
                    angulo = (segundos/86400) * 2 * np.pi
                    dia = hora_local.day
                    graficos_por_mes[(year, month)].append((angulo, dia, categorie))

    for (year, month), day in eventos_por_mes.items():
        if not day:
                continue
        else:
            imagen_base64  = generateCalendar(year, month, day)
            if imagen_base64:
                calendars.append({
                    'img': imagen_base64 
                })
            else:
                error_message = "No se pudo el calendario"
                return redirect(f"/main?error={urllib.parse.quote(error_message)}")
        puntos_mes = graficos_por_mes.get((year,month), [])
        if not puntos_mes:
                continue
        else:
                if puntos_mes:
                    graphic_img = genGraph(puntos_mes)
                    graphic.append({
                        'img': graphic_img
                    })
                else:
                    error_message = "No se pudo la grafica"
                    return redirect(f"/main?error={urllib.parse.quote(error_message)}")  
                
    for item in cat_color:
        nombre = item['nombre']
        color = item['color']
        cuenta = conteo_delitos.get(nombre, 0)
        cat_color_cuenta.append({'nombre': nombre, 'color': color, 'cuenta': cuenta})
    data_table = genDataImg(cat_color_cuenta)
                
    return data_table, graphic, calendars