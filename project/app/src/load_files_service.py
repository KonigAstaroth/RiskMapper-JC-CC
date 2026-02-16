import datetime
from django.shortcuts import redirect
import urllib.parse
from app.src.utils.resolve_icons import resolveIcons
from app.src.utils.events_geo import resolveManualGeo, resolveBulkGeo
from app.core.auth.firebase_config import db
from app.src.utils.parse_timestamp import parseTimestamp
import pandas as pd
from app.src.utils.parse_excel_datetime import resolveDate, resolveTime, combineDateTime
from app.src.utils.bulk_load_helpers import location_check, check_valid_value


def loadFilesService(request):
    if request.method == 'POST':
        if 'archivo' in request.FILES:
            excel_file = request.FILES['archivo']
            # Procesar el archivo según sea necesario
            return bulkLoad(request, excel_file)
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
        "delito": request.POST.get("crime"),
        "categoria": request.POST.get("categ", "").upper(),
        "descripcion": request.POST.get("descripcion") or "",
        "fecha": request.POST.get("FechaHoraHecho"),
        "icono": resolveIcons(request.POST.get("icons")),
    }

    has_address = all((
        data.get('calle'),
        data.get('colonia'),
        data.get('estado'),
        data.get('municipio'),
    ))

    has_coords = all((
        data.get('lat'),
        data.get('lng'),
    ))

    if (has_address or has_coords) and all([data.get('fecha'), data.get('delito'), data.get('icono'), data.get('categoria')]):

        data = resolveManualGeo(data)

        data['FechaHoraHecho'] = parseTimestamp(data.pop('fecha'))

        try:
            db.collection('Eventos').add({
                "Calle_hechos": data["calle"],
                "ColoniaHechos": data["colonia"],
                "Estado_hechos": data["estado"],
                "Delito": data["delito"],
                "FechaHoraHecho": data["fecha"],
                "icono": data["icono"],
                "Municipio_hechos": data["municipio"],
                "Categoria": data["categoria"],
                "latitud": data["lat"],
                "longitud": data["lng"],
                'updatedAt': datetime.datetime.now(datetime.timezone.utc),
                'Descripcion': data["descripcion"],
            })
            success_message = "Datos agregados exitosamente"
            return redirect(f"/loadFiles?success={urllib.parse.quote(success_message)}")
        except:
            error_message = "Error al subir datos"
            return redirect(f"/loadFiles?error={urllib.parse.quote(error_message)}")
    else:
        error_message = "Faltan datos por agregar"
        return redirect(f"/loadFiles?error={urllib.parse.quote(error_message)}")


def bulkLoad(request, excel_file):
    try:
        df = pd.read_excel(excel_file, engine='openpyxl', keep_default_na=False)
    except:
        error_message = "Error al leer el archivo Excel"
        return redirect(f"/loadFiles?error={urllib.parse.quote(error_message)}")

    if "FechaHecho" in df.columns:
        df['FechaHecho'] = df['FechaHecho'].apply(resolveDate)
    if "HoraHecho" in df.columns:
        df["HoraHecho"] = df["HoraHecho"].apply(resolveTime)

    df["FechaHoraHecho"] = df.apply(
        lambda row: combineDateTime(row.get("FechaHecho"), row.get("HoraHecho")),
        axis=1
    )

    df.drop(columns=["FechaHecho", "HoraHecho"], inplace=True, errors='ignore')
    data = df.where(pd.notnull(df), None).to_dict(orient='records')
    location_data=['latitud', 'longitud', 'Estado_hechos', 'Municipio_hechos', 'ColoniaHechos', 'Calle_hechos' ]

    has_street2 = 'Calle_hechos2' in df.columns

    for event in data:
        try:
            if not location_check(event, location_data):
                resolveBulkGeo(event, has_street2)

            event['icon'] = resolveIcons(event.get('Categoria'))
            event['updatedAt'] = datetime.datetime.now(datetime.timezone.utc)
            event['Categoria'] = event.get('Categoria', '').upper()
            db.collection('Eventos').add(event)
        except:
            error_message = "Error al subir evento"
            return redirect(f"/loadFiles?error={urllib.parse.quote(error_message)}")
    success_message = "La carga de datos ha sido exitosa"
    return redirect(f"/loadFiles?success={urllib.parse.quote(success_message)}")

