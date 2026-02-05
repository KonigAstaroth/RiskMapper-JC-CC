from geopy.geocoders import GoogleV3
from django.conf import settings

def getLatLng(direccion):
     try:
          geolocator = GoogleV3(api_key=settings.GOOGLE_MAPS_KEY)
          location = geolocator.geocode(direccion)
          if location:
               lat = location.latitude
               lng = location.longitude
          else:
               lat = None
               lng = None
          map_config = {
               'center': {'lat': float(lat) if lat is not None else 19.42847, 
                         'lng': float(lng) if lng is not None else -99.12766
               },
               'zoom': 14 if lat and lng else 6
          }
          return map_config
     except Exception as e:
          print(str(e))
          return {
            'center': {'lat': 19.42847, 'lng': -99.12766},
            'zoom': 6
        }