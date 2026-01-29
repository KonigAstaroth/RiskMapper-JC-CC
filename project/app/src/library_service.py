import datetime
from app.core.auth.firebase_config import db
from app.views import library
from django.utils import timezone as dj_timezone
from django.core.cache import cache


CACHE_KEY_MARKERS = 'firebase_markers'
CACHE_KEY_LAST_UPDATE = 'firebase_markers_last_update'

def edit_event(request, id):

    updates = {}
    if request.method == 'POST':
        # Collect fields to update  
        if calle := request.POST.get('calle'):
            updates['Calle_hechos'] = calle
        if colonia := request.POST.get('colonia'):
            updates['ColoniaHechos'] = colonia
        if municipio:= request.POST.get('municipio'):
            updates['Municipio_hechos'] = municipio
        if estado := request.POST.get('estado'):
            updates['Estado_hechos'] = estado

        # Map icono values and update
        icono = request.POST.get('icono')
        if icono:
            ICON_MAP = {
                'amenazas': 'amenazas',
                'robo a negocio': 'robonegocio',
                'homicidio doloso': 'homicidiodoloso',
                'feminicidio': 'feminicidio',
                'secuestro': 'secuestro',
                'trata de personas': 'tratapersonas',
                'robo a transeúnte': 'robotranseunte',
                'extorsión': 'extorsion',
                'robo a casa habitación': 'robocasa',
                'violación': 'violacion',
                'narcomenudeo': 'narcomenudeo',
                'categoria de bajo impacto': 'bajoimpacto',
                'delito de bajo impacto': 'bajoimpacto',
                'arma de fuego': 'armafuego',
                'robo de accesorios de auto': 'robovehiculo',
                'robo de vehículo': 'robovehiculo',
                'robo a cuentahabiente saliendo del cajero con violencia': 'robocuentahabiente',
                'robo a pasajero a bordo de microbus': 'robomicrobus',
                'robo a repartidor': 'roborepartidor',
                'robo a pasajero a bordo del metro': 'robometro',
                'lesiones dolosas por disparo de arma de fuego': 'armafuego',
                'hecho no delictivo': 'nodelito',
                'robo a pasajero a bordo de taxi con violencia': 'robotaxi',
                'robo a transportista': 'robotransportista',
                'default': 'default',
            }

            icon = ICON_MAP.get(icono, 'default')
            updates['icono'] = icon

        if FechaHoraHecho := request.POST.get('FechaHoraHecho'):
            if 'T' in FechaHoraHecho:
                FechaHora= datetime.datetime.fromisoformat(FechaHoraHecho) 
            else:
                FechaHora = datetime.datetime.strptime(FechaHoraHecho, "%Y-%m-%d %H:%M:%S")

            if dj_timezone.is_naive(FechaHora):
                timestamp = dj_timezone.make_aware(FechaHora)
            else:
                timestamp = FechaHora
            updates['FechaHoraHecho'] = timestamp
        if categoria := request.POST.get('categoria'):
            updates['Categoria'] = categoria
        if delito := request.POST.get('delito'):
            updates['Delito'] = delito
        if descripcion := request.POST.get('descripcion'):
            updates['Descripcion'] = descripcion
        
        # Update the document in Firestore
        if updates:
            try:
                updateNow = datetime.datetime.now(datetime.timezone.utc)
                updates['updatedAt'] = updateNow
                db.collection('Eventos').document(id).update(updates)
            except Exception as e:
                print(e)


    return library(request)

def deleteEvent(request, id):
      
     if request.method == 'POST':
          doc_ref = db.collection('Eventos').document(id)
          doc = doc_ref.get()
          try:
               if doc.exists:
                    doc_ref.delete()
                    cache.delete(CACHE_KEY_LAST_UPDATE)
                    cache.delete(CACHE_KEY_MARKERS)
          except Exception as e:
               print(e)
     
     return library(request)

