from geopy.geocoders import GoogleV3
from django.conf import settings
from google_crc32c import exc
from app.src.utils.bulk_load_helpers import check_valid_value, getEstadoMunicipio, build_address, getCalleColonia, sanitize_text

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
                    street_name = sanitize_text(comp['long_name'])
                elif 'street_number' in types:
                    street_number = comp['long_name']
                elif 'sublocality' in types or 'sublocality_level_1' in types:
                    data['colonia'] = sanitize_text(comp['long_name'])
                elif 'locality' in types:
                    data['municipio'] = sanitize_text(comp['long_name'])
                elif 'administrative_area_level_1' in types:
                    data['estado'] = sanitize_text(comp['long_name'])

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
        return data

def resolveBulkGeo(event, has_adress2 = False):

    has_coords = check_valid_value(event.get('latitud')) and check_valid_value(event.get('longitud'))
    has_city = check_valid_value(event.get('Municipio_hechos'))
    has_state = check_valid_value(event.get('Estado_hechos'))

    street = event.get('Calle_hechos')
    sublocality = event.get('ColoniaHechos')

    has_address = check_valid_value(street) and  check_valid_value(sublocality)

    # Has coordinates
    if has_coords:
        # If doesn't have state and city
        lat = event['latitud']
        lng = event['longitud']

        location = None
        try:
            location = geolocator.reverse((lat,lng))
        except: 
            location = None

        if location:
            if not has_city or not has_state:
                municipio, estado = getEstadoMunicipio(location)

                if municipio:
                    event['Municipio_hechos'] = municipio
                if estado:
                    event['Estado_hechos'] = estado

            # If it doesn't have street or sublocality
            if not has_address:
                calle, colonia = getCalleColonia(location)  

                if calle:
                    event['Calle_hechos'] = calle
                if colonia:
                    event['ColoniaHechos'] = colonia    
    # It doesn't have coords but city and state
    else:
        address= build_address(event, has_adress2)
        ubi = geolocator.geocode(address)
        try:
            if ubi:
                event['latitud'] = ubi.latitude
                event['longitud'] = ubi.longitude
        except Exception:
            pass

    return event
        