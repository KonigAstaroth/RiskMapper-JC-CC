import math
from django.core.cache import cache
from app.core.auth.firebase_config import db
import json
from django.utils import timezone as dj_timezone
from django.utils.safestring import mark_safe

CACHE_KEY_MARKERS = 'firebase_markers'
CACHE_KEY_LAST_UPDATE = 'firebase_markers_last_update'


def markers():
    last_update = cache.get(CACHE_KEY_LAST_UPDATE)
    markers_cached = cache.get(CACHE_KEY_MARKERS)

          
    ref = db.collection('Eventos')
    
    query_has_update = False
    
    
    if last_update:
        changes_query = ref.where('updatedAt', '>', last_update)
        changes = changes_query.limit(1).get()
        query_has_update = len(changes) > 0
    else:
        query_has_update =True
    

    def clean_value(v):
        if isinstance(v, float) and math.isnan(v):
            return None
        return v

    if query_has_update:
        data = ref.limit(2000).get() or []
        list_markers = []
        max_update = last_update

        for doc in data:
            valor = doc.to_dict()
            update_doc = valor.get('updatedAt')
            if update_doc:
                if not max_update or update_doc > max_update:
                        max_update = update_doc

            
            fecha_obj = valor.get('FechaHoraHecho')
            fecha_str = ''
            if fecha_obj:
                fecha_local = dj_timezone.localtime(fecha_obj)
                fecha_str = fecha_local.strftime('%d/%m/%Y, %H:%M:%S')
            marker = {
                'lat': clean_value(valor.get('latitud')),
                'lng': clean_value(valor.get('longitud')),
                'Categoria': clean_value(valor.get('Categoria')),
                'icono': clean_value(valor.get('icono')),
                'delito': clean_value(valor.get('Delito')),
                'fecha': fecha_str,
                'calle': clean_value(valor.get('Calle_hechos')),
                'colonia': clean_value(valor.get('ColoniaHechos')),
                'estado': clean_value(valor.get('Estado_hechos')),
                'municipio': clean_value(valor.get('Municipio_hechos')),
                'descripcion': clean_value(valor.get('Descripcion'))
            }
            list_markers.append(marker)
        cache.set(CACHE_KEY_MARKERS, list_markers, None)
        cache.set(CACHE_KEY_LAST_UPDATE, max_update, None)
    else:
        list_markers = markers_cached or []

    markers_json = mark_safe(json.dumps(list_markers))
    
    return markers_json