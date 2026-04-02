import datetime
from celery import shared_task
from django.shortcuts import redirect
import urllib.parse
from app.src.utils.resolve_icons import resolveIcons
from app.src.utils.events_geo import resolveManualGeo, resolveBulkGeo
from app.core.auth.firebase_config import db
from app.src.utils.parse_timestamp import parseTimestamp
import pandas as pd
from app.src.utils.parse_excel_datetime import resolveDate, resolveTime, combineDateTime
from app.src.utils.bulk_load_helpers import location_check, normalize_text, sanitize_text, is_valid_float
import io


def loadFilesService(request):
    if request.method == 'POST':
        if 'archivo' in request.FILES:
            excel_file = request.FILES['archivo']
            # Procesar el archivo según sea necesario
            file_bytes = excel_file.read()

            task = bulk_load_task.delay( file_bytes)
            request.session["bulk_task_id"] = task.id
            request.session["loading_bulk"] = True

            return redirect('loadFiles')
        else:
            # Manejo de carga manual
            return handleManualLoad(request)
    return redirect('loadFiles')


def handleManualLoad(request):
    data = {
        "calle": request.POST.get("calle"),
        "colonia": request.POST.get("colonia"),
        "municipio": request.POST.get("municipio"),
        "estado": request.POST.get("estado"),
        "lat": request.POST.get("lat"),
        "lng": request.POST.get("lng"),
        "delito": request.POST.get("delito"),
        "categoria": request.POST.get("categoria", "").upper(),
        "descripcion": request.POST.get("descripcion") or "",
        "fecha": request.POST.get("FechaHoraHecho"),
        "icono": resolveIcons(request.POST.get("icons")),
    }

    has_coords = is_valid_float(data.get('lat')) and is_valid_float(data.get('lng'))

    has_address = all((
        data.get('calle'),
        data.get('colonia'),
        data.get('estado'),
        data.get('municipio'),
    ))

    if has_coords:
        data['lat'] = float(data['lat'])
        data['lng'] = float(data['lng'])

    data["calle"] = sanitize_text(data["calle"])
    data["colonia"] = sanitize_text(data["colonia"])
    data["municipio"] = sanitize_text(data["municipio"])
    data["estado"] = sanitize_text(data["estado"])

    calle = data["calle"] 
    colonia = data["colonia"] 
    municipio = data["municipio"] 
    estado = data["estado"] 

    try:
        if (has_address or has_coords) and all([data.get('fecha'), data.get('delito'), data.get('icono'), data.get('categoria')]):

            data = resolveManualGeo(data)

            data['FechaHoraHecho'] = parseTimestamp(data.get('fecha'))

            partes = [calle, colonia, municipio, estado]
            direccion = " ".join(p for p in partes if p)
            direccion = normalize_text(direccion)

            try:
                db.collection('Eventos').add({
                    "Calle_hechos": data["calle"],
                    "ColoniaHechos": data["colonia"],
                    "Estado_hechos": data["estado"],
                    "Municipio_hechos": data["municipio"],
                    "Delito": data["delito"],
                    "FechaHoraHecho": data['FechaHoraHecho'],
                    "icono": data["icono"],
                    "Categoria": data["categoria"],
                    "latitud": data["lat"],
                    "longitud": data["lng"],
                    'updatedAt': datetime.datetime.now(datetime.timezone.utc),
                    'Descripcion': data["descripcion"],
                    'direccion_full': direccion
                })
                success_message = "Datos agregados exitosamente"
                return redirect(f"/loadFiles?success={urllib.parse.quote(success_message)}")
            except:
                error_message = "Error al subir datos"
                return redirect(f"/loadFiles?error={urllib.parse.quote(error_message)}")
        else:
            error_message = "Faltan datos por agregar"
            return redirect(f"/loadFiles?error={urllib.parse.quote(error_message)}")
    except:
        error_message = "Error al subir datos"
        return redirect(f"/loadFiles?error={urllib.parse.quote(error_message)}")
    

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def bulk_load_task(self, file_bytes):

    file_stream = io.BytesIO(file_bytes)
    try:
        df = pd.read_excel(file_stream, engine='openpyxl', keep_default_na=False)
    except:
        return {"status": "error", "message": "Error al leer el archivo Excel"}

    if "FechaHecho" in df.columns:
        df['FechaHecho'] = pd.to_datetime(
            df['FechaHecho'],
            errors='coerce',
            dayfirst=True
        )

        # Excel numbers
        mask = df['FechaHecho'].isna()
        df.loc[mask, 'FechaHecho'] = pd.to_datetime(
            df.loc[mask, 'FechaHecho'],
            errors='coerce',
            origin='1899-12-30',
            unit='D'
        )
    else:
        df['FechaHecho'] = pd.NaT

    if "HoraHecho" in df.columns:
        df['HoraHecho'] = pd.to_datetime(
            df['HoraHecho'],
            errors='coerce'
        )
    else:
        df['HoraHecho'] = pd.NaT

    # Combine dates
    df['FechaHoraHecho'] = df['FechaHecho'] + (df['HoraHecho'] - df['HoraHecho'].dt.normalize())

    # Clean Nat if is None
    df['FechaHoraHecho'] = df['FechaHoraHecho'].apply(lambda x: x.to_pydatetime() if pd.notnull(x) else None)

    df.drop(columns=["FechaHecho", "HoraHecho"], inplace=True, errors='ignore')
    data = df.where(pd.notnull(df), None).to_dict(orient='records')
    location_data=['latitud', 'longitud', 'Estado_hechos', 'Municipio_hechos', 'ColoniaHechos', 'Calle_hechos' ]

    has_street2 = 'Calle_hechos2' in df.columns
    batch = db.batch()
    count = 0

    for event in data:
        try:
            event['Estado_hechos'] = sanitize_text(event.get('Estado_hechos'))
            event['Municipio_hechos'] = sanitize_text(event.get('Municipio_hechos'))
            event['ColoniaHechos'] = sanitize_text(event.get('ColoniaHechos'))
            event['Calle_hechos'] = sanitize_text(event.get('Calle_hechos'))

            estado = event['Estado_hechos']
            municipio = event['Municipio_hechos'] 
            colonia = event['ColoniaHechos'] 
            calle = event['Calle_hechos']


            if has_street2:
                event['Calle_hechos2'] = sanitize_text(event.get('Calle_hechos2'))
                calle2 = event['Calle_hechos2']
                partes = [calle, calle2, colonia, municipio, estado]
            else:
                partes = [calle, colonia, municipio, estado]

            direccion = " ".join(p for p in partes if p)
            direccion = normalize_text(direccion)

            if not location_check(event, location_data):
                event = resolveBulkGeo(event, has_street2)

            event['icono'] = resolveIcons(event.get('Categoria'))
            event['updatedAt'] = datetime.datetime.now(datetime.timezone.utc)
            event['Categoria'] = event.get('Categoria', '').upper()
            event['direccion_full'] = direccion

            ref = db.collection('Eventos').document()
            batch.set(ref, event)
            count +=1

            if count % 400 == 0:
                batch.commit()
                batch = db.batch()
        except:
            continue
    batch.commit()

    return {"status": "success", "inserted": count}

