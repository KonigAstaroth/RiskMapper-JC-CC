from geopy.geocoders import GoogleV3
from django.conf import settings

def resolveManualGeo(data):
    geolocator = GoogleV3(api_key=settings.GOOGLE_MAPS_KEY)

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