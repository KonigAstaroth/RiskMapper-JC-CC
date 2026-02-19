from django.shortcuts import render,redirect
from django.conf import settings
import json
import matplotlib
matplotlib.use('agg')
from time import time

# Imports needed for context & display important info
from app.src.admin_service.admins import getPrivileges
from app.src.utils.users import getUsers
from app.src.library_service import searchEvent
from app.src.utils.report_generation_utils.lists import lista_delitos
from app.src.report_generation_service import generateReport
from app.src.utils.cache_events import markers
from app.src.login import updateLastLogin


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
     priv = getPrivileges(request)
     idioma = request.GET.get("idioma", "es")
     request.session['lang'] = idioma
     
     map_config = {
        'center': {'lat': 19.42847, 'lng': -99.12766},
        'zoom': 6
     }

     markers_json = markers()

     #Filtrado de datos
     graphic = request.session.get('graphic')
     calendars = request.session.get('calendarios', [])
     
     hour_txt = request.session.get('hour_txt', None)
     AiText = request.session.get('AiText', None)
     lugar = request.session.get('lugar')
     data_table = request.session.get('tabla_base64', None)
     
     if request.method == 'POST':
          graphic, calendars, data_table, lugar = generateReport(request)
          return redirect('main')
                 
     error = request.GET.get("error")

     context = {
          'priv': priv,
          'google_maps_api_key': settings.GOOGLE_MAPS_KEY,
          'markers': markers_json,
          'graphic': graphic,
          'calendarios': calendars,
          'timestamp': int(time()),
          'lugar': lugar,
          'hour_txt': hour_txt,
          'AiText': AiText,
          'map_config_json': json.dumps(map_config),
          'error': error,
          'lista_delitos': lista_delitos,
          'tabla_base64': data_table,     
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
     
     if not priv:
          return redirect("main")
     success = request.GET.get("success")
     error = request.GET.get("error")
     return render(request, 'manageUser.html', {"usuarios": usuarios, "success": success, "error": error})


def loadFiles(request):
    priv = getPrivileges(request)

    success = request.GET.get("success")
    error = request.GET.get("error")
    return render(request, "loadFiles.html", {"error": error, 'success': success, 'priv': priv,})


def library(request):
    priv = getPrivileges(request)
    eventos =[]

    if request.method == 'POST':
          eventos = searchEvent(request)

    return render(request, 'library.html', {
        'eventos': eventos,
        'priv': priv
    })
