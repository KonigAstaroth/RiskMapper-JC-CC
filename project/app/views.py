import json
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render,redirect
# Imports needed for context & display important info
from app.src.utils.users import getUsers
from app.src.login import updateLastLogin
from app.src.utils.cache_events import markers
from app.src.business_units_service import getUnits
from app.src.admin_service.admins import getPrivileges
from app.src.library_service import searchEvent, buildFilters
from app.src.utils.map_config_helper import map_config_center
from app.src.get_database_report_data import getDataDBMain
from app.src.utils.report_generation_utils.lists import lista_delitos

def userSettings(request):
    priv = getPrivileges(request)
    units = getUnits(request)
    return render(request, 'userSettings.html', {'unidades': units, 'priv': priv})

def login(request):
     updateLastLogin(request)
     error = request.GET.get("error")
     return render(request, 'login.html', {'error': error})

def forgotpass (request):             
    error = request.GET.get("error")
    success = request.GET.get("success")
    return render(request, 'forgotPass.html', {'error':error, 'success': success})

def recoverPass (request, token):
     error = request.GET.get("error")
     success = request.GET.get('success')
     return render(request, 'recoverPass.html', {'error': error, 'success':success})

def main (request):  
     try:
          priv = getPrivileges(request)
          
          map_config = map_config_center(request)

          markers_json = markers()
          
          unidades = getUnits(request)

          # Check if a report is in process
          task_id = request.session.get("task_id")

          graphic, calendars, hour_txt, AiText, lugar, data_table = getDataDBMain(task_id, request)
                    
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
               'unidades':unidades, 
               'generating_report' : request.session.get('generating_report', False)    
          }
          return render (request, 'main.html', context)
     except Exception as e:
        import traceback
        error_completo = traceback.format_exc()
        return HttpResponse(f"Error detectado: {str(e)} <br><pre>{error_completo}</pre>", status=200)

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
    context = {
         "error": error, 'success': success, 'priv': priv,
         "loading_bulk": request.session.get("loading_bulk", False)
    }
    return render(request, "loadFiles.html", context)

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