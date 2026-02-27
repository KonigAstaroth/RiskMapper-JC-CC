"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from json import load
from django.contrib import admin
from django.urls import path
from app import views
from app.src import login, forgotPassword, logout, report_generation_service, library_service, load_files_service, business_units_service
from app.src.admin_service import admins
from app.src.generate_docx_service import exportDocx
from app.src.utils import set_map_coords, download_template, download_events

 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login, name='login'),
    path('login-process/', login.login_process, name='login-process'),
    path('forgotPassword/', views.forgotpass, name='pass'),
    path('forgotPassword-sendMail', forgotPassword.sendRecoverLink, name='send-recover-mail'),
    path('main/', views.main, name='main'),
    path('search-location', set_map_coords.setSearchCoords, name='getLocationCoordsMap'),
    path('admin-adduser/', admins.adduser, name='admin-adduser'),
    path('logout/', logout.logout, name='logout'),
    path('manageUser/', views.manageUsers, name='manageUsers'),
    path('edit_user<str:id>/', admins.editUser, name='editUser'),
    path('delete_user<str:id>/', admins.deleteUser, name='deleteUser'),
    path('loadFiles/', views.loadFiles, name='loadFiles'),
    path('loadFilesService/', load_files_service.loadFilesService, name='loadFilesService'),
    path('library/', views.library, name='library'),
    path('recoverPass/<token>/', views.recoverPass, name='recoverPass'),
    path('exportDocx/', exportDocx.ProcessDocx, name='export'),
    path('edit_event<str:id>/', library_service.edit_event, name='edit_event'),
    path('delete_event<str:id>/', library_service.deleteEvent, name='delete_event'),
    path('report-generation/', report_generation_service.generateReport, name='generate_report'),
    path('settings/', views.userSettings, name='userSettings'),
    path('addBusinessUnit/', business_units_service.addUnit, name='addUnit'),
    path('editunit<str:id>/', business_units_service.editUnit, name='editUnit'),
    path('deleteunit<str:id>/', business_units_service.deleteUnit, name='deleteUnit'),
    path('download-template/', download_template.downloadTemplate, name='download-template'),
    path('download-events-from-library/', download_events.downloadEvents, name='excel-events')
    

    # Deprecated urls (for now)
    # path('signup/', views.signup, name='signup'),
    # path('signup-process/', signup.signupProcess, name='signup-process'),
    # path('subscriptions/', views.subscriptions, name='subs'),
    # path('process-subscription/', stripe.processSubscription, name='process-subscription'),
    # path('success/', views.success, name='success'),
]
