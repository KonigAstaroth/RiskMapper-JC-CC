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
import numpy as np
import io
import base64
from time import time


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


          if calle:
               filters['Calle_hechos'] = calle
          if colonia := request.POST.get('colonia'):
               filters['ColoniaHechos'] = colonia
          if municipio := request.POST.get('municipio'):
               filters['Municipio_hechos'] = municipio
          if estado := request.POST.get('estado'):
               filters['Estado_hechos'] = estado
          
          query_ref = ref

          if filters:
               for campo, valor in filters.items():
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
                
                
                
     
    success = request.GET.get("success")
    error = request.GET.get("error")
    return render(request, "loadFiles.html", {"error": error, 'success': success})





# Create your views here.
