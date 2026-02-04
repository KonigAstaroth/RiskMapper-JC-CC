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
from app.src import login, forgotPassword, logout
from app.src.stripe_service import stripe
from app.src.admin_service import admins
from app.src.generate_docx_service import exportDocx
from app.src import library_service, load_files_service



 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login, name='login'),
    path('login-process', login.login_process, name='login-process'),
    path('signup/', views.signup, name='signup'),
    path('subscriptions/', views.subscriptions, name='subs'),
    path('process-subscription/', stripe.processSubscription, name='process-subscription'),
    path('policy/', views.policy, name='policy'),
    path('forgotPassword/', views.forgotpass, name='pass'),
    path('forgotPassword-sendMail', forgotPassword.sendRecoverLink, name='send-recover-mail'),
    path('main/', views.main, name='main'),
    path('add/', views.add, name='add'),
    path('admin-adduser/', admins.adduser, name='admin-adduser'),
    path('logout/', logout.logout, name='logout'),
    path('manageUser/', views.manage_user, name='manageUser'),
    path('edit_user<str:id>/', admins.editUser, name='editUser'),
    path('delete_user<str:id>/', admins.deleteUser, name='deleteUser'),
    path('loadFiles/', views.loadFiles, name='loadFiles'),
    path('loadFilesService/', load_files_service.loadFilesService, name='loadFilesService'),
    path('library/', views.library, name='library'),
    path('recoverPass/<token>/', views.recoverPass, name='recoverPass'),
    path('exportDocx/', exportDocx.ProcessDocx, name='export'),
    path('edit_event<str:id>/', library_service.edit_event, name='edit_event'),
    path('delete_event<str:id>/', library_service.deleteEvent, name='delete_event'),
    path('success/', views.success, name='success')
]
