import requests
from django.shortcuts import render,redirect
from django.conf import settings
from django.contrib import messages
from firebase_admin import firestore, auth
from datetime import timedelta
import urllib.parse
import datetime
from datetime import timezone
import pandas as pd
import json
from django.utils.safestring import mark_safe
from django.utils import timezone as dj_timezone
from google.cloud.firestore import FieldFilter
import matplotlib.pyplot as plt
import matplotlib
import calendar
matplotlib.use('agg')
import numpy as np
import io
import base64
from time import time
from geopy.geocoders import GoogleV3
from collections import defaultdict
from django.core.cache import cache
from .utils import sendEmail
from docx import Document
from docx.shared import Inches, Pt
from io import BytesIO
from django.http import HttpResponse
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from collections import Counter





db = firestore.client()
CACHE_KEY_MARKERS = 'firebase_markers'
CACHE_KEY_LAST_UPDATE = 'firebase_markers_last_update'

FIREBASE_AUTH_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={settings.FIREBASE_API_KEY}"

def login(request):
    sessionCookie = request.COOKIES.get('session')
    if sessionCookie:
         decoded_claims = auth.verify_session_cookie(sessionCookie, check_revoked=True)
         uid = decoded_claims["uid"]
         db.collection('Usuarios').document(uid).update({'lastAccess': datetime.datetime.now(timezone.utc)})
         return redirect ("main")

    if request.method == 'POST':
        recaptcha_response = request.POST.get('g-recaptcha-response')

        data = {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }
        verify_url = 'https://www.google.com/recaptcha/api/siteverify'
        result = requests.post(verify_url, data=data).json()

        if not result.get('success'):
            messages.error(request, "Se debe de validar el CAPTCHA")
            return redirect('/')
        
        email = request.POST["email"]
        password = request.POST["password"]
        remember = request.POST.get("remember")
             
        login = {"email": email, "password": password, "returnSecureToken": True}
        auth_response = requests.post(FIREBASE_AUTH_URL, json=login)
        
        if auth_response.status_code == 200:
                user_data = auth_response.json()
                id_token = user_data["idToken"]
                if remember == "checked":
                     expires_in = timedelta(days=14)
                else: 
                    expires_in = timedelta(days=1)

                try:
                    session_cookie = auth.create_session_cookie(id_token, expires_in=expires_in)
                    response_redirect = redirect("main")
                    response_redirect.set_cookie(
                        key='session',
                        value=session_cookie,
                        max_age=expires_in.total_seconds(),
                        httponly=True,
                        secure=False  # Cambiar a True en producción con HTTPS
                    )
                    decoded_claims = auth.verify_session_cookie(session_cookie)
                    uid = decoded_claims["uid"]
                    db.collection('Usuarios').document(uid).update({'lastAccess': datetime.datetime.now(timezone.utc)})
                    
                    return response_redirect
                except Exception as e:
                    messages.error(request, "Error al crear la cookie de sesión:", str(e))
                    return redirect('/')
        else:
             messages.error(request, "Correo o contraseña incorrectos") 
             return redirect('/')
    return render(request, 'login.html')

def policy (request):
    return render(request, 'policy.html')

def generate_token(email, uid):
     s = URLSafeTimedSerializer(settings.SECRET_KEY)
     return s.dumps(email, salt="recover-pass")

def forgotpass (request):
    if request.method == "POST":
          try:
               
               email = request.POST.get('email')
               user = auth.get_user_by_email(email)
               if user:
                    token = generate_token(email, user.uid)
                    link = request.build_absolute_uri(f"http://127.0.0.1:8000/recoverPass/{token}/")
                    sendEmail(email, link)
                    success_message = "Correo para restablecer contraseña ha sido enviado"
                    return redirect(f"/forgotPassword?success={urllib.parse.quote(success_message)}")
                    
          except Exception as e:
               error_message = f"{e}"
               return redirect(f"/forgotPassword?error={urllib.parse.quote(error_message)}")
                  
    error = request.GET.get("error")
    success = request.GET.get("success")
    return render(request, 'forgotPass.html', {'error':error, 'success': success})

