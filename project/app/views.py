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
                    db.collection('Usuarios').document(uid).update({'lastAccess': datetime.datetime.now(timezone.utc)})
                    
                    return response_redirect
                except Exception as e:
                    messages.error(request, "Error al crear la cookie de sesión:", e)
                    print(e)
                    return redirect('/')
        else:
             messages.error(request, "Correo o contraseña incorrectos") 
             return redirect('/')
    return render(request, 'login.html')

def policy (request):
    return render(request, 'policy.html')

def forgotpass (request):
    return render(request, 'forgotPass.html')

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
          
     ref = db.collection('Eventos')
     data = ref.get() or []

     list_markers = []

     for doc in data:
          valor = doc.to_dict()
          marker = {
               'lat': valor.get('latitud'),
               'lng': valor.get('longitud'),
               'name': valor.get('Categoria')
          }
          list_markers.append(marker)

     markers_json = mark_safe(json.dumps(list_markers))
     
     
     return render (request, 'main.html',{ 'name': name, 'priv': priv, 'usuarios':usuarios, 'key': settings.GOOGLE_MAPS_KEY, 'markers': markers_json})

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

def loadFiles (request):
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
          
          if 'archivo' in request.FILES:
               try:
                    excel_file = request.FILES['archivo']
                    print("✅ Archivo recibido:", excel_file.name)
                    df = pd.read_excel(excel_file,engine='openpyxl')
                    print(df.head())

                    for columna in df.select_dtypes(include=['datetime']):
                         df[columna] = df[columna].astype(str)

                    datos = df.where(pd.notnull(df), None).to_dict(orient='records')

                    for evento in datos:
                         try:
                              evento = convertir_tiempos_a_string(evento)
                              db.collection('Eventos').add(evento)
                         except Exception as e:
                              print(f"Error: {e}")

                    return redirect('main')
               except Exception as e:
                    return render(request, 'loadFiles.html', {
                'error': f'Error al procesar el archivo: {e}'
            })

     return render(request, "loadFiles.html", {"priv":priv})

def convertir_tiempos_a_string(diccionario):
    for clave, valor in diccionario.items():
        if isinstance(valor, datetime.time):
            diccionario[clave] = valor.strftime('%H:%M') 
    return diccionario


# Create your views here.
