import pandas as pd
import math
import re

def check_valid_value(valor):
     if valor is None:
        return False
     if pd.isna(valor):
          return False
     if isinstance(valor, float) and math.isnan(valor):
        return False
     return str(valor).strip().upper() not in ['NA', 'N/A', '', 'NONE']

def location_check(evento, campos):
     return all(evento.get(campo) not in ['', None, 'NA', 'N/a', 'n/a', 'N/A', 'na'] for campo in campos)

def getEstadoMunicipio(location):
     municipio = estado = None
     if location and location.raw.get('address_components', []):
          for comp in location.raw['address_components']:
               tipos = comp['types']
               if 'locality' in tipos or 'sublocality' in tipos or 'administrative_area_level_2' in tipos:
                    municipio = comp['long_name']
               elif 'administrative_area_level_1' in tipos:
                    estado = comp['long_name']
     return municipio, estado

def build_address(evento, has_street2=False):
     partes = [
        evento.get('Calle_hechos'),
        evento.get('Calle_hechos2') if has_street2 else None,
        evento.get('ColoniaHechos'),
        evento.get('Municipio_hechos'),
        evento.get('Estado_hechos')
     ]
     
     return ', '.join(p for p in partes if check_valid_value(p))

def sanitize_text(text):
     if text == None:
          return ""
     
     text = str(text).strip()
     text = re.sub(r'\s+', ' ', text)

     return text.title()

def  is_valid_float(number):
     try:
          float(number)
          return True
     except:
          return False