def recoverPass (request, token):
     s = URLSafeTimedSerializer(settings.SECRET_KEY)
     
     try:
          email = s.loads(token, salt="recover-pass", max_age = 900)
     except SignatureExpired:
          error_message = "El enlace ha expirado. Solicita uno nuevo."
          return redirect(f"/recoverPass/{token}?error={urllib.parse.quote(error_message)}") 
     except BadSignature:
          error_message = "El enlace es inválido."
          return redirect(f"/recoverPass/{token}?error={urllib.parse.quote(error_message)}") 
     
     if not email:
          return redirect('login')
     contra = request.POST.get('password')
     repassword = request.POST.get('repassword')
     
     if request.method == 'POST':
          
          if not contra or not repassword:
               error_message = "Faltan campos por llenar"
               return redirect(f"/recoverPass/{token}?error={urllib.parse.quote(error_message)}") 
          if contra != repassword:
               error_message = "Las contraseñas no coinciden"
               return redirect(f"/recoverPass/{token}?error={urllib.parse.quote(error_message)}")  
          
          try:
               
               user = auth.get_user_by_email(email)
               auth.update_user(user.uid, password=contra)
               success_message = "Contraseña restablecida"
               return redirect(f"/recoverPass/{token}?success={urllib.parse.quote(success_message)}")
          except Exception as e:
               error_message = str(e)
               return redirect(f"/recoverPass/{token}?error={urllib.parse.quote(error_message)}") 
          

     error = request.GET.get("error")
     success = request.GET.get('success')
     return render(request, 'recoverPass.html', {'error': error, 'success':success})

     

def time_to_num(time_str):
     try:
          hh, mm, ss = map(int, time_str.strip().split(':'))
          return ss +60*(mm + 60*hh)
     except Exception as e:
          print(f"Error al convertir '{time_str}': {e}")
          return None
     
def getRange(eventos):
     horas = []

     for evento in eventos:
        fecha = evento.get('FechaHoraHecho')
        if not fecha:
            print("Evento sin fecha:", evento)
            continue

        
        fecha_dt = None
        if isinstance(fecha, str):
            try:
                fecha_dt = datetime.fromisoformat(fecha)
            except Exception as e:
                print("Error al convertir string a datetime:", e)
                continue
        elif hasattr(fecha, 'to_datetime'):
            try:
                fecha_dt = fecha.to_datetime()
            except Exception as e:
                print("Error al usar to_datetime():", e)
                continue
        elif isinstance(fecha, datetime.datetime):
            fecha_dt = fecha
        else:
            print("Tipo de fecha no reconocido:", type(fecha))
            continue

        if fecha_dt.tzinfo is not None:
            fecha_local = dj_timezone.localtime(fecha_dt)
        else:
            fecha_local = fecha_dt  

        horas.append(fecha_local.hour)
     

     if not horas:
        return None, None

     ctr = Counter(horas)
     hora_critica, cantidad = ctr.most_common(1)[0]
     return hora_critica, cantidad

