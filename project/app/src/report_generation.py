from django.shortcuts import redirect
from collections import defaultdict
from app.src.utils.report_generation_utils.hourly_range import getRange
from app.src.utils.getCoords import getLatLng
import datetime
import asyncio
from datetime import timezone
from google.cloud.firestore import FieldFilter
from datetime import timedelta
from django.utils.safestring import mark_safe
from app.src.AI_generation_service import genAI
import urllib.parse
from app.src.utils.report_generation_utils.graphics_generation import reportGraphics
from app.core.auth.firebase_config import db
from app.src.business_units_service import getUnitSelected

def process_report(data, uid):
    direccion = ""
    banner = []

    str_startDate = None
    str_endDate_API = None
    str_prev_startDate = None
    str_prev_endDate = None
    eventos_lista = []

    hour_txt = None
    map_config = None
    unit_info = None

    graphic = None
    calendars = None
    data_table = None
    filters = {}
    filtersAi = {}
    direccion = ""
    banner = []
    
    str_startDate = None
    str_endDate_API = None
    
    municipio = data.get('municipio')
    estado = data.get('estado')
    startDate_str = data.get('startDate')
    endDate_str = data.get('endDate')
    delitos_select = data.get('delitos', [])
    business_unit_id = data.get('selectUnit')


    if municipio:
        filters['Municipio_hechos'] = municipio
        filtersAi['Municipio'] = municipio
        direccion += municipio + ', '
        banner.append(municipio)
    if estado:
        filters['Estado_hechos'] = estado
        filtersAi['Estado'] = estado
        direccion += estado + ', '
        banner.append(estado)

    if direccion:
        map_config = getLatLng(direccion)
    lugar = ', '.join(f"{k}" for k in banner)

    unit_info =  getUnitSelected(uid, business_unit_id)
    
    if startDate_str and endDate_str:
        startDate = datetime.datetime.strptime(startDate_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        endDate_inclusive = datetime.datetime.strptime(endDate_str, "%Y-%m-%d").replace(tzinfo=timezone.utc) 
        endDate_DB = endDate_inclusive + timedelta(days=1)
        delta = (endDate_inclusive - startDate).days + 1

        prev_startDate = startDate - timedelta(days=delta)
        prev_endDate = endDate_inclusive - timedelta(days=delta)
        
        str_startDate = startDate.strftime("%Y-%m-%d")
        str_endDate_API = endDate_inclusive.strftime("%Y-%m-%d")
        str_prev_startDate = prev_startDate.strftime("%Y-%m-%d")
        str_prev_endDate = prev_endDate.strftime("%Y-%m-%d")
        filters['startDate']=startDate
        filters['endDate']=endDate_DB
    else:
        pass

    now = datetime.datetime.now(timezone.utc)
    
    if not filters:
        return redirect("main")
        
    ref = db.collection('Eventos')
    query_ref = ref

    if filters:
        for campo, valor in filters.items():
            if campo == "startDate":
                    query_ref = query_ref.where(filter=FieldFilter("FechaHoraHecho", '>=', valor))
            elif campo == "endDate":
                    query_ref = query_ref.where(filter=FieldFilter("FechaHoraHecho", '<=', valor))
            else:
                    if isinstance(valor, str):
                        valor = valor.strip() 
                    query_ref = query_ref.where(filter=FieldFilter(campo, '==', valor))
    if delitos_select:
        if len(delitos_select)<= 10:
            query_ref = query_ref.where(filter=FieldFilter("Categoria", "in", delitos_select))
        else:
            error_message = "Error: Demasiados delitos seleccionados."
            return redirect(f"/main?error={urllib.parse.quote(error_message)}")
        
    query_ref = query_ref.limit(500)

    eventos_por_mes = defaultdict(list)
    graficos_por_mes = defaultdict(list)

    for doc in query_ref.stream():
        evento = doc.to_dict()
        eventos_lista.append(evento)


    if eventos_lista:
        
        try:
            hour_txt = getRange(eventos_lista)
        except:
            hour_txt = "No se encontraron eventos para graficar."

        data_table, graphic, calendars = reportGraphics(eventos_lista, eventos_por_mes, graficos_por_mes)
    else:
       hour_txt = "No se encontraron eventos para graficar."  
    
    AiData = asyncio.run(genAI(
        filtersAi, str_startDate, str_endDate_API, 
        now, delitos_select, eventos_lista, unit_info,
        str_prev_startDate, str_prev_endDate
    ))

    return {
        "graphic": graphic, "calendars": calendars, "tabla_base64": data_table,
        "hour_txt": hour_txt, "AiText": AiData["ai_text"], "AiMarkdown": AiData["ai_markdown"],
        "lugar": lugar, "map_config": map_config, "now_str": now.strftime("%d-%m-%Y"), "eventos_count": len(eventos_lista)
    }