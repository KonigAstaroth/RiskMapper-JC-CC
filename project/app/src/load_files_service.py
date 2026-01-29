import datetime
from django.shortcuts import redirect
import urllib.parse
from app.src.utils.resolve_icons import resolveIcons
from app.src.utils.events_geo import resolveManualGeo
from app.core.auth.firebase_config import db
from app.src.utils.parse_timestamp import parseTimestamp


def loadFilesService(request):
    if request.method == 'POST':
        if 'archivo' in request.FILES:
            excel_file = request.FILES['archivo']
            # Procesar el archivo según sea necesario
            bulkLoad(request, excel_file)
        else:
            # Manejo de carga manual
            handleManualLoad(request)


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


def bulkLoad(request, file):
    return

