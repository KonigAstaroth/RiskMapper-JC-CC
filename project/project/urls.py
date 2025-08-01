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
from django.contrib import admin
from django.urls import path
from app import views


 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('subscriptions/', views.subscriptions, name='subs'),
    path('policy/', views.policy, name='policy'),
    path('forgotPassword/', views.forgotpass, name='pass'),
    path('main/', views.main, name='main'),
    path('add/', views.add, name='add'),
    path('logout/', views.logout, name='logout'),
    path('manageUser/', views.manage_user, name='manageUser'),
    path('edit_user<str:id>/', views.editUser, name='editUser'),
    path('delete_user<str:id>/', views.deleteUser, name='deleteUser'),
    path('loadFiles/', views.loadFiles, name='loadFiles'),
    path('library/', views.library, name='library'),
    path('recoverPass/<token>/', views.recoverPass, name='recoverPass'),
    path('exportDocx/', views.exportarDocx, name='export'),
    path('edit_event<str:id>/', views.edit_event, name='edit_event'),
    path('delete_event<str:id>/', views.deleteEvent, name='delete_event'),
    path('success/', views.success, name='success')
]
