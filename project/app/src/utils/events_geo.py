from geopy.geocoders import GoogleV3
from django.conf import settings
from app.src.utils.bulk_load_helpers import location_check, check_valid_value, getEstadoMunicipio, build_address

geolocator = GoogleV3(api_key=settings.GOOGLE_MAPS_KEY)

def resolveManualGeo(data):

    calle = data.get("calle")
    colonia = data.get("colonia")
    municipio = data.get("municipio")
    estado = data.get("estado")
    lat = data.get("lat")
    lng = data.get("lng")

    if all([calle, colonia, municipio, estado, lat, lng]):
        return data
    
    if lat and lng and not all([calle, colonia, estado, municipio]):
        location = geolocator.reverse((lat,lng))
        if location and location.raw:
            componentes = location.raw.get('address_components', [])
            for comp in componentes:
                types = comp['types']
                if 'route' in types :
                    street_name = comp['long_name']
                elif 'street_number' in types:
                    street_number = comp['long_name']
                elif 'sublocality' in types or 'sublocality_level_1' in types:
                    data['colonia'] = comp['long_name']
                elif 'locality' in types:
                    data['municipio'] = comp['long_name']
                elif 'administrative_area_level_1' in types:
                    data['estado'] = comp['long_name']

                if street_name and street_number:
                    data['calle'] = f"{street_name} {street_number}"
                else:
                    data['calle'] = street_name
        return data
    
    if all([calle, colonia, municipio, estado]) and not (lat and lng):
        direccion=f"{calle}, {colonia}, {estado}, {municipio}"
        location = geolocator.geocode(direccion)
        data['lat'] = location.latitude
        data['lng'] = location.longitude

def resolveBulkGeo(event, has_adress2 = False):
    if not (check_valid_value(event.get('latitud')) and check_valid_value(event.get('longitud'))):
        return
    lat = event['latitud']
    lng = event['longitud']

    if not check_valid_value(event.get('Estado_hechos')) or not check_valid_value(event.get('Municipio_hechos')):
        location = geolocator.reverse((lat,lng))
        municipio, estado = getEstadoMunicipio(location)

        if municipio:
            event['Municipio_hechos'] = municipio
        if estado:
            event['Estado_hechos'] = estado
    if check_valid_value(event.get('Estado_hechos')) and check_valid_value(event.get('Municipio_hechos')):
        address= build_address(event, has_adress2)
        ubi = geolocator.geocode(address)

        if ubi:
            event['latitud'] = ubi.latitude
            event['longitud'] = ubi.longitude
        