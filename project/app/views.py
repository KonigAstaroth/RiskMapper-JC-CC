from django.shortcuts import render,redirect
from django.conf import settings
from datetime import timedelta
import urllib.parse
import datetime
from datetime import timezone
import json
from django.utils.safestring import mark_safe
from django.utils import timezone as dj_timezone
from google.cloud.firestore import FieldFilter
import matplotlib
matplotlib.use('agg')
import numpy as np
from time import time
from collections import defaultdict
from django.core.cache import cache
import tracemalloc

import math

# Quitar despues, solo es para evitar errores en main y otros
from app.core.auth.firebase_config import db, auth
from app.src.AI_generation_service import genAI
from app.src.utils.report_generation_utils.hourly_range import getRange
from app.src.utils.report_generation_utils.parse_timestamp_num import time_to_num

# Imports needed for context & display important info
from app.src.admin_service.admins import getPrivileges
from app.src.utils.users import getUsers
from app.src.utils.getCoords import getLatLng
from app.src.library_service import searchEvent
from app.src.graph_generation_service import genDataImg, genGraph, generateCalendar

CACHE_KEY_MARKERS = 'firebase_markers'
CACHE_KEY_LAST_UPDATE = 'firebase_markers_last_update'

def signup(request):            
     error = request.GET.get("error")
     return render(request, 'signup.html', {"error": error})

def subscriptions(request):
     return render(request, 'selectSub.html')

def success(request):
     # plan = request.session.get('plan')
     # email = request.session.get('email_usr')
     # try:
          
     #      user = auth.get_user_by_email(email)
     # except:
     #      return HttpResponse('Usuario no autenticado', status=401)
     
     # if plan not in ['esencial', 'premium', 'profesional']:
     #      return HttpResponse("Plan inválido", status=400)
     
     # PLAN_CONFIG ={
     #      'esencial': {'requests': 10, 'events': 100},
     #      'premium': {'requests': 50, 'events': 200},
     #      'profesional': {'requests': 80, 'events': 2000}
     # }

     # config=PLAN_CONFIG[plan]
     # sub_type = plan
     # requests = config['requests']
     # events = config['events']

     # user_doc = db.collection('Usuarios').document(user.uid)

     # now = datetime.datetime.now(timezone.utc)
     # endSub = now + datetime.timedelta(days=30)
     # end_sub = datetime.datetime.combine(endSub.date(), time(23,59), tzinfo=timezone.utc)
     # try:
     #      user_doc.update({
     #           'sub_type': sub_type,
     #           'requests': requests,
     #           'events': events,
     #           'start_sub': now,
     #           'last_sub': now,
     #           'end_sub': end_sub,
     #           'status': "active"

     #      })
     # except Exception as e:
     #      return HttpResponse('Usuario no encontrado', status=401)

     return render(request, 'success.html')

def login(request):
    sessionCookie = request.COOKIES.get('session')
    if sessionCookie:
         decoded_claims = auth.verify_session_cookie(sessionCookie, check_revoked=True)
         uid = decoded_claims["uid"]
         db.collection('Usuarios').document(uid).update({'lastAccess': datetime.datetime.now(timezone.utc)})
         return redirect ("main")

    return render(request, 'login.html')

def policy (request):
    return render(request, 'policy.html')

def forgotpass (request):             
    error = request.GET.get("error")
    success = request.GET.get("success")
    return render(request, 'forgotPass.html', {'error':error, 'success': success})

def recoverPass (request, token):
     error = request.GET.get("error")
     success = request.GET.get('success')
     return render(request, 'recoverPass.html', {'error': error, 'success':success})

