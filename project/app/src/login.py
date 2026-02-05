import datetime
from app.core.auth.firebase_config import FIREBASE_AUTH_URL
from app.core.auth.check_captcha_answered import checkCaptcha
import requests
# from app.core.auth.check_login_errors import login_errors
from django.shortcuts import redirect
import urllib.parse
from datetime import timedelta, timezone
from app.core.auth.firebase_config import db, auth
from django.contrib import messages

def loginToken(email, password):
    login = {"email": email, "password": password, "returnSecureToken": True}
    auth_response = requests.post(FIREBASE_AUTH_URL, json=login)

    if auth_response.status_code == 200:
        user_data = auth_response.json()
        id_token = user_data["idToken"]
        return id_token
    else:
        try:
            error_data = auth_response.json()
            error_message = error_data.get("error", {}).get("message", "UKNOWN_ERROR")

            return f"ERROR: {error_message}"
        except Exception:
            return "ERROR: Error desconocido"


def login_process(request):
    if request.method == 'POST':
        recaptcha_response = request.POST.get('g-recaptcha-response')

        email = request.POST["email"]
        password = request.POST["password"]
        remember = request.POST.get("remember")

        result = checkCaptcha(recaptcha_response)

        if not result.get('success'):
            error_msg = "Se debe de validar el CAPTCHA"
            return redirect(f"/?error={urllib.parse.quote(error_msg)}")
        
        id_token = loginToken(email, password)

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
                secure=True  # Cambiar a True en producción con HTTPS
            )
            decoded_claims = auth.verify_session_cookie(session_cookie)
            uid = decoded_claims["uid"]
            db.collection('Usuarios').document(uid).update({'lastAccess': datetime.datetime.now(timezone.utc)})
            
            return response_redirect
        except Exception as e:
            messages.error(request, "Error al crear la cookie de sesión:", str(e))
            return redirect('/')
