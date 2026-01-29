import datetime
from app.core.auth.firebase_config import db
from app.views import library
from django.utils import timezone as dj_timezone
from django.core.cache import cache
from datetime import timedelta,timezone
from google.cloud.firestore import FieldFilter


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

def searchEvent(request):
    eventos = []
    ref = db.collection('Eventos')
    filters = {}
    
    if request.method == 'POST':
        

        startDate_str = request.POST.get('startDate')
        endDate_str = request.POST.get('endDate')
        direccion = request.POST.get('direccion', '')
        search = request.POST.get('searchBy')
        categoria = request.POST.get('categoria')

        partes_direccion = [parte.strip() for parte in direccion.split(',') if parte.strip()]

        if search == "full":
            calle = partes_direccion[0] if len(partes_direccion) > 0 else None
            colonia = partes_direccion[1] if len(partes_direccion) > 1 else None
            municipio = partes_direccion[2] if len(partes_direccion) > 2 else None
            estado = partes_direccion[3] if len(partes_direccion) > 3 else None

            if calle:
                filters['Calle_hechos'] = calle
            if colonia:
                filters['ColoniaHechos'] = colonia
            if municipio:
                filters['Municipio_hechos'] = municipio
            if estado:
                filters['Estado_hechos'] = estado
        elif search == "estado":
            estado = partes_direccion[0] if len(partes_direccion) > 0 else None
            if estado:
                filters['Estado_hechos'] = estado
        elif search == "municipio":
            municipio = partes_direccion[0] if len(partes_direccion) > 0 else None
            if municipio:
                filters['Municipio_hechos'] = municipio
        elif search == "estadoMunicipio":
            municipio = partes_direccion[0] if len(partes_direccion) > 0 else None
            estado = partes_direccion[1] if len(partes_direccion) > 1 else None
            if municipio:
                filters['Municipio_hechos'] = municipio.strip()
            if estado:
                filters['Estado_hechos'] = estado.strip()

        
        if startDate_str and endDate_str:
            filters['startDate'] = startDate_str
            filters['endDate'] = endDate_str

        if categoria:
            filters['Categoria'] = categoria

        
    if filters:
          query_ref = ref

          startDate_str = filters.get('startDate')
          endDate_str = filters.get('endDate')

          
          if startDate_str and endDate_str:
               startDate = datetime.datetime.strptime(startDate_str, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
               endDate = datetime.datetime.strptime(endDate_str, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)
               query_ref = query_ref.where(filter=FieldFilter("FechaHoraHecho", '>=', startDate))
               query_ref = query_ref.where(filter=FieldFilter("FechaHoraHecho", '<=', endDate))

          
          filters_sin_fechas = {k: v for k, v in filters.items() if k not in ['startDate', 'endDate']}

          
          for campo, valor in filters_sin_fechas.items():
               print(f"Campo: {campo}, Valor: {valor}")
               if isinstance(valor, str):
                    valor = valor.strip()
               query_ref = query_ref.where(filter=FieldFilter(campo, '==', valor))

          resultados = query_ref.stream()
          for doc in resultados:
               data = doc.to_dict()
               data['id'] = doc.id
               eventos.append(data)
    return eventos