def main (request):
     sessionCookie = request.COOKIES.get('session')
     priv = getPrivileges(request)
     idioma = request.GET.get("idioma", "es")
     request.session['lang'] = idioma

     if not sessionCookie:
          return redirect ("login")
     try:
          decoded_claims = auth.verify_session_cookie(sessionCookie, check_revoked=True)
          uid = decoded_claims["uid"]
     except:
          return redirect("login")
     
     usuarios = getUsers()


     # datos necesarios para google maps
     last_update = cache.get(CACHE_KEY_LAST_UPDATE)
     markers_cached = cache.get(CACHE_KEY_MARKERS)

          
     ref = db.collection('Eventos')
     
     query_has_update = False
     
     
     if last_update:
          changes_query = ref.where('updatedAt', '>', last_update)
          changes = changes_query.limit(1).get()
          query_has_update = len(changes) > 0
     else:
          query_has_update =True
     
     map_config = {
        'center': {'lat': 19.42847, 'lng': -99.12766},
        'zoom': 6
     }

     def clean_value(v):
          if isinstance(v, float) and math.isnan(v):
               return None
          return v

     if query_has_update:
          data = ref.limit(500).get() or []
          list_markers = []
          max_update = last_update

          for doc in data:
               valor = doc.to_dict()
               update_doc = valor.get('updatedAt')
               if update_doc:
                    if not max_update or update_doc > max_update:
                         max_update = update_doc

               
               fecha_obj = valor.get('FechaHoraHecho')
               fecha_str = ''
               if fecha_obj:
                    fecha_local = dj_timezone.localtime(fecha_obj)
                    fecha_str = fecha_local.strftime('%d/%m/%Y, %H:%M:%S')
               marker = {
                    'lat': clean_value(valor.get('latitud')),
                    'lng': clean_value(valor.get('longitud')),
                    'Categoria': clean_value(valor.get('Categoria')),
                    'icono': clean_value(valor.get('icono')),
                    'delito': clean_value(valor.get('Delito')),
                    'fecha': fecha_str,
                    'calle': clean_value(valor.get('Calle_hechos')),
                    'colonia': clean_value(valor.get('ColoniaHechos')),
                    'estado': clean_value(valor.get('Estado_hechos')),
                    'municipio': clean_value(valor.get('Municipio_hechos')),
                    'descripcion': clean_value(valor.get('Descripcion'))
               }
               list_markers.append(marker)
          cache.set(CACHE_KEY_MARKERS, list_markers, None)
          cache.set(CACHE_KEY_LAST_UPDATE, max_update, None)
     else:
          list_markers = markers_cached or []

     markers_json = mark_safe(json.dumps(list_markers))

     #Filtrado de datos
     graphic = request.session.get('graphic')
     calendarios = request.session.get('calendarios', [])
     
     hour_txt = request.session.get('hour_txt', None)
     AiText = request.session.get('AiText', None)
     lugar = request.session.get('lugar')
     tabla = request.session.get('tabla_base64', None)
     

     if request.method != 'POST':
          if not request.session.get('desde_busqueda'):
               request.session.pop('desde_busqueda', None)
               
          else:
               if not request.session.get('ready_to_export'):
                    request.session.pop('graphic', None)
                    request.session.pop('calendarios', None)
                    request.session.pop('lugar', None)
                    request.session.pop('hour_txt', None)
                    request.session.pop('AiText', None)
                    request.session.pop('tabla_base64', None)
                    map_config = request.session.pop('map_config', {
                         'center': {'lat': 19.42847, 'lng': -99.12766},
                         'zoom': 6
                         })
          if 'map_config' in request.session:
               map_config = request.session['map_config']
               
     
     
     

     lista_delitos= [
          {'valor': 'AMENAZAS', 'nombre': 'Amenazas'},
          {'valor': 'ROBO A NEGOCIO', 'nombre': 'Robo a negocio'},
          {'valor': 'HOMICIDIO DOLOSO', 'nombre': 'Homicidio doloso'},
          {'valor': 'FEMINICIDIO', 'nombre': 'Feminicidio'},
          {'valor': 'SECUESTRO', 'nombre': 'Secuestro'},
          {'valor': 'TRATA DE PERSONAS', 'nombre': 'Trata de personas'},
          {'valor': 'ROBO A TRANSEÚNTE', 'nombre': 'Robo a transeúnte'},
          {'valor': 'EXTORSIÓN', 'nombre': 'Extorsión'},
          {'valor': 'ROBO A CASA HABITACIÓN', 'nombre': 'Robo a casa habitación'},
          {'valor': 'VIOLACIÓN', 'nombre': 'Violación'},
          {'valor': 'NARCOMENUDEO', 'nombre': 'Narcomenudeo'},
          {'valor': 'CATEGORIA DE BAJO IMPACTO', 'nombre': 'Delito de bajo impacto'},
          {'valor': 'ARMA DE FUEGO', 'nombre': 'Lesión con arma de fuego'},
          {'valor': 'ROBO DE ACCESORIOS DE AUTO', 'nombre': 'Robo de accesorios de auto'},
          {'valor': 'ROBO A CUENTAHABIENTE SALIENDO DEL CAJERO CON VIOLENCIA', 'nombre': 'Robo a cuentahabiente'},
          {'valor': 'ROBO DE VEHÍCULO', 'nombre': 'Robo de vehículo'},
          {'valor': 'ROBO A PASAJERO A BORDO DE MICROBUS', 'nombre': 'Robo en microbús'},
          {'valor': 'ROBO A REPARTIDOR', 'nombre': 'Robo a repartidor'},
          {'valor': 'ROBO A PASAJERO A BORDO DEL METRO', 'nombre': 'Robo en metro'},
          {'valor': 'LESIONES DOLOSAS POR DISPARO DE ARMA DE FUEGO', 'nombre': 'Lesiones por arma de fuego'},
          {'valor': 'HECHO NO DELICTIVO', 'nombre': 'Hecho no delictivo'},
          {'valor': 'ROBO A PASAJERO A BORDO DE TAXI CON VIOLENCIA', 'nombre': 'Robo en taxi'},
          {'valor': 'ROBO A TRANSPORTISTA', 'nombre': 'Robo a transportista'},
     ]

     color_delitos = [
          {'valor': 'AMENAZAS', 'nombre': 'Amenazas', 'color': '#8A2BE2'},
          {'valor': 'ROBO A NEGOCIO', 'nombre': 'Robo a negocio', 'color': '#FF69B4'},
          {'valor': 'HOMICIDIO DOLOSO', 'nombre': 'Homicidio doloso', 'color': '#4B0082'},
          {'valor': 'FEMINICIDIO', 'nombre': 'Feminicidio', 'color': '#DC143C'},
          {'valor': 'SECUUESTRO', 'nombre': 'Secuestro', 'color': '#FF1493'},
          {'valor': 'TRATA DE PERSONAS', 'nombre': 'Trata de personas', 'color': '#B22222'},
          {'valor': 'ROBO A TRANSEÚNTE', 'nombre': 'Robo a transeúnte', 'color': '#00FF00'},
          {'valor': 'EXTORSIÓN', 'nombre': 'Extorsión', 'color': '#DAA520'},
          {'valor': 'ROBO A CASA HABITACIÓN', 'nombre': 'Robo a casa habitación', 'color': '#800080'},
          {'valor': 'VIOLACIÓN', 'nombre': 'Violación', 'color': '#8B0000'},
          {'valor': 'NARCOMENUDEO', 'nombre': 'Narcomenudeo', 'color': '#006400'},
          {'valor': 'CATEGORIA DE BAJO IMPACTO', 'nombre': 'Delito de bajo impacto', 'color': '#A0A0A0'},
          {'valor': 'ARMA DE FUEGO', 'nombre': 'Lesión con arma de fuego', 'color': '#00008B'},
          {'valor': 'ROBO DE ACCESORIOS DE AUTO', 'nombre': 'Robo de accesorios de auto', 'color': '#A0522D'},
          {'valor': 'ROBO A CUENTAHABIENTE SALIENDO DEL CAJERO CON VIOLENCIA', 'nombre': 'Robo a cuentahabiente', 'color': '#FF0000'},
          {'valor': 'ROBO DE VEHÍCULO', 'nombre': 'Robo de vehículo', 'color': '#FFA500'},
          {'valor': 'ROBO A PASAJERO A BORDO DE MICROBUS', 'nombre': 'Robo en microbús', 'color': '#FFD700'},
          {'valor': 'ROBO A REPARTIDOR', 'nombre': 'Robo a repartidor', 'color': '#ADFF2F'},
          {'valor': 'ROBO A PASAJERO A BORDO DEL METRO', 'nombre': 'Robo en metro', 'color': '#00FFFF'},
          {'valor': 'LESIONES DOLOSAS POR DISPARO DE ARMA DE FUEGO', 'nombre': 'Lesiones por arma de fuego', 'color': '#00008B'},
          {'valor': 'HECHO NO DELICTIVO', 'nombre': 'Hecho no delictivo', 'color': '#D3D3D3'},
          {'valor': 'ROBO A PASAJERO A BORDO DE TAXI CON VIOLENCIA', 'nombre': 'Robo en taxi', 'color': '#40E0D0'},
          {'valor': 'ROBO A TRANSPORTISTA', 'nombre': 'Robo a transportista', 'color': '#0000FF'},
     ]


     
     if request.method == 'POST' and 'buscar' in request.POST :
          # process = psutil.Process(os.getpid())
          # mem_inicio = process.memory_info().rss / 1024**2
          # cpu_inicio = psutil.cpu_percent(interval=0.1)

          # print(f"[ANTES] Memoria: {mem_inicio:.2f} MB, CPU: {cpu_inicio}%")

          # tracemalloc.start() 
          filters = {}
          filtersAi = {}
          direccion = ""
          graphic = []
          calendarios = []
          banner = []
          tabla = None
          
          str_startDate = None
          str_endDate_API = None
          descripcion_cliente = ""
          
          municipio = request.POST.get('municipio')
          estado = request.POST.get('estado')
          startDate_str = request.POST.get('startDate')
          endDate_str = request.POST.get('endDate')
          delitos_select = request.POST.getlist('delitos')
          descripcion_cliente = request.POST.get('descripcion_cliente')


          if municipio:
               filters['Municipio_hechos'] = municipio
               filtersAi['Municipio'] = municipio
               direccion += municipio + ', '
               banner.append(municipio)
          if estado:
               filters['Estado_hechos'] = estado
               filtersAi['Estado'] = estado
               direccion += estado + ', '
               banner.append(estado)

          map_config = getLatLng(direccion)
          lugar = ', '.join(f"{k}" for k in banner)
          
          if startDate_str and endDate_str:
               startDate = datetime.datetime.strptime(startDate_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
               endDate_inclusive = datetime.datetime.strptime(endDate_str, "%Y-%m-%d").replace(tzinfo=timezone.utc) 
               endDate_DB = endDate_inclusive + timedelta(days=1)
               
               str_startDate = startDate.strftime("%Y-%m-%d")
               str_endDate_API = endDate_inclusive.strftime("%Y-%m-%d")
               filters['startDate']=startDate
               filters['endDate']=endDate_DB
          else:
               pass

          now = datetime.datetime.now(timezone.utc)
          lang = request.session.get('lang')
          AiText = genAI(filtersAi, str_startDate,str_endDate_API, now, delitos_select, request)
          

          if not (('startDate' in filters and 'endDate' in filters) or any(k in filters for k in ['Municipio_hechos', 'Estado_hechos', 'Calle_hechos', 'ColoniaHechos'])):
               request.session['graphic'] = []
               request.session['calendarios'] = []
               request.session['tabla_base64'] = None
               request.session['ready_to_export'] = True
               request.session['hour_txt'] = "No se encontraron eventos para graficar."
               request.session['AiText'] = mark_safe(AiText)
               request.session['lugar'] = lugar
               request.session['map_config'] = map_config
               return redirect("main")
               
          

          query_ref = ref

          if filters:
               for campo, valor in filters.items():
                    if campo == "startDate":
                         query_ref = query_ref.where(filter=FieldFilter("FechaHoraHecho", '>=', valor))
                    elif campo == "endDate":
                         query_ref = query_ref.where(filter=FieldFilter("FechaHoraHecho", '<=', valor))
                    else:
                         if isinstance(valor, str):
                              valor = valor.strip() 
                         query_ref = query_ref.where(filter=FieldFilter(campo, '==', valor))
          if delitos_select:
               if len(delitos_select)<= 10:
                    query_ref = query_ref.where(filter=FieldFilter("Categoria", "in", delitos_select))
               else:
                    error_message = "Demasiados delitos seleccionados para aplicar filtro 'in'"
                    return redirect(f"/main?error={urllib.parse.quote(error_message)}")
               
          preview = list(query_ref.limit(1).stream())

          if not preview:
               request.session['graphic'] = []
               request.session['calendarios'] = []
               request.session['tabla_base64'] = None
               request.session['ready_to_export'] = True
               request.session['hour_txt'] = "No se encontraron eventos para graficar."
               request.session['AiText'] = mark_safe(AiText)
               request.session['lugar'] = lugar
               request.session['map_config'] = map_config
               request.session['now_str']  = now.strftime("%d-%m-%Y")
               return redirect("main")

          # mem_despues = process.memory_info().rss / 1024**2
          # cpu_despues = psutil.cpu_percent(interval=0.1)

          # print(f"[DESPUÉS] Memoria: {mem_despues:.2f} MB, CPU: {cpu_despues}%")
          # print(f"[DIFERENCIA] Memoria usada durante proceso: {mem_despues - mem_inicio:.2f} MB")

          

          eventos_por_mes = defaultdict(list)
          graficos_por_mes = defaultdict(list)
          cat_color = []

          

          resultados = list(query_ref.stream())

          eventos_lista=[doc.to_dict() for doc in resultados]
          conteo_delitos = defaultdict(int)
          

          hora_critica, cantidad = getRange(eventos_lista)
          
          if hora_critica is not None:
               if cantidad > 1:
                    if lang == 'en':
                         hour_txt = f"Between {hora_critica}:00 and {hora_critica+1}:00 it was registered {cantidad} events, which highlights this interval as a possible risk point."
                    elif lang == 'es':
                         hour_txt = f"Entre las {hora_critica}:00 y las {hora_critica+1}:00 horas se registró {cantidad} eventos, lo que destaca este intervalo como un posible punto de riesgo."
               elif cantidad == 1:
                    if lang == 'en':
                         hour_txt = f"Between {hora_critica}:00 and {hora_critica+1}:00 it was registered {cantidad} event, which highlights this interval as a possible risk point."
                    elif lang == 'es':
                         hour_txt = f"Entre las {hora_critica}:00 y las {hora_critica+1}:00 horas se registró {cantidad} evento, lo que destaca este intervalo como un posible punto de riesgo."
          else:
               hour_txt = "No hay eventos para calcular rango horario crítico."

          
          for  eventos in eventos_lista:
               date_obj = eventos.get('FechaHoraHecho')
               if not date_obj:
                    continue
               fecha = date_obj
               categorie = eventos.get('Categoria')
               

               match = next((item for item in color_delitos if item['valor'] == categorie), None)
               if match:
                    nombre = match['nombre']
                    color = match['color']
               else:
                    nombre = 'Otro'
                    color = 'gray'

               conteo_delitos[nombre] += 1

               if not any(c['nombre'] == nombre for c in cat_color):
                    cat_color.append({'nombre': nombre, 'color': color})

               if fecha:
                    if isinstance(fecha,str):
                         fecha = datetime.fromisoformat(fecha)
                    elif hasattr(fecha, 'to_datetime'):
                         fecha = fecha.to_datetime()

                    year = fecha.year
                    month = fecha.month
                    day = fecha.day
               

               eventos_por_mes[(year, month)].append((day, categorie))
               

               if date_obj:
                    hora_local = dj_timezone.localtime(date_obj)
                    hora_str = hora_local.strftime('%H:%M:%S').strip()
                    hora_str = ''.join(c for c in hora_str if c.isdigit() or c == ':')
                    segundos = time_to_num(hora_str)
                    if segundos is not None:
                         angulo = (segundos/86400) * 2 * np.pi
                         dia = hora_local.day
                         graficos_por_mes[(year, month)].append((angulo, dia, categorie))
                    
          for (year, month), day in eventos_por_mes.items():
                    if not day:
                         continue
                    else:
                         imagen_base64  = generateCalendar(year, month, day)
                         if imagen_base64:
                              calendarios.append({
                                   'img': imagen_base64 
                              })
                         else:
                              error_message = "No se pudo el calendario"
                              return redirect(f"/main?error={urllib.parse.quote(error_message)}")
                    puntos_mes = graficos_por_mes.get((year,month), [])
                    if not puntos_mes:
                         continue
                    else:
                         if puntos_mes:
                              graphic_img = genGraph(puntos_mes)
                              graphic.append({
                                   'img': graphic_img
                              })
                         else:
                              error_message = "No se pudo la grafica"
                              return redirect(f"/main?error={urllib.parse.quote(error_message)}")  
                         
          cat_color_cuenta = []
          for item in cat_color:
               nombre = item['nombre']
               color = item['color']
               cuenta = conteo_delitos.get(nombre, 0)
               cat_color_cuenta.append({'nombre': nombre, 'color': color, 'cuenta': cuenta})
          
          tabla = genDataImg(cat_color_cuenta)
          
     

          # snapshot = tracemalloc.take_snapshot()
          # top_stats = snapshot.statistics('lineno')

          # print("[TRACEMALLOC] Top 10 líneas con mayor consumo de memoria:")
          # for stat in top_stats[:10]:
          #      print(stat)
          request.session['graphic'] = graphic
          request.session['calendarios'] = calendarios
          request.session['lugar'] = lugar
          request.session['hour_txt'] = hour_txt
          request.session['desde_busqueda'] = True
          request.session['AiText'] = mark_safe(AiText)
          request.session['map_config'] = map_config
          request.session['tabla_base64'] = tabla
          request.session['ready_to_export'] = True
          request.session['now_str']  = now.strftime("%d-%m-%Y")
          return redirect('main') 
          
     error = request.GET.get("error")

     context = {
          'priv': priv,
          'usuarios': usuarios,
          'google_maps_api_key': settings.GOOGLE_MAPS_KEY,
          'markers': markers_json,
          'graphic': graphic,
          'calendarios': calendarios,
          'timestamp': int(time()),
          'lugar': lugar,
          'hour_txt': hour_txt,
          'AiText': AiText,
          'map_config_json': json.dumps(map_config),
          'error': error,
          'lista_delitos': lista_delitos,
          'tabla_base64': tabla,
          
     }

    
     return render (request, 'main.html', context)

def add (request):            
     success = request.GET.get("success")
     error = request.GET.get("error")
     return render (request, "addUser.html", {"success": success, "error": error})

def manageUsers(request):
     query = request.GET.get("search")
     usuarios = getUsers(query)
     priv = getPrivileges(request)
     sessionCookie = request.COOKIES.get('session')
     
     if not priv:
          return redirect("main")
     
     if not sessionCookie:
          return redirect ("login")
     success = request.GET.get("success")
     error = request.GET.get("error")
     return render(request, 'manageUser.html', {"usuarios": usuarios, "success": success, "error": error})


def loadFiles(request):
    sessionCookie = request.COOKIES.get('session')
    priv = getPrivileges(request)

    try:
        decoded_claims = auth.verify_session_cookie(sessionCookie, check_revoked=True)
        uid = decoded_claims["uid"]
    except Exception as e:
        print("Error autenticando:", e)
        return redirect("login")

    if not sessionCookie:
        return redirect("login")
    usuarios = getUsers()     
    success = request.GET.get("success")
    error = request.GET.get("error")
    return render(request, "loadFiles.html", {"error": error, 'success': success, 'usuarios': usuarios, 'priv': priv,})


def library(request):
    sessionCookie = request.COOKIES.get('session')
    priv = getPrivileges(request)
    eventos =[]

    if not sessionCookie:
        return redirect("login")
    try:
        decoded_claims = auth.verify_session_cookie(sessionCookie, check_revoked=True)
        uid = decoded_claims["uid"]
    except:
        return redirect("login")

    usuarios = getUsers()
    
    if request.method == 'POST':
          eventos = searchEvent(request)

    return render(request, 'library.html', {
        'usuarios': usuarios,
        'eventos': eventos,
        'priv': priv
    })
