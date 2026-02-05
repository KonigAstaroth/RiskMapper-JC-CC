from django.shortcuts import redirect
from app.core.auth.firebase_config import db, auth
import urllib.parse

def signupProcess(request):
    if request.method == 'POST':
          name = request.POST.get('name')
          lastName = request.POST.get('lastName')
          email = request.POST.get('correo_personal')
          password = request.POST.get('clave_segura')
          repassword = request.POST.get('clave_repetida')
          client = request.POST.get('client')
          try:
               if name and lastName and email and password == repassword:
                    user = auth.create_user(email=email, password=password)
                    db.collection("Usuarios").document(user.uid).set({
                    "email": email,
                    "name": name,
                    "lastname": lastName,
                    "privileges":False,
                    "lastAccess": None,
                    "client_type": client
                    })
                    request.session['email_usr'] = email
                    return redirect('subs')
               elif repassword != password:
                    error_message = "La contraseña no coicide"
                    return redirect(f"/signup?error={urllib.parse.quote(error_message)}") 
               else:
                    error_message = "Faltan campos por ser llenados"
                    return redirect(f"/signup?error={urllib.parse.quote(error_message)}") 
          except Exception as e:
               return redirect(f"/signup?error={urllib.parse.quote(e)}")