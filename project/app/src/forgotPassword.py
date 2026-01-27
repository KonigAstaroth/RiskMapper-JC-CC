from django.shortcuts import redirect
import urllib

from itsdangerous import URLSafeTimedSerializer
from app.core.auth.firebase_config import auth
from app.src.utils.mailHandler import sendEmail
from django.conf import settings
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

def generate_token(email, uid):
     s = URLSafeTimedSerializer(settings.SECRET_KEY)
     return s.dumps(email, salt="recover-pass")

def sendRecoverLink(request):
    if request.method == "POST":
          try:
               
               email = request.POST.get('email')
               user = auth.get_user_by_email(email)
               if user:
                    token = generate_token(email, user.uid)
                    # Se debe de cambiar el link correcto en produccion
                    link = request.build_absolute_uri(f"https://riskmapper-jc-cc.onrender.com/recoverPass/{token}/")
                    sendEmail(email, link)
                    success_message = "Correo para restablecer contraseña ha sido enviado"
                    return redirect(f"/forgotPassword?success={urllib.parse.quote(success_message)}")
                    
          except Exception as e:
               error_message = f"{e}"
               return redirect(f"/forgotPassword?error={urllib.parse.quote(error_message)}")
          

def recoverPasswordProcess (request, token):
     s = URLSafeTimedSerializer(settings.SECRET_KEY)
     
     try:
          email = s.loads(token, salt="recover-pass", max_age = 900)
     except SignatureExpired:
          error_message = "El enlace ha expirado. Solicita uno nuevo."
          return redirect(f"/recoverPass/{token}?error={urllib.parse.quote(error_message)}") 
     except BadSignature:
          error_message = "El enlace es inválido."
          return redirect(f"/recoverPass/{token}?error={urllib.parse.quote(error_message)}") 
     
     if not email:
          return redirect('login')
     contra = request.POST.get('password')
     repassword = request.POST.get('repassword')
     
     if request.method == 'POST':
          
          if not contra or not repassword:
               error_message = "Faltan campos por llenar"
               return redirect(f"/recoverPass/{token}?error={urllib.parse.quote(error_message)}") 
          if contra != repassword:
               error_message = "Las contraseñas no coinciden"
               return redirect(f"/recoverPass/{token}?error={urllib.parse.quote(error_message)}")  
          
          try:
               
               user = auth.get_user_by_email(email)
               auth.update_user(user.uid, password=contra)
               success_message = "Contraseña restablecida"
               return redirect(f"/recoverPass/{token}?success={urllib.parse.quote(success_message)}")
          except Exception as e:
               error_message = str(e)
               return redirect(f"/recoverPass/{token}?error={urllib.parse.quote(error_message)}") 
          