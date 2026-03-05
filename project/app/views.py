from django.http import HttpResponse
from django.shortcuts import render,redirect
from django.conf import settings
import json

# Imports needed for context & display important info
from app.src.admin_service.admins import getPrivileges
from app.src.utils.users import getUsers
from app.src.library_service import searchEvent, buildFilters
from app.src.utils.report_generation_utils.lists import lista_delitos
from app.src.utils.map_config_helper import map_config_center
from app.src.utils.cache_events import markers
from app.src.login import updateLastLogin
from app.src.business_units_service import getUnits

# Testing
from app.core.auth.firebase_config import db

def userSettings(request):
    units = getUnits(request)
    return render(request, 'userSettings.html', {'unidades': units})

def login(request):
     updateLastLogin(request)
     return render(request, 'login.html')

def forgotpass (request):             
    error = request.GET.get("error")
    success = request.GET.get("success")
    return render(request, 'forgotPass.html', {'error':error, 'success': success})

def recoverPass (request, token):
     error = request.GET.get("error")
     success = request.GET.get('success')
     return render(request, 'recoverPass.html', {'error': error, 'success':success})

def main (request):
     uid = getattr(request, 'uid', None)
    
    # 1. Prueba de Fuego: ¿Podemos leer de Firestore?
     try:
        user_ref = db.collection('Usuarios').document(uid).get()
        if user_ref.exists:
            user_data = user_ref.to_dict()
        else:
            user_data = {"error": "El documento no existe en Firestore"}
     except Exception as e:
        # Si falla aquí, es un tema de permisos del JSON o del objeto 'db'
        return HttpResponse(f"Falla Firestore: {str(e)}", status=500)   
     priv = getPrivileges(request)
     idioma = request.GET.get("idioma", "es")
     request.session['lang'] = idioma
     
     map_config = map_config_center(request)

     markers_json = markers()

     unidades = getUnits(request)

     #Filtrado de datos
     graphic = request.session.get('graphic')
     calendars = request.session.get('calendarios', [])
     hour_txt = request.session.get('hour_txt', None)
     AiText = request.session.get('AiText', None)
     lugar = request.session.get('lugar')
     data_table = request.session.get('tabla_base64', None)
                 
     error = request.GET.get("error")

     context = {
          'priv': priv,
          'google_maps_api_key': settings.GOOGLE_MAPS_KEY,
          'markers': markers_json,
          'graphic': graphic,
          'calendarios': calendars,
          'lugar': lugar,
          'hour_txt': hour_txt,
          'AiText': AiText,
          'map_config_json': json.dumps(map_config),
          'error': error,
          'lista_delitos': lista_delitos,
          'tabla_base64': data_table,
          'unidades':unidades     
     }
     return render (request, 'main.html', context)

def manageUsers(request):
     query = request.GET.get("search")
     role_filter = request.GET.get("role_filter")
     usuarios = getUsers(query, role_filter)
     priv = getPrivileges(request)
     
     if not priv:
          return redirect("main")
     success = request.GET.get("success")
     error = request.GET.get("error")
     return render(request, 'manageUser.html', {"usuarios": usuarios, "success": success, "error": error, 'priv': priv,})


def loadFiles(request):
    priv = getPrivileges(request)

    success = request.GET.get("success")
    error = request.GET.get("error")
    return render(request, "loadFiles.html", {"error": error, 'success': success, 'priv': priv,})


def library(request):
    priv = getPrivileges(request)
    eventos =[]
    if request.method == 'POST':
          filters = buildFilters(request)
          eventos = searchEvent(filters)
          request.session['filters_library'] = filters

    return render(request, 'library.html', {
        'eventos': eventos,
        'priv': priv
    })
