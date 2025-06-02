import requests
from django.shortcuts import render,redirect
from django.conf import settings
from django.contrib import messages
from firebase_admin import firestore, auth
from django.conf import settings
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
from PIL import Image
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
matplotlib.use('agg')
import numpy as np
import io
import base64
from time import time
from geopy.geocoders import GoogleV3


db = firestore.client()

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
                    db.collection('Usuarios').document(uid).update({'lastAccess': datetime.datetime.now(timezone.make_aware)})
                    
                    return response_redirect
                except Exception as e:
                    messages.error(request, "Error al crear la cookie de sesión:", e)
                    return redirect('/')
        else:
             messages.error(request, "Correo o contraseña incorrectos") 
             return redirect('/')
    return render(request, 'login.html')

def policy (request):
    return render(request, 'policy.html')

def forgotpass (request):
    return render(request, 'forgotPass.html')

def time_to_num(time_str):
     try:
          hh, mm, ss = map(int, time_str.strip().split(':'))
          return ss +60*(mm + 60*hh)
     except Exception as e:
          print(f"Error al convertir '{time_str}': {e}")
          return None

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
          
     ref = db.collection('Eventos')
     data = ref.get() or []

     list_markers = []


     for doc in data:
          valor = doc.to_dict()

          fecha_obj = valor.get('FechaHoraHecho')

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

     markers_json = mark_safe(json.dumps(list_markers))

     #Filtrado de datos
     graphic = request.session.pop('graphic', None)

     if request.method == 'POST' and 'buscar' in request.POST :
          filters = {}

          calle = request.POST.get('calle')
          colonia = request.POST.get('colonia')
          municipio = request.POST.get('municipio')
          estado = request.POST.get('estado')
          startDate_str = request.POST.get('startDate')
          endDate_str = request.POST.get('endDate')


          if calle:
               filters['Calle_hechos'] = calle
          if colonia := request.POST.get('colonia'):
               filters['ColoniaHechos'] = colonia
          if municipio := request.POST.get('municipio'):
               filters['Municipio_hechos'] = municipio
          if estado := request.POST.get('estado'):
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
          resultados = query_ref.stream()

          
          angulos =[]
          radios= []
          
         
          for  doc in resultados:
               eventos = doc.to_dict()
               date_obj = eventos.get('FechaHoraHecho')
               print("filtros:", filters)

               print(eventos)
               

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
                    
               else:
                    print("No hay timestamp")

               print("angulos", angulos)
               print("radios", radios)

          if angulos and radios:
               fig =  plt.figure(figsize=(7,7))
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
               return redirect('main') 
               

     context = {
          'name': name,
          'priv': priv,
          'usuarios': usuarios,
          'google_maps_api_key': settings.GOOGLE_MAPS_KEY,
          'markers': markers_json,
          'graphic': graphic,
          'timestamp': int(time()),
          
     }

          
               
          
     return render (request, 'main.html', context)

def generateCalendar(year: int, month: int, dayIcons: list):
     cal = calendar.monthcalendar(year, month)
     fig, ax = plt.subplot(figsize=(10,8))
     ax.set_axis_off()
     ax.set_title(calendar.month_name[month] + f" {year}", fontsize=20)

     dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

     for i, dias in enumerate(dias_semana):
          ax.text(i+0.5, len(cal), dias, ha='center', va= 'center', fontsize=12, weight='bold')
     icono_cache = {}

     for fila, semana in enumerate(cal):
          for columna, dia in enumerate(semana):
               if dia != 0:
                    ax.text(columna + 0.5, len(cal) - fila - 0.5, str(dia), ha='center', va='top', fontsize=10)
                    for dia_evento, icono in dayIcons:
                         if dia_evento == dia:
                              if icono not in icono_cache:
                                   imagen = Image.open(f"iconos/{icono}.png").resize((30, 30))
                                   icono_cache[icono] = OffsetImage(imagen)
                         ab = AnnotationBbox(icono_cache[icono], (columna + 0.5, len(cal) - fila - 0.5 - 0.3), frameon=False)
                         ax.add_artist(ab)

     plt.xlim(0, 7)
     plt.ylim(0, len(cal) + 1)
     plt.tight_layout()
     nombre_archivo = f"calendario_{year}_{month}.png"
     plt.savefig(f"media/{nombre_archivo}")
     plt.close()
     return nombre_archivo

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

    try:
        decoded_claims = auth.verify_session_cookie(sessionCookie, check_revoked=True)
        uid = decoded_claims["uid"]
    except Exception as e:
        print("Error autenticando:", e)
        return redirect("login")

    if not sessionCookie:
        return redirect("login")

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
                      
                           
                           
            if ((calle and colonia and estado and municipio) or (lat and lng)) and fechaValue and (crime or evento) and icono:
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
                              "longitud": lng
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
                               "longitud": lng_geo
                               })
                         print("latitud: ", location.latitude)
                         print("longitud: ", location.longitude)

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
                              "longitud": lng
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
    return render(request, "loadFiles.html", {"error": error, 'success': success})





# Create your views here.