def main (request):
     sessionCookie = request.COOKIES.get('session')
     priv = getPrivileges(request)

     if not sessionCookie:
          return redirect ("login")
     try:
          decoded_claims = auth.verify_session_cookie(sessionCookie, check_revoked=True)
          uid = decoded_claims["uid"]
     except:
          return redirect("login")
     
     doc_ref = db.collection("Usuarios").document(uid)
     doc = doc_ref.get()

     if doc.exists:
          name = doc.to_dict().get("name")


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
     

     if query_has_update:
          data = ref.get() or []
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
                    'lat': valor.get('latitud'),
                    'lng': valor.get('longitud'),
                    'Categoria': valor.get('Categoria'),
                    'icono': valor.get('icono'),
                    'delito': valor.get('Delito'),
                    'fecha': fecha_str,
                    'calle': valor.get('Calle_hechos'),
                    'colonia': valor.get('ColoniaHechos'),
                    'estado': valor.get('Estado_hechos'),
                    'municipio': valor.get('Municipio_hechos')
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
     
     hour_txt = None
     
     if request.method == 'POST' and 'buscar' in request.POST :
          filters = {}
          
          
          
          calle = request.POST.get('calle')
          colonia = request.POST.get('colonia')
          municipio = request.POST.get('municipio')
          estado = request.POST.get('estado')
          startDate_str = request.POST.get('startDate')
          endDate_str = request.POST.get('endDate')
          Municipio = request.POST.get('municipio')
          Estado = request.POST.get('estado')
          
          

          if calle:
               filters['Calle_hechos'] = calle
          if colonia:
               filters['ColoniaHechos'] = colonia
          if municipio:
               filters['Municipio_hechos'] = municipio
          if estado:
               filters['Estado_hechos'] = estado
 
          if startDate_str and endDate_str:
               startDate = datetime.datetime.strptime(startDate_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
               endDate = datetime.datetime.strptime(endDate_str, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)
               filters['startDate']=startDate
               filters['endDate']=endDate
          
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
          resultados = list(query_ref.stream())

          eventos_lista=[doc.to_dict() for doc in resultados]

          hora_critica, cantidad = getRange(eventos_lista)

          if hora_critica is not None:
               hour_txt = f"{hora_critica}:00 a {hora_critica+1}:00, contiene una cantidad de {cantidad} de eventos"
          else:
               hour_txt = "No hay eventos para calcular rango horario crítico."

          eventos_por_mes = defaultdict(list)
          
          angulos =[]
          radios= []

         
          for  eventos in eventos_lista:
               date_obj = eventos.get('FechaHoraHecho')
               fecha = date_obj


               if isinstance(fecha,str):
                    fecha = datetime.fromisoformat(fecha)
               elif hasattr(fecha, 'to_datetime'):
                    fecha = fecha.to_datetime()

               year = fecha.year
               month = fecha.month
               day = fecha.day
               
               

               eventos_por_mes[(year, month)].append(day)
               

               if date_obj:
                    hora_local = dj_timezone.localtime(date_obj)
                    hora_str = hora_local.strftime('%H:%M:%S').strip()
                    hora_str = ''.join(c for c in hora_str if c.isdigit() or c == ':')
                    segundos = time_to_num(hora_str)
                    if segundos is not None:
                         angulo = (segundos/86400) * 2 * np.pi
                         angulos.append(angulo)
                         dia = hora_local.day
                         radios.append(dia)
                    
          for (year, month),day in eventos_por_mes.items():
                    imagen_base64  = generateCalendar(year, month, day)
                    if imagen_base64:
                         calendarios.append({
                              'img': imagen_base64 
                         })
                    else:
                         print("No hay calendario")

          if angulos and radios:
               fig =  plt.figure(figsize=(6,6))
               ax = plt.subplot(111, polar=True)
               sc = ax.scatter(angulos, radios, color='blue', s=80, alpha=0.75)
               ax.set_theta_direction(-1)
               ax.set_theta_offset(np.pi/2)

               horas =[f"{h:02d}:00" for h in range(24)]
               ticks = [(h/24) * 2 * np.pi for h in range(24)]
               ax.set_xticks(ticks)
               ax.set_xticklabels(horas, fontsize=8)
               ax.set_rlabel_position(135) 
               ax.set_ylim(0,31)
               
               
               buffer = io.BytesIO()
               plt.savefig(buffer, format='png')
               buffer.seek(0)
               img_png = buffer.getvalue()
               graphic = base64.b64encode(img_png).decode('utf-8')
               buffer.close()
          request.session['graphic'] = graphic
          request.session['calendarios'] = calendarios
          request.session['estado'] = Estado
          request.session['municipio'] = Municipio
          request.session['hour_txt'] = hour_txt
          request.session['desde_busqueda'] = True
          return redirect('main') 
     else:
          Municipio = request.session.get('municipio')
          Estado = request.session.get('estado')

          if request.session.pop('desde_busqueda', False) is not True:
               request.session.pop('graphic', None)
               request.session.pop('calendarios', None)
               request.session.pop('municipio', None)
               request.session.pop('estado', None)
               request.session.pop('hour_txt', None)

          
          
               

     context = {
          'name': name,
          'priv': priv,
          'usuarios': usuarios,
          'google_maps_api_key': settings.GOOGLE_MAPS_KEY,
          'markers': markers_json,
          'graphic': graphic,
          'calendarios': calendarios,
          'timestamp': int(time()),
          'municipio': Municipio,
          'estado': Estado,
          'hour_txt': hour_txt
          
     }

    
     return render (request, 'main.html', context)

def exportarDocx(request):
     graphic = request.session.get('graphic')
     calendarios = request.session.get('calendarios', [])
     horas = request.session.get('hour_txt')

     doc = Document()
     
     doc.add_heading('Análisis de eventos', 0)
     doc.add_paragraph("Parrafo generado por IA")

     for calendario in calendarios:
          img_base64 = calendario.get('img')
          if img_base64:
               if img_base64.startswith('data:image'):
                    img_base64 = img_base64.split(',')[1]
               try:
                    calendario_data = base64.b64decode(img_base64)
                    calendario_stream = BytesIO(calendario_data)
                    doc.add_heading('Gráfico de distribución por fecha:', level= 2)
                    doc.add_picture(calendario_stream, width=Inches(2))  
               except:
                    doc.add_paragraph('Error al cargar calendario')

     if graphic :
          if graphic.startswith('data:image'):
               graphic = graphic.split(',')[1]
          try:
               graphic_data = base64.b64decode(graphic)
               graphic_stream = BytesIO(graphic_data)
               doc.add_heading('Gráfico de distribución horaria:', level= 2)
               doc.add_picture(graphic_stream, width=Inches(4))  
          except:
               doc.add_paragraph('Error al agregar calendario')
     if horas:
          try:
               doc.add_paragraph( horas)
          except:
               doc.add_paragraph("No hay rango horario crítico")

     response = HttpResponse(
          content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
     )

     response['Content-Disposition'] = 'attachment; filename ="Analisis_de_eventos.docx"'
     doc.save(response)
     request.session.pop('graphic', None)
     request.session.pop('calendarios', None)
     request.session.pop('hour_txt', None)

     return response

def generateCalendar( year: int, month: int, days_event: list) -> str:
     cal = calendar.monthcalendar(year, month)
     fig, ax = plt.subplots(figsize=(5,5))
     ax.set_axis_off()
     ax.set_title(calendar.month_name[month] + f" {year}", fontsize=20)

     dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

     for i, dias in enumerate(dias_semana):
          ax.text(i+0.5, len(cal), dias, ha='center', va= 'center', fontsize=12, weight='bold')
     

     for fila, semana in enumerate(cal):
          for columna, dia in enumerate(semana):
               if dia != 0:
                    y = len(cal) - fila - 0.5
                    x = columna + 0.5
                    ax.text(x, y + 0.3, str(dia), ha='center', va='top', fontsize=10)
                    if dia in days_event:
                         circle = plt.Circle((x, y -0.2), 0.15, color= 'red')
                         ax.add_patch(circle) 

     plt.xlim(0, 7)
     plt.ylim(0, len(cal) + 1)
     plt.tight_layout()

     buffer = io.BytesIO()
     plt.savefig(buffer, format='png')
     buffer.seek(0)
     imagen_png = buffer.getvalue()
     imagen_base64 = base64.b64encode(imagen_png).decode('utf-8')
     buffer.close()
     
     plt.close()
     return imagen_base64 

def getPrivileges(request):
      sessionCookie = request.COOKIES.get('session')
      decoded_claims = auth.verify_session_cookie(sessionCookie, check_revoked=True)
      uid = decoded_claims["uid"]
      doc_ref = db.collection("Usuarios").document(uid)
      doc = doc_ref.get()
      if doc.exists:
           return doc.to_dict().get("privileges",False)
      else:
           return False


def logout (request):
     response = redirect("login")
     response.delete_cookie('session')
     request.session.flush()
     
     return response

def add (request):
     priv = getPrivileges(request)
     sessionCookie = request.COOKIES.get('session')
     
     try:
          decoded_claims = auth.verify_session_cookie(sessionCookie, check_revoked=True)
          uid = decoded_claims["uid"]
     except:
          return redirect("login")
     
     priv = getPrivileges(request)
     if not priv:
               return redirect("main")
     
     if not sessionCookie:
          return redirect ("login")
     
     if request.method == "POST":
          
        email = request.POST.get("email")
        password = request.POST.get("password")
        name = request.POST.get("name")
        lastname = request.POST.get("lastname")
        privileges = request.POST.get('privileges')

        if name and lastname and password and email and privileges:
             
             try:
                  user = auth.create_user(email=email, password=password)
                  db.collection("Usuarios").document(user.uid).set({
                    "email": email,
                    "name": name,
                    "lastname": lastname,
                    "privileges":privileges,
                    "lastAccess": None
                    
                    })
                  success_message = "Usuario agregado correctamente"
                  return redirect(f"/add?success={urllib.parse.quote(success_message)}")
             except Exception as e:
                  error_message = str(e)
                  return redirect(f"/add?error={urllib.parse.quote(error_message)}")
                  
        else:
             error_message = "Faltan campos por ser llenados"
             return redirect(f"/add?error={urllib.parse.quote(error_message)}")
                  
     success = request.GET.get("success")
     error = request.GET.get("error")
     return render (request, "addUser.html", {"success": success, "error": error,'priv': priv})

def manage_user(request):
     usuarios = getUsers()
     priv = getPrivileges(request)
     sessionCookie = request.COOKIES.get('session')
     
     try:
          decoded_claims = auth.verify_session_cookie(sessionCookie, check_revoked=True)
          uid = decoded_claims["uid"]
     except:
          return redirect("login")
     
     priv = getPrivileges(request)
     if not priv:
               return redirect("main")
     
     if not sessionCookie:
          return redirect ("login")
     return render(request, 'manageUser.html', {"usuarios": usuarios, "priv":priv})

def getUsers():
     docs = db.collection("Usuarios").stream()
     listUsers=[]

     for doc in docs:
          datos = doc.to_dict()
          datos['id'] = doc.id
          listUsers.append(datos)

     return listUsers

def editUser(request, id):
     
     if request.method == 'POST':
        uid = id
        updates = {}

        if name := request.POST.get('name'):
            updates['name'] = name

        if lastname := request.POST.get('lastname'):
            updates['lastname'] = lastname

        if email := request.POST.get('email'):
            updates['email'] = email
            if uid:
                try:
                    auth.update_user(uid, email=email)
                except Exception as e:
                    print("Error actualizando email:", e)

        if password := request.POST.get('password'):
            if uid:
                try:
                    auth.update_user(uid, password=password)
                except Exception as e:
                    print("Error actualizando contraseña:", e)

        if privileges := request.POST.get('privileges'):
            updates['privileges'] = privileges == 'true'

        if updates:
            db.collection('Usuarios').document(id).update(updates)
     return redirect('manageUser')
               

def deleteUser(request, id):
     if request.method == 'POST':
          doc_ref = db.collection('Usuarios').document(id)
          doc = doc_ref.get()
          if doc.exists:
               uid = id
               doc_ref.delete()
               if uid:
                    try:
                         auth.delete_user(uid)
                    except auth.UserNotFoundError:
                         pass
          
     return redirect('manageUser')

def display_users(request):
     usuarios = getUsers()
     priv = getPrivileges(request)
     sessionCookie = request.COOKIES.get('session')
     
     try:
          decoded_claims = auth.verify_session_cookie(sessionCookie, check_revoked=True)
          uid = decoded_claims["uid"]
     except:
          return redirect("login")
     
     priv = getPrivileges(request)
     if not priv:
               return redirect("main")
     
     if not sessionCookie:
          return redirect ("login")
     return (request,{"usuarios": usuarios, "priv":priv})

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

    if request.method == "POST":
        if 'archivo' in request.FILES:
            try:
                excel_file = request.FILES['archivo']
                df = pd.read_excel(excel_file, engine='openpyxl')

                def convertir_fecha(fecha):
                    if isinstance(fecha, str):
                        try:
                            return datetime.datetime.fromisoformat(fecha)
                        except:
                            return None
                    if isinstance(fecha, datetime.datetime):
                        return fecha
                    return None

                def convertir_hora(h):
                    if isinstance(h, str):
                        try:
                            return datetime.datetime.strptime(h, "%H:%M:%S").time()
                        except:
                            return None
                    if isinstance(h, datetime.time):
                        return h
                    return None

                if "FechaHecho" in df.columns:
                    df["FechaHecho"] = df["FechaHecho"].apply(convertir_fecha)
                if "HoraHecho" in df.columns:
                    df["HoraHecho"] = df["HoraHecho"].apply(convertir_hora)

                # Combinar fecha + hora en un solo datetime (Muy util para consultas mas delante)
                def combinar_fecha_hora(fecha, hora):
                    if isinstance(fecha, datetime.datetime) and isinstance(hora, datetime.time):
                        return datetime.datetime.combine(fecha.date(), hora)
                    return None

                df["FechaHoraHecho"] = df.apply(
                    lambda row: combinar_fecha_hora(row.get("FechaHecho"), row.get("HoraHecho")),
                    axis=1
                )

                df.drop(columns=["FechaHecho", "HoraHecho"], inplace=True, errors='ignore')

                if "HoraInicio" in df.columns:
                     df["HoraInicio"] = df["HoraInicio"].astype(str)

                datos = df.where(pd.notnull(df), None).to_dict(orient='records')

                for evento in datos:
                    try:
                        if 'latitud'  in df.columns and 'longitud'  in df.columns and evento.get('latitud') != 'NA' and evento.get('longitud') != 'NA':
                              if 'Municipio_hechos' not in df.columns and 'Estado_hechos' not in df.columns:
                                   geolocator = GoogleV3(api_key=settings.GOOGLE_MAPS_KEY)
                                   latitud = evento.get('latitud', '')
                                   longitud = evento.get('longitud', '')
                                   location = geolocator.reverse((latitud,longitud))
                                   municipio_geo, estado_geo = getEstadoMunicipio(location)
                                   if municipio_geo:
                                        evento['Municipio_hechos'] = municipio_geo
                                   if estado_geo:
                                        evento['Estado_hechos'] = estado_geo
                              else:
                                   geolocator = GoogleV3(api_key=settings.GOOGLE_MAPS_KEY)
                                   calle_dir = evento.get('Calle_hechos')
                                   col_dir = evento.get('ColoniaHechos')
                                   if 'Calle_hechos2' in df.columns and evento.get('Calle_hechos2') != 'NA':
                                        calle_dir_dos = evento.get('Calle_hechos2')
                                        direccion = f"{calle_dir}, {calle_dir_dos}, {col_dir}"
                                   else:
                                        direccion = f"{calle_dir}, {col_dir}"
               
                                   location = geolocator.geocode(direccion)
                                   municipio_geo, estado_geo = getEstadoMunicipio(location)

                                   if municipio_geo:
                                        evento['Municipio_hechos'] = municipio_geo
                                   if estado_geo:
                                        evento['Estado_hechos'] = estado_geo

                        delito = evento.get('Delito', '')
                        icono = None
                        if isinstance(delito, str):
                            delito_lower = delito.lower()
                            if 'amenazas' in delito_lower:
                                icono = 'amenazas'
                            elif 'robo a negocio' in delito_lower:
                                icono = 'robonegocio'
                            elif 'homicidio doloso' in delito_lower:
                                 icono = 'homicidiodoloso'
                            elif 'feminicidio' in delito_lower:
                                 icono = 'feminicidio'
                            elif 'secuestro' in delito_lower:
                                 icono = 'secuestro'
                            elif 'trata de personas' in delito_lower:
                                 icono = 'tratapersonas'
                            elif 'robo a transeunte' in delito_lower:
                                 icono = 'robotranseunte'
                            elif 'extorsión' in delito_lower:
                                 icono = 'extorsion'
                            elif 'robo a casa habitación' in delito_lower:
                                 icono = 'robocasa'
                            elif 'violación' in delito_lower:
                                 icono = 'violacion'
                            elif 'narcomenudeo' in delito_lower:
                                 icono = 'narcomenudeo'
                            elif 'delito de bajo impacto' in delito_lower:
                                 icono = "bajoimpacto"
                            elif 'arma de fuego' in delito_lower:
                                 icono = 'armafuego'
                            elif 'robo de vehiculo' in delito_lower:
                                 icono = 'robovehiculo'
                            elif 'robo de accesorios de auto' in delito_lower:
                                 icono= 'robovehiculo'

                        
                        evento['icono'] = icono
                        evento['updatedAt'] = datetime.datetime.now(datetime.timezone.utc)
                        db.collection('Eventos').add(evento)

                    except Exception as e:
                        error_message = "Error subiendo evento a Firestore"
                        return redirect(f"/loadFiles?error={urllib.parse.quote(error_message)}")
                        
                        

                success_message = "La carga ha sido exitosa"
                return redirect(f"/loadFiles?success={urllib.parse.quote(success_message)}")

            except Exception as e:
                error_message = "Error general"
                return redirect(f"/loadFiles?error={urllib.parse.quote(error_message)}")

        # Carga manual
        else:
            calle = request.POST.get("calle")
            colonia = request.POST.get("colonia")
            estado = request.POST.get("estado")
            municipio = request.POST.get("municipio")
            crime = request.POST.get("crime")
            fechaValue = request.POST.get("FechaHoraHecho")
            evento = request.POST.get("evento")
            categoria = request.POST.get("categ")
            lat = request.POST.get('lat')
            lng = request.POST.get('lng')
            
            crime_str = str(crime)
            crime_upper = crime_str.upper()
            

          # Este segmento es sobre los iconos
            try:
                icono = None
                if 'amenazas' in crime:
                    icono = 'amenazas'
                elif 'robo a negocio' in crime:
                    icono = 'robonegocio'
                elif 'homicidio doloso' in crime:
                        icono = 'homicidiodoloso'
                elif 'feminicidio' in crime:
                        icono = 'feminicidio'
                elif 'secuestro' in crime:
                        icono = 'secuestro'
                elif 'trata de personas' in crime:
                        icono = 'tratapersonas'
                elif 'robo a transeunte' in crime:
                        icono = 'robotranseunte'
                elif 'extorsion' in crime:
                        icono = 'extorsion'
                elif 'robo a casa habitacion' in crime:
                        icono = 'robocasa'
                elif 'violacion' in crime:
                        icono = 'violacion'
                elif 'narcomenudeo' in crime:
                        icono = 'narcomenudeo'
                elif 'delito de bajo impacto' in crime:
                        icono = "bajoimpacto"
                elif 'arma de fuego' in crime:
                        icono = 'armafuego'
                elif 'robo de vehiculo' in crime:
                        icono = 'robovehiculo'
                elif 'robo de accesorios de auto' in crime:
                        icono= 'robovehiculo'
                
                      
            except Exception as e:
                 print(e)

            timestamp = None

            if fechaValue:
                 try:
                    if 'T' in fechaValue:
                        dt= datetime.datetime.fromisoformat(fechaValue) 
                    else:
                        dt=datetime.datetime.strptime(fechaValue, "%Y-%m-%d %H:%M:%S")

                    timestamp = dj_timezone.make_aware(dt)
                        
                 except Exception as e:
                      return render(request, 'loadFiles.HTML', {
                           'error': f'Error al convertir la fecha: {e}'
                      })
                 if dt:
                    year = dt.year
                    month = dt.month
                    meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
                    mes = meses[month-1]
                      
                           
          
            if ((calle and colonia and estado and municipio) or (lat and lng)) and fechaValue and (crime or evento) and icono:
                now = datetime.datetime.now(datetime.timezone.utc)
                try:
                    if ((not calle and not colonia and not estado and not municipio) and lat and lng):
                         geolocator = GoogleV3(api_key=settings.GOOGLE_MAPS_KEY)
                         
                         location = geolocator.reverse((lat,lng))
                         if location and location.raw:
                              componentes = location.raw.get('address_components', [])
                              calle_geo = colonia_geo = municipio_geo = estado_geo = None
                              for comp in componentes:
                                   tipos = comp['types']
                                   if 'route' in tipos :
                                        calle_geo = comp['long_name']
                                   elif 'street_number' in tipos:
                                        numero_geo = comp['long_name']
                                   elif 'sublocality' in tipos or 'sublocality_level_1' in tipos:
                                        colonia_geo = comp['long_name']
                                   elif 'locality' in tipos:
                                        municipio_geo = comp['long_name']
                                   elif 'administrative_area_level_1' in tipos:
                                        estado_geo = comp['long_name']

                                   if calle_geo and numero_geo:
                                        calleNumero = f"{calle_geo} {numero_geo}"
                                   else:
                                        calleNumero = calle_geo

                              db.collection('Eventos').add({
                              "Calle_hechos": calleNumero,
                              "ColoniaHechos": colonia_geo,
                              "Estado_hechos": estado_geo,
                              "Delito": crime_upper,
                              "FechaHoraHecho": timestamp,
                              "Evento":evento,
                              "icono": icono,
                              "Municipio_hechos": municipio_geo,
                              "Categoria": categoria,
                              "latitud": lat,
                              "longitud": lng,
                              'updatedAt': now,
                              'Ano_hecho': year,
                              'Ano_inicio': year,
                              'Mes_hecho': mes,
                              'Mes_inicio': mes
                              })
                    if (( calle and colonia and  estado and  municipio) and (not lat and not lng)):
                         direccion=f"{calle}, {colonia}, {estado}, {municipio}"
                         geolocator = GoogleV3(api_key=settings.GOOGLE_MAPS_KEY)
                         location = geolocator.geocode(direccion)
                         lat_geo = location.latitude
                         lng_geo = location.longitude

                         db.collection('Eventos').add({
                               "Calle_hechos": calle,
                               "ColoniaHechos": colonia,
                               "Estado_hechos": estado,
                               "Delito": crime_upper,
                               "FechaHoraHecho": timestamp,
                               "Evento":evento,
                               "icono": icono,
                               "Municipio_hechos": municipio,
                               "Categoria": categoria,
                               "latitud": lat_geo,
                               "longitud": lng_geo,
                               'updatedAt': now,
                               'Ano_hecho': year,
                               'Ano_inicio': year,
                               'Mes_hecho': mes,
                               'Mes_inicio': mes
                               })
                         

                    elif calle and colonia and estado and municipio and lat and lng:
                     
                         db.collection('Eventos').add({
                              "Calle_hechos": calle,
                              "ColoniaHechos": colonia,
                              "Estado_hechos": estado,
                              "Delito": crime_upper,
                              "FechaHoraHecho": timestamp,
                              "Evento":evento,
                              "icono": icono,
                              "Municipio_hechos": municipio,
                              "Categoria": categoria,
                              "latitud": lat,
                              "longitud": lng,
                              'updatedAt': now,
                              'Ano_hecho': year,
                              'Ano_inicio': year,
                              'Mes_hecho': mes,
                              'Mes_inicio': mes
                              })
                    success_message = "Datos agregados exitosamente"
                    return redirect(f"/loadFiles?success={urllib.parse.quote(success_message)}")
                except:
                     error_message = "Error al subir datos"
                     return redirect(f"/loadFiles?error={urllib.parse.quote(error_message)}")
            else:
                 error_message = "Faltan datos por agregar"
                 return redirect(f"/loadFiles?error={urllib.parse.quote(error_message)}")
     
    success = request.GET.get("success")
    error = request.GET.get("error")
    return render(request, "loadFiles.html", {"error": error, 'success': success, 'usuarios': usuarios, 'priv': priv,})

def getEstadoMunicipio(location):
     municipio = estado = None
     if location and location.raw.get('address_components', []):
          for comp in location.raw['address_components']:
               tipos = comp['types']
               if 'locality' in tipos:
                    municipio = comp['long_name']
               elif 'administrative_area_level_1' in tipos:
                    estado = comp['long_name']
     return municipio, estado

def library(request):
     sessionCookie = request.COOKIES.get('session')
     priv = getPrivileges(request)

     if not sessionCookie:
          return redirect ("login")
     try:
          decoded_claims = auth.verify_session_cookie(sessionCookie, check_revoked=True)
          uid = decoded_claims["uid"]
     except:
          return redirect("login")
     usuarios = getUsers()
     ref = db.collection('Eventos')
     
     eventos =[]
     if request.method == 'POST':
          filters = {}
          
          startDate_str = request.POST.get('startDate')
          endDate_str = request.POST.get('endDate')
          direccion = request.POST.get('direccion' , '')
          search = request.POST.get('searchBy')

          partes_direccion = [parte.strip() for parte in direccion.split(',') if parte.strip()]

          if(search =="full"):
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
          elif (search =="estado"):
               estado = partes_direccion[0] if len(partes_direccion) > 0 else None
               if estado:
                    filters['Estado_hechos'] = estado
          elif (search =="municipio"):
               municipio = partes_direccion[0] if len(partes_direccion) > 0 else None
               if municipio:
                    filters['Municipio_hechos'] = municipio
          elif (search=="estadoMunicipio"):
               
               municipio = partes_direccion[0] if len(partes_direccion) > 0 else None
               estado = partes_direccion[1] if len(partes_direccion) > 1 else None
               if municipio:
                    filters['Municipio_hechos'] = municipio.strip()
               if estado:
                    filters['Estado_hechos'] = estado.strip()
               
          
 
          if startDate_str and endDate_str:
               startDate = datetime.datetime.strptime(startDate_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
               endDate = datetime.datetime.strptime(endDate_str, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)
               filters['startDate']=startDate
               filters['endDate']=endDate
          
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
          resultados = query_ref.stream()
          
          for doc in resultados:
               data = doc.to_dict()
               eventos.append(data)
          
        
     return render(request, 'library.html', {'usuarios': usuarios, 'eventos': eventos, 'priv': priv})




# Create your views here.
